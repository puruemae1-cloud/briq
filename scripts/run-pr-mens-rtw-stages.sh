#!/usr/bin/env bash
# Scrape Prada men's RTW in 5 stages with ~20 min rest between stages.
set -euo pipefail
cd "$(dirname "$0")/.."

STAGES=5
SLEEP_SECS=1200

for stage in $(seq 1 "$STAGES"); do
  echo "=== Prada men's RTW stage ${stage}/${STAGES} — $(date -Iseconds) ==="
  python3 scripts/scrape-pr-mens-rtw.py --stage "$stage" --stages "$STAGES"
  if [[ "$stage" -lt "$STAGES" ]]; then
    echo "Resting ${SLEEP_SECS}s (~20 min) before stage $((stage + 1))…"
    sleep "$SLEEP_SECS"
  fi
done

echo "=== Building Prada men's RTW catalog — $(date -Iseconds) ==="
python3 scripts/build-pr-catalog.py --only mens-rtw

echo "=== Verifying images ==="
python3 scripts/verify-product-images.py --brand pr || true

echo "=== Done — $(date -Iseconds) ==="
