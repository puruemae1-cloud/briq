#!/usr/bin/env bash
# Dior men's SLG: 3 scrape stages (5 min pause) → merge → enrich → KO → CDN → commit/push.
set -euo pipefail
cd "$(dirname "$0")/.."
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/Library/Caches/ms-playwright}"
export PYTHONUNBUFFERED=1
LOG=/tmp/di-men-slg-pipeline.log
PAUSE_SEC="${PAUSE_SEC:-300}"
exec > >(tee -a "$LOG") 2>&1

echo "=== men SLG pipeline start $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

for stage in 1 2 3; do
  echo "=== STAGE $stage ==="
  python3 scripts/scrape-di-men-slg.py --stage "$stage" | tee "/tmp/di-men-slg-s${stage}.log"
  echo "EXIT_STAGE_${stage}:$?"
  if [[ "$stage" != "3" ]]; then
    echo "pause ${PAUSE_SEC}s"
    sleep "$PAUSE_SEC"
  fi
done

echo "=== MERGE ==="
python3 scripts/merge-di-catalog-ko.py | tee /tmp/di-men-slg-merge.log
echo "EXIT_MERGE:$?"

echo "=== ENRICH ==="
python3 scripts/enrich-di-men-slg-pdp.py | tee /tmp/di-men-slg-enrich.log
echo "EXIT_ENRICH:$?"

echo "=== KO ==="
python3 scripts/check-catalog-korean.py --brand di --fail | tee /tmp/di-men-slg-ko.log
echo "EXIT_KO:$?"

echo "=== IMAGES ==="
python3 scripts/check-di-image-integrity.py | tee /tmp/di-men-slg-images.log
echo "EXIT_IMAGES:$?"

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

echo "=== CDN only men SLG folders ==="
python3 - <<'PY'
import json
from pathlib import Path
raw = json.load(open("src/data/di/di-men-slg-catalog-raw.json"))
folders = []
for p in raw.get("products") or []:
    imgs = p.get("images") or []
    if not imgs:
        continue
    parts = str(imgs[0]).split("/")
    if "di-pdp" in parts:
        folders.append(parts[parts.index("di-pdp") + 1])
folders = sorted(set(folders))
Path("/tmp/di-men-slg-cdn-only.txt").write_text("\n".join(folders) + "\n")
print("cdn_folders", len(folders))
PY

python3 scripts/push-product-images-tag.py --dirs di-pdp --skip-whiten --only-file /tmp/di-men-slg-cdn-only.txt | tee /tmp/di-men-slg-cdn.log
echo "EXIT_CDN:$?"

echo "=== DONE $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
