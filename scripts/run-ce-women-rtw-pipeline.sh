#!/usr/bin/env bash
# Celine women RTW: scrape → build catalog.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
LIMIT="${1:-0}"

python3 scripts/scrape-celine-family.py --family ce-women-rtw --limit "$LIMIT"
python3 scripts/build-ce-catalog.py
echo "OK ce-women-rtw pipeline"
