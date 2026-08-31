#!/usr/bin/env bash
# Continue Dior bags pipeline after an in-flight stage-1 scrape.
# Usage: WAIT_PID=<stage1_pid> bash scripts/continue-di-bags-pipeline.sh
set -euo pipefail
cd "$(dirname "$0")/.."
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/Library/Caches/ms-playwright}"
export PYTHONUNBUFFERED=1
LOG=/tmp/di-bags-pipeline.log
PAUSE_SEC="${PAUSE_SEC:-300}"
WAIT_PID="${WAIT_PID:-}"

exec >>"$LOG" 2>&1
echo "=== pipeline start $(date -u +%Y-%m-%dT%H:%M:%SZ) WAIT_PID=$WAIT_PID ==="

if [[ -n "$WAIT_PID" ]]; then
  echo "waiting for pid $WAIT_PID"
  while kill -0 "$WAIT_PID" 2>/dev/null; do sleep 20; done
  echo "pid $WAIT_PID exited"
fi

# If stage1 log has no DONE, and raw missing/thin, run stage1
RAW=src/data/di/di-bags-women-catalog-raw.json
need_s1=0
if [[ ! -f "$RAW" ]]; then
  need_s1=1
else
  n=$(python3 -c "import json; print(len(json.load(open('$RAW')).get('products') or []))")
  echo "raw_count=$n"
  # stage1 leaves should contribute a few hundred
  if [[ "$n" -lt 50 ]]; then need_s1=1; fi
fi

if [[ "$need_s1" -eq 1 ]]; then
  echo "=== STAGE 1 ==="
  python3 scripts/scrape-di-bags.py --stage 1 | tee /tmp/di-bags-s1.log
  echo "EXIT_STAGE_1:$?"
fi

echo "pause ${PAUSE_SEC}s before stage 2"
sleep "$PAUSE_SEC"

echo "=== STAGE 2 ==="
python3 scripts/scrape-di-bags.py --stage 2 | tee /tmp/di-bags-s2.log
echo "EXIT_STAGE_2:$?"

echo "pause ${PAUSE_SEC}s before stage 3"
sleep "$PAUSE_SEC"

echo "=== STAGE 3 ==="
python3 scripts/scrape-di-bags.py --stage 3 | tee /tmp/di-bags-s3.log
echo "EXIT_STAGE_3:$?"

echo "=== MERGE ==="
python3 scripts/merge-di-catalog-ko.py | tee /tmp/di-bags-merge.log
echo "EXIT_MERGE:$?"

echo "=== KO CHECK ==="
python3 scripts/check-catalog-korean.py --brand di --fail | tee /tmp/di-bags-ko.log
echo "EXIT_KO:$?"

echo "=== CDN di-pdp ==="
python3 scripts/push-product-images-tag.py --dirs di-pdp | tee /tmp/di-bags-cdn.log
echo "EXIT_CDN:$?"

echo "=== PIPELINE_DONE $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
python3 - <<'PY'
import json
from pathlib import Path
raw=json.load(open('src/data/di/di-bags-women-catalog-raw.json'))
cat=json.load(open('src/data/di/di-catalog.json'))
bags=[p for p in cat if 'di-bags-womens' in (p.get('diCollections') or []) or (p.get('subcategory') or '').startswith('di-') and 'bag' in (p.get('subcategory') or '')]
icons=sum(1 for p in cat if any(c.startswith('di-') and ('bag' in c or c in ('di-handbags','di-clutches','di-tote-bags','di-mini-bags','di-bucket-bags','di-crossbody-shoulder-bags','di-accessorize-bag','di-bags-all','di-bags-womens','dior-bags')) for c in (p.get('diCollections') or [])))
print('raw', len(raw.get('products') or []))
print('catalog_bagish', icons)
print('di-ts', Path('src/data/di/di-catalog.ts').stat().st_size)
PY
