#!/usr/bin/env python3
"""Weekly London Undercover sync for Briq.

Re-scrapes umbrella + lifestyle Shopify collections (replace raw → drop
discontinued), downloads new images, rebuilds catalogues.

  python3 scripts/weekly-lu-stock-sync.py
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UMBRELLA_RAW = ROOT / "src/data/lu/lu-pdp-raw.json"
LIFESTYLE_RAW = ROOT / "src/data/lu/lu-lifestyle-pdp-raw.json"
IMG_ROOT = ROOT / "public/products/lu-pdp"


def run(script: str) -> None:
    print(f"→ {script}", flush=True)
    subprocess.check_call(
        [sys.executable, "-u", str(ROOT / "scripts" / script)],
        cwd=str(ROOT),
    )


def prune_images() -> int:
    if not IMG_ROOT.exists():
        return 0
    keep: set[str] = set()
    for path in (UMBRELLA_RAW, LIFESTYLE_RAW):
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        for p in data.values():
            h = p.get("handle")
            if h:
                keep.add(str(h))
    removed = 0
    for d in list(IMG_ROOT.iterdir()):
        if d.is_dir() and d.name not in keep:
            shutil.rmtree(d, ignore_errors=True)
            removed += 1
    if removed:
        print(f"pruned {removed} orphan lu-pdp folders", flush=True)
    return removed


def main() -> None:
    run("scrape-lu.py")
    prune_images()
    run("build-lu-catalog.py")
    run("build-lu-lifestyle-catalog.py")
    print("London Undercover weekly sync complete.", flush=True)


if __name__ == "__main__":
    main()
