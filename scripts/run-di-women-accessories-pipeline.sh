#!/usr/bin/env bash
# Dior women's fashion accessories: 3 scrape stages → merge → enrich → prices → KO → batched CDN → commit/push.
set -uo pipefail
cd "$(dirname "$0")/.."
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/Library/Caches/ms-playwright}"
export PYTHONUNBUFFERED=1
export PATH="/usr/bin:/bin:/usr/local/bin:$HOME/.local/bin:$HOME/.local/node/bin:$PATH"
LOG=/tmp/di-women-accessories-pipeline.log
STATUS=/tmp/di-women-accessories-STATUS
DEPLOYED=/tmp/di-women-accessories-DEPLOYED
PAUSE_SEC="${PAUSE_SEC:-90}"
exec >>"$LOG" 2>&1

echo "=== women accessories pipeline start $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
touch "$STATUS"

if [[ -f "$DEPLOYED" ]]; then
  echo "already deployed"
  exit 0
fi

for stage in 1 2 3; do
  if grep -q "STAGE_${stage}_OK" "$STATUS" 2>/dev/null; then
    echo "skip stage $stage"
    continue
  fi
  echo "=== STAGE $stage ==="
  set +e
  python3 scripts/scrape-di-women-accessories.py --stage "$stage"
  st=$?
  set -e
  echo "EXIT_STAGE_${stage}:$st"
  if [[ "$st" -ne 0 ]]; then
    echo "STAGE_${stage}_FAIL:$st" >>"$STATUS"
    exit "$st"
  fi
  echo "STAGE_${stage}_OK" >>"$STATUS"
  if [[ "$stage" != "3" ]]; then
    echo "pause ${PAUSE_SEC}s"
    sleep "$PAUSE_SEC" || true
  fi
done

run_step() {
  local stamp="$1"; shift
  if grep -q "${stamp}_OK" "$STATUS" 2>/dev/null; then
    echo "skip $stamp"
    return 0
  fi
  echo "=== $stamp ==="
  set +e
  "$@"
  local st=$?
  set -e
  echo "EXIT_${stamp}:$st"
  if [[ "$st" -ne 0 ]]; then
    echo "${stamp}_FAIL:$st" >>"$STATUS"
    exit "$st"
  fi
  echo "${stamp}_OK" >>"$STATUS"
}

python3 - <<'PY'
import json
from pathlib import Path
p = Path("src/data/di/di-women-slg-catalog-raw.json")
if p.is_file():
    data = json.loads(p.read_text())
    changed = 0
    for row in data.get("products") or []:
        cols = list(row.get("collections") or [])
        if "di-women-accessories" not in cols:
            if "dior-accessories" in cols:
                cols.insert(cols.index("dior-accessories") + 1, "di-women-accessories")
            else:
                cols = ["dior", "dior-accessories", "di-women-accessories", *cols]
            row["collections"] = list(dict.fromkeys(cols))
            changed += 1
    if changed:
        p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print("patched_slg_collections", changed)
PY

run_step MERGE python3 scripts/merge-di-catalog-ko.py
run_step ENRICH python3 scripts/enrich-di-women-accessories-pdp.py
run_step PRICES python3 scripts/fix-di-catalog-prices.py --check
run_step KO python3 scripts/check-catalog-korean.py --brand di --fail
run_step THUMBS python3 scripts/recenter-di-women-card-holder-thumbs.py

python3 - <<'PY'
from pathlib import Path
p = Path("src/data/di/di-catalog.ts")
p.write_text(
    "/* Auto-generated — do not edit */\n"
    'import type { Product } from "@/data/product-types";\n'
    'import data from "./di-catalog.json";\n'
    "\n"
    "/** Dior catalog (JSON import keeps TS small). */\n"
    "export const diCatalogProducts = data as unknown as Product[];\n"
)
print("ts", p.stat().st_size)
PY

echo "=== CDN folders ==="
python3 - <<'PY'
import json
from pathlib import Path
raw = json.load(open("src/data/di/di-women-accessories-catalog-raw.json"))
folders = []
for p in raw.get("products") or []:
    imgs = p.get("images") or []
    if not imgs:
        continue
    parts = str(imgs[0]).split("/")
    if "di-pdp" in parts:
        folders.append(parts[parts.index("di-pdp") + 1])
folders = sorted(set(folders))
Path("/tmp/di-women-accessories-cdn-only.txt").write_text("\n".join(folders) + "\n")
print("cdn_folders", len(folders))
PY

if [[ -s /tmp/di-women-accessories-cdn-only.txt ]]; then
  rm -f /tmp/di-women-accessories-cdn-batch-*
  split -l 80 /tmp/di-women-accessories-cdn-only.txt /tmp/di-women-accessories-cdn-batch-
  batches=(/tmp/di-women-accessories-cdn-batch-*)
  total=${#batches[@]}
  n=0
  for batch in "${batches[@]}"; do
    [[ -f "$batch" ]] || continue
    n=$((n + 1))
    if grep -q "CDN_BATCH_${n}_OK" "$STATUS" 2>/dev/null; then
      echo "skip CDN batch $n"
      continue
    fi
    echo "=== CDN batch $n/$total ==="
    set +e
    python3 scripts/push-product-images-tag.py --dirs di-pdp --skip-whiten --only-file "$batch" --skip-purge
    st=$?
    set -e
    echo "EXIT_CDN_${n}:$st"
    if [[ "$st" -ne 0 ]]; then
      echo "CDN_BATCH_${n}_FAIL:$st" >>"$STATUS"
      echo "CDN_BATCH_${n}_SKIP" >>"$STATUS"
    else
      echo "CDN_BATCH_${n}_OK" >>"$STATUS"
    fi
  done
else
  echo "CDN_SKIP_EMPTY" >>"$STATUS"
fi

echo "=== COMMIT / PUSH ==="
git add \
  scripts/di_common.py \
  scripts/scrape-di-women-accessories.py \
  scripts/enrich-di-women-accessories-pdp.py \
  scripts/run-di-women-accessories-pipeline.sh \
  scripts/merge-di-catalog-ko.py \
  scripts/recenter-di-women-card-holder-thumbs.py \
  src/data/categories.ts \
  src/data/brand-heroes.ts \
  src/data/di/di-catalog.json \
  src/data/di/di-catalog.ts \
  src/data/di/di-women-accessories-catalog-raw.json \
  src/data/di/di-women-accessories-leaves.json \
  src/data/di/di-women-accessories-pdp-cache.json \
  src/data/di/di-women-slg-catalog-raw.json \
  src/data/product-images-manifest.json \
  || true

if ! git diff --cached --quiet; then
  git commit -m "$(cat <<'EOF'
Add Dior womens fashion accessories under Accessories → Dior → 여성용.

Split the official GB all-accessories hub into PLP leaves and nest existing small leather goods underneath.
EOF
)"
  git push origin HEAD
else
  echo "nothing to commit"
fi

touch "$DEPLOYED"
echo "=== DONE $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
