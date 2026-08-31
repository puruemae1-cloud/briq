#!/usr/bin/env bash
# Wait for continue-di-bags-pipeline.sh to finish, then commit + push main.
set -euo pipefail
cd "$(dirname "$0")/.."
LOG=/tmp/di-bags-deploy.log
exec >>"$LOG" 2>&1
echo "=== deploy waiter $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

# Wait until pipeline log says done (or pipeline + scrape gone and merge done)
for i in $(seq 1 240); do
  if grep -q 'PIPELINE_DONE' /tmp/di-bags-pipeline.log 2>/dev/null; then
    echo "saw PIPELINE_DONE"
    break
  fi
  if ! pgrep -f 'continue-di-bags-pipeline|scrape-di-bags|merge-di-catalog-ko|push-product-images-tag' >/dev/null 2>&1; then
    if grep -q 'EXIT_MERGE:0\|DONE ' /tmp/di-bags-merge.log 2>/dev/null || grep -q 'PIPELINE_DONE\|EXIT_CDN' /tmp/di-bags-pipeline.log 2>/dev/null; then
      echo "jobs idle + merge/cdn evidence"
      break
    fi
  fi
  sleep 30
done

if ! grep -q 'PIPELINE_DONE' /tmp/di-bags-pipeline.log 2>/dev/null; then
  # If scrape finished but merge not run, do merge+cdn here
  if [[ -f src/data/di/di-bags-women-catalog-raw.json ]] && ! grep -q 'EXIT_MERGE:0' /tmp/di-bags-pipeline.log 2>/dev/null; then
    echo "=== fallback MERGE ==="
    python3 scripts/merge-di-catalog-ko.py | tee /tmp/di-bags-merge.log
    python3 scripts/check-catalog-korean.py --brand di --fail | tee /tmp/di-bags-ko.log
    python3 scripts/weekly-sync-status.py
    python3 scripts/push-product-images-tag.py --dirs di-pdp | tee /tmp/di-bags-cdn.log
  fi
fi

python3 scripts/weekly-sync-status.py

# Keep di-catalog.ts thin
python3 - <<'PY'
from pathlib import Path
p = Path("src/data/di/di-catalog.ts")
text = p.read_text() if p.exists() else ""
if len(text) > 2000 or "di-catalog.json" not in text:
    p.write_text(
        "/* Auto-generated — do not edit */\n"
        'import type { Product } from "@/data/product-types";\n'
        'import data from "./di-catalog.json";\n'
        "\n"
        "/** Dior Maison + Jewelry + Bags catalog (JSON import keeps TS small). */\n"
        "export const diCatalogProducts = data as unknown as Product[];\n"
    )
    print("rewrote thin di-catalog.ts", p.stat().st_size)
else:
    print("di-catalog.ts ok", p.stat().st_size)
PY

python3 - <<'PY'
import json
from pathlib import Path
raw = json.load(open("src/data/di/di-bags-women-catalog-raw.json"))
cat = json.load(open("src/data/di/di-catalog.json"))
leaf = {
    "di-bags-all","di-handbags","di-crossbody-shoulder-bags","di-tote-bags",
    "di-bucket-bags","di-clutches","di-mini-bags","di-accessorize-bag","di-bags-womens","dior-bags",
}
n = sum(1 for p in cat if leaf.intersection(p.get("diCollections") or []))
print("raw", len(raw.get("products") or []), "catalog_bags", n, "ts", Path("src/data/di/di-catalog.ts").stat().st_size)
PY

git add \
  scripts/di_common.py \
  scripts/scrape-di-bags.py \
  scripts/run-di-bags-stages.sh \
  scripts/continue-di-bags-pipeline.sh \
  scripts/merge-di-catalog-ko.py \
  src/data/categories.ts \
  src/data/brand-heroes.ts \
  src/data/di/di-catalog.json \
  src/data/di/di-catalog.ts \
  src/data/di/di-bags-women-catalog-raw.json \
  src/data/di/di-bags-women-leaves.json \
  src/data/product-images-manifest.json \
  .cursor/rules/dior-catalog.mdc \
  2>/dev/null || true

# pdp cache is gitignored usually — skip
git status -sb | head -40

if git diff --cached --quiet; then
  echo "nothing staged — check unstaged"
  git status -sb | head -50
  # try add again if catalog dirty
  git add -u src/data/di/ src/data/categories.ts src/data/brand-heroes.ts scripts/ .cursor/rules/dior-catalog.mdc src/data/product-images-manifest.json || true
fi

if git diff --cached --quiet; then
  echo "NO_CHANGES_TO_COMMIT"
  echo DEPLOY_SKIPPED > /tmp/di-bags-DEPLOYED
  exit 0
fi

git commit -m "$(cat <<'EOF'
Add Dior women's bags under Bags → 디올 → 여성용 (~388 SKUs).

Import official by-category leaves (handbags, crossbody, totes, bucket, clutches, mini, accessorize) with Korean copy and PDP images.
EOF
)"

git push origin main
echo "DEPLOYED $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee /tmp/di-bags-DEPLOYED
git rev-parse --short HEAD
git status -sb | head -10
