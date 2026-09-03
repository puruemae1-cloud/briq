#!/usr/bin/env bash
# Polish CW option labels + enrich attrs, rebuild, commit. Disconnect-safe.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONUNBUFFERED=1
LOG=/tmp/cw-option-polish.log
STATUS=/tmp/cw-option-polish-STATUS
DEPLOYED=/tmp/cw-option-polish-DEPLOYED
exec >>"$LOG" 2>&1
echo "=== start $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
touch "$STATUS"
[[ -f "$DEPLOYED" ]] && { echo already; exit 0; }

run_step() {
  local stamp="$1"; shift
  grep -q "${stamp}_OK" "$STATUS" 2>/dev/null && { echo skip "$stamp"; return 0; }
  echo "=== $stamp ==="
  set +e; "$@"; local st=$?; set -e
  echo "EXIT_${stamp}:$st"
  [[ "$st" -ne 0 ]] && { echo "${stamp}_FAIL:$st" >>"$STATUS"; exit "$st"; }
  echo "${stamp}_OK" >>"$STATUS"
}

run_step ENRICH_ATTRS python3 scripts/enrich-cw-variation-attrs.py
run_step REBUILD python3 scripts/rebuild-cw-catalog.py
run_step KO python3 scripts/check-catalog-korean.py --brand cw --fail

git add \
  scripts/rebuild-cw-catalog.py \
  scripts/weekly-cw-stock-sync.py \
  scripts/enrich-cw-variation-attrs.py \
  scripts/run-cw-option-polish.sh \
  scripts/watch-cw-option-polish.sh \
  src/data/cw/cw-catalog.ts \
  src/data/cw/cw-pdp-enriched.json \
  || true
if ! git diff --cached --quiet; then
  git commit -m "$(cat <<'EOF'
Fix Christopher Ward dial size and strap option labels and prices.

Enrich variation attributes for family SKUs and keep multi-case chips human-readable across weekly sync.
EOF
)"
  git push origin HEAD
fi
touch "$DEPLOYED"
echo "=== DONE $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
