#!/usr/bin/env bash
# Vercel Ignored Build Step.
# Exit 0 → skip this build (commit is behind main).
# Exit 1 → continue building.
set -u

REPO="puruemae1-cloud/briq"
HEAD="${VERCEL_GIT_COMMIT_SHA:-}"
if [ -z "$HEAD" ] && command -v git >/dev/null 2>&1; then
  HEAD="$(git rev-parse HEAD 2>/dev/null || true)"
fi
if [ -z "$HEAD" ]; then
  echo "vercel-skip-stale: no commit SHA — building"
  exit 1
fi

json="$(curl -fsS -H "Accept: application/vnd.github+json" -H "User-Agent: briq-vercel-skip-stale" \
  "https://api.github.com/repos/${REPO}/compare/${HEAD}...main" || true)"
if [ -z "$json" ]; then
  echo "vercel-skip-stale: compare API failed — building"
  exit 1
fi

python3 - "$json" "$HEAD" <<'PY'
import json, sys
raw, head = sys.argv[1], sys.argv[2]
try:
    data = json.loads(raw)
except json.JSONDecodeError:
    print("vercel-skip-stale: bad JSON — building")
    sys.exit(1)
if data.get("message"):
    print("vercel-skip-stale: API", data.get("message"), "— building")
    sys.exit(1)
status = data.get("status")
ahead = int(data.get("ahead_by") or 0)
behind = int(data.get("behind_by") or 0)
print(f"vercel-skip-stale: {head[:12]} vs main status={status} ahead_by={ahead} behind_by={behind}")
# compare HEAD...main: main is `head` of the compare. If main moved on, this commit is behind.
if status == "identical":
    sys.exit(1)
if ahead > 0 and behind == 0:
    print("Skipping stale Vercel build — a newer main commit already exists.")
    sys.exit(0)
sys.exit(1)
PY
