#!/usr/bin/env python3
"""Build Chanel catalogue → src/data/ch/ch-catalog.json + ch-catalog.ts.

Sources:
  - ch-rtw-catalog-raw.json → category luxury (RTW)
  - ch-handbags-catalog-raw.json → category bags
  - ch-slg-catalog-raw.json → category bags (small leather goods)
  - ch-shoes-catalog-raw.json → category shoes
  - ch-jewellery-catalog-raw.json → category accessories

Pricing (same as Gucci): KRW = round_만원(GBP × 2100 × 1.05 × 1.15)
Korean copy via gtx + ch-translate-cache.json.
RTW size chart: French FR 34–50. Handbags / SLG: One Size + dimensions in copy.
Shoes: EU (French) sizes as shown on chanel.com GB PDPs.
Costume jewellery: mostly One Size (UNI); rings use French ring sizes + chart.
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

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "src/data/ch/ch-rtw-catalog-raw.json"
HANDBAGS_RAW_PATH = ROOT / "src/data/ch/ch-handbags-catalog-raw.json"
SLG_RAW_PATH = ROOT / "src/data/ch/ch-slg-catalog-raw.json"
SHOES_RAW_PATH = ROOT / "src/data/ch/ch-shoes-catalog-raw.json"
JEWELLERY_RAW_PATH = ROOT / "src/data/ch/ch-jewellery-catalog-raw.json"
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
    "ch-the-chanel-handbag",
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

SLG_PARENT_COLS = ["chanel", "chanel-bags", "ch-slg"]

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

    title_en = (row.get("title") or "").strip() or str(code)
    details = row.get("details") or {}
    color_en = (details.get("color") or "").strip()
    fabrics_en = (details.get("fabrics") or "").strip()
    desc_en = (details.get("description") or "").strip()
    ref = (details.get("reference") or "").strip()

    name_ko = t(title_en)
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
    return prod


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

    title_en = as_text(row.get("title")) or str(code)
    details = row.get("details") or {}
    if not isinstance(details, dict):
        details = {}
    color_en = as_text(details.get("color"))
    fabrics_en = as_text(details.get("fabrics"))
    desc_en = as_text(details.get("description"))
    dims_en = as_text(details.get("dimensions"))
    ref = as_text(details.get("reference"))

    name_ko = t(title_en)
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
    return prod


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

    title_en = as_text(row.get("title")) or str(code)
    details = row.get("details") or {}
    if not isinstance(details, dict):
        details = {}
    color_en = as_text(details.get("color"))
    fabrics_en = as_text(details.get("fabrics"))
    desc_en = as_text(details.get("description"))
    dims_en = as_text(details.get("dimensions"))
    ref = as_text(details.get("reference"))

    name_ko = t(title_en)
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
        "가방",
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
    return prod


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

    title_en = as_text(row.get("title")) or str(code)
    details = row.get("details") or {}
    if not isinstance(details, dict):
        details = {}
    color_en = as_text(details.get("color"))
    fabrics_en = as_text(details.get("fabrics"))
    desc_en = as_text(details.get("description"))
    ref = as_text(details.get("reference"))

    name_ko = t(title_en)
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
    return prod


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

    title_en = as_text(row.get("title")) or str(code)
    details = row.get("details") or {}
    if not isinstance(details, dict):
        details = {}
    color_en = as_text(details.get("color"))
    fabrics_en = as_text(details.get("fabrics"))
    desc_en = as_text(details.get("description"))
    dims_en = as_text(details.get("dimensions"))
    ref = as_text(details.get("reference"))

    name_ko = t(title_en)
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
    return prod


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

    def _is_slg_prev(p: dict) -> bool:
        cols = set(p.get("chCollections") or [])
        return "ch-slg" in cols or p.get("subcategory") in SLG_SHAPE_LEAVES

    # Keep existing catalog rows when a raw source is missing (partial rebuild).
    if not rtw_rows or not bag_rows or not slg_rows or not shoe_rows or not jew_rows:
        for prev in prev_map.values():
            cat = prev.get("category")
            if not rtw_rows and cat == "luxury":
                products.append(prev)
                seen.add(prev["id"])
            if cat == "bags":
                if not bag_rows and not _is_slg_prev(prev):
                    products.append(prev)
                    seen.add(prev["id"])
                if not slg_rows and _is_slg_prev(prev):
                    products.append(prev)
                    seen.add(prev["id"])
            if not shoe_rows and cat == "shoes":
                products.append(prev)
                seen.add(prev["id"])
            if not jew_rows and cat == "accessories":
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

    products.sort(key=lambda p: p["id"])
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n")
    OUT_TS.write_text(
        'import type { Product } from "@/data/product-types";\n'
        'import data from "./ch-catalog.json";\n\n'
        "/** Auto-generated — Chanel RTW + Handbags + SLG + Shoes + Jewellery. */\n"
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
            "ch-women-looks",
        ]
    }
    in_stock = sum(1 for p in products if p.get("inStock"))
    bags_n = sum(1 for p in products if p.get("category") == "bags")
    luxury_n = sum(1 for p in products if p.get("category") == "luxury")
    shoes_n = sum(1 for p in products if p.get("category") == "shoes")
    jew_n = sum(1 for p in products if p.get("category") == "accessories")
    for p in products:
        for c in p.get("chCollections") or []:
            if c in leaf_n:
                leaf_n[c] += 1

    print(f"Wrote {len(products)} products → {OUT_JSON}", flush=True)
    print(
        f"luxury={luxury_n} bags={bags_n} shoes={shoes_n} accessories={jew_n} "
        f"inStock={in_stock}",
        flush=True,
    )
    print(f"leafCounts={leaf_n}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
