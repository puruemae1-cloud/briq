#!/usr/bin/env python3
"""Build Chanel catalogue → src/data/ch/ch-catalog.json + ch-catalog.ts.

Sources:
  - ch-rtw-catalog-raw.json → category luxury (RTW)
  - ch-handbags-catalog-raw.json → category bags
  - ch-slg-catalog-raw.json → category accessories (small leather goods)
  - ch-shoes-catalog-raw.json → category shoes
  - ch-jewellery-catalog-raw.json → category accessories
  - ch-high-jewellery-catalog-raw.json → category accessories (High Jewellery)
  - ch-fine-jewellery-catalog-raw.json → category accessories (Fine Jewellery)
  - ch-sunglasses-catalog-raw.json → category accessories (sunglasses)
  - ch-fragrance-catalog-raw.json → category accessories (fragrance)
  - ch-makeup-catalog-raw.json → category accessories (makeup)
  - ch-other-acc-catalog-raw.json → category accessories (other accessories)
  - ch-watches-catalog-raw.json → category watches (J12 / Première / BOY·FRIEND / Monsieur / Code Coco)

Pricing (same as Gucci): KRW = round_만원(GBP × 2100 × 1.05 × 1.15)
Korean copy via gtx + ch-translate-cache.json.
RTW size chart: French FR 34–50. Handbags / SLG: One Size + dimensions in copy.
Shoes: EU (French) sizes as shown on chanel.com GB PDPs.
Costume jewellery: mostly One Size (UNI); rings use French ring sizes + chart.
Sunglasses: One Size + official frame measurements (mm) in copy.
Fragrance: One Size (volume is in the official product name).
Makeup: One Size (shade is in the official product name / colour).
Other accessories: belts numeric cm; hats S/M/L head-circ; most UNI.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from ch_hybris_details import compose_official_name  # noqa: E402

RAW_PATH = ROOT / "src/data/ch/ch-rtw-catalog-raw.json"
HANDBAGS_RAW_PATH = ROOT / "src/data/ch/ch-handbags-catalog-raw.json"
SLG_RAW_PATH = ROOT / "src/data/ch/ch-slg-catalog-raw.json"
SHOES_RAW_PATH = ROOT / "src/data/ch/ch-shoes-catalog-raw.json"
JEWELLERY_RAW_PATH = ROOT / "src/data/ch/ch-jewellery-catalog-raw.json"
HIGH_JEWELLERY_RAW_PATH = ROOT / "src/data/ch/ch-high-jewellery-catalog-raw.json"
FINE_JEWELLERY_RAW_PATH = ROOT / "src/data/ch/ch-fine-jewellery-catalog-raw.json"
SUNGLASSES_RAW_PATH = ROOT / "src/data/ch/ch-sunglasses-catalog-raw.json"
FRAGRANCE_RAW_PATH = ROOT / "src/data/ch/ch-fragrance-catalog-raw.json"
MAKEUP_RAW_PATH = ROOT / "src/data/ch/ch-makeup-catalog-raw.json"
OTHER_ACC_RAW_PATH = ROOT / "src/data/ch/ch-other-acc-catalog-raw.json"
WATCHES_RAW_PATH = ROOT / "src/data/ch/ch-watches-catalog-raw.json"
OUT_JSON = ROOT / "src/data/ch/ch-catalog.json"
OUT_TS = ROOT / "src/data/ch/ch-catalog.ts"
CACHE_PATH = ROOT / "src/data/ch/ch-translate-cache.json"

SHAPE_LEAVES = [
    "ch-women-jackets",
    "ch-women-dresses",
    "ch-women-blouses-tops",
    "ch-women-cardigans-sweaters",
    "ch-women-skirts",
    "ch-women-trousers-shorts",
    "ch-women-swimwear",
    "ch-women-outerwear",
]

PARENT_COLS = ["chanel", "ch-women", "ch-women-rtw", "ch-women-looks"]

BAG_SHAPE_LEAVES = [
    "ch-women-flap-bags",
    "ch-women-hobo-bags",
    "ch-women-tote-bowling-bags",
    "ch-women-bucket-bags",
    "ch-women-backpacks",
    "ch-women-evening-bags",
    "ch-women-mini-bags",
]

BAG_PARENT_COLS = ["chanel", "chanel-bags", "ch-handbags"]

SLG_SHAPE_LEAVES = [
    "ch-women-wallets-on-chain",
    "ch-women-micro-bags",
    "ch-women-vanity",
    "ch-women-card-holders-wallets",
    "ch-women-pouches-cases",
    "ch-women-leather-accessories",
]

SLG_PARENT_COLS = ["chanel", "chanel-accessories", "ch-slg"]

SHOE_SHAPE_LEAVES = [
    "ch-women-pumps-slingbacks",
    "ch-women-ballet-mary-janes",
    "ch-women-elegant-sandals",
    "ch-women-casual-sandals",
    "ch-women-loafers",
    "ch-women-boots",
    "ch-women-sneakers",
]

SHOE_PARENT_COLS = ["chanel", "chanel-shoes", "ch-shoes"]

JEWELLERY_SHAPE_LEAVES = [
    "ch-women-earrings",
    "ch-women-necklaces",
    "ch-women-bracelets-cuffs",
    "ch-women-brooches",
    "ch-women-rings",
]

JEWELLERY_PARENT_COLS = ["chanel", "chanel-accessories", "ch-jewellery"]

HIGH_JEWELLERY_LEAF = "ch-high-jewellery"
HIGH_JEWELLERY_PARENT_COLS = ["chanel", "chanel-accessories", HIGH_JEWELLERY_LEAF]

FINE_JEWELLERY_LEAF = "ch-fine-jewellery"
FINE_JEWELLERY_PARENT_COLS = ["chanel", "chanel-accessories", FINE_JEWELLERY_LEAF]

SUNGLASSES_LEAF = "ch-women-sunglasses"
SUNGLASSES_PARENT_COLS = ["chanel", "chanel-accessories", "ch-sunglasses", SUNGLASSES_LEAF]

FRAGRANCE_LEAF = "ch-fragrance"
FRAGRANCE_PARENT_COLS = ["chanel", "chanel-accessories", FRAGRANCE_LEAF]

MAKEUP_GROUP_IDS = [
    "ch-makeup-complexion",
    "ch-makeup-eyes",
    "ch-makeup-lips",
    "ch-makeup-nails",
    "ch-makeup-brushes",
]
MAKEUP_SHAPE_LEAVES = [
    "ch-makeup-foundations",
    "ch-makeup-base",
    "ch-makeup-healthy-glow",
    "ch-makeup-blush",
    "ch-makeup-powders",
    "ch-makeup-bronzers",
    "ch-makeup-concealer",
    "ch-makeup-highlighter",
    "ch-makeup-eyeshadows",
    "ch-makeup-mascara",
    "ch-makeup-brows",
    "ch-makeup-eyeliners",
    "ch-makeup-eye-palette",
    "ch-makeup-lip-gloss",
    "ch-makeup-lipsticks",
    "ch-makeup-lip-pencils",
    "ch-makeup-lip-balms",
    "ch-makeup-liquid-lipsticks",
    "ch-makeup-manicure",
    "ch-makeup-nail-colour",
    "ch-makeup-eye-brushes",
    "ch-makeup-complexion-brushes",
    "ch-makeup-lip-brushes",
    *MAKEUP_GROUP_IDS,
]
MAKEUP_PARENT_COLS = ["chanel", "chanel-accessories", "ch-makeup"]

OTHER_ACC_SHAPE_LEAVES = [
    "ch-women-headwear",
    "ch-women-belts",
    "ch-women-scarves",
    "ch-women-camellias",
    "ch-women-winter-accessories",
    "ch-women-summer-accessories",
]

OTHER_ACC_PARENT_COLS = ["chanel", "chanel-accessories", "ch-other-accessories"]

WATCH_SHAPE_LEAVES = [
    "ch-watches-j12",
    "ch-watches-premiere",
    "ch-watches-boy-friend",
    "ch-watches-monsieur",
    "ch-watches-code-coco",
]
WATCH_PARENT_COLS = ["chanel-watches", "ch-watches"]

# Chanel costume jewellery PDPs mostly use UNI (One Size). Rings that expose
# numeric sizes follow French ring sizing (finger circumference ≈ FR number).
# Chanel.com fashion PDPs surface the WFJ-style finger-circumference guide;
# Briq keeps FR as the picker label to match French maison convention.
CH_RING_SIZE_ROWS = [
    # FR, UK, US, INNER CIRC (MM), KR (MM)
    ["44", "F", "3", "44", "44"],
    ["45", "F½", "3.25", "45", "45"],
    ["46", "G", "3.75", "46", "46"],
    ["47", "H", "4", "47", "47"],
    ["48", "I", "4.5", "48", "48"],
    ["49", "J", "5", "49", "49"],
    ["50", "K", "5.25", "50", "50"],
    ["51", "L", "5.75", "51", "51"],
    ["52", "L½", "6", "52", "52"],
    ["53", "M", "6.5", "53", "53"],
    ["54", "N", "6.75", "54", "54"],
    ["55", "O", "7.25", "55", "55"],
    ["56", "P", "7.5", "56", "56"],
    ["57", "Q", "8", "57", "57"],
    ["58", "Q½", "8.25", "58", "58"],
    ["59", "R", "8.75", "59", "59"],
    ["60", "S", "9", "60", "60"],
    ["61", "T", "9.5", "61", "61"],
    ["62", "U", "10", "62", "62"],
    ["63", "V", "10.25", "63", "63"],
    ["64", "V½", "10.75", "64", "64"],
    ["65", "W", "11", "65", "65"],
]

CH_RING_SIZE_CHART = {
    "id": "ch-women-rings",
    "titleKo": "샤넬 링 사이즈 가이드",
    "noteKo": (
        "샤넬 코스튬 주얼리 링은 프랑스(FR) 링 사이즈를 기준으로 합니다. "
        "Briq 사이즈 선택란의 FR 52·FR 54 등은 공홈 제품 사이즈와 대응하며, "
        "INNER CIRC / KR(mm)은 손가락 둘레(㎜) 참고값입니다. 중간 사이즈일 경우 "
        "더 큰 쪽을 권장합니다. 스타일에 따라 핏이 다를 수 있으니 참고용으로 "
        "확인해 주세요."
    ),
    "headers": ["FR", "UK", "US", "INNER CIRC (MM)", "KR (MM)"],
    "rows": CH_RING_SIZE_ROWS,
}

# Chanel eyewear PDPs publish frame measurements (lens / bridge / temple / …).
# Products are One Size; the chart explains how to read those mm values.
CH_EYEWEAR_SIZE_CHART = {
    "id": "ch-women-sunglasses",
    "titleKo": "샤넬 선글라스 프레임 사이즈 가이드",
    "noteKo": (
        "샤넬 선글라스는 공홈과 같이 원 사이즈로 판매되며, 제품별 프레임 치수"
        "(렌즈 폭·브릿지·템플·프레임 높이·프론트 폭)가 밀리미터(mm)로 표기됩니다. "
        "Briq 상품 설명의 사이즈 항목은 공홈 PDP의 mm 값을 따릅니다."
    ),
    "headers": ["항목", "의미", "단위"],
    "rows": [
        ["렌즈 폭", "Lens width — 한쪽 렌즈의 가로 폭", "mm"],
        ["브릿지", "Bridge — 코 위 브릿지 폭", "mm"],
        ["템플", "Temple — 다리(템플) 길이", "mm"],
        ["프레임 높이", "Height — 프레임/렌즈 세로 높이", "mm"],
        ["프론트 폭", "Front width — 프레임 전체 가로 폭", "mm"],
    ],
}

# Chanel.com does not publish a public belt conversion table; GB PDPs use
# numeric cm sizes (typically 65–120). Labels match the official size picker.
CH_BELT_SIZE_CHART = {
    "id": "ch-women-belts",
    "titleKo": "샤넬 벨트 사이즈 가이드",
    "noteKo": (
        "샤넬 벨트 사이즈는 공홈과 같이 센티미터(cm)로 표기됩니다. "
        "Briq 사이즈 선택란의 숫자는 chanel.com GB PDP의 사이즈와 동일합니다. "
        "chanel.com은 별도의 국가별 환산표를 공개하지 않으므로 cm 표기를 그대로 "
        "사용합니다. 중간 사이즈일 경우 더 큰 쪽을 권장합니다."
    ),
    "headers": ["SIZE (CM)"],
    "rows": [
        ["65"],
        ["70"],
        ["75"],
        ["80"],
        ["85"],
        ["90"],
        ["95"],
        ["100"],
        ["105"],
        ["110"],
        ["115"],
        ["120"],
    ],
}

# Head-circumference reference for lettered hat sizes (same bands as Gucci).
CH_HAT_SIZE_CHART = {
    "id": "ch-women-headwear",
    "titleKo": "샤넬 헤드웨어 사이즈 가이드",
    "noteKo": (
        "머리 둘레(cm) 참고표입니다. 샤넬 공홈 모자는 주로 S / M / L로 판매됩니다. "
        "스타일·소재에 따라 핏이 다를 수 있으니 중간 사이즈일 경우 더 큰 쪽을 "
        "권장합니다."
    ),
    "headers": ["SIZE", "머리 둘레 (CM)", "머리 둘레 (IN)"],
    "rows": [
        ["S", "55–56", "21.7–22"],
        ["M", "57–58", "22.4–22.8"],
        ["L", "59–60", "23.2–23.6"],
    ],
}

# Chanel GB shoe PDPs use French/EU numeric sizes (34–42, half sizes).
# Conversion follows standard French women's EU ↔ UK/US ↔ KR(mm)/JP(cm).
# chanel.com does not publish a public shoes conversion table; EU labels match
# the orliSize values shown on official product pages.
CH_WOMEN_SHOES_ROWS = [
    # EU, UK, US, KR(mm), JP(cm)
    ["34", "1", "4", "210", "21"],
    ["34.5", "1.5", "4.5", "215", "21.5"],
    ["35", "2", "5", "220", "22"],
    ["35.5", "2.5", "5.5", "225", "22.5"],
    ["36", "3", "6", "230", "23"],
    ["36.5", "3.5", "6.5", "235", "23.5"],
    ["37", "4", "7", "240", "24"],
    ["37.5", "4.5", "7.5", "245", "24.5"],
    ["38", "5", "8", "250", "25"],
    ["38.5", "5.5", "8.5", "255", "25.5"],
    ["39", "6", "9", "260", "26"],
    ["39.5", "6.5", "9.5", "265", "26.5"],
    ["40", "7", "10", "270", "27"],
    ["40.5", "7.5", "10.5", "275", "27.5"],
    ["41", "8", "11", "280", "28"],
    ["41.5", "8.5", "11.5", "285", "28.5"],
    ["42", "9", "12", "290", "29"],
]

CH_WOMEN_SHOES_SIZE_CHART = {
    "id": "ch-women-shoes",
    "titleKo": "샤넬 여성 슈즈 사이즈 가이드",
    "noteKo": (
        "샤넬 슈즈는 공홈(chanel.com) 제품 페이지와 동일하게 프랑스/유럽(EU) 사이즈를 "
        "사용합니다. Briq 사이즈 선택란의 EU 38·EU 38.5 등은 공홈에 표기된 사이즈와 "
        "같습니다. UK·US·KR(mm)·JP(cm)은 표준 프랑스 여성 슈즈 환산이며, 스타일·소재에 "
        "따라 핏이 다를 수 있으니 참고용으로 확인해 주세요."
    ),
    "headers": ["EU", "UK", "US", "KR (MM)", "JP (CM)"],
    "rows": CH_WOMEN_SHOES_ROWS,
}

# French women's RTW conversion (Chanel FR sizes). Body measures are approximate
# maison / industry references for shopper guidance.
CH_WOMEN_RTW_SIZE_CHART = {
    "id": "ch-women-rtw",
    "titleKo": "샤넬 여성 레디투웨어 사이즈 가이드",
    "noteKo": (
        "샤넬 레디투웨어는 프랑스(FR) 사이즈를 기준으로 합니다. Briq 사이즈 선택란의 "
        "FR 34·36 등은 제품에 표기된 사이즈와 동일합니다. 브랜드·시즌·실루엣에 따라 "
        "핏이 다를 수 있으니 참고용으로 확인해 주세요."
    ),
    "headers": [
        "FR",
        "IT",
        "UK",
        "US",
        "BUST (CM)",
        "WAIST (CM)",
        "HIP (CM)",
    ],
    "rows": [
        ["34", "38", "6", "2", "80", "62", "86"],
        ["36", "40", "8", "4", "84", "66", "90"],
        ["38", "42", "10", "6", "88", "70", "94"],
        ["40", "44", "12", "8", "92", "74", "98"],
        ["42", "46", "14", "10", "96", "78", "102"],
        ["44", "48", "16", "12", "100", "82", "106"],
        ["46", "50", "18", "14", "104", "86", "110"],
        ["48", "52", "20", "16", "108", "90", "114"],
        ["50", "54", "22", "18", "112", "94", "118"],
    ],
    "tabs": [
        {
            "id": "fr",
            "labelKo": "FR 사이즈",
            "headers": [
                "FR",
                "IT",
                "UK",
                "US",
                "BUST (CM)",
                "WAIST (CM)",
                "HIP (CM)",
            ],
            "rows": [
                ["34", "38", "6", "2", "80", "62", "86"],
                ["36", "40", "8", "4", "84", "66", "90"],
                ["38", "42", "10", "6", "88", "70", "94"],
                ["40", "44", "12", "8", "92", "74", "98"],
                ["42", "46", "14", "10", "96", "78", "102"],
                ["44", "48", "16", "12", "100", "82", "106"],
                ["46", "50", "18", "14", "104", "86", "110"],
                ["48", "52", "20", "16", "108", "90", "114"],
                ["50", "54", "22", "18", "112", "94", "118"],
            ],
        }
    ],
}


def gbp_to_krw(gbp: float | None) -> int:
    """KRW = round_만원(GBP × 2100 × 1.05 × 1.15)."""
    if gbp is None:
        return 0
    base = float(gbp) * 2100 * 1.05 * 1.15
    return int(round(base / 10_000) * 10_000)


_KO: dict[str, str] = {}
if CACHE_PATH.exists():
    try:
        _KO = json.loads(CACHE_PATH.read_text())
    except Exception:
        _KO = {}


def en_ratio(s: str) -> float:
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return 0.0
    latin = sum(1 for c in letters if ("A" <= c <= "Z") or ("a" <= c <= "z"))
    return latin / len(letters)


def gtx(text: str) -> str:
    q = urllib.parse.quote(text[:4500])
    url = (
        "https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl=en&tl=ko&dt=t&q={q}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=35) as r:
        data = json.loads(r.read().decode())
    return "".join(part[0] for part in data[0] if part and part[0])


# Exact / phrase glossary applied on EN source before MT (avoids bad gtx like Cuff→동).
_EN_TITLE_KO = {
    "Clip-on Pendant Earrings": "클립온 펜던트 이어링",
    "Pendant Earrings": "펜던트 이어링",
    "Stud Earrings": "스터드 이어링",
    "Hoop Earrings": "후프 이어링",
    "Earrings": "이어링",
    "Earring": "이어링",
    "Necklaces": "네크리스",
    "Necklace": "네크리스",
    "Choker": "초커",
    "Bracelets & Cuffs": "브레이슬릿 & 커프",
    "Bracelets": "브레이슬릿",
    "Bracelet": "브레이슬릿",
    "Cuffs": "커프",
    "Cuff": "커프",
    "Brooches": "브로치",
    "Brooch": "브로치",
    "Rings": "링",
    "Ring": "링",
    "Bouton de Camélia": "부통 드 카멜리아",
    "Bouton de Camelia": "부통 드 카멜리아",
    "Extrait de Camélia": "엑스트레 드 카멜리아",
    "Extrait de Camelia": "엑스트레 드 카멜리아",
    "Fil de Camélia": "필 드 카멜리아",
    "Fil de Camelia": "필 드 카멜리아",
    "Camélia": "카멜리아",
    "Camelia": "카멜리아",
    "Crawling Earrings": "크롤링 이어링",
    "Supple Choker": "서플 초커",
    "Transformable Earrings": "트랜스포머블 이어링",
    "Transformable": "트랜스포머블",
    "Plume de CHANEL": "플룸 드 샤넬",
    "Plume de Chanel": "플룸 드 샤넬",
    "High Jewellery": "High 주얼리",
    "Fine Jewellery": "Fine 주얼리",
    "Watches": "시계",
    "J12": "J12",
    "Première": "프리미에르",
    "Premiere": "프리미에르",
    "BOY·FRIEND": "보이·프렌드",
    "BOY.FRIEND": "보이·프렌드",
    "Boy·Friend": "보이·프렌드",
    "Monsieur": "무슈",
    "Code Coco": "코드 코코",
    "Calibre": "칼리버",
    "Ceramic": "세라믹",
    "Matte": "매트",
    "Superleggera": "수퍼레제라",
    "Sunglasses": "선글라스",
    "Fragrance": "향수",
    "Makeup": "메이크업",
    "Base": "베이스",
    "Eyes": "아이",
    "Lips": "립",
    "Complexion": "컴플렉션",
    "Foundations": "파운데이션",
    "Foundation": "파운데이션",
    "Healthy Glow Makeup": "헬시 글로우",
    "Blush": "블러시",
    "Powders": "파우더",
    "Powder": "파우더",
    "Bronzers": "브론저",
    "Bronzer": "브론저",
    "Concealer": "컨실러",
    "Highlighter": "하이라이터",
    "Eyeshadows": "아이섀도우",
    "Eyeshadow": "아이섀도우",
    "Mascara": "마스카라",
    "Brows": "브로우",
    "Eyeliners": "아이라이너",
    "Eyeliner": "아이라이너",
    "Eye Palette": "아이 팔레트",
    "Lip Gloss": "립글로스",
    "Lipsticks": "립스틱",
    "Lipstick": "립스틱",
    "Lip Pencils": "립펜슬",
    "Lip Pencil": "립펜슬",
    "Lip Balms and Lip Care": "립밤 & 립케어",
    "Lip Balm": "립밤",
    "Liquid Lipsticks": "리퀴드 립스틱",
    "Liquid Lipstick": "리퀴드 립스틱",
    "Nails": "네일",
    "Manicure": "매니큐어",
    "Nail Colour": "네일 컬러",
    "Brushes & Accessories": "브러시 & 액세서리",
    "Eye Brushes": "아이 브러시",
    "Complexion Brushes": "컴플렉션 브러시",
    "Lip Brushes": "립 브러시",
    "ROUGE COCO": "루쥬 코코",
    "Rouge Coco": "루쥬 코코",
    "ROUGE COCO FLASH": "루쥬 코코 플래시",
    "Rouge Coco Flash": "루쥬 코코 플래시",
    "ROUGE COCO BLOOM": "루쥬 코코 블룸",
    "Rouge Coco Bloom": "루쥬 코코 블룸",
    "ROUGE COCO BAUME": "루쥬 코코 봄",
    "Rouge Coco Baume": "루쥬 코코 봄",
    "LES BEIGES": "레 베쥬",
    "Les Beiges": "레 베쥬",
    "LE VERNIS": "르 베르니",
    "Le Vernis": "르 베르니",
    "LE VOLUME": "르 볼륨",
    "Le Volume": "르 볼륨",
    "LE VOLUME RÉVOLUTION": "르 볼륨 레볼루션",
    "Le Volume Révolution": "르 볼륨 레볼루션",
    "INIMITABLE": "이니미타블",
    "Inimitable": "이니미타블",
    "ROUGE ALLURE": "루쥬 알뤼르",
    "Rouge Allure": "루쥬 알뤼르",
    "ULTRA LE TEINT": "울트라 르 탱",
    "Ultra Le Teint": "울트라 르 탱",
    "LE LIFT": "르 리프트",
    "Le Lift": "르 리프트",
    "VITALUMIÈRE": "비탈뤼미에르",
    "Vitalumière": "비탈뤼미에르",
    "JOUES CONTRASTE": "주 콩트라스트",
    "Joues Contraste": "주 콩트라스트",
    "LE BLANC": "르 블랑",
    "Le Blanc": "르 블랑",
    "LE CORRECTEUR": "르 코렉퇴르",
    "Le Correcteur": "르 코렉퇴르",
    "STYLO YEUX": "스틸로 이외",
    "Stylo Yeux": "스틸로 이외",
    "STYLO SOURCILS": "스틸로 수르실",
    "Stylo Sourcils": "스틸로 수르실",
    "LA LIGNE GRAPHIQUE": "라 린 그라피크",
    "La Ligne Graphique": "라 린 그라피크",
    "LE LINER": "르 라이너",
    "Le Liner": "르 라이너",
    "LE ROUGE DUO ULTRA TENUE": "르 루쥬 듀오 울트라 트뉘",
    "Le Rouge Duo Ultra Tenue": "르 루쥬 듀오 울트라 트뉘",
    "PINCEAU": "팽소",
    "Pinceau": "팽소",
    "MIROIR": "미루아르",
    "Miroir": "미루아르",
    "Longwear": "롱웨어",
    "Satin Lipstick": "사틴 립스틱",
    "Hydrating and Smoothing Lip Care": "수분·스무딩 립케어",
    "Eau de Parfum": "오 드 빠르펭",
    "Eau de Toilette": "오 드 뚜알렛",
    "Eau de Cologne": "오 드 코롱",
    "Eau de Parfum Spray": "오 드 빠르펭 스프레이",
    "Eau de Toilette Spray": "오 드 뚜알렛 스프레이",
    "Parfum": "빠르펭",
    "Extrait": "엑스트레",
    "Les Exclusifs de CHANEL": "레 젝스클루시프 드 샤넬",
    "Les Eaux de CHANEL": "레 조 드 샤넬",
    "COCO MADEMOISELLE": "코코 마드모아젤",
    "Coco Mademoiselle": "코코 마드모아젤",
    "BLEU DE CHANEL": "블루 드 샤넬",
    "Bleu de Chanel": "블루 드 샤넬",
    "GABRIELLE CHANEL": "가브리엘 샤넬",
    "ALLURE HOMME SPORT": "알뤼르 옴 스포츠",
    "ALLURE HOMME": "알뤼르 옴",
    "CHANCE EAU SPLENDIDE": "샹스 오 스플랑디드",
    "CHANCE EAU TENDRE": "샹스 오 땅드르",
    "CHANCE EAU FRAÎCHE": "샹스 오 프레슈",
    "CHANCE EAU FRAICHE": "샹스 오 프레슈",
    "CHANCE": "샹스",
    "Body Oil": "바디 오일",
    "Body Lotion": "바디 로션",
    "Hair Mist": "헤어 미스트",
    "Shower Gel": "샤워 젤",
    "Moisturising Body Cream": "모이스처라이징 바디 크림",
    "Moisturizing Body Cream": "모이스처라이징 바디 크림",
    "Hand Cream": "핸드 크림",
    "Twist and Spray": "트위스트 앤 스프레이",
    "Eyeglasses": "안경",
    "Optical": "옵티컬",
    "Blue Light Glasses": "블루라이트 글라스",
    "Oval Eyeglasses": "오벌 안경",
    "Cat Eye": "캣아이",
    "Butterfly": "버터플라이",
    "Rectangle": "렉탱글",
    "Square": "스퀘어",
    "Pilot": "파일럿",
    "Pantos": "판토스",
    "Shield": "실드",
    "Acetate": "아세테이트",
    "Case": "케이스",
    "Bezel": "베젤",
    "Crown": "크라운",
    "Dial": "다이얼",
    "Strap": "스트랩",
    "Movement": "무브먼트",
    "Functions": "기능",
    "Water-resistance": "방수",
    "Diamonds": "다이아몬드",
    "Material": "소재",
    "Lens width": "렌즈 너비",
    "Lens height": "렌즈 높이",
    "Frame width": "프레임 너비",
    "Branch length": "템플 길이",
    "highly resistant ceramic": "고강도 세라믹",
    "Highly resistant white ceramic and steel": "고강도 화이트 세라믹과 스틸",
    "Highly resistant black ceramic and steel": "고강도 블랙 세라믹과 스틸",
    "Highly resistant ceramic and steel": "고강도 세라믹과 스틸",
    "white ceramic and steel": "화이트 세라믹과 스틸",
    "black ceramic and steel": "블랙 세라믹과 스틸",
    "Yellow gold and diamonds": "옐로우 골드와 다이아몬드",
    "White gold and diamonds": "화이트 골드와 다이아몬드",
    "Beige gold and diamonds": "베이지 골드와 다이아몬드",
    "Self-winding": "오토매틱",
    "quartz movement": "쿼츠 무브먼트",
    "brilliant-cut diamonds": "브릴리언트 컷 다이아몬드",
    "Coco Crush": "코코 크러쉬",
    "COCO CRUSH": "코코 크러쉬",
    "Ultra": "울트라",
    "Bridal": "브라이덜",
    "Engagement Ring": "약혼 반지",
    "Wedding Ring": "웨딩 반지",
    "Camélia": "카멜리아",
    "Comète": "코메뜨",
    "Comete": "코메뜨",
    "Ruban": "루반",
    "Ruban": "루반",
    "Allure Céleste": "알뤼르 셀레스트",
    "Allure Celeste": "알뤼르 셀레스트",
    "Bijoux de Diamants": "비주 드 디아망",
    "Wallets on Chain": "월렛 온 체인",
    "Wallet On Chain": "월렛 온 체인",
    "Wallet on Chain": "월렛 온 체인",
    "Classic Wallet On Chain": "클래식 월렛 온 체인",
    "BOY CHANEL Wallet On Chain": "보이 샤넬 월렛 온 체인",
    "Micro Bags": "마이크로백",
    "Micro Bag": "마이크로백",
    "Mini Bag Charm": "미니백 참",
    "Vanity": "배니티",
    "Long Vanity with chain": "롱 배니티 체인",
    "Large Vanity with chain": "라지 배니티 체인",
    "Vanity with chain": "배니티 체인",
    "Vanity with Chain": "배니티 체인",
    "CHANEL 19 Wallet on Chain": "샤넬 19 월렛 온 체인",
    "CHANEL 19 Wallet On Chain": "샤넬 19 월렛 온 체인",
    "Card Holders & Wallets": "카드홀더 & 월렛",
    "Card Holder": "카드홀더",
    "Classic Card Holder": "클래식 카드홀더",
    "Flap Card Holder": "플랩 카드홀더",
    "Zipped Card Holder": "지퍼 카드홀더",
    "Passport Holder": "패스포트 홀더",
    "Long Wallet": "롱 월렛",
    "Long Zipped Wallet": "롱 지퍼 월렛",
    "Small Flap Wallet": "스몰 플랩 월렛",
    "Classic Small Flap Wallet": "클래식 스몰 플랩 월렛",
    "Classic Zipped Coin Purse": "클래식 지퍼 코인 퍼스",
    "Zipped Coin Purse": "지퍼 코인 퍼스",
    "Pouches & Cases": "파우치 & 케이스",
    "Zipped Pouch": "지퍼 파우치",
    "Large Zipped Pouch": "라지 지퍼 파우치",
    "Classic Zipped Pouch": "클래식 지퍼 파우치",
    "Leather Accessories": "레더 액세서리",
    "Clutch with chain": "체인 클러치",
    "Clutch": "클러치",
    "Pilot Sunglasses": "파일럿 선글라스",
    "Oval Sunglasses": "오벌 선글라스",
    "Square Sunglasses": "스퀘어 선글라스",
    "Round Sunglasses": "라운드 선글라스",
    "Cat Eye Sunglasses": "캣아이 선글라스",
    "Cat-Eye Sunglasses": "캣아이 선글라스",
    "Butterfly Sunglasses": "버터플라이 선글라스",
    "Rectangle Sunglasses": "렉탱글 선글라스",
    "Shield Sunglasses": "실드 선글라스",
    "Pantos Sunglasses": "판토스 선글라스",
    "Sunglasses": "선글라스",
    "Headwear": "헤드웨어",
    "Straw Hat": "스트로 햇",
    "Cloche Hat": "클로슈 햇",
    "Cap": "캡",
    "Hat": "햇",
    "Belts": "벨트",
    "Belt": "벨트",
    "Scarves": "스카프",
    "Scarf": "스카프",
    "Silk Scarf": "실크 스카프",
    "Cashmere Scarf": "캐시미어 스카프",
    "Bandeau": "반도",
    "Camellias": "카멜리아",
    "Camellia": "카멜리아",
    "Winter Accessories": "윈터 악세서리",
    "Summer Accessories": "서머 악세서리",
    "Other Accessories": "기타 악세서리",
    "Gloves": "장갑",
    "Muffler": "머플러",
    "Hair Accessory": "헤어 액세서리",
    "Hair Clip": "헤어 클립",
    "Brooch Camellia": "브로치 카멜리아",
}


def t(text: str | None) -> str:
    s = re.sub(r"\s+", " ", (text or "").strip())
    if not s:
        return ""
    if s in _EN_TITLE_KO:
        _KO[s] = _EN_TITLE_KO[s]
        return _EN_TITLE_KO[s]
    if s in _KO and en_ratio(_KO[s]) < 0.55 and _KO[s] not in {"동", "소매"}:
        return _KO[s]
    # Already mostly Korean
    if en_ratio(s) < 0.35:
        _KO[s] = s
        return s
    # Phrase glossary on EN source (longest first) before MT.
    pre = s
    for en, ko in sorted(_EN_TITLE_KO.items(), key=lambda kv: -len(kv[0])):
        pre = pre.replace(en, ko)
    if pre != s and en_ratio(pre) < 0.35:
        _KO[s] = pre
        return pre
    try:
        ko = gtx(s)
        time.sleep(0.05)
    except Exception:
        ko = s
    ko = (
        ko.replace("Chanel", "샤넬")
        .replace("CHANEL", "샤넬")
        .replace("샤 넬", "샤넬")
        .replace("Ready-to-Wear", "레디투웨어")
        .replace("Ready-To-Wear", "레디투웨어")
        .replace("Flap Bag", "플랩백")
        .replace("Hobo Bag", "호보백")
        .replace("Shopping Bag", "쇼핑백")
        .replace("Bowling Bag", "볼링백")
        .replace("Bucket Bag", "버킷백")
        .replace("Backpack", "백팩")
        .replace("Evening Bag", "이브닝백")
        .replace("Mini Bag", "미니백")
        .replace("Handbag", "핸드백")
        .replace("Calfskin", "카프스킨")
        .replace("Lambskin", "램스킨")
        .replace("Gold-Tone Metal", "골드 톤 메탈")
        .replace("Silver-Tone Metal", "실버 톤 메탈")
        .replace("Ballet flats", "발레 플랫")
        .replace("Ballet Flats", "발레 플랫")
        .replace("발레 아파트", "발레 플랫")
        .replace("Mary Janes", "메리제인")
        .replace("Mary Jane", "메리제인")
        .replace("메리 제인스", "메리제인")
        .replace("메리 제인", "메리제인")
        .replace("Slingbacks", "슬링백")
        .replace("Slingback", "슬링백")
        .replace("Pumps", "펌프스")
        .replace("Pump", "펌프스")
        .replace("Mules", "뮬")
        .replace("Mule", "뮬")
        .replace("노새", "뮬")
        .replace("Trainers", "스니커즈")
        .replace("Trainer", "스니커즈")
        .replace("Thongs", "통 샌들")
        .replace("Thong", "통 샌들")
        .replace("통 스타일", "통 샌들")
        .replace("Loafers", "로퍼")
        .replace("Loafer", "로퍼")
        .replace("Sneakers", "스니커즈")
        .replace("Sneaker", "스니커즈")
        .replace("Sandals", "샌들")
        .replace("Sandal", "샌들")
        .replace("Short Boots", "숏 부츠")
        .replace("High Boots", "하이 부츠")
        .replace("Boots", "부츠")
        .replace("Boot", "부츠")
        .replace("Lace-Up Shoes", "레이스업 슈즈")
        .replace("Moccasins", "모카신")
        .replace("Moccasin", "모카신")
        .replace("Espadrilles", "에스파드리유")
        .replace("Espadrille", "에스파드리유")
        .replace("Earrings", "이어링")
        .replace("Earring", "이어링")
        .replace("Necklaces", "네크리스")
        .replace("Necklace", "네크리스")
        .replace("Choker", "초커")
        .replace("Bracelets", "브레이슬릿")
        .replace("Bracelet", "브레이슬릿")
        .replace("Cuffs", "커프")
        .replace("Cuff", "커프")
        .replace("Brooches", "브로치")
        .replace("Brooch", "브로치")
        .replace("Rings", "링")
        .replace("Ring", "링")
        .replace("Clip-on Pendant Earrings", "클립온 펜던트 이어링")
        .replace("Pendant Earrings", "펜던트 이어링")
        .replace("귀걸이", "이어링")
    )
    if s.lower() in {"cuff", "cuffs"}:
        ko = "커프"
    _KO[s] = ko
    return ko


def accent_for(key: str) -> str:
    h = hashlib.md5((key or "x").encode()).hexdigest()
    r = 40 + int(h[0:2], 16) % 80
    g = 40 + int(h[2:4], 16) % 80
    b = 40 + int(h[4:6], 16) % 80
    return f"#{r:02x}{g:02x}{b:02x}"


def reorder_locals_garment_first(row: dict) -> list[str]:
    """Put studio STOCKMAN garment shots before lifestyle model photos.

    Existing downloads keep file numbers from the old order; we only reorder
    the path list so PLP / PDP primary image is the garment packshot.
    """
    return _reorder_locals_by_typology(
        row,
        preferred=(
            "PACKSHOT_STOCKMAN",
            "PACKSHOT_OTHER",
            "PACKSHOT_ALTERNATIVE",
            "PACKSHOT_DEFAULT",
            "LOOK",
            "EDITORIAL",
        ),
    )


def reorder_locals_handbag_front(row: dict) -> list[str]:
    """Prefer closed front / default packshots for handbags.

    Chanel bag PDPs lead with ARTISTIQUE_VUE1_LARGE / OTHER which are often
    open-bag or interior heroes. Briq PLP needs the clear front product shot:
    ARTISTIQUE_VUE1 (not LARGE) or PACKSHOT_DEFAULT.
    """
    return _reorder_locals_by_typology(
        row,
        preferred=(
            "PACKSHOT_ARTISTIQUE_VUE1",
            "PACKSHOT_DEFAULT",
            "PACKSHOT_ARTISTIQUE_VUE2",
            "PACKSHOT_ARTISTIQUE_VUE3",
            "PACKSHOT_ARTISTIQUE_VUE4",
            "PACKSHOT_ARTISTIQUE_VUE5",
            "PACKSHOT_ALTERNATIVE",
            "PACKSHOT_EXTRA",
            "PACKSHOT_OTHER",
            "PACKSHOT_ARTISTIQUE_VUE1_LARGE",
            "LOOK",
            "EDITORIAL",
        ),
    )


def reorder_locals_shoe_front(row: dict) -> list[str]:
    """Prefer default / front packshots for shoes."""
    return _reorder_locals_by_typology(
        row,
        preferred=(
            "PACKSHOT_DEFAULT",
            "PACKSHOT_ARTISTIQUE_VUE1",
            "PACKSHOT_ARTISTIQUE_VUE2",
            "PACKSHOT_ARTISTIQUE_VUE3",
            "PACKSHOT_ARTISTIQUE_VUE4",
            "PACKSHOT_ARTISTIQUE_VUE5",
            "PACKSHOT_ALTERNATIVE",
            "PACKSHOT_EXTRA",
            "PACKSHOT_OTHER",
            "PACKSHOT_ARTISTIQUE_VUE1_LARGE",
            "LOOK",
            "EDITORIAL",
        ),
    )


def _reorder_locals_by_typology(row: dict, preferred: tuple[str, ...]) -> list[str]:
    locals_ = list(row.get("localImages") or [])
    if not locals_ and row.get("localImage"):
        locals_ = [row["localImage"]]
    cdn = list(row.get("images") or [])
    metas = [m for m in (row.get("imageMeta") or []) if isinstance(m, dict)]
    if not locals_:
        return []
    if not cdn or not metas:
        return locals_

    # Map by URL (cdn/localImages share download order; imageMeta may differ).
    src_to_local: dict[str, str] = {}
    for i, src in enumerate(cdn):
        if i < len(locals_) and src:
            src_to_local[str(src)] = locals_[i]
            # Also key by filename — Chanel sometimes varies query/path slightly
            fn = str(src).rsplit("/", 1)[-1]
            if fn:
                src_to_local.setdefault(fn, locals_[i])

    def score(m: dict) -> tuple[int, int, int]:
        typ = str(m.get("typology") or "").upper()
        angle = str(m.get("viewAngle") or "").upper()
        try:
            rank = preferred.index(typ)
        except ValueError:
            rank = 50
        angle_rank = {"FRONT": 0, "BACK": 1, "DETAIL": 2}.get(angle, 5)
        return (rank, angle_rank, 0)

    ordered: list[str] = []
    seen_loc: set[str] = set()
    for m in sorted(metas, key=score):
        src = str(m.get("source") or "")
        loc = src_to_local.get(src) or src_to_local.get(src.rsplit("/", 1)[-1])
        if loc and loc not in seen_loc:
            seen_loc.add(loc)
            ordered.append(loc)
    for loc in locals_:
        if loc not in seen_loc:
            ordered.append(loc)
    return ordered


def format_size_label(size: str) -> str:
    s = (size or "").strip()
    if not s:
        return "One Size"
    if re.fullmatch(r"\d+(\.\d+)?", s):
        return f"FR {s}"
    return s


def format_shoe_size_label(size: str) -> str:
    s = (size or "").strip()
    if not s:
        return "One Size"
    if re.fullmatch(r"\d+(\.\d+)?", s):
        return f"EU {s}"
    if s.upper().startswith("EU"):
        return s
    return s


def format_other_acc_size_label(size: str, leaves: list[str] | None = None) -> str:
    s = (size or "").strip()
    if not s or s.upper() in {"UNI", "OS", "ONE SIZE", "ONESIZE", "U"}:
        return "One Size"
    leaves = leaves or []
    if re.fullmatch(r"\d+(\.\d+)?", s) and "ch-women-belts" in leaves:
        return f"{s} cm"
    return s


def format_jewellery_size_label(size: str, leaf: str | None = None) -> str:
    s = (size or "").strip()
    if not s or s.upper() in {"UNI", "OS", "ONE SIZE", "ONESIZE", "U"}:
        return "One Size"
    if re.fullmatch(r"\d+(\.\d+)?", s):
        # Numeric sizes on Chanel costume jewellery are French ring sizes.
        return f"FR {s}"
    if s.upper().startswith("FR"):
        return s
    return s


def format_eyewear_dims(dims) -> str:
    """Prefer mm frame measurements from Chanel eyewear PDP details.dimensions."""
    if not dims:
        return ""
    rows = dims if isinstance(dims, list) else [dims]
    mm = None
    for row in rows:
        if isinstance(row, dict) and str(row.get("unit") or "").lower() == "mm":
            mm = row
            break
    if not mm:
        for row in rows:
            if isinstance(row, dict) and any(
                k in row for k in ("lensWidth", "bridgeWidth", "temple", "height", "frontWidth")
            ):
                mm = row
                break
    if not isinstance(mm, dict):
        return as_text(dims)
    parts: list[str] = []
    mapping = [
        ("lensWidth", "렌즈"),
        ("bridgeWidth", "브릿지"),
        ("temple", "템플"),
        ("height", "높이"),
        ("frontWidth", "프론트"),
    ]
    for key, label in mapping:
        val = mm.get(key)
        if val is None or val == "":
            continue
        parts.append(f"{label} {val}mm")
    return " · ".join(parts)


def size_slug(size: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (size or "").lower()).strip("-")
    return s or "os"


def load_prev() -> dict[str, dict]:
    out: dict[str, dict] = {}
    if OUT_JSON.exists():
        try:
            for p in json.loads(OUT_JSON.read_text()):
                if p.get("id"):
                    out[p["id"]] = p
        except Exception:
            pass
    return out


def build_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    code = row.get("productCode") or row.get("sku") or row.get("id")
    if not code:
        return None
    gbp = row.get("gbpPrice")
    if gbp is None:
        return None
    price = gbp_to_krw(float(gbp))
    if price <= 0:
        return None

    leaf = row.get("leaf")
    cols = [
        c
        for c in (row.get("collections") or [])
        if c in {*SHAPE_LEAVES, *PARENT_COLS}
    ]
    cols = sorted(set([*cols, *PARENT_COLS, leaf] if leaf else [*cols, *PARENT_COLS]))
    if leaf and leaf not in SHAPE_LEAVES:
        return None
    primary = leaf if leaf in SHAPE_LEAVES else next(
        (c for c in SHAPE_LEAVES if c in cols), "ch-women-rtw"
    )

    title_en, name_ko = official_name_pair(row, code)
    details = row.get("details") or {}
    color_en = (details.get("color") or "").strip()
    fabrics_en = (details.get("fabrics") or "").strip()
    desc_en = (details.get("description") or "").strip()
    ref = (details.get("reference") or "").strip()

    color_ko = t(color_en) if color_en else ""
    fabrics_ko = t(fabrics_en) if fabrics_en else ""
    desc_ko = t(desc_en) if desc_en else ""

    parts = [desc_ko]
    if color_ko:
        parts.append(f"컬러: {color_ko}")
    if fabrics_ko:
        parts.append(f"소재: {fabrics_ko}")
    if ref:
        parts.append(f"레퍼런스: {ref}")
    description_ko = "\n\n".join(p for p in parts if p)

    images = reorder_locals_garment_first(row)
    # Require at least one real local file
    images = [
        p
        for p in images
        if (ROOT / "public" / p.lstrip("/")).is_file()
        and (ROOT / "public" / p.lstrip("/")).stat().st_size > 2048
    ]
    if not images:
        print(f"skip no local image: {code}", flush=True)
        return None
    image = images[0]
    # Hover: next studio angle if available, else second image
    hover = images[1] if len(images) > 1 else None
    if hover and not (
        (ROOT / "public" / hover.lstrip("/")).is_file()
        and (ROOT / "public" / hover.lstrip("/")).stat().st_size > 2048
    ):
        hover = images[1] if len(images) > 1 else None

    pid = f"ch-{str(code).lower()}"
    registered = (prev or {}).get("registeredAt") or now_iso

    size_rows = row.get("sizes") or []
    variants: list[dict] = []
    any_in = False
    for sz in size_rows:
        size_raw = str(sz.get("orliSize") or sz.get("size") or "").strip()
        if not size_raw:
            continue
        label = format_size_label(size_raw)
        slug = size_slug(size_raw)
        sku = str(sz.get("sku") or sz.get("id") or f"{code}-{slug}")
        # Chanel.com RTW SSR almost always reports OUT_OF_STOCK (boutique /
        # not sold online). Briq fulfils as special order — keep sizes buyable.
        in_stock = True
        any_in = True
        v: dict = {
            "id": f"{pid}-{slug}",
            "name": f"{title_en} — {label}",
            "nameKo": f"{name_ko} — {label}",
            "sku": sku,
            "gbpPrice": float(gbp),
            "price": price,
            "image": image,
            "images": images,
            "sourceUrl": row.get("url") or "",
            "inStock": in_stock,
            "colorKey": color_en.lower() or "default",
            "colorNameKo": color_ko or color_en or "기본",
            "size": label,
            "chCollections": cols,
        }
        if hover:
            v["hoverImage"] = hover
        variants.append(v)

    if not variants:
        in_stock = True
        any_in = True
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
                "sourceUrl": row.get("url") or "",
                "inStock": in_stock,
                "colorKey": color_en.lower() or "default",
                "colorNameKo": color_ko or color_en or "기본",
                "size": "One Size",
                "chCollections": cols,
            }
        ]
        if hover:
            variants[0]["hoverImage"] = hover
    else:
        any_in = any(v["inStock"] for v in variants)

    tags = [
        "chanel",
        "샤넬",
        "rtw",
        "의류",
        "여성",
        "ready-to-wear",
        *cols,
    ]
    badge = "New" if row.get("new") else None

    story = []
    if desc_ko:
        story.append(
            {
                "titleKo": name_ko,
                "bodyKo": desc_ko,
                "image": image,
            }
        )

    prod: dict = {
        "id": pid,
        "name": title_en,
        "nameKo": name_ko,
        "brand": "샤넬",
        "price": price,
        "category": "luxury",
        "subcategory": primary,
        "chCollections": cols,
        "tags": tags,
        "descriptionKo": description_ko,
        "image": image,
        "images": images,
        "accent": accent_for(str(code)),
        "badge": badge,
        "gbpPrice": float(gbp),
        "sku": code,
        "sourceUrl": row.get("url") or "",
        "inStock": any_in,
        "variants": variants,
        "sizeChart": CH_WOMEN_RTW_SIZE_CHART,
        "storySections": story,
        "registeredAt": registered,
        "editTier": "new" if badge == "New" else "signature",
    }
    if hover:
        prod["hoverImage"] = hover
    return apply_detail_fields(prod, row, name_ko=name_ko, image=image)


def as_text(val) -> str:
    if val is None:
        return ""
    if isinstance(val, list):
        # Prefer centimetre dimensions when Chanel returns in/cm/mm triples.
        cm_parts = []
        other_parts = []
        for v in val:
            if isinstance(v, dict):
                unit = str(v.get("unit") or "").lower()
                value = as_text(v.get("value"))
                if not value:
                    continue
                if unit == "cm":
                    cm_parts.append(f"{value} cm")
                elif unit:
                    other_parts.append(f"{value} {unit}")
                else:
                    other_parts.append(value)
            else:
                t = as_text(v)
                if t:
                    other_parts.append(t)
        parts = cm_parts or other_parts
        return " · ".join(p for p in parts if p)
    if isinstance(val, dict):
        for k in ("label", "value", "text", "description"):
            if val.get(k):
                return as_text(val.get(k))
        return ""
    return str(val).strip()


def official_title_en(row: dict, code: str | None = None) -> str:
    """Prefer official PDP heading: title + materials subtitle (+ colour)."""
    return official_name_pair(row, code)[0]


def official_name_pair(row: dict, code: str | None = None) -> tuple[str, str]:
    """Return (name_en, name_ko) matching official Chanel PDP heading.

    Translate short title + material subtitle separately so Korean stays natural
    (e.g. J12 + 고강도 화이트 세라믹과 스틸).
    """
    details = row.get("details") if isinstance(row.get("details"), dict) else {}
    title = as_text(row.get("title"))
    short = as_text(row.get("titleShort")) or title
    subtitle = as_text(row.get("subtitle") or details.get("subtitle"))
    color = as_text(details.get("color"))
    if subtitle and title and subtitle.lower() in title.lower():
        composed = title
    else:
        composed = compose_official_name(short, subtitle, color) or title
    composed = composed or str(code or row.get("id") or row.get("sku") or "")

    if short and subtitle:
        parts_ko = [t(short), t(subtitle)]
        if (
            color
            and color.lower() in composed.lower()
            and color.lower() not in subtitle.lower()
            and color.lower() not in short.lower()
        ):
            parts_ko.append(t(color))
        name_ko = " ".join(p for p in parts_ko if p)
        return composed, name_ko or t(composed)
    return composed, t(composed)


CHAR_LABEL_KO = {
    "Sizes": "사이즈",
    "Size": "사이즈",
    "Case": "케이스",
    "Bezel": "베젤",
    "Crown": "크라운",
    "Dial": "다이얼",
    "Strap": "스트랩",
    "Bracelet": "브레이슬릿",
    "Movement": "무브먼트",
    "Functions": "기능",
    "Water-resistance": "방수",
    "Water resistance": "방수",
    "Diamonds": "다이아몬드",
    "Material": "소재",
    "Materials": "소재",
    "Feature": "특징",
    "Lens width": "렌즈 너비",
    "Lens height": "렌즈 높이",
    "Frame width": "프레임 너비",
    "Branch length": "템플 길이",
    "Bridge": "브릿지",
    "Color": "컬러",
    "Colour": "컬러",
    "Reference": "레퍼런스",
    "Volume": "용량",
    "Olfactory family": "향조",
    "Concentration": "농도",
    "Key ingredients": "주요 성분",
    "Ingredients": "성분",
    "Shade": "셰이드",
    "Finish": "피니시",
    "Texture": "텍스처",
    "Coverage": "커버리지",
    "Application": "사용법",
}


def characteristics_list(details: dict | None) -> list[dict]:
    if not isinstance(details, dict):
        return []
    raw = details.get("characteristics") or []
    out: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        label = as_text(item.get("label"))
        value = as_text(item.get("value"))
        if label and value:
            out.append({"label": label, "value": value})
    return out


def build_tech_specs(details: dict | None) -> list[dict]:
    specs: list[dict] = []
    for item in characteristics_list(details):
        label_en = item["label"]
        value_en = item["value"]
        label_ko = CHAR_LABEL_KO.get(label_en) or t(label_en) or label_en
        value_ko = t(value_en) or value_en
        specs.append({"labelKo": label_ko, "valueKo": value_ko})
    return specs


def build_ch_detail_fields(
    row: dict,
    *,
    name_ko: str,
    image: str | None,
    extra_meta: list[str] | None = None,
) -> tuple[str, list[dict], list[dict]]:
    """Return (descriptionKo, storySections, techSpecs) from enriched raw details."""
    details = row.get("details") if isinstance(row.get("details"), dict) else {}
    editorial = as_text(details.get("editorial"))
    desc_en = as_text(details.get("description"))
    body_en = editorial or desc_en
    body_ko = t(body_en) if body_en else ""

    chars = characteristics_list(details)
    tech = build_tech_specs(details)

    meta_parts: list[str] = []
    for line in extra_meta or []:
        if line and str(line).strip():
            meta_parts.append(str(line).strip())

    blocks = [b for b in [body_ko, *meta_parts] if b]
    uniq: list[str] = []
    seen: set[str] = set()
    for b in blocks:
        key = b[:80]
        if key in seen:
            continue
        seen.add(key)
        uniq.append(b)
    description_ko = "\n\n".join(uniq)

    story: list[dict] = []
    if body_ko:
        story.append({"titleKo": name_ko, "bodyKo": body_ko, "image": image})
    if chars:
        spec_body = "\n".join(
            f"{(CHAR_LABEL_KO.get(c['label']) or t(c['label']) or c['label'])}: "
            f"{t(c['value']) or c['value']}"
            for c in chars
        )
        if spec_body and (not body_ko or spec_body[:40] not in body_ko):
            story.append(
                {
                    "titleKo": "제품 상세",
                    "bodyKo": spec_body,
                    "image": image,
                }
            )
    return description_ko, story, tech


def apply_detail_fields(
    prod: dict, row: dict, *, name_ko: str, image: str | None
) -> dict:
    """Attach enriched Korean copy + techSpecs onto a built Chanel product."""
    details = row.get("details") if isinstance(row.get("details"), dict) else {}
    has_enrich = bool(details.get("characteristics") or details.get("editorial"))
    if not has_enrich:
        desc_en = as_text(details.get("description"))
        if desc_en and len(desc_en) > 100:
            desc_ko = t(desc_en)
            cur = prod.get("descriptionKo") or ""
            if desc_ko and len(desc_ko) > len(cur):
                prod["descriptionKo"] = desc_ko
                if not prod.get("storySections"):
                    prod["storySections"] = [
                        {"titleKo": name_ko, "bodyKo": desc_ko, "image": image}
                    ]
        return prod

    existing = as_text(prod.get("descriptionKo"))
    meta = []
    for block in existing.split("\n\n"):
        if ":" in block and len(block) < 160:
            meta.append(block)
    description_ko, story, tech = build_ch_detail_fields(
        row, name_ko=name_ko, image=image, extra_meta=meta
    )
    if description_ko:
        prod["descriptionKo"] = description_ko
    if story:
        prod["storySections"] = story
    if tech:
        prod["techSpecs"] = tech
    return prod


def build_handbag_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    code = row.get("productCode") or row.get("sku") or row.get("id")
    if not code:
        return None
    gbp = row.get("gbpPrice")
    if gbp is None:
        return None
    price = gbp_to_krw(float(gbp))
    if price <= 0:
        return None

    leaves = [
        c
        for c in (row.get("leaves") or row.get("collections") or [])
        if c in BAG_SHAPE_LEAVES
    ]
    leaf = row.get("leaf") if row.get("leaf") in BAG_SHAPE_LEAVES else None
    if leaf and leaf not in leaves:
        leaves.append(leaf)
    if not leaves:
        return None
    primary = next((c for c in BAG_SHAPE_LEAVES if c in leaves), leaves[0])
    cols = sorted(set([*BAG_PARENT_COLS, *leaves]))

    title_en, name_ko = official_name_pair(row, code)
    details = row.get("details") or {}
    if not isinstance(details, dict):
        details = {}
    color_en = as_text(details.get("color"))
    fabrics_en = as_text(details.get("fabrics"))
    desc_en = as_text(details.get("description"))
    dims_en = as_text(details.get("dimensions"))
    ref = as_text(details.get("reference"))

    color_ko = t(color_en) if color_en else ""
    fabrics_ko = t(fabrics_en) if fabrics_en else ""
    desc_ko = t(desc_en) if desc_en else ""
    dims_ko = t(dims_en) if dims_en else ""

    parts = [desc_ko]
    if color_ko:
        parts.append(f"컬러: {color_ko}")
    if fabrics_ko:
        parts.append(f"소재: {fabrics_ko}")
    if dims_ko:
        parts.append(f"사이즈: {dims_ko}")
    if ref:
        parts.append(f"레퍼런스: {ref}")
    description_ko = "\n\n".join(p for p in parts if p)

    images = reorder_locals_handbag_front(row)
    images = [
        p
        for p in images
        if (ROOT / "public" / p.lstrip("/")).is_file()
        and (ROOT / "public" / p.lstrip("/")).stat().st_size > 2048
    ]
    if not images:
        print(f"skip no local image (bag): {code}", flush=True)
        return None
    image = images[0]
    hover = images[1] if len(images) > 1 else None

    pid = f"ch-{str(code).lower()}"
    registered = (prev or {}).get("registeredAt") or now_iso

    # Handbags: One Size (boutique special order — always buyable)
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
            "sourceUrl": row.get("url") or "",
            "inStock": True,
            "colorKey": color_en.lower() or "default",
            "colorNameKo": color_ko or color_en or "기본",
            "size": "One Size",
            "chCollections": cols,
        }
    ]
    if hover:
        variants[0]["hoverImage"] = hover

    tags = [
        "chanel",
        "샤넬",
        "handbag",
        "가방",
        "핸드백",
        "여성",
        *cols,
    ]
    badge = "New" if row.get("new") else None
    story = []
    if desc_ko:
        story.append({"titleKo": name_ko, "bodyKo": desc_ko, "image": image})

    prod: dict = {
        "id": pid,
        "name": title_en,
        "nameKo": name_ko,
        "brand": "샤넬",
        "price": price,
        "category": "bags",
        "subcategory": primary,
        "chCollections": cols,
        "tags": tags,
        "descriptionKo": description_ko,
        "image": image,
        "images": images,
        "accent": accent_for(str(code)),
        "badge": badge,
        "gbpPrice": float(gbp),
        "sku": code,
        "sourceUrl": row.get("url") or "",
        "inStock": True,
        "variants": variants,
        "storySections": story,
        "registeredAt": registered,
        "editTier": "new" if badge == "New" else "signature",
    }
    if hover:
        prod["hoverImage"] = hover
    return apply_detail_fields(prod, row, name_ko=name_ko, image=image)


def build_slg_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    """Small leather goods — same pricing/copy pattern as handbags (One Size + dims)."""
    code = row.get("productCode") or row.get("sku") or row.get("id")
    if not code:
        return None
    gbp = row.get("gbpPrice")
    if gbp is None:
        return None
    price = gbp_to_krw(float(gbp))
    if price <= 0:
        return None

    leaf = row.get("leaf") if row.get("leaf") in SLG_SHAPE_LEAVES else None
    leaves = [
        c
        for c in (row.get("leaves") or row.get("collections") or [])
        if c in SLG_SHAPE_LEAVES
    ]
    if leaf:
        leaves = [leaf]
    elif not leaves:
        return None
    primary = leaf or next((c for c in SLG_SHAPE_LEAVES if c in leaves), leaves[0])
    cols = sorted(set([*SLG_PARENT_COLS, primary]))

    title_en, name_ko = official_name_pair(row, code)
    details = row.get("details") or {}
    if not isinstance(details, dict):
        details = {}
    color_en = as_text(details.get("color"))
    fabrics_en = as_text(details.get("fabrics"))
    desc_en = as_text(details.get("description"))
    dims_en = as_text(details.get("dimensions"))
    ref = as_text(details.get("reference"))

    color_ko = t(color_en) if color_en else ""
    fabrics_ko = t(fabrics_en) if fabrics_en else ""
    desc_ko = t(desc_en) if desc_en else ""
    dims_ko = t(dims_en) if dims_en else ""

    parts = [desc_ko]
    if color_ko:
        parts.append(f"컬러: {color_ko}")
    if fabrics_ko:
        parts.append(f"소재: {fabrics_ko}")
    if dims_ko:
        parts.append(f"사이즈: {dims_ko}")
    if ref:
        parts.append(f"레퍼런스: {ref}")
    description_ko = "\n\n".join(p for p in parts if p)

    images = reorder_locals_handbag_front(row)
    images = [
        p
        for p in images
        if (ROOT / "public" / p.lstrip("/")).is_file()
        and (ROOT / "public" / p.lstrip("/")).stat().st_size > 2048
    ]
    if not images:
        print(f"skip no local image (slg): {code}", flush=True)
        return None
    image = images[0]
    hover = images[1] if len(images) > 1 else None

    pid = f"ch-{str(code).lower()}"
    registered = (prev or {}).get("registeredAt") or now_iso

    # Official Chanel SLG is sold as One Size; dimensions live in copy (사이즈: …).
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
            "sourceUrl": row.get("url") or "",
            "inStock": True,
            "colorKey": color_en.lower() or "default",
            "colorNameKo": color_ko or color_en or "기본",
            "size": "One Size",
            "chCollections": cols,
        }
    ]
    if hover:
        variants[0]["hoverImage"] = hover

    tags = [
        "chanel",
        "샤넬",
        "slg",
        "small leather goods",
        "스몰 레더 굿즈",
        "악세서리",
        "여성",
        *cols,
    ]
    badge = "New" if row.get("new") else None
    story = []
    if desc_ko:
        story.append({"titleKo": name_ko, "bodyKo": desc_ko, "image": image})

    prod: dict = {
        "id": pid,
        "name": title_en,
        "nameKo": name_ko,
        "brand": "샤넬",
        "price": price,
        "category": "accessories",
        "subcategory": primary,
        "chCollections": cols,
        "tags": tags,
        "descriptionKo": description_ko,
        "image": image,
        "images": images,
        "accent": accent_for(str(code)),
        "badge": badge,
        "gbpPrice": float(gbp),
        "sku": code,
        "sourceUrl": row.get("url") or "",
        "inStock": True,
        "variants": variants,
        "storySections": story,
        "registeredAt": registered,
        "editTier": "new" if badge == "New" else "signature",
    }
    if hover:
        prod["hoverImage"] = hover
    return apply_detail_fields(prod, row, name_ko=name_ko, image=image)


def build_shoe_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    code = row.get("productCode") or row.get("sku") or row.get("id")
    if not code:
        return None
    gbp = row.get("gbpPrice")
    if gbp is None:
        return None
    price = gbp_to_krw(float(gbp))
    if price <= 0:
        return None

    leaves = [
        c
        for c in (row.get("leaves") or row.get("collections") or [])
        if c in SHOE_SHAPE_LEAVES
    ]
    leaf = row.get("leaf") if row.get("leaf") in SHOE_SHAPE_LEAVES else None
    if leaf and leaf not in leaves:
        leaves.append(leaf)
    if not leaves:
        return None
    primary = next((c for c in SHOE_SHAPE_LEAVES if c in leaves), leaves[0])
    cols = sorted(set([*SHOE_PARENT_COLS, *leaves]))

    title_en, name_ko = official_name_pair(row, code)
    details = row.get("details") or {}
    if not isinstance(details, dict):
        details = {}
    color_en = as_text(details.get("color"))
    fabrics_en = as_text(details.get("fabrics"))
    desc_en = as_text(details.get("description"))
    ref = as_text(details.get("reference"))

    color_ko = t(color_en) if color_en else ""
    fabrics_ko = t(fabrics_en) if fabrics_en else ""
    desc_ko = t(desc_en) if desc_en else ""

    parts = [desc_ko]
    if color_ko:
        parts.append(f"컬러: {color_ko}")
    if fabrics_ko:
        parts.append(f"소재: {fabrics_ko}")
    if ref:
        parts.append(f"레퍼런스: {ref}")
    description_ko = "\n\n".join(p for p in parts if p)

    images = reorder_locals_shoe_front(row)
    images = [
        p
        for p in images
        if (ROOT / "public" / p.lstrip("/")).is_file()
        and (ROOT / "public" / p.lstrip("/")).stat().st_size > 2048
    ]
    if not images:
        print(f"skip no local image (shoe): {code}", flush=True)
        return None
    image = images[0]
    hover = images[1] if len(images) > 1 else None

    pid = f"ch-{str(code).lower()}"
    registered = (prev or {}).get("registeredAt") or now_iso

    size_rows = row.get("sizes") or []
    variants: list[dict] = []
    for sz in size_rows:
        size_raw = str(sz.get("orliSize") or sz.get("size") or "").strip()
        if not size_raw:
            continue
        label = format_shoe_size_label(size_raw)
        slug = size_slug(size_raw)
        sku = str(sz.get("sku") or sz.get("id") or f"{code}-{slug}")
        # Boutique / special-order — keep sizes buyable like RTW.
        v: dict = {
            "id": f"{pid}-{slug}",
            "name": f"{title_en} — {label}",
            "nameKo": f"{name_ko} — {label}",
            "sku": sku,
            "gbpPrice": float(gbp),
            "price": price,
            "image": image,
            "images": images,
            "sourceUrl": row.get("url") or "",
            "inStock": True,
            "colorKey": color_en.lower() or "default",
            "colorNameKo": color_ko or color_en or "기본",
            "size": label,
            "chCollections": cols,
        }
        if hover:
            v["hoverImage"] = hover
        variants.append(v)

    if not variants:
        print(f"skip no sizes (shoe): {code}", flush=True)
        return None

    tags = [
        "chanel",
        "샤넬",
        "shoes",
        "슈즈",
        "여성",
        *cols,
    ]
    badge = "New" if row.get("new") else None
    story = []
    if desc_ko:
        story.append({"titleKo": name_ko, "bodyKo": desc_ko, "image": image})

    prod: dict = {
        "id": pid,
        "name": title_en,
        "nameKo": name_ko,
        "brand": "샤넬",
        "price": price,
        "category": "shoes",
        "subcategory": primary,
        "chCollections": cols,
        "tags": tags,
        "descriptionKo": description_ko,
        "image": image,
        "images": images,
        "accent": accent_for(str(code)),
        "badge": badge,
        "gbpPrice": float(gbp),
        "sku": code,
        "sourceUrl": row.get("url") or "",
        "inStock": True,
        "variants": variants,
        "sizeChart": CH_WOMEN_SHOES_SIZE_CHART,
        "storySections": story,
        "registeredAt": registered,
        "editTier": "new" if badge == "New" else "signature",
    }
    if hover:
        prod["hoverImage"] = hover
    return apply_detail_fields(prod, row, name_ko=name_ko, image=image)


def build_jewellery_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    code = row.get("productCode") or row.get("sku") or row.get("id")
    if not code:
        return None
    gbp = row.get("gbpPrice")
    if gbp is None:
        return None
    price = gbp_to_krw(float(gbp))
    if price <= 0:
        return None

    leaves = [
        c
        for c in (row.get("leaves") or row.get("collections") or [])
        if c in JEWELLERY_SHAPE_LEAVES
    ]
    leaf = row.get("leaf") if row.get("leaf") in JEWELLERY_SHAPE_LEAVES else None
    # Prefer the resolved PDP leaf; ignore polluted multi-leaf PLP tags.
    if leaf:
        leaves = [leaf]
    elif not leaves:
        return None
    primary = leaf or next((c for c in JEWELLERY_SHAPE_LEAVES if c in leaves), leaves[0])
    cols = sorted(set([*JEWELLERY_PARENT_COLS, primary]))

    title_en, name_ko = official_name_pair(row, code)
    details = row.get("details") or {}
    if not isinstance(details, dict):
        details = {}
    color_en = as_text(details.get("color"))
    fabrics_en = as_text(details.get("fabrics"))
    desc_en = as_text(details.get("description"))
    dims_en = as_text(details.get("dimensions"))
    ref = as_text(details.get("reference"))

    color_ko = t(color_en) if color_en else ""
    fabrics_ko = t(fabrics_en) if fabrics_en else ""
    desc_ko = t(desc_en) if desc_en else ""
    dims_ko = t(dims_en) if dims_en else ""

    parts = [desc_ko]
    if color_ko:
        parts.append(f"컬러: {color_ko}")
    if fabrics_ko:
        parts.append(f"소재: {fabrics_ko}")
    if dims_ko:
        parts.append(f"사이즈: {dims_ko}")
    if ref:
        parts.append(f"레퍼런스: {ref}")
    description_ko = "\n\n".join(p for p in parts if p)

    images = reorder_locals_shoe_front(row)
    images = [
        p
        for p in images
        if (ROOT / "public" / p.lstrip("/")).is_file()
        and (ROOT / "public" / p.lstrip("/")).stat().st_size > 2048
    ]
    if not images:
        print(f"skip no local image (jewellery): {code}", flush=True)
        return None
    image = images[0]
    hover = images[1] if len(images) > 1 else None

    pid = f"ch-{str(code).lower()}"
    registered = (prev or {}).get("registeredAt") or now_iso

    size_rows = row.get("sizes") or []
    variants: list[dict] = []
    for sz in size_rows:
        size_raw = str(sz.get("orliSize") or sz.get("size") or "").strip() or "UNI"
        label = format_jewellery_size_label(size_raw, primary)
        slug = size_slug(size_raw if size_raw.upper() != "UNI" else "os")
        sku = str(sz.get("sku") or sz.get("id") or f"{code}-{slug}")
        v: dict = {
            "id": f"{pid}-{slug}",
            "name": f"{title_en} — {label}",
            "nameKo": f"{name_ko} — {label if label != 'One Size' else '원 사이즈'}",
            "sku": sku,
            "gbpPrice": float(gbp),
            "price": price,
            "image": image,
            "images": images,
            "sourceUrl": row.get("url") or "",
            "inStock": True,
            "colorKey": color_en.lower() or "default",
            "colorNameKo": color_ko or color_en or "기본",
            "size": label,
            "chCollections": cols,
        }
        if hover:
            v["hoverImage"] = hover
        variants.append(v)

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
                "sourceUrl": row.get("url") or "",
                "inStock": True,
                "colorKey": color_en.lower() or "default",
                "colorNameKo": color_ko or color_en or "기본",
                "size": "One Size",
                "chCollections": cols,
            }
        ]
        if hover:
            variants[0]["hoverImage"] = hover

    tags = [
        "chanel",
        "샤넬",
        "jewellery",
        "주얼리",
        "악세서리",
        "여성",
        *cols,
    ]
    badge = "New" if row.get("new") else None
    story = []
    if desc_ko:
        story.append({"titleKo": name_ko, "bodyKo": desc_ko, "image": image})

    prod: dict = {
        "id": pid,
        "name": title_en,
        "nameKo": name_ko,
        "brand": "샤넬",
        "price": price,
        "category": "accessories",
        "subcategory": primary,
        "chCollections": cols,
        "tags": tags,
        "descriptionKo": description_ko,
        "image": image,
        "images": images,
        "accent": accent_for(str(code)),
        "badge": badge,
        "gbpPrice": float(gbp),
        "sku": code,
        "sourceUrl": row.get("url") or "",
        "inStock": True,
        "variants": variants,
        "storySections": story,
        "registeredAt": registered,
        "editTier": "new" if badge == "New" else "signature",
    }
    if primary == "ch-women-rings":
        prod["sizeChart"] = CH_RING_SIZE_CHART
    if hover:
        prod["hoverImage"] = hover
    return apply_detail_fields(prod, row, name_ko=name_ko, image=image)


def build_high_jewellery_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    code = row.get("productCode") or row.get("sku") or row.get("id")
    if not code:
        return None
    gbp = row.get("gbpPrice")
    if gbp is None:
        return None
    price = gbp_to_krw(float(gbp))
    if price <= 0:
        return None

    cols = sorted(set([*HIGH_JEWELLERY_PARENT_COLS]))
    title_en, name_ko = official_name_pair(row, code)
    details = row.get("details") or {}
    if not isinstance(details, dict):
        details = {}
    color_en = as_text(details.get("color"))
    fabrics_en = as_text(details.get("fabrics"))
    desc_en = as_text(details.get("description"))
    dims_en = as_text(details.get("dimensions"))
    ref = as_text(details.get("reference"))
    collection_en = as_text(row.get("collection"))

    color_ko = t(color_en) if color_en else ""
    fabrics_ko = t(fabrics_en) if fabrics_en else ""
    desc_ko = t(desc_en) if desc_en else ""
    dims_ko = t(dims_en) if dims_en else ""
    collection_ko = t(collection_en) if collection_en else ""

    parts = [desc_ko]
    if collection_ko:
        parts.append(f"컬렉션: {collection_ko}")
    if color_ko:
        parts.append(f"컬러: {color_ko}")
    if fabrics_ko:
        parts.append(f"소재: {fabrics_ko}")
    if dims_ko:
        parts.append(f"사이즈: {dims_ko}")
    if ref:
        parts.append(f"레퍼런스: {ref}")
    description_ko = "\n\n".join(p for p in parts if p)

    images = reorder_locals_shoe_front(row)
    images = [
        p
        for p in images
        if (ROOT / "public" / p.lstrip("/")).is_file()
        and (ROOT / "public" / p.lstrip("/")).stat().st_size > 2048
    ]
    if not images:
        print(f"skip no local image (high-jewellery): {code}", flush=True)
        return None
    image = images[0]
    hover = images[1] if len(images) > 1 else None

    pid = f"ch-{str(code).lower()}"
    registered = (prev or {}).get("registeredAt") or now_iso
    shape = (row.get("shape") or "").lower()
    is_ring = shape == "rings" or bool(re.search(r"\brings?\b", title_en, flags=re.I))

    size_rows = row.get("sizes") or []
    variants: list[dict] = []
    for sz in size_rows:
        size_raw = str(sz.get("orliSize") or sz.get("size") or "").strip() or "UNI"
        label = format_jewellery_size_label(
            size_raw, "ch-women-rings" if is_ring else HIGH_JEWELLERY_LEAF
        )
        slug = size_slug(size_raw if size_raw.upper() != "UNI" else "os")
        sku = str(sz.get("sku") or sz.get("id") or f"{code}-{slug}")
        v: dict = {
            "id": f"{pid}-{slug}",
            "name": f"{title_en} — {label}",
            "nameKo": f"{name_ko} — {label if label != 'One Size' else '원 사이즈'}",
            "sku": sku,
            "gbpPrice": float(gbp),
            "price": price,
            "image": image,
            "images": images,
            "sourceUrl": row.get("url") or "",
            "inStock": True,
            "colorKey": color_en.lower() or "default",
            "colorNameKo": color_ko or color_en or "기본",
            "size": label,
            "chCollections": cols,
        }
        if hover:
            v["hoverImage"] = hover
        variants.append(v)

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
                "sourceUrl": row.get("url") or "",
                "inStock": True,
                "colorKey": color_en.lower() or "default",
                "colorNameKo": color_ko or color_en or "기본",
                "size": "One Size",
                "chCollections": cols,
            }
        ]
        if hover:
            variants[0]["hoverImage"] = hover

    tags = [
        "chanel",
        "샤넬",
        "jewellery",
        "주얼리",
        "High 주얼리",
        "하이 주얼리",
        "악세서리",
        "여성",
        *cols,
    ]
    if collection_ko:
        tags.append(collection_ko)
    badge = "New" if row.get("new") else None
    story = []
    if desc_ko:
        story.append({"titleKo": name_ko, "bodyKo": desc_ko, "image": image})

    prod: dict = {
        "id": pid,
        "name": title_en,
        "nameKo": name_ko,
        "brand": "샤넬",
        "price": price,
        "category": "accessories",
        "subcategory": HIGH_JEWELLERY_LEAF,
        "chCollections": cols,
        "tags": tags,
        "descriptionKo": description_ko,
        "image": image,
        "images": images,
        "accent": accent_for(str(code)),
        "badge": badge,
        "gbpPrice": float(gbp),
        "sku": code,
        "sourceUrl": row.get("url") or "",
        "inStock": True,
        "variants": variants,
        "storySections": story,
        "registeredAt": registered,
        "editTier": "new" if badge == "New" else "signature",
    }
    if is_ring:
        prod["sizeChart"] = CH_RING_SIZE_CHART
    if hover:
        prod["hoverImage"] = hover
    return apply_detail_fields(prod, row, name_ko=name_ko, image=image)


def build_fine_jewellery_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    code = row.get("productCode") or row.get("sku") or row.get("id")
    if not code:
        return None
    gbp = row.get("gbpPrice")
    if gbp is None:
        return None
    price = gbp_to_krw(float(gbp))
    if price <= 0:
        return None

    cols = sorted(set([*FINE_JEWELLERY_PARENT_COLS]))
    title_en, name_ko = official_name_pair(row, code)
    details = row.get("details") or {}
    if not isinstance(details, dict):
        details = {}
    color_en = as_text(details.get("color"))
    fabrics_en = as_text(details.get("fabrics"))
    desc_en = as_text(details.get("description"))
    dims_en = as_text(details.get("dimensions"))
    ref = as_text(details.get("reference"))
    collection_en = as_text(row.get("collection"))

    color_ko = t(color_en) if color_en else ""
    fabrics_ko = t(fabrics_en) if fabrics_en else ""
    desc_ko = t(desc_en) if desc_en else ""
    dims_ko = t(dims_en) if dims_en else ""
    collection_ko = t(collection_en) if collection_en else ""

    parts = [desc_ko]
    if collection_ko:
        parts.append(f"컬렉션: {collection_ko}")
    if color_ko:
        parts.append(f"컬러: {color_ko}")
    if fabrics_ko:
        parts.append(f"소재: {fabrics_ko}")
    if dims_ko:
        parts.append(f"사이즈: {dims_ko}")
    if ref:
        parts.append(f"레퍼런스: {ref}")
    description_ko = "\n\n".join(p for p in parts if p)

    images = reorder_locals_shoe_front(row)
    images = [
        p
        for p in images
        if (ROOT / "public" / p.lstrip("/")).is_file()
        and (ROOT / "public" / p.lstrip("/")).stat().st_size > 2048
    ]
    if not images:
        images = [
            p
            for p in (row.get("localImages") or [])
            if (ROOT / "public" / str(p).lstrip("/")).is_file()
            and (ROOT / "public" / str(p).lstrip("/")).stat().st_size > 2048
        ]
    if not images:
        print(f"skip no local image (fine-jewellery): {code}", flush=True)
        return None
    image = images[0]
    hover = images[1] if len(images) > 1 else None

    pid = f"ch-{str(code).lower()}"
    registered = (prev or {}).get("registeredAt") or now_iso
    shape = (row.get("shape") or "").lower()
    is_ring = shape == "rings" or bool(re.search(r"\brings?\b", title_en, flags=re.I))

    size_rows = row.get("sizes") or []
    variants: list[dict] = []
    for sz in size_rows:
        size_raw = str(sz.get("orliSize") or sz.get("size") or "").strip() or "UNI"
        label = format_jewellery_size_label(
            size_raw, "ch-women-rings" if is_ring else FINE_JEWELLERY_LEAF
        )
        slug = size_slug(size_raw if size_raw.upper() != "UNI" else "os")
        sku = str(sz.get("sku") or sz.get("id") or f"{code}-{slug}")
        v: dict = {
            "id": f"{pid}-{slug}",
            "name": f"{title_en} — {label}",
            "nameKo": f"{name_ko} — {label if label != 'One Size' else '원 사이즈'}",
            "sku": sku,
            "gbpPrice": float(gbp),
            "price": price,
            "image": image,
            "images": images,
            "sourceUrl": row.get("url") or "",
            "inStock": True,
            "colorKey": color_en.lower() or "default",
            "colorNameKo": color_ko or color_en or "기본",
            "size": label,
            "chCollections": cols,
        }
        if hover:
            v["hoverImage"] = hover
        variants.append(v)

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
                "sourceUrl": row.get("url") or "",
                "inStock": True,
                "colorKey": color_en.lower() or "default",
                "colorNameKo": color_ko or color_en or "기본",
                "size": "One Size",
                "chCollections": cols,
            }
        ]
        if hover:
            variants[0]["hoverImage"] = hover

    tags = [
        "chanel",
        "샤넬",
        "jewellery",
        "주얼리",
        "Fine 주얼리",
        "파인 주얼리",
        "악세서리",
        "여성",
        *cols,
    ]
    if collection_ko:
        tags.append(collection_ko)
    badge = "New" if row.get("new") else None
    story = []
    if desc_ko:
        story.append({"titleKo": name_ko, "bodyKo": desc_ko, "image": image})

    prod: dict = {
        "id": pid,
        "name": title_en,
        "nameKo": name_ko,
        "brand": "샤넬",
        "price": price,
        "category": "accessories",
        "subcategory": FINE_JEWELLERY_LEAF,
        "chCollections": cols,
        "tags": tags,
        "descriptionKo": description_ko,
        "image": image,
        "images": images,
        "accent": accent_for(str(code)),
        "badge": badge,
        "gbpPrice": float(gbp),
        "sku": code,
        "sourceUrl": row.get("url") or "",
        "inStock": True,
        "variants": variants,
        "storySections": story,
        "registeredAt": registered,
        "editTier": "new" if badge == "New" else "signature",
    }
    if is_ring:
        prod["sizeChart"] = CH_RING_SIZE_CHART
    if hover:
        prod["hoverImage"] = hover
    return apply_detail_fields(prod, row, name_ko=name_ko, image=image)


def build_sunglasses_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    code = row.get("productCode") or row.get("sku") or row.get("id")
    if not code:
        return None
    gbp = row.get("gbpPrice")
    if gbp is None:
        return None
    price = gbp_to_krw(float(gbp))
    if price <= 0:
        return None

    primary = SUNGLASSES_LEAF
    cols = sorted(set(SUNGLASSES_PARENT_COLS))

    title_en, name_ko = official_name_pair(row, code)
    details = row.get("details") or {}
    if not isinstance(details, dict):
        details = {}
    color_en = as_text(details.get("color"))
    fabrics_en = as_text(details.get("fabrics"))
    desc_en = as_text(details.get("description"))
    dims_en = format_eyewear_dims(details.get("dimensions"))
    ref = as_text(details.get("reference"))
    lens_color = as_text(details.get("eyeLensColor"))
    uv = details.get("freeStat") if isinstance(details.get("freeStat"), dict) else {}
    uv_label = as_text(uv.get("label")) if uv else ""
    treatment = details.get("treatment") if isinstance(details.get("treatment"), dict) else {}
    treatment_label = as_text(treatment.get("label")) if treatment else ""

    color_ko = t(color_en) if color_en else ""
    fabrics_ko = t(fabrics_en) if fabrics_en else ""
    desc_ko = t(desc_en) if desc_en else ""
    lens_ko = t(lens_color) if lens_color else ""

    parts = [desc_ko]
    if color_ko:
        parts.append(f"컬러: {color_ko}")
    if lens_ko:
        parts.append(f"렌즈: {lens_ko}")
    if fabrics_ko:
        parts.append(f"소재: {fabrics_ko}")
    if dims_en:
        parts.append(f"사이즈: {dims_en}")
    if uv_label:
        parts.append(f"UV: {uv_label}")
    if treatment_label:
        parts.append(f"처리: {treatment_label}")
    if ref:
        parts.append(f"레퍼런스: {ref}")
    description_ko = "\n\n".join(p for p in parts if p)

    # Prefer packshot order already stored; reuse handbag local reorder helper.
    images = reorder_locals_handbag_front(row)
    images = [
        p
        for p in images
        if (ROOT / "public" / p.lstrip("/")).is_file()
        and (ROOT / "public" / p.lstrip("/")).stat().st_size > 2048
    ]
    if not images:
        # Fall back to listed localImages order
        images = [
            p
            for p in (row.get("localImages") or [])
            if (ROOT / "public" / str(p).lstrip("/")).is_file()
            and (ROOT / "public" / str(p).lstrip("/")).stat().st_size > 2048
        ]
    if not images:
        print(f"skip no local image (sunglasses): {code}", flush=True)
        return None
    image = images[0]
    hover = images[1] if len(images) > 1 else None

    pid = f"ch-{str(code).lower()}"
    registered = (prev or {}).get("registeredAt") or now_iso

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
            "sourceUrl": row.get("url") or "",
            "inStock": True,
            "colorKey": color_en.lower() or "default",
            "colorNameKo": color_ko or color_en or "기본",
            "size": "One Size",
            "chCollections": cols,
        }
    ]
    if hover:
        variants[0]["hoverImage"] = hover

    tags = [
        "chanel",
        "샤넬",
        "sunglasses",
        "선글라스",
        "eyewear",
        "아이웨어",
        "악세서리",
        "여성",
        *cols,
    ]
    badge = "New" if row.get("new") else None
    story = []
    if desc_ko:
        story.append({"titleKo": name_ko, "bodyKo": desc_ko, "image": image})

    prod: dict = {
        "id": pid,
        "name": title_en,
        "nameKo": name_ko,
        "brand": "샤넬",
        "price": price,
        "category": "accessories",
        "subcategory": primary,
        "chCollections": cols,
        "tags": tags,
        "descriptionKo": description_ko,
        "image": image,
        "images": images,
        "accent": accent_for(str(code)),
        "badge": badge,
        "gbpPrice": float(gbp),
        "sku": code,
        "sourceUrl": row.get("url") or "",
        "inStock": True,
        "variants": variants,
        "sizeChart": CH_EYEWEAR_SIZE_CHART,
        "storySections": story,
        "registeredAt": registered,
        "editTier": "new" if badge == "New" else "signature",
    }
    if hover:
        prod["hoverImage"] = hover
    return apply_detail_fields(prod, row, name_ko=name_ko, image=image)


def build_fragrance_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    code = row.get("productCode") or row.get("sku") or row.get("id")
    if not code:
        return None
    gbp = row.get("gbpPrice")
    if gbp is None:
        return None
    price = gbp_to_krw(float(gbp))
    if price <= 0:
        return None

    primary = FRAGRANCE_LEAF
    cols = sorted(set(FRAGRANCE_PARENT_COLS))

    title_en, name_ko = official_name_pair(row, code)
    details = row.get("details") or {}
    if not isinstance(details, dict):
        details = {}
    desc_en = as_text(details.get("editorial") or details.get("description"))
    ref = as_text(details.get("reference")) or str(code)
    volume = as_text(details.get("volume") or details.get("dimensions"))
    collection = as_text(row.get("collection") or row.get("categoryLabel"))

    desc_ko = t(desc_en) if desc_en else ""
    collection_ko = t(collection) if collection else ""

    parts = [desc_ko]
    if collection_ko:
        parts.append(f"컬렉션: {collection_ko}")
    if volume:
        parts.append(f"용량: {volume}")
    if ref:
        parts.append(f"레퍼런스: {ref}")
    description_ko = "\n\n".join(p for p in parts if p)

    images = [
        p
        for p in (row.get("localImages") or [])
        if (ROOT / "public" / str(p).lstrip("/")).is_file()
        and (ROOT / "public" / str(p).lstrip("/")).stat().st_size > 2048
    ]
    if not images:
        print(f"skip no local image (fragrance): {code}", flush=True)
        return None
    image = images[0]
    hover = images[1] if len(images) > 1 else None

    pid = f"ch-{str(code).lower()}"
    registered = (prev or {}).get("registeredAt") or now_iso

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
            "sourceUrl": row.get("url") or "",
            "inStock": True,
            "colorKey": "default",
            "colorNameKo": "기본",
            "size": "One Size",
            "chCollections": cols,
        }
    ]
    if hover:
        variants[0]["hoverImage"] = hover

    tags = [
        "chanel",
        "샤넬",
        "fragrance",
        "향수",
        "perfume",
        "퍼퓸",
        "악세서리",
        *cols,
    ]
    badge = "New" if row.get("new") else None
    story = []
    if desc_ko:
        story.append({"titleKo": name_ko, "bodyKo": desc_ko, "image": image})

    prod: dict = {
        "id": pid,
        "name": title_en,
        "nameKo": name_ko,
        "brand": "샤넬",
        "price": price,
        "category": "accessories",
        "subcategory": primary,
        "chCollections": cols,
        "tags": tags,
        "descriptionKo": description_ko,
        "image": image,
        "images": images,
        "accent": accent_for(str(code)),
        "badge": badge,
        "gbpPrice": float(gbp),
        "sku": code,
        "sourceUrl": row.get("url") or "",
        "inStock": True,
        "variants": variants,
        "storySections": story,
        "registeredAt": registered,
        "editTier": "new" if badge == "New" else "signature",
    }
    if hover:
        prod["hoverImage"] = hover
    return apply_detail_fields(prod, row, name_ko=name_ko, image=image)


def build_makeup_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    code = row.get("productCode") or row.get("sku") or row.get("id")
    if not code:
        return None
    gbp = row.get("gbpPrice")
    if gbp is None:
        return None
    price = gbp_to_krw(float(gbp))
    if price <= 0:
        return None

    allowed = {"ch-makeup", *MAKEUP_SHAPE_LEAVES}
    leaves = [
        c
        for c in (row.get("leaves") or row.get("collections") or [])
        if c in MAKEUP_SHAPE_LEAVES
    ]
    leaf = row.get("leaf") if row.get("leaf") in MAKEUP_SHAPE_LEAVES else None
    if leaf and leaf not in leaves:
        leaves.append(leaf)
    if not leaves:
        leaves = ["ch-makeup-brushes"]
    primary = next((c for c in MAKEUP_SHAPE_LEAVES if c in leaves), leaves[0])
    if leaf:
        primary = leaf
    cols = sorted(set([*MAKEUP_PARENT_COLS, *leaves]) & (allowed | set(MAKEUP_PARENT_COLS)))

    title_en, name_ko = official_name_pair(row, code)
    details = row.get("details") or {}
    if not isinstance(details, dict):
        details = {}
    desc_en = as_text(details.get("editorial") or details.get("description"))
    ref = as_text(details.get("reference")) or str(code)
    shade = as_text(details.get("color"))
    collection = as_text(row.get("collection") or row.get("categoryLabel"))

    desc_ko = t(desc_en) if desc_en else ""
    collection_ko = t(collection) if collection else ""
    shade_ko = t(shade) if shade else ""

    parts = [desc_ko]
    if collection_ko:
        parts.append(f"카테고리: {collection_ko}")
    if shade_ko:
        parts.append(f"컬러: {shade_ko}")
    if ref:
        parts.append(f"레퍼런스: {ref}")
    description_ko = "\n\n".join(p for p in parts if p)

    images = [
        p
        for p in (row.get("localImages") or [])
        if (ROOT / "public" / str(p).lstrip("/")).is_file()
        and (ROOT / "public" / str(p).lstrip("/")).stat().st_size > 2048
    ]
    if not images:
        print(f"skip no local image (makeup): {code}", flush=True)
        return None
    image = images[0]
    hover = images[1] if len(images) > 1 else None

    pid = f"ch-{str(code).lower()}"
    registered = (prev or {}).get("registeredAt") or now_iso
    shade_label = shade or "One Size"
    shade_ko_label = shade_ko or "원 사이즈"

    variants = [
        {
            "id": f"{pid}-os",
            "name": f"{title_en} — {shade_label}",
            "nameKo": f"{name_ko} — {shade_ko_label}",
            "sku": code,
            "gbpPrice": float(gbp),
            "price": price,
            "image": image,
            "images": images,
            "sourceUrl": row.get("url") or "",
            "inStock": True,
            "colorKey": re.sub(r"[^a-z0-9]+", "-", shade.lower()).strip("-")
            if shade
            else "default",
            "colorNameKo": shade_ko or "기본",
            "size": "One Size",
            "chCollections": cols,
        }
    ]
    if hover:
        variants[0]["hoverImage"] = hover

    tags = [
        "chanel",
        "샤넬",
        "makeup",
        "메이크업",
        "beauty",
        "뷰티",
        "악세서리",
        *cols,
    ]
    badge = "New" if row.get("new") else None
    story = []
    if desc_ko:
        story.append({"titleKo": name_ko, "bodyKo": desc_ko, "image": image})

    prod: dict = {
        "id": pid,
        "name": title_en,
        "nameKo": name_ko,
        "brand": "샤넬",
        "price": price,
        "category": "accessories",
        "subcategory": primary,
        "chCollections": cols,
        "tags": tags,
        "descriptionKo": description_ko,
        "image": image,
        "images": images,
        "accent": accent_for(str(code)),
        "badge": badge,
        "gbpPrice": float(gbp),
        "sku": code,
        "sourceUrl": row.get("url") or "",
        "inStock": True,
        "variants": variants,
        "storySections": story,
        "registeredAt": registered,
        "editTier": "new" if badge == "New" else "signature",
    }
    if hover:
        prod["hoverImage"] = hover
    return apply_detail_fields(prod, row, name_ko=name_ko, image=image)


def build_other_acc_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    """Other accessories — keep official multi-leaf tags (e.g. scarf + winter)."""
    code = row.get("productCode") or row.get("sku") or row.get("id")
    if not code:
        return None
    gbp = row.get("gbpPrice")
    if gbp is None:
        return None
    price = gbp_to_krw(float(gbp))
    if price <= 0:
        return None

    leaves = [
        c
        for c in (row.get("leaves") or row.get("collections") or [])
        if c in OTHER_ACC_SHAPE_LEAVES
    ]
    leaf = row.get("leaf") if row.get("leaf") in OTHER_ACC_SHAPE_LEAVES else None
    if leaf and leaf not in leaves:
        leaves.append(leaf)
    if not leaves:
        return None
    primary = next((c for c in OTHER_ACC_SHAPE_LEAVES if c in leaves), leaves[0])
    if leaf:
        primary = leaf
    cols = sorted(set([*OTHER_ACC_PARENT_COLS, *leaves]))

    title_en, name_ko = official_name_pair(row, code)
    details = row.get("details") or {}
    if not isinstance(details, dict):
        details = {}
    color_en = as_text(details.get("color"))
    fabrics_en = as_text(details.get("fabrics"))
    desc_en = as_text(details.get("description"))
    dims_en = as_text(details.get("dimensions"))
    ref = as_text(details.get("reference"))

    color_ko = t(color_en) if color_en else ""
    fabrics_ko = t(fabrics_en) if fabrics_en else ""
    desc_ko = t(desc_en) if desc_en else ""
    dims_ko = t(dims_en) if dims_en else ""

    parts = [desc_ko]
    if color_ko:
        parts.append(f"컬러: {color_ko}")
    if fabrics_ko:
        parts.append(f"소재: {fabrics_ko}")
    if dims_ko:
        parts.append(f"사이즈: {dims_ko}")
    if ref:
        parts.append(f"레퍼런스: {ref}")
    description_ko = "\n\n".join(p for p in parts if p)

    images = reorder_locals_handbag_front(row)
    images = [
        p
        for p in images
        if (ROOT / "public" / p.lstrip("/")).is_file()
        and (ROOT / "public" / p.lstrip("/")).stat().st_size > 2048
    ]
    if not images:
        images = [
            p
            for p in (row.get("localImages") or [])
            if (ROOT / "public" / str(p).lstrip("/")).is_file()
            and (ROOT / "public" / str(p).lstrip("/")).stat().st_size > 2048
        ]
    if not images:
        print(f"skip no local image (other-acc): {code}", flush=True)
        return None
    image = images[0]
    hover = images[1] if len(images) > 1 else None

    pid = f"ch-{str(code).lower()}"
    registered = (prev or {}).get("registeredAt") or now_iso

    size_rows = row.get("sizes") or []
    variants: list[dict] = []
    for sz in size_rows:
        size_raw = str(sz.get("orliSize") or sz.get("size") or "").strip() or "UNI"
        label = format_other_acc_size_label(size_raw, leaves)
        slug = size_slug(size_raw if size_raw.upper() != "UNI" else "os")
        sku = str(sz.get("sku") or sz.get("id") or f"{code}-{slug}")
        v: dict = {
            "id": f"{pid}-{slug}",
            "name": f"{title_en} — {label}",
            "nameKo": f"{name_ko} — {label if label != 'One Size' else '원 사이즈'}",
            "sku": sku,
            "gbpPrice": float(gbp),
            "price": price,
            "image": image,
            "images": images,
            "sourceUrl": row.get("url") or "",
            "inStock": True,
            "colorKey": color_en.lower() or "default",
            "colorNameKo": color_ko or color_en or "기본",
            "size": label,
            "chCollections": cols,
        }
        if hover:
            v["hoverImage"] = hover
        variants.append(v)

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
                "sourceUrl": row.get("url") or "",
                "inStock": True,
                "colorKey": color_en.lower() or "default",
                "colorNameKo": color_ko or color_en or "기본",
                "size": "One Size",
                "chCollections": cols,
            }
        ]
        if hover:
            variants[0]["hoverImage"] = hover

    tags = [
        "chanel",
        "샤넬",
        "other accessories",
        "기타 악세서리",
        "악세서리",
        "여성",
        *cols,
    ]
    badge = "New" if row.get("new") else None
    story = []
    if desc_ko:
        story.append({"titleKo": name_ko, "bodyKo": desc_ko, "image": image})

    size_chart = None
    if "ch-women-belts" in leaves:
        size_chart = CH_BELT_SIZE_CHART
    elif "ch-women-headwear" in leaves:
        size_chart = CH_HAT_SIZE_CHART

    prod: dict = {
        "id": pid,
        "name": title_en,
        "nameKo": name_ko,
        "brand": "샤넬",
        "price": price,
        "category": "accessories",
        "subcategory": primary,
        "chCollections": cols,
        "tags": tags,
        "descriptionKo": description_ko,
        "image": image,
        "images": images,
        "accent": accent_for(str(code)),
        "badge": badge,
        "gbpPrice": float(gbp),
        "sku": code,
        "sourceUrl": row.get("url") or "",
        "inStock": True,
        "variants": variants,
        "storySections": story,
        "registeredAt": registered,
        "editTier": "new" if badge == "New" else "signature",
    }
    if size_chart:
        prod["sizeChart"] = size_chart
    if hover:
        prod["hoverImage"] = hover
    return apply_detail_fields(prod, row, name_ko=name_ko, image=image)


def build_watch_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    code = row.get("productCode") or row.get("sku") or row.get("id")
    if not code:
        return None
    gbp = row.get("gbpPrice")
    if gbp is None:
        return None
    price = gbp_to_krw(float(gbp))
    if price <= 0:
        return None

    leaves = [
        c
        for c in (row.get("leaves") or row.get("collections") or [])
        if c in WATCH_SHAPE_LEAVES
    ]
    leaf = row.get("leaf") if row.get("leaf") in WATCH_SHAPE_LEAVES else None
    if leaf and leaf not in leaves:
        leaves.insert(0, leaf)
    if not leaves:
        leaves = ["ch-watches-j12"]
    primary = next((c for c in WATCH_SHAPE_LEAVES if c in leaves), leaves[0])

    cols = sorted(set([*WATCH_PARENT_COLS, *leaves]))
    title_en, name_ko = official_name_pair(row, code)
    details = row.get("details") or {}
    if not isinstance(details, dict):
        details = {}
    color_en = as_text(details.get("color"))
    fabrics_en = as_text(details.get("fabrics"))
    desc_en = as_text(details.get("description"))
    dims_en = as_text(details.get("dimensions"))
    ref = as_text(details.get("reference"))
    collection_en = as_text(row.get("collection"))

    color_ko = t(color_en) if color_en else ""
    fabrics_ko = t(fabrics_en) if fabrics_en else ""
    desc_ko = t(desc_en) if desc_en else ""
    dims_ko = t(dims_en) if dims_en else ""
    collection_ko = t(collection_en) if collection_en else ""

    parts = [desc_ko]
    if collection_ko:
        parts.append(f"컬렉션: {collection_ko}")
    if color_ko:
        parts.append(f"컬러: {color_ko}")
    if fabrics_ko:
        parts.append(f"소재: {fabrics_ko}")
    if dims_ko:
        parts.append(f"스펙: {dims_ko}")
    if ref:
        parts.append(f"레퍼런스: {ref}")
    description_ko = "\n\n".join(p for p in parts if p)

    images = reorder_locals_shoe_front(row)
    images = [
        p
        for p in images
        if (ROOT / "public" / p.lstrip("/")).is_file()
        and (ROOT / "public" / p.lstrip("/")).stat().st_size > 2048
    ]
    if not images:
        images = [
            p
            for p in (row.get("localImages") or [])
            if (ROOT / "public" / str(p).lstrip("/")).is_file()
            and (ROOT / "public" / str(p).lstrip("/")).stat().st_size > 2048
        ]
    if not images:
        print(f"skip no local image (watches): {code}", flush=True)
        return None
    image = images[0]
    hover = images[1] if len(images) > 1 else None

    pid = f"ch-{str(code).lower()}"
    registered = (prev or {}).get("registeredAt") or now_iso
    leaf_label = {
        "ch-watches-j12": "J12",
        "ch-watches-premiere": "Première",
        "ch-watches-boy-friend": "BOY·FRIEND",
        "ch-watches-monsieur": "Monsieur",
        "ch-watches-code-coco": "Code Coco",
    }.get(primary, "Watches")

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
            "sourceUrl": row.get("url") or "",
            "inStock": True,
            "colorKey": color_en.lower() or "default",
            "colorNameKo": color_ko or color_en or "기본",
            "size": "One Size",
            "chCollections": cols,
        }
    ]
    if hover:
        variants[0]["hoverImage"] = hover

    tags = [
        "chanel",
        "샤넬",
        "watches",
        "시계",
        leaf_label,
        "여성",
        "남성",
        *cols,
    ]
    if collection_ko:
        tags.append(collection_ko)
    badge = "New" if row.get("new") else None
    story = []
    if desc_ko:
        story.append({"titleKo": name_ko, "bodyKo": desc_ko, "image": image})

    prod: dict = {
        "id": pid,
        "name": title_en,
        "nameKo": name_ko,
        "brand": "샤넬",
        "price": price,
        "category": "watches",
        "subcategory": primary,
        "chCollections": cols,
        "tags": tags,
        "descriptionKo": description_ko,
        "image": image,
        "images": images,
        "accent": accent_for(str(code)),
        "badge": badge,
        "gbpPrice": float(gbp),
        "sku": code,
        "sourceUrl": row.get("url") or "",
        "inStock": True,
        "variants": variants,
        "storySections": story,
        "registeredAt": registered,
        "editTier": "new" if badge == "New" else "signature",
    }
    if hover:
        prod["hoverImage"] = hover
    return apply_detail_fields(prod, row, name_ko=name_ko, image=image)


def main() -> int:
    prev_map = load_prev()
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    products: list[dict] = []
    seen: set[str] = set()

    rtw_rows: list[dict] = []
    if RAW_PATH.exists():
        rtw_rows = json.loads(RAW_PATH.read_text()).get("products") or []
    else:
        print(f"WARN missing RTW raw: {RAW_PATH}", flush=True)

    bag_rows: list[dict] = []
    if HANDBAGS_RAW_PATH.exists():
        bag_rows = json.loads(HANDBAGS_RAW_PATH.read_text()).get("products") or []
    else:
        print(f"WARN missing handbags raw: {HANDBAGS_RAW_PATH}", flush=True)

    slg_rows: list[dict] = []
    if SLG_RAW_PATH.exists():
        slg_rows = json.loads(SLG_RAW_PATH.read_text()).get("products") or []
    else:
        print(f"WARN missing SLG raw: {SLG_RAW_PATH}", flush=True)

    shoe_rows: list[dict] = []
    if SHOES_RAW_PATH.exists():
        shoe_rows = json.loads(SHOES_RAW_PATH.read_text()).get("products") or []
    else:
        print(f"WARN missing shoes raw: {SHOES_RAW_PATH}", flush=True)

    jew_rows: list[dict] = []
    if JEWELLERY_RAW_PATH.exists():
        jew_rows = json.loads(JEWELLERY_RAW_PATH.read_text()).get("products") or []
    else:
        print(f"WARN missing jewellery raw: {JEWELLERY_RAW_PATH}", flush=True)

    hj_rows: list[dict] = []
    if HIGH_JEWELLERY_RAW_PATH.exists():
        hj_rows = json.loads(HIGH_JEWELLERY_RAW_PATH.read_text()).get("products") or []
    else:
        print(f"WARN missing high-jewellery raw: {HIGH_JEWELLERY_RAW_PATH}", flush=True)

    fj_rows: list[dict] = []
    if FINE_JEWELLERY_RAW_PATH.exists():
        fj_rows = json.loads(FINE_JEWELLERY_RAW_PATH.read_text()).get("products") or []
    else:
        print(f"WARN missing fine-jewellery raw: {FINE_JEWELLERY_RAW_PATH}", flush=True)

    sunglass_rows: list[dict] = []
    if SUNGLASSES_RAW_PATH.exists():
        sunglass_rows = json.loads(SUNGLASSES_RAW_PATH.read_text()).get("products") or []
    else:
        print(f"WARN missing sunglasses raw: {SUNGLASSES_RAW_PATH}", flush=True)

    fragrance_rows: list[dict] = []
    if FRAGRANCE_RAW_PATH.exists():
        fragrance_rows = json.loads(FRAGRANCE_RAW_PATH.read_text()).get("products") or []
    else:
        print(f"WARN missing fragrance raw: {FRAGRANCE_RAW_PATH}", flush=True)

    makeup_rows: list[dict] = []
    if MAKEUP_RAW_PATH.exists():
        makeup_rows = json.loads(MAKEUP_RAW_PATH.read_text()).get("products") or []
    else:
        print(f"WARN missing makeup raw: {MAKEUP_RAW_PATH}", flush=True)

    other_acc_rows: list[dict] = []
    if OTHER_ACC_RAW_PATH.exists():
        other_acc_rows = json.loads(OTHER_ACC_RAW_PATH.read_text()).get("products") or []
    else:
        print(f"WARN missing other-acc raw: {OTHER_ACC_RAW_PATH}", flush=True)

    watch_rows: list[dict] = []
    if WATCHES_RAW_PATH.exists():
        watch_rows = json.loads(WATCHES_RAW_PATH.read_text()).get("products") or []
    else:
        print(f"WARN missing watches raw: {WATCHES_RAW_PATH}", flush=True)

    def _is_slg_prev(p: dict) -> bool:
        cols = set(p.get("chCollections") or [])
        return "ch-slg" in cols or p.get("subcategory") in SLG_SHAPE_LEAVES

    def _is_jew_prev(p: dict) -> bool:
        cols = set(p.get("chCollections") or [])
        return "ch-jewellery" in cols or p.get("subcategory") in JEWELLERY_SHAPE_LEAVES

    def _is_hj_prev(p: dict) -> bool:
        cols = set(p.get("chCollections") or [])
        return HIGH_JEWELLERY_LEAF in cols or p.get("subcategory") == HIGH_JEWELLERY_LEAF

    def _is_fj_prev(p: dict) -> bool:
        cols = set(p.get("chCollections") or [])
        return FINE_JEWELLERY_LEAF in cols or p.get("subcategory") == FINE_JEWELLERY_LEAF

    def _is_sunglass_prev(p: dict) -> bool:
        cols = set(p.get("chCollections") or [])
        return (
            "ch-sunglasses" in cols
            or p.get("subcategory") == SUNGLASSES_LEAF
        )

    def _is_fragrance_prev(p: dict) -> bool:
        cols = set(p.get("chCollections") or [])
        return FRAGRANCE_LEAF in cols or p.get("subcategory") == FRAGRANCE_LEAF

    def _is_makeup_prev(p: dict) -> bool:
        cols = set(p.get("chCollections") or [])
        return (
            "ch-makeup" in cols
            or p.get("subcategory") in MAKEUP_SHAPE_LEAVES
        )

    def _is_other_acc_prev(p: dict) -> bool:
        cols = set(p.get("chCollections") or [])
        return (
            "ch-other-accessories" in cols
            or p.get("subcategory") in OTHER_ACC_SHAPE_LEAVES
        )

    def _is_watch_prev(p: dict) -> bool:
        cols = set(p.get("chCollections") or [])
        return (
            "chanel-watches" in cols
            or "ch-watches" in cols
            or p.get("subcategory") in WATCH_SHAPE_LEAVES
        )

    # Keep existing catalog rows when a raw source is missing (partial rebuild).
    if (
        not rtw_rows
        or not bag_rows
        or not slg_rows
        or not shoe_rows
        or not jew_rows
        or not hj_rows
        or not fj_rows
        or not sunglass_rows
        or not fragrance_rows
        or not makeup_rows
        or not other_acc_rows
        or not watch_rows
    ):
        for prev in prev_map.values():
            cat = prev.get("category")
            if not rtw_rows and cat == "luxury":
                products.append(prev)
                seen.add(prev["id"])
            if cat == "bags" and not _is_slg_prev(prev):
                if not bag_rows:
                    products.append(prev)
                    seen.add(prev["id"])
            if not slg_rows and _is_slg_prev(prev):
                products.append(prev)
                seen.add(prev["id"])
            if not shoe_rows and cat == "shoes":
                products.append(prev)
                seen.add(prev["id"])
            if not watch_rows and _is_watch_prev(prev):
                products.append(prev)
                seen.add(prev["id"])
            if cat == "accessories" and not _is_slg_prev(prev):
                if not jew_rows and _is_jew_prev(prev):
                    products.append(prev)
                    seen.add(prev["id"])
                if not hj_rows and _is_hj_prev(prev):
                    products.append(prev)
                    seen.add(prev["id"])
                if not fj_rows and _is_fj_prev(prev):
                    products.append(prev)
                    seen.add(prev["id"])
                if not sunglass_rows and _is_sunglass_prev(prev):
                    products.append(prev)
                    seen.add(prev["id"])
                if not fragrance_rows and _is_fragrance_prev(prev):
                    if prev["id"] not in seen:
                        products.append(prev)
                        seen.add(prev["id"])
                if not makeup_rows and _is_makeup_prev(prev):
                    if prev["id"] not in seen:
                        products.append(prev)
                        seen.add(prev["id"])
                if not other_acc_rows and _is_other_acc_prev(prev):
                    products.append(prev)
                    seen.add(prev["id"])
                if (
                    not jew_rows
                    and not hj_rows
                    and not fj_rows
                    and not sunglass_rows
                    and not fragrance_rows
                    and not makeup_rows
                    and not other_acc_rows
                    and not _is_jew_prev(prev)
                    and not _is_hj_prev(prev)
                    and not _is_fj_prev(prev)
                    and not _is_sunglass_prev(prev)
                    and not _is_fragrance_prev(prev)
                    and not _is_makeup_prev(prev)
                    and not _is_other_acc_prev(prev)
                ):
                    products.append(prev)
                    seen.add(prev["id"])

    for i, row in enumerate(rtw_rows, start=1):
        if row.get("_skip"):
            continue
        pid_guess = f"ch-{str(row.get('sku') or row.get('id') or '').lower()}"
        prod = build_product(row, prev_map.get(pid_guess), now_iso)
        if not prod or prod["id"] in seen:
            continue
        seen.add(prod["id"])
        products.append(prod)
        if i % 40 == 0:
            CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2))
            print(f"built RTW {i}/{len(rtw_rows)}", flush=True)

    for i, row in enumerate(bag_rows, start=1):
        if row.get("_skip"):
            continue
        pid_guess = f"ch-{str(row.get('sku') or row.get('id') or '').lower()}"
        prod = build_handbag_product(row, prev_map.get(pid_guess), now_iso)
        if not prod or prod["id"] in seen:
            continue
        seen.add(prod["id"])
        products.append(prod)
        if i % 40 == 0:
            CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2))
            print(f"built bags {i}/{len(bag_rows)}", flush=True)

    for i, row in enumerate(slg_rows, start=1):
        if row.get("_skip"):
            continue
        pid_guess = f"ch-{str(row.get('sku') or row.get('id') or '').lower()}"
        prod = build_slg_product(row, prev_map.get(pid_guess), now_iso)
        if not prod or prod["id"] in seen:
            continue
        seen.add(prod["id"])
        products.append(prod)
        if i % 40 == 0:
            CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2))
            print(f"built SLG {i}/{len(slg_rows)}", flush=True)

    for i, row in enumerate(shoe_rows, start=1):
        if row.get("_skip"):
            continue
        pid_guess = f"ch-{str(row.get('sku') or row.get('id') or '').lower()}"
        prod = build_shoe_product(row, prev_map.get(pid_guess), now_iso)
        if not prod or prod["id"] in seen:
            continue
        seen.add(prod["id"])
        products.append(prod)
        if i % 40 == 0:
            CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2))
            print(f"built shoes {i}/{len(shoe_rows)}", flush=True)

    for i, row in enumerate(jew_rows, start=1):
        if row.get("_skip"):
            continue
        pid_guess = f"ch-{str(row.get('sku') or row.get('id') or '').lower()}"
        prod = build_jewellery_product(row, prev_map.get(pid_guess), now_iso)
        if not prod or prod["id"] in seen:
            continue
        seen.add(prod["id"])
        products.append(prod)
        if i % 40 == 0:
            CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2))
            print(f"built jewellery {i}/{len(jew_rows)}", flush=True)

    for i, row in enumerate(hj_rows, start=1):
        if row.get("_skip"):
            continue
        pid_guess = f"ch-{str(row.get('sku') or row.get('id') or '').lower()}"
        prod = build_high_jewellery_product(row, prev_map.get(pid_guess), now_iso)
        if not prod or prod["id"] in seen:
            continue
        seen.add(prod["id"])
        products.append(prod)
        if i % 20 == 0:
            CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2))
            print(f"built high-jewellery {i}/{len(hj_rows)}", flush=True)

    for i, row in enumerate(fj_rows, start=1):
        if row.get("_skip"):
            continue
        pid_guess = f"ch-{str(row.get('sku') or row.get('id') or '').lower()}"
        # Prefer Fine over High if a SKU somehow appears in both (should not).
        if pid_guess in seen:
            continue
        prod = build_fine_jewellery_product(row, prev_map.get(pid_guess), now_iso)
        if not prod or prod["id"] in seen:
            continue
        seen.add(prod["id"])
        products.append(prod)
        if i % 40 == 0:
            CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2))
            print(f"built fine-jewellery {i}/{len(fj_rows)}", flush=True)

    for i, row in enumerate(sunglass_rows, start=1):
        if row.get("_skip"):
            continue
        pid_guess = f"ch-{str(row.get('sku') or row.get('id') or '').lower()}"
        prod = build_sunglasses_product(row, prev_map.get(pid_guess), now_iso)
        if not prod or prod["id"] in seen:
            continue
        seen.add(prod["id"])
        products.append(prod)
        if i % 40 == 0:
            CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2))
            print(f"built sunglasses {i}/{len(sunglass_rows)}", flush=True)

    for i, row in enumerate(fragrance_rows, start=1):
        if row.get("_skip"):
            continue
        pid_guess = f"ch-{str(row.get('sku') or row.get('id') or '').lower()}"
        prod = build_fragrance_product(row, prev_map.get(pid_guess), now_iso)
        if not prod or prod["id"] in seen:
            continue
        seen.add(prod["id"])
        products.append(prod)
        if i % 40 == 0:
            CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2))
            print(f"built fragrance {i}/{len(fragrance_rows)}", flush=True)

    by_id = {p["id"]: p for p in products}

    def _makeup_cols_from_row(row: dict) -> list[str]:
        leaves = [
            c
            for c in (row.get("leaves") or row.get("collections") or [])
            if c in MAKEUP_SHAPE_LEAVES
        ]
        leaf = row.get("leaf") if row.get("leaf") in MAKEUP_SHAPE_LEAVES else None
        if leaf and leaf not in leaves:
            leaves.append(leaf)
        if not leaves:
            leaves = ["ch-makeup-brushes"]
        return sorted(set([*MAKEUP_PARENT_COLS, *leaves]))

    def _merge_makeup_onto(existing: dict, row: dict) -> None:
        extra = _makeup_cols_from_row(row)
        cols = sorted(set(existing.get("chCollections") or []) | set(extra))
        existing["chCollections"] = cols
        tags = list(dict.fromkeys([*(existing.get("tags") or []), "makeup", "메이크업", "beauty", "뷰티", *cols]))
        existing["tags"] = tags
        for v in existing.get("variants") or []:
            if isinstance(v, dict):
                v["chCollections"] = sorted(set(v.get("chCollections") or []) | set(extra))

    for i, row in enumerate(makeup_rows, start=1):
        if row.get("_skip"):
            continue
        pid_guess = f"ch-{str(row.get('sku') or row.get('id') or '').lower()}"
        if pid_guess in seen:
            existing = by_id.get(pid_guess)
            if existing:
                _merge_makeup_onto(existing, row)
            continue
        prod = build_makeup_product(row, prev_map.get(pid_guess), now_iso)
        if not prod or prod["id"] in seen:
            continue
        seen.add(prod["id"])
        by_id[prod["id"]] = prod
        products.append(prod)
        if i % 40 == 0:
            CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2))
            print(f"built makeup {i}/{len(makeup_rows)}", flush=True)

    for i, row in enumerate(other_acc_rows, start=1):
        if row.get("_skip"):
            continue
        pid_guess = f"ch-{str(row.get('sku') or row.get('id') or '').lower()}"
        prod = build_other_acc_product(row, prev_map.get(pid_guess), now_iso)
        if not prod or prod["id"] in seen:
            continue
        seen.add(prod["id"])
        products.append(prod)
        if i % 40 == 0:
            CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2))
            print(f"built other-acc {i}/{len(other_acc_rows)}", flush=True)

    for i, row in enumerate(watch_rows, start=1):
        if row.get("_skip"):
            continue
        pid_guess = f"ch-{str(row.get('sku') or row.get('id') or '').lower()}"
        prod = build_watch_product(row, prev_map.get(pid_guess), now_iso)
        if not prod or prod["id"] in seen:
            continue
        seen.add(prod["id"])
        products.append(prod)
        if i % 20 == 0:
            CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2))
            print(f"built watches {i}/{len(watch_rows)}", flush=True)

    products.sort(key=lambda p: p["id"])
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n")
    OUT_TS.write_text(
        'import type { Product } from "@/data/product-types";\n'
        'import data from "./ch-catalog.json";\n\n'
        "/** Auto-generated — Chanel RTW + Handbags + SLG + Shoes + Jewellery + High/Fine Jewellery + Sunglasses + Fragrance + Makeup + Other Accessories + Watches. */\n"
        "export const chCatalogProducts = data as unknown as Product[];\n"
    )
    CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2) + "\n")

    leaf_n = {
        leaf: 0
        for leaf in [
            *SHAPE_LEAVES,
            *BAG_SHAPE_LEAVES,
            *SLG_SHAPE_LEAVES,
            *SHOE_SHAPE_LEAVES,
            *JEWELLERY_SHAPE_LEAVES,
            HIGH_JEWELLERY_LEAF,
            FINE_JEWELLERY_LEAF,
            SUNGLASSES_LEAF,
            FRAGRANCE_LEAF,
            *MAKEUP_SHAPE_LEAVES,
            *OTHER_ACC_SHAPE_LEAVES,
            *WATCH_SHAPE_LEAVES,
            "ch-women-looks",
        ]
    }
    in_stock = sum(1 for p in products if p.get("inStock"))
    bags_n = sum(1 for p in products if p.get("category") == "bags")
    luxury_n = sum(1 for p in products if p.get("category") == "luxury")
    shoes_n = sum(1 for p in products if p.get("category") == "shoes")
    jew_n = sum(1 for p in products if p.get("category") == "accessories")
    watches_n = sum(
        1
        for p in products
        if p.get("category") == "watches"
        and (
            "chanel-watches" in (p.get("chCollections") or [])
            or "ch-watches" in (p.get("chCollections") or [])
            or p.get("subcategory") in WATCH_SHAPE_LEAVES
        )
    )
    for p in products:
        for c in p.get("chCollections") or []:
            if c in leaf_n:
                leaf_n[c] += 1

    print(f"Wrote {len(products)} products → {OUT_JSON}", flush=True)
    print(
        f"luxury={luxury_n} bags={bags_n} shoes={shoes_n} accessories={jew_n} "
        f"watches={watches_n} inStock={in_stock}",
        flush=True,
    )
    print(f"leafCounts={leaf_n}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
