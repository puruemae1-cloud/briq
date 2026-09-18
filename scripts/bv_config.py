#!/usr/bin/env python3
"""Bottega Veneta (UK SFCC) pipeline configuration.

Leaf cgids were resolved from official PLP HTML (`data-querystring` / searchajax).
Shared path slugs (sunglasses, bracelets, …) map to gender-prefixed SFCC ids
(e.g. men-sunglasses / women-sunglasses) — never use the bare slug alone.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "src/data/bv"
IMG_ROOT = ROOT / "public/products/bv-pdp"
PDP_CACHE = RAW_DIR / "bv-pdp-cache.json"
TRANSLATE_CACHE = RAW_DIR / "bv-translate-cache.json"
OUT_JSON = RAW_DIR / "bv-catalog.json"
OUT_TS = RAW_DIR / "bv-catalog.ts"

BASE = "https://www.bottegaveneta.com"
SFCC = f"{BASE}/on/demandware.store/Sites-BV-R-WEUR-Site/en_GB"
LOCALE_PATH = "/en-gb"

BV_ROOT = ["bottega-veneta"]
BV_MEN = ["bottega-veneta", "bv-men"]
BV_WOMEN = ["bottega-veneta", "bv-women"]
BV_BAGS = ["bottega-veneta", "bottega-veneta-bags"]
BV_SHOES = ["bottega-veneta", "bottega-veneta-shoes"]
BV_ACC = ["bottega-veneta", "bottega-veneta-accessories"]


def _leaf(
    leaf_id: str,
    label_en: str,
    label_ko: str,
    path: str,
    cgid: str,
    parents: list[str],
) -> dict:
    return {
        "id": leaf_id,
        "labelEn": label_en,
        "labelKo": label_ko,
        "path": path,
        "cgid": cgid,
        "url": f"{BASE}{path}",
        "collections": [*parents, leaf_id],
    }


def _hub(
    hub_id: str,
    *,
    cgid: str,
    path: str,
    label_en: str,
    label_ko: str,
    category: str,
    parents: list[str],
    leaves: list[dict],
    membership_only: bool = False,
) -> dict:
    return {
        "id": hub_id,
        "cgid": cgid,
        "path": path,
        "labelEn": label_en,
        "labelKo": label_ko,
        "category": category,
        "parents": parents,
        "leaves": leaves,
        "membershipOnly": membership_only,
        "out": f"bv-{hub_id}-catalog-raw.json",
    }


# --- Men bags ---
_MB = ["bottega-veneta", "bottega-veneta-bags", "bv-men", "bv-men-bags"]
MEN_BAGS_LEAVES = [
    _leaf("bv-men-bags-intrecciato", "Intrecciato", "인트레치아토", "/en-gb/men-collection-gb/men-bags/intrecciato", "men-intrecciato", _MB),
    _leaf("bv-men-bags-diago", "Diago", "디아고", "/en-gb/men-collection-gb/men-bags/diago", "men-diago", _MB),
    _leaf("bv-men-bags-veneto", "Veneto", "베네토", "/en-gb/men-collection-gb/men-bags/veneto", "men-veneto", _MB),
    _leaf("bv-men-bags-andiamo", "Andiamo", "안디아모", "/en-gb/men-collection-gb/men-bags/men-andiamo", "men-andiamo", _MB),
    _leaf("bv-men-bags-cabat", "Cabat", "카밧", "/en-gb/men-collection-gb/men-bags/men-cabat", "men-cabat", _MB),
    _leaf("bv-men-bags-getaway", "Getaway", "겟어웨이", "/en-gb/men-collection-gb/men-bags/men-getaway", "men-getaway", _MB),
    _leaf("bv-men-bags-crossbody", "Crossbody Bags", "크로스바디", "/en-gb/men-collection-gb/men-bags/men-crossbody-bags", "men-crossbody-bags", _MB),
    _leaf("bv-men-bags-tote", "Tote Bags", "토트백", "/en-gb/men-collection-gb/men-bags/men-tote-bags", "men-tote-bags", _MB),
    _leaf("bv-men-bags-backpack", "Backpack", "백팩", "/en-gb/men-collection-gb/men-bags/backpack", "men-backpacks", _MB),
    _leaf("bv-men-bags-belt", "Belt Bags", "벨트백", "/en-gb/men-collection-gb/men-bags/belt", "men-belt-bags", _MB),
    _leaf("bv-men-bags-briefcase", "Briefcase", "브리프케이스", "/en-gb/men-collection-gb/men-bags/briefcase", "men-briefcases", _MB),
    _leaf("bv-men-bags-document-case", "Document Case", "서류 케이스", "/en-gb/men-collection-gb/men-bags/document-case", "men-document-cases", _MB),
]

# --- Men shoes ---
_MS = ["bottega-veneta", "bottega-veneta-shoes", "bv-men", "bv-men-shoes"]
MEN_SHOES_LEAVES = [
    _leaf("bv-men-shoes-shot", "Shot", "샷", "/en-gb/men-collection-gb/men-shoes/men-shot", "men-shot", _MS),
    _leaf("bv-men-shoes-orbit-flash", "Orbit Flash", "오빗 플래시", "/en-gb/men-collection-gb/men-shoes/men-orbit-flash", "men-orbit-flash", _MS),
    _leaf("bv-men-shoes-orbit", "Orbit", "오빗", "/en-gb/men-collection-gb/men-shoes/men-orbit", "men-orbit", _MS),
    _leaf("bv-men-shoes-silenzio", "Silenzio", "실렌치오", "/en-gb/men-collection-gb/men-shoes/men-silenzio", "men-silenzio", _MS),
    _leaf("bv-men-shoes-astaire", "Astaire", "아스테어", "/en-gb/men-collection-gb/men-shoes/men-astaire", "men-astaire", _MS),
    _leaf("bv-men-shoes-palazzo", "Palazzo", "팔라초", "/en-gb/men-collection-gb/men-shoes/men-palazzo", "men-palazzo", _MS),
    _leaf("bv-men-shoes-haddock", "Haddock", "해독", "/en-gb/men-collection-gb/men-shoes/haddock", "men-haddock", _MS),
    _leaf("bv-men-shoes-sneakers", "Sneakers", "스니커즈", "/en-gb/men-collection-gb/men-shoes/men-sneakers", "men-sneakers", _MS),
    _leaf("bv-men-shoes-loafers", "Loafers", "로퍼", "/en-gb/men-collection-gb/men-shoes/loafers", "men-loafers", _MS),
    _leaf("bv-men-shoes-lace-ups", "Lace-Ups", "레이스업", "/en-gb/men-collection-gb/men-shoes/lace-ups", "men-lace-ups", _MS),
    _leaf("bv-men-shoes-boots", "Boots", "부츠", "/en-gb/men-collection-gb/men-shoes/boots", "men-boots", _MS),
    _leaf("bv-men-shoes-slippers", "Slippers", "슬리퍼", "/en-gb/men-collection-gb/men-shoes/slippers", "men-slippers", _MS),
    _leaf("bv-men-shoes-sandals", "Sandals", "샌들", "/en-gb/men-collection-gb/men-shoes/men-sandals", "men-sandals", _MS),
]

# --- Men clothing ---
_MC = ["bottega-veneta", "bv-men", "bv-men-clothing"]
MEN_CLOTHING_LEAVES = [
    _leaf("bv-men-clothing-coats", "Coats", "코트", "/en-gb/men-collection-gb/men-clothing/coats", "men-outerwear", _MC),
    _leaf("bv-men-clothing-jackets", "Jackets", "재킷", "/en-gb/men-collection-gb/men-clothing/jackets", "men-jackets", _MC),
    _leaf("bv-men-clothing-knitwear", "Knitwear", "니트웨어", "/en-gb/men-collection-gb/men-clothing/knitwear", "men-knitwear", _MC),
    _leaf("bv-men-clothing-leather", "Leather", "레더", "/en-gb/men-collection-gb/men-clothing/leather", "men-leather", _MC),
    _leaf("bv-men-clothing-trousers", "Trousers and Shorts", "트라우저 & 쇼츠", "/en-gb/men-collection-gb/men-clothing/trousers-and-shorts", "men-trousers", _MC),
    _leaf("bv-men-clothing-denim", "Denim", "데님", "/en-gb/men-collection-gb/men-clothing/denim", "men-denim", _MC),
    _leaf("bv-men-clothing-shirts", "Shirts", "셔츠", "/en-gb/men-collection-gb/men-clothing/shirts", "men-shirts", _MC),
    _leaf("bv-men-clothing-tshirts", "T-Shirts", "티셔츠", "/en-gb/men-collection-gb/men-clothing/t-shirts", "men-tshirts", _MC),
    _leaf("bv-men-clothing-polos", "Polos", "폴로", "/en-gb/men-collection-gb/men-clothing/polos", "men-polos", _MC),
    _leaf("bv-men-clothing-swimwear", "Swimwear", "스윔웨어", "/en-gb/men-collection-gb/men-clothing/swimwear", "men-swimwear", _MC),
]

# --- Men wallets ---
_MW = ["bottega-veneta", "bottega-veneta-accessories", "bv-men", "bv-men-wallets"]
MEN_WALLETS_LEAVES = [
    _leaf("bv-men-wallets-small", "Small Wallets", "스몰 월렛", "/en-gb/men-collection-gb/men-wallets/small-wallets", "men-small-wallets", _MW),
    _leaf("bv-men-wallets-long", "Long Wallets", "롱 월렛", "/en-gb/men-collection-gb/men-wallets/long-wallets", "men-long-wallets", _MW),
    _leaf("bv-men-wallets-card-cases", "Card Cases", "카드 케이스", "/en-gb/men-collection-gb/men-wallets/card-cases", "men-card-cases", _MW),
    _leaf("bv-men-wallets-pouches", "Pouches", "파우치", "/en-gb/men-collection-gb/men-wallets/pouches", "men-pouches", _MW),
    _leaf("bv-men-wallets-intrecciato", "Intrecciato", "인트레치아토", "/en-gb/men-collection-gb/men-wallets/men-wallets-intrecciato", "men-wallets-intrecciato", _MW),
    _leaf("bv-men-wallets-piccolo", "Intrecciato Piccolo", "인트레치아토 피콜로", "/en-gb/men-collection-gb/men-wallets/men-intrecciato-piccolo", "men-intrecciato-piccolo", _MW),
    _leaf("bv-men-wallets-cassette", "Cassette", "카세트", "/en-gb/men-collection-gb/men-wallets/men-wallets-cassette", "men-wallets-cassette", _MW),
]

# --- Men travel (hub only) ---
_MT = ["bottega-veneta", "bottega-veneta-accessories", "bv-men"]
MEN_TRAVEL_LEAVES = [
    _leaf("bv-men-travel", "Travel", "트래블", "/en-gb/men-collection-gb/men-travel", "men-travel", _MT),
]

# --- Men accessories ---
_MA = ["bottega-veneta", "bottega-veneta-accessories", "bv-men", "bv-men-accessories"]
MEN_ACC_LEAVES = [
    _leaf("bv-men-acc-key-rings", "Key Rings", "키링", "/en-gb/men-collection-gb/men-accessories/men-key-rings", "men-keyrings", _MA),
    _leaf("bv-men-acc-belts", "Belts", "벨트", "/en-gb/men-collection-gb/men-accessories/men-belts", "men-belts", _MA),
    _leaf("bv-men-acc-tech", "Tech", "테크", "/en-gb/men-collection-gb/men-accessories/men-tech", "men-tech", _MA),
    _leaf("bv-men-acc-scarves-ties", "Scarves and Ties", "스카프 & 타이", "/en-gb/men-collection-gb/men-accessories/scarves-and-ties", "men-scarves", _MA),
    _leaf("bv-men-acc-gloves", "Gloves", "장갑", "/en-gb/men-collection-gb/men-accessories/men-gloves", "men-gloves", _MA),
    _leaf("bv-men-acc-hats", "Hats", "모자", "/en-gb/men-collection-gb/men-accessories/men-hats", "men-hats", _MA),
    _leaf("bv-men-acc-bathrobes", "Bathrobes and Towels", "배스로브 & 타월", "/en-gb/men-collection-gb/men-accessories/bathrobes-and-towels", "men-bathrobe", _MA),
]

# --- Men eyewear (gender-prefixed cgids — bare "sunglasses" collides) ---
_ME = ["bottega-veneta", "bottega-veneta-accessories", "bv-men", "bv-men-eyewear"]
MEN_EYEWEAR_LEAVES = [
    _leaf("bv-men-eyewear-sunglasses", "Sunglasses", "선글라스", "/en-gb/men-collection-gb/men-eyewear/sunglasses", "men-sunglasses", _ME),
    _leaf("bv-men-eyewear-opticals", "Opticals", "옵티컬", "/en-gb/men-collection-gb/men-eyewear/opticals", "men-opticals", _ME),
    _leaf("bv-men-eyewear-aviator", "Aviator", "에비에이터", "/en-gb/men-collection-gb/men-eyewear/aviator", "men-sunglasses-aviator", _ME),
    _leaf("bv-men-eyewear-panthos", "Panthos", "판토스", "/en-gb/men-collection-gb/men-eyewear/panthos", "men-sunglasses-panthos", _ME),
    _leaf("bv-men-eyewear-rectangular", "Rectangular", "레탱귤러", "/en-gb/men-collection-gb/men-eyewear/rectangular", "men-sunglasses-rectangular", _ME),
    _leaf("bv-men-eyewear-squared", "Squared", "스퀘어드", "/en-gb/men-collection-gb/men-eyewear/squared", "men-sunglasses-squared", _ME),
]

# --- Men jewellery ---
_MJ = ["bottega-veneta", "bottega-veneta-accessories", "bv-men", "bv-men-jewellery"]
MEN_JEWELLERY_LEAVES = [
    _leaf("bv-men-jewellery-earrings", "Earrings", "이어링", "/en-gb/men-collection-gb/men-jewellery/men-earrings", "men-earrings", _MJ),
    _leaf("bv-men-jewellery-rings", "Rings", "링", "/en-gb/men-collection-gb/men-jewellery/men-rings", "men-rings", _MJ),
    _leaf("bv-men-jewellery-bracelets", "Bracelets", "브레이슬릿", "/en-gb/men-collection-gb/men-jewellery/bracelets", "men-bracelets", _MJ),
    _leaf("bv-men-jewellery-necklaces", "Necklaces", "네크리스", "/en-gb/men-collection-gb/men-jewellery/necklaces", "men-necklaces", _MJ),
    # Path /cufflinks redirects to a PDP; SFCC id is men-cufflinks (1 SKU).
    _leaf("bv-men-jewellery-cufflinks", "Cufflinks", "커프링크스", "/en-gb/men-collection-gb/men-jewellery/cufflinks", "men-cufflinks", _MJ),
]

# --- Women bags ---
_WB = ["bottega-veneta", "bottega-veneta-bags", "bv-women", "bv-women-bags"]
WOMEN_BAGS_LEAVES = [
    _leaf("bv-women-bags-mini", "Mini Bags", "미니 백", "/en-gb/women-collection-gb/women-bags/mini", "women-mini-bags", _WB),
    _leaf("bv-women-bags-crossbody", "Crossbody Bags", "크로스바디", "/en-gb/women-collection-gb/women-bags/women-crossbody-bags", "women-crossbody-bags", _WB),
    _leaf("bv-women-bags-shoulder", "Shoulder Bags", "숄더백", "/en-gb/women-collection-gb/women-bags/shoulder", "women-shoulder-bags", _WB),
    _leaf("bv-women-bags-top-handle", "Top Handle", "탑 핸들", "/en-gb/women-collection-gb/women-bags/handle", "women-top-handle-bags", _WB),
    _leaf("bv-women-bags-tote", "Tote / Shopper", "토트백", "/en-gb/women-collection-gb/women-bags/women-shopper", "women-tote-bags", _WB),
    _leaf("bv-women-bags-clutch", "Clutches", "클러치", "/en-gb/women-collection-gb/women-bags/clutch", "women-clutches", _WB),
    _leaf("bv-women-bags-jodie", "Jodie", "조디", "/en-gb/women-collection-gb/women-bags/jodie", "women-jodie", _WB),
    _leaf("bv-women-bags-andiamo", "Andiamo", "안디아모", "/en-gb/women-collection-gb/women-bags/women-andiamo", "women-andiamo", _WB),
    _leaf("bv-women-bags-barbara", "Barbara", "바바라", "/en-gb/women-collection-gb/women-bags/women-barbara", "women-barbara", _WB),
    _leaf("bv-women-bags-campana", "Campana", "캄파나", "/en-gb/women-collection-gb/women-bags/women-campana", "women-campana", _WB),
    _leaf("bv-women-bags-pinacoteca", "Pinacoteca", "피나코테카", "/en-gb/women-collection-gb/women-bags/pinacoteca", "women-pinacoteca", _WB),
    _leaf("bv-women-bags-sardine", "Sardine", "사르딘", "/en-gb/women-collection-gb/women-bags/sardine", "women-sardine", _WB),
    _leaf("bv-women-bags-cabat", "Cabat", "카밧", "/en-gb/women-collection-gb/women-bags/cabat", "women-cabat", _WB),
    _leaf("bv-women-bags-bang-bang", "Bang Bang", "뱅뱅", "/en-gb/women-collection-gb/women-bags/bang-bang", "women-bang-bang", _WB),
    _leaf("bv-women-bags-lauren", "Lauren", "로렌", "/en-gb/women-collection-gb/women-bags/lauren", "women-lauren", _WB),
    _leaf("bv-women-bags-parachute", "Parachute", "패러슈트", "/en-gb/women-collection-gb/women-bags/parachute", "women-parachute", _WB),
    _leaf("bv-women-bags-knot-clutch", "Knot Clutch", "노트 클러치", "/en-gb/women-collection-gb/women-bags/knot-clutch", "women-knot-clutch", _WB),
    _leaf("bv-women-bags-madison", "Madison", "매디슨", "/en-gb/women-collection-gb/women-bags/women-madison", "women-madison", _WB),
]

# --- Women shoes ---
_WS = ["bottega-veneta", "bottega-veneta-shoes", "bv-women", "bv-women-shoes"]
WOMEN_SHOES_LEAVES = [
    _leaf("bv-women-shoes-sneakers", "Sneakers", "스니커즈", "/en-gb/women-collection-gb/women-shoes/women-sneakers", "women-sneakers", _WS),
    _leaf("bv-women-shoes-boots", "Boots", "부츠", "/en-gb/women-collection-gb/women-shoes/boots", "women-boots", _WS),
    _leaf("bv-women-shoes-pumps", "Pumps", "펌프스", "/en-gb/women-collection-gb/women-shoes/pumps", "women-pumps", _WS),
    _leaf("bv-women-shoes-sandals", "Sandals", "샌들", "/en-gb/women-collection-gb/women-shoes/women-sandals", "women-sandals", _WS),
    _leaf("bv-women-shoes-loafers-laceups", "Loafers and Lace-Ups", "로퍼 & 레이스업", "/en-gb/women-collection-gb/women-shoes/loafers-and-lace-ups", "loafers-and-lace-ups", _WS),
    _leaf("bv-women-shoes-ballerinas", "Ballerinas and Slippers", "발레리나 & 슬리퍼", "/en-gb/women-collection-gb/women-shoes/ballerinas-and-slippers", "ballerinas-and-slippers", _WS),
    _leaf("bv-women-shoes-shot", "Shot", "샷", "/en-gb/women-collection-gb/women-shoes/women-shot", "women-shot", _WS),
    _leaf("bv-women-shoes-orbit", "Orbit", "오빗", "/en-gb/women-collection-gb/women-shoes/women-orbit", "women-orbit", _WS),
    _leaf("bv-women-shoes-orbit-flash", "Orbit Flash", "오빗 플래시", "/en-gb/women-collection-gb/women-shoes/women-orbit-flash", "women-orbit-flash", _WS),
    _leaf("bv-women-shoes-silenzio", "Silenzio", "실렌치오", "/en-gb/women-collection-gb/women-shoes/women-silenzio", "women-silenzio", _WS),
    _leaf("bv-women-shoes-astaire", "Astaire", "아스테어", "/en-gb/women-collection-gb/women-shoes/women-astaire", "women-astaire", _WS),
]

# --- Women clothing ---
_WC = ["bottega-veneta", "bv-women", "bv-women-clothing"]
WOMEN_CLOTHING_LEAVES = [
    _leaf("bv-women-clothing-outerwear", "Outerwear", "아우터", "/en-gb/women-collection-gb/women-clothing/women-outerwear", "women-outerwear", _WC),
    _leaf("bv-women-clothing-jackets", "Jackets", "재킷", "/en-gb/women-collection-gb/women-clothing/jackets", "women-jackets", _WC),
    _leaf("bv-women-clothing-knitwear", "Knitwear", "니트웨어", "/en-gb/women-collection-gb/women-clothing/knitwear", "women-knitwear", _WC),
    _leaf("bv-women-clothing-leather", "Leather", "레더", "/en-gb/women-collection-gb/women-clothing/leather", "women-leather", _WC),
    _leaf("bv-women-clothing-dresses", "Dresses", "드레스", "/en-gb/women-collection-gb/women-clothing/dresses", "women-dresses", _WC),
    _leaf("bv-women-clothing-skirts", "Skirts", "스커트", "/en-gb/women-collection-gb/women-clothing/skirts", "women-skirts", _WC),
    _leaf("bv-women-clothing-trousers", "Trousers and Shorts", "트라우저 & 쇼츠", "/en-gb/women-collection-gb/women-clothing/trousers-and-shorts", "women-trousers", _WC),
    _leaf("bv-women-clothing-denim", "Denim", "데님", "/en-gb/women-collection-gb/women-clothing/denim", "women-denim", _WC),
    _leaf("bv-women-clothing-shirts", "Shirts", "셔츠", "/en-gb/women-collection-gb/women-clothing/shirts", "women-shirts", _WC),
    _leaf("bv-women-clothing-tops", "Tops and T-Shirts", "탑 & 티셔츠", "/en-gb/women-collection-gb/women-clothing/tops-and-t-shirts", "women-tops", _WC),
    _leaf("bv-women-clothing-swimwear", "Swimwear", "스윔웨어", "/en-gb/women-collection-gb/women-clothing/swimwear", "women-swimwear", _WC),
]

# --- Women wallets ---
_WW = ["bottega-veneta", "bottega-veneta-accessories", "bv-women", "bv-women-wallets"]
WOMEN_WALLETS_LEAVES = [
    _leaf("bv-women-wallets-small", "Small Wallets", "스몰 월렛", "/en-gb/women-collection-gb/women-wallets/small-wallets", "women-small-wallets", _WW),
    _leaf("bv-women-wallets-long", "Long Wallets", "롱 월렛", "/en-gb/women-collection-gb/women-wallets/long-wallets", "women-long-wallets", _WW),
    _leaf("bv-women-wallets-card-cases", "Card Cases", "카드 케이스", "/en-gb/women-collection-gb/women-wallets/card-cases", "women-card-cases", _WW),
    _leaf("bv-women-wallets-pouches", "Pouches", "파우치", "/en-gb/women-collection-gb/women-wallets/pouches", "women-pouches", _WW),
    _leaf("bv-women-wallets-intrecciato", "Intrecciato", "인트레치아토", "/en-gb/women-collection-gb/women-wallets/women-wallets-intrecciato", "women-wallets-intrecciato", _WW),
    _leaf("bv-women-wallets-cassette", "Cassette", "카세트", "/en-gb/women-collection-gb/women-wallets/women-wallets-cassette", "women-wallets-cassette", _WW),
]

# --- Women travel ---
_WT = ["bottega-veneta", "bottega-veneta-accessories", "bv-women"]
WOMEN_TRAVEL_LEAVES = [
    _leaf("bv-women-travel", "Travel", "트래블", "/en-gb/women-collection-gb/women-travel", "women-travel", _WT),
]

# --- Women accessories ---
_WA = ["bottega-veneta", "bottega-veneta-accessories", "bv-women", "bv-women-accessories"]
WOMEN_ACC_LEAVES = [
    _leaf("bv-women-acc-key-rings", "Key Rings", "키링", "/en-gb/women-collection-gb/women-accessories/women-key-rings", "women-key-rings", _WA),
    _leaf("bv-women-acc-belts", "Belts", "벨트", "/en-gb/women-collection-gb/women-accessories/women-belts", "women-belts", _WA),
    _leaf("bv-women-acc-tech", "Tech", "테크", "/en-gb/women-collection-gb/women-accessories/women-tech", "women-tech", _WA),
    _leaf("bv-women-acc-scarves", "Scarves", "스카프", "/en-gb/women-collection-gb/women-accessories/scarves", "women-scarves", _WA),
    _leaf("bv-women-acc-gloves", "Gloves", "장갑", "/en-gb/women-collection-gb/women-accessories/women-gloves", "women-gloves", _WA),
    _leaf("bv-women-acc-hats", "Hats", "모자", "/en-gb/women-collection-gb/women-accessories/women-hats", "women-hats", _WA),
    _leaf("bv-women-acc-bathrobes", "Bathrobes and Towels", "배스로브 & 타월", "/en-gb/women-collection-gb/women-accessories/bathrobes-and-towels", "women-bathrobe", _WA),
]

# --- Women eyewear ---
_WE = ["bottega-veneta", "bottega-veneta-accessories", "bv-women", "bv-women-eyewear"]
WOMEN_EYEWEAR_LEAVES = [
    _leaf("bv-women-eyewear-sunglasses", "Sunglasses", "선글라스", "/en-gb/women-collection-gb/women-eyewear/sunglasses", "women-sunglasses", _WE),
    _leaf("bv-women-eyewear-opticals", "Opticals", "옵티컬", "/en-gb/women-collection-gb/women-eyewear/opticals", "women-opticals", _WE),
    _leaf("bv-women-eyewear-aviator", "Aviator", "에비에이터", "/en-gb/women-collection-gb/women-eyewear/aviator", "women-sunglasses-aviator", _WE),
    _leaf("bv-women-eyewear-panthos", "Panthos", "판토스", "/en-gb/women-collection-gb/women-eyewear/panthos", "women-sunglasses-panthos", _WE),
    _leaf("bv-women-eyewear-rectangular", "Rectangular", "레탱귤러", "/en-gb/women-collection-gb/women-eyewear/rectangular", "women-sunglasses-rectangular", _WE),
    _leaf("bv-women-eyewear-squared", "Squared", "스퀘어드", "/en-gb/women-collection-gb/women-eyewear/squared", "women-sunglasses-squared", _WE),
    _leaf("bv-women-eyewear-cat-eye", "Cat Eye", "캣아이", "/en-gb/women-collection-gb/women-eyewear/cat-eye", "women-sunglasses-cat-eye", _WE),
    _leaf("bv-women-eyewear-oval", "Oval", "오발", "/en-gb/women-collection-gb/women-eyewear/oval", "women-sunglasses-oval", _WE),
]

# --- Women jewellery ---
_WJ = ["bottega-veneta", "bottega-veneta-accessories", "bv-women", "bv-women-jewellery"]
WOMEN_JEWELLERY_LEAVES = [
    _leaf("bv-women-jewellery-earrings", "Earrings", "이어링", "/en-gb/women-collection-gb/women-jewellery/women-earrings", "women-earrings", _WJ),
    _leaf("bv-women-jewellery-rings", "Rings", "링", "/en-gb/women-collection-gb/women-jewellery/women-rings", "women-rings", _WJ),
    _leaf("bv-women-jewellery-bracelets", "Bracelets", "브레이슬릿", "/en-gb/women-collection-gb/women-jewellery/bracelets", "women-bracelets", _WJ),
    _leaf("bv-women-jewellery-necklaces", "Necklaces", "네크리스", "/en-gb/women-collection-gb/women-jewellery/necklaces", "women-necklaces", _WJ),
    _leaf("bv-women-jewellery-brooch", "Brooch", "브로치", "/en-gb/women-collection-gb/women-jewellery/women-brooch", "women-brooch", _WJ),
]

# --- Home ---
_HM = ["bottega-veneta", "bottega-veneta-accessories", "bv-home"]
HOME_LEAVES = [
    _leaf("bv-home-leather", "Leather", "레더", "/en-gb/home/leather", "leather-accessories", _HM),
    _leaf("bv-home-textiles", "Textiles", "텍스타일", "/en-gb/home/textiles", "textile", _HM),
    _leaf("bv-home-games", "Games", "게임", "/en-gb/home/games", "games", _HM),
    _leaf("bv-home-pet", "Pet Accessories", "펫 액세서리", "/en-gb/home/pet-accessories", "pet-accessories", _HM),
    _leaf("bv-home-decor", "Decor", "데코", "/en-gb/home/decor", "decor", _HM),
]

# --- Fragrances ---
_FR = ["bottega-veneta", "bottega-veneta-accessories", "bv-fragrances"]
FRAGRANCES_LEAVES = [
    _leaf("bv-fragrances-edp", "Eau de Parfum", "오 드 퍼퓸", "/en-gb/fragrances/fragrances-category/fragrances-category-eau-de-parfum", "fragrances-category-eau-de-parfum", _FR),
    _leaf("bv-fragrances-parfum", "Parfum", "퍼퓸", "/en-gb/fragrances/fragrances-category/fragrances-category-parfum", "fragrances-category-parfum", _FR),
    _leaf("bv-fragrances-candles", "Candles", "캔들", "/en-gb/fragrances/fragrances-category/fragrances-category-candles", "candles", _FR),
    _leaf("bv-fragrances-refill", "Refill", "리필", "/en-gb/fragrances/fragrances-category/fragrances-category-refill", "fragrances-category-refill", _FR),
    _leaf("bv-fragrances-travel-set", "Travel Set", "트래블 세트", "/en-gb/fragrances/fragrances-category/fragrances-category-travel-set", "fragrances-category-travelset", _FR),
]

# --- Gifts (membership tagging) ---
_GH = ["bottega-veneta", "bv-gifts", "bv-gifts-her"]
_GM = ["bottega-veneta", "bv-gifts", "bv-gifts-him"]
GIFTS_LEAVES = [
    _leaf("bv-gifts-her-bags", "Gifts for Her — Bags", "그녀를 위한 선물 — 백", "/en-gb/gifts/gifts-for-her/bags", "women-gifting-bags", _GH),
    _leaf("bv-gifts-her-shoes", "Gifts for Her — Shoes", "그녀를 위한 선물 — 슈즈", "/en-gb/gifts/gifts-for-her/shoes", "women-gifting-shoes", _GH),
    _leaf("bv-gifts-her-wallets", "Gifts for Her — Wallets", "그녀를 위한 선물 — 월렛", "/en-gb/gifts/gifts-for-her/wallets", "women-gifting-wallets", _GH),
    _leaf("bv-gifts-her-jewellery", "Gifts for Her — Jewellery", "그녀를 위한 선물 — 주얼리", "/en-gb/gifts/gifts-for-her/jewellery", "women-gifting-jewellery", _GH),
    _leaf("bv-gifts-her-accessories", "Gifts for Her — Accessories", "그녀를 위한 선물 — 액세서리", "/en-gb/gifts/gifts-for-her/accessories", "women-gifting-accessories", _GH),
    _leaf("bv-gifts-him-bags", "Gifts for Him — Bags", "그를 위한 선물 — 백", "/en-gb/gifts/gifts-for-him/men-gifting-bags-1", "men-gifting-bags", _GM),
    _leaf("bv-gifts-him-shoes", "Gifts for Him — Shoes", "그를 위한 선물 — 슈즈", "/en-gb/gifts/gifts-for-him/shoes", "men-gifting-shoes", _GM),
    _leaf("bv-gifts-him-wallets", "Gifts for Him — Wallets", "그를 위한 선물 — 월렛", "/en-gb/gifts/gifts-for-him/wallets", "men-gifting-wallets", _GM),
    _leaf("bv-gifts-him-jewellery", "Gifts for Him — Jewellery", "그를 위한 선물 — 주얼리", "/en-gb/gifts/gifts-for-him/jewellery", "men-gifting-jewellery", _GM),
    _leaf("bv-gifts-him-accessories", "Gifts for Him — Accessories", "그를 위한 선물 — 액세서리", "/en-gb/gifts/gifts-for-him/men-gifting-accessories-1", "men-gifting-accessories", _GM),
]

HUBS: list[dict] = [
    _hub("men-bags", cgid="men-bags", path="/en-gb/men-collection-gb/men-bags", label_en="Men Bags", label_ko="남성 백", category="bags", parents=_MB[:-1] + ["bv-men-bags"], leaves=MEN_BAGS_LEAVES),
    _hub("men-shoes", cgid="men-shoes", path="/en-gb/men-collection-gb/men-shoes", label_en="Men Shoes", label_ko="남성 슈즈", category="shoes", parents=_MS[:-1] + ["bv-men-shoes"], leaves=MEN_SHOES_LEAVES),
    _hub("men-clothing", cgid="men-clothing", path="/en-gb/men-collection-gb/men-clothing", label_en="Men Clothing", label_ko="남성 의류", category="luxury", parents=_MC[:-1] + ["bv-men-clothing"], leaves=MEN_CLOTHING_LEAVES),
    _hub("men-wallets", cgid="men-wallets", path="/en-gb/men-collection-gb/men-wallets", label_en="Men Wallets", label_ko="남성 월렛", category="accessories", parents=_MW[:-1] + ["bv-men-wallets"], leaves=MEN_WALLETS_LEAVES),
    _hub("men-travel", cgid="men-travel", path="/en-gb/men-collection-gb/men-travel", label_en="Men Travel", label_ko="남성 트래블", category="accessories", parents=[*_MT, "bv-men-travel"], leaves=MEN_TRAVEL_LEAVES),
    _hub("men-accessories", cgid="men-accessories", path="/en-gb/men-collection-gb/men-accessories", label_en="Men Accessories", label_ko="남성 액세서리", category="accessories", parents=_MA[:-1] + ["bv-men-accessories"], leaves=MEN_ACC_LEAVES),
    _hub("men-eyewear", cgid="men-eyewear", path="/en-gb/men-collection-gb/men-eyewear", label_en="Men Eyewear", label_ko="남성 아이웨어", category="accessories", parents=_ME[:-1] + ["bv-men-eyewear"], leaves=MEN_EYEWEAR_LEAVES),
    _hub("men-jewellery", cgid="men-jewellery", path="/en-gb/men-collection-gb/men-jewellery", label_en="Men Jewellery", label_ko="남성 주얼리", category="accessories", parents=_MJ[:-1] + ["bv-men-jewellery"], leaves=MEN_JEWELLERY_LEAVES),
    _hub("women-bags", cgid="women-bags", path="/en-gb/women-collection-gb/women-bags", label_en="Women Bags", label_ko="여성 백", category="bags", parents=_WB[:-1] + ["bv-women-bags"], leaves=WOMEN_BAGS_LEAVES),
    _hub("women-shoes", cgid="women-shoes", path="/en-gb/women-collection-gb/women-shoes", label_en="Women Shoes", label_ko="여성 슈즈", category="shoes", parents=_WS[:-1] + ["bv-women-shoes"], leaves=WOMEN_SHOES_LEAVES),
    _hub("women-clothing", cgid="women-clothing", path="/en-gb/women-collection-gb/women-clothing", label_en="Women Clothing", label_ko="여성 의류", category="luxury", parents=_WC[:-1] + ["bv-women-clothing"], leaves=WOMEN_CLOTHING_LEAVES),
    _hub("women-wallets", cgid="women-wallets", path="/en-gb/women-collection-gb/women-wallets", label_en="Women Wallets", label_ko="여성 월렛", category="accessories", parents=_WW[:-1] + ["bv-women-wallets"], leaves=WOMEN_WALLETS_LEAVES),
    _hub("women-travel", cgid="women-travel", path="/en-gb/women-collection-gb/women-travel", label_en="Women Travel", label_ko="여성 트래블", category="accessories", parents=[*_WT, "bv-women-travel"], leaves=WOMEN_TRAVEL_LEAVES),
    _hub("women-accessories", cgid="women-accessories", path="/en-gb/women-collection-gb/women-accessories", label_en="Women Accessories", label_ko="여성 액세서리", category="accessories", parents=_WA[:-1] + ["bv-women-accessories"], leaves=WOMEN_ACC_LEAVES),
    _hub("women-eyewear", cgid="women-eyewear", path="/en-gb/women-collection-gb/women-eyewear", label_en="Women Eyewear", label_ko="여성 아이웨어", category="accessories", parents=_WE[:-1] + ["bv-women-eyewear"], leaves=WOMEN_EYEWEAR_LEAVES),
    _hub("women-jewellery", cgid="women-jewellery", path="/en-gb/women-collection-gb/women-jewellery", label_en="Women Jewellery", label_ko="여성 주얼리", category="accessories", parents=_WJ[:-1] + ["bv-women-jewellery"], leaves=WOMEN_JEWELLERY_LEAVES),
    _hub("home", cgid="home", path="/en-gb/home-content.html", label_en="Home", label_ko="홈", category="accessories", parents=_HM, leaves=HOME_LEAVES),
    _hub("fragrances", cgid="fragrances", path="/en-gb/fragrances.html", label_en="Fragrances", label_ko="프래그런스", category="accessories", parents=_FR, leaves=FRAGRANCES_LEAVES),
    _hub(
        "gifts",
        cgid="macro-gifts",
        path="/en-gb/macro-gifts.html",
        label_en="Gifts",
        label_ko="기프트",
        category="accessories",
        parents=["bottega-veneta", "bv-gifts"],
        leaves=GIFTS_LEAVES,
        membership_only=True,
    ),
]

HUBS_BY_ID = {h["id"]: h for h in HUBS}
HUB_ORDER = [h["id"] for h in HUBS]


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
        # Prefer richer PDP / images
        if not merged.get("localImages") and prev.get("localImages"):
            merged["localImages"] = prev["localImages"]
        if not merged.get("sizes") and prev.get("sizes"):
            merged["sizes"] = prev["sizes"]
        if not merged.get("sizeGuide") and prev.get("sizeGuide"):
            merged["sizeGuide"] = prev["sizeGuide"]
        by_id[rid] = merged
    return list(by_id.values())
