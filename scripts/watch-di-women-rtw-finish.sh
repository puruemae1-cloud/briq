#!/usr/bin/env bash
# Watch finish-di-women-rtw.sh until DEPLOYED. Does NOT re-run full scrape/KO loop.
set -u
cd "$(dirname "$0")/.."
WATCH=/tmp/di-women-rtw-finish-watch.log
DEPLOYED=/tmp/di-women-rtw-DEPLOYED
LOCK=/tmp/di-women-rtw-finish-watch.lock
exec >>"$WATCH" 2>&1
echo "=== finish-watch start $(date -u +%Y-%m-%dT%H:%M:%SZ) pid=$$ ==="
if [[ -f "$LOCK" ]]; then
  old=$(cat "$LOCK" 2>/dev/null || true)
  if [[ -n "${old:-}" ]] && kill -0 "$old" 2>/dev/null; then
    echo "another finish-watch alive $old"; exit 0
  fi
fi
echo $$ >"$LOCK"
trap 'rm -f "$LOCK"' EXIT

alive() {
  pgrep -f 'scripts/finish-di-women-rtw.sh' >/dev/null \
    || pgrep -f 'push-product-images-tag.py --dirs di-pdp' >/dev/null
}

while true; do
  if [[ -f "$DEPLOYED" ]]; then
    echo "deployed — exit"; exit 0
  fi
  if alive; then
    echo "$(date -u +%H:%M:%SZ) finish alive"
  else
    echo "$(date -u +%H:%M:%SZ) restart finish"
    nohup bash scripts/finish-di-women-rtw.sh >/dev/null 2>&1 &
    sleep 5
  fi
  sleep 60
done
