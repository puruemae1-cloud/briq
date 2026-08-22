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
RAW_BAGS = ROOT / "src/data/pr/pr-handbags-catalog-raw.json"
RAW_RTW = ROOT / "src/data/pr/pr-womens-rtw-catalog-raw.json"
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
    q = urllib.parse.quote(text[:4500])
    url = (
        "https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl=en&tl=ko&dt=t&q={q}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=35) as r:
        data = json.loads(r.read().decode())
    return "".join(part[0] for part in data[0] if part and part[0])


def apply_glossary(s: str) -> str:
    out = s
    # longer phrases first
    for en, ko in sorted(_GLOSSARY.items(), key=lambda kv: -len(kv[0])):
        out = re.sub(re.escape(en), ko, out, flags=re.I)
    # Prada brand keep as 프라다 when standalone product naming
    out = re.sub(r"\bPrada\b", "프라다", out)
    out = re.sub(r"\s{2,}", " ", out).strip()
    return out


def t(text: str | None) -> str:
    s = re.sub(r"\s+", " ", (text or "").strip())
    if not s:
        return ""
    if s in _KO and en_ratio(_KO[s]) < 0.55:
        return apply_glossary(_KO[s])
    # short glossary hit
    if s in _GLOSSARY:
        return _GLOSSARY[s]
    if en_ratio(s) < 0.35 or len(s) < 3:
        return apply_glossary(s)
    try:
        ko = gtx(s).strip()
        if ko:
            ko = apply_glossary(ko)
            _KO[s] = ko
            return ko
    except Exception:
        pass
    return apply_glossary(s)


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
    return {
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


def main() -> None:
    rows: list[dict] = []
    if RAW_BAGS.exists():
        bags = json.loads(RAW_BAGS.read_text()).get("products") or []
        for r in bags:
            r = dict(r)
            r["_kind"] = "handbag"
            rows.append(r)
    if RAW_RTW.exists():
        rtw = json.loads(RAW_RTW.read_text()).get("products") or []
        for r in rtw:
            r = dict(r)
            r["_kind"] = "rtw"
            rows.append(r)
    if not rows:
        raise SystemExit(
            "Missing Prada raw catalogues — run scrape-pr-handbags.py "
            "and/or scrape-pr-womens-rtw.py first"
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
    seen: set[str] = set()
    for i, row in enumerate(rows, start=1):
        sku = str(row.get("productCode") or row.get("id") or "")
        kind = row.get("_kind") or row.get("kind") or "handbag"
        if kind in {"womens-rtw", "rtw"}:
            prod = build_rtw_product(row, prev_by_sku.get(sku), now_iso)
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

    products.sort(key=lambda p: p["id"])
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n")
    OUT_TS.write_text(
        'import type { Product } from "@/data/products";\n'
        'import data from "./pr-catalog.json";\n\n'
        "/** Auto-generated — Prada women's handbags + ready-to-wear (GB). */\n"
        "export const prCatalogProducts = data as unknown as Product[];\n"
    )
    CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2))
    print(f"Wrote {len(products)} products → {OUT_JSON}", flush=True)
    bags_n = sum(1 for p in products if p.get("category") == "bags")
    lux_n = sum(1 for p in products if p.get("category") == "luxury")
    print(f"  bags={bags_n} luxury/rtw={lux_n}", flush=True)
    for leaf in RTW_LEAF_COLLECTIONS:
        n = sum(1 for p in products if leaf in (p.get("prCollections") or []))
        if n:
            print(f"  {leaf}: {n}", flush=True)


if __name__ == "__main__":
    main()
