"""Detect Arc'teryx pale / white-ish apparel colourways that must skip greymat.

Official images.arcteryx.com packshots of White Light, Arctic Silk, Sea Salt,
Solitude, Moondrop, Atmos, etc. are crushed by soft remap / rembg onto #e7e7e7
(garment blends into the grey mat). Keep CDN bytes as-is — same idea as
ps_pale_colour.py / gc_pale_colour.py.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CACHE_PATH = ROOT / "src/data/ax/ax-apparel-pdp-cache.json"
CATALOG_PATH = ROOT / "src/data/ax/ax-apparel-catalog.json"

# Official colour labels (and slug tokens) that read as white / off-white /
# pale grey on Arc'teryx GB.
PALE_TOKEN_RE = re.compile(
    r"(^|[\s/_-])("
    r"white(?:[\s_-]?light)?|off[\s_-]?white|arctic[\s_-]?silk|"
    r"sea[\s_-]?salt|solitude|moondrop|lt[\s_-]?moondrop|atmos"
    r")([\s/_-]|$)",
    re.I,
)


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:80] or "item"


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


def is_pale_ax_colour(
    *,
    color: str | None = None,
    color_key: str | None = None,
    color_name: str | None = None,
) -> bool:
    """True when this AX colourway should keep official CDN bytes (no greymat)."""
    for raw in (color, color_key, color_name):
        lab = _norm(raw)
        if not lab:
            continue
        spaced = lab.replace("-", " ").replace("_", " ").replace("/", " ")
        if PALE_TOKEN_RE.search(lab) or PALE_TOKEN_RE.search(spaced):
            return True
        # Slug form: white-light, arctic-silk, sea-salt-habitat, …
        if PALE_TOKEN_RE.search(slugify(lab)):
            return True
    return False


def pale_axa_colour_dirs(cache: dict | None = None) -> set[str]:
    """Relative dirs under axa-pdp that must skip greymat: ``PID/color-slug``."""
    data = cache
    if data is None:
        if not CACHE_PATH.is_file():
            return set()
        data = json.loads(CACHE_PATH.read_text())
    out: set[str] = set()
    if not isinstance(data, dict):
        return out
    for pid, row in data.items():
        if not isinstance(row, dict):
            continue
        pid_s = str(pid).strip()
        if not pid_s or pid_s.startswith("_"):
            continue
        colours = row.get("colourImages") or {}
        if isinstance(colours, dict):
            for color in colours:
                if is_pale_ax_colour(color=str(color)):
                    out.add(f"{pid_s}/{slugify(str(color))}")
        for color in row.get("colours") or []:
            if is_pale_ax_colour(color=str(color)):
                out.add(f"{pid_s}/{slugify(str(color))}")
    if CATALOG_PATH.is_file():
        try:
            catalog = json.loads(CATALOG_PATH.read_text())
        except Exception:
            catalog = []
        if isinstance(catalog, list):
            for prod in catalog:
                if not isinstance(prod, dict):
                    continue
                for v in prod.get("variants") or []:
                    if not isinstance(v, dict):
                        continue
                    ck = _norm(v.get("colorKey"))
                    cn = _norm(v.get("colorNameKo") or v.get("colorName") or v.get("nameKo"))
                    if not is_pale_ax_colour(color_key=ck, color_name=cn):
                        continue
                    img = _norm(v.get("image") or "")
                    m = re.search(r"/products/axa-pdp/([^/]+)/([^/]+)/", img)
                    if m:
                        out.add(f"{m.group(1)}/{m.group(2)}")
                    elif ck:
                        # Fall back: product id is axa-x000… → X000…
                        sku = str(prod.get("sku") or "").strip()
                        if not sku:
                            pid = str(prod.get("id") or "")
                            sku = pid.replace("axa-", "").upper() if pid.startswith("axa-") else ""
                        if sku:
                            out.add(f"{sku}/{slugify(ck)}")
    return out


def is_pale_axa_image_path(path: Path | str) -> bool:
    """True when path is under axa-pdp/<pid>/<pale-slug>/…"""
    p = Path(path)
    parts = p.parts
    try:
        i = parts.index("axa-pdp")
    except ValueError:
        return False
    if i + 2 >= len(parts):
        return False
    key = f"{parts[i + 1]}/{parts[i + 2]}"
    return key in pale_axa_colour_dirs()
