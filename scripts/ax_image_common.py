"""Shared Arc'teryx PDP image download helpers (official CDN bytes, no greymat)."""
from __future__ import annotations

import re
import urllib.request
from pathlib import Path

from studio_whiten import save_product_image  # noqa: E402

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:80] or "item"


def fetch_bytes(url: str) -> bytes | None:
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": UA, "Accept": "image/*"}
        )
        with urllib.request.urlopen(req, timeout=45) as r:
            data = r.read()
        return data if data and len(data) >= 800 else None
    except Exception:
        return None


def is_hover_url(url: str) -> bool:
    return bool(re.search(r"[-_]Hover\.", url, re.I))


def save_colour_gallery(
    dest_dir: Path,
    urls: list[str],
    *,
    greymat: bool = False,
    max_frames: int = 8,
) -> tuple[int, int]:
    """Write ``1.jpg``…``N.jpg``, ``hover.jpg``, and ``thumb.jpg`` from official URLs."""
    urls = [u for u in urls if u and "placeholder" not in u.lower()]
    if not urls:
        return 0, 1
    dest_dir.mkdir(parents=True, exist_ok=True)
    ok = fail = 0
    hover_saved = False
    for i, url in enumerate(urls[:max_frames], start=1):
        data = fetch_bytes(url)
        if not data:
            fail += 1
            continue
        path = dest_dir / f"{i}.jpg"
        save_product_image(path, data, greymat=greymat)
        ok += 1
        if is_hover_url(url):
            save_product_image(dest_dir / "hover.jpg", data, greymat=greymat)
            hover_saved = True
    primary = dest_dir / "1.jpg"
    if primary.exists() and primary.stat().st_size > 800:
        save_product_image(dest_dir / "thumb.jpg", primary.read_bytes(), greymat=greymat)
    if not hover_saved:
        for url in urls[:max_frames]:
            if is_hover_url(url):
                data = fetch_bytes(url)
                if data:
                    save_product_image(dest_dir / "hover.jpg", data, greymat=greymat)
                break
    return ok, fail
