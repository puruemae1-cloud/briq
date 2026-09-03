#!/usr/bin/env bash
# Detached watchdog: keep Dior women RTW pipeline alive until /tmp/di-women-rtw-DEPLOYED.
# Safe across chat disconnects. Does not kill a healthy in-flight scrape.
set -u
cd "$(dirname "$0")/.."
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/Library/Caches/ms-playwright}"
export PYTHONUNBUFFERED=1
export PAUSE_SEC="${PAUSE_SEC:-20}"

LOG=/tmp/di-women-rtw-pipeline.log
WATCH=/tmp/di-women-rtw-watchdog.log
STATUS=/tmp/di-women-rtw-STATUS
DEPLOYED=/tmp/di-women-rtw-DEPLOYED
LOCK=/tmp/di-women-rtw-watchdog.lock

exec >>"$WATCH" 2>&1
echo "=== watchdog start $(date -u +%Y-%m-%dT%H:%M:%SZ) pid=$$ ==="

if [[ -f "$LOCK" ]]; then
  old=$(cat "$LOCK" 2>/dev/null || true)
  if [[ -n "${old:-}" ]] && kill -0 "$old" 2>/dev/null; then
    echo "another watchdog alive pid=$old — exit"
    exit 0
  fi
fi
echo $$ >"$LOCK"
trap 'rm -f "$LOCK"' EXIT

pipeline_alive() {
  pgrep -f 'scripts/run-di-women-rtw-pipeline.sh' >/dev/null \
    || pgrep -f 'scripts/scrape-di-women-rtw.py' >/dev/null \
    || pgrep -f 'scripts/enrich-di-women-rtw-pdp.py' >/dev/null \
    || pgrep -f 'scripts/merge-di-catalog-ko.py' >/dev/null \
    || pgrep -f 'push-product-images-tag.py --dirs di-pdp' >/dev/null
}

start_pipeline() {
  echo "=== launching pipeline $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  # Avoid nested tee double-logging: pipeline already tees to LOG
  nohup bash scripts/run-di-women-rtw-pipeline.sh >/dev/null 2>&1 &
  echo "pipeline_pid=$!"
  sleep 5
}

# Ensure STATUS file exists
touch "$STATUS"

while true; do
  if [[ -f "$DEPLOYED" ]]; then
    echo "=== DEPLOYED marker present — watchdog done $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
    exit 0
  fi
  if pipeline_alive; then
    echo "$(date -u +%H:%M:%SZ) alive status=$(tr '\n' ' ' <"$STATUS" 2>/dev/null)"
  else
    echo "$(date -u +%H:%M:%SZ) DEAD — resume"
    start_pipeline
  fi
  sleep 90
done
