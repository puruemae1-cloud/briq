#!/usr/bin/env bash
# Keep accessorize-bag pipeline alive until DEPLOYED (chat-disconnect safe).
set -u
cd "$(dirname "$0")/.."
WATCH=/tmp/di-acc-bag-watch.log
DEPLOYED=/tmp/di-acc-bag-DEPLOYED
LOCK=/tmp/di-acc-bag-watch.lock
STATUS=/tmp/di-acc-bag-STATUS
exec >>"$WATCH" 2>&1
echo "=== watch start $(date -u +%Y-%m-%dT%H:%M:%SZ) pid=$$ ==="
if [[ -f "$LOCK" ]]; then
  old=$(cat "$LOCK" 2>/dev/null || true)
  if [[ -n "${old:-}" ]] && kill -0 "$old" 2>/dev/null; then
    echo "another watch alive $old"; exit 0
  fi
fi
echo $$ >"$LOCK"
trap 'rm -f "$LOCK"' EXIT

alive() {
  pgrep -f 'scripts/run-di-accessorize-bag-pipeline.sh' >/dev/null \
    || pgrep -f 'scripts/reclassify-di-accessorize-bag.py' >/dev/null \
    || pgrep -f 'push-product-images-tag.py --dirs di-pdp' >/dev/null
}

# If KO is thrashing, stop after 3 fails
ko_fails() {
  grep -c 'KO_FAIL' "$STATUS" 2>/dev/null || echo 0
}

while true; do
  if [[ -f "$DEPLOYED" ]]; then
    echo "deployed — exit"; exit 0
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
    nohup bash scripts/run-di-accessorize-bag-pipeline.sh >/dev/null 2>&1 &
    sleep 5
  fi
  sleep 60
done
