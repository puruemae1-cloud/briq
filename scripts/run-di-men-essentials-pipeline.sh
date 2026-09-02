#!/usr/bin/env bash
# Dior Men's Essentials hub → route into shoes / RTW / accessories → merge → KO → CDN.
set -euo pipefail
cd "$(dirname "$0")/.."
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/Library/Caches/ms-playwright}"
export PYTHONUNBUFFERED=1
LOG=/tmp/di-men-essentials-pipeline.log
exec > >(tee -a "$LOG") 2>&1

echo "=== men essentials pipeline start $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

echo "=== SCRAPE ==="
python3 scripts/scrape-di-men-essentials.py | tee /tmp/di-men-essentials-scrape.log
echo "EXIT_SCRAPE:$?"

echo "=== MERGE ==="
python3 scripts/merge-di-catalog-ko.py | tee /tmp/di-men-essentials-merge.log
echo "EXIT_MERGE:$?"

python3 scripts/fix-di-essentials-routing.py | tee /tmp/di-men-essentials-routing.log
echo "EXIT_ROUTING:$?"

python3 scripts/fix-di-catalog-prices.py --check | tee /tmp/di-men-essentials-prices.log
echo "EXIT_PRICES:$?"

echo "=== KO ==="
python3 scripts/check-catalog-korean.py --brand di --fail | tee /tmp/di-men-essentials-ko.log
echo "EXIT_KO:$?"

python3 - <<'PY'
from pathlib import Path
p = Path("src/data/di/di-catalog.ts")
if p.stat().st_size > 2000 or "di-catalog.json" not in p.read_text():
    p.write_text(
        "/* Auto-generated — do not edit */\n"
        'import type { Product } from "@/data/product-types";\n'
        'import data from "./di-catalog.json";\n'
        "\n"
        "/** Dior Maison + Jewelry + Bags catalog (JSON import keeps TS small). */\n"
        "export const diCatalogProducts = data as unknown as Product[];\n"
    )
print("ts", p.stat().st_size)
PY

echo "=== CDN only essentials folders ==="
python3 - <<'PY'
import json
from pathlib import Path
raw = json.load(open("src/data/di/di-men-essentials-catalog-raw.json"))
folders = []
for p in raw.get("products") or []:
    imgs = p.get("images") or []
    if not imgs:
        continue
    parts = str(imgs[0]).split("/")
    if "di-pdp" in parts:
        folders.append(parts[parts.index("di-pdp") + 1])
folders = sorted(set(folders))
Path("/tmp/di-men-essentials-cdn-only.txt").write_text("\n".join(folders) + "\n")
print("cdn_folders", len(folders))
print("buckets", raw.get("bucketCounts"))
PY

if [[ -s /tmp/di-men-essentials-cdn-only.txt ]]; then
  python3 scripts/push-product-images-tag.py --dirs di-pdp --skip-whiten --only-file /tmp/di-men-essentials-cdn-only.txt | tee /tmp/di-men-essentials-cdn.log
  echo "EXIT_CDN:$?"
else
  echo "EXIT_CDN:0 (no folders)"
fi

echo "=== DONE $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
