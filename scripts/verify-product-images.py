#!/usr/bin/env python3
"""Verify catalog PDP image paths exist locally and on the product-images tag.

Prevents the failure mode where scrape/build writes public/products/*-pdp/
(gitignored) and updates the catalog, but never publishes the tag that Vercel
serves via raw.githubusercontent.com/.../product-images/...

  python3 scripts/verify-product-images.py --brand gc
  python3 scripts/verify-product-images.py --brand bb --remote --all-images
  python3 scripts/verify-product-images.py --all-brands --remote

Exit 1 if any primary image is missing locally (default) or on the tag (--remote).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAG = "product-images"
PRODUCTS_PREFIX = "public/products/"

BRAND_CATALOGS: dict[str, list[Path]] = {
    "gc": [ROOT / "src/data/gc/gc-catalog.json"],
    "bb": [ROOT / "src/data/bb/bb-catalog.json"],
    "ps": [ROOT / "src/data/ps/ps-catalog.json"],
    "ch": [ROOT / "src/data/ch/ch-catalog.json"],
    "pr": [ROOT / "src/data/pr/pr-catalog.json"],
    "bs": [ROOT / "src/data/bs/bs-catalog.json"],
    "ax": [ROOT / "src/data/ax/ax-catalog.json"],
    "axa": [ROOT / "src/data/ax/ax-apparel-catalog.json"],
    "axo": [ROOT / "src/data/ax/ax-outlet-catalog.json"],
    "axg": [ROOT / "src/data/ax/ax-gear-catalog.json"],
    "gg": [ROOT / "src/data/gg/gg-catalog.ts"],
    "cw": [ROOT / "src/data/cw/cw-catalog.ts"],
    "lu": [
        ROOT / "src/data/lu/lu-catalog.ts",
        ROOT / "src/data/lu/lu-lifestyle-catalog.ts",
    ],
}

PATH_RE = re.compile(r"/products/[a-z0-9][\w.-]*-pdp/[^\"'\\s)]+")


def _load_json_products(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "products" in data:
        return list(data["products"])
    raise SystemExit(f"Unexpected catalog shape: {path}")


def _load_ts_paths(path: Path) -> list[dict]:
    text = path.read_text(errors="ignore")
    found = []
    for raw in PATH_RE.findall(text):
        p = raw.rstrip(".,;")
        if p.endswith((".jpg", ".jpeg", ".png", ".webp")):
            found.append(p)
    uniq: list[str] = []
    seen: set[str] = set()
    for p in found:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    if not uniq:
        return []
    return [{"id": path.name, "image": uniq[0], "images": uniq}]


def load_products(brand: str) -> list[dict]:
    paths = BRAND_CATALOGS.get(brand)
    if not paths:
        raise SystemExit(
            f"Unknown brand: {brand}. Choose from {', '.join(sorted(BRAND_CATALOGS))}"
        )
    products: list[dict] = []
    for path in paths:
        if not path.is_file():
            raise SystemExit(f"Missing catalog: {path}")
        if path.suffix == ".json":
            products.extend(_load_json_products(path))
        else:
            products.extend(_load_ts_paths(path))
    return products


def primary_image(product: dict) -> str | None:
    img = product.get("image") or product.get("localImage")
    if isinstance(img, str) and img.startswith("/products/"):
        return img
    images = product.get("images")
    if isinstance(images, list) and images:
        first = images[0]
        if isinstance(first, str) and first.startswith("/products/"):
            return first
    return None


def all_product_images(product: dict) -> list[str]:
    out: list[str] = []
    for key in ("image", "hoverImage", "localImage", "localHover"):
        v = product.get(key)
        if isinstance(v, str) and v.startswith("/products/"):
            out.append(v)
    for key in ("images", "localImages"):
        v = product.get(key)
        if isinstance(v, list):
            for item in v:
                if isinstance(item, str) and item.startswith("/products/"):
                    out.append(item)
    # dedupe preserve order
    seen: set[str] = set()
    uniq: list[str] = []
    for p in out:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq


def path_on_disk(web_path: str) -> Path:
    # /products/gc-pdp/CODE/1.jpg → public/products/gc-pdp/CODE/1.jpg
    rel = web_path.lstrip("/")
    return ROOT / "public" / rel


def tag_blob_path(web_path: str) -> str:
    return PRODUCTS_PREFIX + web_path.lstrip("/").removeprefix("products/")


def list_tag_paths(prefix: str = PRODUCTS_PREFIX) -> set[str]:
    subprocess.run(
        ["git", "fetch", "origin", f"refs/tags/{TAG}:refs/tags/{TAG}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    proc = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", TAG, prefix],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(
            f"Cannot list {TAG} ({proc.stderr.strip() or proc.stdout.strip()}). "
            "Fetch the tag or run push-product-images-tag.py first."
        )
    return {line.strip() for line in proc.stdout.splitlines() if line.strip()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--brand",
        action="append",
        dest="brands",
        choices=sorted(BRAND_CATALOGS),
        help="Brand to check (repeatable). Default: gc",
    )
    ap.add_argument(
        "--all-brands",
        action="store_true",
        help="Check every brand catalogue",
    )
    ap.add_argument(
        "--remote",
        action="store_true",
        help="Also require images to exist on the product-images tag",
    )
    ap.add_argument(
        "--skip-local",
        action="store_true",
        help="Do not require files on this machine (tag check only)",
    )
    ap.add_argument(
        "--all-images",
        action="store_true",
        help="Check every gallery image, not only the primary",
    )
    ap.add_argument(
        "--ids",
        nargs="*",
        help="Limit to these product ids",
    )
    ap.add_argument(
        "--subcategory-prefix",
        default="",
        help="Only products whose subcategory/tags start with this (e.g. gc-men)",
    )
    args = ap.parse_args()
    if args.skip_local and not args.remote:
        raise SystemExit("--skip-local requires --remote")
    brands = (
        sorted(BRAND_CATALOGS)
        if args.all_brands
        else (args.brands or ["gc"])
    )

    products: list[dict] = []
    for brand in brands:
        products.extend(load_products(brand))
    if args.ids:
        want = set(args.ids)
        products = [p for p in products if p.get("id") in want]
    if args.subcategory_prefix:
        pref = args.subcategory_prefix
        filtered = []
        for p in products:
            sub = str(p.get("subcategory") or "")
            tags = [str(t) for t in (p.get("tags") or [])]
            cols = [str(t) for t in (p.get("gcCollections") or [])]
            blob = " ".join([sub, *tags, *cols])
            if sub.startswith(pref) or any(t.startswith(pref) for t in tags + cols):
                filtered.append(p)
            elif pref in blob:
                filtered.append(p)
        products = filtered

    tag_paths: set[str] | None = None
    if args.remote:
        print(f"Listing files on tag {TAG}…", flush=True)
        tag_paths = list_tag_paths()
        print(f"  {len(tag_paths)} paths on tag", flush=True)

    missing_local: list[tuple[str, str]] = []
    missing_remote: list[tuple[str, str]] = []
    checked = 0

    for p in products:
        pid = str(p.get("id") or "")
        paths = all_product_images(p) if args.all_images else []
        if not paths:
            primary = primary_image(p)
            if primary:
                paths = [primary]
        if not paths:
            continue
        for web in paths:
            checked += 1
            disk = path_on_disk(web)
            if not args.skip_local and not disk.is_file():
                missing_local.append((pid, web))
            if tag_paths is not None:
                blob = tag_blob_path(web)
                if blob not in tag_paths:
                    missing_remote.append((pid, web))

    print(f"Checked {checked} image path(s) across {len(products)} product(s).", flush=True)

    if missing_local:
        print(f"\nMISSING LOCAL ({len(missing_local)}):", flush=True)
        for pid, web in missing_local[:40]:
            print(f"  {pid}  {web}", flush=True)
        if len(missing_local) > 40:
            print(f"  … +{len(missing_local) - 40} more", flush=True)

    if missing_remote:
        print(f"\nMISSING ON TAG {TAG} ({len(missing_remote)}):", flush=True)
        for pid, web in missing_remote[:40]:
            print(f"  {pid}  {web}", flush=True)
        if len(missing_remote) > 40:
            print(f"  … +{len(missing_remote) - 40} more", flush=True)
        print(
            "\nFix: python3 scripts/push-product-images-tag.py --dirs <brand>-pdp",
            flush=True,
        )

    if missing_local or missing_remote:
        return 1
    print("OK — all checked images present.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
