#!/usr/bin/env python3
"""Whiten light studio mats on catalog PDP photos (all brands).

Gucci assets are already re-fetched as White_Center. Other brands ship with
warm/gray studio backgrounds baked into JPGs. This pass detects near-uniform
light corner mats and lifts them to pure white so PLP tiles match the page.

Skips lifestyle / dark / multi-tone frames so model shots stay intact.
"""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = ROOT / "public" / "products"

DEFAULT_DIRS = [
    "bb-pdp",
    "ps-pdp",
    "bs-pdp",
    "ax-pdp",
    "axa-pdp",
    "axg-pdp",
    "axo-pdp",
    "gg-pdp",
    "lu-pdp",
    "cw-pdp",
    "gc-pdp",
]


def _luma(rgb: tuple[float, float, float]) -> float:
    r, g, b = rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def corner_samples(arr: np.ndarray) -> list[np.ndarray]:
    h, w = arr.shape[:2]
    s = max(4, min(h, w) // 40)
    patches = [
        arr[0:s, 0:s],
        arr[0:s, w - s : w],
        arr[h - s : h, 0:s],
        arr[h - s : h, w - s : w],
    ]
    return [p.reshape(-1, 3).mean(axis=0) for p in patches]


def studio_bg_color(arr: np.ndarray) -> np.ndarray | None:
    """Return estimated studio mat RGB, or None if not a light packshot mat."""
    corners = corner_samples(arr)
    luminances = [_luma(tuple(c)) for c in corners]
    # Need a light mat on most corners (warm Arc'teryx mats ~180–210 luma)
    light_idx = [i for i, L in enumerate(luminances) if L >= 168]
    if len(light_idx) < 2:
        return None
    # Prefer 3+ light corners; allow 2 when they agree (product often clips
    # the bottom edge of the frame on packshots).
    light_corners = [corners[i] for i in light_idx]
    bg = np.median(np.stack(light_corners, axis=0), axis=0)
    if len(light_idx) < 3:
        if np.linalg.norm(light_corners[0] - light_corners[1]) > 40:
            return None
        if _luma(tuple(bg)) < 185:
            return None
    for c in light_corners:
        if np.linalg.norm(c - bg) > 65:
            return None
    if _luma(tuple(bg)) < 172:
        return None
    return bg


def whiten_array(arr: np.ndarray, bg: np.ndarray) -> np.ndarray:
    """Softly map pixels near the studio mat toward pure white."""
    f = arr.astype(np.float32)
    dist = np.linalg.norm(f - bg.reshape(1, 1, 3), axis=2)
    # Soft threshold: fully replace close pixels, fade out toward product edges
    hard = 32.0
    soft = 72.0
    alpha = 1.0 - (dist - hard) / (soft - hard)
    alpha = np.clip(alpha, 0.0, 1.0)
    # Don't touch darker product pixels even if chroma is close
    lum = 0.2126 * f[:, :, 0] + 0.7152 * f[:, :, 1] + 0.0722 * f[:, :, 2]
    alpha = np.where(lum < 158, 0.0, alpha)
    a = alpha[..., None]
    out = f * (1.0 - a) + 255.0 * a
    return np.clip(out, 0, 255).astype(np.uint8)


def process_one(path_str: str) -> tuple[str, str]:
    path = Path(path_str)
    try:
        with Image.open(path) as im:
            rgb = im.convert("RGB")
            # Fast path: already pure-white studio corners
            w, h = rgb.size
            probes = [
                rgb.getpixel((2, 2)),
                rgb.getpixel((w - 3, 2)),
                rgb.getpixel((2, h - 3)),
                rgb.getpixel((w - 3, h - 3)),
            ]
            if sum(1 for p in probes if min(p) >= 250) >= 3:
                return path_str, "skip"
            arr = np.asarray(rgb)
            bg = studio_bg_color(arr)
            if bg is None:
                return path_str, "skip"
            out = whiten_array(arr, bg)
            # Skip write if almost unchanged
            if np.mean(np.abs(out.astype(np.int16) - arr.astype(np.int16))) < 0.8:
                return path_str, "skip"
            Image.fromarray(out, mode="RGB").save(
                path, format="JPEG", quality=92, optimize=True
            )
        return path_str, "ok"
    except Exception as e:
        return path_str, f"fail:{e}"


def collect_images(dirs: list[str]) -> list[Path]:
    files: list[Path] = []
    for name in dirs:
        root = PRODUCTS / name
        if not root.exists():
            continue
        files.extend(root.rglob("*.jpg"))
        files.extend(root.rglob("*.jpeg"))
        files.extend(root.rglob("*.webp"))
    return sorted({p.resolve() for p in files if p.is_file()})


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--dirs",
        nargs="*",
        default=DEFAULT_DIRS,
        help="Product image roots under public/products/",
    )
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    files = collect_images(args.dirs)
    if args.limit:
        files = files[: args.limit]
    print(f"candidates={len(files)} dirs={args.dirs}", flush=True)
    if not files:
        return

    ok = skip = fail = 0
    with ProcessPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futs = [ex.submit(process_one, str(p)) for p in files]
        done = 0
        for fut in as_completed(futs):
            _, status = fut.result()
            done += 1
            if status == "ok":
                ok += 1
            elif status == "skip":
                skip += 1
            else:
                fail += 1
                if fail <= 12:
                    print(status, flush=True)
            if done % 500 == 0 or done == len(files):
                print(
                    f"{done}/{len(files)} ok={ok} skip={skip} fail={fail}",
                    flush=True,
                )
    print(f"done ok={ok} skip={skip} fail={fail}", flush=True)


if __name__ == "__main__":
    main()
    sys.exit(0)
