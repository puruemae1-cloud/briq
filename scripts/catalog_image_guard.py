#!/usr/bin/env python3
"""Shared helpers: only keep catalogue image paths that exist on disk."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIN_BYTES = 800


def disk_path(web: str) -> Path:
    return ROOT / "public" / web.lstrip("/")


def image_on_disk(web: str | None) -> bool:
    """True when a /products/… path exists and is a real image file.

    Non-product paths (placeholders under /products/*.svg, remote URLs) pass.
    """
    if not web or not isinstance(web, str):
        return False
    if web.startswith("http://") or web.startswith("https://"):
        return True
    if not web.startswith("/products/"):
        return True
    # /products/foo.svg placeholders live in git; numbered PDP jpgs do not.
    p = disk_path(web)
    try:
        return p.is_file() and p.stat().st_size >= MIN_BYTES
    except OSError:
        return False


def existing_images(paths: list | None) -> list[str]:
    out: list[str] = []
    for raw in paths or []:
        if isinstance(raw, str) and raw and image_on_disk(raw):
            out.append(raw)
    return out
