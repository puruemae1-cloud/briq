#!/usr/bin/env python3
"""Curated Korean copy for Prada women's accessories (non-SLG)."""
from __future__ import annotations

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


def _norm(s: str) -> str:
    return " ".join((s or "").split()).casefold()


_TITLE_CF = {_norm(k): v for k, v in TITLE_KO.items()}
_COLOR_CF = {_norm(k): v for k, v in COLOR_KO.items()}


def seed_accessories_cache(cache: dict[str, str]) -> int:
    n = 0
    for mapping in (TITLE_KO, COLOR_KO):
        for en, ko in mapping.items():
            cache[en] = ko
            n += 1
    return n


def accessories_text_ko(text: str | None) -> str | None:
    s = (text or "").strip()
    if not s:
        return ""
    if s in TITLE_KO:
        return TITLE_KO[s]
    if s in COLOR_KO:
        return COLOR_KO[s]
    hit = _TITLE_CF.get(_norm(s)) or _COLOR_CF.get(_norm(s))
    return hit
