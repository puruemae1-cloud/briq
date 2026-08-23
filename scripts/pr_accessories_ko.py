#!/usr/bin/env python3
"""Curated Korean copy for Prada women's accessories (non-SLG)."""
from __future__ import annotations

import json
from pathlib import Path

_DATA = Path(__file__).resolve().parents[1] / "src/data/pr/pr-accessories-ko-copy.json"
_EXTRA = json.loads(_DATA.read_text()) if _DATA.exists() else {}
DESCRIPTION_KO: dict[str, str] = dict(_EXTRA.get("descriptions") or {})
DETAIL_KO: dict[str, str] = dict(_EXTRA.get("details") or {})
MATERIAL_KO: dict[str, str] = dict(_EXTRA.get("materials") or {})

TITLE_KO: dict[str, str] = {
    "Sunglasses with triangle logo": "트라이앵글 로고 선글라스",
    "Sunglasses with Triangle Logo": "트라이앵글 로고 선글라스",
    "Symbole sunglasses": "Symbole 선글라스",
    "Prada Symbole sunglasses": "Prada Symbole 선글라스",
    "Jacquard silk scarf 90": "자카드 실크 스카프 90",
    "Jacquard silk scarf 70": "자카드 실크 스카프 70",
    "Printed silk scarf 90": "프린트 실크 스카프 90",
    "Printed silk scarf 70": "프린트 실크 스카프 70",
    "Silk bandana": "실크 반다나",
    "Re-Nylon bucket hat": "Re-Nylon 버킷햇",
    "Re-Nylon baseball cap": "Re-Nylon 베이스볼 캡",
    "Nylon baseball cap": "나일론 베이스볼 캡",
    "Leather long gloves": "가죽 롱 글러브",
    "Nappa leather gloves": "나파 가죽 글러브",
    "Leather hair clip": "가죽 헤어 클립",
    "Re-Nylon hair clip": "Re-Nylon 헤어 클립",
    "Saffiano leather keychain": "사피아노 가죽 키체인",
    "Saffiano leather key ring": "사피아노 가죽 키링",
    "Re-Nylon keychain": "Re-Nylon 키체인",
    "Enameled metal ring": "에나멜 메탈 링",
    "Enameled metal necklace": "에나멜 메탈 네클리스",
    "Enameled metal bracelet": "에나멜 메탈 브레이슬릿",
    "Enameled metal earrings": "에나멜 메탈 이어링",
    "Suede belt": "스웨이드 벨트",
    "Saffiano leather belt": "사피아노 가죽 벨트",
    "Re-Nylon pouch": "Re-Nylon 파우치",
    "Micro Re-Nylon pouch": "마이크로 Re-Nylon 파우치",
    "Mini Re-Nylon pouch": "미니 Re-Nylon 파우치",
    "Nappa leather pouch": "나파 가죽 파우치",
    "Saffiano leather pouch": "사피아노 가죽 파우치",
}

COLOR_KO: dict[str, str] = {
    "Black": "블랙",
    "White": "화이트",
    "Dark Brown": "다크 브라운",
    "Red": "레드",
    "Navy": "네이비",
    "Beige": "베이지",
    "Sand Beige": "샌드 베이지",
    "Ivory": "아이보리",
    "Silver": "실버",
    "Gold": "골드",
    "Pink": "핑크",
    "Green": "그린",
    "Orange": "오렌지",
    "Grey": "그레이",
    "Gray": "그레이",
    "Brown": "브라운",
    "Blue": "블루",
    "Natural": "내추럴",
    "Camel": "카멜",
    "Cognac": "코냑",
    "Burgundy": "버건디",
    "Dark Grey": "다크 그레이",
    "Pale Blue": "페일 블루",
    "Forest": "포레스트",
    "Neutral": "뉴트럴",
    "Havana": "아바나",
    "Crystal": "크리스탈",
    "Tortoiseshell": "토터스쉘",
}

PHRASE_KO: list[tuple[str, str]] = sorted(
    [*DETAIL_KO.items(), *DESCRIPTION_KO.items(), *MATERIAL_KO.items()],
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


def seed_accessories_cache(cache: dict[str, str]) -> int:
    n = 0
    for mapping in (TITLE_KO, COLOR_KO, DESCRIPTION_KO, DETAIL_KO, MATERIAL_KO):
        for en, ko in mapping.items():
            cache[en] = ko
            n += 1
    return n


def accessories_text_ko(text: str | None) -> str | None:
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
