#!/usr/bin/env bash
# Durable Saint Laurent scrape+build orchestrator (safe to re-run / resume).
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/scripts:${PYTHONPATH:-}"
mkdir -p tmp src/data/ys

LOG=tmp/ys-pipeline.log
STATE=tmp/ys-pipeline-state.txt
DONE=tmp/ys-pipeline-DONE

# Smallest first.
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

echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) pipeline start" | tee -a "$LOG"
rm -f "$DONE"

for fam in "${FAMILIES[@]}"; do
  echo "$fam" > "$STATE"
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) == $fam ==" | tee -a "$LOG"
  # Retry scrape up to 3 times (bot challenges / network).
  ok=0
  for attempt in 1 2 3; do
    if PYTHONUNBUFFERED=1 python3 scripts/scrape-ys-family.py --family "$fam" >>"$LOG" 2>&1; then
      ok=1
      break
    fi
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) WARN $fam attempt $attempt failed; sleep 20" | tee -a "$LOG"
    sleep 20
  done
  if [[ $ok -ne 1 ]]; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) ERROR $fam scrape failed after retries" | tee -a "$LOG"
    continue
  fi
  PYTHONUNBUFFERED=1 python3 scripts/build-ys-catalog.py >>"$LOG" 2>&1 || true
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) built after $fam" | tee -a "$LOG"
done

PYTHONUNBUFFERED=1 python3 scripts/build-ys-catalog.py >>"$LOG" 2>&1
echo OK > "$DONE"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) pipeline DONE" | tee -a "$LOG"
