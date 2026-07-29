#!/usr/bin/env python3
"""Weekly Burberry Women stock/catalogue sync for Briq.

Re-scrapes UK PLPs + PDPs, rebuilds bb-catalog.ts (preserving registeredAt).
Designed for GitHub Actions (cron) and local runs:
  python3 scripts/weekly-bb-stock-sync.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(script: str) -> None:
    print(f"→ {script}", flush=True)
    subprocess.check_call([sys.executable, str(ROOT / "scripts" / script)], cwd=str(ROOT))


def main() -> None:
    run("scrape-bb-women.py")
    run("build-bb-catalog.py")
    print("Burberry weekly sync complete.", flush=True)


if __name__ == "__main__":
    main()
