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
  df -h / | tail -1
  free -m 2>/dev/null | sed -n 2p || true
  tip=$(git ls-remote origin refs/tags/product-images | awk '{print $1}' || true)
  if [[ -n "${tip:-}" ]]; then
    # Other brand syncs move the tag concurrently; building on a stale tip
    # makes the next push re-upload the whole image tree (HTTP 500).
    git cat-file -e "${tip}^{commit}" 2>/dev/null \
      || git fetch --no-tags origin refs/tags/product-images || true
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
  # The folder-level gap check misses new frames added to folders already on
  # the tag; republish those folders before the hard check.
  python3 scripts/verify-product-images.py "${args[@]}" --remote --skip-local --all-images \
    --write-missing-dirs /tmp/ci-tag-file-gaps.txt >/dev/null || true
  if [[ -s /tmp/ci-tag-file-gaps.txt ]]; then
    echo "republishing $(wc -l < /tmp/ci-tag-file-gaps.txt | tr -d ' ') folder(s) with files missing on the tag"
    # One push per batch: a whole-brand pack (GBs) fails on GitHub's side.
    rm -f /tmp/ci-tag-gap-batch.*
    split -l "${GAP_BATCH:-40}" /tmp/ci-tag-file-gaps.txt /tmp/ci-tag-gap-batch.
    for batch in /tmp/ci-tag-gap-batch.*; do
      python3 scripts/push-product-images-tag.py --dirs "${DIRS[@]}" --merge \
        --only-file "$batch" --skip-purge --skip-whiten || true
    done
  fi
  python3 scripts/verify-product-images.py "${args[@]}" --remote --skip-local --all-images
fi

echo "OK CDN publish+verify"
