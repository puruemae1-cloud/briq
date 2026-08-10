"""Detect Gucci pale / white-ish colourways that must skip greymat/rembg.

Official gucci.com packshots use DarkGray_Center mats. Soft remap or rembg
onto #e7e7e7 can crush white / ivory / cream / light garments. Keep CDN bytes
as-is for these colourways — same idea as ps_pale_colour.py for Paul Smith.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GC_DATA = ROOT / "src/data/gc"
CATALOG_PATH = GC_DATA / "gc-catalog.json"

# Primary colour labels (variant / colorKey) that start with a pale token.
PALE_PRIMARY_RE = re.compile(
    r"^(white|off[\s-]?white|ivory|cream|ecru|chalk|optic\s*white|"
    r"snow|pearl|bone|alabaster|eggshell|oyster|light)\b",
    re.I,
)

# Jewelry metals — not garment pale.
_SKIP_METAL_RE = re.compile(r"white[\s-]?gold|whitegold", re.I)


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return str(
            value.get("label")
            or value.get("name")
            or value.get("id")
            or value.get("color")
            or value.get("colour")
            or ""
        ).strip()
    return str(value).strip()


def is_pale_gc_colour(
    *,
    variant: str | None = None,
    color_key: str | None = None,
    color_name: str | None = None,
    title: str | None = None,
) -> bool:
    """True when this GC colourway should keep official CDN bytes (no greymat)."""
    for raw in (variant, color_key, color_name):
        lab = _norm(raw)
        if not lab:
            continue
        if _SKIP_METAL_RE.search(lab):
            continue
        # colorKey uses hyphens: white-leather, light-blue, ivory-gg-canvas
        spaced = lab.replace("-", " ").replace("_", " ")
        if PALE_PRIMARY_RE.match(lab) or PALE_PRIMARY_RE.match(spaced):
            return True
    # Title fallback only for obvious white/ivory lead-ins (avoid "with white…")
    t = _norm(title)
    if t and PALE_PRIMARY_RE.match(t):
        return True
    return False


def is_pale_gc_row(row: dict | None) -> bool:
    if not row:
        return False
    return is_pale_gc_colour(
        variant=_norm(row.get("variant")),
        title=_norm(row.get("title") or row.get("name")),
        color_key=_norm(row.get("colorKey") or row.get("color_key")),
        color_name=_norm(
            row.get("colorNameKo") or row.get("colorName") or row.get("label")
        ),
    )


def iter_gc_raw_products() -> list[dict]:
    """All product rows across GC *-catalog-raw.json files (deduped by code)."""
    out: list[dict] = []
    seen: set[str] = set()
    if not GC_DATA.is_dir():
        return out
    for path in sorted(GC_DATA.glob("*catalog-raw.json")):
        try:
            data = json.loads(path.read_text())
        except Exception:
            continue
        products = data.get("products") if isinstance(data, dict) else None
        if not isinstance(products, list):
            continue
        for row in products:
            if not isinstance(row, dict):
                continue
            code = str(row.get("productCode") or "").strip()
            if not code or code in seen:
                continue
            seen.add(code)
            out.append(row)
    return out


def pale_gc_codes(
    *,
    include_catalog: bool = True,
) -> set[str]:
    """All gc-pdp folder names (product codes) that must skip greymat."""
    out: set[str] = set()
    for row in iter_gc_raw_products():
        if not is_pale_gc_row(row):
            continue
        code = str(row.get("productCode") or "").strip()
        if code:
            out.add(code)

    if include_catalog and CATALOG_PATH.is_file():
        try:
            catalog = json.loads(CATALOG_PATH.read_text())
        except Exception:
            catalog = []
        if isinstance(catalog, list):
            for prod in catalog:
                if not isinstance(prod, dict):
                    continue
                variants = prod.get("variants") or []
                v0 = variants[0] if variants and isinstance(variants[0], dict) else {}
                if not is_pale_gc_colour(
                    color_key=_norm(v0.get("colorKey")),
                    color_name=_norm(v0.get("colorNameKo") or v0.get("colorName")),
                    title=_norm(prod.get("name") or prod.get("nameKo")),
                ):
                    continue
                sku = str(prod.get("sku") or "").strip()
                if sku:
                    out.add(sku)
                # also from image path /products/gc-pdp/CODE/...
                for img in prod.get("images") or []:
                    if not isinstance(img, str):
                        continue
                    m = re.search(r"/products/gc-pdp/([^/]+)/", img)
                    if m:
                        out.add(m.group(1))
                        break
    return out
