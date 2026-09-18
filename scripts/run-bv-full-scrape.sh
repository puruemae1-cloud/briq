#!/usr/bin/env bash
# Resume-friendly Bottega Veneta full scrape (small hubs first).
# Scrapes only — catalog Korean build runs once at the end (mid-builds are too slow).
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=scripts
export PYTHONUNBUFFERED=1
unset BV_LIMIT

HUBS=(
  women-travel
  men-travel
  home
  fragrances
  men-jewellery
  women-jewellery
  men-eyewear
  women-eyewear
  men-accessories
  women-accessories
  women-wallets
  men-wallets
  men-shoes
  women-shoes
  men-bags
  women-bags
  men-clothing
  women-clothing
  gifts
)

LOG="${1:-/tmp/briq-bv-full-scrape.log}"
echo "==== BV full scrape start $(date -u +%Y-%m-%dT%H:%M:%SZ) ====" | tee -a "$LOG"

hub_done() {
  local hub="$1"
  local f="src/data/bv/bv-${hub}-catalog-raw.json"
  [[ -f "$f" ]] || return 1
  python3 - "$f" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
prods = d.get("products") or []
lc = d.get("leafCounts") or {}
if not prods or not lc:
    raise SystemExit(1)
# Done when every leaf scraped count equals official (when official known)
for v in lc.values():
    off = v.get("official")
    sc = v.get("scraped")
    if off is not None and sc != off:
        raise SystemExit(1)
raise SystemExit(0)
PY
}

fail=0
for hub in "${HUBS[@]}"; do
  if hub_done "$hub"; then
    echo "SKIP hub=$hub (raw complete)" | tee -a "$LOG"
    continue
  fi
  echo "" | tee -a "$LOG"
  echo "#### HUB $hub $(date -u +%Y-%m-%dT%H:%M:%SZ) ####" | tee -a "$LOG"
  if python3 -u scripts/scrape-bv-hub.py --hub "$hub" >>"$LOG" 2>&1; then
    echo "OK hub=$hub" | tee -a "$LOG"
  else
    echo "FAIL hub=$hub (continue)" | tee -a "$LOG"
    fail=$((fail + 1))
  fi
done

echo "==== scrape phase done fails=$fail; building catalog $(date -u +%Y-%m-%dT%H:%M:%SZ) ====" | tee -a "$LOG"
python3 -u scripts/build-bv-catalog.py >>"$LOG" 2>&1 || fail=$((fail + 1))
echo "==== BV full scrape+build done fails=$fail $(date -u +%Y-%m-%dT%H:%M:%SZ) ====" | tee -a "$LOG"
exit "$fail"
