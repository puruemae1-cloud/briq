#!/usr/bin/env python3
"""Purge jsDelivr cache for the Briq `product-images` tag.

Live shop loads `/products/*` and `/banners/*` from
`cdn.jsdelivr.net/gh/...@product-images/...`. When the git tag is force-updated
with the same paths, jsDelivr can keep serving stale bytes for hours/days —
homepage banners looked “not updated” even though GitHub raw was correct.

  python3 scripts/purge-jsdelivr-media.py
  python3 scripts/purge-jsdelivr-media.py --paths public/banners/rot-hero-1.jpg
  python3 scripts/purge-jsdelivr-media.py --dirs banners ch-pdp
"""
from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "puruemae1-cloud/briq"
TAG = "product-images"
PURGE_BASE = f"https://purge.jsdelivr.net/gh/{REPO}@{TAG}"


def purge(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=45) as r:
            r.read(200)
        return True
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"  purge fail {url}: {e}", flush=True)
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--paths",
        nargs="*",
        default=[],
        help="Repo-relative paths under the tag (e.g. public/banners/rot-hero-1.jpg)",
    )
    ap.add_argument(
        "--dirs",
        nargs="*",
        default=[],
        help=(
            "Local folders to expand: 'banners' → public/banners/**/*.jpg, "
            "or a product dir name like ch-pdp → public/products/ch-pdp/**"
        ),
    )
    ap.add_argument(
        "--package-only",
        action="store_true",
        help="Only purge the package tip (no per-file URLs)",
    )
    args = ap.parse_args()

    urls = [PURGE_BASE]
    paths: list[str] = list(args.paths or [])

    for name in args.dirs or []:
        if name == "banners":
            root = ROOT / "public" / "banners"
            prefix = "public/banners"
        else:
            root = ROOT / "public" / "products" / name
            prefix = f"public/products/{name}"
        if not root.is_dir():
            print(f"skip missing {root}", flush=True)
            continue
        for p in root.rglob("*"):
            if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                rel = str(p.relative_to(ROOT)).replace("\\", "/")
                paths.append(rel)

    if not args.package_only:
        for rel in sorted(set(paths)):
            rel = rel.lstrip("/")
            if not rel.startswith("public/"):
                rel = f"public/{rel}"
            urls.append(f"{PURGE_BASE}/{rel}")

    print(f"Purging {len(urls)} jsDelivr URL(s) for @{TAG}…", flush=True)
    ok = sum(1 for u in urls if purge(u))
    print(f"purge done {ok}/{len(urls)}", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
