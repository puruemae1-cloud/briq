#!/usr/bin/env python3
"""Weekly Burberry stock + catalogue sync for Briq.

Re-scrapes UK PLPs + PDPs (forcing size/stock refresh), translates
shop copy EN→KO, then rebuilds bb-catalog.ts while preserving
registeredAt for existing styles.

Covers:
  - option-level sold-out / restock (isInStock on each size)
  - new colourways / styles appearing on Burberry PLPs
  - price + collection membership updates
  - women / men / children / gifts / scarves / bag collections / beauty

Designed for GitHub Actions (cron) and local runs:
  BB_REFRESH_STOCK=1 python3 scripts/weekly-bb-stock-sync.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCRIPTS = (
    "scrape-bb-women.py",
    "scrape-bb-men.py",
    "scrape-bb-children.py",
    "scrape-bb-gifts.py",
    "scrape-bb-scarves.py",
    "scrape-bb-bags-collections.py",
    "scrape-bb-beauty.py",
    "translate-bb-catalog.py",
    "build-bb-catalog.py",
)


def run(script: str, env: dict[str, str]) -> None:
    print(f"→ {script}", flush=True)
    cmd = [sys.executable, str(ROOT / "scripts" / script)]
    if script == "translate-bb-catalog.py":
        cmd.extend(["--workers", "4"])
    subprocess.check_call(cmd, cwd=str(ROOT), env=env)


def main() -> None:
    env = os.environ.copy()
    # Always refresh PDP stock/prices on the weekly job.
    env["BB_REFRESH_STOCK"] = "1"
    print("BB_REFRESH_STOCK=1 (re-fetch size availability + prices)", flush=True)

    for script in SCRIPTS:
        run(script, env)

    print("Checking Burberry Korean copy…", flush=True)
    subprocess.check_call(
        [
            sys.executable,
            str(ROOT / "scripts" / "translate-bb-catalog.py"),
            "--check-catalog",
        ],
        cwd=str(ROOT),
        env=env,
    )
    print("Burberry weekly sync complete.", flush=True)


if __name__ == "__main__":
    main()
