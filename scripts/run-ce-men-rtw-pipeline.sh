#!/usr/bin/env bash
# Celine men's RTW pipeline: scrape official leaves, rebuild catalog, and stage deployable outputs.
set -euo pipefail
cd "$(dirname "$0")/.."
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/Library/Caches/ms-playwright}"
export PYTHONUNBUFFERED=1
export PATH="/usr/bin:/bin:/usr/local/bin:$HOME/.local/bin:$HOME/.local/node/bin:$PATH"
LOG=/tmp/ce-men-rtw-pipeline.log
STATUS=/tmp/ce-men-rtw-STATUS
exec >>"$LOG" 2>&1

echo "=== celine men rtw pipeline start $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
touch "$STATUS"

run_step() {
  local stamp="$1"; shift
  if grep -q "${stamp}_OK" "$STATUS" 2>/dev/null; then
    echo "skip $stamp"
    return 0
  fi
  echo "=== $stamp ==="
  set +e
  "$@"
  local st=$?
  set -e
  echo "EXIT_${stamp}:$st"
  if [[ "$st" -ne 0 ]]; then
    echo "${stamp}_FAIL:$st" >>"$STATUS"
    exit "$st"
  fi
  echo "${stamp}_OK" >>"$STATUS"
}

run_step SCRAPE python3 scripts/scrape-celine-men-rtw.py
run_step BUILD python3 scripts/build-ce-catalog.py

run_step KO python3 - <<'PY'
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "scripts"))
from ko_qa import MAX_KO_EN_RATIO, check_brand  # type: ignore

bad = check_brand("ce", max_ratio=MAX_KO_EN_RATIO)
print(f"ce: bad={len(bad)}", flush=True)
for brand, pid, field, ratio, snippet in bad[:40]:
    print(f"  {brand} {pid} {field} en_ratio={ratio:.2f} {snippet}", flush=True)
if bad:
    raise SystemExit(1)
PY

echo "=== STAGE DEPLOYABLE FILES ==="
git add \
  scripts/celine_common.py \
  scripts/celine_config.py \
  scripts/build-ce-catalog.py \
  scripts/scrape-celine-men-rtw.py \
  scripts/run-ce-men-rtw-pipeline.sh \
  src/data/ce/ce-catalog.json \
  src/data/ce/ce-catalog.ts \
  src/data/ce/ce-men-rtw-catalog-raw.json \
  src/data/ce/ce-translate-cache.json \
  public/products/ce-pdp \
  || true

echo "=== celine men rtw pipeline done $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
