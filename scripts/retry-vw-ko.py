#!/usr/bin/env python3
"""Retry Vivienne Westwood Korean PDP copy family-by-family when gtx recovers.

Skips watches (curated via seed-vw-watches-ko.py). Safe to re-run.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "tmp/vw-ko-retry-state.json"
LOG = ROOT / "tmp/vw-ko-retry.log"

FAMILIES = [
    "bags",
    "shoes",
    "jewellery",
    "accessories",
    "rtw",
    "worlds-end",
]


def log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    line = msg.rstrip()
    print(line, flush=True)
    with LOG.open("a") as f:
        f.write(line + "\n")


def probe() -> bool:
    q = "leather shoulder bag"
    url = (
        "https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl=en&tl=ko&dt=t&q={urllib.parse.quote(q)}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.loads(r.read().decode())
        out = "".join(part[0] for part in data[0] if part and part[0])
        return bool(out.strip()) and any("\uac00" <= c <= "\ud7a3" for c in out)
    except urllib.error.HTTPError as e:
        log(f"probe HTTP {e.code}")
        return False
    except Exception as e:
        log(f"probe err {e}")
        return False


def load_state() -> dict:
    if STATE.is_file():
        try:
            return json.loads(STATE.read_text())
        except Exception:
            pass
    return {"completed": []}


def save_state(st: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, indent=2) + "\n")


def main() -> int:
    st = load_state()
    done = set(st.get("completed") or [])
    pending = [f for f in FAMILIES if f not in done]
    if not pending:
        log("ALL_FAMILIES_DONE")
        return 0
    if not probe():
        log("RATE_LIMITED — retry later")
        return 2
    fam = pending[0]
    log(f"NEXT family={fam}")
    env = os.environ.copy()
    env.pop("BRIQ_FAST_BUILD", None)
    env["VW_LEAF_FILTER"] = fam
    env["PYTHONUNBUFFERED"] = "1"
    r = subprocess.run([sys.executable, "scripts/build-vw-catalog.py"], cwd=ROOT, env=env)
    if r.returncode != 0:
        log(f"FAIL family={fam} rc={r.returncode}")
        return r.returncode
    done.add(fam)
    st["completed"] = sorted(done)
    st["lastFamily"] = fam
    save_state(st)
    log(f"OK family={fam} remaining={len(FAMILIES) - len(done)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
