#!/usr/bin/env python3
"""Curated Korean copy for Prada women's travel bags."""
from __future__ import annotations

TITLE_KO: dict[str, str] = {
    "Small Re-Nylon pouch": "스몰 Re-Nylon 파우치",
    "Mini Re-Nylon pouch": "미니 Re-Nylon 파우치",
    "Re-Nylon pouch": "Re-Nylon 파우치",
    "Large Re-Nylon zipper pouch": "라지 Re-Nylon 지퍼 파우치",
    "Small Re-Nylon zipper pouch": "스몰 Re-Nylon 지퍼 파우치",
    "Medium Re-Nylon zipper pouch": "미디엄 Re-Nylon 지퍼 파우치",
    "Re-Nylon and Saffiano leather duffel bag": "Re-Nylon & 사피아노 가죽 더플백",
    "Re-Nylon and Saffiano leather duffle bag": "Re-Nylon & 사피아노 가죽 더플백",
    "Saffiano Leather Travel Bag": "사피아노 가죽 트래블백",
    "Saffiano leather travel bag": "사피아노 가죽 트래블백",
    "Linen blend duffle bag": "린넨 블렌드 더플백",
    "Canvas duffle bag": "캔버스 더플백",
    "Canvas duffel bag": "캔버스 더플백",
    "Leather duffel bag": "가죽 더플백",
    "Prada Explore Re-Nylon and leather duffel bag": "Prada Explore Re-Nylon & 가죽 더플백",
    "Nappa leather duffel bag": "나파 가죽 더플백",
    "Re-Nylon and Saffiano leather trolley": "Re-Nylon & 사피아노 가죽 트롤리",
    "Saffiano leather trolley": "사피아노 가죽 트롤리",
    "Polycarbonate trolley": "폴리카보네이트 트롤리",
    "Small Re-Nylon and Saffiano leather suitcase": "스몰 Re-Nylon & 사피아노 가죽 슈트케이스",
    "Linen blend drawstring duffel bag": "린넨 블렌드 드로우스트링 더플백",
    "Canvas drawstring duffle bag": "캔버스 드로우스트링 더플백",
}

COLOR_KO: dict[str, str] = {
    "Black": "블랙",
    "Camel Brown": "카멜 브라운",
    "Brandy": "브랜디",
    "Burgundy": "버건디",
    "Natural": "내추럴",
    "Tabacco": "타바코",
    "Mercury Gray": "머큐리 그레이",
    "Burnt Brown": "번트 브라운",
    "Amber": "앰버",
    "Baltic Blue": "발틱 블루",
    "Desert Beige": "데저트 베이지",
    "Dark Brown": "다크 브라운",
    "Bamboo/Cork beige": "밤부/코르크 베이지",
    "Coffee": "커피",
    "White": "화이트",
    "Red": "레드",
    "Navy": "네이비",
}


def _norm(s: str) -> str:
    return " ".join((s or "").split()).casefold()


_TITLE_CF = {_norm(k): v for k, v in TITLE_KO.items()}
_COLOR_CF = {_norm(k): v for k, v in COLOR_KO.items()}


def seed_travel_cache(cache: dict[str, str]) -> int:
    n = 0
    for mapping in (TITLE_KO, COLOR_KO):
        for en, ko in mapping.items():
            cache[en] = ko
            n += 1
    return n


def travel_text_ko(text: str | None) -> str | None:
    s = (text or "").strip()
    if not s:
        return ""
    if s in TITLE_KO:
        return TITLE_KO[s]
    if s in COLOR_KO:
        return COLOR_KO[s]
    return _TITLE_CF.get(_norm(s)) or _COLOR_CF.get(_norm(s))
