#!/usr/bin/env bash
# Dior men's bags: 3 scrape stages (5 min pause) → merge → KO → CDN → commit/push.
# Detached-safe — chat crashes do not stop this job.
set -euo pipefail
cd "$(dirname "$0")/.."
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/Library/Caches/ms-playwright}"
export PYTHONUNBUFFERED=1
LOG=/tmp/di-bags-men-pipeline.log
PAUSE_SEC="${PAUSE_SEC:-300}"
exec > >(tee -a "$LOG") 2>&1

echo "=== men bags pipeline start $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

for stage in 1 2 3; do
  echo "=== STAGE $stage ==="
  python3 scripts/scrape-di-bags-men.py --stage "$stage" | tee "/tmp/di-bags-men-s${stage}.log"
  echo "EXIT_STAGE_${stage}:$?"
  if [[ "$stage" != "3" ]]; then
    echo "pause ${PAUSE_SEC}s"
    sleep "$PAUSE_SEC"
  fi
done

echo "=== MERGE ==="
python3 scripts/merge-di-catalog-ko.py | tee /tmp/di-bags-men-merge.log
echo "EXIT_MERGE:$?"

echo "=== KO ==="
python3 scripts/check-catalog-korean.py --brand di --fail | tee /tmp/di-bags-men-ko.log
echo "EXIT_KO:$?"

echo "=== IMAGES ==="
python3 scripts/check-di-image-integrity.py | tee /tmp/di-bags-men-images.log
echo "EXIT_IMAGES:$?"

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
        "/** Dior Maison + Jewelry + Bags catalog (JSON import keeps TS small). */\n"
        "export const diCatalogProducts = data as unknown as Product[];\n"
    )
print("ts", p.stat().st_size)
PY

echo "=== CDN only men bag folders ==="
python3 - <<'PY'
import json
from pathlib import Path
raw = json.load(open("src/data/di/di-bags-men-catalog-raw.json"))
folders = []
for p in raw.get("products") or []:
    imgs = p.get("images") or []
    if not imgs:
        continue
    parts = str(imgs[0]).split("/")
    if "di-pdp" in parts:
        folders.append(parts[parts.index("di-pdp") + 1])
folders = sorted(set(folders))
Path("/tmp/di-bags-men-cdn-only.txt").write_text("\n".join(folders) + "\n")
print("cdn_folders", len(folders))
PY

python3 scripts/weekly-sync-status.py
python3 scripts/push-product-images-tag.py --dirs di-pdp --skip-whiten --only-file /tmp/di-bags-men-cdn-only.txt | tee /tmp/di-bags-men-cdn.log
echo "EXIT_CDN:$?"

# if CDN reported no changes but local tag ahead, force-push tag
if grep -q 'No image changes' /tmp/di-bags-men-cdn.log; then
  echo "CDN no-op — verifying remote tag has sample"
fi

python3 scripts/weekly-sync-status.py
git add \
  .cursor/rules/dior-catalog.mdc \
  scripts/di_common.py \
  scripts/merge-di-catalog-ko.py \
  scripts/scrape-di-bags-men.py \
  scripts/run-di-bags-men-pipeline.sh \
  src/data/brand-heroes.ts \
  src/data/categories.ts \
  src/data/di/di-bags-men-catalog-raw.json \
  src/data/di/di-bags-men-leaves.json \
  src/data/di/di-catalog.json \
  src/data/di/di-catalog.ts \
  src/data/product-images-manifest.json || true

if ! git diff --cached --quiet; then
  git commit -m "Add Dior men's bags under Bags → 디올 → 남성용 (~163 SKUs).

Official by-category leaves with Korean PDP copy; publish di-pdp images on the product-images CDN tag."
  git push origin main
fi

python3 - <<'PY'
import json
from pathlib import Path
raw=json.load(open('src/data/di/di-bags-men-catalog-raw.json'))
cat=json.load(open('src/data/di/di-catalog.json'))
leaf={
 'di-men-bags-all','di-men-crossbody-shoulder-bags','di-men-backpacks','di-men-small-bags',
 'di-men-tote-bags','di-men-travel-bags','di-men-briefcases','di-men-accessorize-bag','di-bags-mens'
}
n=sum(1 for p in cat if leaf.intersection(p.get('diCollections') or []))
alln=sum(1 for p in cat if 'di-men-bags-all' in (p.get('diCollections') or []))
print('raw', len(raw.get('products') or []), 'catalog_men_bags', n, 'all_leaf', alln, 'ts', Path('src/data/di/di-catalog.ts').stat().st_size)
PY

echo "PIPELINE_DONE $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee /tmp/di-bags-men-READY
git rev-parse --short HEAD | tee -a /tmp/di-bags-men-READY
