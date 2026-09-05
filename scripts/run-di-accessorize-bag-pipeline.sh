#!/usr/bin/env bash
# Accessorize Your Bag: reclassify → KO → CDN (if needed) → commit/push.
# Detached-safe with STATUS stamps + finish watchdog.
set -uo pipefail
cd "$(dirname "$0")/.."
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/Library/Caches/ms-playwright}"
export PYTHONUNBUFFERED=1
LOG=/tmp/di-acc-bag-pipeline.log
STATUS=/tmp/di-acc-bag-STATUS
DEPLOYED=/tmp/di-acc-bag-DEPLOYED
exec >>"$LOG" 2>&1

echo "=== accessorize bag pipeline start $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
touch "$STATUS"

run_step() {
  local stamp="$1"; shift
  if grep -q "${stamp}_OK" "$STATUS" 2>/dev/null; then
    echo "skip $stamp"
    return 0
  fi
  echo "=== $stamp ==="
  set +e
  "$@"
  local st=$?
  set -e
  echo "EXIT_${stamp}:$st"
  if [[ "$st" -ne 0 ]]; then
    echo "${stamp}_FAIL:$st" >>"$STATUS"
    exit "$st"
  fi
  echo "${stamp}_OK" >>"$STATUS"
}

if [[ -f "$DEPLOYED" ]]; then
  echo "already deployed"
  exit 0
fi

run_step RECLASS python3 scripts/reclassify-di-accessorize-bag.py
run_step KO python3 scripts/check-catalog-korean.py --brand di --fail
run_step IMAGES python3 scripts/check-di-image-integrity.py

python3 - <<'PY'
from pathlib import Path
p = Path("src/data/di/di-catalog.ts")
p.write_text(
    "/* Auto-generated — do not edit */\n"
    'import type { Product } from "@/data/product-types";\n'
    'import data from "./di-catalog.json";\n'
    "\n"
    "/** Dior catalog (JSON import keeps TS small). */\n"
    "export const diCatalogProducts = data as unknown as Product[];\n"
)
print("ts", p.stat().st_size)
PY

echo "=== CDN folders ==="
python3 - <<'PY'
import json
from pathlib import Path
from scripts.di_common import slugify
prods = json.loads(Path("src/data/di/di-catalog.json").read_text())
folders = []
for p in prods:
    sub = p.get("subcategory") or ""
    cols = set(p.get("diCollections") or [])
    if not (
        sub == "di-accessorize-bag"
        or sub.startswith("di-acc-bag-")
        or "di-accessorize-bag" in cols
    ):
        continue
    imgs = p.get("images") or []
    if not imgs:
        continue
    parts = str(imgs[0]).split("/")
    if "di-pdp" in parts:
        folders.append(parts[parts.index("di-pdp") + 1])
    else:
        folders.append(slugify(str(p.get("sku") or "")))
folders = sorted(set(folders))
Path("/tmp/di-acc-bag-cdn-only.txt").write_text("\n".join(folders) + "\n")
print("cdn_folders", len(folders))
PY

if [[ -s /tmp/di-acc-bag-cdn-only.txt ]]; then
  rm -f /tmp/di-acc-bag-cdn-batch-*
  split -l 80 /tmp/di-acc-bag-cdn-only.txt /tmp/di-acc-bag-cdn-batch-
  batches=(/tmp/di-acc-bag-cdn-batch-*)
  total=${#batches[@]}
  n=0
  for batch in "${batches[@]}"; do
    [[ -f "$batch" ]] || continue
    n=$((n + 1))
    if grep -q "CDN_BATCH_${n}_OK" "$STATUS" 2>/dev/null; then
      echo "skip CDN batch $n"
      continue
    fi
    echo "=== CDN batch $n/$total ==="
    skip_purge=--skip-purge
    if [[ "$n" -eq "$total" ]]; then
      skip_purge=
    fi
    set +e
    # Skip purge hang on last batch too — images already on tag; purge optional
    python3 scripts/push-product-images-tag.py --dirs di-pdp --skip-whiten --only-file "$batch" --skip-purge
    st=$?
    set -e
    echo "EXIT_CDN_${n}:$st"
    if [[ "$st" -ne 0 ]]; then
      echo "CDN_BATCH_${n}_FAIL:$st" >>"$STATUS"
      exit "$st"
    fi
    echo "CDN_BATCH_${n}_OK" >>"$STATUS"
  done
fi

echo "=== COMMIT / PUSH ==="
git add \
  scripts/di_common.py \
  scripts/reclassify-di-accessorize-bag.py \
  scripts/run-di-accessorize-bag-pipeline.sh \
  scripts/watch-di-accessorize-bag.sh \
  scripts/merge-di-catalog-ko.py \
  src/data/categories.ts \
  src/data/brand-heroes.ts \
  src/data/di/di-catalog.json \
  src/data/di/di-catalog.ts \
  src/data/di/di-accessorize-bag-leaves.json \
  src/data/di/di-accessorize-bag-catalog-raw.json \
  src/data/product-images-manifest.json \
  || true

if ! git diff --cached --quiet; then
  git commit -m "$(cat <<'EOF'
Split Dior Accessorize Your Bag into official category leaves.

Map Bags → Dior → 여성용 → 악세서리 Your Bag to Algolia category.lvl2 leaves (jewelry, totes, mini, straps lines, key rings, Mitzah, purse).
EOF
)"
  git push origin HEAD
else
  echo "nothing to commit"
fi

touch "$DEPLOYED"
echo "=== DONE $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
