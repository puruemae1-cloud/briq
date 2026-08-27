#!/usr/bin/env python3
"""Build Briq Prada women's handbags catalog from scrape raw.

Pricing matches Chanel/Gucci luxury bags:
  KRW = round_만원(GBP × 2100 × 1.05 × 1.15)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from pr_size_charts import (  # noqa: E402
    size_chart_for_mens_rtw_variants,
    size_chart_for_shoes,
    size_chart_for_variants,
)
from pr_sizes import assert_no_mixed_rtw_sizes  # noqa: E402
from pr_shoe_ko import seed_shoe_cache, shoe_text_ko  # noqa: E402
from pr_slg_ko import seed_slg_cache, slg_text_ko  # noqa: E402
from pr_travel_ko import seed_travel_cache, travel_text_ko  # noqa: E402
from pr_mens_handbags_ko import (  # noqa: E402
    mens_handbag_text_ko,
    seed_mens_handbags_cache,
)
from pr_mens_rtw_ko import mens_rtw_text_ko, seed_mens_rtw_cache  # noqa: E402
from pr_accessories_ko import seed_accessories_cache, accessories_text_ko  # noqa: E402
from pr_linea_rossa_ko import seed_linea_rossa_cache, linea_rossa_text_ko  # noqa: E402
from pr_beauty_ko import seed_beauty_cache, beauty_text_ko  # noqa: E402
from pr_fragrances_ko import seed_fragrances_cache, fragrances_text_ko  # noqa: E402
from pr_fine_jewelry_ko import seed_fine_jewelry_cache, fine_jewelry_text_ko  # noqa: E402
from pr_common_ko import apply_phrases as common_phrases  # noqa: E402

# Reject cached / returned copy above this Latin-letter ratio (hybrid EN/KO guard).
_MAX_KO_EN_RATIO = 0.30
RAW_BAGS = ROOT / "src/data/pr/pr-handbags-catalog-raw.json"
RAW_MEN_BAGS = ROOT / "src/data/pr/pr-mens-handbags-catalog-raw.json"
RAW_RTW = ROOT / "src/data/pr/pr-womens-rtw-catalog-raw.json"
RAW_MENS_RTW = ROOT / "src/data/pr/pr-mens-rtw-catalog-raw.json"
RAW_SHOES = ROOT / "src/data/pr/pr-womens-shoes-catalog-raw.json"
RAW_MENS_SHOES = ROOT / "src/data/pr/pr-mens-shoes-catalog-raw.json"
RAW_SLG = ROOT / "src/data/pr/pr-womens-slg-catalog-raw.json"
RAW_MEN_SLG = ROOT / "src/data/pr/pr-mens-slg-catalog-raw.json"
RAW_TRAVEL = ROOT / "src/data/pr/pr-womens-travel-catalog-raw.json"
RAW_MEN_TRAVEL = ROOT / "src/data/pr/pr-mens-travel-catalog-raw.json"
RAW_ACC = ROOT / "src/data/pr/pr-womens-accessories-catalog-raw.json"
RAW_MEN_ACC = ROOT / "src/data/pr/pr-mens-accessories-catalog-raw.json"
RAW_LINEA = ROOT / "src/data/pr/pr-linea-rossa-catalog-raw.json"
RAW_BEAUTY = ROOT / "src/data/pr/pr-beauty-catalog-raw.json"
RAW_FRAGRANCES = ROOT / "src/data/pr/pr-fragrances-catalog-raw.json"
RAW_FINE_JEWELRY = ROOT / "src/data/pr/pr-fine-jewelry-catalog-raw.json"
OUT_JSON = ROOT / "src/data/pr/pr-catalog.json"
OUT_TS = ROOT / "src/data/pr/pr-catalog.ts"
CACHE_PATH = ROOT / "src/data/pr/pr-translate-cache.json"

HANDBAG_LEAF_COLLECTIONS = [
    "pr-women-shoulder-bags",
    "pr-women-top-handle-bags",
    "pr-women-tote-bags",
    "pr-women-mini-bags",
    "pr-women-backpacks",
    "pr-women-briefcases",
]
BAG_PARENT_COLS = ["prada", "prada-bags", "pr-handbags"]
MEN_HANDBAG_LEAF_COLLECTIONS = [
    "pr-men-backpacks-belt-bags",
    "pr-men-briefcases",
    "pr-men-clutches",
    "pr-men-messenger-bags",
    "pr-men-tote-bags",
]
MEN_BAG_PARENT_COLS = ["prada", "prada-bags", "pr-mens-handbags"]
ALL_HANDBAG_LEAF_COLLECTIONS = [
    *HANDBAG_LEAF_COLLECTIONS,
    *MEN_HANDBAG_LEAF_COLLECTIONS,
]

RTW_LEAF_COLLECTIONS = [
    "pr-women-knitwear",
    "pr-women-shirts-tops",
    "pr-women-tshirts-sweatshirts",
    "pr-women-dresses",
    "pr-women-skirts",
    "pr-women-trousers-shorts",
    "pr-women-denim",
    "pr-women-jackets-coats",
    "pr-women-outerwear",
    "pr-women-leather",
    "pr-women-swimwear",
    "pr-women-pajamas-underwear",
]
RTW_PARENT_COLS = ["prada", "prada-luxury", "pr-women", "pr-women-rtw"]

MENS_RTW_LEAF_COLLECTIONS = [
    "pr-men-denim",
    "pr-men-jackets-coats",
    "pr-men-jogging-suits-sweatshirts",
    "pr-men-knitwear",
    "pr-men-leather",
    "pr-men-outerwear",
    "pr-men-pajamas-underwear",
    "pr-men-shirts",
    "pr-men-suits",
    "pr-men-swimwear",
    "pr-men-trousers-bermudas",
    "pr-men-tshirts-polos",
]
MENS_RTW_PARENT_COLS = ["prada", "prada-luxury", "pr-men", "pr-men-rtw"]

SHOES_LEAF_COLLECTIONS = [
    "pr-women-ankle-boots-boots",
    "pr-women-loafers-lace-ups",
    "pr-women-pumps-ballerinas",
    "pr-women-sneakers",
    "pr-women-sandals-mules",
    "pr-women-new-formal",
    "pr-women-chocolate",
]
SHOES_PARENT_COLS = ["prada", "prada-shoes", "pr-women-shoes"]
MENS_SHOES_LEAF_COLLECTIONS = [
    "pr-men-loafers",
    "pr-men-sneakers",
    "pr-men-sandals",
    "pr-men-lace-ups",
    "pr-men-boots",
    "pr-men-americas-cup",
]
MENS_SHOES_PARENT_COLS = ["prada", "prada-shoes", "pr-men-shoes"]
ALL_SHOES_LEAF_COLLECTIONS = [
    *SHOES_LEAF_COLLECTIONS,
    *MENS_SHOES_LEAF_COLLECTIONS,
]

SLG_LEAF_COLLECTIONS = [
    "pr-women-card-holders",
    "pr-women-small-wallets",
    "pr-women-large-wallets",
    "pr-women-wallets-on-chain",
    "pr-women-high-tech-accessories",
]
SLG_PARENT_COLS = ["prada", "prada-accessories", "pr-women-accessories", "pr-women-slg"]
MEN_SLG_LEAF_COLLECTIONS = [
    "pr-men-card-holders",
    "pr-men-small-wallets",
    "pr-men-large-wallets",
    "pr-men-high-tech-accessories",
]
MEN_SLG_PARENT_COLS = [
    "prada",
    "prada-accessories",
    "pr-mens-accessories",
    "pr-mens-slg",
]
ALL_SLG_LEAF_COLLECTIONS = [*SLG_LEAF_COLLECTIONS, *MEN_SLG_LEAF_COLLECTIONS]
ALL_SLG_PARENT_COLS = sorted(set([*SLG_PARENT_COLS, *MEN_SLG_PARENT_COLS]))
ACCESSORIES_PARENT_COLS = ["prada", "prada-accessories", "pr-women-accessories"]
ACCESSORIES_LEAF_COLLECTIONS = [
    "pr-women-sunglasses",
    "pr-women-silks-scarves",
    "pr-women-hats-gloves",
    "pr-women-headbands-hair",
    "pr-women-bag-charms",
    "pr-women-jewels",
    "pr-women-belts",
    "pr-women-pouches",
]
MEN_ACCESSORIES_LEAF_COLLECTIONS = [
    "pr-men-sunglasses",
    "pr-men-hats-gloves",
    "pr-men-bag-charms",
    "pr-men-belts",
    "pr-men-custom-belts",
    "pr-men-silks-scarves",
    "pr-men-ties-bow-ties",
    "pr-men-jewels",
]
MEN_ACCESSORIES_PARENT_COLS = [
    "prada",
    "prada-accessories",
    "pr-mens-accessories",
]
ALL_ACCESSORIES_LEAF_COLLECTIONS = [
    *ACCESSORIES_LEAF_COLLECTIONS,
    *MEN_ACCESSORIES_LEAF_COLLECTIONS,
]
ALL_ACCESSORIES_PARENT_COLS = sorted(
    set([*ACCESSORIES_PARENT_COLS, *MEN_ACCESSORIES_PARENT_COLS])
)

LINEA_ROSSA_LEAF_COLLECTIONS = [
    "pr-linea-rossa-women",
    "pr-linea-rossa-men",
    "pr-linea-rossa-sunglasses",
    "pr-linea-rossa-shoes",
    "pr-linea-rossa-fragrances",
]
LINEA_ROSSA_PARENT_COLS = ["prada", "prada-accessories", "pr-linea-rossa"]
BEAUTY_LEAF_COLLECTIONS = [
    "pr-beauty-face",
    "pr-beauty-eyes",
    "pr-beauty-lips",
    "pr-beauty-skincare",
    "pr-beauty-brushes",
]
BEAUTY_PARENT_COLS = ["prada", "prada-accessories", "pr-beauty"]
FRAGRANCE_LEAF_COLLECTIONS = [
    "pr-fragrances-women",
    "pr-fragrances-men",
    "pr-fragrances-exclusive",
]
FRAGRANCE_PARENT_COLS = ["prada", "prada-accessories", "pr-fragrances"]
FINE_JEWELRY_LEAF_COLLECTIONS = [
    "pr-fine-jewelry-bracelets",
    "pr-fine-jewelry-necklaces",
    "pr-fine-jewelry-rings",
    "pr-fine-jewelry-earrings-brooches",
]
FINE_JEWELRY_PARENT_COLS = ["prada", "prada-accessories", "pr-fine-jewelry"]

TRAVEL_LEAF_COLLECTIONS = [
    "pr-women-travel-bags",
    "pr-women-luggage-carry-on",
    "pr-women-travel-accessories",
]
TRAVEL_PARENT_COLS = ["prada", "prada-bags", "pr-women-travel"]
MEN_TRAVEL_LEAF_COLLECTIONS = [
    "pr-men-travel-bags",
    "pr-men-luggage-carry-on",
    "pr-men-travel-accessories",
]
MEN_TRAVEL_PARENT_COLS = ["prada", "prada-bags", "pr-mens-handbags", "pr-men-travel"]
ALL_TRAVEL_LEAF_COLLECTIONS = [*TRAVEL_LEAF_COLLECTIONS, *MEN_TRAVEL_LEAF_COLLECTIONS]
ALL_TRAVEL_PARENT_COLS = sorted(set([*TRAVEL_PARENT_COLS, *MEN_TRAVEL_PARENT_COLS]))

# Title / material glossary — natural Korean for Prada
_GLOSSARY = {
    "Shoulder bag": "숄더백",
    "Shoulder bags": "숄더백",
    "Top handle": "탑 핸들",
    "Top handles": "탑 핸들백",
    "Tote": "토트백",
    "Totes": "토트백",
    "Mini bag": "미니백",
    "Mini-bag": "미니백",
    "Mini bags": "미니백",
    "Backpack": "백팩",
    "Backpacks": "백팩",
    "Briefcase": "브리프케이스",
    "Briefcases": "브리프케이스",
    "Handbag": "핸드백",
    "Knitwear": "니트웨어",
    "Dress": "드레스",
    "Dresses": "드레스",
    "Skirt": "스커트",
    "Skirts": "스커트",
    "Trousers": "팬츠",
    "Shorts": "쇼츠",
    "Jacket": "재킷",
    "Coat": "코트",
    "Outerwear": "아우터",
    "Denim": "데님",
    "Swimwear": "스윔웨어",
    "Loafers": "로퍼",
    "Loafer": "로퍼",
    "Lace-ups": "레이스업",
    "Lace-up": "레이스업",
    "America's Cup": "아메리카스 컵",
    "Sneakers": "스니커즈",
    "Sneaker": "스니커즈",
    "Pumps": "펌프스",
    "Pump": "펌프스",
    "Sandals": "샌들",
    "Sandal": "샌들",
    "Boots": "부츠",
    "Boot": "부츠",
    "Booties": "부티",
    "Bootie": "부티",
    "Mules": "뮬",
    "Mule": "뮬",
    "Ballerinas": "발레리나",
    "Ballerina": "발레리나",
    "Wallet": "월렛",
    "Wallets": "월렛",
    "Card holder": "카드홀더",
    "Pouch": "파우치",
    "Smartphone": "스마트폰",
    "Rosy Blush": "로지 블러시",
    "Dark Brown": "다크 브라운",
    "Dark Grey": "다크 그레이",
    "Peony Pink": "피오니 핑크",
    "Chalk White": "초크 화이트",
    "Pale Blue": "페일 블루",
    "Sand Beige": "샌드 베이지",
    "Chestnut Brown": "체스트넛 브라운",
    "Forest": "포레스트",
    "Caramel": "카라멜",
    "Alabaster": "알라바스터",
    "Slingback pumps": "슬링백 펌프스",
    "Slingback": "슬링백",
    "Platform sandals": "플랫폼 샌들",
    "Platform": "플랫폼",
    "nubuck leather": "누벅 가죽",
    "nubuck": "누벅",
    "Nubuck": "누벅",
    "brushed leather": "브러시드 가죽",
    "Brushed leather": "브러시드 가죽",
    "antiqued leather": "앤틱 가죽",
    "Antiqued leather": "앤틱 가죽",
    "nappa leather": "나파 가죽",
    "Nappa leather": "나파 가죽",
    "mesh fabric": "메쉬 패브릭",
    "Mesh fabric": "메쉬 패브릭",
    "technical mesh": "테크니컬 메쉬",
    "shearling": "시어링",
    "Shearling": "시어링",
    "satin": "새틴",
    "Satin": "새틴",
    "crochet": "크로셰",
    "Crochet": "크로셰",
    "fabric": "패브릭",
    "Fabric": "패브릭",
    "rubber sole": "러버 솔",
    "leather sole": "레더 솔",
    "leather lining": "가죽 안감",
    "fabric lining": "패브릭 안감",
    "shearling lining": "시어링 안감",
    "hot-stamped logo": "핫스탬프 로고",
    "screen-printed logo": "스크린 프린트 로고",
    "enameled metal triangle logo": "에나멜 메탈 트라이앵글 로고",
    "Enameled metal triangle logo": "에나멜 메탈 트라이앵글 로고",
    "metal lettering logo": "메탈 레터링 로고",
    "logo-engraved": "로고 각인",
    "Monoblock rubber sole": "모노블록 러버 솔",
    "monoblock rubber sole": "모노블록 러버 솔",
    "Removable leather-covered insole": "탈착식 가죽 커버 인솔",
    "leather-covered heel": "가죽 커버 힐",
    "Leather-covered heel": "가죽 커버 힐",
    "Cotton laces": "코튼 레이스",
    "cotton laces": "코튼 레이스",
    "Lug tread": "러그 트레드",
    "Open-side": "오픈 사이드",
    "Feather-embellished": "페더 장식",
    "Embroidered": "자수",
    "Vintage-effect": "빈티지 이펙트",
    "lined": "안감",
    "Upper with": "갑피:",
    "Structure": "구조",
    "Composition": "소재 구성",
    "Care": "케어",
    "Made in Italy": "메이드 인 이탈리아",
    "heel height": "굽 높이",
    "height": "높이",
    "mm": "mm",
    "Shirt": "셔츠",
    "T-shirt": "티셔츠",
    "Sweatshirt": "스웻셔츠",
    "Saffiano leather": "사피아노 가죽",
    "Saffiano": "사피아노",
    "Re-Nylon": "Re-Nylon",
    "leather": "가죽",
    "Leather": "가죽",
    "suede": "스웨이드",
    "Suede": "스웨이드",
    "nylon": "나일론",
    "Nylon": "나일론",
    "cotton canvas": "코튼 캔버스",
    "cotton jersey": "코튼 저지",
    "jersey": "저지",
    "canvas": "캔버스",
    "triangle logo": "트라이앵글 로고",
    "metal hardware": "메탈 하드웨어",
    "zip closure": "지퍼 클로저",
    "Zipper closure": "지퍼 클로저",
    "detachable": "탈부착",
    "adjustable": "길이 조절",
    "shoulder strap": "숄더 스트랩",
    "One Size": "원 사이즈",
    "Black": "블랙",
    "White": "화이트",
    "Beige": "베이지",
    "Brown": "브라운",
    "Navy": "네이비",
    "Forest": "포레스트",
    "Ivory": "아이보리",
    "Silver": "실버",
    "Gold": "골드",
    "Pink": "핑크",
    "Red": "레드",
    "Blue": "블루",
    "Green": "그린",
    "Grey": "그레이",
    "Gray": "그레이",
    "Camel": "카멜",
}


def gbp_to_krw(gbp: float | None) -> int:
    if gbp is None:
        return 0
    base = float(gbp) * 2100 * 1.05 * 1.15
    return int(round(base / 10_000) * 10_000)


_KO: dict[str, str] = {}
if CACHE_PATH.exists():
    _KO = json.loads(CACHE_PATH.read_text())


def en_ratio(s: str) -> float:
    """Latin-letter ratio; whitelisted brand/tech tokens are ignored."""
    cleaned = s or ""
    # Strip model codes BEFORE single-letter tokens (L/M/S) mangle "LR-…".
    cleaned = re.sub(r"LR[\s–\-]*[A-Z]{1,3}\s*\d{2,4}(?:-MK\d)?", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\bF\d{2}\b", "", cleaned)
    # Beauty shade / refill codes (DC70, O103, U001, B03, DC7, etc.)
    cleaned = re.sub(r"\b[A-Z]{1,3}\d{1,4}\b", "", cleaned)
    for tok in (
        "Re-Nylon",
        "Re-Edition",
        "Linea Rossa",
        "Luna Rossa",
        "Homme",
        "Intense",
        "Miracles",
        "Amber",
        "Candy",
        "L'Homme",
        "Vanille",
        "Infusion",
        "Extreme-Tex",
        "America's Cup",
        "America’s Cup",
        "Light Bi-Stretch",
        "Bi-Stretch",
        "Tech Rec",
        "Tec Rec",
        "GORE-TEX",
        "Graphene",
        "Cordura",
        "Lycra",
        "Komatsu Matere",
        "Ustamock",
        "Woolmark Company",
        "Woolmark",
        "Faction",
        "Le Parfum",
        "Original",
        "Active",
        "Soft",
        "Carbon",
        "Ocean",
        "Sport",
        "Toblach",
        "Reveal",
        "Monochrome",
        "Dimensions",
        "Pradascope",
        "그램",
        "gram",
        "Extending Primer",
        "cream-to-powder",
        "Light Glowing",
        "Blurring",
        "Setting Powder",
        "Rebalancing",
        "Mesh Cushion",
        "Holo Nude",
        "Wisteria Gleams",
        "Frosting Care",
        "Optimizing Care",
        "Pradalines",
        "Reflection",
        "LHA",
        "PHA",
        "BHA",
        "AHA",
        "Micro-Peel",
        "Adapto.gn",
        "Augmented Skin",
        "Paradoxe",
        "Glowing",
        "Soft Matte",
        "Hyper Matte",
        "Blushing Care",
        "Micro-Pixel",
        "NEUTRI",
        "MAHOGANY",
        "PORTRAIT",
        "ASTRAL PINK",
        "SPICE MAHOGANY",
        "BRICK MAHOGANY",
        "Hyper Matte",
        "Soft Matte",
        "MIPS",
        "RECCO",
        "Twiceme",
        "PVC",
        "F.18",
        "Gauge",
        "EDP",
        "EDT",
        "Prada",
        "Saffiano",
        "Galleria",
        "Brique",
        "Explore",
        "Bonnie",
        "Jardinière",
        "Jardiniere",
        "Speedrock",
        "nappa",
        "Nappa",
        "Symbole",
        "Shadowplay",
        "Oakley",
        "Prizm",
        "Switchlock",
        "Eyewear Collection",
        "Runway",
        "Single Layer",
        "Nylon",
        "UVA",
        "UVB",
        "TSA",
        "EVA",
        "TPU",
        "mm",
        "cm",
        "ml",
        "GB",
        "L",
        "M",
        "S",
        "OS",
        "TU",
    ):
        cleaned = re.sub(re.escape(tok), "", cleaned, flags=re.I)
    letters = [c for c in cleaned if c.isalpha()]
    if not letters:
        return 0.0
    latin = sum(1 for c in letters if ("A" <= c <= "Z") or ("a" <= c <= "z"))
    return latin / len(letters)


def gtx(text: str) -> str:
    """Translate EN→KO. Prefer Google gtx; fall back to MyMemory on 429/errors."""

    def _gtx_once(chunk: str) -> str:
        q = urllib.parse.quote(chunk[:4500])
        url = (
            "https://translate.googleapis.com/translate_a/single"
            f"?client=gtx&sl=en&tl=ko&dt=t&q={q}"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=35) as r:
            data = json.loads(r.read().decode())
        return "".join(part[0] for part in data[0] if part and part[0])

    def _mymemory_once(chunk: str) -> str:
        # Free tier ~500 chars
        url2 = (
            "https://api.mymemory.translated.net/get"
            f"?q={urllib.parse.quote(chunk[:480])}&langpair=en|ko"
        )
        req2 = urllib.request.Request(url2, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req2, timeout=35) as r:
            data = json.loads(r.read().decode())
        return (data.get("responseData") or {}).get("translatedText") or ""

    def _one(chunk: str) -> str:
        try:
            out = _gtx_once(chunk)
            if out.strip() and en_ratio(out) < 0.70:
                return out
        except Exception:
            pass
        out = _mymemory_once(chunk)
        if out and en_ratio(out) < 0.70:
            return out
        raise RuntimeError("translate-failed")

    text = (text or "").strip()
    if not text:
        return ""
    if len(text) <= 480:
        return _one(text)
    # Split long copy on sentence boundaries for MyMemory limits
    parts = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    buf = ""
    for p in parts:
        if len(buf) + len(p) + 1 <= 480:
            buf = f"{buf} {p}".strip()
        else:
            if buf:
                chunks.append(buf)
            buf = p
    if buf:
        chunks.append(buf)
    outs = []
    for c in chunks:
        outs.append(_one(c))
        time.sleep(0.08)
    return " ".join(outs)

def pretranslate_unique(strings: list[str]) -> None:
    """Warm the cache for a set of English strings (deduped)."""
    uniq = []
    seen: set[str] = set()
    for s in strings:
        s = re.sub(r"\s+", " ", (s or "").strip())
        if not s or s in seen:
            continue
        seen.add(s)
        if s in _KO and en_ratio(_KO[s]) < _MAX_KO_EN_RATIO:
            continue
        if s in _GLOSSARY or en_ratio(s) < 0.35:
            continue
        uniq.append(s)
    print(f"pretranslate {len(uniq)} unique strings…", flush=True)
    for i, s in enumerate(uniq, start=1):
        try:
            ko = t(s)
            if ko and en_ratio(ko) < _MAX_KO_EN_RATIO:
                _KO[s] = ko
        except Exception as e:
            print(f"  skip {i}: {e}", flush=True)
        if i % 20 == 0:
            CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2))
            print(f"  cached {i}/{len(uniq)}", flush=True)
        time.sleep(0.12)
    CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2))


def apply_glossary(s: str) -> str:
    out = s
    # longer phrases first
    for en, ko in sorted(_GLOSSARY.items(), key=lambda kv: -len(kv[0])):
        out = re.sub(re.escape(en), ko, out, flags=re.I)
    # Prada brand keep as 프라다 when standalone product naming
    out = re.sub(r"\bPrada\b", "프라다", out)
    out = re.sub(r"\s{2,}", " ", out).strip()
    return out


_FORCE_TRANSLATE = False
_OFFLINE_TRANSLATE = False


def _phrase_fallback(s: str) -> str:
    from pr_mens_rtw_ko import apply_phrases as mens_rtw_phrases
    from pr_shoe_ko import apply_phrases as shoe_phrases
    from pr_slg_ko import apply_phrases as slg_phrases
    from pr_travel_ko import apply_phrases as travel_phrases
    from pr_accessories_ko import apply_phrases as acc_phrases
    from pr_linea_rossa_ko import apply_phrases as linea_phrases
    from pr_beauty_ko import apply_phrases as beauty_phrases
    from pr_fragrances_ko import apply_phrases as fragrance_phrases
    from pr_fine_jewelry_ko import apply_phrases as fine_jewelry_phrases

    out = common_phrases(
        mens_rtw_phrases(
            slg_phrases(
                shoe_phrases(
                    travel_phrases(
                        linea_phrases(
                            fine_jewelry_phrases(
                                beauty_phrases(fragrance_phrases(acc_phrases(s)))
                            )
                        )
                    )
                )
            )
        )
    )
    return apply_glossary(out)


def _collect_row_strings(rows: list[dict]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in ("officialNameEn", "title", "color", "material", "description"):
            val = row.get(key)
            if val and str(val).strip():
                s = re.sub(r"\s+", " ", str(val).strip())
                if s not in seen:
                    seen.add(s)
                    out.append(s)
        for key in ("details", "materialsCare"):
            for item in row.get(key) or []:
                s = re.sub(r"\s+", " ", str(item).strip())
                if s and s not in seen:
                    seen.add(s)
                    out.append(s)
    return out


def purge_weak_cache(threshold: float = _MAX_KO_EN_RATIO) -> int:
    dropped = 0
    for k in list(_KO.keys()):
        if en_ratio(str(_KO[k])) >= threshold:
            _KO.pop(k, None)
            dropped += 1
    return dropped


def validate_prada_korean(products: list[dict], scope: str = "all") -> None:
    """Fail the build if Prada PDP body copy still looks like hybrid EN/KO."""
    bad: list[tuple[str, str, float]] = []
    for p in products:
        if p.get("brand") != "프라다":
            continue
        cols = p.get("prCollections") or []
        tags = p.get("tags") or []
        if scope == "travel" and "pr-women-travel" not in cols and "pr-men-travel" not in cols:
            continue
        if scope == "mens-travel" and not (
            "travel" in tags
            and (
                "남성" in tags
                or "pr-men-travel" in cols
                or any(c in MEN_TRAVEL_LEAF_COLLECTIONS for c in cols)
            )
        ):
            continue
        if scope == "acc" and "acc" not in tags:
            continue
        if scope == "mens-acc" and not (
            "acc" in tags
            and (
                "남성" in tags
                or "pr-mens-accessories" in cols
                or any(c in MEN_ACCESSORIES_LEAF_COLLECTIONS for c in cols)
            )
        ):
            continue
        if scope == "linea-rossa" and not (
            "linea-rossa" in tags
            or "pr-linea-rossa" in cols
            or any(c in LINEA_ROSSA_LEAF_COLLECTIONS for c in cols)
        ):
            continue
        if scope == "beauty" and not (
            "beauty" in tags
            or "pr-beauty" in cols
            or any(c in BEAUTY_LEAF_COLLECTIONS for c in cols)
        ):
            continue
        if scope == "fragrances" and not (
            "fragrances" in tags
            or "pr-fragrances" in cols
            or any(c in FRAGRANCE_LEAF_COLLECTIONS for c in cols)
        ):
            continue
        if scope == "fine-jewelry" and not (
            "fine-jewelry" in tags
            or "pr-fine-jewelry" in cols
            or any(c in FINE_JEWELRY_LEAF_COLLECTIONS for c in cols)
        ):
            continue
        if scope == "slg" and "slg" not in tags:
            continue
        if scope == "mens-slg" and not (
            "slg" in tags and ("남성" in tags or "pr-mens-slg" in cols or any(c in MEN_SLG_LEAF_COLLECTIONS for c in cols))
        ):
            continue
        if scope == "shoes" and not (
            p.get("category") == "shoes"
            and (
                "pr-women-shoes" in cols
                or any(c in SHOES_LEAF_COLLECTIONS for c in cols)
            )
        ):
            continue
        if scope == "mens-shoes" and not (
            p.get("category") == "shoes"
            and (
                "pr-men-shoes" in cols
                or any(c in MENS_SHOES_LEAF_COLLECTIONS for c in cols)
            )
        ):
            continue
        if scope == "bags" and p.get("category") != "bags":
            continue
        if scope == "mens-bags" and not (
            "pr-mens-handbags" in cols
            or any(c in MEN_HANDBAG_LEAF_COLLECTIONS for c in cols)
        ):
            continue
        if scope == "rtw" and not (
            p.get("category") == "luxury"
            and (
                "pr-women-rtw" in cols
                or "pr-women" in cols
                or any(c in RTW_LEAF_COLLECTIONS for c in cols)
            )
        ):
            continue
        if scope == "mens-rtw" and not (
            p.get("category") == "luxury"
            and (
                "pr-men-rtw" in cols
                or "pr-men" in cols
                or any(c in MENS_RTW_LEAF_COLLECTIONS for c in cols)
            )
        ):
            continue
        pid = str(p.get("id") or "")
        val = str(p.get("descriptionKo") or "").strip()
        if val and en_ratio(val) > _MAX_KO_EN_RATIO:
            bad.append((pid, "descriptionKo", en_ratio(val)))
        for i, sec in enumerate(p.get("storySections") or []):
            # Gallery captions often embed Latin product-line names (Toblach, etc.).
            if str(sec.get("titleKo") or "").strip() == "갤러리":
                continue
            body = str(sec.get("bodyKo") or "").strip()
            if body and en_ratio(body) > _MAX_KO_EN_RATIO:
                bad.append((pid, f"story[{i}].bodyKo", en_ratio(body)))
    if bad:
        bad.sort(key=lambda x: -x[2])
        print("Prada Korean QA failed — hybrid English detected:", flush=True)
        for pid, field, ratio in bad[:12]:
            print(f"  {pid} {field} en_ratio={ratio:.2f}", flush=True)
        raise SystemExit(
            f"Prada Korean QA failed ({len(bad)} fields). "
            "Add curated copy or fix translate pipeline."
        )


def validate_prada_rtw_sizes(products: list[dict], scope: str = "all") -> None:
    """Fail if RTW products mix letter (S/M/L) and numeric (48/48S) size options."""
    if scope not in {"all", "rtw", "mens-rtw"}:
        return
    rtw: list[dict] = []
    for p in products:
        if p.get("brand") != "프라다" or p.get("category") != "luxury":
            continue
        cols = p.get("prCollections") or []
        is_women = (
            "pr-women-rtw" in cols
            or "pr-women" in cols
            or any(c in RTW_LEAF_COLLECTIONS for c in cols)
        )
        is_men = (
            "pr-men-rtw" in cols
            or "pr-men" in cols
            or any(c in MENS_RTW_LEAF_COLLECTIONS for c in cols)
        )
        if scope == "rtw" and not is_women:
            continue
        if scope == "mens-rtw" and not is_men:
            continue
        if scope == "all" and not (is_women or is_men):
            continue
        rtw.append(p)
    assert_no_mixed_rtw_sizes(rtw, context=f"Prada catalog build ({scope})")


def t(text: str | None) -> str:
    s = re.sub(r"\s+", " ", (text or "").strip())
    if not s:
        return ""
    # Prefer SLG curated maps before shoe heuristics (shoe_text_ko treats any
    # short string containing "logo"/"lining" as a shoe detail).
    # Only accept curated / phrase hits that pass hybrid-English QA.
    for curated_fn in (
        fine_jewelry_text_ko,
        beauty_text_ko,
        fragrances_text_ko,
        linea_rossa_text_ko,
        slg_text_ko,
        travel_text_ko,
        mens_handbag_text_ko,
        mens_rtw_text_ko,
        accessories_text_ko,
        shoe_text_ko,
    ):
        curated = curated_fn(s)
        if curated is not None and en_ratio(curated) < _MAX_KO_EN_RATIO:
            _KO[s] = curated
            return curated
    # Reuse good cache hits only (never keep hybrid EN/KO).
    if s in _KO and en_ratio(_KO[s]) < _MAX_KO_EN_RATIO:
        return apply_glossary(_KO[s])
    # Drop stale hybrid cache so gtx / phrase fallback can replace it.
    if s in _KO and en_ratio(_KO[s]) >= _MAX_KO_EN_RATIO:
        _KO.pop(s, None)
    # short glossary hit (exact title phrase)
    if s in _GLOSSARY:
        return _GLOSSARY[s]
    if en_ratio(s) < 0.35 or len(s) < 3:
        return apply_glossary(s)
    if not _OFFLINE_TRANSLATE:
        for attempt in range(5):
            try:
                ko = gtx(s).strip()
                if ko and en_ratio(ko) < 0.45:
                    ko = apply_glossary(ko)
                    if en_ratio(ko) < _MAX_KO_EN_RATIO:
                        _KO[s] = ko
                        time.sleep(0.05)
                        return ko
                time.sleep(0.15 * (attempt + 1))
            except Exception:
                time.sleep(0.2 * (attempt + 1))
    ko = _phrase_fallback(s)
    if en_ratio(ko) < _MAX_KO_EN_RATIO:
        _KO[s] = ko
        return ko
    print(f"WARN untranslated ({en_ratio(ko):.2f}): {s[:96]}…", flush=True)
    return ko


def merge_prada_product_fields(dst: dict, src: dict) -> None:
    """Union collections/tags when the same SKU appears in multiple Prada segments."""
    dst["prCollections"] = sorted(
        set(dst.get("prCollections") or []) | set(src.get("prCollections") or [])
    )
    dst["tags"] = sorted(set(dst.get("tags") or []) | set(src.get("tags") or []))
    # Prefer a leaf subcategory when the destination was a gender/parent hub.
    src_leaf = str(src.get("subcategory") or "")
    dst_leaf = str(dst.get("subcategory") or "")
    leaf_ids = (
        set(ALL_TRAVEL_LEAF_COLLECTIONS)
        | set(ALL_SLG_LEAF_COLLECTIONS)
        | set(LINEA_ROSSA_LEAF_COLLECTIONS)
        | set(BEAUTY_LEAF_COLLECTIONS)
        | set(FRAGRANCE_LEAF_COLLECTIONS)
        | set(FINE_JEWELRY_LEAF_COLLECTIONS)
    )
    if src_leaf in leaf_ids and dst_leaf not in leaf_ids:
        dst["subcategory"] = src_leaf
    # Normalize legacy gallery captions that embed Latin product-line names.
    for sec in dst.get("storySections") or []:
        if str(sec.get("titleKo") or "").strip() == "갤러리":
            sec["bodyKo"] = "제품 디테일."


def dedupe_merge_products(products: list[dict]) -> list[dict]:
    by_id: dict[str, dict] = {}
    order: list[str] = []
    for p in products:
        pid = str(p.get("id") or "")
        if not pid:
            continue
        if pid not in by_id:
            by_id[pid] = p
            order.append(pid)
        else:
            merge_prada_product_fields(by_id[pid], p)
    return [by_id[i] for i in order]


def accent_for(key: str) -> str:
    h = hashlib.md5((key or "x").encode()).hexdigest()
    r = 40 + int(h[0:2], 16) % 80
    g = 40 + int(h[2:4], 16) % 80
    b = 40 + int(h[4:6], 16) % 80
    return f"#{r:02x}{g:02x}{b:02x}"


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:70] or "item"


def dims_ko(dims: dict | None) -> str:
    if not dims:
        return ""
    parts = []
    for key, label in (
        ("height", "높이"),
        ("width", "가로"),
        ("length", "세로"),
        ("depth", "깊이"),
    ):
        v = dims.get(key)
        if v:
            parts.append(f"{label} {v}")
    return " · ".join(parts)


def build_handbag_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    code = row.get("productCode") or row.get("id") or row.get("sku")
    if not code:
        return None
    gbp = row.get("gbpPrice")
    if gbp is None:
        return None
    price = gbp_to_krw(float(gbp))
    if price <= 0:
        return None

    mens = (
        (row.get("_kind") or row.get("kind") or "") in {"mens-handbag", "mens-handbags"}
        or any(
            c in MEN_HANDBAG_LEAF_COLLECTIONS or c == "pr-mens-handbags"
            for c in (row.get("collections") or [])
        )
    )
    leaf_cols = MEN_HANDBAG_LEAF_COLLECTIONS if mens else HANDBAG_LEAF_COLLECTIONS
    parent_cols = MEN_BAG_PARENT_COLS if mens else BAG_PARENT_COLS
    parent_leaf = "pr-mens-handbags" if mens else "pr-handbags"
    gender_tag = "남성" if mens else "여성"

    cols = [
        c
        for c in (row.get("collections") or [])
        if c in leaf_cols or c in parent_cols
    ]
    cols = sorted(set([*cols, *parent_cols]))
    if any(c in leaf_cols for c in cols) and parent_leaf not in cols:
        cols.append(parent_leaf)
        cols = sorted(set(cols))

    leaf = row.get("leaf") or next(
        (c for c in leaf_cols if c in cols), parent_leaf
    )

    images = list(row.get("localImages") or [])
    if not images and row.get("localImage"):
        images = [row["localImage"]]
    images = [
        p
        for p in images
        if (ROOT / "public" / str(p).lstrip("/")).is_file()
        and (ROOT / "public" / str(p).lstrip("/")).stat().st_size > 2048
    ]
    if not images:
        print(f"skip no local image: {code}", flush=True)
        return None

    image = images[0]
    hover = row.get("localHover") or (images[1] if len(images) > 1 else image)
    if hover and not (
        (ROOT / "public" / str(hover).lstrip("/")).is_file()
        and (ROOT / "public" / str(hover).lstrip("/")).stat().st_size > 2048
    ):
        hover = images[1] if len(images) > 1 else image

    title_en = (row.get("officialNameEn") or row.get("title") or code).strip()
    name_ko = t(title_en)
    color_en = (row.get("color") or "").strip()
    color_ko = t(color_en) if color_en else ""

    editorial = (row.get("description") or "").strip()
    editorial_ko = t(editorial) if editorial else ""

    details = [x for x in (row.get("details") or []) if str(x).strip()]
    details_ko = [t(x) for x in details]
    materials = [x for x in (row.get("materialsCare") or []) if str(x).strip()]
    materials_ko = [t(x) for x in materials]
    if row.get("material") and not materials_ko:
        materials_ko = [t(row["material"])]

    dim_line = dims_ko(row.get("dimensions") or {})

    desc_bits = []
    if editorial_ko:
        desc_bits.append(editorial_ko)
    if details_ko:
        desc_bits.append(" · ".join(details_ko[:10]))
    if dim_line:
        desc_bits.append(dim_line)
    description_ko = "\n\n".join(desc_bits).strip()

    story: list[dict] = []
    if editorial_ko:
        story.append({"titleKo": name_ko, "bodyKo": editorial_ko, "image": image})
    if details_ko:
        story.append(
            {
                "titleKo": "디테일",
                "bodyKo": " · ".join(details_ko),
                "image": images[1] if len(images) > 1 else image,
                "reverse": True,
            }
        )
    if materials_ko:
        story.append(
            {
                "titleKo": "소재 & 케어",
                "bodyKo": " · ".join(materials_ko),
                "image": images[2] if len(images) > 2 else image,
            }
        )
    if dim_line:
        story.append(
            {
                "titleKo": "사이즈",
                "bodyKo": dim_line,
                "image": images[3] if len(images) > 3 else image,
                "reverse": True,
            }
        )
    for i, img in enumerate(images[1:], start=1):
        if len(story) >= 8:
            break
        story.append(
            {
                "titleKo": "갤러리",
                "bodyKo": "제품 디테일.",
                "image": img,
                "layout": "wide",
                "reverse": i % 2 == 0,
            }
        )

    tech: list[dict] = []
    if code:
        tech.append({"labelKo": "제품 코드", "valueKo": str(code)})
    if color_ko or color_en:
        tech.append({"labelKo": "컬러", "valueKo": color_ko or color_en})
    if row.get("material"):
        tech.append({"labelKo": "소재", "valueKo": t(row["material"])})
    for key, label in (
        ("height", "높이"),
        ("width", "가로"),
        ("length", "세로"),
        ("depth", "깊이"),
    ):
        v = (row.get("dimensions") or {}).get(key)
        if v:
            tech.append({"labelKo": label, "valueKo": v})

    pid = f"pr-{str(code).lower()}"
    registered = (prev or {}).get("registeredAt") or now_iso
    in_stock = bool(row.get("inStock", True))

    variant = {
        "id": f"{pid}-u",
        "name": f"{title_en} — {color_en or 'One Size'}".strip(" —"),
        "nameKo": f"{name_ko} — {color_ko or '원 사이즈'}".strip(" —"),
        "sku": code,
        "gbpPrice": float(gbp),
        "price": price,
        "image": image,
        "images": images,
        "hoverImage": hover,
        "sourceUrl": row.get("url") or "",
        "inStock": in_stock,
        "colorKey": slugify(color_en or color_ko or "default"),
        "colorNameKo": color_ko or color_en or "기본",
        "size": "One Size",
        "prCollections": cols,
    }

    tags = ["prada", "프라다", "handbag", "핸드백", gender_tag, *cols]

    return {
        "id": pid,
        "name": title_en,
        "nameKo": name_ko,
        "brand": "프라다",
        "price": price,
        "category": "bags",
        "subcategory": leaf,
        "prCollections": cols,
        "tags": tags,
        "descriptionKo": description_ko,
        "image": image,
        "images": images,
        "hoverImage": hover,
        "accent": accent_for(code),
        "badge": None,
        "gbpPrice": float(gbp),
        "sku": code,
        "sourceUrl": row.get("url") or "",
        "inStock": in_stock,
        "variants": [variant],
        "storySections": story,
        "techSpecs": tech or None,
        "registeredAt": registered,
        "editTier": "signature",
    }


def build_rtw_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    code = row.get("productCode") or row.get("id") or row.get("sku")
    if not code:
        return None
    gbp = row.get("gbpPrice")
    if gbp is None:
        return None
    price = gbp_to_krw(float(gbp))
    if price <= 0:
        return None

    cols = [
        c
        for c in (row.get("collections") or [])
        if c in RTW_LEAF_COLLECTIONS or c in RTW_PARENT_COLS
    ]
    cols = sorted(set([*cols, *RTW_PARENT_COLS]))
    leaf = row.get("leaf") or next(
        (c for c in RTW_LEAF_COLLECTIONS if c in cols), "pr-women-rtw"
    )

    images = list(row.get("localImages") or [])
    if not images and row.get("localImage"):
        images = [row["localImage"]]
    images = [
        p
        for p in images
        if (ROOT / "public" / str(p).lstrip("/")).is_file()
        and (ROOT / "public" / str(p).lstrip("/")).stat().st_size > 2048
    ]
    if not images:
        print(f"skip no local image (rtw): {code}", flush=True)
        return None

    image = images[0]
    hover = row.get("localHover") or (images[1] if len(images) > 1 else image)
    if hover and not (
        (ROOT / "public" / str(hover).lstrip("/")).is_file()
        and (ROOT / "public" / str(hover).lstrip("/")).stat().st_size > 2048
    ):
        hover = images[1] if len(images) > 1 else image

    title_en = (row.get("officialNameEn") or row.get("title") or code).strip()
    name_ko = t(title_en)
    color_en = (row.get("color") or "").strip()
    color_ko = t(color_en) if color_en else ""
    editorial = (row.get("description") or "").strip()
    editorial_ko = t(editorial) if editorial else ""
    details = [x for x in (row.get("details") or []) if str(x).strip()]
    details_ko = [t(x) for x in details]
    materials = [x for x in (row.get("materialsCare") or []) if str(x).strip()]
    materials_ko = [t(x) for x in materials]
    if row.get("material") and not materials_ko:
        materials_ko = [t(row["material"])]

    desc_bits = []
    if editorial_ko:
        desc_bits.append(editorial_ko)
    if details_ko:
        desc_bits.append(" · ".join(details_ko[:10]))
    description_ko = "\n\n".join(desc_bits).strip()

    story: list[dict] = []
    if editorial_ko:
        story.append({"titleKo": name_ko, "bodyKo": editorial_ko, "image": image})
    if details_ko:
        story.append(
            {
                "titleKo": "디테일",
                "bodyKo": " · ".join(details_ko),
                "image": images[1] if len(images) > 1 else image,
                "reverse": True,
            }
        )
    if materials_ko:
        story.append(
            {
                "titleKo": "소재 & 케어",
                "bodyKo": " · ".join(materials_ko),
                "image": images[2] if len(images) > 2 else image,
            }
        )
    for i, img in enumerate(images[1:], start=1):
        if len(story) >= 8:
            break
        story.append(
            {
                "titleKo": "갤러리",
                "bodyKo": "제품 디테일.",
                "image": img,
                "layout": "wide",
                "reverse": i % 2 == 0,
            }
        )

    pid = f"pr-{str(code).lower()}"
    registered = (prev or {}).get("registeredAt") or now_iso
    color_key = slugify(color_en or color_ko or "default")

    size_rows = row.get("sizes") or []
    variants: list[dict] = []
    for sz in size_rows:
        label = str(sz.get("size") or "").strip()
        if not label:
            continue
        slug = slugify(label)
        sz_in_stock = bool(sz.get("inStock", False))
        variants.append(
            {
                "id": f"{pid}-{slug}",
                "name": f"{title_en} — {label}",
                "nameKo": f"{name_ko} — {label}",
                "sku": f"{code}-{label}",
                "gbpPrice": float(gbp),
                "price": price,
                "image": image,
                "images": images,
                "hoverImage": hover,
                "sourceUrl": row.get("url") or "",
                "inStock": sz_in_stock,
                "colorKey": color_key,
                "colorNameKo": color_ko or color_en or "기본",
                "size": label,
                "prCollections": cols,
            }
        )
    in_stock = any(v["inStock"] for v in variants) if variants else bool(
        row.get("inStock", True)
    )
    if not variants:
        variants = [
            {
                "id": f"{pid}-os",
                "name": f"{title_en} — One Size",
                "nameKo": f"{name_ko} — 원 사이즈",
                "sku": code,
                "gbpPrice": float(gbp),
                "price": price,
                "image": image,
                "images": images,
                "hoverImage": hover,
                "sourceUrl": row.get("url") or "",
                "inStock": in_stock,
                "colorKey": color_key,
                "colorNameKo": color_ko or color_en or "기본",
                "size": "One Size",
                "prCollections": cols,
            }
        ]

    tags = ["prada", "프라다", "rtw", "레디투웨어", "여성", *cols]
    prod: dict = {
        "id": pid,
        "name": title_en,
        "nameKo": name_ko,
        "brand": "프라다",
        "price": price,
        "category": "luxury",
        "subcategory": leaf,
        "prCollections": cols,
        "tags": tags,
        "descriptionKo": description_ko,
        "image": image,
        "images": images,
        "hoverImage": hover,
        "accent": accent_for(code),
        "badge": None,
        "gbpPrice": float(gbp),
        "sku": code,
        "sourceUrl": row.get("url") or "",
        "inStock": in_stock,
        "variants": variants,
        "storySections": story,
        "registeredAt": registered,
        "editTier": "signature",
    }
    chart = size_chart_for_variants(variants)
    if chart:
        prod["sizeChart"] = chart
    return prod


def _usable_ko(text: str | None) -> str:
    """Keep Korean copy only when hybrid-English QA would pass."""
    s = re.sub(r"\s+", " ", (text or "").strip())
    if not s:
        return ""
    if en_ratio(s) <= _MAX_KO_EN_RATIO:
        return s
    return ""


def _usable_ko_list(items: list[str]) -> list[str]:
    return [x for x in (_usable_ko(v) for v in items) if x]


def build_mens_rtw_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    code = row.get("productCode") or row.get("id") or row.get("sku")
    if not code:
        return None
    gbp = row.get("gbpPrice")
    if gbp is None:
        return None
    price = gbp_to_krw(float(gbp))
    if price <= 0:
        return None

    cols = [
        c
        for c in (row.get("collections") or [])
        if c in MENS_RTW_LEAF_COLLECTIONS or c in MENS_RTW_PARENT_COLS
    ]
    cols = sorted(set([*cols, *MENS_RTW_PARENT_COLS]))
    leaf = row.get("leaf") or next(
        (c for c in MENS_RTW_LEAF_COLLECTIONS if c in cols), "pr-men-rtw"
    )

    images = list(row.get("localImages") or [])
    if not images and row.get("localImage"):
        images = [row["localImage"]]
    images = [
        p
        for p in images
        if (ROOT / "public" / str(p).lstrip("/")).is_file()
        and (ROOT / "public" / str(p).lstrip("/")).stat().st_size > 2048
    ]
    if not images:
        print(f"skip no local image (mens-rtw): {code}", flush=True)
        return None

    image = images[0]
    hover = row.get("localHover") or (images[1] if len(images) > 1 else image)
    if hover and not (
        (ROOT / "public" / str(hover).lstrip("/")).is_file()
        and (ROOT / "public" / str(hover).lstrip("/")).stat().st_size > 2048
    ):
        hover = images[1] if len(images) > 1 else image

    title_en = (row.get("officialNameEn") or row.get("title") or code).strip()
    name_ko = _usable_ko(t(title_en)) or apply_glossary(title_en)
    color_en = (row.get("color") or "").strip()
    color_ko = _usable_ko(t(color_en)) if color_en else ""
    editorial = (row.get("description") or "").strip()
    editorial_ko = _usable_ko(t(editorial)) if editorial else ""
    details = [x for x in (row.get("details") or []) if str(x).strip()]
    details_ko = _usable_ko_list([t(x) for x in details])
    materials = [x for x in (row.get("materialsCare") or []) if str(x).strip()]
    materials_ko = _usable_ko_list([t(x) for x in materials])
    if row.get("material") and not materials_ko:
        materials_ko = _usable_ko_list([t(row["material"])])

    desc_bits = []
    if editorial_ko:
        desc_bits.append(editorial_ko)
    if details_ko:
        desc_bits.append(" · ".join(details_ko[:10]))
    if not desc_bits:
        desc_bits.append(f"{name_ko}. 프라다 남성 레디투웨어.")
    description_ko = "\n\n".join(desc_bits).strip()

    story: list[dict] = []
    if editorial_ko:
        story.append({"titleKo": name_ko, "bodyKo": editorial_ko, "image": image})
    if details_ko:
        story.append(
            {
                "titleKo": "디테일",
                "bodyKo": " · ".join(details_ko),
                "image": images[1] if len(images) > 1 else image,
                "reverse": True,
            }
        )
    if materials_ko:
        story.append(
            {
                "titleKo": "소재 & 케어",
                "bodyKo": " · ".join(materials_ko),
                "image": images[2] if len(images) > 2 else image,
            }
        )
    if not story:
        story.append(
            {
                "titleKo": name_ko,
                "bodyKo": description_ko,
                "image": image,
            }
        )
    for i, img in enumerate(images[1:], start=1):
        if len(story) >= 8:
            break
        story.append(
            {
                "titleKo": "갤러리",
                "bodyKo": "제품 디테일.",
                "image": img,
                "layout": "wide",
                "reverse": i % 2 == 0,
            }
        )

    pid = f"pr-{str(code).lower()}"
    registered = (prev or {}).get("registeredAt") or now_iso
    color_key = slugify(color_en or color_ko or "default")

    size_rows = row.get("sizes") or []
    variants: list[dict] = []
    for sz in size_rows:
        label = str(sz.get("size") or "").strip()
        if not label:
            continue
        slug = slugify(label)
        sz_in_stock = bool(sz.get("inStock", False))
        variants.append(
            {
                "id": f"{pid}-{slug}",
                "name": f"{title_en} — {label}",
                "nameKo": f"{name_ko} — {label}",
                "sku": f"{code}-{label}",
                "gbpPrice": float(gbp),
                "price": price,
                "image": image,
                "images": images,
                "hoverImage": hover,
                "sourceUrl": row.get("url") or "",
                "inStock": sz_in_stock,
                "colorKey": color_key,
                "colorNameKo": color_ko or color_en or "기본",
                "size": label,
                "prCollections": cols,
            }
        )
    in_stock = any(v["inStock"] for v in variants) if variants else bool(
        row.get("inStock", True)
    )
    if not variants:
        variants = [
            {
                "id": f"{pid}-os",
                "name": f"{title_en} — One Size",
                "nameKo": f"{name_ko} — 원 사이즈",
                "sku": code,
                "gbpPrice": float(gbp),
                "price": price,
                "image": image,
                "images": images,
                "hoverImage": hover,
                "sourceUrl": row.get("url") or "",
                "inStock": in_stock,
                "colorKey": color_key,
                "colorNameKo": color_ko or color_en or "기본",
                "size": "One Size",
                "prCollections": cols,
            }
        ]

    tags = ["prada", "프라다", "rtw", "레디투웨어", "남성", *cols]
    prod: dict = {
        "id": pid,
        "name": title_en,
        "nameKo": name_ko,
        "brand": "프라다",
        "price": price,
        "category": "luxury",
        "subcategory": leaf,
        "prCollections": cols,
        "tags": tags,
        "descriptionKo": description_ko,
        "image": image,
        "images": images,
        "hoverImage": hover,
        "accent": accent_for(code),
        "badge": None,
        "gbpPrice": float(gbp),
        "sku": code,
        "sourceUrl": row.get("url") or "",
        "inStock": in_stock,
        "variants": variants,
        "storySections": story,
        "registeredAt": registered,
        "editTier": "signature",
    }
    chart = size_chart_for_mens_rtw_variants(variants)
    if chart:
        prod["sizeChart"] = chart
    return prod


def build_shoes_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    code = row.get("productCode") or row.get("id") or row.get("sku")
    if not code:
        return None
    gbp = row.get("gbpPrice")
    if gbp is None:
        return None
    price = gbp_to_krw(float(gbp))
    if price <= 0:
        return None

    kind = (row.get("_kind") or row.get("kind") or "").strip()
    is_mens = kind in {"mens-shoes"} or "pr-men-shoes" in (
        row.get("collections") or []
    ) or any(
        c in MENS_SHOES_LEAF_COLLECTIONS for c in (row.get("collections") or [])
    )
    leaf_cols = MENS_SHOES_LEAF_COLLECTIONS if is_mens else SHOES_LEAF_COLLECTIONS
    parent_cols = MENS_SHOES_PARENT_COLS if is_mens else SHOES_PARENT_COLS
    default_leaf = "pr-men-shoes" if is_mens else "pr-women-shoes"
    gender_tag = "남성" if is_mens else "여성"

    cols = [
        c
        for c in (row.get("collections") or [])
        if c in leaf_cols or c in parent_cols
    ]
    cols = sorted(set([*cols, *parent_cols]))
    leaf = row.get("leaf") or next(
        (c for c in leaf_cols if c in cols), default_leaf
    )

    images = list(row.get("localImages") or [])
    if not images and row.get("localImage"):
        images = [row["localImage"]]
    images = [
        p
        for p in images
        if (ROOT / "public" / str(p).lstrip("/")).is_file()
        and (ROOT / "public" / str(p).lstrip("/")).stat().st_size > 2048
    ]
    if not images:
        print(f"skip no local image (shoes): {code}", flush=True)
        return None

    image = images[0]
    hover = row.get("localHover") or (images[1] if len(images) > 1 else image)
    if hover and not (
        (ROOT / "public" / str(hover).lstrip("/")).is_file()
        and (ROOT / "public" / str(hover).lstrip("/")).stat().st_size > 2048
    ):
        hover = images[1] if len(images) > 1 else image

    title_en = (row.get("officialNameEn") or row.get("title") or code).strip()
    name_ko = t(title_en)
    color_en = (row.get("color") or "").strip()
    color_ko = t(color_en) if color_en else ""
    editorial = (row.get("description") or "").strip()
    editorial_ko = t(editorial) if editorial else ""
    details = [x for x in (row.get("details") or []) if str(x).strip()]
    details_ko = [t(x) for x in details]
    materials = [x for x in (row.get("materialsCare") or []) if str(x).strip()]
    materials_ko = [t(x) for x in materials]
    if row.get("material") and not materials_ko:
        materials_ko = [t(row["material"])]

    desc_bits = []
    if editorial_ko:
        desc_bits.append(editorial_ko)
    if details_ko:
        desc_bits.append(" · ".join(details_ko[:10]))
    description_ko = "\n\n".join(desc_bits).strip()

    story: list[dict] = []
    if editorial_ko:
        story.append({"titleKo": name_ko, "bodyKo": editorial_ko, "image": image})
    if details_ko:
        story.append(
            {
                "titleKo": "디테일",
                "bodyKo": " · ".join(details_ko),
                "image": images[1] if len(images) > 1 else image,
                "reverse": True,
            }
        )
    if materials_ko:
        story.append(
            {
                "titleKo": "소재 & 케어",
                "bodyKo": " · ".join(materials_ko),
                "image": images[2] if len(images) > 2 else image,
            }
        )
    for i, img in enumerate(images[1:], start=1):
        if len(story) >= 8:
            break
        story.append(
            {
                "titleKo": "갤러리",
                "bodyKo": "제품 디테일.",
                "image": img,
                "layout": "wide",
                "reverse": i % 2 == 0,
            }
        )

    pid = f"pr-{str(code).lower()}"
    registered = (prev or {}).get("registeredAt") or now_iso
    color_key = slugify(color_en or color_ko or "default")

    size_rows = row.get("sizes") or []
    variants: list[dict] = []
    for sz in size_rows:
        label = str(sz.get("size") or "").strip()
        if not label:
            continue
        slug = slugify(label)
        sz_in_stock = bool(sz.get("inStock", False))
        variants.append(
            {
                "id": f"{pid}-{slug}",
                "name": f"{title_en} — {label}",
                "nameKo": f"{name_ko} — {label}",
                "sku": f"{code}-{label}",
                "gbpPrice": float(gbp),
                "price": price,
                "image": image,
                "images": images,
                "hoverImage": hover,
                "sourceUrl": row.get("url") or "",
                "inStock": sz_in_stock,
                "colorKey": color_key,
                "colorNameKo": color_ko or color_en or "기본",
                "size": label,
                "prCollections": cols,
            }
        )
    in_stock = any(v["inStock"] for v in variants) if variants else bool(
        row.get("inStock", True)
    )
    if not variants:
        variants = [
            {
                "id": f"{pid}-os",
                "name": f"{title_en} — One Size",
                "nameKo": f"{name_ko} — 원 사이즈",
                "sku": code,
                "gbpPrice": float(gbp),
                "price": price,
                "image": image,
                "images": images,
                "hoverImage": hover,
                "sourceUrl": row.get("url") or "",
                "inStock": in_stock,
                "colorKey": color_key,
                "colorNameKo": color_ko or color_en or "기본",
                "size": "One Size",
                "prCollections": cols,
            }
        ]

    tags = ["prada", "프라다", "shoes", "슈즈", gender_tag, *cols]
    prod: dict = {
        "id": pid,
        "name": title_en,
        "nameKo": name_ko,
        "brand": "프라다",
        "price": price,
        "category": "shoes",
        "subcategory": leaf,
        "prCollections": cols,
        "tags": tags,
        "descriptionKo": description_ko,
        "image": image,
        "images": images,
        "hoverImage": hover,
        "accent": accent_for(code),
        "badge": None,
        "gbpPrice": float(gbp),
        "sku": code,
        "sourceUrl": row.get("url") or "",
        "inStock": in_stock,
        "variants": variants,
        "storySections": story,
        "registeredAt": registered,
        "editTier": "signature",
    }
    chart = size_chart_for_shoes(variants, mens=is_mens)
    if chart:
        prod["sizeChart"] = chart
    return prod


def _slg_row_images(row: dict) -> list[str]:
    images = list(row.get("localImages") or [])
    if not images and row.get("localImage"):
        images = [row["localImage"]]
    return [
        p
        for p in images
        if (ROOT / "public" / str(p).lstrip("/")).is_file()
        and (ROOT / "public" / str(p).lstrip("/")).stat().st_size > 2048
    ]



def _acc_row_images(row: dict) -> list[str]:
    return _slg_row_images(row)


def _travel_row_images(row: dict) -> list[str]:
    return _acc_row_images(row)


def build_slg_products(rows: list[dict], prev_by_sku: dict[str, dict], now_iso: str) -> list[dict]:
    """Group SLG colorways by parentProduct into multi-color variant products."""
    groups: dict[str, list[dict]] = {}
    for row in rows:
        parent = (row.get("parentProduct") or "").strip()
        code = str(row.get("productCode") or row.get("id") or "")
        key = parent or code
        groups.setdefault(key, []).append(row)

    out: list[dict] = []
    for parent, members in sorted(groups.items()):
        members = sorted(members, key=lambda r: str(r.get("productCode") or ""))
        # Prefer in-stock + imaged colorways
        usable = [r for r in members if _slg_row_images(r) and r.get("gbpPrice") is not None]
        if not usable:
            continue

        primary = usable[0]
        code0 = str(primary.get("productCode") or primary.get("id") or "")
        title_en = (primary.get("officialNameEn") or primary.get("title") or code0).strip()
        name_ko = t(title_en)

        sample_cols = [
            c
            for r in usable
            for c in (r.get("collections") or [])
        ]
        is_mens = any(
            c in MEN_SLG_LEAF_COLLECTIONS or c in MEN_SLG_PARENT_COLS for c in sample_cols
        ) or str(primary.get("_kind") or "") == "mens-slg"
        leaf_cols = MEN_SLG_LEAF_COLLECTIONS if is_mens else SLG_LEAF_COLLECTIONS
        parent_cols = MEN_SLG_PARENT_COLS if is_mens else SLG_PARENT_COLS
        default_leaf = "pr-mens-slg" if is_mens else "pr-women-slg"
        gender_tag = "남성" if is_mens else "여성"

        cols: list[str] = []
        for r in usable:
            cols.extend(
                c
                for c in (r.get("collections") or [])
                if c in leaf_cols or c in parent_cols
            )
        cols = sorted(set([*cols, *parent_cols]))
        leaf = primary.get("leaf") or next(
            (c for c in leaf_cols if c in cols), default_leaf
        )

        variants: list[dict] = []
        story_images: list[str] = []
        prices: list[float] = []
        for r in usable:
            images = _slg_row_images(r)
            if not images:
                continue
            image = images[0]
            hover = r.get("localHover") or (images[1] if len(images) > 1 else image)
            if hover and not (
                (ROOT / "public" / str(hover).lstrip("/")).is_file()
                and (ROOT / "public" / str(hover).lstrip("/")).stat().st_size > 2048
            ):
                hover = images[1] if len(images) > 1 else image
            story_images.extend(images[:3])

            code = str(r.get("productCode") or r.get("id") or "")
            gbp = float(r["gbpPrice"])
            price = gbp_to_krw(gbp)
            if price <= 0:
                continue
            prices.append(gbp)
            color_en = (r.get("color") or "").strip()
            color_ko = t(color_en) if color_en else "기본"
            color_key = slugify(color_en or color_ko or code)
            size_rows = r.get("sizes") or []
            size_labels = [
                str(sz.get("size") or "").strip()
                for sz in size_rows
                if str(sz.get("size") or "").strip()
            ]
            if not size_labels:
                size_labels = ["One Size"]
            for label in size_labels:
                sz_meta = next(
                    (
                        sz
                        for sz in size_rows
                        if str(sz.get("size") or "").strip() == label
                    ),
                    None,
                )
                sz_in_stock = (
                    bool(sz_meta.get("inStock"))
                    if sz_meta
                    else bool(r.get("inStock", True))
                )
                # TU / OS → 원 사이즈 for display
                size_disp = (
                    "원 사이즈"
                    if label.upper() in {"TU", "OS", "ONE SIZE", "ONESIZE"}
                    else label
                )
                size_key = "one-size" if size_disp == "원 사이즈" else slugify(label)
                variants.append(
                    {
                        "id": f"pr-{code.lower()}-{size_key}",
                        "name": f"{title_en} — {color_en or 'Default'} — {label}",
                        "nameKo": f"{name_ko} — {color_ko} — {size_disp}",
                        "sku": f"{code}-{label}",
                        "gbpPrice": gbp,
                        "price": price,
                        "image": image,
                        "images": images,
                        "hoverImage": hover,
                        "sourceUrl": r.get("url") or "",
                        "inStock": sz_in_stock,
                        "colorKey": color_key,
                        "colorNameKo": color_ko,
                        "size": size_disp,
                        "prCollections": cols,
                    }
                )

        if not variants:
            continue

        # Deduplicate story images preserving order
        seen_img: set[str] = set()
        gallery: list[str] = []
        for im in story_images:
            if im not in seen_img:
                seen_img.add(im)
                gallery.append(im)
        image = gallery[0]
        hover = gallery[1] if len(gallery) > 1 else image

        editorial = (primary.get("description") or "").strip()
        editorial_ko = t(editorial) if editorial else ""
        details = [x for x in (primary.get("details") or []) if str(x).strip()]
        details_ko = [t(x) for x in details]
        materials = [x for x in (primary.get("materialsCare") or []) if str(x).strip()]
        materials_ko = [t(x) for x in materials]
        if primary.get("material") and not materials_ko:
            materials_ko = [t(primary["material"])]

        desc_bits = []
        if editorial_ko:
            desc_bits.append(editorial_ko)
        if details_ko:
            desc_bits.append(" · ".join(details_ko[:10]))
        description_ko = "\n\n".join(desc_bits).strip()

        story: list[dict] = []
        if editorial_ko:
            story.append({"titleKo": name_ko, "bodyKo": editorial_ko, "image": image})
        if details_ko:
            story.append(
                {
                    "titleKo": "디테일",
                    "bodyKo": " · ".join(details_ko),
                    "image": gallery[1] if len(gallery) > 1 else image,
                    "reverse": True,
                }
            )
        if materials_ko:
            story.append(
                {
                    "titleKo": "소재 & 케어",
                    "bodyKo": " · ".join(materials_ko),
                    "image": gallery[2] if len(gallery) > 2 else image,
                }
            )
        for i, img in enumerate(gallery[1:], start=1):
            if len(story) >= 8:
                break
            story.append(
                {
                    "titleKo": "갤러리",
                    "bodyKo": "제품 디테일.",
                    "image": img,
                    "layout": "wide",
                    "reverse": i % 2 == 0,
                }
            )

        # Product id: parent when multi-color, else sku
        if len(usable) > 1 and parent:
            pid = f"pr-{parent.lower()}"
            sku_main = parent
        else:
            pid = f"pr-{code0.lower()}"
            sku_main = code0

        prev = prev_by_sku.get(sku_main) or prev_by_sku.get(code0)
        registered = (prev or {}).get("registeredAt") or now_iso
        gbp0 = float(usable[0]["gbpPrice"])
        price0 = gbp_to_krw(gbp0)
        in_stock = any(v["inStock"] for v in variants)

        tags = ["prada", "프라다", "accessories", "악세서리", "slg", gender_tag, *cols]
        out.append(
            {
                "id": pid,
                "name": title_en,
                "nameKo": name_ko,
                "brand": "프라다",
                "price": price0,
                "category": "accessories",
                "subcategory": leaf,
                "prCollections": cols,
                "tags": tags,
                "descriptionKo": description_ko,
                "image": image,
                "images": gallery[:10],
                "hoverImage": hover,
                "accent": accent_for(sku_main),
                "badge": None,
                "gbpPrice": gbp0,
                "sku": sku_main,
                "sourceUrl": primary.get("url") or "",
                "inStock": in_stock,
                "variants": variants,
                "storySections": story,
                "registeredAt": registered,
                "editTier": "signature",
            }
        )
    return out


def build_travel_products(rows: list[dict], prev_by_sku: dict[str, dict], now_iso: str) -> list[dict]:
    """Group travel colorways by parentProduct into multi-color variant products."""
    groups: dict[str, list[dict]] = {}
    for row in rows:
        parent = (row.get("parentProduct") or "").strip()
        code = str(row.get("productCode") or row.get("id") or "")
        key = parent or code
        groups.setdefault(key, []).append(row)

    out: list[dict] = []
    for parent, members in sorted(groups.items()):
        members = sorted(members, key=lambda r: str(r.get("productCode") or ""))
        # Prefer in-stock + imaged colorways
        usable = [r for r in members if _travel_row_images(r) and r.get("gbpPrice") is not None]
        if not usable:
            continue

        primary = usable[0]
        code0 = str(primary.get("productCode") or primary.get("id") or "")
        title_en = (primary.get("officialNameEn") or primary.get("title") or code0).strip()
        name_ko = t(title_en)

        sample_cols = [
            c
            for r in usable
            for c in (r.get("collections") or [])
        ]
        is_mens = any(
            c in MEN_TRAVEL_LEAF_COLLECTIONS or c in MEN_TRAVEL_PARENT_COLS for c in sample_cols
        ) or str(primary.get("_kind") or "") == "mens-travel"
        leaf_cols = MEN_TRAVEL_LEAF_COLLECTIONS if is_mens else TRAVEL_LEAF_COLLECTIONS
        parent_cols = MEN_TRAVEL_PARENT_COLS if is_mens else TRAVEL_PARENT_COLS
        default_leaf = "pr-men-travel" if is_mens else "pr-women-travel"
        gender_tag = "남성" if is_mens else "여성"

        cols: list[str] = []
        for r in usable:
            cols.extend(
                c
                for c in (r.get("collections") or [])
                if c in leaf_cols or c in parent_cols
            )
        cols = sorted(set([*cols, *parent_cols]))
        leaf = primary.get("leaf") or next(
            (c for c in leaf_cols if c in cols), default_leaf
        )

        variants: list[dict] = []
        story_images: list[str] = []
        prices: list[float] = []
        for r in usable:
            images = _travel_row_images(r)
            if not images:
                continue
            image = images[0]
            hover = r.get("localHover") or (images[1] if len(images) > 1 else image)
            if hover and not (
                (ROOT / "public" / str(hover).lstrip("/")).is_file()
                and (ROOT / "public" / str(hover).lstrip("/")).stat().st_size > 2048
            ):
                hover = images[1] if len(images) > 1 else image
            story_images.extend(images[:3])

            code = str(r.get("productCode") or r.get("id") or "")
            gbp = float(r["gbpPrice"])
            price = gbp_to_krw(gbp)
            if price <= 0:
                continue
            prices.append(gbp)
            color_en = (r.get("color") or "").strip()
            color_ko = t(color_en) if color_en else "기본"
            color_key = slugify(color_en or color_ko or code)
            size_rows = r.get("sizes") or []
            size_labels = [
                str(sz.get("size") or "").strip()
                for sz in size_rows
                if str(sz.get("size") or "").strip()
            ]
            if not size_labels:
                size_labels = ["One Size"]
            for label in size_labels:
                sz_meta = next(
                    (
                        sz
                        for sz in size_rows
                        if str(sz.get("size") or "").strip() == label
                    ),
                    None,
                )
                sz_in_stock = (
                    bool(sz_meta.get("inStock"))
                    if sz_meta
                    else bool(r.get("inStock", True))
                )
                # TU / OS → 원 사이즈 for display
                size_disp = (
                    "원 사이즈"
                    if label.upper() in {"TU", "OS", "ONE SIZE", "ONESIZE"}
                    else label
                )
                size_key = "one-size" if size_disp == "원 사이즈" else slugify(label)
                variants.append(
                    {
                        "id": f"pr-{code.lower()}-{size_key}",
                        "name": f"{title_en} — {color_en or 'Default'} — {label}",
                        "nameKo": f"{name_ko} — {color_ko} — {size_disp}",
                        "sku": f"{code}-{label}",
                        "gbpPrice": gbp,
                        "price": price,
                        "image": image,
                        "images": images,
                        "hoverImage": hover,
                        "sourceUrl": r.get("url") or "",
                        "inStock": sz_in_stock,
                        "colorKey": color_key,
                        "colorNameKo": color_ko,
                        "size": size_disp,
                        "prCollections": cols,
                    }
                )

        if not variants:
            continue

        # Deduplicate story images preserving order
        seen_img: set[str] = set()
        gallery: list[str] = []
        for im in story_images:
            if im not in seen_img:
                seen_img.add(im)
                gallery.append(im)
        image = gallery[0]
        hover = gallery[1] if len(gallery) > 1 else image

        editorial = (primary.get("description") or "").strip()
        editorial_ko = t(editorial) if editorial else ""
        details = [x for x in (primary.get("details") or []) if str(x).strip()]
        details_ko = [t(x) for x in details]
        materials = [x for x in (primary.get("materialsCare") or []) if str(x).strip()]
        materials_ko = [t(x) for x in materials]
        if primary.get("material") and not materials_ko:
            materials_ko = [t(primary["material"])]

        desc_bits = []
        if editorial_ko:
            desc_bits.append(editorial_ko)
        if details_ko:
            desc_bits.append(" · ".join(details_ko[:10]))
        description_ko = "\n\n".join(desc_bits).strip()

        story: list[dict] = []
        if editorial_ko:
            story.append({"titleKo": name_ko, "bodyKo": editorial_ko, "image": image})
        if details_ko:
            story.append(
                {
                    "titleKo": "디테일",
                    "bodyKo": " · ".join(details_ko),
                    "image": gallery[1] if len(gallery) > 1 else image,
                    "reverse": True,
                }
            )
        if materials_ko:
            story.append(
                {
                    "titleKo": "소재 & 케어",
                    "bodyKo": " · ".join(materials_ko),
                    "image": gallery[2] if len(gallery) > 2 else image,
                }
            )
        for i, img in enumerate(gallery[1:], start=1):
            if len(story) >= 8:
                break
            story.append(
                {
                    "titleKo": "갤러리",
                    "bodyKo": "제품 디테일.",
                    "image": img,
                    "layout": "wide",
                    "reverse": i % 2 == 0,
                }
            )

        # Product id: parent when multi-color, else sku
        if len(usable) > 1 and parent:
            pid = f"pr-{parent.lower()}"
            sku_main = parent
        else:
            pid = f"pr-{code0.lower()}"
            sku_main = code0

        prev = prev_by_sku.get(sku_main) or prev_by_sku.get(code0)
        registered = (prev or {}).get("registeredAt") or now_iso
        gbp0 = float(usable[0]["gbpPrice"])
        price0 = gbp_to_krw(gbp0)
        in_stock = any(v["inStock"] for v in variants)

        tags = ["prada", "프라다", "bags", "가방", "travel", "여행", gender_tag, *cols]
        out.append(
            {
                "id": pid,
                "name": title_en,
                "nameKo": name_ko,
                "brand": "프라다",
                "price": price0,
                "category": "bags",
                "subcategory": leaf,
                "prCollections": cols,
                "tags": tags,
                "descriptionKo": description_ko,
                "image": image,
                "images": gallery[:10],
                "hoverImage": hover,
                "accent": accent_for(sku_main),
                "badge": None,
                "gbpPrice": gbp0,
                "sku": sku_main,
                "sourceUrl": primary.get("url") or "",
                "inStock": in_stock,
                "variants": variants,
                "storySections": story,
                "registeredAt": registered,
                "editTier": "signature",
            }
        )
    return out

def linea_rossa_fragrance_skus() -> set[str]:
    """SKU keys for Linea Rossa fragrance PLP (Luna Rossa etc.)."""
    out: set[str] = set()
    if not RAW_LINEA.exists():
        return out
    for r in json.loads(RAW_LINEA.read_text()).get("products") or []:
        cols = r.get("collections") or []
        leaf = str(r.get("leaf") or "")
        if "pr-linea-rossa-fragrances" not in cols and leaf != "pr-linea-rossa-fragrances":
            continue
        for k in ("productCode", "id", "sku", "parentProduct"):
            v = str(r.get(k) or "").strip()
            if v:
                out.add(v.upper())
    return out


def build_accessories_products(rows: list[dict], prev_by_sku: dict[str, dict], now_iso: str) -> list[dict]:
    """Group accessories colorways by parentProduct into multi-color variant products."""
    groups: dict[str, list[dict]] = {}
    for row in rows:
        parent = (row.get("parentProduct") or "").strip()
        code = str(row.get("productCode") or row.get("id") or "")
        key = parent or code
        groups.setdefault(key, []).append(row)

    out: list[dict] = []
    for parent, members in sorted(groups.items()):
        members = sorted(members, key=lambda r: str(r.get("productCode") or ""))
        # Prefer in-stock + imaged colorways
        usable = [r for r in members if _acc_row_images(r) and r.get("gbpPrice") is not None]
        if not usable:
            continue

        primary = usable[0]
        code0 = str(primary.get("productCode") or primary.get("id") or "")
        title_en = (primary.get("officialNameEn") or primary.get("title") or code0).strip()
        name_ko = t(title_en)

        sample_cols = [
            c
            for r in usable
            for c in (r.get("collections") or [])
        ]
        is_linea = any(
            c in LINEA_ROSSA_LEAF_COLLECTIONS or c == "pr-linea-rossa"
            for c in sample_cols
        ) or str(primary.get("_kind") or "") in {"linea-rossa", "linea"}
        is_beauty = any(
            c in BEAUTY_LEAF_COLLECTIONS or c == "pr-beauty"
            for c in sample_cols
        ) or str(primary.get("_kind") or "") in {"beauty"}
        is_fragrance = any(
            c in FRAGRANCE_LEAF_COLLECTIONS or c == "pr-fragrances"
            for c in sample_cols
        ) or str(primary.get("_kind") or "") in {"fragrances", "fragrance"}
        is_fine_jewelry = any(
            c in FINE_JEWELRY_LEAF_COLLECTIONS or c == "pr-fine-jewelry"
            for c in sample_cols
        ) or str(primary.get("_kind") or "") in {"fine-jewelry", "fine_jewelry"}
        is_mens = any(
            c in MEN_ACCESSORIES_LEAF_COLLECTIONS or c in MEN_ACCESSORIES_PARENT_COLS
            for c in sample_cols
        ) or str(primary.get("_kind") or "") in {"mens-accessories", "mens-acc"}
        # Prefer explicit scrape kind / leaf over shared prada-accessories parent.
        kind0 = str(primary.get("_kind") or primary.get("kind") or "")
        if kind0 in {"fine-jewelry", "fine_jewelry"} or (
            is_fine_jewelry and not is_beauty and not is_fragrance and not is_linea
        ):
            leaf_cols = FINE_JEWELRY_LEAF_COLLECTIONS
            parent_cols = FINE_JEWELRY_PARENT_COLS
            default_leaf = "pr-fine-jewelry"
            gender_tag = "공용"
            is_fine_jewelry, is_fragrance, is_beauty, is_linea = True, False, False, False
        elif kind0 in {"fragrances", "fragrance"} or (is_fragrance and not is_beauty and not is_linea):
            leaf_cols = FRAGRANCE_LEAF_COLLECTIONS
            parent_cols = FRAGRANCE_PARENT_COLS
            default_leaf = "pr-fragrances"
            if "pr-fragrances-women" in sample_cols and "pr-fragrances-men" not in sample_cols:
                gender_tag = "여성"
            elif "pr-fragrances-men" in sample_cols and "pr-fragrances-women" not in sample_cols:
                gender_tag = "남성"
            else:
                gender_tag = "공용"
            is_fragrance, is_beauty, is_linea = True, False, False
        elif kind0 in {"beauty"} or (is_beauty and not is_linea):
            leaf_cols = BEAUTY_LEAF_COLLECTIONS
            parent_cols = BEAUTY_PARENT_COLS
            default_leaf = "pr-beauty"
            gender_tag = "여성"
            is_fragrance, is_beauty, is_linea = False, True, False
        elif is_linea:
            leaf_cols = LINEA_ROSSA_LEAF_COLLECTIONS
            parent_cols = LINEA_ROSSA_PARENT_COLS
            default_leaf = "pr-linea-rossa"
            if "pr-linea-rossa-women" in sample_cols and "pr-linea-rossa-men" not in sample_cols:
                gender_tag = "여성"
            elif "pr-linea-rossa-men" in sample_cols and "pr-linea-rossa-women" not in sample_cols:
                gender_tag = "남성"
            else:
                gender_tag = "공용"
            is_fragrance, is_beauty, is_linea = False, False, True
        else:
            leaf_cols = (
                MEN_ACCESSORIES_LEAF_COLLECTIONS if is_mens else ACCESSORIES_LEAF_COLLECTIONS
            )
            parent_cols = (
                MEN_ACCESSORIES_PARENT_COLS if is_mens else ACCESSORIES_PARENT_COLS
            )
            default_leaf = "pr-mens-accessories" if is_mens else "pr-women-accessories"
            gender_tag = "남성" if is_mens else "여성"
            is_fragrance = is_beauty = is_linea = False

        cols: list[str] = []
        for r in usable:
            cols.extend(
                c
                for c in (r.get("collections") or [])
                if c in leaf_cols or c in parent_cols
            )
        cols = sorted(set([*cols, *parent_cols]))
        leaf = primary.get("leaf") or next(
            (c for c in leaf_cols if c in cols), default_leaf
        )

        # Luna Rossa / Linea Rossa fragrances: keep both Fragrances + Linea Rossa leaves.
        member_skus = {
            str(r.get(k) or "").strip().upper()
            for r in usable
            for k in ("productCode", "id", "sku", "parentProduct")
            if str(r.get(k) or "").strip()
        }
        is_linea_frag = bool(member_skus & linea_rossa_fragrance_skus()) or (
            "pr-linea-rossa-fragrances" in sample_cols
        )
        if is_linea_frag and (is_fragrance or is_linea):
            frag_leaves = [c for c in sample_cols if c in FRAGRANCE_LEAF_COLLECTIONS]
            if not frag_leaves and is_fragrance:
                frag_leaves = [c for c in cols if c in FRAGRANCE_LEAF_COLLECTIONS]
            if not frag_leaves:
                frag_leaves = ["pr-fragrances-men"]
            cols = sorted(
                set(
                    [
                        *cols,
                        *FRAGRANCE_PARENT_COLS,
                        *LINEA_ROSSA_PARENT_COLS,
                        "pr-linea-rossa-fragrances",
                        *frag_leaves,
                    ]
                )
            )
            if is_fragrance:
                leaf = next(
                    (c for c in FRAGRANCE_LEAF_COLLECTIONS if c in cols),
                    leaf,
                )
            else:
                leaf = "pr-linea-rossa-fragrances"

        variants: list[dict] = []
        story_images: list[str] = []
        prices: list[float] = []
        for r in usable:
            images = _acc_row_images(r)
            if not images:
                continue
            image = images[0]
            hover = r.get("localHover") or (images[1] if len(images) > 1 else image)
            if hover and not (
                (ROOT / "public" / str(hover).lstrip("/")).is_file()
                and (ROOT / "public" / str(hover).lstrip("/")).stat().st_size > 2048
            ):
                hover = images[1] if len(images) > 1 else image
            story_images.extend(images[:3])

            code = str(r.get("productCode") or r.get("id") or "")
            gbp = float(r["gbpPrice"])
            price = gbp_to_krw(gbp)
            if price <= 0:
                continue
            prices.append(gbp)
            color_en = (r.get("color") or "").strip()
            color_ko = t(color_en) if color_en else "기본"
            color_key = slugify(color_en or color_ko or code)
            size_rows = r.get("sizes") or []
            size_labels = [
                str(sz.get("size") or "").strip()
                for sz in size_rows
                if str(sz.get("size") or "").strip()
            ]
            if not size_labels:
                size_labels = ["One Size"]
            for label in size_labels:
                sz_meta = next(
                    (
                        sz
                        for sz in size_rows
                        if str(sz.get("size") or "").strip() == label
                    ),
                    None,
                )
                sz_in_stock = (
                    bool(sz_meta.get("inStock"))
                    if sz_meta
                    else bool(r.get("inStock", True))
                )
                # TU / OS → 원 사이즈 for display
                size_disp = (
                    "원 사이즈"
                    if label.upper() in {"TU", "OS", "ONE SIZE", "ONESIZE"}
                    else label
                )
                size_key = "one-size" if size_disp == "원 사이즈" else slugify(label)
                variants.append(
                    {
                        "id": f"pr-{code.lower()}-{size_key}",
                        "name": f"{title_en} — {color_en or 'Default'} — {label}",
                        "nameKo": f"{name_ko} — {color_ko} — {size_disp}",
                        "sku": f"{code}-{label}",
                        "gbpPrice": gbp,
                        "price": price,
                        "image": image,
                        "images": images,
                        "hoverImage": hover,
                        "sourceUrl": r.get("url") or "",
                        "inStock": sz_in_stock,
                        "colorKey": color_key,
                        "colorNameKo": color_ko,
                        "size": size_disp,
                        "prCollections": cols,
                    }
                )

        if not variants:
            continue

        # Deduplicate story images preserving order
        seen_img: set[str] = set()
        gallery: list[str] = []
        for im in story_images:
            if im not in seen_img:
                seen_img.add(im)
                gallery.append(im)
        image = gallery[0]
        hover = gallery[1] if len(gallery) > 1 else image

        editorial = (primary.get("description") or "").strip()
        editorial_ko = t(editorial) if editorial else ""
        details = [x for x in (primary.get("details") or []) if str(x).strip()]
        details_ko = [t(x) for x in details]
        materials = [x for x in (primary.get("materialsCare") or []) if str(x).strip()]
        materials_ko = [t(x) for x in materials]
        if primary.get("material") and not materials_ko:
            materials_ko = [t(primary["material"])]

        desc_bits = []
        if editorial_ko:
            desc_bits.append(editorial_ko)
        if details_ko:
            desc_bits.append(" · ".join(details_ko[:10]))
        description_ko = "\n\n".join(desc_bits).strip()

        story: list[dict] = []
        if editorial_ko:
            story.append({"titleKo": name_ko, "bodyKo": editorial_ko, "image": image})
        if details_ko:
            story.append(
                {
                    "titleKo": "디테일",
                    "bodyKo": " · ".join(details_ko),
                    "image": gallery[1] if len(gallery) > 1 else image,
                    "reverse": True,
                }
            )
        if materials_ko:
            story.append(
                {
                    "titleKo": "소재 & 케어",
                    "bodyKo": " · ".join(materials_ko),
                    "image": gallery[2] if len(gallery) > 2 else image,
                }
            )
        for i, img in enumerate(gallery[1:], start=1):
            if len(story) >= 8:
                break
            story.append(
                {
                    "titleKo": "갤러리",
                    "bodyKo": "제품 디테일.",
                    "image": img,
                    "layout": "wide",
                    "reverse": i % 2 == 0,
                }
            )

        # Product id: parent when multi-color, else sku
        if len(usable) > 1 and parent:
            pid = f"pr-{parent.lower()}"
            sku_main = parent
        else:
            pid = f"pr-{code0.lower()}"
            sku_main = code0

        prev = prev_by_sku.get(sku_main) or prev_by_sku.get(code0)
        registered = (prev or {}).get("registeredAt") or now_iso
        gbp0 = float(usable[0]["gbpPrice"])
        price0 = gbp_to_krw(gbp0)
        in_stock = any(v["inStock"] for v in variants)

        tags = ["prada", "프라다", "accessories", "악세서리", "acc", gender_tag, *cols]
        if is_linea_frag and (is_fragrance or is_linea):
            tags = sorted(
                set(
                    [
                        *tags,
                        "linea-rossa",
                        "Linea Rossa",
                        "리네아 로사",
                        "prada linea rossa",
                        "fragrances",
                        "향수",
                        "prada fragrances",
                    ]
                )
            )
        elif is_linea:
            tags = sorted(
                set([*tags, "linea-rossa", "Linea Rossa", "리네아 로사", "prada linea rossa"])
            )
        elif is_beauty:
            tags = sorted(set([*tags, "beauty", "뷰티", "prada beauty"]))
        elif is_fine_jewelry:
            tags = sorted(set([*tags, "fine-jewelry", "파인 주얼리", "prada fine jewelry"]))
        elif is_fragrance:
            tags = sorted(set([*tags, "fragrances", "향수", "prada fragrances"]))
        out.append(
            {
                "id": pid,
                "name": title_en,
                "nameKo": name_ko,
                "brand": "프라다",
                "price": price0,
                "category": "accessories",
                "subcategory": leaf,
                "prCollections": cols,
                "tags": tags,
                "descriptionKo": description_ko,
                "image": image,
                "images": gallery[:10],
                "hoverImage": hover,
                "accent": accent_for(sku_main),
                "badge": None,
                "gbpPrice": gbp0,
                "sku": sku_main,
                "sourceUrl": primary.get("url") or "",
                "inStock": in_stock,
                "variants": variants,
                "storySections": story,
                "registeredAt": registered,
                "editTier": "signature",
            }
        )
    return out

def _row_has_price(row: dict) -> bool:
    gbp = row.get("gbpPrice")
    if gbp is None:
        return False
    try:
        return float(gbp) > 0
    except (TypeError, ValueError):
        return False


def _collect_no_price_skus(*row_lists: list[dict]) -> set[str]:
    out: set[str] = set()
    for rows in row_lists:
        for row in rows:
            if _row_has_price(row):
                continue
            for key in ("sku", "productCode", "id", "parentProduct"):
                val = str(row.get(key) or "").strip()
                if val:
                    out.add(val.upper())
    return out


def _preserve_no_price_catalog(
    existing: list[dict], products: list[dict], no_price_skus: set[str]
) -> list[dict]:
    if not no_price_skus:
        return products
    new_ids = {p["id"] for p in products}
    preserved: list[dict] = []
    for p in existing:
        if p["id"] in new_ids:
            continue
        sku = str(p.get("sku") or "").upper()
        if sku in no_price_skus:
            preserved.append(p)
            continue
        for v in p.get("variants") or []:
            base = str(v.get("sku") or "").split("-")[0].upper()
            if base in no_price_skus:
                preserved.append(p)
                break
    if preserved:
        print(
            f"preserved {len(preserved)} catalogue entries (scrape missing GBP price)",
            flush=True,
        )
    return products + preserved


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--only",
        choices=["shoes", "mens-shoes", "rtw", "mens-rtw", "bags", "mens-bags", "slg", "mens-slg", "travel", "mens-travel", "acc", "mens-acc", "linea-rossa", "beauty", "fragrances", "fine-jewelry", "all"],
        default="all",
        help="Rebuild only one Prada segment (keeps others from existing catalog)",
    )
    ap.add_argument(
        "--force-translate",
        action="store_true",
        help="Ignore translate cache and re-run Google Translate",
    )
    ap.add_argument(
        "--offline",
        action="store_true",
        help="Do not call external translate APIs (curated + phrase maps only)",
    )
    args = ap.parse_args()
    only = args.only

    global _FORCE_TRANSLATE, _OFFLINE_TRANSLATE, _KO
    if args.force_translate:
        _FORCE_TRANSLATE = True
        print("force-translate: refreshing curated Korean copy", flush=True)
    if args.offline:
        _OFFLINE_TRANSLATE = True
        print("offline translate mode", flush=True)
    elif args.force_translate and only in {"shoes", "mens-shoes"}:
        # Shoes use curated offline maps (API often 429s).
        _OFFLINE_TRANSLATE = True
        print("offline translate mode (shoes)", flush=True)

    rows: list[dict] = []
    if only in {"all", "bags"} and RAW_BAGS.exists():
        bags = json.loads(RAW_BAGS.read_text()).get("products") or []
        for r in bags:
            r = dict(r)
            r["_kind"] = "handbag"
            rows.append(r)
    if only in {"all", "bags", "mens-bags"} and RAW_MEN_BAGS.exists():
        men_bags = json.loads(RAW_MEN_BAGS.read_text()).get("products") or []
        for r in men_bags:
            r = dict(r)
            r["_kind"] = "mens-handbag"
            rows.append(r)
    if only in {"all", "rtw"} and RAW_RTW.exists():
        rtw = json.loads(RAW_RTW.read_text()).get("products") or []
        for r in rtw:
            r = dict(r)
            r["_kind"] = "rtw"
            rows.append(r)
    mens_rtw_rows: list[dict] = []
    if only in {"all", "mens-rtw"} and RAW_MENS_RTW.exists():
        mens_rtw_rows = [
            dict(r) for r in (json.loads(RAW_MENS_RTW.read_text()).get("products") or [])
        ]
        for r in mens_rtw_rows:
            r["_kind"] = "mens-rtw"
            rows.append(r)
    if only in {"all", "shoes"} and RAW_SHOES.exists():
        shoes = json.loads(RAW_SHOES.read_text()).get("products") or []
        for r in shoes:
            r = dict(r)
            r["_kind"] = "shoes"
            rows.append(r)
    if only in {"all", "mens-shoes"} and RAW_MENS_SHOES.exists():
        mens_shoes = json.loads(RAW_MENS_SHOES.read_text()).get("products") or []
        for r in mens_shoes:
            r = dict(r)
            r["_kind"] = "mens-shoes"
            rows.append(r)
    slg_rows: list[dict] = []
    if only in {"all", "slg"} and RAW_SLG.exists():
        slg_rows = [
            dict(r) for r in (json.loads(RAW_SLG.read_text()).get("products") or [])
        ]
        for r in slg_rows:
            r["_kind"] = "slg"
    if only in {"all", "mens-slg"} and RAW_MEN_SLG.exists():
        mens_slg = [
            dict(r) for r in (json.loads(RAW_MEN_SLG.read_text()).get("products") or [])
        ]
        for r in mens_slg:
            r["_kind"] = "mens-slg"
            slg_rows.append(r)
    travel_rows: list[dict] = []
    if only in {"all", "travel", "bags"} and RAW_TRAVEL.exists():
        travel_rows = [
            dict(r) for r in (json.loads(RAW_TRAVEL.read_text()).get("products") or [])
        ]
        for r in travel_rows:
            r["_kind"] = "travel"
    if only in {"all", "mens-travel", "bags", "mens-bags"} and RAW_MEN_TRAVEL.exists():
        mens_travel = [
            dict(r) for r in (json.loads(RAW_MEN_TRAVEL.read_text()).get("products") or [])
        ]
        for r in mens_travel:
            r["_kind"] = "mens-travel"
            travel_rows.append(r)
    acc_rows: list[dict] = []
    if only in {"all", "acc"} and RAW_ACC.exists():
        acc_rows = [
            dict(r) for r in (json.loads(RAW_ACC.read_text()).get("products") or [])
        ]
        for r in acc_rows:
            r["_kind"] = "acc"
    if only in {"all", "mens-acc"} and RAW_MEN_ACC.exists():
        men_acc_rows = [
            dict(r) for r in (json.loads(RAW_MEN_ACC.read_text()).get("products") or [])
        ]
        for r in men_acc_rows:
            r["_kind"] = "mens-acc"
        acc_rows.extend(men_acc_rows)
    if only in {"all", "linea-rossa"} and RAW_LINEA.exists():
        linea_rows = [
            dict(r) for r in (json.loads(RAW_LINEA.read_text()).get("products") or [])
        ]
        for r in linea_rows:
            r["_kind"] = "linea-rossa"
        acc_rows.extend(linea_rows)
    if only in {"all", "beauty"} and RAW_BEAUTY.exists():
        beauty_rows = [
            dict(r) for r in (json.loads(RAW_BEAUTY.read_text()).get("products") or [])
        ]
        for r in beauty_rows:
            r["_kind"] = "beauty"
        acc_rows.extend(beauty_rows)
    if only in {"all", "fragrances"} and RAW_FRAGRANCES.exists():
        frag_rows = [
            dict(r) for r in (json.loads(RAW_FRAGRANCES.read_text()).get("products") or [])
        ]
        for r in frag_rows:
            r["_kind"] = "fragrances"
        acc_rows.extend(frag_rows)
    if only in {"all", "fine-jewelry"} and RAW_FINE_JEWELRY.exists():
        fj_rows = [
            dict(r) for r in (json.loads(RAW_FINE_JEWELRY.read_text()).get("products") or [])
        ]
        for r in fj_rows:
            r["_kind"] = "fine-jewelry"
        acc_rows.extend(fj_rows)
    if not rows and not slg_rows and not travel_rows and not acc_rows:
        raise SystemExit(
            "Missing Prada raw catalogues — run scrape-pr-handbags.py, "
            "scrape-pr-mens-handbags.py, scrape-pr-mens-rtw.py, "
            "scrape-pr-womens-rtw.py, scrape-pr-womens-shoes.py, "
            "scrape-pr-mens-shoes.py, "
            "scrape-pr-womens-slg.py, scrape-pr-mens-slg.py, "
            "scrape-pr-womens-travel.py, scrape-pr-mens-travel.py, "
            "scrape-pr-womens-accessories.py, scrape-pr-mens-accessories.py, "
            "scrape-pr-linea-rossa.py, scrape-pr-beauty.py, scrape-pr-fragrances.py, "
            "scrape-pr-fine-jewelry.py first"
        )

    skip_no_price = os.environ.get("PR_SKIP_NO_PRICE_UPDATE", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    no_price_skus = _collect_no_price_skus(rows, slg_rows, travel_rows, acc_rows)
    if skip_no_price and no_price_skus:
        before = len(rows) + len(slg_rows) + len(travel_rows) + len(acc_rows)
        rows = [r for r in rows if _row_has_price(r)]
        slg_rows = [r for r in slg_rows if _row_has_price(r)]
        travel_rows = [r for r in travel_rows if _row_has_price(r)]
        acc_rows = [r for r in acc_rows if _row_has_price(r)]
        after = len(rows) + len(slg_rows) + len(travel_rows) + len(acc_rows)
        print(
            f"PR_SKIP_NO_PRICE_UPDATE: omitted {before - after} SKUs without GBP price",
            flush=True,
        )

    if only in {"all", "shoes", "mens-shoes"}:
        n_seed = seed_shoe_cache(_KO)
        print(f"seeded {n_seed} curated shoe strings", flush=True)
    if only in {"all", "slg", "mens-slg"}:
        n_seed = seed_slg_cache(_KO)
        print(f"seeded {n_seed} curated SLG strings", flush=True)
    if only in {"all", "travel", "mens-travel", "bags", "mens-bags"}:
        n_seed = seed_travel_cache(_KO)
        print(f"seeded {n_seed} curated travel strings", flush=True)
    if only in {"all", "bags", "mens-bags"}:
        n_seed = seed_mens_handbags_cache(_KO)
        print(f"seeded {n_seed} curated mens handbag strings", flush=True)
    if only in {"all", "mens-rtw"}:
        n_seed = seed_mens_rtw_cache(_KO)
        print(f"seeded {n_seed} curated mens RTW strings", flush=True)
        if mens_rtw_rows and not _OFFLINE_TRANSLATE:
            pretranslate_unique(_collect_row_strings(mens_rtw_rows))
    if only in {"all", "acc", "mens-acc"}:
        n_seed = seed_accessories_cache(_KO)
        print(f"seeded {n_seed} curated accessories strings", flush=True)
    if only in {"all", "linea-rossa"}:
        n_seed = seed_linea_rossa_cache(_KO)
        print(f"seeded {n_seed} curated Linea Rossa strings", flush=True)
        n_seed = seed_accessories_cache(_KO)
        print(f"seeded {n_seed} curated accessories strings", flush=True)
    if only in {"all", "beauty"}:
        n_seed = seed_beauty_cache(_KO)
        print(f"seeded {n_seed} curated Beauty strings", flush=True)
    if only in {"all", "fragrances"}:
        n_seed = seed_fragrances_cache(_KO)
        print(f"seeded {n_seed} curated Fragrance strings", flush=True)
        n_seed = seed_linea_rossa_cache(_KO)
        print(f"seeded {n_seed} curated Linea Rossa strings", flush=True)
    if only in {"all", "fine-jewelry"}:
        n_seed = seed_fine_jewelry_cache(_KO)
        print(f"seeded {n_seed} curated Fine Jewelry strings", flush=True)
    prev_by_sku: dict[str, dict] = {}
    existing: list[dict] = []
    if OUT_JSON.exists():
        existing = json.loads(OUT_JSON.read_text())
        for p in existing:
            if p.get("sku"):
                prev_by_sku[str(p["sku"])] = p

    # When force-translating shoes, drop cache for every English source string
    # used by the shoe raw catalogue so titles/descriptions re-run through gtx.
    if args.force_translate and only in {"shoes", "mens-shoes"}:
        # Keep good description translations; drop weak ones and re-seed curated.
        dropped = 0
        for k in list(_KO.keys()):
            if en_ratio(str(_KO[k])) >= 0.40:
                _KO.pop(k, None)
                dropped += 1
        print(f"cleared {dropped} weak cache entries for shoe retranslate", flush=True)
        n_seed = seed_shoe_cache(_KO)
        print(f"seeded {n_seed} curated shoe strings", flush=True)
    if args.force_translate and only in {"slg", "mens-slg"}:
        dropped = purge_weak_cache()
        print(f"cleared {dropped} weak cache entries for SLG retranslate", flush=True)
        n_seed = seed_slg_cache(_KO)
        print(f"re-seeded {n_seed} curated SLG strings", flush=True)
    if args.force_translate and only in {"travel", "mens-travel", "bags"}:
        dropped = purge_weak_cache()
        print(f"cleared {dropped} weak cache entries for travel retranslate", flush=True)
        n_seed = seed_travel_cache(_KO)
        print(f"re-seeded {n_seed} curated travel strings", flush=True)
    if args.force_translate and only in {"acc", "mens-acc", "linea-rossa"}:
        dropped = purge_weak_cache()
        print(f"cleared {dropped} weak cache entries for accessories retranslate", flush=True)
        n_seed = seed_accessories_cache(_KO)
        print(f"re-seeded {n_seed} curated accessories strings", flush=True)
        if only in {"linea-rossa", "all"}:
            n_seed = seed_linea_rossa_cache(_KO)
            print(f"re-seeded {n_seed} curated Linea Rossa strings", flush=True)

    now_iso = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )

    products: list[dict] = []
    seen: set[str] = set()
    for i, row in enumerate(rows, start=1):
        sku = str(row.get("productCode") or row.get("id") or "")
        kind = row.get("_kind") or row.get("kind") or "handbag"
        if kind in {"womens-rtw", "rtw"}:
            prod = build_rtw_product(row, prev_by_sku.get(sku), now_iso)
        elif kind in {"mens-rtw"}:
            prod = build_mens_rtw_product(row, prev_by_sku.get(sku), now_iso)
        elif kind in {"womens-shoes", "shoes", "mens-shoes"}:
            prod = build_shoes_product(row, prev_by_sku.get(sku), now_iso)
        elif kind in {"womens-slg", "slg", "mens-slg"}:
            continue  # built via build_slg_products below
        elif kind in {"womens-travel", "travel", "mens-travel"}:
            continue  # built via build_travel_products below
        elif kind in {
            "womens-accessories",
            "acc",
            "mens-accessories",
            "mens-acc",
            "linea-rossa",
            "linea",
            "beauty",
            "fragrances",
            "fragrance",
            "fine-jewelry",
            "fine_jewelry",
        }:
            continue  # built via build_accessories_products below
        else:
            prod = build_handbag_product(row, prev_by_sku.get(sku), now_iso)
        if not prod:
            continue
        if prod["id"] in seen:
            continue
        seen.add(prod["id"])
        products.append(prod)
        if i % 25 == 0:
            CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2))
            print(f"built {i}/{len(rows)}", flush=True)
            time.sleep(0.05)

    if slg_rows:
        print(f"building SLG color groups from {len(slg_rows)} SKUs…", flush=True)
        for prod in build_slg_products(slg_rows, prev_by_sku, now_iso):
            if prod["id"] in seen:
                continue
            seen.add(prod["id"])
            products.append(prod)
        print(f"  SLG products={sum(1 for p in products if p.get('category')=='accessories' and 'slg' in (p.get('tags') or []))}", flush=True)

    if travel_rows:
        if not _OFFLINE_TRANSLATE:
            pretranslate_unique(_collect_row_strings(travel_rows))
        print(f"building travel color groups from {len(travel_rows)} SKUs…", flush=True)
        for prod in build_travel_products(travel_rows, prev_by_sku, now_iso):
            if prod["id"] in seen:
                existing_prod = next((p for p in products if p["id"] == prod["id"]), None)
                if existing_prod:
                    merge_prada_product_fields(existing_prod, prod)
                continue
            seen.add(prod["id"])
            products.append(prod)
        print(
            f"  travel products={sum(1 for p in products if 'travel' in (p.get('tags') or []))}",
            flush=True,
        )

    if acc_rows:
        if not _OFFLINE_TRANSLATE:
            pretranslate_unique(_collect_row_strings(acc_rows))
        print(f"building accessories color groups from {len(acc_rows)} SKUs…", flush=True)
        for prod in build_accessories_products(acc_rows, prev_by_sku, now_iso):
            if prod["id"] in seen:
                existing_prod = next((p for p in products if p["id"] == prod["id"]), None)
                if existing_prod:
                    merge_prada_product_fields(existing_prod, prod)
                continue
            seen.add(prod["id"])
            products.append(prod)
        print(
            f"  accessories products={sum(1 for p in products if 'acc' in (p.get('tags') or []))}",
            flush=True,
        )

    if only != "all" and existing:
        if only == "slg":
            merged = [
                p
                for p in existing
                if not (
                    p.get("brand") == "프라다"
                    and p.get("category") == "accessories"
                    and "slg" in (p.get("tags") or [])
                    and "여성" in (p.get("tags") or [])
                )
            ]
            products = merged + products
        elif only == "mens-slg":
            merged = [
                p
                for p in existing
                if not (
                    p.get("brand") == "프라다"
                    and p.get("category") == "accessories"
                    and "slg" in (p.get("tags") or [])
                    and (
                        "남성" in (p.get("tags") or [])
                        or "pr-mens-slg" in (p.get("prCollections") or [])
                        or any(
                            c in MEN_SLG_LEAF_COLLECTIONS
                            for c in (p.get("prCollections") or [])
                        )
                    )
                )
            ]
            products = merged + products
        elif only == "travel":
            merged = [
                p
                for p in existing
                if "pr-women-travel" not in (p.get("prCollections") or [])
                and not any(
                    c in TRAVEL_LEAF_COLLECTIONS
                    for c in (p.get("prCollections") or [])
                )
            ]
            products = merged + products
        elif only == "mens-travel":
            merged = [
                p
                for p in existing
                if not (
                    p.get("brand") == "프라다"
                    and p.get("category") == "bags"
                    and (
                        "pr-men-travel" in (p.get("prCollections") or [])
                        or any(
                            c in MEN_TRAVEL_LEAF_COLLECTIONS
                            for c in (p.get("prCollections") or [])
                        )
                    )
                )
            ]
            products = merged + products
        elif only == "acc":
            merged = [
                p
                for p in existing
                if not (
                    p.get("brand") == "프라다"
                    and p.get("category") == "accessories"
                    and "acc" in (p.get("tags") or [])
                    and "여성" in (p.get("tags") or [])
                )
            ]
            products = merged + products
        elif only == "mens-acc":
            merged = [
                p
                for p in existing
                if not (
                    p.get("brand") == "프라다"
                    and p.get("category") == "accessories"
                    and "acc" in (p.get("tags") or [])
                    and (
                        "남성" in (p.get("tags") or [])
                        or "pr-mens-accessories" in (p.get("prCollections") or [])
                        or any(
                            c in MEN_ACCESSORIES_LEAF_COLLECTIONS
                            for c in (p.get("prCollections") or [])
                        )
                    )
                    and "linea-rossa" not in (p.get("tags") or [])
                    and "pr-linea-rossa" not in (p.get("prCollections") or [])
                )
            ]
            products = merged + products
        elif only == "linea-rossa":
            merged = [
                p
                for p in existing
                if not (
                    p.get("brand") == "프라다"
                    and (
                        "linea-rossa" in (p.get("tags") or [])
                        or "pr-linea-rossa" in (p.get("prCollections") or [])
                        or any(
                            c in LINEA_ROSSA_LEAF_COLLECTIONS
                            for c in (p.get("prCollections") or [])
                        )
                    )
                )
            ]
            by_id = {p["id"]: p for p in merged}
            out = list(merged)
            for prod in products:
                if prod["id"] in by_id:
                    merge_prada_product_fields(by_id[prod["id"]], prod)
                else:
                    by_id[prod["id"]] = prod
                    out.append(prod)
            products = out
        elif only == "beauty":
            new_ids = {p["id"] for p in products}
            merged = [
                p
                for p in existing
                if p["id"] not in new_ids
                and not (
                    p.get("brand") == "프라다"
                    and (
                        "beauty" in (p.get("tags") or [])
                        or "pr-beauty" in (p.get("prCollections") or [])
                        or any(
                            c in BEAUTY_LEAF_COLLECTIONS
                            for c in (p.get("prCollections") or [])
                        )
                        or str(p.get("subcategory") or "").startswith("pr-beauty")
                    )
                )
            ]
            existing_by_id = {p["id"]: p for p in existing}
            out = list(merged)
            for prod in products:
                old = existing_by_id.get(prod["id"])
                if old:
                    merge_prada_product_fields(prod, old)
                out.append(prod)
            products = out
        elif only == "fragrances":
            new_ids = {p["id"] for p in products}
            merged = [
                p
                for p in existing
                if p["id"] not in new_ids
                and not (
                    p.get("brand") == "프라다"
                    and (
                        "fragrances" in (p.get("tags") or [])
                        or "pr-fragrances" in (p.get("prCollections") or [])
                        or any(
                            c in FRAGRANCE_LEAF_COLLECTIONS
                            for c in (p.get("prCollections") or [])
                        )
                        or str(p.get("subcategory") or "").startswith("pr-fragrances")
                    )
                )
            ]
            existing_by_id = {p["id"]: p for p in existing}
            out = list(merged)
            for prod in products:
                old = existing_by_id.get(prod["id"])
                if old:
                    # Keep fragrance as primary; union Linea Rossa / other segment tags.
                    merge_prada_product_fields(prod, old)
                out.append(prod)
            products = out
        elif only == "fine-jewelry":
            new_ids = {p["id"] for p in products}
            merged = [
                p
                for p in existing
                if p["id"] not in new_ids
                and not (
                    p.get("brand") == "프라다"
                    and (
                        "fine-jewelry" in (p.get("tags") or [])
                        or "pr-fine-jewelry" in (p.get("prCollections") or [])
                        or any(
                            c in FINE_JEWELRY_LEAF_COLLECTIONS
                            for c in (p.get("prCollections") or [])
                        )
                        or str(p.get("subcategory") or "").startswith("pr-fine-jewelry")
                    )
                )
            ]
            existing_by_id = {p["id"]: p for p in existing}
            out = list(merged)
            for prod in products:
                old = existing_by_id.get(prod["id"])
                if old:
                    merge_prada_product_fields(prod, old)
                out.append(prod)
            products = out
        elif only == "bags":
            # Replace all Prada bags (women handbags + men handbags + travel)
            merged = [
                p
                for p in existing
                if not (p.get("brand") == "프라다" and p.get("category") == "bags")
            ]
            products = merged + products
        elif only == "mens-bags":
            merged = [
                p
                for p in existing
                if not (
                    p.get("brand") == "프라다"
                    and p.get("category") == "bags"
                    and (
                        "pr-mens-handbags" in (p.get("prCollections") or [])
                        or any(
                            c in MEN_HANDBAG_LEAF_COLLECTIONS
                            for c in (p.get("prCollections") or [])
                        )
                    )
                )
            ]
            products = merged + products
        elif only == "mens-rtw":
            merged = [
                p
                for p in existing
                if not (
                    p.get("brand") == "프라다"
                    and p.get("category") == "luxury"
                    and (
                        "pr-men-rtw" in (p.get("prCollections") or [])
                        or "pr-men" in (p.get("prCollections") or [])
                        or any(
                            c in MENS_RTW_LEAF_COLLECTIONS
                            for c in (p.get("prCollections") or [])
                        )
                    )
                )
            ]
            products = merged + products
        elif only == "shoes":
            merged = [
                p
                for p in existing
                if not (
                    p.get("brand") == "프라다"
                    and p.get("category") == "shoes"
                    and (
                        "pr-women-shoes" in (p.get("prCollections") or [])
                        or any(
                            c in SHOES_LEAF_COLLECTIONS
                            for c in (p.get("prCollections") or [])
                        )
                    )
                )
            ]
            products = merged + products
        elif only == "mens-shoes":
            merged = [
                p
                for p in existing
                if not (
                    p.get("brand") == "프라다"
                    and p.get("category") == "shoes"
                    and (
                        "pr-men-shoes" in (p.get("prCollections") or [])
                        or any(
                            c in MENS_SHOES_LEAF_COLLECTIONS
                            for c in (p.get("prCollections") or [])
                        )
                    )
                )
            ]
            products = merged + products
        else:
            keep_cat = {
                "rtw": "luxury",
                "mens-rtw": "luxury",
            }.get(only, "luxury")
            merged = [p for p in existing if p.get("category") != keep_cat]
            if only == "rtw":
                merged = [
                    p
                    for p in existing
                    if not (
                        p.get("brand") == "프라다"
                        and p.get("category") == "luxury"
                        and (
                            "pr-women-rtw" in (p.get("prCollections") or [])
                            or "pr-women" in (p.get("prCollections") or [])
                            or any(
                                c in RTW_LEAF_COLLECTIONS
                                for c in (p.get("prCollections") or [])
                            )
                        )
                    )
                ]
            products = merged + products

    products.sort(key=lambda p: p["id"])
    if skip_no_price and no_price_skus and existing:
        products = _preserve_no_price_catalog(existing, products, no_price_skus)
    validate_prada_rtw_sizes(products, scope=only)
    products = dedupe_merge_products(products)
    validate_prada_korean(products, scope=only)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n")
    OUT_TS.write_text(
        'import type { Product } from "@/data/products";\n'
        'import data from "./pr-catalog.json";\n\n'
        "/** Auto-generated — Prada women's handbags + travel + RTW + shoes + SLG (GB). */\n"
        "export const prCatalogProducts = data as unknown as Product[];\n"
    )
    CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2))
    print(f"Wrote {len(products)} products → {OUT_JSON}", flush=True)
    bags_n = sum(1 for p in products if p.get("category") == "bags")
    lux_n = sum(1 for p in products if p.get("category") == "luxury")
    shoes_n = sum(1 for p in products if p.get("category") == "shoes")
    acc_n = sum(
        1
        for p in products
        if p.get("category") == "accessories" and p.get("brand") == "프라다"
    )
    print(
        f"  bags={bags_n} luxury/rtw={lux_n} shoes={shoes_n} accessories/slg={acc_n}",
        flush=True,
    )
    for leaf in HANDBAG_LEAF_COLLECTIONS:
        n = sum(1 for p in products if leaf in (p.get("prCollections") or []))
        if n:
            print(f"  {leaf}: {n}", flush=True)
    for leaf in MEN_HANDBAG_LEAF_COLLECTIONS:
        n = sum(1 for p in products if leaf in (p.get("prCollections") or []))
        if n:
            print(f"  {leaf}: {n}", flush=True)
    for leaf in RTW_LEAF_COLLECTIONS:
        n = sum(1 for p in products if leaf in (p.get("prCollections") or []))
        if n:
            print(f"  {leaf}: {n}", flush=True)
    for leaf in MENS_RTW_LEAF_COLLECTIONS:
        n = sum(1 for p in products if leaf in (p.get("prCollections") or []))
        if n:
            print(f"  {leaf}: {n}", flush=True)
    for leaf in SHOES_LEAF_COLLECTIONS:
        n = sum(1 for p in products if leaf in (p.get("prCollections") or []))
        if n:
            print(f"  {leaf}: {n}", flush=True)
    for leaf in MENS_SHOES_LEAF_COLLECTIONS:
        n = sum(1 for p in products if leaf in (p.get("prCollections") or []))
        if n:
            print(f"  {leaf}: {n}", flush=True)
    for leaf in SLG_LEAF_COLLECTIONS:
        n = sum(1 for p in products if leaf in (p.get("prCollections") or []))
        if n:
            print(f"  {leaf}: {n}", flush=True)
    for leaf in TRAVEL_LEAF_COLLECTIONS:
        n = sum(1 for p in products if leaf in (p.get("prCollections") or []))
        if n:
            print(f"  {leaf}: {n}", flush=True)
    for leaf in MEN_TRAVEL_LEAF_COLLECTIONS:
        n = sum(1 for p in products if leaf in (p.get("prCollections") or []))
        if n:
            print(f"  {leaf}: {n}", flush=True)
    for leaf in ACCESSORIES_LEAF_COLLECTIONS:
        n = sum(1 for p in products if leaf in (p.get("prCollections") or []))
        if n:
            print(f"  {leaf}: {n}", flush=True)
    for leaf in MEN_ACCESSORIES_LEAF_COLLECTIONS:
        n = sum(1 for p in products if leaf in (p.get("prCollections") or []))
        if n:
            print(f"  {leaf}: {n}", flush=True)
    for leaf in LINEA_ROSSA_LEAF_COLLECTIONS:
        n = sum(1 for p in products if leaf in (p.get("prCollections") or []))
        if n:
            print(f"  {leaf}: {n}", flush=True)
    for leaf in BEAUTY_LEAF_COLLECTIONS:
        n = sum(1 for p in products if leaf in (p.get("prCollections") or []))
        if n:
            print(f"  {leaf}: {n}", flush=True)
    for leaf in FRAGRANCE_LEAF_COLLECTIONS:
        n = sum(1 for p in products if leaf in (p.get("prCollections") or []))
        if n:
            print(f"  {leaf}: {n}", flush=True)
    for leaf in FINE_JEWELRY_LEAF_COLLECTIONS:
        n = sum(1 for p in products if leaf in (p.get("prCollections") or []))
        if n:
            print(f"  {leaf}: {n}", flush=True)

    verify = subprocess.run(
        [sys.executable, str(SCRIPTS / "verify-product-images.py"), "--brand", "pr"],
        cwd=str(ROOT),
        check=False,
    )
    if verify.returncode != 0:
        raise SystemExit("Prada catalog image verify failed — fix before shipping.")

    if only in {"all", "rtw", "mens-rtw"}:
        size_verify = subprocess.run(
            [sys.executable, str(SCRIPTS / "verify-pr-rtw-sizes.py")],
            cwd=str(ROOT),
            check=False,
        )
        if size_verify.returncode != 0:
            raise SystemExit(
                "Prada RTW size verify failed — mixed letter+numeric sizes detected."
            )
        # Ensure Short (…S) size-guide tabs/notes are present after any merge path.
        short_patch = subprocess.run(
            [sys.executable, str(SCRIPTS / "patch-pr-rtw-short-size-charts.py")],
            cwd=str(ROOT),
            check=False,
        )
        if short_patch.returncode != 0:
            raise SystemExit("Prada RTW Short size-chart patch failed.")


if __name__ == "__main__":
    main()
