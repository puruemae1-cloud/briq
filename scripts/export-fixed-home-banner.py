#!/usr/bin/env python3
"""Export locked homepage hero / event banners at max practical quality.

- Lanczos upscale + light unsharp mask (1024px sources → desktop width)
- JPEG q98 4:4:4 + WebP q92 for faster delivery at equal-or-better visuals
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
BANNERS = ROOT / "public" / "banners"

DESKTOP_W = 2560
TABLET_W = 1920
MOBILE_W = 1280

JPEG_QUALITY = 98
WEBP_QUALITY = 92


def _sharpen(im: Image.Image) -> Image.Image:
    w, h = im.size
    radius = max(0.8, min(w, h) / 1800)
    return im.filter(ImageFilter.UnsharpMask(radius=radius, percent=110, threshold=2))


def _scale_width(im: Image.Image, width: int) -> Image.Image:
    h = max(1, round(im.height * width / im.width))
    out = im.resize((width, h), Image.Resampling.LANCZOS)
    return _sharpen(out)


def _crop_now_london(scaled: Image.Image, *, ref_full_h: int = 1705, ref_peak: int = 327, ref_gap: int = 14) -> Image.Image:
    """Top crop so bag-handle breathing room matches the locked 40% strap edit."""
    sh = scaled.height
    peak_y = round(ref_peak * sh / ref_full_h)
    gap = max(1, round(ref_gap * scaled.width / DESKTOP_W))
    top = max(0, peak_y - gap)
    return scaled.crop((0, top, scaled.width, sh))


def _save_pair(im: Image.Image, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(
        dest,
        format="JPEG",
        quality=JPEG_QUALITY,
        optimize=True,
        progressive=True,
        subsampling=0,
    )
    webp = dest.with_suffix(".webp")
    im.save(webp, format="WEBP", quality=WEBP_QUALITY, method=6)
    print(
        f"wrote {dest.relative_to(ROOT)} {im.size} jpg={dest.stat().st_size} webp={webp.stat().st_size}"
    )


def export_hero(src: Path, stem: str, *, crop_now_london: bool = False) -> None:
    im = Image.open(src).convert("RGB")
    print(f"source {src.name} {im.size}")

    for width, subdir in ((DESKTOP_W, ""), (TABLET_W, "t"), (MOBILE_W, "m")):
        scaled = _scale_width(im, width)
        out = _crop_now_london(scaled) if crop_now_london else scaled
        base = BANNERS / subdir / stem if subdir else BANNERS / stem
        _save_pair(out, base.with_suffix(".jpg"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("stem", help="filename without extension, e.g. hero-london-door")
    ap.add_argument(
        "--now-london-crop",
        action="store_true",
        help="apply locked Now in London top crop",
    )
    args = ap.parse_args()
    export_hero(args.source, args.stem, crop_now_london=args.now_london_crop)


if __name__ == "__main__":
    main()
