#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/scripts:${PYTHONPATH:-}"

# Smallest families first (bags → shoes → accessories → RTW).
FAMILIES=(
  ys-men-bags
  ys-men-shoes
  ys-men-accessories
  ys-men-slg
  ys-women-jewelry
  ys-women-accessories
  ys-women-slg
  ys-women-shoes
  ys-women-rtw
  ys-men-rtw
  ys-women-bags
)

for fam in "${FAMILIES[@]}"; do
  echo "== $fam =="
  python3 scripts/scrape-ys-family.py --family "$fam" || echo "WARN $fam scrape failed"
done

python3 scripts/build-ys-catalog.py

python3 scripts/list-missing-pdp-on-cdn.py --dirs ys-pdp --fetch --write tmp/ys-missing-on-cdn.txt || true
if [[ -s tmp/ys-missing-on-cdn.txt ]]; then
  PYTHONUNBUFFERED=1 python3 scripts/push-product-images-tag.py \
    --dirs ys-pdp --skip-whiten --merge --skip-purge \
    --only-file tmp/ys-missing-on-cdn.txt || true
fi

python3 scripts/refresh-homepage-rail-picks.py --fail || true
echo "OK YS weekly sync"
