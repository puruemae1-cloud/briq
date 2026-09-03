#!/usr/bin/env bash
# Push missing CW PDP galleries to product-images tag + bump manifest. Disconnect-safe.
set -uo pipefail
cd "$(dirname "$0")/.."
LOG=/tmp/cw-pdp-cdn-push.log
STATUS=/tmp/cw-pdp-cdn-STATUS
DEPLOYED=/tmp/cw-pdp-cdn-DEPLOYED
exec >>"$LOG" 2>&1
echo "=== start $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
touch "$STATUS"
[[ -f "$DEPLOYED" ]] && { echo already; exit 0; }

run_step() {
  local stamp="$1"; shift
  grep -q "${stamp}_OK" "$STATUS" 2>/dev/null && { echo skip "$stamp"; return 0; }
  echo "=== $stamp ==="
  set +e; "$@"; local st=$?; set -e
  echo "EXIT_${stamp}:$st"
  [[ "$st" -ne 0 ]] && { echo "${stamp}_FAIL:$st" >>"$STATUS"; exit "$st"; }
  echo "${stamp}_OK" >>"$STATUS"
}

run_step REDOWNLOAD python3 scripts/redownload-cw-family-galleries.py
run_step REBUILD python3 scripts/rebuild-cw-catalog.py

run_step LIST_MISSING python3 - <<'PY'
import urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
UA={"User-Agent":"Mozilla/5.0"}
base="https://raw.githubusercontent.com/puruemae1-cloud/briq/product-images/public"
root=Path("public/products/cw-pdp")
folders=[d.name for d in root.iterdir() if d.is_dir() and (d/"1.jpg").exists() and (d/"1.jpg").stat().st_size>2500]

def check(name):
    try:
        req=urllib.request.Request(base+f"/products/cw-pdp/{name}/1.jpg", headers=UA, method="HEAD")
        with urllib.request.urlopen(req, timeout=20) as r:
            return name, r.status==200
    except Exception:
        return name, False

missing=[]
with ThreadPoolExecutor(max_workers=20) as ex:
    for name, ok in ex.map(check, folders):
        if not ok:
            missing.append(name)
Path("/tmp/cw-pdp-cdn-missing.txt").write_text("\n".join(sorted(missing))+"\n")
print("missing", len(missing), flush=True)
if not missing:
    print("nothing missing on CDN", flush=True)
PY

if [[ -s /tmp/cw-pdp-cdn-missing.txt ]]; then
  run_step CDN_PUSH python3 scripts/push-product-images-tag.py \
    --dirs cw-pdp --skip-whiten --only-file /tmp/cw-pdp-cdn-missing.txt
else
  echo "CDN_PUSH_SKIP" >>"$STATUS"
fi

run_step VERIFY python3 scripts/verify-product-images.py --brand cw --remote --skip-local --all-images

git add \
  scripts/weekly-cw-stock-sync.py \
  scripts/rebuild-cw-catalog.py \
  scripts/redownload-cw-family-galleries.py \
  scripts/run-cw-pdp-cdn-push.sh \
  scripts/watch-cw-pdp-cdn-push.sh \
  .github/workflows/weekly-cw-sync.yml \
  src/data/cw/cw-catalog.ts \
  src/data/cw/cw-pdp-enriched.json \
  src/data/product-images-manifest.json \
  || true
if ! git diff --cached --quiet; then
  git commit -m "Publish Christopher Ward strap galleries to the product-images CDN."
  git push origin HEAD
fi
touch "$DEPLOYED"
echo "=== DONE $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
