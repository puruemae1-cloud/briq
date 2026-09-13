#!/usr/bin/env python3
"""Verify catalogue image paths exist locally (and optionally on product-images tag).

Prevents shop 404s: product rows must not point at missing PDP files.

  python3 scripts/verify-catalog-images.py --brand ce
  python3 scripts/verify-catalog-images.py --brand gg --check-cdn
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAG = "product-images"

BRAND_CATALOGS = {
    "ce": [ROOT / "src/data/ce/ce-catalog.json"],
    "gg": [ROOT / "src/data/gg/gg-catalog.json"],
    "ax": [
        ROOT / "src/data/ax/ax-apparel-catalog.json",
        ROOT / "src/data/ax/ax-catalog.json",
        ROOT / "src/data/ax/ax-gear-catalog.json",
        ROOT / "src/data/ax/ax-outlet-catalog.json",
    ],
    "mb": [ROOT / "src/data/mb/mb-catalog.json"],
}


def load_products(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    if isinstance(data, list):
        return [p for p in data if isinstance(p, dict)]
    if isinstance(data, dict):
        return [p for p in (data.get("products") or []) if isinstance(p, dict)]
    return []


def image_paths(p: dict) -> list[str]:
    out: list[str] = []
    for key in ("image",):
        v = p.get(key)
        if isinstance(v, str) and v.startswith("/products/"):
            out.append(v)
    imgs = p.get("images")
    if isinstance(imgs, list):
        for v in imgs:
            if isinstance(v, str) and v.startswith("/products/"):
                out.append(v)
    for v in p.get("variants") or []:
        if not isinstance(v, dict):
            continue
        iv = v.get("image")
        if isinstance(iv, str) and iv.startswith("/products/"):
            out.append(iv)
        for x in v.get("images") or []:
            if isinstance(x, str) and x.startswith("/products/"):
                out.append(x)
    return list(dict.fromkeys(out))


def folder_of(rel: str) -> tuple[str, str] | None:
    # /products/ce-pdp/<folder>/1.jpg
    parts = rel.strip("/").split("/")
    if len(parts) < 3 or parts[0] != "products":
        return None
    return parts[1], parts[2]


def tag_has_folder(brand: str, folder: str, cache: dict[str, set[str]]) -> bool:
    if brand not in cache:
        r = subprocess.run(
            ["git", "ls-tree", "-d", "--name-only", f"{TAG}:public/products/{brand}"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        cache[brand] = (
            {line.strip() for line in r.stdout.splitlines() if line.strip()}
            if r.returncode == 0
            else set()
        )
    return folder in cache[brand]


def tag_has_file(rel: str, file_cache: dict[str, set[str]]) -> bool:
    """``rel`` like /products/axa-pdp/SKU/colour/1.jpg — check file on tag."""
    parts = rel.strip("/").split("/")
    if len(parts) < 3 or parts[0] != "products":
        return False
    brand = parts[1]
    rest = "/".join(parts[2:])
    if brand not in file_cache:
        r = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", f"{TAG}:public/products/{brand}"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        file_cache[brand] = (
            {line.strip() for line in r.stdout.splitlines() if line.strip()}
            if r.returncode == 0
            else set()
        )
    return rest in file_cache[brand]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand", choices=sorted(BRAND_CATALOGS), required=True)
    ap.add_argument("--check-cdn", action="store_true")
    ap.add_argument("--allow-placeholder", action="store_true", default=True)
    args = ap.parse_args()

    missing_local: list[str] = []
    missing_cdn: list[str] = []
    placeholder = 0
    checked = 0
    cdn_cache: dict[str, set[str]] = {}
    cdn_files: dict[str, set[str]] = {}
    # Nested colourway trees (Arc'teryx) need file-level CDN checks.
    nested_brands = {"axa-pdp", "axg-pdp", "ax-pdp", "axo-pdp"}

    for path in BRAND_CATALOGS[args.brand]:
        if not path.exists():
            continue
        for p in load_products(path):
            for rel in image_paths(p):
                checked += 1
                if "placeholder" in rel:
                    placeholder += 1
                    if args.allow_placeholder:
                        continue
                local = ROOT / "public" / rel.lstrip("/")
                if not local.is_file() or local.stat().st_size < 800:
                    missing_local.append(f"{p.get('id')}: {rel}")
                    continue
                if args.check_cdn:
                    parsed = folder_of(rel)
                    if not parsed:
                        continue
                    brand, folder = parsed
                    if brand in nested_brands:
                        if not tag_has_file(rel, cdn_files):
                            missing_cdn.append(f"{p.get('id')}: {rel}")
                    elif not tag_has_folder(brand, folder, cdn_cache):
                        missing_cdn.append(f"{p.get('id')}: {rel}")

    print(
        f"{args.brand}: checked={checked} placeholder={placeholder} "
        f"missing_local={len(missing_local)} missing_cdn={len(missing_cdn)}"
    )
    for row in missing_local[:15]:
        print("  LOCAL", row)
    for row in missing_cdn[:15]:
        print("  CDN", row)
    if len(missing_local) > 15:
        print(f"  … +{len(missing_local) - 15} more local")
    if len(missing_cdn) > 15:
        print(f"  … +{len(missing_cdn) - 15} more cdn")
    return 1 if missing_local or missing_cdn else 0


if __name__ == "__main__":
    raise SystemExit(main())
