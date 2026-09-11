#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Full Celine GB catalogue — include accessories/jewellery/SLG so weekly sync
# does not leave Access Denied / empty leaves frozen forever.
FAMILIES=(
  ce-men-rtw
  ce-men-bags
  ce-men-shoes
  ce-men-accessories
  ce-men-jewellery
  ce-men-sunglasses
  ce-men-slg
  ce-women-rtw
  ce-women-bags
  ce-women-shoes
  ce-women-accessories
  ce-women-jewellery
  ce-women-sunglasses
  ce-women-slg
)

for fam in "${FAMILIES[@]}"; do
  echo "== $fam =="
  python3 scripts/scrape-celine-family.py --family "$fam"
done

# Heal any legacy AVAILABLE-NOW-only false sold-outs, then refresh from SFCC.
python3 scripts/repair-ce-availability.py
python3 scripts/refresh-ce-stock-sfcc.py || true

python3 scripts/build-ce-catalog.py

# Keep CDN placeholder present so sold-out / incomplete rows never 404.
if [[ -f public/products/ce-pdp/placeholder.jpg ]]; then
  PYTHONUNBUFFERED=1 python3 scripts/push-product-images-tag.py \
    --dirs ce-pdp --skip-whiten --merge --skip-purge \
    --only placeholder || true
fi

echo "OK CE weekly sync"
