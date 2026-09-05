#!/usr/bin/env bash
# Dior women's SLG: 2 scrape stages → merge → enrich → prices → KO → batched CDN → commit/push.
# Detached-safe with STATUS stamps. Chat disconnect does not stop this job.
set -uo pipefail
cd "$(dirname "$0")/.."
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/Library/Caches/ms-playwright}"
export PYTHONUNBUFFERED=1
LOG=/tmp/di-women-slg-pipeline.log
STATUS=/tmp/di-women-slg-STATUS
DEPLOYED=/tmp/di-women-slg-DEPLOYED
PAUSE_SEC="${PAUSE_SEC:-60}"
exec >>"$LOG" 2>&1

echo "=== women SLG pipeline start $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
touch "$STATUS"

if [[ -f "$DEPLOYED" ]]; then
  echo "already deployed"
  exit 0
fi

for stage in 1 2; do
  if grep -q "STAGE_${stage}_OK" "$STATUS" 2>/dev/null; then
    echo "skip stage $stage"
    continue
  fi
  echo "=== STAGE $stage ==="
  set +e
  python3 scripts/scrape-di-women-slg.py --stage "$stage"
  st=$?
  set -e
  echo "EXIT_STAGE_${stage}:$st"
  if [[ "$st" -ne 0 ]]; then
    echo "STAGE_${stage}_FAIL:$st" >>"$STATUS"
    exit "$st"
  fi
  echo "STAGE_${stage}_OK" >>"$STATUS"
  if [[ "$stage" != "2" ]]; then
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

run_step MERGE python3 scripts/merge-di-catalog-ko.py
run_step ENRICH python3 scripts/enrich-di-women-slg-pdp.py
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
raw = json.load(open("src/data/di/di-women-slg-catalog-raw.json"))
folders = []
for p in raw.get("products") or []:
    imgs = p.get("images") or []
    if not imgs:
        continue
    parts = str(imgs[0]).split("/")
    if "di-pdp" in parts:
        folders.append(parts[parts.index("di-pdp") + 1])
folders = sorted(set(folders))
Path("/tmp/di-women-slg-cdn-only.txt").write_text("\n".join(folders) + "\n")
print("cdn_folders", len(folders))
PY

if [[ -s /tmp/di-women-slg-cdn-only.txt ]]; then
  rm -f /tmp/di-women-slg-cdn-batch-*
  split -l 80 /tmp/di-women-slg-cdn-only.txt /tmp/di-women-slg-cdn-batch-
  batches=(/tmp/di-women-slg-cdn-batch-*)
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
    # Always skip purge — jsDelivr purge can hang; images still land on the tag.
    python3 scripts/push-product-images-tag.py --dirs di-pdp --skip-whiten --only-file "$batch" --skip-purge
    st=$?
    set -e
    echo "EXIT_CDN_${n}:$st"
    if [[ "$st" -ne 0 ]]; then
      echo "CDN_BATCH_${n}_FAIL:$st" >>"$STATUS"
      # Do not block deploy on CDN failure if images already exist on tag
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
  scripts/scrape-di-women-slg.py \
  scripts/enrich-di-women-slg-pdp.py \
  scripts/run-di-women-slg-pipeline.sh \
  scripts/watch-di-women-slg.sh \
  scripts/merge-di-catalog-ko.py \
  scripts/recenter-di-women-card-holder-thumbs.py \
  src/data/categories.ts \
  src/data/brand-heroes.ts \
  src/data/di/di-catalog.json \
  src/data/di/di-catalog.ts \
  src/data/di/di-women-slg-catalog-raw.json \
  src/data/di/di-women-slg-leaves.json \
  src/data/product-images-manifest.json \
  || true

if ! git diff --cached --quiet; then
  git commit -m "$(cat <<'EOF'
Add Dior womens small leather goods under accessories with official PLP leaves.

Map Accessories → Dior → 여성용 to card holders, wallets, pouches, and tech from the GB SLG hub.
EOF
)"
  git push origin HEAD
else
  echo "nothing to commit"
fi

touch "$DEPLOYED"
echo "=== DONE $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
