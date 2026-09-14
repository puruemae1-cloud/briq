#!/usr/bin/env bash
# Shared commit/push helper for weekly brand sync workflows.
# Usage: scripts/ci-commit-push.sh "commit subject" <paths...>
set -euo pipefail

SUBJECT="${1:?commit subject required}"
shift

git config user.name "briq-bot"
git config user.email "briq-bot@users.noreply.github.com"

git add -A "$@"
if git diff --staged --quiet; then
  echo "No catalog changes."
  exit 0
fi

# Re-run nav/PLP guard when weekly syncs touch shop routing surfaces.
if git diff --staged --name-only | grep -Eq '(^|/)(src/data/categories\.ts|src/data/home-banners\.ts|src/app/shop/)'; then
  python3 scripts/check-nav-shop-links.py --fail
fi

# Avoid non-fast-forward if another weekly job pushed first.
pull_rebase() {
  git pull --rebase --autostash origin main || git pull --rebase --autostash origin HEAD || true
}

pull_rebase

git commit -m "$(cat <<EOF
${SUBJECT}

EOF
)"

for attempt in 1 2 3; do
  if git push origin HEAD:main; then
    echo "Pushed catalogue changes to main."
    exit 0
  fi
  echo "Push attempt ${attempt} failed — rebasing and retrying…" >&2
  pull_rebase
done

echo "Push failed after 3 attempts." >&2
exit 1
