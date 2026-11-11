#!/usr/bin/env python3
"""Restore Celine catalogue galleries wiped by disk-only image guards.

When `public/products/ce-pdp` is absent (gitignored), weekly `build-ce-catalog.py`
used to blank every gallery to placeholder even though frames exist on the
`product-images` tag. Re-attach tag/raw galleries onto ce-catalog.json (and
refresh bags/shoes slices).

  python3 scripts/restore-ce-images-from-cdn.py
  python3 scripts/restore-ce-images-from-cdn.py --fetch-tag
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from catalog_image_guard import (  # noqa: E402
    existing_images,
    gallery_on_tag,
    product_images_on_tag,
)
from celine_common import slugify  # noqa: E402
from celine_config import celine_raw_paths  # noqa: E402

OUT = ROOT / "src/data/ce/ce-catalog.json"
PLACEHOLDER = "/products/ce-pdp/placeholder.jpg"


def load_raw_images() -> dict[str, list[str]]:
    by_sku: dict[str, list[str]] = {}
    for path in celine_raw_paths():
        payload = json.loads(path.read_text())
        rows = payload.get("products") if isinstance(payload, dict) else payload
        for row in rows or []:
            if not isinstance(row, dict):
                continue
            sku = str(row.get("sku") or row.get("id") or "").strip()
            if not sku:
                continue
            imgs = [x for x in (row.get("images") or []) if isinstance(x, str) and x]
            if imgs:
                by_sku[sku.upper()] = imgs
                by_sku[slugify(sku.replace(".", "-"))] = imgs
    return by_sku


def needs_restore(product: dict) -> bool:
    image = str(product.get("image") or "")
    images = [x for x in (product.get("images") or []) if isinstance(x, str) and x]
    if not images or "placeholder" in image:
        return True
    return not existing_images(images)


def apply_gallery(product: dict, images: list[str]) -> None:
    product["image"] = images[0]
    product["images"] = images
    for section in product.get("storySections") or []:
        if not isinstance(section, dict):
            continue
        # Leave non-empty remote/editorial frames alone; fill blanks only.
        if not section.get("image"):
            idx = min(len(images) - 1, 1)
            section["image"] = images[idx if section.get("reverse") else 0]
    for variant in product.get("variants") or []:
        if not isinstance(variant, dict):
            continue
        variant["image"] = images[0]
        variant["images"] = images


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch-tag", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    tag = product_images_on_tag(fetch=args.fetch_tag)
    if not tag:
        print("ERROR: could not list product-images tag", file=sys.stderr)
        return 2

    raw_imgs = load_raw_images()
    products = json.loads(OUT.read_text())
    if not isinstance(products, list):
        raise SystemExit("ce-catalog.json must be a list")

    restored = 0
    still_missing = 0
    for product in products:
        if not needs_restore(product):
            continue
        sku = str(product.get("sku") or "").strip()
        pid = str(product.get("id") or "")
        folder = pid[3:] if pid.startswith("ce-") else slugify(sku.replace(".", "-"))
        candidates = (
            existing_images(raw_imgs.get(sku.upper()) or [])
            or existing_images(raw_imgs.get(folder) or [])
            or gallery_on_tag("ce-pdp", folder)
        )
        if not candidates:
            still_missing += 1
            continue
        apply_gallery(product, candidates)
        restored += 1

    placeholder = sum(
        1
        for p in products
        if "placeholder" in str(p.get("image") or "") or not (p.get("images") or [])
    )
    print(
        f"restored={restored} still_missing={still_missing} "
        f"placeholder_left={placeholder}/{len(products)} tag_files={len(tag)}"
    )
    if args.dry_run:
        return 0 if restored or placeholder < max(20, len(products) * 0.05) else 1

    OUT.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n")
    print(f"wrote {OUT}")
    return 0 if placeholder < max(20, len(products) * 0.05) else 1


if __name__ == "__main__":
    raise SystemExit(main())
