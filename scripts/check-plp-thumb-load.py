#!/usr/bin/env python3
"""Guard: PLP card thumbs must not ship the iOS Safari blank-image trap.

Fails if ProductCardMedia current slides are hard-coded to loading=\"lazy\"
without an eager escape, or if CSS forces opacity:0 !important on
.product-card-media__img.is-loading without carving out .is-current ready paint.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "src/components/ProductCardMedia.tsx"
CSS = ROOT / "src/app/globals.css"


def main() -> int:
    errors: list[str] = []
    media = MEDIA.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")

    if "loading=\"lazy\"" in media and "eager" not in media:
        errors.append(
            "ProductCardMedia.tsx: all imgs are loading=lazy — current slides need eager"
        )

    if "loading={eager || current ? \"eager\" : \"lazy\"}" not in media and \
       'loading={eager || current ? "eager" : "lazy"}' not in media:
        # allow equivalent forms
        if not re.search(r'loading=\{[^}]*eager[^}]*\}', media):
            errors.append(
                "ProductCardMedia.tsx: missing eager loading for current/in-view slides"
            )

    if "IntersectionObserver" not in media:
        errors.append(
            "ProductCardMedia.tsx: missing IntersectionObserver to preload gallery thumbs"
        )

    # Dangerous: is-loading { opacity: 0 !important } that also matches is-current
    # without a later override for ready current frames is OK as long as eager exists;
    # still flag if is-current is-loading uses !important forever with only lazy.
    bad = re.search(
        r"\.product-card-media__img\.is-loading\s*\{[^}]*opacity:\s*0\s*!important",
        css,
    )
    if bad and "loading={eager || current" not in media and \
       not re.search(r'loading=\{[^}]*eager', media):
        errors.append(
            "globals.css + ProductCardMedia: opacity:0 !important on is-loading with lazy-only"
        )

    if "content-visibility: auto" in css and "collection-100 .product-grid" in css:
        # narrow check: collection-100 product grid must not use content-visibility:auto
        block = re.search(
            r"\.collection-100\s+\.product-grid\s*>\s*\*\s*\{([^}]+)\}",
            css,
        )
        if block and "content-visibility: auto" in block.group(1):
            errors.append(
                "globals.css: .collection-100 .product-grid uses content-visibility:auto "
                "(delays mobile thumb decode)"
            )

    if errors:
        print("PLP thumb load guard FAILED:")
        for e in errors:
            print(" -", e)
        return 1

    print("PLP thumb load guard OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
