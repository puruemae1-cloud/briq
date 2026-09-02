#!/usr/bin/env python3
"""Incrementally merge Dior raw catalogs into di-catalog with KO Algolia + deep-translator.

Preserves existing good Korean rows. Use after each scrape stage.

  python3 scripts/merge-di-catalog-ko.py
  python3 scripts/check-catalog-korean.py --brand di --fail
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from di_common import (  # noqa: E402
    ALGOLIA_MERCH_API_KEY,
    ALGOLIA_MERCH_APP_ID,
    ALGOLIA_MERCH_INDEX_KO,
    dior_code_to_object_id,
    gbp_to_krw,
    slugify,
)
from di_size_charts import (  # noqa: E402
    size_chart_for_di_mens_rtw,
    size_chart_for_di_mens_shoes,
)
from ko_qa import en_ratio, is_good_korean  # noqa: E402

RAW_PATHS = [
    ROOT / "src/data/di/di-tableware-catalog-raw.json",
    ROOT / "src/data/di/di-objects-catalog-raw.json",
    ROOT / "src/data/di/di-decor-catalog-raw.json",
    ROOT / "src/data/di/di-textile-catalog-raw.json",
    ROOT / "src/data/di/di-jewelry-catalog-raw.json",
    ROOT / "src/data/di/di-timepieces-catalog-raw.json",
    ROOT / "src/data/di/di-icons-catalog-raw.json",
    ROOT / "src/data/di/di-bags-women-catalog-raw.json",
    ROOT / "src/data/di/di-bags-men-catalog-raw.json",
    ROOT / "src/data/di/di-men-rtw-catalog-raw.json",
    ROOT / "src/data/di/di-men-slg-catalog-raw.json",
    ROOT / "src/data/di/di-men-accessories-catalog-raw.json",
    ROOT / "src/data/di/di-men-shoes-catalog-raw.json",
]
CAT = ROOT / "src/data/di/di-catalog.json"
OUT_TS = ROOT / "src/data/di/di-catalog.ts"
ACCENTS = ["#1A1A1A", "#2C2420", "#243028", "#3A2F28", "#1E2830", "#2A2028"]

OBJECTISH = {
    "di-objects",
    "di-objects-all",
    "di-books",
    "di-notebooks",
    "di-desk-accessories",
    "di-candleholders-candles",
    "di-small-objects",
    "di-trinket-trays",
    "di-trays",
    "di-leisure",
    "di-paperweights",
}

DECORISH = {
    "di-decor",
    "di-decor-all",
    "di-decorative-pieces",
    "di-lighting",
    "di-baskets",
    "di-wallpapers",
    "di-vases",
    "di-furniture",
}

TEXTILEISH = {
    "di-textile",
    "di-textile-all",
    "di-cushions",
    "di-bath-linen",
    "di-table-linen",
    "di-throws",
}

JEWELRYISH = {
    "di-jewelry-timepieces",
    "di-jewelry-all",
    "di-earrings",
    "di-bracelets",
    "di-rings",
    "di-necklaces",
    "di-dior-icons",
}

TIMEPIECEISH = {
    "dior-watches",
    "di-timepieces-all",
    "di-la-d-de-dior",
    "di-straps",
}

BAGISH = {
    "dior-bags",
    "di-bags-womens",
    "di-bags-all",
    "di-handbags",
    "di-crossbody-shoulder-bags",
    "di-tote-bags",
    "di-bucket-bags",
    "di-clutches",
    "di-mini-bags",
    "di-accessorize-bag",
    "di-bags-mens",
    "di-men-bags-all",
    "di-men-crossbody-shoulder-bags",
    "di-men-backpacks",
    "di-men-small-bags",
    "di-men-tote-bags",
    "di-men-travel-bags",
    "di-men-briefcases",
    "di-men-accessorize-bag",
}

RTWISH = {
    "di-mens",
    "di-men-rtw-all",
    "di-men-tshirts-polos",
    "di-men-shirts",
    "di-men-knitwear-sweatshirts",
    "di-men-trousers-shorts",
    "di-men-denim",
    "di-men-beachwear",
    "di-men-outerwear",
    "di-men-tailored-jackets",
    "di-men-leather",
    "di-men-suits-tuxedos",
}

SLGISH = {
    "di-men-slg",
    "di-men-slg-all",
    "di-men-card-holders",
    "di-men-compact-wallets",
    "di-men-long-wallets",
    "di-men-pouches",
    "di-men-tech-accessories",
}

MEN_ACCISH = {
    "di-men-accessories",
    "di-men-acc-all",
    "di-men-sunglasses",
    "di-men-belts",
    "di-men-ties-pocket-squares",
    "di-men-scarves",
    "di-men-hats-gloves",
    "di-men-socks",
    "di-men-fashion-jewelry",
    "di-men-silver-jewelry",
    "di-men-key-rings",
    "di-men-charm-jewelry",
    "di-men-lifestyle",
    "di-men-acc-tech",
    "di-men-pet-accessories",
}

MEN_SHOESISH = {
    "dior-shoes",
    "di-men-shoes",
    "di-men-shoes-all",
    "di-men-sneakers",
    "di-men-sandals-mules",
    "di-men-loafers",
    "di-men-lace-ups",
    "di-men-boots",
}

# Prefer specific Maison / jewelry leaves over *-all when picking subcategory.
LEAF_PREF = [
    "di-plates-bowls",
    "di-glasses",
    "di-carafes",
    "di-cutlery",
    "di-tea-coffee",
    "di-books",
    "di-notebooks",
    "di-desk-accessories",
    "di-leisure",
    "di-candleholders-candles",
    "di-small-objects",
    "di-trinket-trays",
    "di-paperweights",
    "di-trays",
    "di-decorative-pieces",
    "di-vases",
    "di-lighting",
    "di-baskets",
    "di-wallpapers",
    "di-furniture",
    "di-cushions",
    "di-bath-linen",
    "di-table-linen",
    "di-throws",
    "di-earrings",
    "di-bracelets",
    "di-rings",
    "di-necklaces",
    "di-la-d-de-dior",
    "di-straps",
    "di-dior-icons",
    "di-handbags",
    "di-crossbody-shoulder-bags",
    "di-tote-bags",
    "di-bucket-bags",
    "di-clutches",
    "di-mini-bags",
    "di-accessorize-bag",
    "di-men-tech-accessories",
    "di-men-pouches",
    "di-men-long-wallets",
    "di-men-compact-wallets",
    "di-men-card-holders",
    "di-men-sunglasses",
    "di-men-belts",
    "di-men-ties-pocket-squares",
    "di-men-scarves",
    "di-men-hats-gloves",
    "di-men-socks",
    "di-men-fashion-jewelry",
    "di-men-silver-jewelry",
    "di-men-key-rings",
    "di-men-charm-jewelry",
    "di-men-lifestyle",
    "di-men-acc-tech",
    "di-men-pet-accessories",
    "di-men-sneakers",
    "di-men-sandals-mules",
    "di-men-loafers",
    "di-men-lace-ups",
    "di-men-boots",
    "di-men-crossbody-shoulder-bags",
    "di-men-backpacks",
    "di-men-small-bags",
    "di-men-tote-bags",
    "di-men-travel-bags",
    "di-men-briefcases",
    "di-men-accessorize-bag",
    "di-tableware-all",
    "di-objects-all",
    "di-decor-all",
    "di-textile-all",
    "di-jewelry-all",
    "di-timepieces-all",
    "di-bags-all",
    "di-men-bags-all",
    "di-men-slg-all",
    "di-men-acc-all",
    "di-men-shoes-all",
]
_LEAF_RANK = {lid: i for i, lid in enumerate(LEAF_PREF)}


def list_price_from_variants(variants: list[dict], fallback: int = 0) -> int:
    prices = [
        int(v["price"])
        for v in variants
        if isinstance(v.get("price"), (int, float)) and v.get("price") > 0
    ]
    return min(prices) if prices else fallback


def features_from_ko_hit(h: dict | None) -> list[str]:
    if not h:
        return []
    chars = h.get("characteristics") or ""
    if not isinstance(chars, str):
        return []
    return [ln.strip() for ln in chars.replace("\r", "").split("\n") if ln.strip()]


def story_sections_for_di(
    description_ko: str,
    images: list[str],
    *,
    rtw: bool = False,
    features_ko: list[str] | None = None,
    material_ko: str = "",
    madein_ko: str = "",
) -> list[dict]:
    if not images:
        return [{"titleKo": "제품 소개", "bodyKo": description_ko, "image": ""}]
    if rtw:
        detail_body = (
            " · ".join((features_ko or [])[:8])
            if features_ko
            else (
                "Dior 공식 제품 컷으로 확인하는 실루엣·소재·"
                "테일러링 디테일입니다."
            )
        )
        material_body = (
            f"주요 소재: {material_ko}. {madein_ko}."
            if material_ko and madein_ko
            else (f"주요 소재: {material_ko}." if material_ko else madein_ko)
        )
        look_idx = next(
            (i for i, img in enumerate(images) if "look_" in img.lower()),
            None,
        )
        sections: list[dict] = [
            {"titleKo": "제품 소개", "bodyKo": description_ko, "image": images[0]},
        ]
        if len(images) > 3:
            sections.append(
                {
                    "titleKo": "디테일 & 특징",
                    "bodyKo": detail_body,
                    "image": images[min(3, len(images) - 1)],
                }
            )
        if len(images) > 5:
            sections.append(
                {
                    "titleKo": "소재 & 제작",
                    "bodyKo": material_body or detail_body,
                    "image": images[min(5, len(images) - 1)],
                }
            )
        if look_idx is not None:
            sections.append(
                {
                    "titleKo": "디올 룩",
                    "bodyKo": (
                        "Dior 남성 컬렉션 룩과 함께 제안되는 "
                        "스타일링 레퍼런스입니다."
                    ),
                    "image": images[look_idx],
                }
            )
        elif len(images) > 7:
            sections.append(
                {
                    "titleKo": "착용 & 스타일",
                    "bodyKo": (
                        "포멀부터 데일리까지 다양한 룩에 어울리는 "
                        "디올 남성 레디투웨어 실루엣입니다."
                    ),
                    "image": images[min(7, len(images) - 1)],
                }
            )
        return sections
    sections = [
        {"titleKo": "제품 소개", "bodyKo": description_ko, "image": images[0]},
    ]
    if len(images) > 4:
        sections.append(
            {
                "titleKo": "디테일",
                "bodyKo": (
                    "Dior 공식 제품 컷으로 확인하는 실루엣·소재·"
                    "시그니처 장식 디테일입니다."
                ),
                "image": images[4],
            }
        )
    if len(images) > 8:
        sections.append(
            {
                "titleKo": "착용 & 스타일",
                "bodyKo": (
                    "데일리부터 트래블까지 다양한 룩에 어울리는 "
                    "디올 백 실루엣입니다."
                ),
                "image": images[min(8, len(images) - 1)],
            }
        )
    return sections


def prefer_leaf(collections: list[str], fallback: str) -> tuple[str, list[str]]:
    """Return (subcategory, reordered collections) preferring specific leaves."""
    cols = list(dict.fromkeys(collections or []))
    leaf_cols = [c for c in cols if c in _LEAF_RANK]
    if not leaf_cols:
        leaf = fallback if fallback in _LEAF_RANK else (fallback or "di-tableware-all")
        if leaf not in cols:
            cols.append(leaf)
        return leaf, cols
    best = min(leaf_cols, key=lambda c: _LEAF_RANK[c])
    parents = [c for c in cols if c not in _LEAF_RANK]
    ordered = parents + sorted(leaf_cols, key=lambda c: _LEAF_RANK[c])
    return best, list(dict.fromkeys(ordered))


def load_raw() -> dict[str, dict]:
    by: dict[str, dict] = {}
    for path in RAW_PATHS:
        if not path.is_file():
            continue
        raw = json.loads(path.read_text())
        for row in raw.get("products") or []:
            code = row.get("id")
            if not code or not row.get("images"):
                continue
            prev = by.get(code)
            if prev:
                cols = list(
                    dict.fromkeys(
                        (prev.get("collections") or []) + (row.get("collections") or [])
                    )
                )
                merged = {**prev, **row, "collections": cols}
                if len(prev.get("images") or []) > len(merged.get("images") or []):
                    merged["images"] = prev["images"]
                by[code] = merged
            else:
                by[code] = row
    return by


def fetch_ko_one(code: str) -> dict | None:
    oid = dior_code_to_object_id(code)
    params = urllib.parse.urlencode(
        {
            "query": code.replace("_", ""),
            "hitsPerPage": 8,
            "attributesToRetrieve": "*",
        }
    )
    body = json.dumps(
        {"requests": [{"indexName": ALGOLIA_MERCH_INDEX_KO, "params": params}]}
    ).encode()
    req = urllib.request.Request(
        f"https://{ALGOLIA_MERCH_APP_ID}-dsn.algolia.net/1/indexes/*/queries",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Algolia-Application-Id": ALGOLIA_MERCH_APP_ID,
            "X-Algolia-API-Key": ALGOLIA_MERCH_API_KEY,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        hits = json.loads(r.read())["results"][0].get("hits") or []
    for h in hits:
        if h.get("objectID") == oid:
            return h
    return None


def translate(text: str) -> str:
    s = re.sub(r"\s+", " ", (text or "").strip())
    if not s:
        return ""
    if is_good_korean(s):
        return s
    try:
        from deep_translator import GoogleTranslator

        tr = GoogleTranslator(source="en", target="ko")
    except Exception:
        from ko_qa import gtx_translate

        for attempt in range(4):
            try:
                ko = gtx_translate(s)
                if is_good_korean(ko):
                    return ko
            except Exception:
                time.sleep(3 * (attempt + 1))
        return ""
    for attempt in range(4):
        try:
            ko = tr.translate(s[:4500])
            if is_good_korean(ko):
                return ko
        except Exception as e:
            print(f"  tr err: {e}", flush=True)
            time.sleep(4 * (attempt + 1))
    return ""


def tags_for(collections: list[str], leaf: str) -> list[str]:
    tags = ["dior", "디올"]
    cols = collections + [leaf]
    if any(c in TIMEPIECEISH for c in cols):
        tags += ["watches", "timepieces", "시계", "타임피스"]
    elif any(c in BAGISH for c in cols):
        tags += ["bags", "handbags", "가방", "핸드백"]
    elif any(c in RTWISH for c in cols):
        tags += ["luxury", "rtw", "ready-to-wear", "의류", "남성"]
    elif any(c in SLGISH for c in cols):
        tags += ["slg", "small leather goods", "악세서리", "남성", "wallet", "card holder"]
    elif any(c in MEN_ACCISH for c in cols):
        tags += ["accessories", "악세서리", "남성"]
    elif any(c in MEN_SHOESISH for c in cols):
        tags += ["shoes", "슈즈", "남성", "sneakers", "footwear"]
    elif any(c in JEWELRYISH for c in cols):
        tags += ["jewelry", "jewellery", "쥬얼리"]
    else:
        tags += ["maison"]
    if any(
        "tableware" in c
        or c.startswith("di-plates")
        or c.startswith("di-glass")
        or c.startswith("di-carafe")
        or c.startswith("di-tea")
        or c.startswith("di-cutlery")
        for c in cols
    ):
        tags += ["tableware", "테이블웨어"]
    if any(c in OBJECTISH for c in cols):
        tags += ["objects", "오브젝트"]
    if any(c in DECORISH for c in cols):
        tags += ["decor", "데코"]
    if any(c in TEXTILEISH for c in cols):
        tags += ["textile", "텍스타일", "텍스타일즈"]
    return list(dict.fromkeys(tags))


def _category_for(collections: list[str], leaf: str, fallback: str = "accessories") -> str:
    cols = collections + [leaf]
    if any(c in TIMEPIECEISH for c in cols):
        return "watches"
    if any(c in BAGISH for c in cols):
        return "bags"
    if any(c in MEN_SHOESISH for c in cols):
        return "shoes"
    if any(c in RTWISH for c in cols):
        return "luxury"
    return fallback


def refresh_existing(existing: dict, row: dict) -> dict:
    images = [img for img in (row.get("images") or []) if img]
    image = images[0]
    raw_leaf = row.get("leafId") or existing.get("subcategory") or "di-tableware-all"
    collections = list(dict.fromkeys(row.get("collections") or existing.get("diCollections") or []))
    if raw_leaf not in collections:
        collections.append(raw_leaf)
    leaf, collections = prefer_leaf(collections, raw_leaf)
    gbp = row.get("gbpPrice")
    try:
        gbp_f = float(gbp) if gbp is not None else float(existing.get("gbpPrice") or 0)
    except (TypeError, ValueError):
        gbp_f = 0.0
    price = gbp_to_krw(gbp_f) if gbp_f else 0
    p = dict(existing)
    p["images"] = images
    p["image"] = image
    p["gbpPrice"] = gbp_f
    p["diCollections"] = collections
    p["subcategory"] = leaf
    p["category"] = _category_for(collections, leaf, p.get("category") or "accessories")
    p["tags"] = tags_for(collections, leaf)
    p["sourceUrl"] = row.get("url") or p.get("sourceUrl") or ""
    if p.get("variants"):
        v = dict(p["variants"][0])
        v["images"] = images
        v["image"] = image
        v["gbpPrice"] = gbp_f
        v["price"] = price
        v["diCollections"] = collections
        v["sourceUrl"] = p["sourceUrl"]
        p["variants"] = [v]
    p["price"] = list_price_from_variants(p.get("variants") or [], price)
    if any(c in RTWISH for c in collections + [leaf]):
        chart = size_chart_for_di_mens_rtw(
            p.get("variants") or [],
            leaf_id=leaf,
            title_en=p.get("name") or "",
        )
        if chart:
            p["sizeChart"] = chart
    elif any(c in MEN_SHOESISH for c in collections + [leaf]):
        p["sizeChart"] = size_chart_for_di_mens_shoes()
    return p


def build_new(row: dict, idx: int, h: dict | None) -> dict:
    h = h or {}
    images = [img for img in (row.get("images") or []) if img]
    image = images[0]
    sku = row["id"]
    pid = f"di-{slugify(sku)}"
    gbp = row.get("gbpPrice")
    try:
        gbp_f = float(gbp) if gbp is not None else 0.0
    except (TypeError, ValueError):
        gbp_f = 0.0
    price = gbp_to_krw(gbp_f) if gbp_f else 0
    raw_leaf = row.get("leafId") or "di-tableware-all"
    collections = list(dict.fromkeys(row.get("collections") or []))
    if raw_leaf not in collections:
        collections.append(raw_leaf)
    leaf, collections = prefer_leaf(collections, raw_leaf)
    color = row.get("color") or {}
    title_en = (row.get("title") or sku).strip()

    title_ko = (h.get("title") or h.get("name") or "").strip()
    sub_ko = (h.get("subtitle") or "").strip()
    desc_ko = re.sub(r"\s+", " ", (h.get("description") or "").strip())

    if not title_ko or not is_good_korean(title_ko):
        title_ko = translate(title_en) or title_en
        time.sleep(0.7)
    if not desc_ko or en_ratio(desc_ko) > 0.45:
        en = ((row.get("details") or {}).get("paragraphs") or [""])[0]
        desc_ko = translate(en) or en
        time.sleep(0.7)
    if (row.get("subtitle") or "") and (not sub_ko or not is_good_korean(sub_ko)):
        sub_ko = translate(row.get("subtitle") or "")
        time.sleep(0.5)

    parts: list[str] = []
    if sub_ko and is_good_korean(sub_ko):
        parts.append(sub_ko)
    if desc_ko:
        parts.append(desc_ko)
    description_ko = "\n\n".join(parts)

    color_ko = None
    if isinstance(h.get("color"), dict):
        color_ko = h["color"].get("label")
    color_ko = color_ko or color.get("label") or "기본"
    color_key = color.get("code") or "default"
    source_url = row.get("url") or ""

    variants: list[dict] = []
    raw_vars = h.get("variants") if isinstance(h.get("variants"), list) else []
    for vv in raw_vars:
        if not isinstance(vv, dict):
            continue
        sz = str(vv.get("sizeFormatted") or vv.get("size") or "").strip()
        if not sz or sz.upper() in ("OS", "ONE SIZE", "TU", "U", "ONESIZE"):
            continue
        v_gbp = gbp_f
        vp = vv.get("price") or {}
        if isinstance(vp, dict) and vp.get("amount") is not None:
            try:
                v_gbp = float(vp["amount"])
            except (TypeError, ValueError):
                pass
        variants.append(
            {
                "id": f"{pid}-sz-{slugify(sz, max_len=24)}",
                "name": sz,
                "nameKo": sz,
                "sku": str(vv.get("sku") or row.get("sku") or sku),
                "gbpPrice": v_gbp,
                "price": gbp_to_krw(v_gbp) if v_gbp else price,
                "image": image,
                "images": images,
                "sourceUrl": source_url,
                "inStock": True,
                "colorKey": color_key,
                "colorNameKo": color_ko,
                "size": sz,
                "diCollections": collections,
            }
        )
    if variants:
        def _sz_key(v: dict):
            try:
                return (0, float(v["size"]))
            except (TypeError, ValueError):
                return (1, str(v.get("size") or ""))

        variants = sorted(variants, key=_sz_key)
    else:
        variants = [
            {
                "id": f"{pid}-os",
                "name": "One Size",
                "nameKo": "원 사이즈",
                "sku": str(row.get("sku") or sku),
                "gbpPrice": gbp_f,
                "price": price,
                "image": image,
                "images": images,
                "sourceUrl": source_url,
                "inStock": True,
                "colorKey": color_key,
                "colorNameKo": color_ko,
                "size": "OS",
                "diCollections": collections,
            }
        ]
    product = {
        "id": pid,
        "name": title_en,
        "nameKo": title_ko,
        "brand": "Dior",
        "category": _category_for(collections, leaf, "accessories"),
        "subcategory": leaf,
        "diCollections": collections,
        "tags": tags_for(collections, leaf),
        "descriptionKo": description_ko,
        "image": image,
        "images": images,
        "accent": ACCENTS[idx % len(ACCENTS)],
        "gbpPrice": gbp_f,
        "price": list_price_from_variants(variants, price),
        "sku": sku,
        "sourceUrl": source_url,
        "variants": variants,
        "storySections": story_sections_for_di(
            description_ko or title_ko,
            images,
            rtw=any(c in RTWISH or c in MEN_SHOESISH for c in collections + [leaf]),
        ),
    }
    feats = features_from_ko_hit(h)
    if feats:
        product["featuresKo"] = feats
    if any(c in RTWISH for c in collections + [leaf]):
        chart = size_chart_for_di_mens_rtw(
            variants,
            leaf_id=leaf,
            title_en=title_en,
        )
        if chart:
            product["sizeChart"] = chart
    elif any(c in MEN_SHOESISH for c in collections + [leaf]):
        product["sizeChart"] = size_chart_for_di_mens_shoes()
    return product


def main() -> None:
    by_raw = load_raw()
    prev = json.loads(CAT.read_text()) if CAT.is_file() else []
    prev_by = {p["sku"]: p for p in prev if p.get("sku")}
    print(f"raw={len(by_raw)} prev={len(prev_by)}", flush=True)

    need = [
        c
        for c in by_raw
        if not (
            prev_by.get(c)
            and is_good_korean(prev_by[c].get("descriptionKo") or "")
            and is_good_korean(prev_by[c].get("nameKo") or "")
        )
    ]
    print(f"need enrich {len(need)}", flush=True)

    ko: dict[str, dict] = {}
    for i, code in enumerate(need, 1):
        h = fetch_ko_one(code)
        if h:
            ko[code] = h
        if i % 15 == 0:
            print(f"  ko {i}/{len(need)} hits={len(ko)}", flush=True)
            time.sleep(1.5)
        else:
            time.sleep(0.25)
    print(f"ko hits {len(ko)}", flush=True)

    out: list[dict] = []
    for i, (code, row) in enumerate(by_raw.items()):
        existing = prev_by.get(code)
        if (
            existing
            and is_good_korean(existing.get("descriptionKo") or "")
            and is_good_korean(existing.get("nameKo") or "")
        ):
            out.append(refresh_existing(existing, row))
        else:
            out.append(build_new(row, i, ko.get(code)))
        if (i + 1) % 40 == 0:
            print(f"built {i+1}/{len(by_raw)}", flush=True)

    # Final pass for remaining EN
    bad = [
        p
        for p in out
        if not is_good_korean(p.get("descriptionKo") or "")
        or not is_good_korean(p.get("nameKo") or "")
    ]
    print(f"translate remaining {len(bad)}", flush=True)
    for i, p in enumerate(bad, 1):
        row = by_raw[p["sku"]]
        if not is_good_korean(p.get("nameKo") or ""):
            p["nameKo"] = translate(row.get("title") or p.get("name") or "") or p["nameKo"]
            time.sleep(0.8)
        en = ((row.get("details") or {}).get("paragraphs") or [""])[0]
        sub = row.get("subtitle") or ""
        parts: list[str] = []
        if sub:
            sk = translate(sub)
            time.sleep(0.6)
            if is_good_korean(sk):
                parts.append(sk)
        dk = translate(en)
        time.sleep(0.9)
        if is_good_korean(dk):
            parts.append(dk)
        if parts:
            p["descriptionKo"] = "\n\n".join(parts)
            if p.get("storySections"):
                p["storySections"][0]["bodyKo"] = p["descriptionKo"]
        print(
            f"[{i}/{len(bad)}] {p['sku']} ok={is_good_korean(p.get('descriptionKo') or '')}",
            flush=True,
        )
        if i % 8 == 0:
            CAT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
            print("--- pause 25s ---", flush=True)
            time.sleep(25)

    CAT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    # Keep di-catalog.ts tiny (JSON import) — embedding 1000+ SKUs inline OOMs Cursor/Vercel.
    OUT_TS.write_text(
        "/* Auto-generated — do not edit */\n"
        'import type { Product } from "@/data/product-types";\n'
        'import data from "./di-catalog.json";\n'
        "\n"
        "/** Dior Maison + Jewelry + Bags catalog (JSON import keeps TS small). */\n"
        "export const diCatalogProducts = data as unknown as Product[];\n"
    )
    good = sum(
        1
        for p in out
        if is_good_korean(p.get("descriptionKo") or "")
        and is_good_korean(p.get("nameKo") or "")
    )
    print(f"DONE {len(out)} good={good}", flush=True)


if __name__ == "__main__":
    main()
