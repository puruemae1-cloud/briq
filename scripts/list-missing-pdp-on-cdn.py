#!/usr/bin/env python3
"""List local PDP folders that are missing from the product-images git tag.

  python3 scripts/list-missing-pdp-on-cdn.py --dirs ce-pdp gg-pdp
  python3 scripts/list-missing-pdp-on-cdn.py --dirs ce-pdp --write tmp/ce-missing-on-cdn.txt

Exit 1 when any folder is missing (useful as a CI / weekly guard).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAG = "product-images"


def tag_dirs(brand: str) -> set[str]:
    prefix = f"public/products/{brand}"
    r = subprocess.run(
        ["git", "ls-tree", "-d", "--name-only", f"{TAG}:{prefix}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        return set()
    return {line.strip() for line in r.stdout.splitlines() if line.strip()}


def local_dirs(brand: str) -> set[str]:
    root = ROOT / "public" / "products" / brand
    if not root.is_dir():
        return set()
    return {p.name for p in root.iterdir() if p.is_dir()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="+", required=True, help="e.g. ce-pdp gg-pdp")
    ap.add_argument("--write", help="Write missing folder names (one per line)")
    ap.add_argument(
        "--fetch",
        action="store_true",
        help="Fetch product-images tag from origin first",
    )
    args = ap.parse_args()

    if args.fetch:
        subprocess.run(
            ["git", "fetch", "origin", f"refs/tags/{TAG}:refs/tags/{TAG}"],
            cwd=ROOT,
            check=False,
        )

    all_missing: list[str] = []
    for brand in args.dirs:
        missing = sorted(local_dirs(brand) - tag_dirs(brand))
        print(f"{brand}: local={len(local_dirs(brand))} on_tag={len(tag_dirs(brand))} missing={len(missing)}")
        for name in missing[:20]:
            print(f"  {name}")
        if len(missing) > 20:
            print(f"  … +{len(missing) - 20} more")
        all_missing.extend(missing)

    if args.write:
        path = Path(args.write)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(all_missing) + ("\n" if all_missing else ""))
        print(f"wrote {path} ({len(all_missing)})")

    return 1 if all_missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
