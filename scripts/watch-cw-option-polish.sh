#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/.."
WATCH=/tmp/cw-option-polish-watch.log
DEPLOYED=/tmp/cw-option-polish-DEPLOYED
LOCK=/tmp/cw-option-polish-watch.lock
STATUS=/tmp/cw-option-polish-STATUS
exec >>"$WATCH" 2>&1
echo "=== watch $(date -u +%Y-%m-%dT%H:%M:%SZ) pid=$$ ==="
if [[ -f "$LOCK" ]]; then
  old=$(cat "$LOCK" 2>/dev/null || true)
  if [[ -n "${old:-}" ]] && kill -0 "$old" 2>/dev/null; then
    echo another alive "$old"; exit 0
  fi
fi
echo $$ >"$LOCK"
trap 'rm -f "$LOCK"' EXIT
alive() {
  pgrep -f 'scripts/run-cw-option-polish.sh' >/dev/null \
    || pgrep -f 'scripts/enrich-cw-variation-attrs.py' >/dev/null \
    || pgrep -f 'scripts/rebuild-cw-catalog.py' >/dev/null \
    || pgrep -f 'scripts/check-catalog-korean.py' >/dev/null
}
touch "$STATUS"
while true; do
  [[ -f "$DEPLOYED" ]] && { echo deployed; exit 0; }
  if alive; then
    echo "$(date -u +%H:%M:%SZ) alive $(tr '\n' ' ' <"$STATUS" | tr -s ' ')"
  else
    echo "$(date -u +%H:%M:%SZ) DEAD — resume"
    nohup bash scripts/run-cw-option-polish.sh >/dev/null 2>&1 &
    sleep 5
  fi
  sleep 60
done
