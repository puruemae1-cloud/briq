"""Rembg-only greymat for Galvin Green pale colourways.

Soft remap (``ok:fast``) washes white/sand garments grey. Pale GG SKUs must
either keep Shopify CDN bytes or be rembg-composited onto #e7e7e7 — never soft
remap. See gg_pale_colour.py / redownload-gg-pale.py.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from studio_greymat import (  # noqa: E402
    already_darkgray,
    rembg_greymat,
    studio_bg_color,
)


def rembg_only_greymat(path: Path | str) -> str:
    """Composite onto DarkGray via rembg, or leave CDN bytes untouched."""
    path = Path(path)
    try:
        with Image.open(path) as im:
            rgb = im.convert("RGB")
            arr = np.asarray(rgb)
            bg = studio_bg_color(arr)
            if bg is None:
                return "skip"
            if already_darkgray(bg):
                return "skip"
            out_im, ok = rembg_greymat(path)
            if not ok:
                return "skip"
            out = np.asarray(out_im)
            if np.mean(np.abs(out.astype(np.int16) - arr.astype(np.int16))) < 0.6:
                return "skip"
            Image.fromarray(out, mode="RGB").save(
                path, format="JPEG", quality=92, optimize=True
            )
        return "ok:rembg"
    except Exception as e:
        return f"fail:{e}"
