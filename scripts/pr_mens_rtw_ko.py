#!/usr/bin/env python3
"""Curated Korean copy helpers for Prada men's ready-to-wear."""
from __future__ import annotations

import json
from pathlib import Path

_DATA = Path(__file__).resolve().parents[1] / "src/data/pr/pr-mens-rtw-ko-copy.json"
_EXTRA: dict = json.loads(_DATA.read_text()) if _DATA.exists() else {}

TITLE_KO: dict[str, str] = dict(_EXTRA.get("titles") or {})
DESCRIPTION_KO: dict[str, str] = dict(_EXTRA.get("descriptions") or {})
DETAIL_KO: dict[str, str] = dict(_EXTRA.get("details") or {})

# Common garment / fit phrases (longer first when applied)
PHRASE_KO: list[tuple[str, str]] = sorted(
    [
        ("Regular fit", "레귤러 핏"),
        ("Slim fit", "슬림 핏"),
        ("Relaxed fit", "릴랙스드 핏"),
        ("Straight leg", "스트레이트 레그"),
        ("Tapered leg", "테이퍼드 레그"),
        ("Wide leg", "와이드 레그"),
        ("Cropped fit", "크롭드 핏"),
        ("Oversized fit", "오버사이즈드 핏"),
        ("Single-breasted", "싱글 브레스티드"),
        ("Double-breasted", "더블 브레스티드"),
        ("Notch lapel", "노치 라펠"),
        ("Peak lapel", "피크 라펠"),
        ("Button closure", "버튼 클로저"),
        ("Zip closure", "지퍼 클로저"),
        ("Elastic waistband", "엘라스틱 허리밴드"),
        ("Drawstring waist", "드로스트링 허리"),
        ("Ribbed cuffs", "리브드 커프"),
        ("Ribbed hem", "리브드 밑단"),
        ("Long sleeves", "롱 슬리브"),
        ("Short sleeves", "숏 슬리브"),
        ("Crew neck", "크루넥"),
        ("V-neck", "브이넥"),
        ("Polo collar", "폴로 칼라"),
        ("Spread collar", "스프레드 칼라"),
        ("Classic collar", "클래식 칼라"),
        ("Patch pockets", "패치 포켓"),
        ("Side pockets", "사이드 포켓"),
        ("Chest pocket", "체스트 포켓"),
        ("Welt pockets", "웰트 포켓"),
        ("Pleated trousers", "플리츠 팬츠"),
        ("Flat front", "플랫 프론트"),
        ("Virgin wool", "버진 울"),
        ("Cashmere", "캐시미어"),
        ("Poplin", "포플린"),
        ("Gabardine", "개버딘"),
        ("Technical fabric", "테크니컬 패브릭"),
        ("Padded", "패디드"),
        ("Quilted", "퀼티드"),
        ("Lined", "안감"),
        ("Unlined", "무안감"),
        ("Made in Italy", "메이드 인 이탈리아"),
        ("Product code", "제품 코드"),
        ("Composition", "소재 구성"),
        ("Care", "케어"),
        ("Suit", "수트"),
        ("Blazer", "블레이저"),
        ("Trousers", "팬츠"),
        ("Bermuda shorts", "버뮤다 쇼츠"),
        ("Polo shirt", "폴로 셔츠"),
        ("T-shirt", "티셔츠"),
        ("Sweatshirt", "스웻셔츠"),
        ("Jogging suit", "조깅 수트"),
        ("Underwear", "언더웨어"),
        ("Pajamas", "파자마"),
        ("Swim shorts", "스윔 쇼츠"),
        ("Swim trunks", "스윔 트렁크"),
        ("Leather jacket", "레더 재킷"),
        ("Bomber jacket", "봄ber 재킷"),
        ("Down jacket", "다운 재킷"),
        ("Windbreaker", "윈드브레이커"),
        ("Coat", "코트"),
        ("Jacket", "재킷"),
        ("Knitwear", "니트웨어"),
        ("Denim", "데님"),
        ("Shirt", "셔츠"),
        ("Wide shoulder", "와이드 숄더"),
        ("Partially lined garment", "부분 안감"),
        ("Partially lined", "부분 안감"),
        ("Raw treatment", "로우 트리트먼트"),
        ("Washed and garment-dyed treatment", "워시 & 가먼트 다이드 트리트먼트"),
        ("Washed and garment dyed treatment", "워시 & 가먼트 다이드 트리트먼트"),
        ("Garment-dyed and washed treatment", "가먼트 다이드 & 워시드 트리트먼트"),
        ("Flapped patch pockets on the chest", "가슴 플랩 패치 포켓"),
        ("Flap patch pockets with button on chest", "가슴 버튼 플랩 패치 포켓"),
        ("Low welt pockets on the front", "앞면 로우 웰트 포켓"),
        ("Welt side pockets", "사이드 웰트 포켓"),
        ("Straight hem adjustable with buttons", "버튼 조절 스트레이트 밑단"),
        ("Straight hem with side slits", "사이드 슬릿 스트레이트 밑단"),
        ("Straight elasticized hem", "스트레이트 엘라스틱 밑단"),
        ("Button-down collar", "버튼다운 칼라"),
        ("Boxy Fit", "박시 핏"),
        ("Boxy fit", "박시 핏"),
        ("Ribbed knit hem and cuffs", "리브드 니트 밑단 & 커프"),
        ("Do not iron latex parts", "라텍스 부분 다림질 금지"),
        ("The model is", "모델 키"),
        ("and wears a size", "착용 사이즈"),
        ("Center-back length", "등 길이"),
        ("Total length", "총장"),
        ("Hem width", "밑단 폭"),
        ("Blouson jacket", "블루종 재킷"),
        ("Caban jacket", "카반 재킷"),
        ("Re-Nylon blouson jacket", "Re-Nylon 블루종 재킷"),
        ("Re-Nylon hooded blouson jacket", "Re-Nylon 후드 블루종 재킷"),
        ("Re-Nylon bomber jacket", "Re-Nylon 봄ber 재킷"),
        ("Nappa leather", "나파 가죽"),
        ("Shearling collar", "시어링 칼라"),
        ("Stand-up collar", "스탠드 칼라"),
        ("Mock turtleneck", "모크 터틀넥"),
        ("Mother-of-pearl button", "자개 버튼"),
        ("Mother-of-pearl buttons", "자개 버튼"),
        ("French cuff for cufflinks", "커프링크스용 프렌치 커프"),
        ("Gallery", "갤러리"),
        ("Product detail.", "제품 디테일."),
    ],
    key=lambda kv: -len(kv[0]),
)


def apply_phrases(text: str) -> str:
    out = text or ""
    for en, ko in PHRASE_KO:
        if en in out:
            out = out.replace(en, ko)
    return out


def mens_rtw_text_ko(text: str) -> str | None:
    s = (text or "").strip()
    if not s:
        return None
    if s in TITLE_KO:
        return TITLE_KO[s]
    if s in DESCRIPTION_KO:
        return DESCRIPTION_KO[s]
    if s in DETAIL_KO:
        return DETAIL_KO[s]
    mapped = apply_phrases(s)
    if mapped != s and len(mapped) >= len(s) * 0.5:
        return mapped
    return None


def seed_mens_rtw_cache(cache: dict[str, str]) -> int:
    n = 0
    for mapping in (TITLE_KO, DESCRIPTION_KO, DETAIL_KO):
        for en, ko in mapping.items():
            if not en or not ko:
                continue
            if en not in cache or cache.get(en) != ko:
                cache[en] = ko
                n += 1
    return n
