#!/usr/bin/env bash
# Weekly Dior sync orchestrator. Runs all Dior category pipelines sequentially.
#
# In CI the whole sync does not fit one runner (6h cap), so each finished unit
# is committed and recorded in PROGRESS. Once DI_BUDGET_MIN has elapsed no new
# unit starts; the workflow re-dispatches itself with DI_RESUME=1 and the next
# run skips units already done this cycle.
set -euo pipefail
cd "$(dirname "$0")/.."
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/Library/Caches/ms-playwright}"
export PYTHONUNBUFFERED=1
LOG=/tmp/di-weekly-sync.log
exec > >(tee -a "$LOG") 2>&1

CI_RUN=0
[[ "${GITHUB_ACTIONS:-}" == "true" ]] && CI_RUN=1
PROGRESS=src/data/di/weekly-progress.json
# Both limits count from JOB_STARTED (set by the workflow) so restore time is
# included: no unit starts after DI_BUDGET_MIN, and a running unit is stopped
# at DI_HARD_MIN so the job still gets to commit before the runner cap.
STARTED="${JOB_STARTED:-$(date +%s)}"
BUDGET_SEC=$(( ${DI_BUDGET_MIN:-0} * 60 ))
HARD_SEC=$(( ${DI_HARD_MIN:-0} * 60 ))
FAILED=""
MORE=0

if [[ "$CI_RUN" == "1" ]]; then
  # These stages log only to their own files; mirror them into the job log.
  STAGE_LOGS=(/tmp/di-bags-pipeline.log /tmp/di-bags-deploy.log /tmp/di-acc-bag-pipeline.log
    /tmp/di-women-accessories-pipeline.log /tmp/di-women-jewelry-pipeline.log
    /tmp/di-women-shoes-pipeline.log /tmp/di-women-slg-pipeline.log)
  touch "${STAGE_LOGS[@]}"
  tail -n0 -F "${STAGE_LOGS[@]}" 2>/dev/null &
  TAIL_PID=$!
  trap 'kill "$TAIL_PID" 2>/dev/null || true' EXIT
fi

run_unit() {
  local left
  if (( HARD_SEC > 0 )) && command -v timeout >/dev/null; then
    left=$(( STARTED + HARD_SEC - $(date +%s) ))
    (( left > 60 )) || left=60
    timeout --kill-after=60 "$left" "$@"
  else
    "$@"
  fi
}

if [[ "${DI_RESUME:-}" != "1" || ! -f "$PROGRESS" ]]; then
  echo '{"done": [], "failed": []}' > "$PROGRESS"
fi

progress_has() {
  python3 -c 'import json, sys
p = json.load(open(sys.argv[1]))
sys.exit(0 if sys.argv[2] in p["done"] + p["failed"] else 1)' "$PROGRESS" "$1"
}

progress_add() {
  python3 -c 'import json, sys
f, key, name = sys.argv[1:]
p = json.load(open(f))
p[key].append(name)
open(f, "w").write(json.dumps(p, indent=2) + "\n")' "$PROGRESS" "$2" "$1"
}

checkpoint() {
  [[ "$CI_RUN" == "1" ]] || return 0
  scripts/ci-commit-push.sh "chore(di): weekly sync — $1" src/data/di \
    src/data/product-images-manifest.json
}

run() {
  local name="$1"
  shift
  if progress_has "$name"; then
    echo "=== $name skipped (already ran this cycle) ==="
    return 0
  fi
  [[ "$MORE" == "1" ]] && return 0
  if (( BUDGET_SEC > 0 && $(date +%s) - STARTED > BUDGET_SEC )); then
    echo "=== time budget reached before $name — continuing in a new run ==="
    MORE=1
    return 0
  fi
  echo "=== $name $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  local rc=0
  run_unit "$@" || rc=$?
  if (( rc == 0 )); then
    progress_add "$name" done
  else
    if (( rc == 124 || rc == 137 )); then
      echo "!!! $name hit the hard time limit — remaining units continue in a new run"
      MORE=1
    fi
    # Stage scripts log to /tmp/di-*.log only; surface them in CI.
    echo "!!! $name failed (exit $rc) — recent /tmp/di-*.log output:"
    tail -n 60 /tmp/di-*.log 2>/dev/null || true
    [[ "$CI_RUN" == "1" ]] || return 1
    # Earlier units are already committed; drop this unit's partial output
    # and keep going so one broken category cannot block the others.
    git checkout -- src/data/di
    git clean -fdq src/data/di
    FAILED="$FAILED $name"
    progress_add "$name" failed
  fi
  checkpoint "$name"
}

run "WOMEN_BAGS_STAGES" bash scripts/run-di-bags-stages.sh
# Stages 1-3 just ran above; the pipeline only merges, checks and publishes.
run "WOMEN_BAGS_PIPELINE" bash -c \
  'SKIP_BAGS_SCRAPE=1 bash scripts/continue-di-bags-pipeline.sh && bash scripts/finish-di-bags-deploy.sh'
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
# Full size runs + OOS chips from Algolia variantsWithStocks (RTW + shoes + belts).
# Must run after enrich/merge so in-stock-only `variants` cannot shrink the PDP.
# Belts also get '{n} cm' labels + cm↔inch size chart (dior.com unit).
run "POST_FIX_SIZES_STOCK" python3 scripts/patch-di-rtw-sizes-from-algolia.py
run "AUDIT_SIZE_STOCK" bash -c 'python3 scripts/audit-brand-size-stock.py --brand di || true'
run "NEW_BADGE_TTL" python3 scripts/apply-new-badge-ttl.py --brand di

if [[ "$MORE" == "1" ]]; then
  [[ -n "${GITHUB_OUTPUT:-}" ]] && echo "more=true" >> "$GITHUB_OUTPUT"
  exit 0
fi

echo "=== DIOR_WEEKLY_DONE $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
if [[ -n "$FAILED" ]]; then
  echo "Failed units:$FAILED" >&2
  exit 1
fi
