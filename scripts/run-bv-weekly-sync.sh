#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/scripts:${PYTHONPATH:-}"
export PYTHONUNBUFFERED=1
export BV_REFRESH_STOCK=1

python3 -u scripts/weekly-bv-stock-sync.py

# Local image guard — never leave catalogue pointing at missing PDP files.
python3 scripts/verify-product-images.py --brand bv --all-images

echo "OK BV weekly sync (local images verified; CDN push/verify is CI)"
