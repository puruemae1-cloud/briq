#!/usr/bin/env bash
# Detached-safe Dior men's RTW PDP enrich (variants + size charts + story).
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONUNBUFFERED=1
LOG=/tmp/di-men-rtw-enrich.log
exec > >(tee -a "$LOG") 2>&1

echo "=== RTW enrich start $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
python3 scripts/enrich-di-men-rtw-pdp.py
echo "EXIT_ENRICH:$?"

echo "=== KO check ==="
python3 scripts/check-catalog-korean.py --brand di --fail || true

if ! git diff --quiet src/data/di/di-catalog.json src/data/di/di-translate-cache.json 2>/dev/null; then
  git add \
    scripts/di_size_charts.py \
    scripts/enrich-di-men-rtw-pdp.py \
    scripts/run-di-men-rtw-enrich.sh \
    scripts/merge-di-catalog-ko.py \
    scripts/run-di-men-rtw-pipeline.sh \
    src/data/di/di-catalog.json \
    src/data/di/di-translate-cache.json
  git commit -m "$(cat <<'EOF'
Enrich Dior mens RTW PDPs with official size charts and detailed copy.

Rebuild Algolia size variants, add shirt collar size guide from dior.com, and expand storySections/featuresKo/techSpecs for all mens RTW SKUs.
EOF
)"
  git push origin main
fi

echo "ENRICH_DONE $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee /tmp/di-men-rtw-enrich-READY
git rev-parse --short HEAD | tee -a /tmp/di-men-rtw-enrich-READY
