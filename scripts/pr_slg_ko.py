#!/usr/bin/env python3
"""Curated Korean copy for Prada small leather goods (women + men)."""
from __future__ import annotations

import json
from pathlib import Path

_DATA = Path(__file__).resolve().parents[1] / "src/data/pr/pr-slg-ko-copy.json"
_EXTRA = json.loads(_DATA.read_text()) if _DATA.exists() else {}
DESCRIPTION_KO: dict[str, str] = dict(_EXTRA.get("descriptions") or {})
DETAIL_KO: dict[str, str] = dict(_EXTRA.get("details") or {})

# Exact product titles from Prada GB hub (officialNameEn / title)
TITLE_KO: dict[str, str] = {
    "Leather wallet with shoulder strap": "숄더 스트랩 가죽 월렛",
    "Leather wallet": "가죽 월렛",
    "Leather pouch": "가죽 파우치",
    "Small leather wallet": "스몰 가죽 월렛",
    "Leather card holder": "가죽 카드홀더",
    "Leather card holder with zipper": "지퍼 가죽 카드홀더",
    "Zipper leather card holder": "지퍼 가죽 카드홀더",
    "Large leather wallet": "라지 가죽 월렛",
    "Leather wallet with coin purse": "코인 퍼스 가죽 월렛",
    "Leather wallet with coin compartment": "코인 수납 가죽 월렛",
    "Leather coin purse": "가죽 코인 퍼스",
    "Antiqued leather wallet": "앤틱 가죽 월렛",
    "Small antiqued leather wallet": "스몰 앤틱 가죽 월렛",
    "Antiqued leather card holder": "앤틱 가죽 카드홀더",
    "Antiqued leather pouch": "앤틱 가죽 파우치",
    "Small nappa leather wallet": "스몰 나파 가죽 월렛",
    "Large nappa leather wallet": "라지 나파 가죽 월렛",
    "Nappa leather wallet with shoulder strap": "숄더 스트랩 나파 가죽 월렛",
    "Nappa leather smartphone holder": "나파 가죽 스마트폰 홀더",
    "Nappa leather smartphone pouch": "나파 가죽 스마트폰 파우치",
    "Nappa leather pouch": "나파 가죽 파우치",
    "Nappa leather zipper pouch": "나파 가죽 지퍼 파우치",
    "Nappa leather card holder": "나파 가죽 카드홀더",
    "Saffiano leather smartphone pouch": "사피아노 가죽 스마트폰 파우치",
    "Saffiano leather smartphone case": "사피아노 가죽 스마트폰 케이스",
    "Saffiano leather wallet with shoulder strap": "숄더 스트랩 사피아노 가죽 월렛",
    "Saffiano leather case for iPhone 17 Pro": "아이폰 17 프로용 사피아노 가죽 케이스",
    "Saffiano leather case for iPhone 17 Pro Max": "아이폰 17 프로 맥스용 사피아노 가죽 케이스",
    "Saffiano leather card holder": "사피아노 가죽 카드홀더",
    "Saffiano Leather card holder": "사피아노 가죽 카드홀더",
    "Saffiano Leather Card Holder": "사피아노 가죽 카드홀더",
    "Saffiano leather card holder with shoulder strap": "숄더 스트랩 사피아노 가죽 카드홀더",
    "Saffiano Leather Badge Holder": "사피아노 가죽 뱃지 홀더",
    "Saffiano leather badge holder": "사피아노 가죽 뱃지 홀더",
    "Saffiano leather pouch": "사피아노 가죽 파우치",
    "Saffiano leather envelope clutch": "사피아노 가죽 엔벨로프 클러치",
    "Saffiano leather document holder": "사피아노 가죽 서류 홀더",
    "Saffiano leather passport holder": "사피아노 가죽 여권 홀더",
    "Saffiano leather key case": "사피아노 가죽 키 케이스",
    "Saffiano leather coin purse": "사피아노 가죽 코인 퍼스",
    "Saffiano coin purse": "사피아노 코인 퍼스",
    "Saffiano leather headphone case with keychain": "키체인 사피아노 가죽 헤드폰 케이스",
    "Saffiano Leather Mini Pouch with keychain": "키체인 사피아노 가죽 미니 파우치",
    "Saffiano leather zip around wallet": "사피아노 가죽 지퍼 어라운드 월렛",
    "Saffiano wallet": "사피아노 월렛",
    "Saffiano leather wallet": "사피아노 가죽 월렛",
    "Saffiano Leather Wallet": "사피아노 가죽 월렛",
    "Saffiano leather wallet with coin purse": "코인 퍼스 사피아노 가죽 월렛",
    "Saffiano Leather Wallet with coin purse": "코인 퍼스 사피아노 가죽 월렛",
    "Small Saffiano leather wallet": "스몰 사피아노 가죽 월렛",
    "Small Saffiano Leather Wallet": "스몰 사피아노 가죽 월렛",
    "Large Saffiano leather wallet": "라지 사피아노 가죽 월렛",
    "Large Saffiano Leather Wallet": "라지 사피아노 가죽 월렛",
    "Small Saffiano and smooth leather wallet": "스몰 사피아노 & 스무스 가죽 월렛",
    "Large Saffiano and leather wallet": "라지 사피아노 & 가죽 월렛",
    "Large Saffiano and smooth leather wallet": "라지 사피아노 & 스무스 가죽 월렛",
    "Saffiano and smooth leather card holder": "사피아노 & 스무스 가죽 카드홀더",
    "Re-Nylon and Saffiano leather card holder": "Re-Nylon & 사피아노 가죽 카드홀더",
    "Re-Nylon and Saffiano leather smartphone case": "Re-Nylon & 사피아노 가죽 스마트폰 케이스",
    "Prada Speedrock Re-Nylon and leather card holder": "프라다 스피드록 Re-Nylon & 가죽 카드홀더",
    "Prada Speedrock Re-Nylon and leather card holder with strap": "스트랩 프라다 스피드록 Re-Nylon & 가죽 카드홀더",
    "Prada Speedrock Re-Nylon smartphone case": "프라다 스피드록 Re-Nylon 스마트폰 케이스",
    "Small woven madras leather wallet": "스몰 우븐 마드라스 가죽 월렛",
    "Woven madras leather card holder": "우븐 마드라스 가죽 카드홀더",
    "Crochet card holder with shoulder strap": "숄더 스트랩 크로셰 카드홀더",
    "Re-Nylon pouch": "Re-Nylon 파우치",
    "Re-Nylon card holder": "Re-Nylon 카드홀더",
    "Re-Nylon wallet": "Re-Nylon 월렛",
    "Re-Nylon smartphone case": "Re-Nylon 스마트폰 케이스",
    "Re-Nylon smartphone pouch": "Re-Nylon 스마트폰 파우치",
    "Suede smartphone pouch": "스웨이드 스마트폰 파우치",
}

