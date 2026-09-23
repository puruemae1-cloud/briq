#!/usr/bin/env bash
# Weekly Dior sync orchestrator. Runs all Dior category pipelines sequentially.
set -euo pipefail
cd "$(dirname "$0")/.."
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/Library/Caches/ms-playwright}"
export PYTHONUNBUFFERED=1
LOG=/tmp/di-weekly-sync.log
exec > >(tee -a "$LOG") 2>&1

run() {
  echo "=== $1 $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  shift
  "$@"
}

run "WOMEN_BAGS_STAGES" bash scripts/run-di-bags-stages.sh
run "WOMEN_BAGS_PIPELINE" bash scripts/continue-di-bags-pipeline.sh
run "WOMEN_BAGS_DEPLOY" bash scripts/finish-di-bags-deploy.sh
run "ACCESSORIZE_BAG" bash scripts/run-di-accessorize-bag-pipeline.sh
run "WOMEN_RTW" bash scripts/run-di-women-rtw-pipeline.sh
run "WOMEN_SHOES" bash scripts/run-di-women-shoes-pipeline.sh
run "WOMEN_SLG" bash scripts/run-di-women-slg-pipeline.sh
run "WOMEN_ACCESSORIES" bash scripts/run-di-women-accessories-pipeline.sh
run "WOMEN_JEWELRY" bash scripts/run-di-women-jewelry-pipeline.sh
run "MEN_RTW" bash scripts/run-di-men-rtw-pipeline.sh
run "MEN_SHOES" bash scripts/run-di-men-shoes-pipeline.sh
run "MEN_SLG" bash scripts/run-di-men-slg-pipeline.sh
run "MEN_ACCESSORIES" bash scripts/run-di-men-accessories-pipeline.sh
run "MEN_ESSENTIALS" bash scripts/run-di-men-essentials-pipeline.sh
run "MEN_BAGS" bash scripts/run-di-bags-men-pipeline.sh
run "POST_FIX_RTW" python3 scripts/enrich-di-men-rtw-pdp.py --translate
run "POST_FIX_WOMEN_RTW" python3 scripts/enrich-di-women-rtw-pdp.py --translate
# Fast Algolia size rebuild for any RTW/homewear/swim SKUs still stuck on OS
run "POST_FIX_RTW_SIZES" python3 scripts/patch-di-rtw-sizes-from-algolia.py
run "NEW_BADGE_TTL" python3 scripts/apply-new-badge-ttl.py --brand di

echo "=== DIOR_WEEKLY_DONE $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
