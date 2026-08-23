"""Shared validation for catalog PDP image files."""
from __future__ import annotations

import io
from pathlib import Path

MIN_BYTES = 2048
MIN_DIM = 100


def validate_image_bytes(data: bytes, *, min_bytes: int = MIN_BYTES) -> bool:
    if len(data) < min_bytes:
        return False
    try:
        from PIL import Image

        im = Image.open(io.BytesIO(data))
        im.verify()
        im = Image.open(io.BytesIO(data))
        w, h = im.size
        return w >= MIN_DIM and h >= MIN_DIM
    except Exception:
        return False


def validate_image_file(path: Path, *, min_bytes: int = MIN_BYTES) -> bool:
    if not path.is_file():
        return False
    try:
        data = path.read_bytes()
    except OSError:
        return False
    return validate_image_bytes(data, min_bytes=min_bytes)
