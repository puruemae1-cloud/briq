#!/usr/bin/env python3
"""Weekly Prada catalogue sync (RTW sizes + stock refresh entrypoint).

When expanding this job, always rebuild via build-pr-catalog.py (or run
patch-pr-rtw-short-size-charts.py) so Short (…S) size-guide tabs stay in sync.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(script: str, extra: list[str] | None = None) -> None:
    cmd = [sys.executable, "-u", str(ROOT / "scripts" / script), *(extra or [])]
    print(f"→ {' '.join(cmd)}", flush=True)
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    subprocess.check_call(cmd, cwd=str(ROOT), env=env)


def main() -> None:
    # Size-guide Short (S) enrichment is also invoked at the end of
    # build-pr-catalog.py for --only rtw / mens-rtw / all.
    run("patch-pr-rtw-short-size-charts.py")
    print("Prada weekly size-chart sync complete.", flush=True)


if __name__ == "__main__":
    main()
