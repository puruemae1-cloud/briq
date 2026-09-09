#!/usr/bin/env bash
# Vivienne Westwood women bags: scrape → build catalog.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
LIMIT="${1:-0}"

python3 scripts/scrape-vw-family.py --family vw-women-bags --limit "$LIMIT"
python3 scripts/build-vw-catalog.py
echo "OK vw-women-bags pipeline"
