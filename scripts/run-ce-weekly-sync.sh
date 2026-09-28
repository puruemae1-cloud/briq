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

# Align nav leaf IDs + backfill belts/silk/hair/SLG/jewellery from titles when
# leaf PLP scrapes missed membership (prevents empty shop chips).
python3 scripts/patch-ce-accessory-membership.py

# Guard: shop nav accessory leaves must not stay empty after sync.
python3 scripts/validate-ce-accessory-leaves.py

# Bags / shoes PLPs read slices, not the full catalogue.
python3 scripts/extract-bags-catalogs.py ce
python3 scripts/extract-shoes-catalogs.py ce

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

# Homepage rails: keep brands exclusive across category sections.
python3 scripts/refresh-homepage-rail-picks.py --fail || true

echo "OK CE weekly sync"
