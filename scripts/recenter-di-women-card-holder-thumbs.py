#!/usr/bin/env python3
"""Re-center low-position Dior women studio thumbnails from Dior originals.

Targets Dior women's product leaves that commonly render with the subject too
low inside Briq's 4:5 product cards. The script rebuilds only the primary
thumbnail from the original Dior remote image so the native Dior background is
preserved while the subject is recentered.
"""
from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image, ImageOps

from banner_smart_crop import subject_bbox

ROOT = Path(__file__).resolve().parents[1]
RAW_FILES = [
    ROOT / "src/data/di/di-women-slg-catalog-raw.json",
    ROOT / "src/data/di/di-women-accessories-catalog-raw.json",
]
OUT_W = 1334
OUT_H = 2000
THRESHOLD = 80.0
LOW_CENTER_Y = 0.60
MIN_BOX = 40
MIN_TARGET_FILL = 0.336
UPWARD_BIAS = 0.18
TARGET_LEAVES = {
    "di-women-card-holders",
    "di-women-wallets",
    "di-women-pouches",
    "di-women-slg-tech",
    "di-women-belts",
    "di-women-slg-all",
}


def iter_items() -> list[tuple[str, Path, str]]:
    items: list[tuple[str, Path, str]] = []
    seen: set[tuple[str, str]] = set()
    for raw_path in RAW_FILES:
        if not raw_path.is_file():
            continue
        payload = json.loads(raw_path.read_text())
        for row in payload.get("products") or []:
            leaf = str(row.get("leafId") or "")
            if leaf not in TARGET_LEAVES:
                continue
            remote = (row.get("remoteImages") or [None])[0]
            images = row.get("images") or []
            first_image = str(images[0]) if images else ""
            if not remote or "/products/di-pdp/" not in first_image:
                continue
            rel = first_image.split("/products/di-pdp/", 1)[1]
            folder = rel.split("/", 1)[0]
            key = (leaf, folder)
            if key in seen:
                continue
            seen.add(key)
            dest = ROOT / "public/products/di-pdp" / folder / "1.jpg"
            dest.parent.mkdir(parents=True, exist_ok=True)
            items.append((leaf, dest, remote))
    items.sort(key=lambda item: (item[0], str(item[1])))
    return items


def fetch_remote_image(url: str) -> Image.Image:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=60) as resp:
        return ImageOps.exif_transpose(Image.open(BytesIO(resp.read())).convert("RGB"))


def recenter_one(path: Path, remote_url: str) -> bool:
    src = fetch_remote_image(remote_url)
    box = subject_bbox(src, threshold=THRESHOLD)
    if box is None:
        return False
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    if bw < MIN_BOX or bh < MIN_BOX:
        return False

    center_y = (y0 + y1) / 2 / src.height
    if center_y <= LOW_CENTER_Y:
        return False

    current_fill = bh / src.height
    target_fill = max(current_fill, MIN_TARGET_FILL)
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2 - bh * UPWARD_BIAS
    crop_h = min(src.height, int(round(bh / target_fill)))
    crop_w = int(round(crop_h * OUT_W / OUT_H))
    if crop_w > src.width:
        crop_w = src.width
        crop_h = int(round(crop_w * OUT_H / OUT_W))

    left = int(round(cx - crop_w / 2))
    top = int(round(cy - crop_h / 2))
    left = max(0, min(src.width - crop_w, left))
    top = max(0, min(src.height - crop_h, top))

    crop = src.crop((left, top, left + crop_w, top + crop_h))
    crop.resize((OUT_W, OUT_H), Image.Resampling.LANCZOS).save(path, quality=92, optimize=True)
    return True


def main() -> None:
    items = iter_items()
    changed = 0
    for leaf, path, remote_url in items:
        try:
            if recenter_one(path, remote_url):
                changed += 1
                print(f"OK {leaf} {path.parent.name}", flush=True)
        except Exception as e:
            print(f"WARN {leaf} {path}: {e}", flush=True)
    print(f"items={len(items)} changed={changed}", flush=True)


if __name__ == "__main__":
    main()
