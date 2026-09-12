#!/usr/bin/env python3
"""List local PDP folders that are missing from the product-images git tag.

  python3 scripts/list-missing-pdp-on-cdn.py --dirs ce-pdp gg-pdp
  python3 scripts/list-missing-pdp-on-cdn.py --dirs ce-pdp --write tmp/ce-missing-on-cdn.txt

Arc'teryx (and similar) store colourways under brand/sku/colour/:
  python3 scripts/list-missing-pdp-on-cdn.py --dirs axa-pdp axg-pdp ax-pdp axo-pdp --nested \\
    --write tmp/ax-missing-on-cdn.txt

With --nested, --write lists product (sku) folder names so
push-product-images-tag.py --only-file can re-sync whole SKUs that gained colours.

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


def tag_nested_colour_dirs(brand: str) -> set[str]:
    """Return ``sku/colour`` paths present on the tag."""
    prefix = f"public/products/{brand}"
    r = subprocess.run(
        ["git", "ls-tree", "-d", "-r", "--name-only", f"{TAG}:{prefix}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        return set()
    out: set[str] = set()
    for line in r.stdout.splitlines():
        name = line.strip()
        if not name or "/" not in name:
            continue
        # sku/colour (ignore deeper)
        parts = name.split("/")
        if len(parts) >= 2:
            out.add(f"{parts[0]}/{parts[1]}")
    return out


def local_dirs(brand: str) -> set[str]:
    root = ROOT / "public" / "products" / brand
    if not root.is_dir():
        return set()
    return {p.name for p in root.iterdir() if p.is_dir()}


def local_nested_colour_dirs(brand: str) -> set[str]:
    root = ROOT / "public" / "products" / brand
    if not root.is_dir():
        return set()
    out: set[str] = set()
    for sku in root.iterdir():
        if not sku.is_dir():
            continue
        for colour in sku.iterdir():
            if not colour.is_dir():
                continue
            primary = colour / "1.jpg"
            if primary.is_file() and primary.stat().st_size >= 800:
                out.add(f"{sku.name}/{colour.name}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="+", required=True, help="e.g. ce-pdp gg-pdp axa-pdp")
    ap.add_argument("--write", help="Write missing folder names (one per line)")
    ap.add_argument(
        "--nested",
        action="store_true",
        help="Compare brand/sku/colour (Arc'teryx). Write product sku ids for push.",
    )
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
        if args.nested:
            local = local_nested_colour_dirs(brand)
            on_tag = tag_nested_colour_dirs(brand)
            missing_colours = sorted(local - on_tag)
            # Push unit is the product (sku) folder
            missing_skus = sorted({c.split("/", 1)[0] for c in missing_colours})
            print(
                f"{brand}: local_colours={len(local)} on_tag_colours={len(on_tag)} "
                f"missing_colours={len(missing_colours)} missing_skus={len(missing_skus)}"
            )
            for name in missing_colours[:20]:
                print(f"  {name}")
            if len(missing_colours) > 20:
                print(f"  … +{len(missing_colours) - 20} more")
            all_missing.extend(missing_skus)
        else:
            missing = sorted(local_dirs(brand) - tag_dirs(brand))
            print(
                f"{brand}: local={len(local_dirs(brand))} on_tag={len(tag_dirs(brand))} "
                f"missing={len(missing)}"
            )
            for name in missing[:20]:
                print(f"  {name}")
            if len(missing) > 20:
                print(f"  … +{len(missing) - 20} more")
            all_missing.extend(missing)

    if args.write:
        path = Path(args.write)
        path.parent.mkdir(parents=True, exist_ok=True)
        # de-dupe while preserving order
        seen: set[str] = set()
        ordered: list[str] = []
        for name in all_missing:
            if name in seen:
                continue
            seen.add(name)
            ordered.append(name)
        path.write_text("\n".join(ordered) + ("\n" if ordered else ""))
        print(f"wrote {path} ({len(ordered)})")

    return 1 if all_missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
