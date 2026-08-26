#!/usr/bin/env python3
"""Curated Korean copy for Prada Linea Rossa."""
from __future__ import annotations

import json
from pathlib import Path

_DATA = Path(__file__).resolve().parents[1] / "src/data/pr/pr-linea-rossa-ko-copy.json"
_EXTRA = json.loads(_DATA.read_text()) if _DATA.exists() else {}
DESCRIPTION_KO: dict[str, str] = dict(_EXTRA.get("descriptions") or {})
DETAIL_KO: dict[str, str] = dict(_EXTRA.get("details") or {})
MATERIAL_KO: dict[str, str] = dict(_EXTRA.get("materials") or {})
TITLE_KO: dict[str, str] = dict(_EXTRA.get("titles") or {})

# Hard overrides / common titles if JSON missing keys
TITLE_KO.update(
    {
        "Prada Linea Rossa sunglasses": "Prada Linea Rossa 선글라스",
        "Linea Rossa sunglasses": "Linea Rossa 선글라스",
        "Patent leather and technical fabric Prada America's Cup sneakers": "페이턴트 가죽 & 테크니컬 패브릭 Prada America's Cup 스니커즈",
        "Prada America's Cup sneakers": "Prada America's Cup 스니커즈",
        "Luna Rossa Carbon EDP 100 ml": "Luna Rossa Carbon 오 드 퍼퓸 100ml",
        "Luna Rossa Carbon": "Luna Rossa Carbon",
        "Stretch jersey swimsuit top": "스트레치 저지 스윔수트 탑",
        "Stretch jersey swim shorts": "스트레치 저지 스윔 쇼츠",
        "Re-Nylon baseball cap": "Re-Nylon 베이스볼 캡",
        "Technical fabric sneakers": "테크니컬 패브릭 스니커즈",
    }
)

COLOR_KO: dict[str, str] = {
    "Black": "블랙",
    "White": "화이트",
    "Red": "레드",
    "Blue": "블루",
    "Navy": "네이비",
    "Grey": "그레이",
    "Gray": "그레이",
    "Silver": "실버",
    "Orange": "오렌지",
    "Yellow": "옐로우",
    "Green": "그린",
    "Brown": "브라운",
    "Beige": "베이지",
    "Crystal": "크리스탈",
    "Havana": "아바나",
}

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


def seed_linea_rossa_cache(cache: dict[str, str]) -> int:
    n = 0
    for mapping in (TITLE_KO, COLOR_KO, DESCRIPTION_KO, DETAIL_KO, MATERIAL_KO):
        for en, ko in mapping.items():
            cache[en] = ko
            n += 1
    return n


def linea_rossa_text_ko(text: str | None) -> str | None:
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
