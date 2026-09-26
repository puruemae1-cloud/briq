#!/usr/bin/env bash
# Ship the homepage cold-boot fix + speed guard: preview build first, main only
# if it succeeds (a failed main build blocks all deploys incl. catalogue syncs).
set -euo pipefail
cd "$(dirname "$0")/.."

REPO=puruemae1-cloud/briq
BRANCH=perf/home-boot
FILES=(
  src/lib/cart-count.ts
  src/lib/cart-server.ts
  src/lib/homepage-data.ts
  src/app/layout.tsx
  src/components/BackToTop.tsx
  .github/workflows/homepage-speed-guard.yml
  .cursor/rules/homepage-speed.mdc
  scripts/ship-home-boot.sh
  scripts/ship-speed-guard.sh
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

wait_for_production() {
  local sha=$1 prod=""
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
git commit -m "perf: keep brand catalogues out of the layout/homepage cold boot.

Root layout imported getCartCount from cart-server, which statically pulls
@/data/products and every brand catalogue into every page chunk (~9s cold
boot). Layout now uses cookie-only lib/cart-count; homepage-data loads
products via dynamic import on cache miss only. Adds a 10-min homepage
warm/TTFB guard workflow and restores the BackToTop button."
SHA=$(git rev-parse HEAD)

echo "== preview build on $BRANCH ($SHA)"
git push -f origin "HEAD:refs/heads/$BRANCH"
sleep 20
if ! wait_for_vercel "$SHA"; then
  echo
  echo "!! Preview build FAILED — main was NOT touched."
  echo "   Log: https://github.com/$REPO/commit/$SHA (click the Vercel ✗)"
  git reset --soft HEAD~1
  exit 1
fi

echo "== preview OK → push to main"
git pull --rebase --autostash origin main
git push origin HEAD:main
MAIN_SHA=$(git rev-parse HEAD)
sleep 30
if wait_for_production "$MAIN_SHA"; then
  echo "== production deployed — warming + measuring"
  for i in 1 2 3 4; do
    curl -s -o /dev/null -m 60 -w "  try$i ttfb=%{time_starttransfer}s\n" "https://www.briq.kr/?v=$RANDOM$i"
    sleep 1
  done
  echo "DONE"
else
  echo "!! production build failed — run: git revert --no-edit $MAIN_SHA && git push origin HEAD:main"
  exit 1
fi
