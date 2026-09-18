#!/usr/bin/env bash
# After BV chunk scrape finishes: build catalog once (no Vercel). Logs only.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=scripts PYTHONUNBUFFERED=1
LOG="${1:-/tmp/briq-bv-finish.log}"
CHUNK_LOG="${2:-/tmp/briq-bv-chunk.log}"

echo "==== wait for chunk $(date -u +%Y-%m-%dT%H:%M:%SZ) ====" | tee -a "$LOG"
# Wait until no scrape-bv / run-bv-chunk, and chunk log says done
for i in $(seq 1 720); do
  if ! pgrep -f 'run-bv-chunk.sh|scrape-bv-hub.py' >/dev/null 2>&1; then
    if grep -q 'chunk done' "$CHUNK_LOG" 2>/dev/null; then
      break
    fi
  fi
  sleep 30
done

echo "==== build catalog $(date -u +%Y-%m-%dT%H:%M:%SZ) ====" | tee -a "$LOG"
python3 -u scripts/build-bv-catalog.py >>"$LOG" 2>&1
rc=$?
echo "==== build exit=$rc $(date -u +%Y-%m-%dT%H:%M:%SZ) ====" | tee -a "$LOG"

# Summary counts
PYTHONPATH=scripts python3 >>"$LOG" 2>&1 <<'PY'
import json
from pathlib import Path
from bv_config import HUBS
raw = Path("src/data/bv")
print("--- hub status ---")
for h in HUBS:
    p = raw / h["out"]
    if not p.exists():
        print(f"MISSING {h['id']}")
        continue
    d = json.loads(p.read_text())
    lc = d.get("leafCounts") or {}
    exp = [l["id"] for l in h["leaves"]]
    ok = all(lid in lc and (lc[lid].get("official") is None or lc[lid].get("scraped") == lc[lid].get("official")) for lid in exp)
    print(f"{'OK' if ok else '..'} {h['id']:20} n={len(d.get('products') or []):4} leaves={len(lc)}/{len(exp)}")
cat = json.loads((raw / "bv-catalog.json").read_text())
print("catalog", len(cat))
print("imgs", len(list(Path("public/products/bv-pdp").glob("*"))))
PY
exit $rc
