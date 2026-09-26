#!/usr/bin/env bash
# Ship: homepage cards via /api/home-data (keeps catalogues out of the / bundle).
# Preview build first; main only if it succeeds.
set -euo pipefail
cd "$(dirname "$0")/.."

REPO=puruemae1-cloud/briq
BRANCH=perf/home-feed
FILES=(
  src/lib/homepage-data.ts
  src/lib/homepage-feed.ts
  src/app/api/home-data/route.ts
  src/app/page.tsx
  src/components/Collection100.tsx
  .cursor/rules/homepage-speed.mdc
  scripts/ship-home-feed.sh
)

status_of() {
  curl -s -m 20 "https://api.github.com/repos/$REPO/commits/$1/status" \
    | grep -m1 '"state"' | tr -d ' ",' | cut -d: -f2
}

wait_for_vercel() {
  local sha=$1 state=""
  for _ in $(seq 1 50); do
    state=$(status_of "$sha")
    echo "  $(date +%T) vercel: ${state:-unknown}"
    case "$state" in success|failure|error) break ;; esac
    sleep 30
  done
  [ "$state" = "success" ]
}

wait_for_production() {
  local sha=$1 prod="" st=""
  for _ in $(seq 1 50); do
    prod=$(curl -s -m 20 "https://api.github.com/repos/$REPO/deployments?sha=$sha&environment=Production" \
      | grep -m1 '"statuses_url"' | cut -d'"' -f4)
    if [ -n "$prod" ]; then
      st=$(curl -s -m 20 "$prod" | grep -m1 '"state"' | tr -d ' ",' | cut -d: -f2)
      echo "  $(date +%T) production: ${st:-pending}"
      case "$st" in success) return 0 ;; failure|error) return 1 ;; esac
    else
      echo "  $(date +%T) production: queued"
    fi
    sleep 30
  done
  return 1
}

echo "== sync with origin/main"
git pull --rebase --autostash origin main

echo "== commit"
git add "${FILES[@]}"
git commit -m "perf: serve homepage cards from /api/home-data so / boots without catalogues.

The / chunk statically reached @/data/products, so every new instance parsed
all brand catalogues (~9s). The page now fetches /api/home-data?v=<deploy>
(CDN s-maxage + Next Data Cache); only that route bundles the catalogues.
Falls back to a local build if the fetch fails."
SHA=$(git rev-parse HEAD)

echo "== preview build on $BRANCH ($SHA)"
git push -f origin "HEAD:refs/heads/$BRANCH"
sleep 20
if ! wait_for_vercel "$SHA"; then
  echo "!! Preview build FAILED — main was NOT touched."
  git reset --soft HEAD~1
  exit 1
fi

echo "== preview OK → push to main"
git pull --rebase --autostash origin main
git push origin HEAD:main
MAIN_SHA=$(git rev-parse HEAD)
sleep 30
if wait_for_production "$MAIN_SHA"; then
  echo "== production deployed — first hit fills the cache"
  curl -s -o /dev/null -m 90 -w "  fill ttfb=%{time_starttransfer}s total=%{time_total}s\n" "https://www.briq.kr/"
  sleep 5
  for i in 1 2 3 4 5 6 7 8; do
    curl -s -o /dev/null -m 60 -w "  try$i ttfb=%{time_starttransfer}s total=%{time_total}s\n" "https://www.briq.kr/"
    sleep 1
  done
  echo "DONE"
else
  echo "!! production build failed — run: git revert --no-edit $MAIN_SHA && git push origin HEAD:main"
  exit 1
fi
