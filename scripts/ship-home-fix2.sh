#!/usr/bin/env bash
# Restore static products import in homepage-data (dynamic import made every
# request recompute) + run functions in Seoul (icn1). Preview first, then main.
set -euo pipefail
cd "$(dirname "$0")/.."

REPO=puruemae1-cloud/briq
BRANCH=perf/home-fix2
FILES=(
  src/lib/homepage-data.ts
  vercel.json
  .cursor/rules/homepage-speed.mdc
  scripts/ship-home-fix2.sh
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
git commit -m "perf: static products import for cached homepage data; run functions in icn1.

await import() inside the unstable_cache callbacks made every homepage request
recompute (TTFB 1.4s, ~9s total). Back to the static import that measured
0.2s TTFB warm. Functions move from iad1 to Seoul for Korean customers."
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
  echo "== production deployed — measuring (first hit fills the cache)"
  sleep 10
  for i in 1 2 3 4 5; do
    curl -s -o /dev/null -m 60 -w "  try$i ttfb=%{time_starttransfer}s total=%{time_total}s\n" "https://www.briq.kr/?v=$RANDOM$i"
    sleep 1
  done
  curl -sI https://www.briq.kr/ | grep -i x-vercel-id
  echo "DONE"
else
  echo "!! production build failed — run: git revert --no-edit $MAIN_SHA && git push origin HEAD:main"
  exit 1
fi
