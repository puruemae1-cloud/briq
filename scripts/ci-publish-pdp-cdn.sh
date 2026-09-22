#!/usr/bin/env bash
# Shared CDN publish + verify for weekly brand syncs.
# Usage:
#   scripts/ci-publish-pdp-cdn.sh bv-pdp bv [--chunk 2]
#   scripts/ci-publish-pdp-cdn.sh ys-pdp ys --chunk 4
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DIRS=()
BRANDS=()
CHUNK=4
MAX_WAVES=500

while [[ $# -gt 0 ]]; do
  case "$1" in
    --chunk) CHUNK="${2:?}"; shift 2 ;;
    --max-waves) MAX_WAVES="${2:?}"; shift 2 ;;
    --brand) BRANDS+=("${2:?}"); shift 2 ;;
    *)
      if [[ "$1" == *-pdp ]] || [[ "$1" == *pdp ]]; then
        DIRS+=("$1")
      else
        BRANDS+=("$1")
      fi
      shift
      ;;
  esac
done

if [[ ${#DIRS[@]} -eq 0 ]]; then
  echo "Usage: $0 <dir-pdp> [dir...] [--brand CODE] [--chunk N]" >&2
  exit 2
fi

export SKIP_TAG_FETCH="${SKIP_TAG_FETCH:-}"
export PYTHONUNBUFFERED=1

echo "=== CDN publish dirs=${DIRS[*]} brands=${BRANDS[*]:-none} chunk=$CHUNK ==="

for attempt in 1 2 3 4 5 6 7 8; do
  tip=$(git ls-remote origin refs/tags/product-images | awk '{print $1}' || true)
  if [[ -n "${tip:-}" ]]; then
    git update-ref refs/tags/product-images "$tip" || true
  fi

  python3 scripts/list-missing-pdp-on-cdn.py --dirs "${DIRS[@]}" --write /tmp/ci-cdn-missing.txt || true
  left=$(wc -l < /tmp/ci-cdn-missing.txt | tr -d ' ')
  echo "attempt=$attempt remaining_local_dirs=$left"
  if [[ "${left:-1}" == "0" ]]; then
    break
  fi
  python3 scripts/push-missing-pdp-chunked.py \
    --dirs "${DIRS[@]}" \
    --chunk "$CHUNK" \
    --max-waves "$MAX_WAVES" || true
  sleep 3
done

# Hard fail if any local PDP folder is still absent from the tag.
python3 scripts/list-missing-pdp-on-cdn.py --dirs "${DIRS[@]}"

# Catalog paths must resolve on the tag (skips local disk).
if [[ ${#BRANDS[@]} -gt 0 ]]; then
  args=()
  for b in "${BRANDS[@]}"; do
    args+=(--brand "$b")
  done
  python3 scripts/verify-product-images.py "${args[@]}" --remote --skip-local --all-images
fi

echo "OK CDN publish+verify"
