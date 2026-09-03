#!/usr/bin/env bash
# Finish Dior women RTW: KO stamp → CDN batches → commit/push → DEPLOYED.
# Idempotent; safe under nohup / chat disconnect.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONUNBUFFERED=1
LOG=/tmp/di-women-rtw-finish.log
STATUS=/tmp/di-women-rtw-STATUS
DEPLOYED=/tmp/di-women-rtw-DEPLOYED
exec >>"$LOG" 2>&1

echo "=== finish start $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
touch "$STATUS"

if [[ -f "$DEPLOYED" ]]; then
  echo "already deployed"
  exit 0
fi

echo "=== KO verify ==="
if python3 scripts/check-catalog-korean.py --brand di --fail; then
  grep -q 'KO_OK' "$STATUS" || echo KO_OK >>"$STATUS"
else
  echo "KO still failing — abort finish"
  exit 1
fi

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

echo "=== CDN folder list ==="
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
  rm -f /tmp/di-women-rtw-cdn-batch-*
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
    echo "=== CDN batch $n/$total $(wc -l < "$batch" | tr -d ' ') folders ==="
    skip_purge=--skip-purge
    if [[ "$n" -eq "$total" ]]; then
      skip_purge=
    fi
    set +e
    python3 scripts/push-product-images-tag.py --dirs di-pdp --skip-whiten --only-file "$batch" $skip_purge
    st=$?
    set -e
    echo "EXIT_CDN_${n}:$st"
    if [[ "$st" -ne 0 ]]; then
      echo "CDN_BATCH_${n}_FAIL:$st" >>"$STATUS"
      exit "$st"
    fi
    echo "CDN_BATCH_${n}_OK" >>"$STATUS"
  done
fi

echo "=== COMMIT / PUSH ==="
git add \
  scripts/di_common.py \
  scripts/di_size_charts.py \
  scripts/scrape-di-women-rtw.py \
  scripts/enrich-di-women-rtw-pdp.py \
  scripts/run-di-women-rtw-pipeline.sh \
  scripts/watch-di-women-rtw.sh \
  scripts/finish-di-women-rtw.sh \
  scripts/merge-di-catalog-ko.py \
  src/data/categories.ts \
  src/data/brand-heroes.ts \
  src/data/di/di-catalog.json \
  src/data/di/di-catalog.ts \
  src/data/di/di-women-rtw-catalog-raw.json \
  src/data/di/di-women-rtw-leaves.json \
  src/data/di/di-women-rtw-pdp-cache.json \
  src/data/di/di-translate-cache.json \
  src/data/product-images-manifest.json \
  || true

if ! git diff --cached --quiet; then
  git commit -m "$(cat <<'EOF'
Add Dior womens ready-to-wear under luxury Dior with official PLP leaves.

Scrape GB women RTW by category, enrich Korean PDPs with variants and FR size charts, and keep GBP→KRW pricing gated.
EOF
)"
  git push origin HEAD
else
  echo "nothing to commit"
fi

touch "$DEPLOYED"
echo "=== DONE $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
