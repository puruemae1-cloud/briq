#!/usr/bin/env bash
# Shared commit/push helper for weekly brand sync workflows.
# Usage: scripts/ci-commit-push.sh "commit subject" <paths...>
set -euo pipefail

SUBJECT="${1:?commit subject required}"
shift

# vercel-skip-stale.sh skips builds for this marker; catalog-deploy.yml ships
# all marked commits with one deploy after the sync batch finishes.
MARKER="[catalog-sync]"
case "$SUBJECT" in
  *"$MARKER"*) ;;
  *) SUBJECT="${SUBJECT} ${MARKER}" ;;
esac

git config user.name "briq-bot"
git config user.email "briq-bot@users.noreply.github.com"

# Bags/shoes PLPs read per-brand slices, so option-level stock must be
# re-extracted whenever a sync rewrites the full brand catalogue.
for path in "$@"; do
  if [[ "$path" =~ ^src/data/([a-z]{2})/?$ ]]; then
    key="${BASH_REMATCH[1]}"
    python3 scripts/extract-bags-catalogs.py "$key" >/dev/null
    python3 scripts/extract-shoes-catalogs.py "$key" >/dev/null
  fi
done

git add -A "$@"
if git diff --staged --quiet; then
  echo "No catalog changes."
  exit 0
fi

# Re-run nav/PLP guard when weekly syncs touch shop routing surfaces.
if git diff --staged --name-only | grep -Eq '(^|/)(src/data/categories\.ts|src/data/home-banners\.ts|src/app/shop/)'; then
  python3 scripts/check-nav-shop-links.py --fail
fi

# Commit before rebasing: an autostash pull would unstage the sync output
# and leave nothing to commit when another weekly job pushed first.
git commit -m "$(cat <<EOF
${SUBJECT}

EOF
)"

pull_rebase() {
  if ! git pull --rebase --autostash origin main; then
    git rebase --abort || true
    echo "Rebase onto origin/main failed." >&2
    return 1
  fi
}

for attempt in 1 2 3; do
  pull_rebase || continue
  if git push origin HEAD:main; then
    echo "Pushed catalogue changes to main."
    exit 0
  fi
  echo "Push attempt ${attempt} failed — rebasing and retrying…" >&2
done

echo "Push failed after 3 attempts." >&2
exit 1
