#!/usr/bin/env python3
"""Curated Korean copy for Prada men's handbags."""
from __future__ import annotations

import json
from pathlib import Path

_DATA = Path(__file__).resolve().parents[1] / "src/data/pr/pr-mens-handbags-ko-copy.json"
_MAP: dict[str, str] = json.loads(_DATA.read_text()) if _DATA.exists() else {}


def mens_handbag_text_ko(text: str) -> str | None:
    s = (text or "").strip()
    if not s:
        return None
    hit = _MAP.get(s)
    return hit if hit else None


def seed_mens_handbags_cache(cache: dict[str, str]) -> int:
    n = 0
    for en, ko in _MAP.items():
        if not en or not ko:
            continue
        if en not in cache or cache.get(en) != ko:
            cache[en] = ko
            n += 1
    return n
