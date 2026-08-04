#!/usr/bin/env python3
"""Restore gitignored PDP image trees from the `product-images` tag.

Weekly CI checkouts `main` without /public/products/*-pdp/. Call this before
scrapers so cached SKUs keep their local files and only new/missing images
are downloaded.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAG = "product-images"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--dirs",
        nargs="+",
        required=True,
        help="Folder names under public/products (e.g. ps-pdp)",
    )
    args = ap.parse_args()

    fetched = subprocess.run(
        ["git", "fetch", "origin", f"refs/tags/{TAG}:refs/tags/{TAG}"],
        cwd=ROOT,
        check=False,
    )
    if fetched.returncode != 0:
        show = subprocess.run(
            ["git", "rev-parse", "--verify", TAG], cwd=ROOT, check=False
        )
        if show.returncode != 0:
            print(f"WARN: tag {TAG} unavailable — continue without restore", flush=True)
            return 0

    for name in args.dirs:
        dest = ROOT / "public" / "products" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        # Extract only this brand tree from the tag
        proc = subprocess.run(
            ["git", "archive", TAG, f"public/products/{name}"],
            cwd=ROOT,
            check=False,
            capture_output=True,
        )
        if proc.returncode != 0:
            print(f"skip restore {name} (not on tag yet)", flush=True)
            continue
        tar = subprocess.run(
            ["tar", "-x", "-C", str(ROOT)],
            input=proc.stdout,
            check=False,
        )
        if tar.returncode != 0:
            print(f"WARN: tar extract failed for {name}", flush=True)
            continue
        n = sum(1 for _ in dest.rglob("*.jpg")) if dest.exists() else 0
        print(f"restored {name} ({n} jpg)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
