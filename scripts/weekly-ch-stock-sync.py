#!/usr/bin/env python3
"""Weekly Chanel stock + catalogue sync for Briq.

  - Discover new SKUs on official GB PLPs (existing scrapers skip complete PDPs)
  - Refresh Korean Product Information for makeup / skincare / fragrance
  - Mark GB sold-out SKUs as inStock=false
  - Rebuild ch-catalog.json

GitHub-hosted runners hard-cap a single job at ~6 hours. This script is
resumable: scrapers skip finished PDPs, enrich uses --resume, and the
workflow re-dispatches on failure/cancellation until the full pass lands.

  python3 scripts/weekly-ch-stock-sync.py
  python3 scripts/weekly-ch-stock-sync.py --phase scrape
  python3 scripts/weekly-ch-stock-sync.py --phase enrich
  python3 scripts/weekly-ch-stock-sync.py --phase stock-build
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCRAPE_SCRIPTS = (
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
)

PHASES = ("scrape", "enrich", "stock-build", "all")


def run(script: str, env: dict[str, str], extra_args: list[str] | None = None) -> None:
    cmd = [sys.executable, "-u", str(ROOT / "scripts" / script)]
    if extra_args:
        cmd.extend(extra_args)
    print(f"→ {' '.join(cmd[2:])}", flush=True)
    subprocess.check_call(cmd, cwd=str(ROOT), env=env)


def run_phase(phase: str, env: dict[str, str]) -> None:
    if phase in ("scrape", "all"):
        for script in SCRAPE_SCRIPTS:
            run(script, env)
    if phase in ("enrich", "all"):
        # Always resume — full beauty re-enrich of ~1.2k SKUs exceeds the
        # GitHub-hosted 6h job cap; retries must continue where we left off.
        run("enrich-ch-beauty-copy.py", env, ["--resume"])
    if phase in ("stock-build", "all"):
        run("sync-ch-gb-stock.py", env)
        run("build-ch-catalog.py", env)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--phase",
        choices=PHASES,
        default="all",
        help="Run one phase (for CI checkpoints) or the full pipeline",
    )
    args = ap.parse_args()
    env = os.environ.copy()
    print(f"weekly-ch-stock-sync phase={args.phase}", flush=True)
    run_phase(args.phase, env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
