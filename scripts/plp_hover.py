#!/usr/bin/env python3
"""Official PLP hover-image helpers shared by brand scrape/build scripts.

Briq cards swap to `hoverImage` on desktop hover. That must match the brand's
own PLP tile swap — not blindly `images[1]` from a PDP gallery (PDP frame 2 is
often a side/detail packshot).
"""
from __future__ import annotations

import re
from typing import Sequence


def gucci_shot_meta(url: str) -> tuple[str | None, str | None]:
    """Return (view_code, type_code) from a Gucci media filename.

    Example: ``602204_1DB0G_1000_003_100_0000_Light-….jpg`` → ``("003", "100")``.
    Type ``100`` is the on-model / lookbook crop used as the PLP hover on gucci.com.
    """
    fn = (url or "").split("/")[-1]
    m = re.search(r"_(\d{3})_(\d{3})_", fn)
    if not m:
        return None, None
    return m.group(1), m.group(2)


def gucci_lifestyle_index(remote_images: Sequence[str]) -> int | None:
    """Index of the first on-model shot in a Gucci remote gallery."""
    for i, url in enumerate(remote_images or []):
        view, typ = gucci_shot_meta(url)
        if typ == "100" and view != "001":
            return i
    return None


def pick_hover_local(
    local_images: Sequence[str],
    *,
    remote_images: Sequence[str] | None = None,
    explicit: str | None = None,
) -> str | None:
    """Resolve a local hover path.

    Preference order:
    1. ``explicit`` local path (already downloaded PLP hover asset)
    2. Gucci lifestyle frame (type ``100``) mapped by gallery index
    3. ``local_images[1]`` (common Shopify / PLP second frame)
    4. ``local_images[0]``
    """
    locals_ = [x for x in (local_images or []) if x]
    if explicit and explicit.strip():
        return explicit.strip()
    if remote_images and locals_:
        idx = gucci_lifestyle_index(remote_images)
        if idx is not None and idx < len(locals_):
            return locals_[idx]
    if len(locals_) > 1:
        return locals_[1]
    return locals_[0] if locals_ else None


def first_alternate_gallery_src(item: dict) -> str | None:
    """PLP ``alternateGalleryImages[0]`` — usually the Gucci tile hover look."""
    for img in item.get("alternateGalleryImages") or []:
        if not isinstance(img, dict):
            continue
        src = (
            img.get("datasrcstandardretina")
            or img.get("datasrcstandard")
            or img.get("src")
            or img.get("datasrc")
        )
        if src:
            return src
    alt = item.get("alternateImage") or {}
    if isinstance(alt, dict):
        return (
            alt.get("datasrcstandardretina")
            or alt.get("datasrcstandard")
            or alt.get("src")
            or alt.get("datasrc")
        )
    return None
