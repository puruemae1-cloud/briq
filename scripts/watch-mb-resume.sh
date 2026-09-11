#!/usr/bin/env bash
# Local crash-safe loop: one Mulberry leaf per wake, then MB-only commit/push.
# Usage: ./scripts/watch-mb-resume.sh   (Ctrl-C to stop)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
INTERVAL="${MB_WATCH_INTERVAL:-300}"
LOG="$ROOT/tmp/mb-watch.log"
mkdir -p "$ROOT/tmp"

commit_mb() {
  git add -- \
    scripts/run-mb-resume.sh \
    scripts/watch-mb-resume.sh \
    src/data/mb \
    src/data/product-images-manifest.json 2>/dev/null || true
  if git diff --cached --quiet; then
    echo "nothing to commit" | tee -a "$LOG"
    return 0
  fi
  local leaf
  leaf="$(python3 -c "import json;print(json.load(open('tmp/mb-resume-state.json')).get('lastLeaf','mb'))" 2>/dev/null || echo mb)"
  git commit -m "Add Mulberry ${leaf} leaf batch." || true
  git fetch origin main
  git rebase origin/main || { git rebase --abort 2>/dev/null || true; return 1; }
  git push origin HEAD
}

echo "== MB watch start $(date -Iseconds) interval=${INTERVAL}s ==" | tee -a "$LOG"
while true; do
  echo "-- wake $(date -Iseconds) --" | tee -a "$LOG"
  if ! ./scripts/run-mb-resume.sh; then
    echo "resume failed; sleep ${INTERVAL}s" | tee -a "$LOG"
    sleep "$INTERVAL"
    continue
  fi
  if grep -q 'ALL_LEAVES_HAVE_RAW\|RESUME_IDLE' "$ROOT/tmp/mb-resume.log" 2>/dev/null; then
    commit_mb || true
    echo "ALL DONE" | tee -a "$LOG"
    exit 0
  fi
  commit_mb || true
  echo "sleep ${INTERVAL}s" | tee -a "$LOG"
  sleep "$INTERVAL"
done
