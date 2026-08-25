#!/usr/bin/env python3
"""Curated Korean copy for Prada women's travel bags."""
from __future__ import annotations

import json
from pathlib import Path

_DATA = Path(__file__).resolve().parents[1] / "src/data/pr/pr-travel-ko-copy.json"
_EXTRA = json.loads(_DATA.read_text()) if _DATA.exists() else {}
DESCRIPTION_KO: dict[str, str] = dict(_EXTRA.get("descriptions") or {})
DETAIL_KO: dict[str, str] = dict(_EXTRA.get("details") or {})
MATERIAL_KO: dict[str, str] = dict(_EXTRA.get("materials") or {})

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
    "Prada Explore Re-Nylon and leather duffel bag": "프라다 익스플로어 Re-Nylon & 가죽 더플백",
    "Nappa leather duffel bag": "나파 가죽 더플백",
    "Re-Nylon and Saffiano leather trolley": "Re-Nylon & 사피아노 가죽 트롤리",
    "Saffiano leather trolley": "사피아노 가죽 트롤리",
    "Polycarbonate trolley": "폴리카보네이트 트롤리",
    "Small Re-Nylon and Saffiano leather suitcase": "스몰 Re-Nylon & 사피아노 가죽 슈트케이스",
    "Medium Re-Nylon and Saffiano leather suitcase": "미디엄 Re-Nylon & 사피아노 가죽 슈트케이스",
    "Linen blend drawstring duffel bag": "린넨 블렌드 드로우스트링 더플백",
    "Canvas drawstring duffle bag": "캔버스 드로우스트링 더플백",
    "Prada Speedrock Re-Nylon and leather pouch": "프라다 스피드록 Re-Nylon & 가죽 파우치",
    "Re-Nylon and Saffiano leather necessaire": "Re-Nylon & 사피아노 가죽 네세세르",
    "Re-Nylon and Saffiano necessaire": "Re-Nylon & 사피아노 네세세르",
    "Re-Nylon and Saffiano leather travel pouch": "Re-Nylon & 사피아노 가죽 트래블 파우치",
    "Saffiano leather travel pouch": "사피아노 가죽 트래블 파우치",
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
    "Caramel": "카라멜",
    "Loden": "로덴",
    "Black/Burnt": "블랙/번트",
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


def seed_travel_cache(cache: dict[str, str]) -> int:
    n = 0
    for mapping in (TITLE_KO, COLOR_KO, DESCRIPTION_KO, DETAIL_KO, MATERIAL_KO):
        for en, ko in mapping.items():
            cache[en] = ko
            n += 1
    return n


def travel_text_ko(text: str | None) -> str | None:
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
