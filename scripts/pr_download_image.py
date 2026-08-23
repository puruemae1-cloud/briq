"""Download Prada PDP images with byte validation."""
from __future__ import annotations

import time
from pathlib import Path

from curl_cffi import requests as cffi_requests

from product_image_bytes import validate_image_bytes, validate_image_file

PR_REFERER = "https://www.prada.com/gb/en/"


def download_image(
    s: cffi_requests.Session,
    url: str,
    dest: Path,
    *,
    min_bytes: int = 2048,
) -> bool:
    if validate_image_file(dest, min_bytes=min_bytes):
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(3):
        try:
            r = s.get(
                url,
                headers={
                    "Accept": "image/jpeg,image/*,*/*",
                    "Referer": PR_REFERER,
                },
                impersonate="chrome124",
                timeout=90,
            )
            if r.status_code != 200 or not validate_image_bytes(
                r.content, min_bytes=min_bytes
            ):
                raise RuntimeError(f"bad image {r.status_code} {len(r.content)}")
            dest.write_bytes(r.content)
            return True
        except Exception:
            if dest.exists():
                dest.unlink(missing_ok=True)
            time.sleep(0.8 * (attempt + 1))
    return False
