#!/usr/bin/env python3
"""Weekly Arc'teryx sync for Briq (outdoor apparel + stock + rebuild).

Designed for cron / GitHub Actions:
  python3 scripts/weekly-ax-stock-sync.py

Steps:
  1) Refresh outdoor apparel PLP feed (new styles)
  2) Playwright-enrich PDPs (colour×size stock, galleries, copy)
  3) Rebuild ax-apparel-catalog.ts
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
    # Playwright package path on macOS user install
    site = Path.home() / "Library/Python/3.9/lib/python/site-packages"
    if site.exists():
        env["PYTHONPATH"] = f"{site}:{env.get('PYTHONPATH','')}"
    subprocess.check_call(cmd, cwd=str(ROOT), env=env)


def main() -> None:
    run("scrape-ax-outdoor-apparel.py")
    run("enrich-ax-apparel-playwright.py")
    run("build-ax-apparel-catalog.py")
    print("Arc'teryx weekly sync complete.", flush=True)


if __name__ == "__main__":
    main()
