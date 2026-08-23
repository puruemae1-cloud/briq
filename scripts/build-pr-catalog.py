#!/usr/bin/env python3
"""Build Briq Prada women's handbags catalog from scrape raw.

Pricing matches Chanel/Gucci luxury bags:
  KRW = round_만원(GBP × 2100 × 1.05 × 1.15)
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
SCRIPTS = ROOT / "scripts"
import sys

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from pr_size_charts import size_chart_for_shoes, size_chart_for_variants  # noqa: E402
from pr_shoe_ko import seed_shoe_cache, shoe_text_ko  # noqa: E402
from pr_slg_ko import seed_slg_cache, slg_text_ko  # noqa: E402
RAW_BAGS = ROOT / "src/data/pr/pr-handbags-catalog-raw.json"
RAW_RTW = ROOT / "src/data/pr/pr-womens-rtw-catalog-raw.json"
RAW_SHOES = ROOT / "src/data/pr/pr-womens-shoes-catalog-raw.json"
RAW_SLG = ROOT / "src/data/pr/pr-womens-slg-catalog-raw.json"
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

SLG_LEAF_COLLECTIONS = [
    "pr-women-card-holders",
    "pr-women-small-wallets",
    "pr-women-large-wallets",
    "pr-women-wallets-on-chain",
    "pr-women-high-tech-accessories",
]
SLG_PARENT_COLS = ["prada", "prada-accessories", "pr-women-slg"]

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
    letters = [c for c in s if c.isalpha()]
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
        if s in _KO and en_ratio(_KO[s]) < 0.40:
            continue
        if s in _GLOSSARY or en_ratio(s) < 0.35:
            continue
        uniq.append(s)
    print(f"pretranslate {len(uniq)} unique strings…", flush=True)
    for i, s in enumerate(uniq, start=1):
        try:
            ko = gtx(s).strip()
            if ko and en_ratio(ko) < 0.70:
                _KO[s] = apply_glossary(ko)
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


def t(text: str | None) -> str:
    s = re.sub(r"\s+", " ", (text or "").strip())
    if not s:
        return ""
    # Prefer SLG curated maps before shoe heuristics (shoe_text_ko treats any
    # short string containing "logo"/"lining" as a shoe detail).
    curated = slg_text_ko(s)
    if curated is not None:
        _KO[s] = curated
        return curated
    curated = shoe_text_ko(s)
    if curated is not None:
        _KO[s] = curated
        return curated
    # Always reuse in-run / good cache hits (force only clears weak entries first).
    if s in _KO and en_ratio(_KO[s]) < 0.40:
        return apply_glossary(_KO[s])
    # short glossary hit (exact title phrase)
    if s in _GLOSSARY:
        return _GLOSSARY[s]
    if en_ratio(s) < 0.35 or len(s) < 3:
        return apply_glossary(s)
    if not _OFFLINE_TRANSLATE:
        for attempt in range(2):
            try:
                ko = gtx(s).strip()
                if ko and en_ratio(ko) < 0.55:
                    ko = apply_glossary(ko)
                    _KO[s] = ko
                    time.sleep(0.05)
                    return ko
                time.sleep(0.1 * (attempt + 1))
            except Exception:
                time.sleep(0.1 * (attempt + 1))
    # Offline fallback for remaining English (esp. long descriptions)
    from pr_shoe_ko import apply_phrases as shoe_phrases
    from pr_slg_ko import apply_phrases as slg_phrases

    ko = apply_glossary(slg_phrases(shoe_phrases(s)))
    _KO[s] = ko
    return ko


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

    cols = [
        c
        for c in (row.get("collections") or [])
        if c in HANDBAG_LEAF_COLLECTIONS or c in BAG_PARENT_COLS
    ]
    cols = sorted(set([*cols, *BAG_PARENT_COLS]))
    if any(c in HANDBAG_LEAF_COLLECTIONS for c in cols) and "pr-handbags" not in cols:
        cols.append("pr-handbags")
        cols = sorted(set(cols))

    leaf = row.get("leaf") or next(
        (c for c in HANDBAG_LEAF_COLLECTIONS if c in cols), "pr-handbags"
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
                "bodyKo": f"{name_ko}의 디테일.",
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

    tags = ["prada", "프라다", "handbag", "핸드백", "여성", *cols]

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
                "bodyKo": f"{name_ko}의 디테일.",
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

    cols = [
        c
        for c in (row.get("collections") or [])
        if c in SHOES_LEAF_COLLECTIONS or c in SHOES_PARENT_COLS
    ]
    cols = sorted(set([*cols, *SHOES_PARENT_COLS]))
    leaf = row.get("leaf") or next(
        (c for c in SHOES_LEAF_COLLECTIONS if c in cols), "pr-women-shoes"
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
                "bodyKo": f"{name_ko}의 디테일.",
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

    tags = ["prada", "프라다", "shoes", "슈즈", "여성", *cols]
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
    chart = size_chart_for_shoes(variants)
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

        cols: list[str] = []
        for r in usable:
            cols.extend(
                c
                for c in (r.get("collections") or [])
                if c in SLG_LEAF_COLLECTIONS or c in SLG_PARENT_COLS
            )
        cols = sorted(set([*cols, *SLG_PARENT_COLS]))
        leaf = primary.get("leaf") or next(
            (c for c in SLG_LEAF_COLLECTIONS if c in cols), "pr-women-slg"
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
                    "bodyKo": f"{name_ko}의 디테일.",
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

        tags = ["prada", "프라다", "accessories", "악세서리", "slg", "여성", *cols]
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


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--only",
        choices=["shoes", "rtw", "bags", "slg", "all"],
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

    global _FORCE_TRANSLATE, _OFFLINE_TRANSLATE, _KO
    if args.force_translate:
        _FORCE_TRANSLATE = True
        print("force-translate: refreshing shoe Korean copy", flush=True)
    if args.offline or args.force_translate:
        # Shoes force-refresh uses curated offline maps (API often 429s).
        _OFFLINE_TRANSLATE = True
        print("offline translate mode", flush=True)

    only = args.only
    rows: list[dict] = []
    if only in {"all", "bags"} and RAW_BAGS.exists():
        bags = json.loads(RAW_BAGS.read_text()).get("products") or []
        for r in bags:
            r = dict(r)
            r["_kind"] = "handbag"
            rows.append(r)
    if only in {"all", "rtw"} and RAW_RTW.exists():
        rtw = json.loads(RAW_RTW.read_text()).get("products") or []
        for r in rtw:
            r = dict(r)
            r["_kind"] = "rtw"
            rows.append(r)
    if only in {"all", "shoes"} and RAW_SHOES.exists():
        shoes = json.loads(RAW_SHOES.read_text()).get("products") or []
        for r in shoes:
            r = dict(r)
            r["_kind"] = "shoes"
            rows.append(r)
    slg_rows: list[dict] = []
    if only in {"all", "slg"} and RAW_SLG.exists():
        slg_rows = [
            dict(r) for r in (json.loads(RAW_SLG.read_text()).get("products") or [])
        ]
        for r in slg_rows:
            r["_kind"] = "slg"
    if not rows and not slg_rows:
        raise SystemExit(
            "Missing Prada raw catalogues — run scrape-pr-handbags.py, "
            "scrape-pr-womens-rtw.py, scrape-pr-womens-shoes.py, "
            "and/or scrape-pr-womens-slg.py first"
        )

    if only in {"all", "slg"}:
        n_seed = seed_slg_cache(_KO)
        print(f"seeded {n_seed} curated SLG strings", flush=True)
    prev_by_sku: dict[str, dict] = {}
    existing: list[dict] = []
    if OUT_JSON.exists():
        existing = json.loads(OUT_JSON.read_text())
        for p in existing:
            if p.get("sku"):
                prev_by_sku[str(p["sku"])] = p

    # When force-translating shoes, drop cache for every English source string
    # used by the shoe raw catalogue so titles/descriptions re-run through gtx.
    if args.force_translate and only == "shoes":
        # Keep good description translations; drop weak ones and re-seed curated.
        dropped = 0
        for k in list(_KO.keys()):
            if en_ratio(str(_KO[k])) >= 0.40:
                _KO.pop(k, None)
                dropped += 1
        print(f"cleared {dropped} weak cache entries for shoe retranslate", flush=True)
        n_seed = seed_shoe_cache(_KO)
        print(f"seeded {n_seed} curated shoe strings", flush=True)
    if args.force_translate and only == "slg":
        dropped = 0
        for k in list(_KO.keys()):
            if en_ratio(str(_KO[k])) >= 0.35:
                _KO.pop(k, None)
                dropped += 1
        print(f"cleared {dropped} weak cache entries for SLG retranslate", flush=True)
        n_seed = seed_slg_cache(_KO)
        print(f"re-seeded {n_seed} curated SLG strings", flush=True)

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
        elif kind in {"womens-shoes", "shoes"}:
            prod = build_shoes_product(row, prev_by_sku.get(sku), now_iso)
        elif kind in {"womens-slg", "slg"}:
            continue  # built via build_slg_products below
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

    if only != "all" and existing:
        if only == "slg":
            merged = [
                p
                for p in existing
                if not (
                    p.get("brand") == "프라다"
                    and p.get("category") == "accessories"
                )
            ]
            products = merged + products
        else:
            keep_cat = {
                "shoes": "shoes",
                "rtw": "luxury",
                "bags": "bags",
            }[only]
            # RTW shares category luxury with nothing else from Prada currently
            merged = [p for p in existing if p.get("category") != keep_cat]
            if only == "rtw":
                # Prada RTW is category luxury; bags are bags; shoes are shoes.
                # Keep bags+shoes+acc, replace luxury Prada RTW only.
                merged = [
                    p
                    for p in existing
                    if not (
                        p.get("brand") == "프라다"
                        and p.get("category") == "luxury"
                    )
                ]
            products = merged + products

    products.sort(key=lambda p: p["id"])
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n")
    OUT_TS.write_text(
        'import type { Product } from "@/data/products";\n'
        'import data from "./pr-catalog.json";\n\n'
        "/** Auto-generated — Prada women's handbags + RTW + shoes + SLG (GB). */\n"
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
    for leaf in RTW_LEAF_COLLECTIONS:
        n = sum(1 for p in products if leaf in (p.get("prCollections") or []))
        if n:
            print(f"  {leaf}: {n}", flush=True)
    for leaf in SHOES_LEAF_COLLECTIONS:
        n = sum(1 for p in products if leaf in (p.get("prCollections") or []))
        if n:
            print(f"  {leaf}: {n}", flush=True)
    for leaf in SLG_LEAF_COLLECTIONS:
        n = sum(1 for p in products if leaf in (p.get("prCollections") or []))
        if n:
            print(f"  {leaf}: {n}", flush=True)


if __name__ == "__main__":
    main()
