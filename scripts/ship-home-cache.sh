#!/usr/bin/env bash
# Ship the homepage data-cache fix: build on a Vercel preview branch first and
# only push to main if that build succeeds (a failed main build blocks deploys).
set -euo pipefail
cd "$(dirname "$0")/.."

REPO=puruemae1-cloud/briq
BRANCH=perf/home-cache
FILES=(
  src/lib/homepage-data.ts
  src/app/page.tsx
  src/components/Collection100.tsx
  scripts/ship-home-cache.sh
  scripts/unblock-deploy.sh
)

wait_for_vercel() {
  local sha=$1 state=""
  for _ in $(seq 1 50); do
    state=$(curl -s -m 20 "https://api.github.com/repos/$REPO/commits/$sha/status" \
      | grep -m1 '"state"' | tr -d ' ",' | cut -d: -f2)
    echo "  $(date +%T) vercel: ${state:-unknown}"
    case "$state" in success|failure|error) break ;; esac
    sleep 30
  done
  [ "$state" = "success" ]
}

echo "== sync with origin/main"
git pull --rebase --autostash origin main

echo "== commit"
git add "${FILES[@]}"
git commit -m "perf: cache homepage product cards in the Vercel data cache.

Cold homepage renders re-parsed every brand catalogue (~15s TTFB). Rails and
100 Collection now come from unstable_cache (trimmed card fields, 1h TTL,
keyed per deployment). Page stays dynamic, so the build is unchanged."
SHA=$(git rev-parse HEAD)

echo "== preview build on $BRANCH ($SHA)"
git push -f origin "HEAD:refs/heads/$BRANCH"
sleep 20
if ! wait_for_vercel "$SHA"; then
  echo
  echo "!! Preview build FAILED — main was NOT touched."
  echo "   Log: open https://github.com/$REPO/commit/$SHA and click the Vercel ✗"
  git reset --soft HEAD~1
  exit 1
fi

echo "== preview OK → push to main"
git pull --rebase --autostash origin main
git push origin HEAD:main
MAIN_SHA=$(git rev-parse HEAD)
sleep 20
if wait_for_vercel "$MAIN_SHA"; then
  echo "== production deployed"
  for i in 1 2 3; do
    curl -s -o /dev/null -w "  try$i ttfb=%{time_starttransfer}s\n" "https://www.briq.kr/?v=$RANDOM"
  done
  echo "DONE"
else
  echo "!! main build failed — run: git revert --no-edit $MAIN_SHA && git push origin HEAD:main"
  exit 1
fi
