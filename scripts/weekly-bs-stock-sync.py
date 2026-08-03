#!/usr/bin/env python3
"""Weekly Belstaff sync for Briq.

Re-scrapes men / women / icons / motorcycle / sale collections, rebuilds the
catalogue, and prunes orphan PDP image folders.

  - Restock: Shopify `variants.available` refreshed on scrape
  - New SKUs: merged in, stamped with fresh registeredAt on build
  - Discontinued: mens scrape replaces raw; missing handles drop on rebuild

Designed for GitHub Actions (cron) and local runs:
  python3 scripts/weekly-bs-stock-sync.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "src/data/bs/bs-catalog-raw.json"
IMG_ROOT = ROOT / "public/products/bs-pdp"

SCRIPTS = (
    "scrape-bs-mens.py",
    "scrape-bs-womens.py",
    "scrape-bs-extra.py",
    "build-bs-catalog.py",
)


def run(script: str) -> None:
    print(f"→ {script}", flush=True)
    subprocess.check_call(
        [sys.executable, "-u", str(ROOT / "scripts" / script)],
        cwd=str(ROOT),
    )


def prune_images() -> int:
    if not RAW_PATH.exists() or not IMG_ROOT.exists():
        return 0
    raw = json.loads(RAW_PATH.read_text())
    keep = {
        str(p.get("handle"))
        for p in (raw.get("products") or [])
        if p.get("handle")
    }
    removed = 0
    for d in list(IMG_ROOT.iterdir()):
        if d.is_dir() and d.name not in keep:
            shutil.rmtree(d, ignore_errors=True)
            removed += 1
    if removed:
        print(f"pruned {removed} orphan bs-pdp folders", flush=True)
    return removed


def main() -> None:
    for script in SCRIPTS[:-1]:
        run(script)
    prune_images()
    run(SCRIPTS[-1])
    print("Belstaff weekly sync complete.", flush=True)


if __name__ == "__main__":
    main()
