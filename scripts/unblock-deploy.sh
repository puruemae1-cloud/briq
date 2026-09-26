#!/usr/bin/env bash
# Revert the failed homepage-ISR commit so Vercel production deploys resume.
set -euo pipefail
cd "$(dirname "$0")/.."

BAD=cea771790a

echo "== fetch"
git fetch origin main

if git merge-base --is-ancestor "$BAD" HEAD && ! git log --oneline origin/main | grep -q "Revert \"perf: serve homepage statically"; then
  echo "== rebase onto origin/main"
  git pull --rebase --autostash origin main
  echo "== revert $BAD"
  git revert --no-edit "$BAD"
  echo "== push"
  git push origin HEAD:main
else
  echo "already reverted — nothing to push"
fi

if git stash list | grep -q "wip-before-revert"; then
  echo "== restore stashed WIP"
  ref=$(git stash list | grep "wip-before-revert" | head -1 | cut -d: -f1)
  git stash pop "$ref" || echo "!! stash pop had conflicts — tell the agent"
fi

echo
git log --oneline -3
echo "DONE"
