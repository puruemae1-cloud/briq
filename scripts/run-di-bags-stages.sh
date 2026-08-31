#!/usr/bin/env bash
# Run Dior women's bags scrape in 3 stages with 5-minute pauses.
# Safe to re-run — raw JSON is checkpointed every ~15 products.
set -euo pipefail
cd "$(dirname "$0")/.."
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/Library/Caches/ms-playwright}"
export PYTHONUNBUFFERED=1
LOGDIR="${TMPDIR:-/tmp}"
PAUSE_SEC="${PAUSE_SEC:-300}"

for stage in 1 2 3; do
  echo "=== STAGE $stage $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" | tee -a "$LOGDIR/di-bags-all.log"
  python3 scripts/scrape-di-bags.py --stage "$stage" 2>&1 | tee "$LOGDIR/di-bags-s${stage}.log"
  echo "EXIT_STAGE_${stage}:$?" | tee -a "$LOGDIR/di-bags-all.log"
  if [[ "$stage" != "3" ]]; then
    echo "pause ${PAUSE_SEC}s before stage $((stage+1))..." | tee -a "$LOGDIR/di-bags-all.log"
    sleep "$PAUSE_SEC"
  fi
done
echo "ALL_STAGES_DONE $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOGDIR/di-bags-all.log"
