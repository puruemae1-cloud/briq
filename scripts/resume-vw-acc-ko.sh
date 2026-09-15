#!/usr/bin/env bash
# Crash-resilient VW accessories Korean retranslate loop.
# Safe to re-run: resumes from vw-translate-cache.json.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p tmp
LOG=tmp/vw-acc-ko-retranslate.log
PIDFILE=tmp/vw-acc-ko-retranslate.pid
MAX_ROUNDS=20

if [[ -f "$PIDFILE" ]]; then
  old=$(cat "$PIDFILE" || true)
  if [[ -n "${old:-}" ]] && kill -0 "$old" 2>/dev/null; then
    echo "already running pid=$old"
    exit 0
  fi
fi

round=0
while (( round < MAX_ROUNDS )); do
  round=$((round + 1))
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) START round=$round" | tee -a "$LOG"
  PYTHONUNBUFFERED=1 python3 scripts/retranslate-vw-ko.py --category accessories >>"$LOG" 2>&1
  rc=$?
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) END round=$round rc=$rc" | tee -a "$LOG"
  if [[ $rc -eq 0 ]]; then
    python3 scripts/check-vw-accessories-korean.py --fail --max-bad 0 >>"$LOG" 2>&1
    exit $?
  fi
  # Non-zero: leftovers or crash — brief pause then resume from cache.
  sleep 5
done
echo "gave up after $MAX_ROUNDS rounds" | tee -a "$LOG"
exit 1
