"""Detect Galvin Green products that must skip greymat/rembg.

White / sand / ivory packshots blend into light studio mats; soft remap and
rembg wash the garment grey (Noah white pants, etc.). Keep official Shopify
CDN bytes — same policy as bs_pale_colour / ps_pale_colour / ax_pale_colour.

Only primary pale colourways are matched (``White``, ``White Cool Grey``,
``Sand``, handle ``…-white``). Multi-colour names where white is not primary
(e.g. ``Black White Orange``) still go through greymat.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "src/data/gg/gg-catalog-raw.json"

# Primary colour token at the start of colorName / end of handle.
PRIMARY_PALE_RE = re.compile(
    r"^(?:"
    r"white|off[\s-]?white|optic[\s-]?white|"
    r"ivory|cream|ecru|chalk|bone|pearl|porcelain|snow|alabaster|"
    r"sand(?:[\s-]?melange)?|beige|putty|linen|oyster|champagne"
    r")(?:$|[\s/-])",
    re.I,
)

HANDLE_PALE_SUFFIX_RE = re.compile(
    r"-(?:"
    r"white|off-white|optic-white|"
    r"ivory|cream|ecru|chalk|bone|pearl|snow|"
    r"sand(?:-melange)?|beige|putty|linen"
    r")$",
    re.I,
)


def _label(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return str(
            value.get("label")
            or value.get("name")
            or value.get("id")
            or ""
        ).strip()
    return str(value).strip()


def is_pale_gg_colour(
    *,
    handle: str | None = None,
    color_name: str | None = None,
    title: str | None = None,
) -> bool:
    """True when this GG SKU should keep official CDN bytes (no greymat)."""
    cn = _label(color_name).replace("_", " ").strip()
    if cn:
        # Prefer official colorName — avoids matching Black White / Navy White
        # handles that merely end in ``-white``.
        return bool(PRIMARY_PALE_RE.search(cn))
    h = _label(handle).replace("_", "-").strip().lower()
    if h and HANDLE_PALE_SUFFIX_RE.search(h):
        return True
    t = _label(title).replace("_", " ").strip()
    if t and PRIMARY_PALE_RE.search(t.split(" - ")[-1].strip()):
        return True
    return False


def is_pale_gg_row(row: dict | None) -> bool:
    if not row:
        return False
    return is_pale_gg_colour(
        handle=str(row.get("handle") or ""),
        color_name=str(row.get("colorName") or row.get("color") or ""),
        title=str(row.get("title") or ""),
    )


def pale_gg_handles(raw: dict | list | None = None) -> set[str]:
    """All gg-pdp folder names that must skip greymat."""
    data = raw
    if data is None:
        if not RAW_PATH.is_file():
            return set()
        data = json.loads(RAW_PATH.read_text())
    products: list[dict] = []
    if isinstance(data, dict):
        prods = data.get("products")
        if isinstance(prods, list):
            products = [p for p in prods if isinstance(p, dict)]
        elif isinstance(prods, dict):
            products = [p for p in prods.values() if isinstance(p, dict)]
    elif isinstance(data, list):
        products = [p for p in data if isinstance(p, dict)]

    out: set[str] = set()
    for row in products:
        if not is_pale_gg_row(row):
            continue
        handle = str(row.get("handle") or "").strip()
        if handle:
            out.add(handle)
    return out
