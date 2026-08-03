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

# Avoid non-fast-forward if another weekly job pushed first.
git pull --rebase --autostash origin HEAD || git pull --rebase --autostash origin main || true

git commit -m "$(cat <<EOF
${SUBJECT}

EOF
)"

git push origin HEAD:main
echo "Pushed catalogue changes to main."
