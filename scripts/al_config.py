#!/usr/bin/env python3
"""AllSaints (UK SFCC) pipeline configuration."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "src/data/al"
IMG_ROOT = ROOT / "public/products/al-pdp"

BASE = "https://www.allsaints.com"
SFCC = f"{BASE}/on/demandware.store/Sites-allsaints-uk-Site/en_GB"
LOCALE = "en_GB"

AL_MEN = ["all-saints", "al-men"]
AL_WOMEN = ["all-saints", "al-women"]
AL_MEN_SHOES = ["all-saints-shoes", "al-men-shoes"]
AL_WOMEN_SHOES = ["all-saints-shoes", "al-women-shoes"]
AL_MEN_ACC = ["all-saints-accessories", "al-men-accessories"]
AL_WOMEN_ACC = ["all-saints-accessories", "al-women-accessories"]


def _leaf(
    leaf_id: str,
    label: str,
    label_ko: str,
    path: str,
    cgid: str,
    parents: list[str],
) -> dict:
    return {
        "id": leaf_id,
        "label": label,
        "labelKo": label_ko,
        "path": path,
        "cgid": cgid,
        "url": f"{BASE}{path}",
        "collections": [*parents, leaf_id],
    }


# --- Men accessories (smallest first) ---
AL_MEN_ACC_LEAVES = [
    _leaf("al-men-acc-all", "View All", "전체", "/men/accessories", "695", AL_MEN_ACC),
    _leaf("al-men-sunglasses", "Sunglasses", "선글라스", "/men/accessories/sunglasses", "22021", AL_MEN_ACC),
    _leaf("al-men-belts", "Belts", "벨트", "/men/accessories/belts", "21841", AL_MEN_ACC),
    _leaf("al-men-wallets", "Wallets", "지갑", "/men/accessories/wallets", "21840", AL_MEN_ACC),
    _leaf("al-men-hats", "Hats", "모자", "/men/accessories/hats", "320", AL_MEN_ACC),
    _leaf("al-men-jewellery", "Jewellery", "주얼리", "/men/jewellery", "21935", AL_MEN_ACC),
    _leaf("al-men-bags", "Bags", "가방", "/men/bags", "316", AL_MEN_ACC),
]

# --- Men shoes ---
AL_MEN_SHOES_LEAVES = [
    _leaf("al-men-shoes-all", "View All", "전체", "/men/boots-and-shoes", "817", AL_MEN_SHOES),
    _leaf("al-men-boots", "Boots", "부츠", "/men/boots-and-shoes/boots/leather", "21998", AL_MEN_SHOES),
    _leaf("al-men-casual-shoes", "Shoes", "슈즈", "/men/boots-and-shoes/shoes", "21770", AL_MEN_SHOES),
    _leaf("al-men-trainers", "Trainers", "스니커즈", "/men/boots-and-shoes/trainers", "21771", AL_MEN_SHOES),
]

# --- Women accessories ---
AL_WOMEN_ACC_LEAVES = [
    _leaf("al-women-acc-all", "View All", "전체", "/women/accessories", "21533", AL_WOMEN_ACC),
    _leaf("al-women-sunglasses", "Sunglasses", "선글라스", "/women/accessories/sunglasses", "22022", AL_WOMEN_ACC),
    _leaf("al-women-belts", "Belts", "벨트", "/women/accessories/belts", "21837", AL_WOMEN_ACC),
    _leaf("al-women-scarves", "Scarves", "스카프", "/women/accessories/scarves", "21838", AL_WOMEN_ACC),
    _leaf("al-women-hats", "Hats", "모자", "/women/accessories/hats", "21932", AL_WOMEN_ACC),
    _leaf("al-women-jewellery", "Jewellery", "주얼리", "/women/jewellery", "21848", AL_WOMEN_ACC),
    _leaf("al-women-handbags", "Handbags", "핸드백", "/women/handbags", "8606", AL_WOMEN_ACC),
]

# --- Women shoes ---
AL_WOMEN_SHOES_LEAVES = [
    _leaf("al-women-shoes-all", "View All", "전체", "/women/boots-and-shoes", "21765", AL_WOMEN_SHOES),
    _leaf("al-women-boots", "Boots", "부츠", "/women/boots-and-shoes/boots", "21769", AL_WOMEN_SHOES),
    _leaf("al-women-flats", "Flats", "플랫", "/women/boots-and-shoes/flats", "21766", AL_WOMEN_SHOES),
    _leaf("al-women-heels", "Heels", "힐", "/women/boots-and-shoes/heels", "21768", AL_WOMEN_SHOES),
    _leaf("al-women-trainers", "Trainers", "스니커즈", "/women/boots-and-shoes/trainers", "21767", AL_WOMEN_SHOES),
]

# --- Men RTW ---
AL_MEN_RTW_LEAVES = [
    _leaf("al-men-rtw-all", "View All", "전체", "/men/clothing", "men-clothing", AL_MEN),
    _leaf("al-men-coats-jackets", "Coats and Jackets", "코트 & 재킷", "/men/coats-and-jackets", "814", AL_MEN),
    _leaf("al-men-jeans", "Jeans", "진", "/men/jeans", "7", AL_MEN),
    _leaf("al-men-knitwear", "Knitwear", "니트웨어", "/men/knitwear", "10", AL_MEN),
    _leaf("al-men-leathers", "Leathers", "레더", "/men/leathers", "9", AL_MEN),
    _leaf("al-men-leather-jackets", "Leather Jackets", "레더 재킷", "/men/leathers/leather-jackets", "21974", AL_MEN),
    _leaf("al-men-shirts", "Shirts", "셔츠", "/men/shirts", "11", AL_MEN),
    _leaf("al-men-sweatshirts-hoodies", "Sweatshirts and Hoodies", "스웨트셔츠 & 후디", "/men/sweatshirts-and-hoodies", "12", AL_MEN),
    _leaf("al-men-tshirts", "T-Shirts", "티셔츠", "/men/t-shirts", "13", AL_MEN),
    _leaf("al-men-trousers", "Trousers", "트라우저", "/men/trousers", "312", AL_MEN),
    _leaf("al-men-sweatpants", "Sweatpants", "스웨트팬츠", "/men/trousers/sweatpants", "21686", AL_MEN),
]

# --- Women RTW ---
AL_WOMEN_RTW_LEAVES = [
    _leaf("al-women-rtw-all", "View All", "전체", "/women/clothing", "women-clothing", AL_WOMEN),
    _leaf("al-women-coats-jackets", "Coats and Jackets", "코트 & 재킷", "/women/coats-and-jackets", "840", AL_WOMEN),
    _leaf("al-women-dresses", "Dresses", "드레스", "/women/dresses", "22", AL_WOMEN),
    _leaf("al-women-jeans", "Jeans", "진", "/women/jeans", "23", AL_WOMEN),
    _leaf("al-women-knitwear", "Knitwear", "니트웨어", "/women/knitwear", "26", AL_WOMEN),
    _leaf("al-women-leather", "Leather", "레더", "/women/leather", "25", AL_WOMEN),
    _leaf("al-women-leather-jackets", "Leather Jackets", "레더 재킷", "/women/leather/leather-jackets", "21965", AL_WOMEN),
    _leaf("al-women-shirts", "Shirts", "셔츠", "/women/shirts", "233", AL_WOMEN),
    _leaf("al-women-skirts-shorts", "Skirts and Shorts", "스커트 & 쇼츠", "/women/skirts-and-shorts", "822", AL_WOMEN),
    _leaf("al-women-sweatshirts-hoodies", "Sweatshirts and Hoodies", "스웨트셔츠 & 후디", "/women/sweatshirts-and-hoodies", "475", AL_WOMEN),
    _leaf("al-women-tshirts", "T-Shirts", "티셔츠", "/women/t-shirts", "824", AL_WOMEN),
    _leaf("al-women-tops-shirts", "Tops and Shirts", "탑 & 셔츠", "/women/tops-and-shirts", "21726", AL_WOMEN),
    _leaf("al-women-trousers-leggings", "Trousers and Leggings", "트라우저 & 레깅스", "/women/trousers-and-leggings", "823", AL_WOMEN),
]


def _family(out: str, hub: str, category: str, leaves: list[dict]) -> dict:
    return {"out": out, "hub": hub, "category": category, "leaves": leaves}


# Smallest first for scrape / weekly.
AL_FAMILY_SCRAPERS: dict[str, dict] = {
    "al-men-accessories": _family("al-men-accessories-catalog-raw.json", "men-acc", "accessories", AL_MEN_ACC_LEAVES),
    "al-men-shoes": _family("al-men-shoes-catalog-raw.json", "men-shoes", "shoes", AL_MEN_SHOES_LEAVES),
    "al-women-accessories": _family("al-women-accessories-catalog-raw.json", "women-acc", "accessories", AL_WOMEN_ACC_LEAVES),
    "al-women-shoes": _family("al-women-shoes-catalog-raw.json", "women-shoes", "shoes", AL_WOMEN_SHOES_LEAVES),
    "al-men-rtw": _family("al-men-rtw-catalog-raw.json", "men-rtw", "luxury", AL_MEN_RTW_LEAVES),
    "al-women-rtw": _family("al-women-rtw-catalog-raw.json", "women-rtw", "luxury", AL_WOMEN_RTW_LEAVES),
}

AL_FAMILY_ORDER = list(AL_FAMILY_SCRAPERS.keys())


def merge_product_rows(existing: list[dict], new_rows: list[dict]) -> list[dict]:
    by_id: dict[str, dict] = {}
    for row in existing:
        rid = str(row.get("id") or row.get("sku") or "")
        if rid:
            by_id[rid] = row
    for row in new_rows:
        rid = str(row.get("id") or row.get("sku") or "")
        if not rid:
            continue
        prev = by_id.get(rid)
        if not prev:
            by_id[rid] = row
            continue
        merged = dict(prev)
        merged.update({k: v for k, v in row.items() if v not in (None, "", [], {})})
        cols = list(
            dict.fromkeys(
                [*(prev.get("collections") or []), *(row.get("collections") or [])]
            )
        )
        merged["collections"] = cols
        # Prefer richer PDP fields from new scrape when present.
        for key in ("sizes", "images", "imageUrls", "localImages", "description", "bullets", "sizeAndFit"):
            if row.get(key):
                merged[key] = row[key]
        by_id[rid] = merged
    return list(by_id.values())
