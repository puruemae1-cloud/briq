#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_GLOB = "src/data/di/*-catalog-raw.json"
MIN_BYTES = 800


def iter_image_paths(product: dict) -> list[str]:
    out: list[str] = []
    for key in ("image", "hoverImage"):
        value = product.get(key)
        if isinstance(value, str) and value.startswith("/products/di-pdp/"):
            out.append(value)
    for key in ("images",):
        for value in product.get(key) or []:
            if isinstance(value, str) and value.startswith("/products/di-pdp/"):
                out.append(value)
    for variant in product.get("variants") or []:
        if not isinstance(variant, dict):
            continue
        out.extend(iter_image_paths(variant))
    return out


def local_path(src: str) -> Path:
    return ROOT / "public" / src.lstrip("/")


def folder_from_src(src: str) -> str:
    return src.split("/products/di-pdp/", 1)[1].split("/", 1)[0]


def main() -> int:
    raw_files = sorted(ROOT.glob(RAW_GLOB))
    if not raw_files:
      print("no di raw files found")
      return 1

    checked = 0
    missing: list[str] = []
    tiny: list[str] = []
    underscore: list[str] = []

    for raw_file in raw_files:
        payload = json.loads(raw_file.read_text())
        products = payload.get("products")
        if not isinstance(products, list):
            continue
        for product in products:
            if not isinstance(product, dict):
                continue
            for src in iter_image_paths(product):
                checked += 1
                folder = folder_from_src(src)
                if "_" in folder:
                    underscore.append(src)
                path = local_path(src)
                if not path.exists():
                    missing.append(src)
                    continue
                if path.stat().st_size < MIN_BYTES:
                    tiny.append(f"{src} ({path.stat().st_size} bytes)")

    print(
        "checked_images",
        checked,
        "missing",
        len(missing),
        "tiny",
        len(tiny),
        "underscore",
        len(underscore),
    )
    for label, items in (
        ("missing", missing),
        ("tiny", tiny),
        ("underscore", underscore),
    ):
        for item in items[:50]:
            print(label, item)
        if len(items) > 50:
            print(label, f"... {len(items) - 50} more")

    return 0 if not (missing or tiny or underscore) else 1


if __name__ == "__main__":
    raise SystemExit(main())
