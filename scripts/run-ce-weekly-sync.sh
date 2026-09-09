#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
for fam in ce-men-rtw ce-men-bags ce-men-shoes ce-women-rtw ce-women-bags ce-women-shoes; do
  echo "== $fam =="
  python3 scripts/scrape-celine-family.py --family "$fam"
done
python3 scripts/build-ce-catalog.py
echo "OK CE weekly sync"
