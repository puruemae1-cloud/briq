#!/usr/bin/env bash
# Overnight AllSaints import — smallest families first, then build + CDN.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/scripts:${PYTHONPATH:-}"
export PYTHONUNBUFFERED=1
LOG="$ROOT/tmp/al-pipeline.log"
mkdir -p "$ROOT/tmp"

exec > >(tee -a "$LOG") 2>&1
echo "==== AL pipeline start $(date -u +%Y-%m-%dT%H:%M:%SZ) ===="

FAMILIES=(
  al-men-accessories
  al-men-shoes
  al-women-accessories
  al-women-shoes
  al-men-rtw
  al-women-rtw
)

for fam in "${FAMILIES[@]}"; do
  echo "== scrape $fam =="
  python3 scripts/scrape-al-family.py --family "$fam" || echo "WARN scrape $fam failed"
  echo "== retag $fam =="
  python3 scripts/retag-al-leaves.py --family "$fam" || echo "WARN retag $fam failed"
done

echo "== build catalog =="
python3 scripts/build-al-catalog.py

echo "== KO QA / retranslate =="
for i in 1 2 3 4 5; do
  python3 scripts/retranslate-al-ko.py --category all || true
  if python3 scripts/check-al-korean.py --fail --max-bad 0; then
    break
  fi
  echo "WARN KO attempt $i"
done

echo "== CDN missing images =="
python3 scripts/list-missing-pdp-on-cdn.py --dirs al-pdp --fetch --write tmp/al-missing-on-cdn.txt || true
if [[ -s tmp/al-missing-on-cdn.txt ]]; then
  python3 scripts/push-product-images-tag.py --dirs al-pdp --only-file tmp/al-missing-on-cdn.txt --skip-whiten || true
fi

echo "==== AL pipeline done $(date -u +%Y-%m-%dT%H:%M:%SZ) ===="
