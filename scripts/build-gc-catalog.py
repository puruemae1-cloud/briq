#!/usr/bin/env python3
"""Build Gucci catalogue from scraped raw (handbags + RTW + shoes + wallets + travel).

Pricing: KRW = round_천원(GBP × 2100 × 1.05 × 1.15)
Prefer official Korean copy from Gucci catalog API; fall back to gtx translate.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

from plp_hover import pick_hover_local

ROOT = Path(__file__).resolve().parents[1]
HANDBAG_RAW = ROOT / "src/data/gc/gc-catalog-raw.json"
RTW_RAW = ROOT / "src/data/gc/gc-rtw-catalog-raw.json"
SHOES_RAW = ROOT / "src/data/gc/gc-shoes-catalog-raw.json"
WALLETS_RAW = ROOT / "src/data/gc/gc-wallets-catalog-raw.json"
TRAVEL_RAW = ROOT / "src/data/gc/gc-travel-catalog-raw.json"
OUT_JSON = ROOT / "src/data/gc/gc-catalog.json"
OUT_TS = ROOT / "src/data/gc/gc-catalog.ts"
CACHE_PATH = ROOT / "src/data/gc/gc-translate-cache.json"

# Back-compat alias
RAW_PATH = HANDBAG_RAW

HANDBAG_LEAF_COLLECTIONS = [
    "gc-women-shoulder-bags",
    "gc-women-mini-bags",
    "gc-women-crossbody-bags",
    "gc-women-tote-bags",
    "gc-women-top-handle-bags",
    "gc-women-backpacks-beltbags",
    "gc-women-clutches-evening",
    "gc-women-personalised",
]

RTW_LEAF_COLLECTIONS = [
    "gc-women-knitwear",
    "gc-women-tops-shirts",
    "gc-women-tshirts-sweatshirts",
    "gc-women-dresses",
    "gc-women-pants-shorts",
    "gc-women-denim",
    "gc-women-skirts",
    "gc-women-swimwear",
    "gc-women-coats-jackets",
    "gc-women-outerwear",
    "gc-women-leather",
    "gc-women-activewear",
    "gc-women-cocktail-evening",
]

SHOES_LEAF_COLLECTIONS = [
    "gc-women-sneakers",
    "gc-women-moccasins",
    "gc-women-slippers-mules",
    "gc-women-sandals",
    "gc-women-slides",
    "gc-women-pumps",
    "gc-women-ballet-flats",
    "gc-women-boots",
]

SHOES_PARENT_COLLECTIONS = [
    "gc-women-shoes",
    "gc-shoes-womens",
    "gucci-shoes",
]

WALLETS_LEAF_COLLECTIONS = [
    "gc-women-long-wallets",
    "gc-women-chain-wallets",
    "gc-women-compact-wallets",
    "gc-women-card-holders",
    "gc-women-bag-charms-keychains",
    "gc-women-pouches",
    "gc-women-tech-accessories",
]

WALLETS_PARENT_COLLECTIONS = [
    "gc-women-wallets",
    "gc-accessories-womens",
    "gucci-accessories",
]

TRAVEL_LEAF_COLLECTIONS = [
    "gc-women-trolley",
    "gc-women-weekend-duffle",
    "gc-women-travel-accessories",
    "gc-women-hard-shell-luggage",
]

TRAVEL_PARENT_COLLECTIONS = [
    "gc-women-travel",
    "gc-accessories-womens",
    "gucci-accessories",
]

# Keep old name for any external imports
LEAF_COLLECTIONS = HANDBAG_LEAF_COLLECTIONS

_STYLE_COLOR_RE = re.compile(r"^(\d{6})([A-Z0-9]{5})(\d{4})$", re.I)


def style_color_key(sku: str) -> tuple[str, str] | None:
    m = _STYLE_COLOR_RE.match(str(sku or "").strip())
    if not m:
        return None
    return m.group(1).upper(), m.group(3).upper()

# Official Gucci women RTW size guide (Tops / Bottoms) — letter SIZE + IT mapping.
# Jeans column on bottoms matches gucci.com size guide (KnowSize / brand tables).
GC_WOMEN_RTW_TOPS = {
    "id": "tops",
    "labelKo": "상의",
    "headers": ["SIZE", "IT", "EU", "UK/AU", "US", "JP", "SHOULDER (CM/IN)"],
    "rows": [
        ["XXXS", "34", "30", "2", "00", "3", "37 / 14.6"],
        ["XXS", "36", "32", "4", "0", "5", "38 / 15"],
        ["XS", "38", "34", "6", "2", "7", "39 / 15.4"],
        ["S", "40", "36", "8", "4", "9", "40 / 15.7"],
        ["M", "42", "38", "10", "6", "11", "41 / 16.1"],
        ["L", "44", "40", "12", "8", "13", "42.5 / 16.7"],
        ["XL", "46", "42", "14", "10", "15", "44 / 17.3"],
        ["XXL", "48", "44", "16", "12", "17", "45.5 / 17.9"],
        ["XXXL", "50", "46", "18", "14", "19", "47 / 18.5"],
        ["4XL", "52", "48", "20", "16", "21", "48.5 / 19"],
    ],
}

GC_WOMEN_RTW_BOTTOMS = {
    "id": "bottoms",
    "labelKo": "하의",
    "headers": [
        "SIZE",
        "IT",
        "EU",
        "UK/AU",
        "US",
        "JP",
        "JEANS",
        "WAIST (CM/IN)",
        "HIP (CM/IN)",
    ],
    "rows": [
        ["XXXS", "34", "30", "2", "00", "3", "20", "59 / 23.2", "85 / 33.5"],
        ["XXS", "36", "32", "4", "0", "5", "22", "62 / 24.4", "88 / 34.6"],
        ["XS", "38", "34", "6", "2", "7", "24", "65 / 25.6", "91 / 35.8"],
        ["S", "40", "36", "8", "4", "9", "26", "68 / 26.8", "94 / 37"],
        ["M", "42", "38", "10", "6", "11", "28", "71 / 27.9", "97 / 38.2"],
        ["L", "44", "40", "12", "8", "13", "30", "75 / 29.5", "101 / 39.8"],
        ["XL", "46", "42", "14", "10", "15", "32", "79 / 31.1", "105 / 41.3"],
        ["XXL", "48", "44", "16", "12", "17", "34", "83 / 32.7", "109 / 42.9"],
        ["XXXL", "50", "46", "18", "14", "19", "36", "87 / 34.3", "113 / 44.5"],
        ["4XL", "52", "48", "20", "16", "21", "38", "91 / 35.8", "117 / 46.1"],
    ],
}

# Denim / jeans waist sizes as sold on gucci.com (Briq labels them "IT 23" etc.).
# Primary JEANS column matches the PDP size picker; IT column is apparel conversion.
GC_WOMEN_DENIM_ROWS = [
    # jeans, size, IT, EU, UK/AU, US, JP, waist, hip
    ["20", "XXXS", "34", "30", "2", "00", "3", "59 / 23.2", "85 / 33.5"],
    ["21", "XXXS", "35", "31", "3", "00", "4", "60.5 / 23.8", "86.5 / 34.1"],
    ["22", "XXS", "36", "32", "4", "0", "5", "62 / 24.4", "88 / 34.6"],
    ["23", "XXS", "37", "33", "5", "1", "6", "63.5 / 25", "89.5 / 35.2"],
    ["24", "XS", "38", "34", "6", "2", "7", "65 / 25.6", "91 / 35.8"],
    ["25", "XS", "39", "34", "6", "2", "7", "66.5 / 26.2", "92.5 / 36.4"],
    ["26", "S", "40", "36", "8", "4", "9", "68 / 26.8", "94 / 37"],
    ["27", "S", "41", "36", "8", "4", "9", "69.5 / 27.4", "95.5 / 37.6"],
    ["28", "M", "42", "38", "10", "6", "11", "71 / 27.9", "97 / 38.2"],
    ["29", "M", "43", "38", "10", "6", "11", "73 / 28.7", "99 / 39"],
    ["30", "L", "44", "40", "12", "8", "13", "75 / 29.5", "101 / 39.8"],
    ["31", "L", "45", "40", "12", "8", "13", "77 / 30.3", "103 / 40.6"],
    ["32", "XL", "46", "42", "14", "10", "15", "79 / 31.1", "105 / 41.3"],
    ["33", "XL", "47", "42", "14", "10", "15", "81 / 31.9", "107 / 42.1"],
    ["34", "XXL", "48", "44", "16", "12", "17", "83 / 32.7", "109 / 42.9"],
    ["35", "XXL", "49", "44", "16", "12", "17", "85 / 33.5", "111 / 43.7"],
    ["36", "XXXL", "50", "46", "18", "14", "19", "87 / 34.3", "113 / 44.5"],
]

GC_WOMEN_DENIM = {
    "id": "denim",
    "labelKo": "진/데님",
    "headers": [
        "JEANS",
        "SIZE",
        "IT",
        "EU",
        "UK/AU",
        "US",
        "JP",
        "WAIST (CM/IN)",
        "HIP (CM/IN)",
    ],
    "rows": GC_WOMEN_DENIM_ROWS,
}

GC_WOMEN_RTW_SIZE_CHART = {
    "id": "gc-women-rtw",
    "titleKo": "구찌 여성 레디투웨어 사이즈 가이드",
    "noteKo": (
        "사이즈표는 신체 치수 기준입니다. 구찌 여성 의류는 이탈리아(IT) 사이즈를 "
        "기준으로 하며, Briq 표기의 XS·S·M 또는 IT 숫자는 아래 SIZE/IT 열과 대응합니다. "
        "진·데님은 JEANS(허리) 사이즈를 사용합니다. 브랜드·시즌·실루엣에 따라 핏이 "
        "다를 수 있으니 참고용으로 확인해 주세요."
    ),
    "headers": GC_WOMEN_RTW_TOPS["headers"],
    "rows": GC_WOMEN_RTW_TOPS["rows"],
    "tabs": [GC_WOMEN_RTW_TOPS, GC_WOMEN_RTW_BOTTOMS, GC_WOMEN_DENIM],
}

GC_WOMEN_DENIM_SIZE_CHART = {
    "id": "gc-women-denim",
    "titleKo": "구찌 여성 진/데님 사이즈 가이드",
    "noteKo": (
        "이 상품은 진/데님 허리 사이즈(JEANS)로 판매됩니다. 사이즈 선택란의 "
        "IT 23·IT 24 등은 진 허리 사이즈이며, 일반 의류 IT 34·36과는 다릅니다. "
        "아래 JEANS 열을 기준으로 골라 주세요."
    ),
    "headers": GC_WOMEN_DENIM["headers"],
    "rows": GC_WOMEN_DENIM["rows"],
    "tabs": [GC_WOMEN_DENIM, GC_WOMEN_RTW_BOTTOMS, GC_WOMEN_RTW_TOPS],
}

# Official Gucci UK women shoes size guide
# (https://www.gucci.com/uk/en_gb/st/shoes-size-guide — Women's Shoes Size Chart).
# PDP pickers use IT sizes; half sizes appear as 34+ in catalog API → IT 34.5.
GC_WOMEN_SHOES_ROWS = [
    # IT, UK, FR, US, AU, KR(mm), JP(cm)
    ["34", "1", "35", "4", "3.5", "210", "21"],
    ["34.5", "1.5", "35.5", "4.5", "4", "215", "21.5"],
    ["35", "2", "36", "5", "4.5", "220", "22"],
    ["35.5", "2.5", "36.5", "5.5", "5", "225", "22.5"],
    ["36", "3", "37", "6", "5.5", "230", "23"],
    ["36.5", "3.5", "37.5", "6.5", "6", "235", "23.5"],
    ["37", "4", "38", "7", "6.5", "240", "24"],
    ["37.5", "4.5", "38.5", "7.5", "7", "245", "24.5"],
    ["38", "5", "39", "8", "7.5", "250", "25"],
    ["38.5", "5.5", "39.5", "8.5", "8", "255", "25.5"],
    ["39", "6", "40", "9", "8.5", "260", "26"],
    ["39.5", "6.5", "40.5", "9.5", "9", "265", "26.5"],
    ["40", "7", "41", "10", "9.5", "270", "27"],
    ["40.5", "7.5", "41.5", "10.5", "10", "275", "27.5"],
    ["41", "8", "42", "11", "10.5", "280", "28"],
    ["41.5", "8.5", "42.5", "11.5", "11", "285", "28.5"],
    ["42", "9", "43", "12", "11.5", "290", "29"],
    # Extended for SKUs sold above official women chart max (IT 42)
    ["42.5", "9.5", "43.5", "12.5", "12", "295", "29.5"],
    ["43", "10", "44", "13", "12.5", "300", "30"],
]

GC_WOMEN_SHOES_SIZE_CHART = {
    "id": "gc-women-shoes",
    "titleKo": "구찌 여성 슈즈 사이즈 가이드",
    "noteKo": (
        "사이즈표는 구찌 공식 여성 슈즈 가이드 기준입니다. Briq 표기 사이즈는 "
        "이탈리아(IT) 기준이며, 사이즈 선택란의 IT 37·IT 37.5 등은 아래 IT 열과 "
        "대응합니다. FR는 프랑스 사이즈입니다. IT 42.5·43은 일부 상품에만 "
        "제공되며 공식 표의 패턴을 연장한 값입니다. 스타일·소재에 따라 핏이 "
        "다를 수 있으니 참고용으로 확인해 주세요."
    ),
    "headers": ["IT", "UK", "FR", "US", "AU", "KR (MM)", "JP (CM)"],
    "rows": GC_WOMEN_SHOES_ROWS,
}


def _variant_size_numbers(variants: list[dict]) -> list[int]:
    nums: list[int] = []
    for v in variants:
        label = str(v.get("size") or "")
        m = re.search(r"(\d{2})", label)
        if m:
            nums.append(int(m.group(1)))
    return nums


def size_chart_for_rtw(variants: list[dict]) -> dict:
    """Pick denim jeans chart when PDP sizes are waist 20–36, else RTW guide."""
    nums = _variant_size_numbers(variants)
    if nums and max(nums) <= 36 and min(nums) <= 28 and max(nums) - min(nums) <= 20:
        # Jeans waist run (e.g. 23–32), not apparel IT 36–50
        if max(nums) < 36 or min(nums) < 34:
            return GC_WOMEN_DENIM_SIZE_CHART
    return GC_WOMEN_RTW_SIZE_CHART


def gbp_to_krw(gbp: float | None) -> int:
    if gbp is None:
        return 0
    base = float(gbp) * 2100 * 1.05 * 1.15
    return int(round(base / 1_000) * 1_000)


_KO: dict[str, str] = {}
if CACHE_PATH.exists():
    _KO = json.loads(CACHE_PATH.read_text())


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


def t(text: str | None) -> str:
    s = re.sub(r"\s+", " ", (text or "").strip())
    if not s:
        return ""
    if s in _KO and en_ratio(_KO[s]) < 0.55:
        return _KO[s]
    if en_ratio(s) < 0.35 or len(s) < 4:
        return s
    try:
        ko = gtx(s).strip()
        if ko:
            _KO[s] = ko
            return ko
    except Exception:
        pass
    return s


def html_to_text(html: str) -> str:
    s = unescape(html or "")
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"</p>", "\n", s, flags=re.I)
    s = re.sub(r"<li>", "• ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n\n", s)
    return s.strip()


def accent_for(key: str) -> str:
    h = hashlib.md5((key or "x").encode()).hexdigest()
    r = 40 + int(h[0:2], 16) % 80
    g = 40 + int(h[2:4], 16) % 80
    b = 40 + int(h[4:6], 16) % 80
    return f"#{r:02x}{g:02x}{b:02x}"


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:70] or "item"


def clean_name_ko(name: str) -> str:
    s = (name or "").strip()
    m = re.match(r"^\[([^\]]+)\]\s*(.*)$", s)
    if m:
        inner, rest = m.group(1).strip(), m.group(2).strip()
        return f"{inner} {rest}".strip() if rest else inner
    return s


_IMPORTER_GUCCI_KR_RE = re.compile(
    r"수입자\s*:?\s*구찌코리아",
    flags=re.I,
)


def strip_gucci_warranty(text: str) -> str:
    if not text:
        return ""
    s = text.replace("\xa0", " ").replace("\u202f", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"품질보증기준\s*:[^·\n]*", "", s, flags=re.I)
    s = re.sub(
        r"AS\s*유선접수\s*:[^·\n]*clientservice\.kr@gucci\.com",
        "",
        s,
        flags=re.I,
    )
    s = re.sub(r"clientservice\.kr@gucci\.com", "", s, flags=re.I)
    s = re.sub(
        r"AS\s*유선접수\s*:[^·\n]*02-3452-1921[^·\n]*",
        "",
        s,
        flags=re.I,
    )
    # Official KR detailParts include importer line; drop from Briq PDP copy.
    s = _IMPORTER_GUCCI_KR_RE.sub("", s)
    s = re.sub(r"(?:\s*[·•]\s*){2,}", " · ", s)
    s = re.sub(r"^\s*[·•]\s*", "", s)
    s = re.sub(r"\s*[·•]\s*$", "", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r"[ \t]+\n", "\n", s)
    return s.strip(" \t·•\n")


def is_gucci_warranty_line(line: str) -> bool:
    s = (line or "").replace("\xa0", " ")
    if "품질보증기준" in s:
        return True
    if "clientservice.kr@gucci.com" in s.lower():
        return True
    if re.search(r"AS\s*유선접수", s, flags=re.I):
        return True
    if _IMPORTER_GUCCI_KR_RE.search(s):
        return True
    return False


def detail_lines(parts: list | None) -> list[str]:
    out: list[str] = []
    for p in parts or []:
        line = html_to_text(str(p))
        if not line:
            continue
        if re.fullmatch(r"[A-Z]{1,3}\d{2}", line):
            continue
        if is_gucci_warranty_line(line):
            cleaned = strip_gucci_warranty(line)
            if cleaned:
                out.append(cleaned)
            continue
        if "전자의료" in line or "electromedical" in line.lower() or "WARNING:" in line:
            before = re.split(r"WARNING:|경고:", line, maxsplit=1)[0].strip()
            if before:
                out.append(before)
            continue
        out.append(line)
    return out


def care_lines(care: str | None) -> list[str]:
    if not care:
        return []
    return [html_to_text(x) for x in care.split("|") if html_to_text(x)]


def format_size_label(size: str) -> str:
    s = (size or "").strip()
    if not s:
        return "One Size"
    # Shoe half sizes already normalized to 34.5 in scraper
    if re.fullmatch(r"\d+(\.\d+)?", s):
        return f"IT {s}"
    if s.isdigit():
        return f"IT {s}"
    return s.upper() if len(s) <= 4 else s


def format_shoe_size_label(size: str) -> str:
    s = (size or "").strip()
    if not s:
        return "One Size"
    if s.endswith("+") and s[:-1].replace(".", "", 1).isdigit():
        s = f"{s[:-1]}.5"
    if re.fullmatch(r"\d+(\.\d+)?", s):
        return f"IT {s}"
    return s


def size_slug(size: str) -> str:
    return slugify(format_size_label(size))


def common_copy(row: dict) -> dict:
    ko = row.get("translationKo") or {}
    en = row.get("translationEn") or {}
    code = row.get("productCode") or row.get("id") or ""

    title_en = (row.get("title") or en.get("name") or code).strip()
    name_ko = clean_name_ko(ko.get("name") or "") or t(title_en)

    color_en = (row.get("variant") or en.get("variationDescription") or "").strip()
    color_ko = (ko.get("variationDescription") or "").strip() or (
        t(color_en) if color_en else ""
    )
    colors = ko.get("colors") or en.get("colors") or []
    if not color_ko and colors:
        color_ko = colors[0].get("name") or ""

    editorial_ko = strip_gucci_warranty(
        html_to_text(ko.get("editorialDescription") or "")
    )
    editorial_en = html_to_text(en.get("editorialDescription") or "")
    if not editorial_ko and editorial_en:
        editorial_ko = strip_gucci_warranty(t(editorial_en))

    details_ko = [
        strip_gucci_warranty(x) for x in detail_lines(ko.get("detailParts"))
    ]
    details_ko = [x for x in details_ko if x]
    if not details_ko:
        details_ko = [
            strip_gucci_warranty(t(x))
            for x in detail_lines(en.get("detailParts"))
        ]
        details_ko = [x for x in details_ko if x]

    care_ko = care_lines(ko.get("materialCare"))
    if not care_ko:
        care_ko = [t(x) for x in care_lines(en.get("materialCare"))]

    materials_ko = ko.get("materials") or []
    if not materials_ko and en.get("materials"):
        materials_ko = [t(x) for x in en["materials"]]

    images = list(row.get("localImages") or [])
    if not images and row.get("localImage"):
        images = [row["localImage"]]
    if not images:
        remotes = row.get("images") or (
            [] if not row.get("image") else [row["image"]]
        )
        images = remotes[:1]

    image = images[0] if images else ""
    hover = (
        row.get("localHover")
        or pick_hover_local(
            images,
            remote_images=row.get("images") or [],
            explicit=None,
        )
        or image
    )

    description_bits = [editorial_ko] if editorial_ko else []
    if details_ko:
        description_bits.append(" · ".join(details_ko[:8]))
    description_ko = strip_gucci_warranty(
        "\n\n".join(x for x in description_bits if x).strip()
    )

    story: list[dict] = []
    if editorial_ko:
        story.append(
            {"titleKo": name_ko, "bodyKo": editorial_ko, "image": image}
        )
    if details_ko:
        story.append(
            {
                "titleKo": "디테일",
                "bodyKo": strip_gucci_warranty(" · ".join(details_ko)),
                "image": images[1] if len(images) > 1 else image,
                "reverse": True,
            }
        )
    if materials_ko:
        story.append(
            {
                "titleKo": "소재",
                "bodyKo": " · ".join(materials_ko),
                "image": images[2] if len(images) > 2 else image,
            }
        )
    if care_ko:
        story.append(
            {
                "titleKo": "케어",
                "bodyKo": " · ".join(care_ko),
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
                "bodyKo": f"{name_ko}의 디테일.",
                "image": img,
                "layout": "wide",
                "reverse": i % 2 == 0,
            }
        )

    return {
        "code": code,
        "title_en": title_en,
        "name_ko": name_ko,
        "color_en": color_en,
        "color_ko": color_ko,
        "color_key": slugify(color_en or color_ko or "default"),
        "images": images,
        "image": image,
        "hover": hover,
        "description_ko": description_ko,
        "story": story,
    }


def build_handbag_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    code = row.get("productCode") or row.get("id")
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
        if c in HANDBAG_LEAF_COLLECTIONS or c == "gc-handbags"
    ]
    if any(c in HANDBAG_LEAF_COLLECTIONS for c in cols) and "gc-handbags" not in cols:
        cols.append("gc-handbags")
    cols = sorted(set(cols))
    if not cols:
        cols = ["gc-handbags"]

    leaf = next((c for c in HANDBAG_LEAF_COLLECTIONS if c in cols), "gc-handbags")
    copy = common_copy(row)
    pid = f"gc-{str(code).lower()}"
    registered = (prev or {}).get("registeredAt") or now_iso

    variant = {
        "id": f"{pid}-u",
        "name": f"{copy['title_en']} — {copy['color_en'] or 'One Size'}".strip(" —"),
        "nameKo": f"{copy['name_ko']} — {copy['color_ko'] or '원 사이즈'}".strip(" —"),
        "sku": code,
        "gbpPrice": float(gbp),
        "price": price,
        "image": copy["image"],
        "images": copy["images"],
        "hoverImage": copy["hover"],
        "sourceUrl": row.get("url") or "",
        "inStock": bool(row.get("inStock", True)),
        "colorKey": copy["color_key"],
        "colorNameKo": copy["color_ko"] or copy["color_en"] or "기본",
        "size": "One Size",
        "gcCollections": cols,
    }

    tags = ["gucci", "구찌", "handbag", "핸드백", *cols]
    badge = None
    label = (row.get("label") or "").lower()
    if "new" in label:
        badge = "New"

    return {
        "id": pid,
        "name": copy["title_en"],
        "nameKo": copy["name_ko"],
        "brand": "구찌",
        "price": price,
        "category": "bags",
        "subcategory": leaf,
        "gcCollections": cols,
        "tags": tags,
        "descriptionKo": copy["description_ko"],
        "image": copy["image"],
        "images": copy["images"],
        "hoverImage": copy["hover"],
        "accent": accent_for(code),
        "badge": badge,
        "gbpPrice": float(gbp),
        "sku": code,
        "sourceUrl": row.get("url") or "",
        "inStock": bool(row.get("inStock", True)),
        "variants": [variant],
        "storySections": copy["story"],
        "registeredAt": registered,
        "editTier": "new" if badge == "New" else "signature",
    }


def build_rtw_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    code = row.get("productCode") or row.get("id")
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
        if c in {*RTW_LEAF_COLLECTIONS, "gc-women-rtw", "gc-women", "gucci"}
    ]
    cols = sorted(set([*cols, "gc-women-rtw", "gc-women", "gucci"]))

    leaf = next((c for c in RTW_LEAF_COLLECTIONS if c in cols), "gc-women-rtw")
    copy = common_copy(row)
    pid = f"gc-{str(code).lower()}"
    registered = (prev or {}).get("registeredAt") or now_iso
    in_stock = bool(row.get("inStock", True))

    size_rows = row.get("sizes") or []
    variants: list[dict] = []
    if size_rows:
        for sz in size_rows:
            size_raw = str(sz.get("size") or "").strip()
            if not size_raw:
                continue
            label = format_size_label(size_raw)
            slug = size_slug(size_raw)
            sku = str(sz.get("sku") or f"{code}-{slug}")
            variants.append(
                {
                    "id": f"{pid}-{slug}",
                    "name": f"{copy['title_en']} — {label}",
                    "nameKo": f"{copy['name_ko']} — {label}",
                    "sku": sku,
                    "gbpPrice": float(gbp),
                    "price": price,
                    "image": copy["image"],
                    "images": copy["images"],
                    "hoverImage": copy["hover"],
                    "sourceUrl": row.get("url") or "",
                    "inStock": in_stock,
                    "colorKey": copy["color_key"],
                    "colorNameKo": copy["color_ko"] or copy["color_en"] or "기본",
                    "size": label,
                    "gcCollections": cols,
                }
            )
    if not variants:
        variants = [
            {
                "id": f"{pid}-os",
                "name": f"{copy['title_en']} — One Size",
                "nameKo": f"{copy['name_ko']} — 원 사이즈",
                "sku": code,
                "gbpPrice": float(gbp),
                "price": price,
                "image": copy["image"],
                "images": copy["images"],
                "hoverImage": copy["hover"],
                "sourceUrl": row.get("url") or "",
                "inStock": in_stock,
                "colorKey": copy["color_key"],
                "colorNameKo": copy["color_ko"] or copy["color_en"] or "기본",
                "size": "One Size",
                "gcCollections": cols,
            }
        ]

    tags = ["gucci", "구찌", "rtw", "의류", "여성", "ready-to-wear", *cols]
    badge = None
    label = (row.get("label") or "").lower()
    if "new" in label:
        badge = "New"

    return {
        "id": pid,
        "name": copy["title_en"],
        "nameKo": copy["name_ko"],
        "brand": "구찌",
        "price": price,
        "category": "luxury",
        "subcategory": leaf,
        "gcCollections": cols,
        "tags": tags,
        "descriptionKo": copy["description_ko"],
        "image": copy["image"],
        "images": copy["images"],
        "hoverImage": copy["hover"],
        "accent": accent_for(code),
        "badge": badge,
        "gbpPrice": float(gbp),
        "sku": code,
        "sourceUrl": row.get("url") or "",
        "inStock": in_stock,
        "variants": variants,
        "sizeChart": size_chart_for_rtw(variants),
        "storySections": copy["story"],
        "registeredAt": registered,
        "editTier": "new" if badge == "New" else "signature",
    }


def build_wallet_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    """Wallets / small leather — One Size; dimensions live in PDP detail copy.

    Matches handbag pattern (no apparel size chart). Official detailParts often
    include W×H×D strings which land in descriptionKo via common_copy.
    """
    code = row.get("productCode") or row.get("id")
    if not code:
        return None
    gbp = row.get("gbpPrice")
    if gbp is None:
        return None
    price = gbp_to_krw(float(gbp))
    if price <= 0:
        return None

    allowed = {*WALLETS_LEAF_COLLECTIONS, *WALLETS_PARENT_COLLECTIONS}
    cols = [c for c in (row.get("collections") or []) if c in allowed]
    cols = sorted(set([*cols, *WALLETS_PARENT_COLLECTIONS]))

    leaf = next(
        (c for c in WALLETS_LEAF_COLLECTIONS if c in cols), "gc-women-wallets"
    )
    copy = common_copy(row)
    pid = f"gc-{str(code).lower()}"
    registered = (prev or {}).get("registeredAt") or now_iso

    variant = {
        "id": f"{pid}-u",
        "name": f"{copy['title_en']} — {copy['color_en'] or 'One Size'}".strip(" —"),
        "nameKo": f"{copy['name_ko']} — {copy['color_ko'] or '원 사이즈'}".strip(" —"),
        "sku": code,
        "gbpPrice": float(gbp),
        "price": price,
        "image": copy["image"],
        "images": copy["images"],
        "hoverImage": copy["hover"],
        "sourceUrl": row.get("url") or "",
        "inStock": bool(row.get("inStock", True)),
        "colorKey": copy["color_key"],
        "colorNameKo": copy["color_ko"] or copy["color_en"] or "기본",
        "size": "One Size",
        "gcCollections": cols,
    }

    tags = ["gucci", "구찌", "wallet", "월렛", "악세서리", "여성", *cols]
    badge = None
    label = (row.get("label") or "").lower()
    if "new" in label:
        badge = "New"

    return {
        "id": pid,
        "name": copy["title_en"],
        "nameKo": copy["name_ko"],
        "brand": "구찌",
        "price": price,
        "category": "accessories",
        "subcategory": leaf,
        "gcCollections": cols,
        "tags": tags,
        "descriptionKo": copy["description_ko"],
        "image": copy["image"],
        "images": copy["images"],
        "hoverImage": copy["hover"],
        "accent": accent_for(code),
        "badge": badge,
        "gbpPrice": float(gbp),
        "sku": code,
        "sourceUrl": row.get("url") or "",
        "inStock": bool(row.get("inStock", True)),
        "variants": [variant],
        "storySections": copy["story"],
        "registeredAt": registered,
        "editTier": "new" if badge == "New" else "signature",
    }


def build_travel_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    """Travel bags / luggage — One Size; W×H×D + capacity in PDP detail copy.

    Same pattern as handbags/wallets (no apparel size chart).
    """
    code = row.get("productCode") or row.get("id")
    if not code:
        return None
    gbp = row.get("gbpPrice")
    if gbp is None:
        return None
    price = gbp_to_krw(float(gbp))
    if price <= 0:
        return None

    allowed = {*TRAVEL_LEAF_COLLECTIONS, *TRAVEL_PARENT_COLLECTIONS}
    cols = [c for c in (row.get("collections") or []) if c in allowed]
    cols = sorted(set([*cols, *TRAVEL_PARENT_COLLECTIONS]))

    leaf = next(
        (c for c in TRAVEL_LEAF_COLLECTIONS if c in cols), "gc-women-travel"
    )
    copy = common_copy(row)
    pid = f"gc-{str(code).lower()}"
    registered = (prev or {}).get("registeredAt") or now_iso

    variant = {
        "id": f"{pid}-u",
        "name": f"{copy['title_en']} — {copy['color_en'] or 'One Size'}".strip(" —"),
        "nameKo": f"{copy['name_ko']} — {copy['color_ko'] or '원 사이즈'}".strip(" —"),
        "sku": code,
        "gbpPrice": float(gbp),
        "price": price,
        "image": copy["image"],
        "images": copy["images"],
        "hoverImage": copy["hover"],
        "sourceUrl": row.get("url") or "",
        "inStock": bool(row.get("inStock", True)),
        "colorKey": copy["color_key"],
        "colorNameKo": copy["color_ko"] or copy["color_en"] or "기본",
        "size": "One Size",
        "gcCollections": cols,
    }

    tags = [
        "gucci",
        "구찌",
        "travel",
        "여행",
        "luggage",
        "러기지",
        "악세서리",
        "여성",
        *cols,
    ]
    badge = None
    label = (row.get("label") or "").lower()
    if "new" in label:
        badge = "New"

    return {
        "id": pid,
        "name": copy["title_en"],
        "nameKo": copy["name_ko"],
        "brand": "구찌",
        "price": price,
        "category": "accessories",
        "subcategory": leaf,
        "gcCollections": cols,
        "tags": tags,
        "descriptionKo": copy["description_ko"],
        "image": copy["image"],
        "images": copy["images"],
        "hoverImage": copy["hover"],
        "accent": accent_for(code),
        "badge": badge,
        "gbpPrice": float(gbp),
        "sku": code,
        "sourceUrl": row.get("url") or "",
        "inStock": bool(row.get("inStock", True)),
        "variants": [variant],
        "storySections": copy["story"],
        "registeredAt": registered,
        "editTier": "new" if badge == "New" else "signature",
    }


def build_shoe_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    code = row.get("productCode") or row.get("id")
    if not code:
        return None
    gbp = row.get("gbpPrice")
    if gbp is None:
        return None
    price = gbp_to_krw(float(gbp))
    if price <= 0:
        return None

    allowed = {*SHOES_LEAF_COLLECTIONS, *SHOES_PARENT_COLLECTIONS}
    cols = [c for c in (row.get("collections") or []) if c in allowed]
    cols = sorted(set([*cols, *SHOES_PARENT_COLLECTIONS]))

    leaf = next((c for c in SHOES_LEAF_COLLECTIONS if c in cols), "gc-women-shoes")
    copy = common_copy(row)
    pid = f"gc-{str(code).lower()}"
    registered = (prev or {}).get("registeredAt") or now_iso
    in_stock = bool(row.get("inStock", True))

    size_rows = row.get("sizes") or []
    variants: list[dict] = []
    if size_rows:
        for sz in size_rows:
            size_raw = str(sz.get("size") or "").strip()
            if not size_raw:
                continue
            label = format_shoe_size_label(size_raw)
            slug = size_slug(label)
            sku = str(sz.get("sku") or f"{code}-{slug}")
            variants.append(
                {
                    "id": f"{pid}-{slug}",
                    "name": f"{copy['title_en']} — {label}",
                    "nameKo": f"{copy['name_ko']} — {label}",
                    "sku": sku,
                    "gbpPrice": float(gbp),
                    "price": price,
                    "image": copy["image"],
                    "images": copy["images"],
                    "hoverImage": copy["hover"],
                    "sourceUrl": row.get("url") or "",
                    "inStock": in_stock,
                    "colorKey": copy["color_key"],
                    "colorNameKo": copy["color_ko"] or copy["color_en"] or "기본",
                    "size": label,
                    "gcCollections": cols,
                }
            )
    if not variants:
        variants = [
            {
                "id": f"{pid}-os",
                "name": f"{copy['title_en']} — One Size",
                "nameKo": f"{copy['name_ko']} — 원 사이즈",
                "sku": code,
                "gbpPrice": float(gbp),
                "price": price,
                "image": copy["image"],
                "images": copy["images"],
                "hoverImage": copy["hover"],
                "sourceUrl": row.get("url") or "",
                "inStock": in_stock,
                "colorKey": copy["color_key"],
                "colorNameKo": copy["color_ko"] or copy["color_en"] or "기본",
                "size": "One Size",
                "gcCollections": cols,
            }
        ]

    tags = ["gucci", "구찌", "shoes", "슈즈", "여성", *cols]
    badge = None
    label = (row.get("label") or "").lower()
    if "new" in label:
        badge = "New"

    return {
        "id": pid,
        "name": copy["title_en"],
        "nameKo": copy["name_ko"],
        "brand": "구찌",
        "price": price,
        "category": "shoes",
        "subcategory": leaf,
        "gcCollections": cols,
        "tags": tags,
        "descriptionKo": copy["description_ko"],
        "image": copy["image"],
        "images": copy["images"],
        "hoverImage": copy["hover"],
        "accent": accent_for(code),
        "badge": badge,
        "gbpPrice": float(gbp),
        "sku": code,
        "sourceUrl": row.get("url") or "",
        "inStock": in_stock,
        "variants": variants,
        "sizeChart": GC_WOMEN_SHOES_SIZE_CHART,
        "storySections": copy["story"],
        "registeredAt": registered,
        "editTier": "new" if badge == "New" else "signature",
    }


def build_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    kind = (row.get("kind") or "").lower()
    cols = row.get("collections") or []
    if kind == "shoes" or any(
        c in SHOES_LEAF_COLLECTIONS or c in SHOES_PARENT_COLLECTIONS for c in cols
    ):
        return build_shoe_product(row, prev, now_iso)
    if kind == "rtw" or any(
        c in RTW_LEAF_COLLECTIONS or c in {"gc-women-rtw", "gc-women"} for c in cols
    ):
        return build_rtw_product(row, prev, now_iso)
    # Travel before wallets — shared parents (gucci-accessories) must not misroute.
    if kind == "travel" or any(
        c in TRAVEL_LEAF_COLLECTIONS or c == "gc-women-travel" for c in cols
    ):
        return build_travel_product(row, prev, now_iso)
    if kind == "wallets" or any(
        c in WALLETS_LEAF_COLLECTIONS or c == "gc-women-wallets" for c in cols
    ):
        return build_wallet_product(row, prev, now_iso)
    return build_handbag_product(row, prev, now_iso)


def dedupe_style_color_name(products: list[dict]) -> list[dict]:
    """Drop near-duplicate colourways that share style + colour code + name.

    Gucci keys by full productCode (style+material+colour). Some materials are
    distinct PDPs for the same black cardigan / Jackie bag — keep the richer
    gallery and drop the rest so PLP/PDP don't show clones.
    """
    pat = re.compile(r"^(\d{6})([A-Z0-9]{5})(\d{4})$", re.I)
    buckets: dict[tuple[str, str, str], list[dict]] = {}
    passthrough: list[dict] = []
    for p in products:
        sku = str(p.get("sku") or "").upper()
        m = pat.match(sku)
        if not m:
            passthrough.append(p)
            continue
        style, _mat, color = m.groups()
        name = str(p.get("name") or "").strip().lower()
        buckets.setdefault((style, color.upper(), name), []).append(p)

    kept: list[dict] = list(passthrough)
    dropped = 0
    for group in buckets.values():
        if len(group) == 1:
            kept.append(group[0])
            continue
        ranked = sorted(
            group,
            key=lambda p: (
                len(p.get("images") or []),
                len(p.get("variants") or []),
                p.get("id") or "",
            ),
            reverse=True,
        )
        kept.append(ranked[0])
        dropped += len(ranked) - 1
        for loser in ranked[1:]:
            print(
                f"dedupe drop {loser.get('id')} (keep {ranked[0].get('id')})",
                flush=True,
            )
    if dropped:
        print(f"dedupe removed {dropped} style+color+name clones", flush=True)
    kept.sort(key=lambda p: p["id"])
    return kept


def load_rows() -> tuple[list[dict], dict, dict]:
    """Load raw rows. Wallets/travel skip duplicates already in handbags or catalog."""
    rows: list[dict] = []
    existing_skus: set[str] = set()
    existing_ids: set[str] = set()
    existing_style_colors: set[tuple[str, str]] = set()

    def remember(sku: str) -> None:
        if not sku:
            return
        existing_skus.add(sku.upper())
        existing_ids.add(f"gc-{sku.lower()}")
        sc = style_color_key(sku)
        if sc:
            existing_style_colors.add(sc)

    if HANDBAG_RAW.exists():
        data = json.loads(HANDBAG_RAW.read_text())
        for row in data.get("products") or []:
            row = dict(row)
            row.setdefault("kind", "handbag")
            sku = str(row.get("productCode") or row.get("id") or "")
            remember(sku)
            rows.append(row)
    if RTW_RAW.exists():
        data = json.loads(RTW_RAW.read_text())
        for row in data.get("products") or []:
            row = dict(row)
            row["kind"] = "rtw"
            sku = str(row.get("productCode") or row.get("id") or "")
            remember(sku)
            rows.append(row)
    if SHOES_RAW.exists():
        data = json.loads(SHOES_RAW.read_text())
        for row in data.get("products") or []:
            row = dict(row)
            row["kind"] = "shoes"
            sku = str(row.get("productCode") or row.get("id") or "")
            remember(sku)
            rows.append(row)

    wallet_stats = {
        "raw": 0,
        "skipped_bag_sku": 0,
        "skipped_bag_style_color": 0,
        "kept": 0,
    }
    if WALLETS_RAW.exists():
        data = json.loads(WALLETS_RAW.read_text())
        for row in data.get("products") or []:
            wallet_stats["raw"] += 1
            row = dict(row)
            row["kind"] = "wallets"
            sku = str(row.get("productCode") or row.get("id") or "")
            if sku.upper() in existing_skus or f"gc-{sku.lower()}" in existing_ids:
                wallet_stats["skipped_bag_sku"] += 1
                continue
            sc = style_color_key(sku)
            if sc and sc in existing_style_colors:
                wallet_stats["skipped_bag_style_color"] += 1
                continue
            wallet_stats["kept"] += 1
            remember(sku)
            rows.append(row)

    travel_stats = {
        "raw": 0,
        "skipped_existing_sku": 0,
        "skipped_existing_id": 0,
        "skipped_style_color": 0,
        "kept": 0,
    }
    if TRAVEL_RAW.exists():
        data = json.loads(TRAVEL_RAW.read_text())
        for row in data.get("products") or []:
            travel_stats["raw"] += 1
            row = dict(row)
            row["kind"] = "travel"
            sku = str(row.get("productCode") or row.get("id") or "")
            briq_id = f"gc-{sku.lower()}" if sku else ""
            if sku.upper() in existing_skus:
                travel_stats["skipped_existing_sku"] += 1
                continue
            if briq_id and briq_id in existing_ids:
                travel_stats["skipped_existing_id"] += 1
                continue
            sc = style_color_key(sku)
            if sc and sc in existing_style_colors:
                travel_stats["skipped_style_color"] += 1
                continue
            travel_stats["kept"] += 1
            remember(sku)
            rows.append(row)

    return rows, wallet_stats, travel_stats


def main() -> None:
    rows, wallet_stats, travel_stats = load_rows()
    if not rows:
        raise SystemExit(
            "Missing Gucci raw catalogues — run scrape-gc-handbags.py, "
            "scrape-gc-womens-rtw.py, scrape-gc-womens-shoes.py, "
            "scrape-gc-womens-wallets.py and/or scrape-gc-womens-travel.py first"
        )

    prev_by_sku: dict[str, dict] = {}
    if OUT_JSON.exists():
        for p in json.loads(OUT_JSON.read_text()):
            if p.get("sku"):
                prev_by_sku[str(p["sku"])] = p

    now_iso = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    products: list[dict] = []
    seen_ids: set[str] = set()
    for i, row in enumerate(rows, start=1):
        sku = str(row.get("productCode") or row.get("id") or "")
        prod = build_product(row, prev_by_sku.get(sku), now_iso)
        if not prod:
            continue
        if prod["id"] in seen_ids:
            # Later sources (rtw/shoes) may overwrite handbags of same code
            # only when kind is rtw/shoes — keep first unless shoes/rtw wins.
            # Wallets/travel never overwrite bags (already filtered in load_rows).
            if row.get("kind") in {"rtw", "shoes"}:
                products = [p for p in products if p["id"] != prod["id"]]
                products.append(prod)
            continue
        seen_ids.add(prod["id"])
        products.append(prod)
        if i % 50 == 0:
            CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2))
            print(f"built {i}/{len(rows)}", flush=True)
            time.sleep(0.05)

    products.sort(key=lambda p: p["id"])
    products = dedupe_style_color_name(products)
    OUT_JSON.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n")
    OUT_TS.write_text(
        'import type { Product } from "@/data/products";\n'
        'import data from "./gc-catalog.json";\n\n'
        "/** Auto-generated — Gucci handbags + RTW + shoes + wallets + travel. */\n"
        "export const gcCatalogProducts = data as unknown as Product[];\n"
    )
    CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2))
    print(f"Wrote {len(products)} products → {OUT_JSON}", flush=True)
    bags_n = sum(1 for p in products if p.get("category") == "bags")
    rtw_n = sum(1 for p in products if p.get("category") == "luxury")
    shoes_n = sum(1 for p in products if p.get("category") == "shoes")
    acc_n = sum(1 for p in products if p.get("category") == "accessories")
    travel_n = sum(
        1
        for p in products
        if "gc-women-travel" in (p.get("gcCollections") or [])
        or any(
            c in TRAVEL_LEAF_COLLECTIONS for c in (p.get("gcCollections") or [])
        )
    )
    print(
        f"  handbags: {bags_n}  rtw: {rtw_n}  shoes: {shoes_n}  "
        f"accessories: {acc_n}  travel: {travel_n}",
        flush=True,
    )
    if wallet_stats["raw"]:
        print(
            f"  wallets raw={wallet_stats['raw']} "
            f"kept={wallet_stats['kept']} "
            f"skipped_bag_sku={wallet_stats['skipped_bag_sku']} "
            f"skipped_bag_style_color={wallet_stats['skipped_bag_style_color']}",
            flush=True,
        )
    if travel_stats["raw"]:
        print(
            f"  travel raw={travel_stats['raw']} "
            f"kept={travel_stats['kept']} "
            f"skipped_sku={travel_stats['skipped_existing_sku']} "
            f"skipped_id={travel_stats['skipped_existing_id']} "
            f"skipped_style_color={travel_stats['skipped_style_color']}",
            flush=True,
        )
    for leaf in RTW_LEAF_COLLECTIONS:
        n = sum(1 for p in products if leaf in (p.get("gcCollections") or []))
        print(f"  {leaf}: {n}", flush=True)
    for leaf in SHOES_LEAF_COLLECTIONS:
        n = sum(1 for p in products if leaf in (p.get("gcCollections") or []))
        print(f"  {leaf}: {n}", flush=True)
    for leaf in WALLETS_LEAF_COLLECTIONS:
        n = sum(1 for p in products if leaf in (p.get("gcCollections") or []))
        print(f"  {leaf}: {n}", flush=True)
    for leaf in TRAVEL_LEAF_COLLECTIONS:
        n = sum(1 for p in products if leaf in (p.get("gcCollections") or []))
        print(f"  {leaf}: {n}", flush=True)
    travel_parent_only = sum(
        1
        for p in products
        if "gc-women-travel" in (p.get("gcCollections") or [])
        and not any(
            c in TRAVEL_LEAF_COLLECTIONS for c in (p.get("gcCollections") or [])
        )
    )
    if travel_parent_only:
        print(f"  gc-women-travel (no leaf): {travel_parent_only}", flush=True)


if __name__ == "__main__":
    main()