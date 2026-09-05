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

echo "=== DIOR_WEEKLY_DONE $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
