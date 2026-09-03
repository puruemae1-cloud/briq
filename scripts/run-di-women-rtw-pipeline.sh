#!/usr/bin/env bash
# Dior women's RTW: 4 scrape stages → merge → enrich → price check → KO → batched CDN → commit/push.
# Detached-safe — chat crashes do not stop this job. Resume via STATUS stamps.
set -euo pipefail
cd "$(dirname "$0")/.."
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/Library/Caches/ms-playwright}"
export PYTHONUNBUFFERED=1
LOG=/tmp/di-women-rtw-pipeline.log
STATUS=/tmp/di-women-rtw-STATUS
PAUSE_SEC="${PAUSE_SEC:-120}"
exec > >(tee -a "$LOG") 2>&1

echo "=== women rtw pipeline start $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
touch "$STATUS"

for stage in 1 2 3 4; do
  if grep -q "STAGE_${stage}_OK" "$STATUS" 2>/dev/null; then
    echo "skip stage $stage (already done)"
    continue
  fi
  echo "=== STAGE $stage ==="
  set +e
  python3 scripts/scrape-di-women-rtw.py --stage "$stage" | tee "/tmp/di-women-rtw-s${stage}.log"
  st=$?
  set -e
  echo "EXIT_STAGE_${stage}:$st"
  if [[ "$st" -ne 0 ]]; then
    echo "STAGE_${stage}_FAIL:$st" >> "$STATUS"
    exit "$st"
  fi
  echo "STAGE_${stage}_OK" >> "$STATUS"
  if [[ "$stage" != "4" ]]; then
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
    echo "${stamp}_FAIL:$st" >> "$STATUS"
    exit "$st"
  fi
  echo "${stamp}_OK" >> "$STATUS"
}

run_step MERGE python3 scripts/merge-di-catalog-ko.py
run_step ENRICH python3 scripts/enrich-di-women-rtw-pdp.py --translate
run_step PRICES python3 scripts/fix-di-catalog-prices.py --check
run_step KO python3 scripts/check-catalog-korean.py --brand di --fail

python3 - <<'PY'
from pathlib import Path
p = Path("src/data/di/di-catalog.ts")
if p.stat().st_size > 2000 or "di-catalog.json" not in p.read_text():
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

echo "=== CDN only women RTW folders ==="
python3 - <<'PY'
import json
from pathlib import Path
raw = json.load(open("src/data/di/di-women-rtw-catalog-raw.json"))
folders = []
for p in raw.get("products") or []:
    imgs = p.get("images") or []
    if not imgs:
        continue
    parts = str(imgs[0]).split("/")
    if "di-pdp" in parts:
        folders.append(parts[parts.index("di-pdp") + 1])
folders = sorted(set(folders))
Path("/tmp/di-women-rtw-cdn-only.txt").write_text("\n".join(folders) + "\n")
print("cdn_folders", len(folders))
PY

if [[ -s /tmp/di-women-rtw-cdn-only.txt ]]; then
  split -l 80 /tmp/di-women-rtw-cdn-only.txt /tmp/di-women-rtw-cdn-batch-
  batches=(/tmp/di-women-rtw-cdn-batch-*)
  total=${#batches[@]}
  n=0
  for batch in "${batches[@]}"; do
    [[ -f "$batch" ]] || continue
    n=$((n + 1))
    if grep -q "CDN_BATCH_${n}_OK" "$STATUS" 2>/dev/null; then
      echo "skip CDN batch $n"
      continue
    fi
    echo "=== CDN batch $n/$total $(wc -l < "$batch") folders ==="
    skip_purge=--skip-purge
    if [[ "$n" -eq "$total" ]]; then
      skip_purge=
    fi
    python3 scripts/push-product-images-tag.py --dirs di-pdp --skip-whiten --only-file "$batch" $skip_purge \
      | tee -a /tmp/di-women-rtw-cdn.log
    echo "CDN_BATCH_${n}_OK" >> "$STATUS"
  done
fi

echo "=== COMMIT / PUSH ==="
git add \
  scripts/di_common.py \
  scripts/di_size_charts.py \
  scripts/scrape-di-women-rtw.py \
  scripts/enrich-di-women-rtw-pdp.py \
  scripts/run-di-women-rtw-pipeline.sh \
  scripts/merge-di-catalog-ko.py \
  src/data/categories.ts \
  src/data/brand-heroes.ts \
  src/data/di/di-catalog.json \
  src/data/di/di-catalog.ts \
  src/data/di/di-women-rtw-catalog-raw.json \
  src/data/di/di-women-rtw-leaves.json \
  || true
if ! git diff --cached --quiet; then
  git commit -m "$(cat <<'EOF'
Add Dior womens ready-to-wear under luxury Dior with official PLP leaves.

Scrape GB women RTW by category, enrich Korean PDPs with variants and FR size charts, and keep GBP→KRW pricing gated.
EOF
)"
  git push origin HEAD
fi

touch /tmp/di-women-rtw-DEPLOYED
echo "=== DONE $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
