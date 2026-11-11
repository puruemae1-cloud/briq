#!/usr/bin/env python3
"""Shared helpers: keep catalogue image paths that exist on disk or the CDN tag.

PDP jpgs live on the `product-images` git tag (gitignored locally) and are
served via jsDelivr / GitHub raw rewrites. Catalogue builders must not strip
galleries just because `public/products/*-pdp` is absent on the build machine —
that wiped nearly all Celine images during the 2026-11-06 weekly sync.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIN_BYTES = 800
TAG = "product-images"

_tag_paths: set[str] | None = None
_tag_listed = False


def disk_path(web: str) -> Path:
    return ROOT / "public" / web.lstrip("/")


def product_images_on_tag(*, fetch: bool = False) -> set[str]:
    """Web paths (`/products/...`) present on the `product-images` tag.

    Returns an empty set when the tag cannot be listed so callers can fall back
    to disk-only checks without crashing offline builds.
    """
    global _tag_paths, _tag_listed
    if _tag_listed and _tag_paths is not None and not fetch:
        return _tag_paths
    if fetch:
        subprocess.run(
            ["git", "fetch", "--no-tags", "origin", f"+refs/tags/{TAG}:refs/tags/{TAG}"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    r = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", TAG, "public/products/"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    _tag_listed = True
    if r.returncode != 0:
        _tag_paths = set()
        return _tag_paths
    out: set[str] = set()
    for line in r.stdout.splitlines():
        name = line.strip()
        if not name.startswith("public/"):
            continue
        out.add(name[len("public") :])  # /products/...
    _tag_paths = out
    return _tag_paths


def clear_tag_cache() -> None:
    global _tag_paths, _tag_listed
    _tag_paths = None
    _tag_listed = False


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


def image_on_tag(web: str | None) -> bool:
    if not web or not isinstance(web, str):
        return False
    if not web.startswith("/products/"):
        return False
    base = web.split("?", 1)[0]
    return base in product_images_on_tag()


def image_available(web: str | None) -> bool:
    """True when the path can be served (local disk or product-images CDN tag)."""
    if not web or not isinstance(web, str):
        return False
    if "placeholder" in web:
        return False
    if web.startswith("http://") or web.startswith("https://"):
        return True
    if not web.startswith("/products/"):
        return True
    return image_on_disk(web) or image_on_tag(web)


def existing_images(paths: list | None) -> list[str]:
    out: list[str] = []
    for raw in paths or []:
        if isinstance(raw, str) and raw and image_available(raw):
            out.append(raw.split("?", 1)[0] if raw.startswith("/products/") else raw)
    return out


def _sort_key(path: str) -> tuple[int, str]:
    stem = Path(path).stem
    digits = re.sub(r"\D", "", stem) or "0"
    try:
        return (int(digits), path)
    except ValueError:
        return (0, path)


def gallery_on_tag(brand_dir: str, folder: str) -> list[str]:
    """Numbered PDP frames for ``/products/{brand_dir}/{folder}/`` on the CDN tag."""
    if not brand_dir or not folder:
        return []
    prefix = f"/products/{brand_dir.strip('/')}/{folder.strip('/')}/"
    files = [
        p
        for p in product_images_on_tag()
        if p.startswith(prefix) and Path(p).suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    ]
    return sorted(files, key=_sort_key)
