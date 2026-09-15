#!/usr/bin/env python3
"""Saint Laurent (YSL) GB pipeline configuration."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "src/data/ys"
IMG_ROOT = ROOT / "public/products/ys-pdp"
BASE = "https://www.ysl.com"
LOCALE = "en-gb"
NEXT_BUILD = "v3"

YS_MEN = ["saint-laurent", "ys-men"]
YS_WOMEN = ["saint-laurent", "ys-women"]
YS_MEN_BAGS = ["saint-laurent-bags", "ys-men-bags"]
YS_WOMEN_BAGS = ["saint-laurent-bags", "ys-women-bags"]
YS_MEN_SHOES = ["saint-laurent-shoes", "ys-men-shoes"]
YS_WOMEN_SHOES = ["saint-laurent-shoes", "ys-women-shoes"]
YS_MEN_ACC = ["saint-laurent-accessories", "ys-men-accessories"]
YS_WOMEN_ACC = ["saint-laurent-accessories", "ys-women-accessories"]


def _leaf(leaf_id: str, label: str, label_ko: str, slug: str, parents: list[str]) -> dict:
    return {
        "id": leaf_id,
        "label": label,
        "labelKo": label_ko,
        "slug": slug,
        "url": f"{BASE}/{LOCALE}/ca/{slug}",
        "collections": [*parents, leaf_id],
    }


# --- Men RTW (luxury) ---
YS_MEN_RTW_LEAVES = [
    _leaf("ys-men-rtw-all", "View All", "전체", "shop-men/ready-to-wear/all-ready-to-wear", YS_MEN),
    _leaf("ys-men-shirts", "Shirts", "셔츠", "shop-men/ready-to-wear/shirts", YS_MEN),
    _leaf("ys-men-jersey", "Jersey", "저지", "shop-men/ready-to-wear/jersey", YS_MEN),
    _leaf("ys-men-knitwear", "Knitwear", "니트웨어", "shop-men/ready-to-wear/knitwear", YS_MEN),
    _leaf("ys-men-denim", "Denim", "데님", "shop-men/ready-to-wear/denim-men", YS_MEN),
    _leaf("ys-men-jackets-pants", "Jackets and Pants", "재킷 & 팬츠", "shop-men/ready-to-wear/jackets-and-pants", YS_MEN),
    _leaf("ys-men-outerwear", "Outerwear", "아우터웨어", "shop-men/ready-to-wear/outerwear", YS_MEN),
    _leaf("ys-men-coats-trench", "Coats and Trench", "코트 & 트렌치", "shop-men/ready-to-wear/coats-and-trench", YS_MEN),
    _leaf("ys-men-leather", "Leather", "레더", "shop-men/ready-to-wear/leather", YS_MEN),
]

# --- Men shoes ---
YS_MEN_SHOES_LEAVES = [
    _leaf("ys-men-shoes-all", "View All", "전체", "shop-men/shoes/all-shoes", YS_MEN_SHOES),
    _leaf("ys-men-sneakers", "Sneakers", "스니커즈", "shop-men/shoes/sneakers", YS_MEN_SHOES),
    _leaf("ys-men-loafers", "Loafers", "로퍼", "shop-men/shoes/loafers", YS_MEN_SHOES),
    _leaf("ys-men-derbies", "Derbies", "더비", "shop-men/shoes/derbies", YS_MEN_SHOES),
    _leaf("ys-men-boots", "Boots", "부츠", "shop-men/shoes/boots", YS_MEN_SHOES),
    _leaf("ys-men-sandals", "Sandals", "샌들", "shop-men/shoes/sandals", YS_MEN_SHOES),
]

# --- Men bags ---
YS_MEN_BAGS_LEAVES = [
    _leaf("ys-men-bags-all", "View All", "전체", "shop-men/bags/all-bags", YS_MEN_BAGS),
    _leaf("ys-men-backpacks", "Backpacks", "백팩", "shop-men/bags/backpacks", YS_MEN_BAGS),
    _leaf("ys-men-briefcases", "Briefcases", "브리프케이스", "shop-men/bags/briefcases", YS_MEN_BAGS),
    _leaf("ys-men-messengers", "Messengers", "메신저", "shop-men/bags/messengers", YS_MEN_BAGS),
    _leaf("ys-men-totes", "Totes", "토트", "shop-men/bags/totes", YS_MEN_BAGS),
    _leaf("ys-men-travel-bags", "Travel Bags", "트래블 백", "shop-men/bags/travel-bags", YS_MEN_BAGS),
]

# --- Men SLG (accessories hub) ---
YS_MEN_SLG_LEAVES = [
    _leaf("ys-men-slg-all", "View All", "전체", "shop-men/small-leather-goods/all-small-leather-goods", YS_MEN_ACC),
    _leaf("ys-men-card-cases", "Card Cases", "카드 케이스", "shop-men/small-leather-goods/card-cases", YS_MEN_ACC),
    _leaf("ys-men-wallets", "Wallets", "지갑", "shop-men/small-leather-goods/wallets", YS_MEN_ACC),
    _leaf("ys-men-pouches", "Pouches", "파우치", "shop-men/small-leather-goods/pouches", YS_MEN_ACC),
    _leaf("ys-men-cases-holders", "Cases and Holders", "케이스 & 홀더", "shop-men/small-leather-goods/cases-and-holders", YS_MEN_ACC),
    _leaf("ys-men-slg-other", "Other Accessories", "기타", "shop-men/small-leather-goods/other-accessories", YS_MEN_ACC),
]

# --- Men accessories ---
YS_MEN_ACC_LEAVES = [
    _leaf("ys-men-acc-all", "View All", "전체", "shop-men/accessories/all-accessories", YS_MEN_ACC),
    _leaf("ys-men-belts", "Belts", "벨트", "shop-men/accessories/belts", YS_MEN_ACC),
    _leaf("ys-men-hats-gloves", "Hats and Gloves", "모자 & 장갑", "shop-men/accessories/hats-and-gloves", YS_MEN_ACC),
    _leaf("ys-men-jewelry", "Jewelry", "주얼리", "shop-men/accessories/jewelry", YS_MEN_ACC),
    _leaf("ys-men-scarves-ties", "Scarves and Ties", "스카프 & 타이", "shop-men/accessories/scarves-and-ties", YS_MEN_ACC),
    _leaf("ys-men-sunglasses", "Sunglasses", "선글라스", "shop-men/accessories/sunglasses", YS_MEN_ACC),
]

# --- Women RTW ---
YS_WOMEN_RTW_LEAVES = [
    _leaf("ys-women-rtw-all", "View All", "전체", "shop-women/ready-to-wear/all-ready-to-wear", YS_WOMEN),
]

# --- Women shoes ---
YS_WOMEN_SHOES_LEAVES = [
    _leaf("ys-women-shoes-all", "View All", "전체", "shop-women/shoes/all-shoes", YS_WOMEN_SHOES),
    _leaf("ys-women-sneakers", "Sneakers", "스니커즈", "shop-women/shoes/sneakers", YS_WOMEN_SHOES),
    _leaf("ys-women-pumps", "Pumps and Slingbacks", "펌프스 & 슬링백", "shop-women/shoes/pumps-and-slingbacks", YS_WOMEN_SHOES),
    _leaf("ys-women-sandals", "Sandals", "샌들", "shop-women/shoes/sandals", YS_WOMEN_SHOES),
    _leaf("ys-women-flat-sandals", "Flat Sandals", "플랫 샌들", "shop-women/shoes/flat-sandals", YS_WOMEN_SHOES),
    _leaf("ys-women-flats-loafers", "Flats and Loafers", "플랫 & 로퍼", "shop-women/shoes/flats-and-loafers", YS_WOMEN_SHOES),
    _leaf("ys-women-ballerinas", "Ballerinas", "발레리나", "shop-women/shoes/ballerinas", YS_WOMEN_SHOES),
    _leaf("ys-women-mules-wedges", "Mules and Wedges", "뮬 & 웨지", "shop-women/shoes/mules-and-wedges", YS_WOMEN_SHOES),
    _leaf("ys-women-boots", "Boots", "부츠", "shop-women/shoes/boots", YS_WOMEN_SHOES),
    _leaf("ys-women-booties", "Booties", "부티", "shop-women/shoes/booties", YS_WOMEN_SHOES),
]

# --- Women bags ---
YS_WOMEN_BAGS_LEAVES = [
    _leaf("ys-women-bags-all", "View All", "전체", "shop-women/handbags/all-handbags", YS_WOMEN_BAGS),
]

# --- Women SLG ---
YS_WOMEN_SLG_LEAVES = [
    _leaf("ys-women-slg-all", "View All", "전체", "shop-women/small-leather-goods/all-small-leather-goods", YS_WOMEN_ACC),
]

# --- Women accessories ---
YS_WOMEN_ACC_LEAVES = [
    _leaf("ys-women-acc-all", "View All", "전체", "shop-women/accessories/all-accessories", YS_WOMEN_ACC),
    _leaf("ys-women-belts", "Belts", "벨트", "shop-women/accessories/belts", YS_WOMEN_ACC),
    _leaf("ys-women-gloves", "Gloves", "장갑", "shop-women/accessories/gloves", YS_WOMEN_ACC),
    _leaf("ys-women-hats", "Hats", "모자", "shop-women/accessories/hats", YS_WOMEN_ACC),
    _leaf("ys-women-scarves-silk", "Scarves and Silk", "스카프 & 실크", "shop-women/accessories/scarves-and-silk", YS_WOMEN_ACC),
    _leaf("ys-women-sunglasses", "Sunglasses", "선글라스", "shop-women/accessories/sunglasses", YS_WOMEN_ACC),
]

# --- Women jewelry ---
YS_WOMEN_JEWELRY_LEAVES = [
    _leaf("ys-women-jewelry-all", "View All", "전체", "shop-women/jewelry/all-jewelry", YS_WOMEN_ACC),
    _leaf("ys-women-earrings", "Earrings", "이어링", "shop-women/jewelry/earrings", YS_WOMEN_ACC),
    _leaf("ys-women-necklaces", "Necklaces", "네크리스", "shop-women/jewelry/necklaces", YS_WOMEN_ACC),
    _leaf("ys-women-cuffs-bracelets", "Cuffs and Bracelets", "커프 & 브레이슬릿", "shop-women/jewelry/cuffs-and-bracelets", YS_WOMEN_ACC),
    _leaf("ys-women-brooches-rings", "Brooches and Rings", "브로치 & 링", "shop-women/jewelry/brooches-and-rings", YS_WOMEN_ACC),
    _leaf("ys-women-lucky-charms", "Lucky Charms", "럭키 참", "shop-women/jewelry/lucky-charms", YS_WOMEN_ACC),
]


def _family(out: str, hub: str, category: str, leaves: list[dict]) -> dict:
    return {"out": out, "hub": hub, "category": category, "leaves": leaves}


YS_FAMILY_SCRAPERS: dict[str, dict] = {
    # Smallest first order for pipelines / weekly.
    "ys-men-bags": _family("ys-men-bags-catalog-raw.json", "men-bags", "bags", YS_MEN_BAGS_LEAVES),
    "ys-men-shoes": _family("ys-men-shoes-catalog-raw.json", "men-shoes", "shoes", YS_MEN_SHOES_LEAVES),
    "ys-men-accessories": _family("ys-men-accessories-catalog-raw.json", "men-acc", "accessories", YS_MEN_ACC_LEAVES),
    "ys-men-slg": _family("ys-men-slg-catalog-raw.json", "men-slg", "accessories", YS_MEN_SLG_LEAVES),
    "ys-women-jewelry": _family("ys-women-jewelry-catalog-raw.json", "women-jewelry", "accessories", YS_WOMEN_JEWELRY_LEAVES),
    "ys-women-accessories": _family("ys-women-accessories-catalog-raw.json", "women-acc", "accessories", YS_WOMEN_ACC_LEAVES),
    "ys-women-slg": _family("ys-women-slg-catalog-raw.json", "women-slg", "accessories", YS_WOMEN_SLG_LEAVES),
    "ys-women-shoes": _family("ys-women-shoes-catalog-raw.json", "women-shoes", "shoes", YS_WOMEN_SHOES_LEAVES),
    "ys-women-rtw": _family("ys-women-rtw-catalog-raw.json", "women-rtw", "luxury", YS_WOMEN_RTW_LEAVES),
    "ys-men-rtw": _family("ys-men-rtw-catalog-raw.json", "men-rtw", "luxury", YS_MEN_RTW_LEAVES),
    "ys-women-bags": _family("ys-women-bags-catalog-raw.json", "women-bags", "bags", YS_WOMEN_BAGS_LEAVES),
}

# Weekly / build order: small catalogs first.
YS_FAMILY_ORDER = list(YS_FAMILY_SCRAPERS.keys())


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
        # Union collections
        cols = list(
            dict.fromkeys(
                [*(prev.get("collections") or []), *(row.get("collections") or [])]
            )
        )
        merged["collections"] = cols
        by_id[rid] = merged
    return list(by_id.values())
