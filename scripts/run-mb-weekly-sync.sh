#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Priority first: what's-new hubs, then remaining leaves.
PRIORITY=(
  mb-men-whats-new
  mb-women-whats-new
)

# Full leaf set from mulberry_config (order: small bags first).
LEAVES=(
  mb-women-clutches
  mb-women-mini
  mb-women-bucket
  mb-women-backpacks
  mb-women-crossbody
  mb-women-top-handle
  mb-women-totes
  mb-women-shoulder
  mb-women-bags-all
  mb-women-icons
  mb-women-travel-accessories
  mb-women-travel-holdalls
  mb-women-travel-luggage
  mb-women-travel-all
  mb-men-messenger
  mb-men-briefcases
  mb-men-backpacks
  mb-men-holdalls
  mb-men-bags-all
  mb-men-travel
  mb-men-wallets
  mb-men-keyrings
  mb-men-organisers
  mb-men-sunglasses
  mb-men-care
  mb-men-accessories-all
  mb-men-lifestyle
  mb-gifts-him
  mb-women-purses
  mb-women-lifestyle
  mb-gifts-her
  mb-gifts
  mb-men-whats-new
  mb-women-whats-new
)

run_leaf() {
  local leaf="$1"
  echo "== $leaf =="
  PYTHONUNBUFFERED=1 python3 scripts/scrape-mulberry-leaf.py --leaf "$leaf" --skip-existing || {
    echo "WARN leaf failed: $leaf"
    return 0
  }
}

echo "== Mulberry weekly: priority what's-new =="
for leaf in "${PRIORITY[@]}"; do
  run_leaf "$leaf"
done

echo "== Mulberry weekly: remaining leaves =="
for leaf in "${LEAVES[@]}"; do
  # skip if already done in priority
  skip=0
  for p in "${PRIORITY[@]}"; do
    if [[ "$leaf" == "$p" ]]; then skip=1; break; fi
  done
  if [[ "$skip" -eq 1 ]]; then continue; fi
  run_leaf "$leaf"
done

PYTHONUNBUFFERED=1 BRIQ_FAST_BUILD=0 python3 scripts/build-mb-catalog.py

# Publish any local mb-pdp folders missing from the product-images CDN tag
# (Vercel serves photos from the tag — never rely on main for PDP bytes).
python3 scripts/list-missing-pdp-on-cdn.py --dirs mb-pdp --fetch --write tmp/mb-missing-on-cdn.txt || true
if [[ -s tmp/mb-missing-on-cdn.txt ]]; then
  PYTHONUNBUFFERED=1 python3 scripts/push-product-images-tag.py \
    --dirs mb-pdp --skip-whiten --merge --skip-purge \
    --only-file tmp/mb-missing-on-cdn.txt
fi
python3 scripts/verify-catalog-images.py --brand mb --check-cdn || true
python3 scripts/refresh-homepage-rail-picks.py --fail || true

echo "OK MB weekly sync"
