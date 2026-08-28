"""Detect Paul Smith products that must skip greymat/rembg.

All PS *clothing* (mens / womens / tailoring / suits) keeps official CDN bytes —
greymat/rembg destroys light studio mats and pale garments (sand, beige, ecru,
white, grey, …). Shoes and accessories may still greymat when backgrounds are
very light.

Pale colour detection also covers white / ivory / cream / ecru / mid greys when
channel metadata is missing (PLP-only rows).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "src/data/ps/ps-catalog-raw.json"

# Apparel channels — never greymat (official paulsmith.com packshots are fine).
PS_CLOTHING_CHANNELS = frozenset(
    {"clothing", "clothing-women", "tailoring", "suits-women"}
)

# Exact colour labels from Elevate entity.colour_group / detailed_colour_label.
PALE_COLOUR_RE = re.compile(
    r"^(white|off[\s-]?white|ivory|cream|ecru|chalk|optic\s*white|"
    r"snow|pearl|bone|alabaster|eggshell|oyster|"
    # Mid greys / silver — rembg on light mats leaves awkward white patches.
    r"grey|gray|silver|grey\s*marl|gray\s*marl|light\s*grey|light\s*gray|"
    r"heather\s*grey|heather\s*gray|smoke\s*grey|smoke\s*gray|ash|marl)$",
    re.I,
)

# colour_group alone is enough for the whole Grey / Silver family (incl. charcoal).
PALE_COLOUR_GROUP_RE = re.compile(
    r"^(white|off[\s-]?white|ivory|cream|ecru|chalk|grey|gray|silver)$",
    re.I,
)

# Handle prefix when PDP entity is missing (PLP-only rows).
_HANDLE_PALE_RE = re.compile(
    r"^(?:mens?|womens?|men-s|women-s)-?"
    r"(white|off-white|ivory|cream|ecru|chalk|pearl|bone|"
    r"grey|gray|silver|grey-marl|gray-marl)\b"
    r"|^(white|off-white|ivory|cream|ecru|chalk|pearl|bone|"
    r"grey|gray|silver|grey-marl|gray-marl)\b",
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
        ent.get("colour_group"),
    ):
        lab = _label(raw)
        if lab and PALE_COLOUR_GROUP_RE.match(lab):
            return True
    for raw in (
        detailed_colour,
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


def is_ps_clothing_row(row: dict | None) -> bool:
    """True for PS apparel (clothing / tailoring / suits) — skip greymat."""
    if not row:
        return False
    channels = row.get("channels") or []
    return bool(set(channels) & PS_CLOTHING_CHANNELS)


def is_ps_no_greymat_row(row: dict | None) -> bool:
    """True when this PS product must keep official CDN bytes (no greymat)."""
    if not row:
        return False
    if is_ps_clothing_row(row):
        return True
    return is_pale_ps_row(row)


def should_skip_ps_greymat(
    entity: dict | None = None,
    *,
    handle: str | None = None,
    channels: list[str] | set[str] | None = None,
) -> bool:
    """True when scrape/push must not greymat this PS SKU."""
    if channels and set(channels) & PS_CLOTHING_CHANNELS:
        return True
    return is_pale_ps_colour(entity, handle=handle)


def ps_no_greymat_handles(raw: dict | None = None) -> set[str]:
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
        if not is_ps_no_greymat_row(row):
            continue
        handle = str(row.get("handle") or "").strip()
        if handle:
            out.add(handle)
    return out


def pale_ps_handles(raw: dict | None = None) -> set[str]:
    """Alias for ps_no_greymat_handles (clothing + pale colourways)."""
    return ps_no_greymat_handles(raw)
