#!/usr/bin/env bash
# Keep Dior women SLG pipeline alive until DEPLOYED (chat-disconnect safe).
set -u
cd "$(dirname "$0")/.."
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/Library/Caches/ms-playwright}"
export PYTHONUNBUFFERED=1
export PAUSE_SEC="${PAUSE_SEC:-30}"

WATCH=/tmp/di-women-slg-watch.log
DEPLOYED=/tmp/di-women-slg-DEPLOYED
LOCK=/tmp/di-women-slg-watch.lock
STATUS=/tmp/di-women-slg-STATUS
exec >>"$WATCH" 2>&1
echo "=== watch start $(date -u +%Y-%m-%dT%H:%M:%SZ) pid=$$ ==="

if [[ -f "$LOCK" ]]; then
  old=$(cat "$LOCK" 2>/dev/null || true)
  if [[ -n "${old:-}" ]] && kill -0 "$old" 2>/dev/null; then
    echo "another watch alive $old"
    exit 0
  fi
fi
echo $$ >"$LOCK"
trap 'rm -f "$LOCK"' EXIT

alive() {
  pgrep -f 'scripts/run-di-women-slg-pipeline.sh' >/dev/null \
    || pgrep -f 'scripts/scrape-di-women-slg.py' >/dev/null \
    || pgrep -f 'scripts/enrich-di-women-slg-pdp.py' >/dev/null \
    || pgrep -f 'scripts/merge-di-catalog-ko.py' >/dev/null \
    || pgrep -f 'push-product-images-tag.py --dirs di-pdp' >/dev/null
}

ko_fails() {
  grep -c 'KO_FAIL' "$STATUS" 2>/dev/null || echo 0
}

touch "$STATUS"

while true; do
  if [[ -f "$DEPLOYED" ]]; then
    echo "deployed — exit"
    exit 0
  fi
  fails=$(ko_fails | tr -d '[:space:]')
  if [[ "${fails:-0}" -ge 3 ]]; then
    echo "KO failed ${fails}x — stop thrash; needs manual fix"
    exit 1
  fi
  if alive; then
    echo "$(date -u +%H:%M:%SZ) alive status=$(tr '\n' ' ' <"$STATUS" 2>/dev/null | tr -s ' ')"
  else
    echo "$(date -u +%H:%M:%SZ) DEAD — resume"
    nohup bash scripts/run-di-women-slg-pipeline.sh >/dev/null 2>&1 &
    sleep 5
  fi
  sleep 60
done
