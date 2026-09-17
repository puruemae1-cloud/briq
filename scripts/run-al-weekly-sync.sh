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
from al_config import AL_FAMILY_ORDER

for fam in AL_FAMILY_ORDER:
    print(f"== {fam} ==", flush=True)
    r = subprocess.run(
        [sys.executable, "scripts/scrape-al-family.py", "--family", fam],
        cwd=str(Path.cwd()),
    )
    if r.returncode != 0:
        print(f"WARN {fam} failed rc={r.returncode}", flush=True)

r = subprocess.run([sys.executable, "scripts/build-al-catalog.py"])
if r.returncode != 0:
    raise SystemExit(r.returncode)

# Korean QA — fail weekly sync if EN leftovers remain.
last_rc = 1
for attempt in range(1, 6):
    print(f"== AL KO retranslate attempt {attempt}/5 ==", flush=True)
    r = subprocess.run(
        [sys.executable, "scripts/retranslate-al-ko.py", "--category", "all"],
        cwd=str(Path.cwd()),
    )
    last_rc = r.returncode
    qa = subprocess.run(
        [sys.executable, "scripts/check-al-korean.py", "--fail", "--max-bad", "0"],
        cwd=str(Path.cwd()),
    )
    if qa.returncode == 0:
        raise SystemExit(0)
    print(f"WARN attempt {attempt}: retranslate_rc={last_rc} qa_rc={qa.returncode}", flush=True)

print("ERROR AL KO still English after 5 retranslate attempts", flush=True)
raise SystemExit(last_rc or 1)
PY
echo "OK AL weekly sync"
