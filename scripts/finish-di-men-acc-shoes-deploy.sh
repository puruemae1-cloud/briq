#!/usr/bin/env bash
# Resilient finish: KO QA → commit/push main → CDN (sparse) → status file.
# Safe to re-run; skips steps already done.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONUNBUFFERED=1
LOG=/tmp/di-men-acc-shoes-deploy.log
STATUS=/tmp/di-men-acc-shoes-DEPLOYED
exec >>"$LOG" 2>&1

echo "=== resilient deploy $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

if ! grep -q '^OK ' /tmp/di-men-acc-shoes-ko-last.log 2>/dev/null; then
  echo "=== KO QA ==="
  if python3 scripts/check-catalog-korean.py --brand di --fail | tee /tmp/di-men-acc-shoes-ko-last.log; then
    echo "KO_OK"
  else
    echo "=== KO fix pass ==="
    python3 scripts/fix-di-ko-hybrid.py || true
    python3 scripts/check-catalog-korean.py --brand di --fail | tee /tmp/di-men-acc-shoes-ko-last.log
  fi
fi

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

python3 scripts/weekly-sync-status.py || true

if ! grep -q '^DEPLOYED ' "$STATUS" 2>/dev/null; then
  git add \
    scripts/di_slg_ko.py \
    scripts/ko_qa.py \
    scripts/fix-di-ko-hybrid.py \
    scripts/finish-di-men-acc-shoes-deploy.sh \
    scripts/push-product-images-tag.py \
    scripts/scrape-di-men-accessories.py \
    scripts/scrape-di-men-shoes.py \
    scripts/enrich-di-men-accessories-pdp.py \
    scripts/enrich-di-men-shoes-pdp.py \
    scripts/run-di-men-accessories-pipeline.sh \
    scripts/run-di-men-shoes-pipeline.sh \
    scripts/merge-di-catalog-ko.py \
    src/data/categories.ts \
    src/data/brand-heroes.ts \
    src/data/di/di-catalog.json \
    src/data/di/di-catalog.ts \
    src/data/di/di-translate-cache.json \
    src/data/di/di-men-accessories-catalog-raw.json \
    src/data/di/di-men-accessories-leaves.json \
    src/data/di/di-men-shoes-catalog-raw.json \
    src/data/di/di-men-shoes-leaves.json \
    src/data/product-images-manifest.json \
    2>/dev/null || true

  if git diff --cached --quiet; then
    git add -u src/data/di/ scripts/ src/data/categories.ts src/data/brand-heroes.ts 2>/dev/null || true
  fi

  if ! git diff --cached --quiet; then
    git commit -m "$(cat <<'EOF'
Publish Dior mens accessories and shoes with Korean PDPs.

397 accessories + 215 shoes from official PLPs, size charts, translated copy, and di-pdp images.
EOF
)"
    git push origin main
    REV=$(git rev-parse --short HEAD)
    echo "MAIN_PUSHED $REV $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  else
    echo "MAIN_ALREADY_CLEAN"
  fi
fi

if ! grep -q '^CDN_OK' "$STATUS" 2>/dev/null; then
  echo "=== CDN (sparse di-pdp) ==="
  python3 - <<'PY'
import json
from pathlib import Path
folders=set()
for raw_path in ['src/data/di/di-men-shoes-catalog-raw.json','src/data/di/di-men-accessories-catalog-raw.json']:
    raw=json.loads(Path(raw_path).read_text())
    for p in raw.get('products') or []:
        imgs=p.get('images') or []
        if not imgs: continue
        parts=str(imgs[0]).split('/')
        if 'di-pdp' in parts:
            folders.add(parts[parts.index('di-pdp')+1])
Path('/tmp/di-men-acc-shoes-cdn-only.txt').write_text('\n'.join(sorted(folders))+'\n')
print('cdn_folders', len(folders))
PY
  # Batches of 80 — each run uses sparse checkout (fast).
  split -l 80 /tmp/di-men-acc-shoes-cdn-only.txt /tmp/di-men-acc-shoes-cdn-batch-
  batch_n=0
  total_batches=0
  for _ in /tmp/di-men-acc-shoes-cdn-batch-*; do total_batches=$((total_batches+1)); done
  for batch in /tmp/di-men-acc-shoes-cdn-batch-*; do
    [[ -f "$batch" ]] || continue
    batch_n=$((batch_n+1))
    if grep -q "BATCH_${batch_n}_OK" "$STATUS" 2>/dev/null; then
      echo "skip batch $batch_n (already done)"
      continue
    fi
    echo "=== CDN batch $batch_n/$total_batches $(wc -l < "$batch") folders ==="
    skip_purge=--skip-purge
    if [[ "$batch_n" -eq "$total_batches" ]]; then
      skip_purge=
    fi
    python3 scripts/push-product-images-tag.py \
      --dirs di-pdp --skip-whiten --only-file "$batch" $skip_purge \
      | tee -a /tmp/di-men-acc-shoes-cdn.log
    echo "BATCH_${batch_n}_OK" >> "$STATUS"
    sleep 2
  done
  echo "CDN_OK $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$STATUS"
fi

REV=$(git rev-parse --short HEAD 2>/dev/null || echo unknown)
echo "DEPLOYED $REV $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee "$STATUS"
