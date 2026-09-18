#!/usr/bin/env bash
# Run only given BV hubs. Skips hubs whose raw has ALL expected leaves complete.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=scripts PYTHONUNBUFFERED=1
unset BV_LIMIT
LOG="${1:-/tmp/briq-bv-chunk.log}"
shift || true
HUBS=("$@")
if [[ ${#HUBS[@]} -eq 0 ]]; then
  HUBS=(women-bags men-clothing women-clothing gifts)
fi

hub_done() {
  local hub="$1"
  PYTHONPATH=scripts python3 - "$hub" <<'PY'
import json, sys
from pathlib import Path
from bv_config import HUBS_BY_ID
hub = sys.argv[1]
h = HUBS_BY_ID[hub]
path = Path("src/data/bv") / h["out"]
if not path.exists():
    raise SystemExit(1)
d = json.loads(path.read_text())
prods = d.get("products") or []
lc = d.get("leafCounts") or {}
expected = [leaf["id"] for leaf in h["leaves"]]
if not prods or not expected:
    raise SystemExit(1)
for lid in expected:
    v = lc.get(lid)
    if not v:
        raise SystemExit(1)
    off, sc = v.get("official"), v.get("scraped")
    if off is not None and sc != off:
        raise SystemExit(1)
raise SystemExit(0)
PY
}

echo "==== BV chunk $(date -u +%Y-%m-%dT%H:%M:%SZ) hubs=${HUBS[*]} ====" | tee -a "$LOG"
fail=0
for hub in "${HUBS[@]}"; do
  if hub_done "$hub"; then
    echo "SKIP $hub (all leaves complete)" | tee -a "$LOG"
    continue
  fi
  echo "#### $hub $(date -u +%Y-%m-%dT%H:%M:%SZ) ####" | tee -a "$LOG"
  if python3 -u scripts/scrape-bv-hub.py --hub "$hub" >>"$LOG" 2>&1; then
    echo "OK $hub" | tee -a "$LOG"
  else
    echo "FAIL $hub" | tee -a "$LOG"
    fail=$((fail+1))
  fi
done
echo "==== chunk done fails=$fail $(date -u +%Y-%m-%dT%H:%M:%SZ) ====" | tee -a "$LOG"
exit $fail
