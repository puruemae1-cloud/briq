#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/scripts:${PYTHONPATH:-}"
python3 - <<'PY'
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path("scripts").resolve()))
from vw_config import VW_FAMILY_SCRAPERS

for fam in VW_FAMILY_SCRAPERS:
    print(f"== {fam} ==", flush=True)
    r = subprocess.run(
        [sys.executable, "scripts/scrape-vw-family.py", "--family", fam],
        cwd=str(Path.cwd()),
    )
    if r.returncode != 0:
        print(f"WARN {fam} failed rc={r.returncode}", flush=True)

r = subprocess.run([sys.executable, "scripts/build-vw-catalog.py"])
raise SystemExit(r.returncode)
PY
echo "OK VW weekly sync"