COLOR_KO: dict[str, str] = {
    "Black": "블랙",
    "White": "화이트",
    "Dark Brown": "다크 브라운",
    "Red": "레드",
    "Fiery Red": "파이어리 레드",
    "Rosy Blush": "로지 블러시",
    "Dark Grey": "다크 그레이",
    "Forest": "포레스트",
    "Peony Pink": "피오니 핑크",
    "Powder Pink": "파우더 핑크",
    "Peach": "피치",
    "Chalk White": "초크 화이트",
    "Caramel": "카라멜",
    "Cognac": "코냑",
    "Pale Blue": "페일 블루",
    "Alabaster": "알라바스터",
    "Chestnut Brown": "체스트넛 브라운",
    "Sand Beige": "샌드 베이지",
    "Beige": "베이지",
    "Navy": "네이비",
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
    "Neutral": "뉴트럴",
    "Natural": "내추럴",
    "Chrome": "크롬",
    "Burgundy": "버건디",
    "Aviator Blue": "에비에이터 블루",
    "Aviation Blue": "에비에이션 블루",
    "Pyrite": "파이라이트",
    "Clay Grey": "클레이 그레이",
    "Travertine Stone": "트래버틴 스톤",
    "Opal": "오팔",
    "Black/Hibiscus": "블랙/히비스커스",
    "Black/Pale Pink": "블랙/페일 핑크",
    "Black/Baltic Blue": "블랙/발틱 블루",
    "Peach/Red": "피치/레드",
    "Granite Gray": "그래나이트 그레이",
    "Ivy Green": "아이비 그린",
    "Brandy": "브랜디",
    "Baltic Blue": "발틱 블루",
    "Baltic Blue/Marble Gray": "발틱 블루/마블 그레이",
    "Sienna": "시에나",
    "Smoky Gray": "스모키 그레이",
    "Cocoa Brown": "코코아 브라운",
    "Loden Green": "로덴 그린",
    "Marina Blue": "마리나 블루",
    "Ruby Red": "루비 레드",
    "Bamboo Gray": "밤부 그레이",
    "Graphite": "그래파이트",
    "Leather/Talc": "레더/탈크",
    "Selva Green/Burgundy": "셀바 그린/버건디",
}

PHRASE_KO: list[tuple[str, str]] = sorted(
    [*DETAIL_KO.items(), *DESCRIPTION_KO.items()],
    key=lambda kv: -len(kv[0]),
)


def _norm(s: str) -> str:
    return " ".join((s or "").split()).casefold()


_TITLE_CF = {_norm(k): v for k, v in TITLE_KO.items()}
_COLOR_CF = {_norm(k): v for k, v in COLOR_KO.items()}
_DESC_CF = {_norm(k): v for k, v in DESCRIPTION_KO.items()}
_DETAIL_CF = {_norm(k): v for k, v in DETAIL_KO.items()}


def apply_phrases(text: str) -> str:
    out = text or ""
    for en, ko in PHRASE_KO:
        if en in out:
            out = out.replace(en, ko)
    return out


def seed_slg_cache(cache: dict[str, str]) -> int:
    n = 0
    for mapping in (TITLE_KO, COLOR_KO, DESCRIPTION_KO, DETAIL_KO):
        for en, ko in mapping.items():
            cache[en] = ko
            n += 1
    return n


def slg_text_ko(text: str | None) -> str | None:
    s = (text or "").strip()
    if not s:
        return ""
    for mapping in (TITLE_KO, COLOR_KO, DESCRIPTION_KO, DETAIL_KO):
        if s in mapping:
            return mapping[s]
    hit = (
        _TITLE_CF.get(_norm(s))
        or _COLOR_CF.get(_norm(s))
        or _DESC_CF.get(_norm(s))
        or _DETAIL_CF.get(_norm(s))
    )
    if hit:
        return hit
    return None
