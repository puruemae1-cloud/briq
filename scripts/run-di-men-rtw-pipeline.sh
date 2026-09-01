#!/usr/bin/env bash
# Dior men's RTW: 4 scrape stages (5 min pause) → merge → KO → CDN → commit/push.
# Detached-safe — chat crashes do not stop this job.
set -euo pipefail
cd "$(dirname "$0")/.."
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/Library/Caches/ms-playwright}"
export PYTHONUNBUFFERED=1
LOG=/tmp/di-men-rtw-pipeline.log
PAUSE_SEC="${PAUSE_SEC:-300}"
exec > >(tee -a "$LOG") 2>&1

echo "=== men rtw pipeline start $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

for stage in 1 2 3 4; do
  echo "=== STAGE $stage ==="
  python3 scripts/scrape-di-men-rtw.py --stage "$stage" | tee "/tmp/di-men-rtw-s${stage}.log"
  echo "EXIT_STAGE_${stage}:$?"
  if [[ "$stage" != "4" ]]; then
    echo "pause ${PAUSE_SEC}s"
    sleep "$PAUSE_SEC"
  fi
done

echo "=== MERGE ==="
python3 scripts/merge-di-catalog-ko.py | tee /tmp/di-men-rtw-merge.log
echo "EXIT_MERGE:$?"

echo "=== KO ==="
python3 scripts/check-catalog-korean.py --brand di --fail | tee /tmp/di-men-rtw-ko.log
echo "EXIT_KO:$?"

# thin ts guard
python3 - <<'PY'
from pathlib import Path
p = Path("src/data/di/di-catalog.ts")
if p.stat().st_size > 2000 or "di-catalog.json" not in p.read_text():
    p.write_text(
        "/* Auto-generated — do not edit */\n"
        'import type { Product } from "@/data/product-types";\n'
        'import data from "./di-catalog.json";\n'
        "\n"
        "/** Dior Maison + Jewelry + Bags + mens RTW catalog (JSON import keeps TS small). */\n"
        "export const diCatalogProducts = data as unknown as Product[];\n"
    )
print("ts", p.stat().st_size)
PY

echo "=== CDN only men RTW folders ==="
python3 - <<'PY'
import json
from pathlib import Path
raw = json.load(open("src/data/di/di-men-rtw-catalog-raw.json"))
folders = []
for p in raw.get("products") or []:
    imgs = p.get("images") or []
    if not imgs:
        continue
    parts = str(imgs[0]).split("/")
    if "di-pdp" in parts:
        folders.append(parts[parts.index("di-pdp") + 1])
folders = sorted(set(folders))
Path("/tmp/di-men-rtw-cdn-only.txt").write_text("\n".join(folders) + "\n")
print("cdn_folders", len(folders))
PY

python3 scripts/weekly-sync-status.py
python3 scripts/push-product-images-tag.py --dirs di-pdp --skip-whiten --only-file /tmp/di-men-rtw-cdn-only.txt | tee /tmp/di-men-rtw-cdn.log
echo "EXIT_CDN:$?"

python3 scripts/weekly-sync-status.py
git add \
  .cursor/rules/dior-catalog.mdc \
  scripts/di_common.py \
  scripts/di_size_charts.py \
  scripts/merge-di-catalog-ko.py \
  scripts/scrape-di-men-rtw.py \
  scripts/run-di-men-rtw-pipeline.sh \
  src/data/brand-heroes.ts \
  src/data/categories.ts \
  src/data/di/di-men-rtw-catalog-raw.json \
  src/data/di/di-men-rtw-leaves.json \
  src/data/di/di-catalog.json \
  src/data/di/di-catalog.ts \
  src/data/product-images-manifest.json || true

if ! git diff --cached --quiet; then
  git commit -m "$(cat <<'EOF'
Add Dior mens ready-to-wear under Luxury / Dior / men (~549 SKUs).

Official by-category leaves with Korean PDP copy and Dior GB size charts; publish di-pdp images on the product-images CDN tag.
EOF
)"
  git push origin main
fi

python3 - <<'PY'
import json
from pathlib import Path
raw = json.load(open("src/data/di/di-men-rtw-catalog-raw.json"))
cat = json.load(open("src/data/di/di-catalog.json"))
leaf = {
    "di-mens",
    "di-men-rtw-all",
    "di-men-tshirts-polos",
    "di-men-shirts",
    "di-men-knitwear-sweatshirts",
    "di-men-trousers-shorts",
    "di-men-denim",
    "di-men-beachwear",
    "di-men-outerwear",
    "di-men-tailored-jackets",
    "di-men-leather",
    "di-men-suits-tuxedos",
}
n = sum(1 for p in cat if leaf.intersection(p.get("diCollections") or []))
charts = sum(1 for p in cat if leaf.intersection(p.get("diCollections") or []) and p.get("sizeChart"))
print(
    "raw",
    len(raw.get("products") or []),
    "catalog_men_rtw",
    n,
    "with_chart",
    charts,
    "ts",
    Path("src/data/di/di-catalog.ts").stat().st_size,
)
PY

echo "PIPELINE_DONE $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee /tmp/di-men-rtw-READY
git rev-parse --short HEAD | tee -a /tmp/di-men-rtw-READY
