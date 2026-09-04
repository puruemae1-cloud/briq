"""Detect Belstaff products that must skip greymat/rembg.

White / chalk / pale-stone / silver / sand packshots are destroyed by soft
remap and rembg (washed sneakers, grey blocks). Keep official Shopify CDN
bytes — same policy as ps_pale_colour / ax_pale_colour / gc_pale_colour.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "src/data/bs/bs-catalog-raw.json"

# Colour tokens that appear as Belstaff handle suffixes or colorName labels.
PALE_TOKEN_RE = re.compile(
    r"(^|[-_/ ])("
    r"white|flat[\s-]?white|off[\s-]?white|optic[\s-]?white|"
    r"ivory|cream|ecru|chalk|bone|pearl|porcelain|snow|alabaster|"
    r"pale[\s-]?stone|stone|sand|dark[\s-]?sand|beige|putty|"
    r"silver|silver[\s-]?birch|ash|cloud|concrete|mist|heather|"
    r"natural|oyster|champagne|linen|ecru"
    r")([-_/ ]|$)",
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


def is_pale_bs_colour(
    *,
    handle: str | None = None,
    color_name: str | None = None,
    title: str | None = None,
) -> bool:
    """True when this Belstaff SKU should keep official CDN bytes (no greymat)."""
    for raw in (color_name, handle, title):
        lab = _label(raw)
        if lab and PALE_TOKEN_RE.search(lab.replace("_", "-")):
            return True
    return False


def is_pale_bs_row(row: dict | None) -> bool:
    if not row:
        return False
    return is_pale_bs_colour(
        handle=str(row.get("handle") or ""),
        color_name=str(row.get("colorName") or row.get("color") or ""),
        title=str(row.get("title") or ""),
    )


def pale_bs_handles(raw: dict | list | None = None) -> set[str]:
    """All bs-pdp folder names that must skip greymat."""
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
        if not is_pale_bs_row(row):
            continue
        handle = str(row.get("handle") or "").strip()
        if handle:
            out.add(handle)
    return out
