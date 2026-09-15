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
if r.returncode != 0:
    raise SystemExit(r.returncode)

# Bags hub must keep colourways in category=bags (not accessories).
r = subprocess.run(
    [sys.executable, "scripts/check-vw-bags-coverage.py", "--fail"],
    cwd=str(Path.cwd()),
)
if r.returncode != 0:
    raise SystemExit(r.returncode)

# Accessories/jewellery hub must keep full leaf scrape (not just *-all hubs).
r = subprocess.run(
    [sys.executable, "scripts/check-vw-accessories-coverage.py", "--fail"],
    cwd=str(Path.cwd()),
)
if r.returncode != 0:
    raise SystemExit(r.returncode)

# PDP Korean copy for accessories must not stay English after scrape/build.
# Retry loop: Bing/gtx flakes mid-batch; cache makes each round resume safely.
last_rc = 1
for attempt in range(1, 6):
    print(f"== accessories KO retranslate attempt {attempt}/5 ==", flush=True)
    r = subprocess.run(
        [sys.executable, "scripts/retranslate-vw-ko.py", "--category", "accessories"],
        cwd=str(Path.cwd()),
    )
    last_rc = r.returncode
    qa = subprocess.run(
        [sys.executable, "scripts/check-vw-accessories-korean.py", "--fail", "--max-bad", "0"],
        cwd=str(Path.cwd()),
    )
    if qa.returncode == 0:
        raise SystemExit(0)
    print(f"WARN attempt {attempt}: retranslate_rc={last_rc} qa_rc={qa.returncode}", flush=True)

print("ERROR accessories KO still English after 5 retranslate attempts", flush=True)
raise SystemExit(last_rc or 1)
PY
echo "OK VW weekly sync"
