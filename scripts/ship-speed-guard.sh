#!/usr/bin/env bash
# Push the homepage speed guard workflow + Cursor rule (no app code changes).
set -euo pipefail
cd "$(dirname "$0")/.."

git pull --rebase --autostash origin main
git add .github/workflows/homepage-speed-guard.yml .cursor/rules/homepage-speed.mdc scripts/ship-speed-guard.sh
git commit -m "ci: homepage speed guard (10-min warm ping + TTFB alert) and Cursor rule."
git push origin HEAD:main
git log --oneline -1
echo "DONE"
