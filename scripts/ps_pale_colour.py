"""Detect Paul Smith pale / white-ish colourways that must skip greymat/rembg.

Official packshots of white, ivory, cream, ecru, etc. are destroyed by soft
remap (garment → grey) or rembg composite onto #e7e7e7 (grey blocks). Keep
paulsmith.com CDN bytes as-is for these colourways — same idea as Burberry.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "src/data/ps/ps-catalog-raw.json"

# Exact colour labels from Elevate entity.colour_group / detailed_colour_label.
PALE_COLOUR_RE = re.compile(
    r"^(white|off[\s-]?white|ivory|cream|ecru|chalk|optic\s*white|"
    r"snow|pearl|bone|alabaster|eggshell|oyster)$",
    re.I,
)

# Handle prefix when PDP entity is missing (PLP-only rows).
_HANDLE_PALE_RE = re.compile(
    r"^(?:mens?|womens?|men-s|women-s)-?"
    r"(white|off-white|ivory|cream|ecru|chalk|pearl|bone)\b"
    r"|^(white|off-white|ivory|cream|ecru|chalk|pearl|bone)\b",
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


def is_pale_ps_colour(
    entity: dict | None = None,
    *,
    handle: str | None = None,
    colour_group: str | None = None,
    detailed_colour: str | None = None,
) -> bool:
    """True when this PS product should keep official CDN bytes (no greymat)."""
    ent = entity or {}
    for raw in (
        colour_group,
        detailed_colour,
        ent.get("colour_group"),
        ent.get("detailed_colour_label"),
    ):
        lab = _label(raw)
        if lab and PALE_COLOUR_RE.match(lab):
            return True
    h = (handle or "").strip().lstrip("/")
    if h and _HANDLE_PALE_RE.search(h.replace("_", "-")):
        return True
    return False


def is_pale_ps_row(row: dict | None) -> bool:
    if not row:
        return False
    return is_pale_ps_colour(
        row.get("entity") if isinstance(row.get("entity"), dict) else {},
        handle=str(row.get("handle") or ""),
    )


def pale_ps_handles(raw: dict | None = None) -> set[str]:
    """All ps-pdp folder names that must skip greymat."""
    data = raw
    if data is None:
        if not RAW_PATH.is_file():
            return set()
        import json

        data = json.loads(RAW_PATH.read_text())
    out: set[str] = set()
    if not isinstance(data, dict):
        return out
    for row in data.values():
        if not isinstance(row, dict):
            continue
        if not is_pale_ps_row(row):
            continue
        handle = str(row.get("handle") or "").strip()
        if handle:
            out.add(handle)
    return out
