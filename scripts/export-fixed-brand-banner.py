#!/usr/bin/env python3
"""Export a locked brand/shop banner with soft blurred B&W side (or top/bottom) margins."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
BANNERS = ROOT / "public" / "banners"

DESKTOP = (2560, 1280)
TABLET = (1920, 960)
MOBILE = (1280, 640)


def _grayscale_rgb(im: Image.Image) -> Image.Image:
    g = im.convert("L")
    return Image.merge("RGB", (g, g, g))


def _cover_size(src: tuple[int, int], dst: tuple[int, int]) -> tuple[int, int]:
    sw, sh = src
    dw, dh = dst
    scale = max(dw / sw, dh / sh)
    return max(1, round(sw * scale)), max(1, round(sh * scale))


def _soft_edge_blend(
    bg: Image.Image, fg: Image.Image, x: int, y: int, feather: int
) -> Image.Image:
    out = bg.copy()
    fw, fh = fg.size
    mask = Image.new("L", (fw, fh), 255)
    px = mask.load()
    f = min(feather, fw // 2, fh // 2)
    for i in range(f):
        a = int(255 * (i / f))
        for yy in range(fh):
            px[i, yy] = a
            px[fw - 1 - i, yy] = a
        for xx in range(fw):
            px[xx, i] = min(px[xx, i], a)
            px[xx, fh - 1 - i] = min(px[xx, fh - 1 - i], a)
    out.paste(fg, (x, y), mask)
    return out


def make_panorama(src: Image.Image, out_w: int, out_h: int) -> Image.Image:
    """Color subject centered; margins = blurred B&W cover of the same photo."""
    bg = _grayscale_rgb(src)
    bg = bg.resize(_cover_size(bg.size, (out_w, out_h)), Image.Resampling.LANCZOS)
    bw, bh = bg.size
    left = (bw - out_w) // 2
    top = (bh - out_h) // 2
    bg = bg.crop((left, top, left + out_w, top + out_h))
    bg = bg.filter(ImageFilter.GaussianBlur(radius=max(28, out_w // 55)))
    bg = ImageEnhance.Brightness(bg).enhance(0.72)
    bg = ImageEnhance.Contrast(bg).enhance(1.05)

    sw, sh = src.size
    scale = min(out_w / sw, out_h / sh)
    fw = max(1, round(sw * scale))
    fh = max(1, round(sh * scale))
    if fw > out_w:
        scale = out_w / sw
        fw = out_w
        fh = max(1, round(sh * scale))
    if fh > out_h:
        scale = out_h / sh
        fh = out_h
        fw = max(1, round(sw * scale))
    fg = src.resize((fw, fh), Image.Resampling.LANCZOS)

    x = (out_w - fw) // 2
    y = (out_h - fh) // 2
    feather = max(12, min(fw, fh) // 28)
    return _soft_edge_blend(bg, fg, x, y, feather)


def export_set(src: Path, stem: str, *, quality: int = 97) -> None:
    im = Image.open(src).convert("RGB")
    for size, subdir in ((DESKTOP, ""), (TABLET, "t"), (MOBILE, "m")):
        out = make_panorama(im, size[0], size[1])
        dest = BANNERS / subdir / f"{stem}.jpg" if subdir else BANNERS / f"{stem}.jpg"
        dest.parent.mkdir(parents=True, exist_ok=True)
        out.save(
            dest,
            format="JPEG",
            quality=quality,
            optimize=True,
            progressive=True,
            subsampling=0,
        )
        webp = dest.with_suffix(".webp")
        out.save(webp, format="WEBP", quality=92, method=6)
        print(f"wrote {dest.relative_to(ROOT)} {out.size} jpg={dest.stat().st_size} webp={webp.stat().st_size}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("stem", help="banner filename without .jpg, e.g. brand-chanel-premiere")
    ap.add_argument("--quality", type=int, default=97)
    args = ap.parse_args()
    export_set(args.source, args.stem, quality=args.quality)


if __name__ == "__main__":
    main()
