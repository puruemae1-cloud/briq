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

# Fill sparse DETAILS / CARE from SFCC longDescription (empty image-only rows).
python3 scripts/enrich-ce-pdp-copy-sfcc.py || true

python3 scripts/build-ce-catalog.py

# Backfill any rows still on placeholder, then publish local PDP folders that
# are not yet on the product-images CDN tag (prevents broken <img> in shop).
python3 scripts/repair-ce-missing-images.py --category-hint all || true
python3 scripts/list-missing-pdp-on-cdn.py --dirs ce-pdp --fetch --write tmp/ce-missing-on-cdn.txt || true
if [[ -s tmp/ce-missing-on-cdn.txt ]]; then
  PYTHONUNBUFFERED=1 python3 scripts/push-product-images-tag.py \
    --dirs ce-pdp --skip-whiten --merge --skip-purge \
    --only-file tmp/ce-missing-on-cdn.txt
fi
python3 scripts/verify-catalog-images.py --brand ce --check-cdn || true

echo "OK CE weekly sync"
