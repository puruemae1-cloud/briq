#!/usr/bin/env bash
# Overnight supervisor for Saint Laurent: keep pipeline alive, prevent Mac sleep,
# and commit+push when DONE.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

LOG=tmp/ys-pipeline.log
WLOG=tmp/ys-overnight.log
PIDF=tmp/ys-pipeline.pid
DONE=tmp/ys-pipeline-DONE
DEPLOYED=tmp/ys-pipeline-DEPLOYED

mkdir -p tmp
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) overnight supervisor start pid=$$" | tee -a "$WLOG"

# Prevent idle sleep while this supervisor runs (Mac).
if command -v caffeinate >/dev/null 2>&1; then
  caffeinate -dims -w $$ &
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) caffeinate attached" | tee -a "$WLOG"
fi

start_pipeline() {
  nohup bash scripts/run-ys-pipeline.sh >> tmp/ys-pipeline.nohup.out 2>&1 &
  echo $! > "$PIDF"
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) started pipeline pid=$(cat "$PIDF")" | tee -a "$WLOG"
}

deploy_if_needed() {
  if [[ -f "$DEPLOYED" ]]; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) already deployed" | tee -a "$WLOG"
    return 0
  fi
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) deploying YS catalog…" | tee -a "$WLOG"
  git add \
    src/data/ys \
    public/products/ys-pdp \
    public/brands/saint-laurent.svg \
    scripts/ysl_*.py \
    scripts/scrape-ys-family.py \
    scripts/build-ys-catalog.py \
    scripts/check-ys-coverage.py \
    scripts/run-ys-pipeline.sh \
    scripts/run-ys-weekly-sync.sh \
    scripts/patch-ys-categories.py \
    .github/workflows/weekly-ys-sync.yml \
    src/data/products.ts \
    src/data/product-types.ts \
    src/data/categories.ts \
    src/data/brand-heroes.ts \
    src/lib/shop-brand.ts \
    src/config/site.ts \
    src/config/brand-nav-order.ts \
    2>/dev/null || true

  if git diff --cached --quiet; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) nothing new to commit" | tee -a "$WLOG"
    echo OK > "$DEPLOYED"
    return 0
  fi

  git commit -m "$(cat <<'EOF'
Add Saint Laurent full catalog sync (union PLP coverage).

EOF
)" || {
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) commit failed" | tee -a "$WLOG"
    return 1
  }
  git push origin HEAD | tee -a "$WLOG" || {
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) push failed" | tee -a "$WLOG"
    return 1
  }
  echo OK > "$DEPLOYED"
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) deploy OK" | tee -a "$WLOG"
}

# Soften end-of-pipeline: coverage fail should not loop forever.
# (run-ys-pipeline may exit 1; we still try deploy of whatever is built.)
while true; do
  if [[ -f "$DEPLOYED" ]]; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) overnight complete" | tee -a "$WLOG"
    exit 0
  fi

  if [[ -f "$DONE" ]]; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) DONE seen — deploy" | tee -a "$WLOG"
    if deploy_if_needed; then
      exit 0
    fi
    # Deploy failed — retry later, do not wipe DONE.
    sleep 120
    continue
  fi

  pid=$(cat "$PIDF" 2>/dev/null || true)
  if [[ -n "${pid:-}" ]] && kill -0 "$pid" 2>/dev/null; then
    sleep 120
    continue
  fi

  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) pipeline dead — restart" | tee -a "$WLOG"
  start_pipeline
  sleep 90
done
