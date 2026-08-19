#!/usr/bin/env python3
"""Weekly Chanel stock + catalogue sync for Briq.

  - Discover new SKUs on official GB PLPs (existing scrapers skip complete PDPs)
  - Refresh Korean Product Information for makeup / skincare / fragrance
  - Mark GB sold-out SKUs as inStock=false
  - Rebuild ch-catalog.json

  python3 scripts/weekly-ch-stock-sync.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# PLP discovery first (cached PDPs are reused), then copy/stock, then build.
SCRIPTS = (
    "scrape-ch-makeup.py",
    "scrape-ch-skincare.py",
    "scrape-ch-fragrance.py",
    "scrape-ch-handbags.py",
    "scrape-ch-rtw.py",
    "scrape-ch-shoes.py",
    "scrape-ch-slg.py",
    "scrape-ch-jewellery.py",
    "scrape-ch-fine-jewellery.py",
    "scrape-ch-high-jewellery.py",
    "scrape-ch-sunglasses.py",
    "scrape-ch-other-acc.py",
    "scrape-ch-watches.py",
    "enrich-ch-beauty-copy.py",
    "sync-ch-gb-stock.py",
    "build-ch-catalog.py",
)


def run(script: str, env: dict[str, str]) -> None:
    print(f"→ {script}", flush=True)
    subprocess.check_call(
        [sys.executable, "-u", str(ROOT / "scripts" / script)],
        cwd=str(ROOT),
        env=env,
    )


def main() -> int:
    env = os.environ.copy()
    for script in SCRIPTS:
        run(script, env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
