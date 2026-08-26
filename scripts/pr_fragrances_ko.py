#!/usr/bin/env python3
"""Curated Korean copy for Prada Fragrances."""
from __future__ import annotations

import json
from pathlib import Path

_DATA = Path(__file__).resolve().parents[1] / "src/data/pr/pr-fragrances-ko-copy.json"
_EXTRA = json.loads(_DATA.read_text()) if _DATA.exists() else {}
DESCRIPTION_KO: dict[str, str] = dict(_EXTRA.get("descriptions") or {})
DETAIL_KO: dict[str, str] = dict(_EXTRA.get("details") or {})
MATERIAL_KO: dict[str, str] = dict(_EXTRA.get("materials") or {})
TITLE_KO: dict[str, str] = dict(_EXTRA.get("titles") or {})
COLOR_KO: dict[str, str] = dict(_EXTRA.get("colors") or {})

PHRASE_KO: list[tuple[str, str]] = sorted(
    [*DETAIL_KO.items(), *DESCRIPTION_KO.items(), *MATERIAL_KO.items(), *TITLE_KO.items()],
    key=lambda kv: -len(kv[0]),
)


def _norm(s: str) -> str:
    return " ".join((s or "").split()).casefold()


_TITLE_CF = {_norm(k): v for k, v in TITLE_KO.items()}
_COLOR_CF = {_norm(k): v for k, v in COLOR_KO.items()}
_DESC_CF = {_norm(k): v for k, v in DESCRIPTION_KO.items()}
_DETAIL_CF = {_norm(k): v for k, v in DETAIL_KO.items()}
_MAT_CF = {_norm(k): v for k, v in MATERIAL_KO.items()}


def apply_phrases(text: str) -> str:
    out = text or ""
    for en, ko in PHRASE_KO:
        if en in out:
            out = out.replace(en, ko)
    return out


def seed_fragrances_cache(cache: dict[str, str]) -> int:
    n = 0
    for mapping in (TITLE_KO, COLOR_KO, DESCRIPTION_KO, DETAIL_KO, MATERIAL_KO):
        for en, ko in mapping.items():
            cache[en] = ko
            n += 1
    return n


def fragrances_text_ko(text: str | None) -> str | None:
    s = (text or "").strip()
    if not s:
        return ""
    for mapping in (TITLE_KO, COLOR_KO, DESCRIPTION_KO, DETAIL_KO, MATERIAL_KO):
        if s in mapping:
            return mapping[s]
    hit = (
        _TITLE_CF.get(_norm(s))
        or _COLOR_CF.get(_norm(s))
        or _DESC_CF.get(_norm(s))
        or _DETAIL_CF.get(_norm(s))
        or _MAT_CF.get(_norm(s))
    )
    if hit:
        return hit
    return None
