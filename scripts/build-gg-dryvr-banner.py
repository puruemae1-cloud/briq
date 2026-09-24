#!/usr/bin/env python3
"""Build Galvin Green DryVR shop banner video + poster set."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tmp/gg-dryvr-hero.mp4"
BANNERS = ROOT / "public/banners"
OUT_MP4 = BANNERS / "brand-galvin-green.mp4"
POSTER_RAW = ROOT / "tmp/gg-dryvr-poster.jpg"


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.check_call(cmd)


def ffmpeg_bin() -> str:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def main() -> None:
    if not SRC.is_file() or SRC.stat().st_size < 1000:
        raise SystemExit(f"missing source {SRC}")
    BANNERS.mkdir(parents=True, exist_ok=True)
    (BANNERS / "t").mkdir(exist_ok=True)
    (BANNERS / "m").mkdir(exist_ok=True)
    ff = ffmpeg_bin()

    run(
        [
            ff,
            "-y",
            "-i",
            str(SRC),
            "-vf",
            "scale=1280:-2",
            "-c:v",
            "libx264",
            "-profile:v",
            "main",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            "-an",
            "-crf",
            "26",
            "-preset",
            "medium",
            str(OUT_MP4),
        ]
    )
    run(
        [
            ff,
            "-y",
            "-ss",
            "0.5",
            "-i",
            str(SRC),
            "-frames:v",
            "1",
            "-q:v",
            "3",
            str(POSTER_RAW),
        ]
    )

    sys.path.insert(0, str(ROOT / "scripts"))
    from banner_smart_crop import (  # noqa: E402
        FocalPoint,
        SHOP_DESKTOP,
        SHOP_MOBILE,
        SHOP_TABLET,
        cover_crop,
        save_jpeg,
    )
    from PIL import Image  # noqa: E402

    im = Image.open(POSTER_RAW).convert("RGB")
    focal = FocalPoint(0.5, 0.45)
    stems = [
        "brand-galvin-green",
        "brand-galvin-green-1",
        "brand-galvin-green-2",
        "brand-galvin-green-3",
    ]
    configs = [
        ("", SHOP_DESKTOP),
        ("t", SHOP_TABLET),
        ("m", SHOP_MOBILE),
    ]
    for stem in stems:
        for sub, size in configs:
            crop = cover_crop(im, size, focal, vertical_bias="torso")
            dest = BANNERS / sub / f"{stem}.jpg" if sub else BANNERS / f"{stem}.jpg"
            dest.parent.mkdir(parents=True, exist_ok=True)
            save_jpeg(crop, dest, quality=88)
            crop.save(dest.with_suffix(".webp"), format="WEBP", quality=84, method=6)
            print(f"wrote {dest.relative_to(ROOT)} {crop.size} {dest.stat().st_size}", flush=True)

    print(f"mp4 bytes={OUT_MP4.stat().st_size}", flush=True)
    # Probe via ffmpeg (imageio-ffmpeg may not ship ffprobe).
    try:
        subprocess.check_call(
            [ff, "-i", str(OUT_MP4)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError:
        # ffmpeg -i exits non-zero after printing stream info — expected.
        pass


if __name__ == "__main__":
    main()
