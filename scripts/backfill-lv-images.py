#!/usr/bin/env python3
"""Backfill LV furniture images (+ titles) from existing PDP cache without re-browsing.

  python3 scripts/backfill-lv-images.py
  python3 scripts/build-lv-catalog.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lv_common import IMG_ROOT, download_image, normalize_image_list, slugify  # noqa: E402

RAW = ROOT / "src/data/lv/lv-furniture-catalog-raw.json"
CACHE = ROOT / "src/data/lv/lv-furniture-pdp-cache.json"


def main() -> int:
    if not RAW.is_file():
        print(f"missing {RAW}", flush=True)
        return 1
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.is_file() else {}
    products = raw.get("products") or []
    updated = 0
    for p in products:
        url = p.get("url")
        details = cache.get(url) if url else None
        if details:
            if details.get("title") and (
                not p.get("title")
                or str(p.get("title")).startswith("nvprod")
                or p.get("title") == p.get("id")
            ):
                p["title"] = details["title"]
            if details.get("gbpPrice") and not p.get("gbpPrice"):
                p["gbpPrice"] = details["gbpPrice"]
            d = p.setdefault("details", {})
            if details.get("paragraphs") and not d.get("paragraphs"):
                d["paragraphs"] = details["paragraphs"]
            if details.get("bullets") and not d.get("bullets"):
                d["bullets"] = details["bullets"]
            if details.get("specs") and not d.get("specs"):
                d["specs"] = details["specs"]
            if details.get("descriptionHtml") and not d.get("descriptionHtml"):
                d["descriptionHtml"] = details["descriptionHtml"]
            imgs = normalize_image_list(details.get("images") or [])
        else:
            imgs = normalize_image_list(p.get("images") or [])

        folder = IMG_ROOT / slugify(str(p.get("id") or p.get("title") or "item"))
        paths: list[str] = []
        for i, img_url in enumerate(imgs, start=1):
            dest = folder / f"{i}.jpg"
            if download_image(img_url, dest):
                rel = "/" + dest.relative_to(ROOT / "public").as_posix()
                paths.append(rel)
            if len(paths) >= 16:
                break
        p["images"] = paths
        updated += 1
        print(f"{p.get('id')}: {len(paths)} imgs — {p.get('title')}", flush=True)

    RAW.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Updated {updated} products in {RAW.relative_to(ROOT)}", flush=True)
    missing = sum(1 for p in products if not p.get("images"))
    if missing:
        print(f"WARN: {missing} products still have 0 images", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
