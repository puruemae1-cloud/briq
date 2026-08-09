#!/usr/bin/env python3
"""Build Gucci catalogue from scraped raw
(handbags + men's bags + women's/men's RTW + women's/men's shoes + wallets +
fashion accessories + travel + jewellery + gifts).

Pricing: KRW = round_천원(GBP × 2100 × 1.05 × 1.15)
Prefer official Korean copy from Gucci catalog API; fall back to gtx translate.

Gifts: existing productCodes get gift gcCollections merged on; only truly new
gift SKUs are imported as PDPs (duplicates are never re-imported).
Men's RTW / men's bags / men's shoes: exact duplicate productCodes tag
membership onto the existing PDP instead of creating a second one.
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
MENS_HANDBAG_RAW = ROOT / "src/data/gc/gc-mens-handbags-catalog-raw.json"
RTW_RAW = ROOT / "src/data/gc/gc-rtw-catalog-raw.json"
MENS_RTW_RAW = ROOT / "src/data/gc/gc-mens-rtw-catalog-raw.json"
SHOES_RAW = ROOT / "src/data/gc/gc-shoes-catalog-raw.json"
MENS_SHOES_RAW = ROOT / "src/data/gc/gc-mens-shoes-catalog-raw.json"
WALLETS_RAW = ROOT / "src/data/gc/gc-wallets-catalog-raw.json"
FASHION_ACC_RAW = ROOT / "src/data/gc/gc-fashion-accessories-catalog-raw.json"
TRAVEL_RAW = ROOT / "src/data/gc/gc-travel-catalog-raw.json"
JEWELLERY_RAW = ROOT / "src/data/gc/gc-jewellery-catalog-raw.json"
GIFTS_RAW = ROOT / "src/data/gc/gc-gifts-catalog-raw.json"
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

MENS_HANDBAG_LEAF_COLLECTIONS = [
    "gc-men-crossbody-messengers",
    "gc-men-backpacks",
    "gc-men-tote-bags",
    "gc-men-small-bags-pouches",
    "gc-men-belt-slingbags",
    "gc-men-duffle-bags",
]

MENS_HANDBAG_PARENT_COLLECTIONS = [
    "gc-mens-handbags",
    "gucci-bags",
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

MEN_RTW_LEAF_COLLECTIONS = [
    "gc-men-tshirts-polos",
    "gc-men-tracksuit-sweatshirts",
    "gc-men-shirts",
    "gc-men-knitwear",
    "gc-men-denim",
    "gc-men-trousers-shorts",
    "gc-men-swimwear",
    "gc-men-outerwear",
    "gc-men-leather",
    "gc-men-formal-wear",
    "gc-men-coats-jackets",
]

MEN_RTW_PARENT_COLLECTIONS = [
    "gc-men-rtw",
    "gc-men",
    "gucci",
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

MEN_SHOES_LEAF_COLLECTIONS = [
    "gc-men-sneakers",
    "gc-men-loafers-moccasins",
    "gc-men-slides-sandals",
    "gc-men-driving",
    "gc-men-lace-ups",
    "gc-men-boots",
]

MEN_SHOES_PARENT_COLLECTIONS = [
    "gc-men-shoes",
    "gc-shoes-mens",
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

# Soft accessories (belts/scarves/hats/eyewear/hair/socks). Bag charms reuse
# wallets leaf id and are usually skipped as duplicates at load time.
FASHION_ACC_LEAF_COLLECTIONS = [
    "gc-women-belts",
    "gc-women-scarves-silks",
    "gc-women-hats-gloves",
    "gc-women-eyewear",
    "gc-women-hair-accessories",
    "gc-women-socks-tights",
    "gc-women-bag-charms-keychains",
]

FASHION_ACC_PARENT_COLLECTIONS = [
    "gc-women-fashion-accessories",
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

JEWELLERY_LEAF_COLLECTIONS = [
    "gc-gold-jewellery-women",
    "gc-gold-jewellery-men",
    "gc-silver-jewellery-women",
    "gc-silver-jewellery-men",
    "gc-fashion-jewellery",
    "gc-watches-women",
    "gc-watches-men",
]

JEWELLERY_PARENT_COLLECTIONS = [
    "gc-jewellery-watches",
    "gc-gold-jewellery",
    "gc-silver-jewellery",
    "gc-watches",
    "gucci-accessories",
]

GIFTS_LEAF_COLLECTIONS = [
    "gc-gifts-her",
    "gc-gifts-him",
    "gc-gifts-personalised",
    "gc-gifts-beauty",
    "gc-gifts-jewellery",
    "gc-gifts-children",
]

GIFTS_PARENT_COLLECTIONS = [
    "gc-gifts",
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

# Official Gucci UK men clothing size chart
# https://www.gucci.com/uk/en_gb/st/gucci-clothing-size-chart — Men's Size Chart
GC_MEN_RTW_TOPS = {
    "id": "tops",
    "labelKo": "상의",
    "headers": ["SIZE", "IT", "SHOULDERS (CM/IN)", "CHEST (CM/IN)"],
    "rows": [
        ["-", "40", "43 / 17", "82 / 32.3"],
        ["XXS", "42", "44 / 17.3", "86 / 33.8"],
        ["XS", "44", "45 / 17.7", "90 / 35.4"],
        ["S", "46", "46 / 18.1", "94 / 37"],
        ["M", "48", "47 / 18.5", "98 / 38.6"],
        ["L", "50", "48 / 18.9", "102 / 40.2"],
        ["XL", "52", "49 / 19.3", "106 / 41.7"],
        ["XXL", "54", "50 / 19.7", "110 / 43.3"],
        ["XXXL", "56", "51 / 20.1", "114 / 44.9"],
        ["-", "58", "52 / 20.5", "118 / 46.5"],
        ["-", "60", "53 / 20.9", "122 / 48"],
    ],
}

GC_MEN_RTW_BOTTOMS = {
    "id": "bottoms",
    "labelKo": "하의",
    "headers": ["SIZE", "IT", "JEANS", "WAIST (CM/IN)", "HIPS (CM/IN)"],
    "rows": [
        ["-", "40", "26-27", "63 / 24.8", "83 / 32.6"],
        ["XXS", "42", "28-29", "67 / 26.4", "87 / 34.2"],
        ["XS", "44", "30-31", "71 / 28", "91 / 35.8"],
        ["S", "46", "32-33", "75 / 29.5", "95 / 37.4"],
        ["M", "48", "34-35", "79 / 31.1", "99 / 39"],
        ["L", "50", "36-37", "83 / 32.7", "103 / 40.5"],
        ["XL", "52", "38-39", "87 / 34.2", "107 / 42.1"],
        ["XXL", "54", "40-41", "91 / 35.8", "111 / 43.7"],
        ["XXXL", "56", "42-43", "95 / 37.4", "115 / 45.3"],
        ["-", "58", "44-45", "99 / 39", "119 / 46.8"],
        ["-", "60", "46", "103 / 40.5", "123 / 48.4"],
    ],
}

# Men jeans waist as sold on gucci.com PDPs — expanded from official JEANS ranges.
GC_MEN_DENIM_ROWS = [
    # jeans, size, IT, waist, hips
    ["26", "-", "40", "63 / 24.8", "83 / 32.6"],
    ["27", "-", "40", "65 / 25.6", "85 / 33.5"],
    ["28", "XXS", "42", "67 / 26.4", "87 / 34.2"],
    ["29", "XXS", "42", "69 / 27.2", "89 / 35"],
    ["30", "XS", "44", "71 / 28", "91 / 35.8"],
    ["31", "XS", "44", "73 / 28.7", "93 / 36.6"],
    ["32", "S", "46", "75 / 29.5", "95 / 37.4"],
    ["33", "S", "46", "77 / 30.3", "97 / 38.2"],
    ["34", "M", "48", "79 / 31.1", "99 / 39"],
    ["35", "M", "48", "81 / 31.9", "101 / 39.8"],
    ["36", "L", "50", "83 / 32.7", "103 / 40.5"],
    ["37", "L", "50", "85 / 33.5", "105 / 41.3"],
    ["38", "XL", "52", "87 / 34.2", "107 / 42.1"],
    ["39", "XL", "52", "89 / 35", "109 / 42.9"],
    ["40", "XXL", "54", "91 / 35.8", "111 / 43.7"],
    ["41", "XXL", "54", "93 / 36.6", "113 / 44.5"],
    ["42", "XXXL", "56", "95 / 37.4", "115 / 45.3"],
    ["43", "XXXL", "56", "97 / 38.2", "117 / 46.1"],
    ["44", "-", "58", "99 / 39", "119 / 46.8"],
    ["45", "-", "58", "101 / 39.8", "121 / 47.6"],
    ["46", "-", "60", "103 / 40.5", "123 / 48.4"],
]

GC_MEN_DENIM = {
    "id": "denim",
    "labelKo": "진/데님",
    "headers": ["JEANS", "SIZE", "IT", "WAIST (CM/IN)", "HIPS (CM/IN)"],
    "rows": GC_MEN_DENIM_ROWS,
}

GC_MEN_RTW_SIZE_CHART = {
    "id": "gc-men-rtw",
    "titleKo": "구찌 남성 레디투웨어 사이즈 가이드",
    "noteKo": (
        "사이즈표는 구찌 공식 남성 의류 가이드 기준입니다. 구찌 남성 의류는 "
        "이탈리아(IT) 사이즈를 기준으로 하며, Briq 표기의 XS·S·M 또는 IT 숫자는 "
        "아래 SIZE/IT 열과 대응합니다. 진·데님은 JEANS(허리) 사이즈를 사용합니다. "
        "브랜드·시즌·실루엣에 따라 핏이 다를 수 있으니 참고용으로 확인해 주세요."
    ),
    "headers": GC_MEN_RTW_TOPS["headers"],
    "rows": GC_MEN_RTW_TOPS["rows"],
    "tabs": [GC_MEN_RTW_TOPS, GC_MEN_RTW_BOTTOMS, GC_MEN_DENIM],
}

GC_MEN_DENIM_SIZE_CHART = {
    "id": "gc-men-denim",
    "titleKo": "구찌 남성 진/데님 사이즈 가이드",
    "noteKo": (
        "이 상품은 진/데님 허리 사이즈(JEANS)로 판매됩니다. 사이즈 선택란의 "
        "IT 30·IT 32 등은 진 허리 사이즈이며, 일반 의류 IT 46·48과는 다릅니다. "
        "아래 JEANS 열을 기준으로 골라 주세요."
    ),
    "headers": GC_MEN_DENIM["headers"],
    "rows": GC_MEN_DENIM["rows"],
    "tabs": [GC_MEN_DENIM, GC_MEN_RTW_BOTTOMS, GC_MEN_RTW_TOPS],
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

# Official Gucci UK men shoes size guide
# (https://www.gucci.com/uk/en_gb/st/shoes-size-guide — Men's Shoes Size Chart).
# Official columns: SIZE, IT/EU, UK/AU, US, KR(MM), JP(CM).
# Presented like women's (IT/UK/FR/US/AU/KR/JP): IT = IT/EU, UK = UK/AU,
# FR = IT/EU (men's FR tracks EU; official table has no separate FR),
# AU = UK/AU. PDP pickers use IT sizes; half sizes as 40+ → IT 40.5.
GC_MEN_SHOES_ROWS = [
    # IT, UK, FR, US, AU, KR(mm), JP(cm)
    ["38", "4", "38", "4.5", "4", "230", "23"],
    ["38.5", "4.5", "38.5", "5", "4.5", "235", "23.5"],
    ["39", "5", "39", "5.5", "5", "240", "24"],
    ["39.5", "5.5", "39.5", "6", "5.5", "245", "24.5"],
    ["40", "6", "40", "6.5", "6", "250", "25"],
    ["40.5", "6.5", "40.5", "7", "6.5", "255", "25.5"],
    ["41", "7", "41", "7.5", "7", "260", "26"],
    ["41.5", "7.5", "41.5", "8", "7.5", "265", "26.5"],
    ["42", "8", "42", "8.5", "8", "270", "27"],
    ["42.5", "8.5", "42.5", "9", "8.5", "275", "27.5"],
    ["43", "9", "43", "9.5", "9", "280", "28"],
    ["43.5", "9.5", "43.5", "10", "9.5", "285", "28.5"],
    ["44", "10", "44", "10.5", "10", "290", "29"],
    ["44.5", "10.5", "44.5", "11", "10.5", "295", "29.5"],
    ["45", "11", "45", "11.5", "11", "300", "30"],
    ["45.5", "11.5", "45.5", "12", "11.5", "305", "30.5"],
    ["46", "12", "46", "12.5", "12", "310", "31"],
    ["46.5", "12.5", "46.5", "13", "12.5", "315", "31.5"],
    ["47", "13", "47", "13.5", "13", "320", "32"],
    ["47.5", "13.5", "47.5", "14", "13.5", "325", "32.5"],
    ["48", "14", "48", "14.5", "14", "330", "33"],
    ["48.5", "14.5", "48.5", "15", "14.5", "335", "33.5"],
    ["49", "15", "49", "15.5", "15", "340", "34"],
    ["49.5", "15.5", "49.5", "16", "15.5", "345", "34.5"],
    ["50", "16", "50", "16.5", "16", "350", "35"],
    # Extended for SKUs sold above official men chart max (IT 50 / UK 16)
    ["50.5", "16.5", "50.5", "17", "16.5", "355", "35.5"],
    ["51", "17", "51", "17.5", "17", "360", "36"],
]

GC_MEN_SHOES_SIZE_CHART = {
    "id": "gc-men-shoes",
    "titleKo": "구찌 남성 슈즈 사이즈 가이드",
    "noteKo": (
        "사이즈표는 구찌 공식 남성 슈즈 가이드"
        "(gucci.com/uk/en_gb/st/shoes-size-guide) 기준입니다. "
        "공식 표는 SIZE·IT/EU·UK/AU·US·KR·JP 열이며, Briq에서는 여성 표와 "
        "같은 IT·UK·FR·US·AU·KR·JP 형식으로 정리했습니다. IT는 IT/EU, UK·AU는 "
        "공식 UK/AU, FR는 남성 EU와 동일하게 IT/EU를 둡니다. Briq 표기 사이즈는 "
        "이탈리아(IT) 기준이며 사이즈 선택란의 IT 40·IT 40.5 등은 아래 IT 열과 "
        "대응합니다. IT 50.5·51은 일부 상품에만 제공되며 공식 표의 패턴을 "
        "연장한 값입니다. 스타일·소재에 따라 핏이 다를 수 있으니 참고용으로 "
        "확인해 주세요."
    ),
    "headers": ["IT", "UK", "FR", "US", "AU", "KR (MM)", "JP (CM)"],
    "rows": GC_MEN_SHOES_ROWS,
}

# Official Gucci UK ring & bracelet size guide
# https://www.gucci.com/uk/en_gb/st/gucci-jewelry-sizes
# Ring SIZE column matches catalog sizeDescription (01–27). LETTER column is
# the sparse XXS–XXL mapping shown on the official chart (blank header on site).
GC_RING_SIZE_ROWS = [
    # SIZE, LETTER, FR, UK, US, JP
    ["01", "-", "41", "B", "1 3/4", "1.2"],
    ["02", "-", "42", "D", "2 1/4", "2.1"],
    ["03", "-", "43", "E - F", "2 1/2", "3.1"],
    ["04", "-", "44", "F", "3", "4.0"],
    ["05", "-", "45", "F - G", "3 1/4", "5.0"],
    ["06", "-", "46", "G", "3 3/4", "5.9"],
    ["07", "-", "47", "H", "4", "6.9"],
    ["08", "XXS", "48", "I", "4 1/2", "7.8"],
    ["09", "-", "49", "J", "5", "8.8"],
    ["10", "XS", "50", "J - K", "5 1/4", "9.7"],
    ["11", "-", "51", "K - L", "5 3/4", "10.7"],
    ["12", "-", "52", "L", "6", "11.7"],
    ["13", "S", "53", "M - N", "6 1/2", "12.6"],
    ["14", "-", "54", "N - O", "6 3/4", "13.6"],
    ["15", "-", "55", "O - P", "7 1/4", "14.6"],
    ["16", "M", "56", "P", "7 1/2", "15.5"],
    ["17", "-", "57", "Q", "8", "16.4"],
    ["18", "-", "58", "Q - R", "8 1/4", "17.4"],
    ["19", "L", "59", "R", "8 3/4", "18.3"],
    ["20", "-", "60", "S", "9", "19.3"],
    ["21", "-", "61", "S - T", "9 1/2", "20.3"],
    ["22", "-", "62", "T - U", "10", "21.2"],
    ["23", "XL", "63", "U - V", "10 1/4", "22.2"],
    ["24", "-", "64", "V", "10 3/4", "23.1"],
    ["25", "-", "65", "W", "11", "24.1"],
    ["26", "XXL", "66", "X", "11 1/2", "25.0"],
    ["27", "-", "67", "X - Y", "11 3/4", "26.0"],
]

GC_RING_SIZE_CHART = {
    "id": "gc-jewellery-rings",
    "titleKo": "구찌 링 사이즈 가이드",
    "noteKo": (
        "사이즈표는 구찌 공식 링·브레이슬릿 가이드"
        "(gucci.com/uk/en_gb/st/gucci-jewelry-sizes) 기준입니다. "
        "Briq 사이즈 선택란의 숫자(예: 13)는 아래 SIZE 열과 대응합니다. "
        "중간 사이즈일 경우 더 큰 쪽을 권장합니다. 와이드 밴드는 한 사이즈 업을 "
        "권장하는 스타일이 있을 수 있습니다."
    ),
    "headers": ["SIZE", "LETTER", "FR", "UK", "US", "JP"],
    "rows": GC_RING_SIZE_ROWS,
}

GC_BRACELET_SIZE_ROWS = [
    # SIZE, CM (inner circumference), IN
    ["XS", "15", "5.9"],
    ["S", "16", "6.3"],
    ["M", "17", "6.7"],
    ["L", "18", "7"],
    ["XL", "19", "7.5"],
    ["20", "20", "7.9"],
    ["21", "21", "8.3"],
]

GC_BRACELET_SIZE_CHART = {
    "id": "gc-jewellery-bracelets",
    "titleKo": "구찌 브레이슬릿 사이즈 가이드",
    "noteKo": (
        "사이즈표는 구찌 공식 링·브레이슬릿 가이드 기준입니다. "
        "PDP 드롭다운의 숫자(예: 16·17)는 손목 안쪽 둘레(CM)에 해당합니다. "
        "가장 가까운 치수를 선택해 주세요."
    ),
    "headers": ["SIZE", "CM", "IN"],
    "rows": GC_BRACELET_SIZE_ROWS,
}

# Official Gucci belt size guide (cm from buckle to centre hole).
# https://www.gucci.com/uk/en_gb/st/gucci-belt-sizes
GC_BELT_SIZE_ROWS = [
    # SIZE(cm), IT, EU, UK, US, JEANS
    ["65", "34", "30", "2", "00", "20–22"],
    ["70", "36", "32", "4", "0", "22–24"],
    ["75", "38", "34", "6", "2", "24–26"],
    ["80", "40", "36", "8", "4", "26–28"],
    ["85", "42", "38", "10", "6", "28–30"],
    ["90", "44", "40", "12", "8", "30–32"],
    ["95", "46", "42", "14", "10", "32–34"],
    ["100", "48", "44", "16", "12", "34–36"],
    ["105", "50", "46", "18", "14", "36–38"],
    ["110", "52", "48", "20", "16", "38–40"],
    ["115", "54", "50", "22", "18", "40–42"],
    ["120", "56", "52", "24", "20", "42–44"],
]

GC_BELT_SIZE_CHART = {
    "id": "gc-women-belts",
    "titleKo": "구찌 벨트 사이즈 가이드",
    "noteKo": (
        "사이즈(cm)는 버클 끝에서 가운데 구멍까지의 길이입니다"
        "(gucci.com 벨트 사이즈 가이드). 힙에 착용할 때는 로우라이즈 "
        "진 사이즈를 참고하고, 허리에 착용할 때는 한 사이즈 작게 "
        "선택하세요. 중간 사이즈일 경우 더 큰 쪽을 권장합니다."
    ),
    "headers": ["SIZE (CM)", "IT", "EU", "UK", "US", "JEANS"],
    "rows": GC_BELT_SIZE_ROWS,
}

# Head circumference guide for lettered hat sizes (Gucci soft accessories).
GC_HAT_SIZE_CHART = {
    "id": "gc-women-hats",
    "titleKo": "구찌 모자 사이즈 가이드",
    "noteKo": (
        "머리 둘레(cm) 참고표입니다. 스타일·소재에 따라 핏이 다를 수 있으니 "
        "중간 사이즈일 경우 더 큰 쪽을 권장합니다."
    ),
    "headers": ["SIZE", "머리 둘레 (CM)", "머리 둘레 (IN)"],
    "rows": [
        ["XXS", "52–53", "20.5–20.9"],
        ["XS", "53–54", "20.9–21.3"],
        ["S", "55–56", "21.7–22"],
        ["M", "57–58", "22.4–22.8"],
        ["L", "59–60", "23.2–23.6"],
        ["XL", "61–62", "24–24.4"],
        ["XXL", "63–64", "24.8–25.2"],
    ],
}

# Letter sock / tight sizes mapped to approximate EU shoe range.
GC_SOCKS_SIZE_CHART = {
    "id": "gc-women-socks",
    "titleKo": "구찌 삭스·타이즈 사이즈 가이드",
    "noteKo": (
        "알파벳 사이즈는 대략적인 EU 슈즈 범위 기준입니다. "
        "중간 사이즈일 경우 더 큰 쪽을 선택하세요."
    ),
    "headers": ["SIZE", "EU", "UK", "US", "KR (MM)"],
    "rows": [
        ["XS", "34–36", "1–3", "4–6", "210–225"],
        ["S", "35–37", "2–4", "5–7", "220–235"],
        ["M", "38–40", "5–7", "7.5–9.5", "240–255"],
        ["L", "41–43", "8–10", "10–12", "260–275"],
        ["XL", "44–46", "11–13", "12.5–14.5", "280–295"],
    ],
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


def size_chart_for_mens_rtw(variants: list[dict]) -> dict:
    """Pick men denim jeans chart when PDP sizes are waist ~26–42, else men RTW."""
    nums = _variant_size_numbers(variants)
    if nums and max(nums) <= 46 and min(nums) <= 34 and max(nums) - min(nums) <= 22:
        # Jeans waist (e.g. 28–36), not apparel IT 44–56
        if max(nums) < 44 or min(nums) < 40:
            return GC_MEN_DENIM_SIZE_CHART
    return GC_MEN_RTW_SIZE_CHART


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


def men_shoe_uk_to_it(size: str) -> str:
    """Gucci men catalog sizeDescription is UK (= official SIZE column).

    Official IT/EU = UK + 34 (see shoes-size-guide Men's chart).
    Values already in IT range (≥34) are left unchanged (re-scraped raw).
    """
    s = (size or "").strip()
    if s.endswith("+") and s[:-1].replace(".", "", 1).isdigit():
        s = f"{s[:-1]}.5"
    try:
        val = float(s)
    except ValueError:
        return s
    if val >= 34:
        it = val
    else:
        it = val + 34.0
    if it == int(it):
        return str(int(it))
    return f"{it:.1f}".rstrip("0").rstrip(".")


def format_men_shoe_size_label(size: str) -> str:
    return format_shoe_size_label(men_shoe_uk_to_it(size))


def format_jewellery_size_label(size: str, kind: str) -> str:
    s = (size or "").strip()
    if not s or s.upper() in {"U", "OS", "ONE SIZE", "NS"}:
        return "One Size"
    if kind == "bracelet" and re.fullmatch(r"\d+", s):
        return f"{s} cm"
    if kind == "ring" and re.fullmatch(r"\d+", s):
        # Keep Gucci SIZE as zero-padded when catalog sends 06 / 13
        return s.zfill(2) if len(s) <= 2 else s
    return s


def format_fashion_acc_size_label(size: str, kind: str) -> str:
    s = (size or "").strip()
    if not s or s.upper() in {"U", "OS", "ONE SIZE", "NS"}:
        return "One Size"
    if kind == "belt" and re.fullmatch(r"\d+", s):
        return f"{s} cm"
    if kind in {"hat", "socks"}:
        return s.upper()
    return s


def fashion_acc_size_kind(row: dict, size_rows: list[dict]) -> str:
    """belt | hat | socks | onesize — from leaf membership + size set."""
    cols = set(row.get("collections") or [])
    raw_sizes = [
        str(sz.get("size") or "").strip()
        for sz in size_rows
        if str(sz.get("size") or "").strip()
    ]
    meaningful = [
        s for s in raw_sizes if s.upper() not in {"U", "OS", "ONE SIZE", "NS"}
    ]
    if not meaningful:
        return "onesize"
    if "gc-women-belts" in cols:
        return "belt"
    if "gc-women-hats-gloves" in cols:
        return "hat"
    if "gc-women-socks-tights" in cols:
        return "socks"
    # Numeric cm-like sizes without leaf hint → belt
    if all(re.fullmatch(r"\d+", s) for s in meaningful):
        nums = [int(s) for s in meaningful]
        if min(nums) >= 60 and max(nums) <= 130:
            return "belt"
    letters = {s.upper() for s in meaningful}
    if letters & {"XXS", "XS", "S", "M", "L", "XL", "XXL"}:
        title = f"{row.get('title') or ''} {row.get('variant') or ''}".lower()
        if re.search(r"\b(sock|tight|pantyhose|stocking)\b", title):
            return "socks"
        return "hat"
    return "onesize"


def jewellery_size_kind(row: dict, size_rows: list[dict]) -> str:
    """ring | bracelet | onesize — from nested PLP hints, title, and size set."""
    hints = {str(h).lower() for h in (row.get("typeHints") or [])}
    title = f"{row.get('title') or ''} {row.get('variant') or ''}".lower()
    raw_sizes = [
        str(sz.get("size") or "").strip()
        for sz in size_rows
        if str(sz.get("size") or "").strip()
    ]
    meaningful = [
        s for s in raw_sizes if s.upper() not in {"U", "OS", "ONE SIZE", "NS"}
    ]
    if not meaningful:
        return "onesize"
    if "rings" in hints or re.search(r"\bring\b", title):
        return "ring"
    if "bracelets" in hints or re.search(r"\b(bracelet|bangle|cuff)\b", title):
        return "bracelet"
    letters = {s.upper() for s in meaningful}
    if letters & {"XS", "S", "M", "L", "XL", "XXS", "XXL"}:
        return "bracelet"
    nums: list[int] = []
    for s in meaningful:
        if re.fullmatch(r"\d+", s):
            nums.append(int(s))
    if nums and min(nums) >= 15 and max(nums) <= 21 and "ring" not in title:
        return "bracelet"
    return "ring"


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


def build_mens_handbag_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    """Men's bags — same pricing / One Size + dimensions pattern as women's handbags."""
    code = row.get("productCode") or row.get("id")
    if not code:
        return None
    gbp = row.get("gbpPrice")
    if gbp is None:
        return None
    price = gbp_to_krw(float(gbp))
    if price <= 0:
        return None

    allowed = {
        *MENS_HANDBAG_LEAF_COLLECTIONS,
        *MENS_HANDBAG_PARENT_COLLECTIONS,
    }
    cols = [c for c in (row.get("collections") or []) if c in allowed]
    if any(c in MENS_HANDBAG_LEAF_COLLECTIONS for c in cols) and "gc-mens-handbags" not in cols:
        cols.append("gc-mens-handbags")
    if "gucci-bags" not in cols:
        cols.append("gucci-bags")
    cols = sorted(set(cols))
    if not cols:
        cols = ["gc-mens-handbags", "gucci-bags"]

    leaf = next(
        (c for c in MENS_HANDBAG_LEAF_COLLECTIONS if c in cols),
        "gc-mens-handbags",
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

    tags = ["gucci", "구찌", "handbag", "핸드백", "남성", "mens", *cols]
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


def build_mens_rtw_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
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
        if c
        in {
            *MEN_RTW_LEAF_COLLECTIONS,
            *MEN_RTW_PARENT_COLLECTIONS,
        }
    ]
    cols = sorted(set([*cols, "gc-men-rtw", "gc-men", "gucci"]))

    leaf = next((c for c in MEN_RTW_LEAF_COLLECTIONS if c in cols), "gc-men-rtw")
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

    tags = ["gucci", "구찌", "rtw", "의류", "남성", "mens", "ready-to-wear", *cols]
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
        "sizeChart": size_chart_for_mens_rtw(variants),
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


def build_fashion_accessory_product(
    row: dict, prev: dict | None, now_iso: str
) -> dict | None:
    """Belts / scarves / hats / eyewear / hair / socks — sized when catalog has variants."""
    code = row.get("productCode") or row.get("id")
    if not code:
        return None
    gbp = row.get("gbpPrice")
    if gbp is None:
        return None
    price = gbp_to_krw(float(gbp))
    if price <= 0:
        return None

    allowed = {
        *FASHION_ACC_LEAF_COLLECTIONS,
        *FASHION_ACC_PARENT_COLLECTIONS,
        # Bag charms may also carry wallet parents from the scraper.
        *WALLETS_PARENT_COLLECTIONS,
        "gc-women-wallets",
    }
    cols = [c for c in (row.get("collections") or []) if c in allowed]
    cols = sorted(set([*cols, *FASHION_ACC_PARENT_COLLECTIONS]))

    leaf = next(
        (c for c in FASHION_ACC_LEAF_COLLECTIONS if c in cols),
        "gc-women-fashion-accessories",
    )
    copy = common_copy(row)
    pid = f"gc-{str(code).lower()}"
    registered = (prev or {}).get("registeredAt") or now_iso
    in_stock = bool(row.get("inStock", True))

    size_rows = row.get("sizes") or []
    kind = fashion_acc_size_kind(row, size_rows)
    variants: list[dict] = []
    if kind != "onesize" and size_rows:
        for sz in size_rows:
            size_raw = str(sz.get("size") or "").strip()
            if not size_raw:
                continue
            if size_raw.upper() in {"U", "OS", "ONE SIZE", "NS"}:
                continue
            label = format_fashion_acc_size_label(size_raw, kind)
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
                "id": f"{pid}-u",
                "name": f"{copy['title_en']} — {copy['color_en'] or 'One Size'}".strip(
                    " —"
                ),
                "nameKo": f"{copy['name_ko']} — {copy['color_ko'] or '원 사이즈'}".strip(
                    " —"
                ),
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

    tags = [
        "gucci",
        "구찌",
        "accessories",
        "악세서리",
        "패션 액세서리",
        "여성",
        *cols,
    ]
    badge = None
    label = (row.get("label") or "").lower()
    if "new" in label:
        badge = "New"

    size_chart = None
    has_sized = any(v.get("size") != "One Size" for v in variants)
    if kind == "belt" and has_sized:
        size_chart = GC_BELT_SIZE_CHART
    elif kind == "hat" and has_sized:
        size_chart = GC_HAT_SIZE_CHART
    elif kind == "socks" and has_sized:
        size_chart = GC_SOCKS_SIZE_CHART

    prod = {
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
        "inStock": in_stock,
        "variants": variants,
        "storySections": copy["story"],
        "registeredAt": registered,
        "editTier": "new" if badge == "New" else "signature",
    }
    if size_chart:
        prod["sizeChart"] = size_chart
    return prod


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


def build_jewellery_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    """Jewellery & watches — ring/bracelet size charts when variants exist."""
    code = row.get("productCode") or row.get("id")
    if not code:
        return None
    gbp = row.get("gbpPrice")
    if gbp is None:
        return None
    price = gbp_to_krw(float(gbp))
    if price <= 0:
        return None

    allowed = {*JEWELLERY_LEAF_COLLECTIONS, *JEWELLERY_PARENT_COLLECTIONS}
    cols = [c for c in (row.get("collections") or []) if c in allowed]
    cols = sorted(set([*cols, "gc-jewellery-watches", "gucci-accessories"]))

    leaf = next(
        (c for c in JEWELLERY_LEAF_COLLECTIONS if c in cols), "gc-jewellery-watches"
    )
    copy = common_copy(row)
    pid = f"gc-{str(code).lower()}"
    registered = (prev or {}).get("registeredAt") or now_iso
    in_stock = bool(row.get("inStock", True))

    size_rows = row.get("sizes") or []
    kind = jewellery_size_kind(row, size_rows)
    variants: list[dict] = []
    if kind != "onesize" and size_rows:
        for sz in size_rows:
            size_raw = str(sz.get("size") or "").strip()
            if not size_raw:
                continue
            if size_raw.upper() in {"U", "OS", "ONE SIZE", "NS"}:
                continue
            label = format_jewellery_size_label(size_raw, kind)
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
                "id": f"{pid}-u",
                "name": f"{copy['title_en']} — {copy['color_en'] or 'One Size'}".strip(
                    " —"
                ),
                "nameKo": f"{copy['name_ko']} — {copy['color_ko'] or '원 사이즈'}".strip(
                    " —"
                ),
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

    tags = [
        "gucci",
        "구찌",
        "jewellery",
        "쥬얼리",
        "watches",
        "시계",
        "악세서리",
        *cols,
    ]
    badge = None
    label = (row.get("label") or "").lower()
    if "new" in label:
        badge = "New"

    size_chart = None
    if kind == "ring" and any(v.get("size") != "One Size" for v in variants):
        size_chart = GC_RING_SIZE_CHART
    elif kind == "bracelet" and any(v.get("size") != "One Size" for v in variants):
        size_chart = GC_BRACELET_SIZE_CHART

    prod = {
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
        "inStock": in_stock,
        "variants": variants,
        "storySections": copy["story"],
        "registeredAt": registered,
        "editTier": "new" if badge == "New" else "signature",
    }
    if size_chart:
        prod["sizeChart"] = size_chart
    return prod


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


def build_mens_shoe_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    code = row.get("productCode") or row.get("id")
    if not code:
        return None
    gbp = row.get("gbpPrice")
    if gbp is None:
        return None
    price = gbp_to_krw(float(gbp))
    if price <= 0:
        return None

    allowed = {*MEN_SHOES_LEAF_COLLECTIONS, *MEN_SHOES_PARENT_COLLECTIONS}
    cols = [c for c in (row.get("collections") or []) if c in allowed]
    if any(c in MEN_SHOES_LEAF_COLLECTIONS for c in cols) and "gc-men-shoes" not in cols:
        cols.append("gc-men-shoes")
    if "gc-shoes-mens" not in cols:
        cols.append("gc-shoes-mens")
    if "gucci-shoes" not in cols:
        cols.append("gucci-shoes")
    cols = sorted(set(cols))
    if not any(c in MEN_SHOES_LEAF_COLLECTIONS for c in cols):
        cols = sorted(set([*cols, *MEN_SHOES_PARENT_COLLECTIONS]))

    leaf = next(
        (c for c in MEN_SHOES_LEAF_COLLECTIONS if c in cols),
        "gc-men-shoes",
    )
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
            label = format_men_shoe_size_label(size_raw)
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

    tags = ["gucci", "구찌", "shoes", "슈즈", "남성", "mens", *cols]
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
        "sizeChart": GC_MEN_SHOES_SIZE_CHART,
        "storySections": copy["story"],
        "registeredAt": registered,
        "editTier": "new" if badge == "New" else "signature",
    }


def build_gift_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    """New gift-only SKUs (beauty, kids, men's gifts not already in catalogue)."""
    code = row.get("productCode") or row.get("id")
    if not code:
        return None
    gbp = row.get("gbpPrice")
    if gbp is None:
        return None
    price = gbp_to_krw(float(gbp))
    if price <= 0:
        return None

    allowed = {*GIFTS_LEAF_COLLECTIONS, *GIFTS_PARENT_COLLECTIONS}
    cols = [c for c in (row.get("collections") or []) if c in allowed]
    cols = sorted(set([*cols, *GIFTS_PARENT_COLLECTIONS]))

    leaf = next((c for c in GIFTS_LEAF_COLLECTIONS if c in cols), "gc-gifts")
    copy = common_copy(row)
    pid = f"gc-{str(code).lower()}"
    registered = (prev or {}).get("registeredAt") or now_iso
    in_stock = bool(row.get("inStock", True))

    size_rows = row.get("sizes") or []
    variants: list[dict] = []
    for sz in size_rows:
        size_raw = str(sz.get("size") or "").strip()
        if not size_raw:
            continue
        if size_raw.upper() in {"U", "OS", "ONE SIZE", "NS"}:
            continue
        label = size_raw
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
                "name": f"{copy['title_en']} — {copy['color_en'] or 'One Size'}".strip(
                    " —"
                ),
                "nameKo": f"{copy['name_ko']} — {copy['color_ko'] or '원 사이즈'}".strip(
                    " —"
                ),
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

    tags = ["gucci", "구찌", "gift", "선물", "악세서리", *cols]
    if "gc-gifts-beauty" in cols:
        tags.extend(["fragrance", "향수", "makeup", "메이크업", "뷰티"])
    if "gc-gifts-children" in cols:
        tags.extend(["kids", "키즈", "children"])
    if "gc-gifts-personalised" in cols:
        tags.extend(["personalised", "퍼스널라이즈", "monogram"])

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
        "inStock": in_stock,
        "variants": variants,
        "storySections": copy["story"],
        "registeredAt": registered,
        "editTier": "new" if badge == "New" else "signature",
    }


def build_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    kind = (row.get("kind") or "").lower()
    cols = row.get("collections") or []
    if kind == "gifts":
        return build_gift_product(row, prev, now_iso)
    if kind in {"mens-handbags", "mens_handbags", "men-handbags"} or any(
        c in MENS_HANDBAG_LEAF_COLLECTIONS or c == "gc-mens-handbags" for c in cols
    ):
        return build_mens_handbag_product(row, prev, now_iso)
    if kind in {"mens-shoes", "mens_shoes", "men-shoes"} or any(
        c in MEN_SHOES_LEAF_COLLECTIONS or c in {"gc-men-shoes", "gc-shoes-mens"}
        for c in cols
    ):
        return build_mens_shoe_product(row, prev, now_iso)
    if kind == "shoes" or any(
        c in SHOES_LEAF_COLLECTIONS or c in SHOES_PARENT_COLLECTIONS for c in cols
    ):
        return build_shoe_product(row, prev, now_iso)
    if kind in {"mens-rtw", "men-rtw", "mens_rtw"} or any(
        c in MEN_RTW_LEAF_COLLECTIONS or c in {"gc-men-rtw", "gc-men"} for c in cols
    ):
        return build_mens_rtw_product(row, prev, now_iso)
    if kind == "rtw" or any(
        c in RTW_LEAF_COLLECTIONS or c in {"gc-women-rtw", "gc-women"} for c in cols
    ):
        return build_rtw_product(row, prev, now_iso)
    # Jewellery before travel/wallets — do NOT match bare gucci-accessories
    # (shared with wallets/travel/fashion).
    if kind in {"jewellery", "jewelry"} or any(
        c in JEWELLERY_LEAF_COLLECTIONS
        or c
        in {
            "gc-jewellery-watches",
            "gc-gold-jewellery",
            "gc-silver-jewellery",
            "gc-watches",
        }
        for c in cols
    ):
        return build_jewellery_product(row, prev, now_iso)
    # Travel before wallets — shared parents (gucci-accessories) must not misroute.
    if kind == "travel" or any(
        c in TRAVEL_LEAF_COLLECTIONS or c == "gc-women-travel" for c in cols
    ):
        return build_travel_product(row, prev, now_iso)
    # Fashion soft accessories before wallets — bag charms leaf is shared.
    if kind in {"fashion-accessories", "fashion_accessories"} or any(
        c in FASHION_ACC_LEAF_COLLECTIONS or c == "gc-women-fashion-accessories"
        for c in cols
    ):
        # Pure bag-charms rows (no other fashion leaf) keep wallet builder.
        fashion_leaves = [
            c
            for c in cols
            if c in FASHION_ACC_LEAF_COLLECTIONS
            and c != "gc-women-bag-charms-keychains"
        ]
        if not fashion_leaves and "gc-women-bag-charms-keychains" in cols:
            return build_wallet_product(row, prev, now_iso)
        return build_fashion_accessory_product(row, prev, now_iso)
    if kind == "wallets" or any(
        c in WALLETS_LEAF_COLLECTIONS or c == "gc-women-wallets" for c in cols
    ):
        return build_wallet_product(row, prev, now_iso)
    return build_handbag_product(row, prev, now_iso)


def dedupe_style_color_name(products: list[dict]) -> list[dict]:
    """Drop near-duplicate colourways that share style + colour + name + variant.

    Gucci keys by full productCode (style+material+colour). True clones reuse the
    same variation copy at the same price with different material codes — keep the
    richer gallery. Distinct materials (e.g. leather vs GG canvas, or hand-treated
    vs plain leather) must remain separate PDPs even when the 4-digit colour matches.
    """
    pat = re.compile(r"^(\d{6})([A-Z0-9]{5})(\d{4})$", re.I)
    buckets: dict[tuple[str, str, str, str], list[dict]] = {}
    passthrough: list[dict] = []
    for p in products:
        sku = str(p.get("sku") or "").upper()
        m = pat.match(sku)
        if not m:
            passthrough.append(p)
            continue
        style, _mat, color = m.groups()
        name = str(p.get("name") or "").strip().lower()
        variant = ""
        for v in p.get("variants") or []:
            # "Name — black leather" → variation side
            vn = str(v.get("name") or "")
            if " — " in vn:
                variant = vn.split(" — ", 1)[-1].strip().lower()
                break
            if " - " in vn:
                variant = vn.split(" - ", 1)[-1].strip().lower()
                break
        if not variant:
            accent = p.get("accent") or {}
            if isinstance(accent, dict):
                variant = str(accent.get("labelEn") or accent.get("label") or "").strip().lower()
        buckets.setdefault((style, color.upper(), name, variant), []).append(p)

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


def gift_cols_from_row(row: dict) -> list[str]:
    allowed = {*GIFTS_LEAF_COLLECTIONS, *GIFTS_PARENT_COLLECTIONS}
    return sorted({c for c in (row.get("collections") or []) if c in allowed})


def mens_rtw_cols_from_row(row: dict) -> list[str]:
    allowed = {*MEN_RTW_LEAF_COLLECTIONS, *MEN_RTW_PARENT_COLLECTIONS}
    cols = {c for c in (row.get("collections") or []) if c in allowed}
    if any(c in MEN_RTW_LEAF_COLLECTIONS for c in cols):
        cols.add("gc-men-rtw")
        cols.add("gc-men")
        cols.add("gucci")
    elif "gc-men-rtw" in cols or "gc-men" in cols:
        cols.add("gc-men-rtw")
        cols.add("gc-men")
        cols.add("gucci")
    return sorted(cols)


def apply_mens_rtw_membership(
    products: list[dict], mens_rtw_tags: dict[str, list[str]]
) -> int:
    """Merge men's RTW collection ids onto existing (often women's) PDPs."""
    tagged = 0
    for p in products:
        sku = str(p.get("sku") or "").upper()
        extra = mens_rtw_tags.get(sku)
        if not extra:
            continue
        cols = sorted(set(p.get("gcCollections") or []) | set(extra))
        if cols != sorted(p.get("gcCollections") or []):
            tagged += 1
        p["gcCollections"] = cols
        tags = list(p.get("tags") or [])
        for c in extra:
            if c not in tags:
                tags.append(c)
        for t in ("rtw", "의류", "남성", "mens", "ready-to-wear"):
            if t not in tags:
                tags.append(t)
        p["tags"] = tags
        # If previously women's-only, keep women's tags but ensure men's nav works
        for v in p.get("variants") or []:
            if "gcCollections" in v:
                v["gcCollections"] = sorted(
                    set(v.get("gcCollections") or []) | set(extra)
                )
    return tagged


def mens_shoe_cols_from_row(row: dict) -> list[str]:
    allowed = {*MEN_SHOES_LEAF_COLLECTIONS, *MEN_SHOES_PARENT_COLLECTIONS}
    cols = {c for c in (row.get("collections") or []) if c in allowed}
    if any(c in MEN_SHOES_LEAF_COLLECTIONS for c in cols):
        cols.add("gc-men-shoes")
        cols.add("gc-shoes-mens")
        cols.add("gucci-shoes")
    elif "gc-men-shoes" in cols or "gc-shoes-mens" in cols:
        cols.add("gc-men-shoes")
        cols.add("gc-shoes-mens")
        cols.add("gucci-shoes")
    return sorted(cols)


def apply_mens_shoe_membership(
    products: list[dict], mens_tags: dict[str, list[str]]
) -> int:
    """Merge men's shoe collection ids onto existing (often women's) PDPs.

    Exact duplicates are not re-imported; they still appear under 남성용 슈즈.
    """
    tagged = 0
    for p in products:
        sku = str(p.get("sku") or "").upper()
        extra = mens_tags.get(sku)
        if not extra:
            continue
        cols = sorted(set(p.get("gcCollections") or []) | set(extra))
        if cols != sorted(p.get("gcCollections") or []):
            tagged += 1
        p["gcCollections"] = cols
        tags = list(p.get("tags") or [])
        for c in extra:
            if c not in tags:
                tags.append(c)
        for t in ("shoes", "슈즈", "남성", "mens"):
            if t not in tags:
                tags.append(t)
        p["tags"] = tags
        # Shared unisex SKUs keep women's size chart if already set; only attach
        # men's chart when the PDP has no shoe chart yet.
        if not p.get("sizeChart"):
            p["sizeChart"] = GC_MEN_SHOES_SIZE_CHART
        for v in p.get("variants") or []:
            if "gcCollections" in v:
                v["gcCollections"] = sorted(
                    set(v.get("gcCollections") or []) | set(extra)
                )
    return tagged


def mens_bag_cols_from_row(row: dict) -> list[str]:
    allowed = {*MENS_HANDBAG_LEAF_COLLECTIONS, *MENS_HANDBAG_PARENT_COLLECTIONS}
    cols = {c for c in (row.get("collections") or []) if c in allowed}
    if any(c in MENS_HANDBAG_LEAF_COLLECTIONS for c in cols):
        cols.add("gc-mens-handbags")
        cols.add("gucci-bags")
    elif "gc-mens-handbags" in cols:
        cols.add("gucci-bags")
    return sorted(cols)


def apply_gift_membership(products: list[dict], gift_tags: dict[str, list[str]]) -> int:
    """Merge gift collection ids onto existing products. Returns tagged count."""
    tagged = 0
    for p in products:
        sku = str(p.get("sku") or "").upper()
        extra = gift_tags.get(sku)
        if not extra:
            continue
        cols = sorted(set(p.get("gcCollections") or []) | set(extra))
        if cols != sorted(p.get("gcCollections") or []):
            tagged += 1
        p["gcCollections"] = cols
        tags = list(p.get("tags") or [])
        for c in extra:
            if c not in tags:
                tags.append(c)
        if "gift" not in tags:
            tags.append("gift")
        if "선물" not in tags:
            tags.append("선물")
        p["tags"] = tags
        for v in p.get("variants") or []:
            if "gcCollections" in v:
                v["gcCollections"] = sorted(
                    set(v.get("gcCollections") or []) | set(extra)
                )
    return tagged


def apply_mens_bag_membership(
    products: list[dict], mens_tags: dict[str, list[str]]
) -> int:
    """Merge men's bag collection ids onto existing (often women's) PDPs.

    Exact duplicates are not re-imported; they still appear under 남성용 핸드백.
    """
    tagged = 0
    for p in products:
        sku = str(p.get("sku") or "").upper()
        extra = mens_tags.get(sku)
        if not extra:
            continue
        cols = sorted(set(p.get("gcCollections") or []) | set(extra))
        if cols != sorted(p.get("gcCollections") or []):
            tagged += 1
        p["gcCollections"] = cols
        tags = list(p.get("tags") or [])
        for c in extra:
            if c not in tags:
                tags.append(c)
        for t in ("handbag", "핸드백", "남성", "mens"):
            if t not in tags:
                tags.append(t)
        p["tags"] = tags
        for v in p.get("variants") or []:
            if "gcCollections" in v:
                v["gcCollections"] = sorted(
                    set(v.get("gcCollections") or []) | set(extra)
                )
    return tagged


def load_rows() -> tuple[
    list[dict],
    dict,
    dict,
    dict,
    dict,
    dict,
    dict,
    dict,
    dict,
    dict[str, list[str]],
    dict[str, list[str]],
    dict[str, list[str]],
    dict[str, list[str]],
]:
    """Load raw rows. Later sources skip duplicates already in catalog.

    Returns gift_tags / mens_bag_tags / mens_rtw_tags / mens_shoes_tags:
    sku → collection ids to merge onto existing products (no second PDP).
    """
    rows: list[dict] = []
    existing_skus: set[str] = set()
    existing_ids: set[str] = set()
    existing_style_colors: set[tuple[str, str]] = set()
    gift_tags: dict[str, list[str]] = {}
    mens_bag_tags: dict[str, list[str]] = {}
    mens_rtw_tags: dict[str, list[str]] = {}
    mens_shoes_tags: dict[str, list[str]] = {}

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

    mens_bag_stats = {
        "raw": 0,
        "skipped_existing_sku": 0,
        "skipped_existing_id": 0,
        "skipped_style_color": 0,
        "tagged_existing": 0,
        "kept": 0,
    }
    if MENS_HANDBAG_RAW.exists():
        data = json.loads(MENS_HANDBAG_RAW.read_text())
        for row in data.get("products") or []:
            mens_bag_stats["raw"] += 1
            row = dict(row)
            row["kind"] = "mens-handbags"
            sku = str(row.get("productCode") or row.get("id") or "")
            briq_id = f"gc-{sku.lower()}" if sku else ""
            mcols = mens_bag_cols_from_row(row)
            if sku.upper() in existing_skus:
                if mcols:
                    mens_bag_tags[sku.upper()] = mcols
                    mens_bag_stats["tagged_existing"] += 1
                mens_bag_stats["skipped_existing_sku"] += 1
                continue
            if briq_id and briq_id in existing_ids:
                if mcols:
                    mens_bag_tags[sku.upper()] = mcols
                    mens_bag_stats["tagged_existing"] += 1
                mens_bag_stats["skipped_existing_id"] += 1
                continue
            # Do not skip on style+colour alone — leather vs canvas (etc.) share
            # the 4-digit colour code but are distinct PDPs on gucci.com.
            mens_bag_stats["kept"] += 1
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

    mens_rtw_stats = {
        "raw": 0,
        "skipped_existing_sku": 0,
        "skipped_existing_id": 0,
        "tagged_existing": 0,
        "kept": 0,
    }
    if MENS_RTW_RAW.exists():
        data = json.loads(MENS_RTW_RAW.read_text())
        for row in data.get("products") or []:
            mens_rtw_stats["raw"] += 1
            row = dict(row)
            row["kind"] = "mens-rtw"
            sku = str(row.get("productCode") or row.get("id") or "")
            briq_id = f"gc-{sku.lower()}" if sku else ""
            mcols = mens_rtw_cols_from_row(row)
            if sku.upper() in existing_skus:
                if mcols:
                    mens_rtw_tags[sku.upper()] = mcols
                    mens_rtw_stats["tagged_existing"] += 1
                mens_rtw_stats["skipped_existing_sku"] += 1
                continue
            if briq_id and briq_id in existing_ids:
                if mcols:
                    mens_rtw_tags[sku.upper()] = mcols
                    mens_rtw_stats["tagged_existing"] += 1
                mens_rtw_stats["skipped_existing_id"] += 1
                continue
            mens_rtw_stats["kept"] += 1
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

    mens_shoes_stats = {
        "raw": 0,
        "skipped_existing_sku": 0,
        "skipped_existing_id": 0,
        "tagged_existing": 0,
        "kept": 0,
    }
    if MENS_SHOES_RAW.exists():
        data = json.loads(MENS_SHOES_RAW.read_text())
        for row in data.get("products") or []:
            mens_shoes_stats["raw"] += 1
            row = dict(row)
            row["kind"] = "mens-shoes"
            sku = str(row.get("productCode") or row.get("id") or "")
            briq_id = f"gc-{sku.lower()}" if sku else ""
            mcols = mens_shoe_cols_from_row(row)
            if sku.upper() in existing_skus:
                if mcols:
                    mens_shoes_tags[sku.upper()] = mcols
                    mens_shoes_stats["tagged_existing"] += 1
                mens_shoes_stats["skipped_existing_sku"] += 1
                continue
            if briq_id and briq_id in existing_ids:
                if mcols:
                    mens_shoes_tags[sku.upper()] = mcols
                    mens_shoes_stats["tagged_existing"] += 1
                mens_shoes_stats["skipped_existing_id"] += 1
                continue
            mens_shoes_stats["kept"] += 1
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

    fashion_stats = {
        "raw": 0,
        "skipped_existing_sku": 0,
        "skipped_existing_id": 0,
        "skipped_style_color": 0,
        "kept": 0,
    }
    if FASHION_ACC_RAW.exists():
        data = json.loads(FASHION_ACC_RAW.read_text())
        for row in data.get("products") or []:
            fashion_stats["raw"] += 1
            row = dict(row)
            row["kind"] = "fashion-accessories"
            sku = str(row.get("productCode") or row.get("id") or "")
            briq_id = f"gc-{sku.lower()}" if sku else ""
            if sku.upper() in existing_skus:
                fashion_stats["skipped_existing_sku"] += 1
                continue
            if briq_id and briq_id in existing_ids:
                fashion_stats["skipped_existing_id"] += 1
                continue
            sc = style_color_key(sku)
            if sc and sc in existing_style_colors:
                fashion_stats["skipped_style_color"] += 1
                continue
            fashion_stats["kept"] += 1
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

    jewellery_stats = {
        "raw": 0,
        "skipped_existing_sku": 0,
        "skipped_existing_id": 0,
        "skipped_style_color": 0,
        "kept": 0,
    }
    if JEWELLERY_RAW.exists():
        data = json.loads(JEWELLERY_RAW.read_text())
        for row in data.get("products") or []:
            jewellery_stats["raw"] += 1
            row = dict(row)
            row["kind"] = "jewellery"
            sku = str(row.get("productCode") or row.get("id") or "")
            briq_id = f"gc-{sku.lower()}" if sku else ""
            if sku.upper() in existing_skus:
                jewellery_stats["skipped_existing_sku"] += 1
                continue
            if briq_id and briq_id in existing_ids:
                jewellery_stats["skipped_existing_id"] += 1
                continue
            sc = style_color_key(sku)
            if sc and sc in existing_style_colors:
                jewellery_stats["skipped_style_color"] += 1
                continue
            jewellery_stats["kept"] += 1
            remember(sku)
            rows.append(row)

    gifts_stats = {
        "raw": 0,
        "tagged_existing": 0,
        "skipped_style_color": 0,
        "kept_new": 0,
    }
    if GIFTS_RAW.exists():
        data = json.loads(GIFTS_RAW.read_text())
        for row in data.get("products") or []:
            gifts_stats["raw"] += 1
            row = dict(row)
            row["kind"] = "gifts"
            sku = str(row.get("productCode") or row.get("id") or "")
            gcols = gift_cols_from_row(row)
            if not gcols:
                continue
            if sku.upper() in existing_skus or row.get("tagOnly"):
                gift_tags[sku.upper()] = gcols
                gifts_stats["tagged_existing"] += 1
                continue
            briq_id = f"gc-{sku.lower()}" if sku else ""
            if briq_id and briq_id in existing_ids:
                gift_tags[sku.upper()] = gcols
                gifts_stats["tagged_existing"] += 1
                continue
            sc = style_color_key(sku)
            if sc and sc in existing_style_colors:
                # Near-dup of an existing colourway — tag the style+color family
                # via sku key when exact match missing; skip new PDP.
                gifts_stats["skipped_style_color"] += 1
                continue
            gifts_stats["kept_new"] += 1
            remember(sku)
            rows.append(row)

    return (
        rows,
        mens_bag_stats,
        mens_rtw_stats,
        mens_shoes_stats,
        wallet_stats,
        fashion_stats,
        travel_stats,
        jewellery_stats,
        gifts_stats,
        gift_tags,
        mens_bag_tags,
        mens_rtw_tags,
        mens_shoes_tags,
    )


def main() -> None:
    (
        rows,
        mens_bag_stats,
        mens_rtw_stats,
        mens_shoes_stats,
        wallet_stats,
        fashion_stats,
        travel_stats,
        jewellery_stats,
        gifts_stats,
        gift_tags,
        mens_bag_tags,
        mens_rtw_tags,
        mens_shoes_tags,
    ) = load_rows()
    if not rows:
        raise SystemExit(
            "Missing Gucci raw catalogues — run scrape-gc-handbags.py, "
            "scrape-gc-mens-handbags.py, scrape-gc-womens-rtw.py, "
            "scrape-gc-mens-rtw.py, "
            "scrape-gc-womens-shoes.py, scrape-gc-mens-shoes.py, "
            "scrape-gc-womens-wallets.py, "
            "scrape-gc-womens-fashion-accessories.py, scrape-gc-womens-travel.py, "
            "scrape-gc-jewellery-watches.py and/or scrape-gc-gifts.py first"
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
            # Wallets/fashion/travel/jewellery never overwrite bags (already filtered).
            if row.get("kind") in {"rtw", "mens-rtw", "shoes", "mens-shoes"}:
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
    mens_tagged = apply_mens_bag_membership(products, mens_bag_tags)
    mens_rtw_tagged = apply_mens_rtw_membership(products, mens_rtw_tags)
    mens_shoes_tagged = apply_mens_shoe_membership(products, mens_shoes_tags)
    gift_tagged = apply_gift_membership(products, gift_tags)
    OUT_JSON.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n")
    OUT_TS.write_text(
        'import type { Product } from "@/data/products";\n'
        'import data from "./gc-catalog.json";\n\n'
        "/** Auto-generated — Gucci handbags + men's bags + women's/men's RTW + "
        "women's/men's shoes + wallets + fashion accessories + travel + jewellery + gifts. */\n"
        "export const gcCatalogProducts = data as unknown as Product[];\n"
    )
    CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2))
    print(f"Wrote {len(products)} products → {OUT_JSON}", flush=True)
    bags_n = sum(1 for p in products if p.get("category") == "bags")
    mens_bags_n = sum(
        1
        for p in products
        if "gc-mens-handbags" in (p.get("gcCollections") or [])
        or any(
            c in MENS_HANDBAG_LEAF_COLLECTIONS for c in (p.get("gcCollections") or [])
        )
    )
    rtw_n = sum(1 for p in products if p.get("category") == "luxury")
    mens_rtw_n = sum(
        1
        for p in products
        if "gc-men-rtw" in (p.get("gcCollections") or [])
        or any(c in MEN_RTW_LEAF_COLLECTIONS for c in (p.get("gcCollections") or []))
    )
    shoes_n = sum(1 for p in products if p.get("category") == "shoes")
    mens_shoes_n = sum(
        1
        for p in products
        if "gc-shoes-mens" in (p.get("gcCollections") or [])
        or "gc-men-shoes" in (p.get("gcCollections") or [])
        or any(c in MEN_SHOES_LEAF_COLLECTIONS for c in (p.get("gcCollections") or []))
    )
    acc_n = sum(1 for p in products if p.get("category") == "accessories")
    fashion_n = sum(
        1
        for p in products
        if "gc-women-fashion-accessories" in (p.get("gcCollections") or [])
        or any(
            c in FASHION_ACC_LEAF_COLLECTIONS and c != "gc-women-bag-charms-keychains"
            for c in (p.get("gcCollections") or [])
        )
    )
    travel_n = sum(
        1
        for p in products
        if "gc-women-travel" in (p.get("gcCollections") or [])
        or any(
            c in TRAVEL_LEAF_COLLECTIONS for c in (p.get("gcCollections") or [])
        )
    )
    jewellery_n = sum(
        1
        for p in products
        if "gc-jewellery-watches" in (p.get("gcCollections") or [])
        or any(
            c in JEWELLERY_LEAF_COLLECTIONS for c in (p.get("gcCollections") or [])
        )
    )
    gifts_n = sum(
        1
        for p in products
        if "gc-gifts" in (p.get("gcCollections") or [])
        or any(c in GIFTS_LEAF_COLLECTIONS for c in (p.get("gcCollections") or []))
    )
    print(
        f"  handbags: {bags_n}  mens-bags: {mens_bags_n}  rtw: {rtw_n}  "
        f"mens-rtw: {mens_rtw_n}  "
        f"shoes: {shoes_n}  mens-shoes: {mens_shoes_n}  accessories: {acc_n}  fashion: {fashion_n}  "
        f"travel: {travel_n}  jewellery: {jewellery_n}  gifts: {gifts_n}",
        flush=True,
    )
    if mens_bag_stats["raw"]:
        skipped = (
            mens_bag_stats["skipped_existing_sku"]
            + mens_bag_stats["skipped_existing_id"]
            + mens_bag_stats["skipped_style_color"]
        )
        print(
            f"  mens-bags raw={mens_bag_stats['raw']} "
            f"kept={mens_bag_stats['kept']} skipped={skipped} "
            f"tagged_existing={mens_bag_stats.get('tagged_existing', 0)} "
            f"(merged onto products={mens_tagged}) "
            f"(sku={mens_bag_stats['skipped_existing_sku']} "
            f"id={mens_bag_stats['skipped_existing_id']} "
            f"style_color={mens_bag_stats['skipped_style_color']})",
            flush=True,
        )
        for leaf in MENS_HANDBAG_LEAF_COLLECTIONS:
            n = sum(1 for p in products if leaf in (p.get("gcCollections") or []))
            print(f"    {leaf}: {n}", flush=True)
    if mens_rtw_stats["raw"]:
        skipped = (
            mens_rtw_stats["skipped_existing_sku"]
            + mens_rtw_stats["skipped_existing_id"]
        )
        print(
            f"  mens-rtw raw={mens_rtw_stats['raw']} "
            f"kept={mens_rtw_stats['kept']} skipped={skipped} "
            f"tagged_existing={mens_rtw_stats.get('tagged_existing', 0)} "
            f"(merged onto products={mens_rtw_tagged}) "
            f"(sku={mens_rtw_stats['skipped_existing_sku']} "
            f"id={mens_rtw_stats['skipped_existing_id']})",
            flush=True,
        )
        for leaf in MEN_RTW_LEAF_COLLECTIONS:
            n = sum(1 for p in products if leaf in (p.get("gcCollections") or []))
            print(f"    {leaf}: {n}", flush=True)
    if mens_shoes_stats["raw"]:
        skipped = (
            mens_shoes_stats["skipped_existing_sku"]
            + mens_shoes_stats["skipped_existing_id"]
        )
        print(
            f"  mens-shoes raw={mens_shoes_stats['raw']} "
            f"kept={mens_shoes_stats['kept']} skipped={skipped} "
            f"tagged_existing={mens_shoes_stats.get('tagged_existing', 0)} "
            f"(merged onto products={mens_shoes_tagged}) "
            f"(sku={mens_shoes_stats['skipped_existing_sku']} "
            f"id={mens_shoes_stats['skipped_existing_id']})",
            flush=True,
        )
        for leaf in MEN_SHOES_LEAF_COLLECTIONS:
            n = sum(1 for p in products if leaf in (p.get("gcCollections") or []))
            print(f"    {leaf}: {n}", flush=True)
    if wallet_stats["raw"]:
        print(
            f"  wallets raw={wallet_stats['raw']} "
            f"kept={wallet_stats['kept']} "
            f"skipped_bag_sku={wallet_stats['skipped_bag_sku']} "
            f"skipped_bag_style_color={wallet_stats['skipped_bag_style_color']}",
            flush=True,
        )
    if fashion_stats["raw"]:
        skipped = (
            fashion_stats["skipped_existing_sku"]
            + fashion_stats["skipped_existing_id"]
            + fashion_stats["skipped_style_color"]
        )
        print(
            f"  fashion-acc raw={fashion_stats['raw']} "
            f"kept={fashion_stats['kept']} "
            f"skipped_dups={skipped} "
            f"(sku={fashion_stats['skipped_existing_sku']} "
            f"id={fashion_stats['skipped_existing_id']} "
            f"style_color={fashion_stats['skipped_style_color']})",
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
    if jewellery_stats["raw"]:
        print(
            f"  jewellery raw={jewellery_stats['raw']} "
            f"kept={jewellery_stats['kept']} "
            f"skipped_sku={jewellery_stats['skipped_existing_sku']} "
            f"skipped_id={jewellery_stats['skipped_existing_id']} "
            f"skipped_style_color={jewellery_stats['skipped_style_color']}",
            flush=True,
        )
    if gifts_stats["raw"]:
        print(
            f"  gifts raw={gifts_stats['raw']} "
            f"new={gifts_stats['kept_new']} "
            f"tagged_existing={gifts_stats['tagged_existing']} "
            f"(merged onto products={gift_tagged}) "
            f"skipped_style_color={gifts_stats['skipped_style_color']}",
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
    for leaf in FASHION_ACC_LEAF_COLLECTIONS:
        if leaf == "gc-women-bag-charms-keychains":
            continue
        n = sum(1 for p in products if leaf in (p.get("gcCollections") or []))
        print(f"  {leaf}: {n}", flush=True)
    for leaf in TRAVEL_LEAF_COLLECTIONS:
        n = sum(1 for p in products if leaf in (p.get("gcCollections") or []))
        print(f"  {leaf}: {n}", flush=True)
    for leaf in JEWELLERY_LEAF_COLLECTIONS:
        n = sum(1 for p in products if leaf in (p.get("gcCollections") or []))
        print(f"  {leaf}: {n}", flush=True)
    for leaf in GIFTS_LEAF_COLLECTIONS:
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
    jw_parent_only = sum(
        1
        for p in products
        if "gc-jewellery-watches" in (p.get("gcCollections") or [])
        and not any(
            c in JEWELLERY_LEAF_COLLECTIONS for c in (p.get("gcCollections") or [])
        )
    )
    if jw_parent_only:
        print(f"  gc-jewellery-watches (no leaf): {jw_parent_only}", flush=True)


if __name__ == "__main__":
    main()