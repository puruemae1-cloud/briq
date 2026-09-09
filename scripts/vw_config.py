#!/usr/bin/env python3
"""Shared Vivienne Westwood pipeline configuration."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "src/data/vw"

VW_WOMEN_PARENT = ["vivienne-westwood", "vw-women"]
VW_MEN_PARENT = ["vivienne-westwood", "vw-men"]
VW_WOMEN_BAGS_PARENT = ["vivienne-westwood-bags", "vw-bags", "vw-women-bags"]
VW_MEN_BAGS_PARENT = ["vivienne-westwood-bags", "vw-bags", "vw-men-bags"]
VW_WOMEN_SHOES_PARENT = ["vivienne-westwood-shoes", "vw-shoes", "vw-women-shoes"]
VW_MEN_SHOES_PARENT = ["vivienne-westwood-shoes", "vw-shoes", "vw-men-shoes"]
VW_WOMEN_JEWELLERY_PARENT = ["vivienne-westwood-accessories", "vw-accessories", "vw-women-jewellery"]
VW_WOMEN_ACCESSORIES_PARENT = ["vivienne-westwood-accessories", "vw-accessories", "vw-women-accessories"]
VW_MEN_ACCESSORIES_PARENT = ["vivienne-westwood-accessories", "vw-accessories", "vw-men-accessories"]
VW_WOMEN_WATCHES_PARENT = ["vivienne-westwood-watches", "vw-watches", "vw-women-watches"]

VW_WOMEN_RTW_LEAVES = [
    {
        "id": "vw-women-rtw-all",
        "label": "View All",
        "labelKo": "전체",
        "url": "https://www.viviennewestwood.com/en-gb/women/clothing/",
        "collections": [*VW_WOMEN_PARENT, "vw-women-rtw", "vw-women-rtw-all"],
    },
]

VW_WOMEN_BAGS_LEAVES = [
    {
        "id": "vw-women-bags-all",
        "label": "View All",
        "labelKo": "전체",
        "url": "https://www.viviennewestwood.com/en-gb/women/bags/",
        "collections": [*VW_WOMEN_BAGS_PARENT, "vw-women-bags-all"],
    },
]

VW_WOMEN_SHOES_LEAVES = [
    {
        "id": "vw-women-shoes-all",
        "label": "View All",
        "labelKo": "전체",
        "url": "https://www.viviennewestwood.com/en-gb/women/shoes/",
        "collections": [*VW_WOMEN_SHOES_PARENT, "vw-women-shoes-all"],
    },
]

VW_WOMEN_JEWELLERY_LEAVES = [
    {
        "id": "vw-women-jewellery-all",
        "label": "View All",
        "labelKo": "전체",
        "url": "https://www.viviennewestwood.com/en-gb/women/jewellery/",
        "collections": [*VW_WOMEN_JEWELLERY_PARENT, "vw-women-jewellery-all"],
    },
]

VW_WOMEN_ACCESSORIES_LEAVES = [
    {
        "id": "vw-women-acc-all",
        "label": "View All",
        "labelKo": "전체",
        "url": "https://www.viviennewestwood.com/en-gb/women/accessories/",
        "collections": [*VW_WOMEN_ACCESSORIES_PARENT, "vw-women-acc-all"],
    },
]

VW_WOMEN_WATCHES_LEAVES = [
    {
        "id": "vw-women-watches-all",
        "label": "View All",
        "labelKo": "전체",
        "url": "https://www.viviennewestwood.com/en-gb/watches/",
        "collections": [*VW_WOMEN_WATCHES_PARENT, "vw-women-watches-all"],
    },
]

VW_MEN_RTW_LEAVES = [
    {
        "id": "vw-men-rtw-all",
        "label": "View All",
        "labelKo": "전체",
        "url": "https://www.viviennewestwood.com/en-gb/men/clothing/",
        "collections": [*VW_MEN_PARENT, "vw-men-rtw", "vw-men-rtw-all"],
    },
]

VW_MEN_BAGS_LEAVES = [
    {
        "id": "vw-men-bags-all",
        "label": "View All",
        "labelKo": "전체",
        "url": "https://www.viviennewestwood.com/en-gb/men/bags/",
        "collections": [*VW_MEN_BAGS_PARENT, "vw-men-bags-all"],
    },
]

VW_MEN_SHOES_LEAVES = [
    {
        "id": "vw-men-shoes-all",
        "label": "View All",
        "labelKo": "전체",
        "url": "https://www.viviennewestwood.com/en-gb/men/shoes/",
        "collections": [*VW_MEN_SHOES_PARENT, "vw-men-shoes-all"],
    },
]

VW_MEN_ACCESSORIES_LEAVES = [
    {
        "id": "vw-men-acc-all",
        "label": "View All",
        "labelKo": "전체",
        "url": "https://www.viviennewestwood.com/en-gb/men/accessories/",
        "collections": [*VW_MEN_ACCESSORIES_PARENT, "vw-men-acc-all"],
    },
]


VW_WORLDS_END_PARENT = ["vivienne-westwood", "vw-worlds-end"]
VW_WORLDS_END_LEAVES = [
    {"id": "vw-worlds-end-all", "label": "Worlds End", "labelKo": "Worlds End",
     "url": "https://www.viviennewestwood.com/en-gb/worlds-end/",
     "collections": [*VW_WORLDS_END_PARENT, "vw-worlds-end-all"]},
]

VW_FAMILY_SCRAPERS = {
    "vw-women-rtw": {
        "out": "vw-women-rtw-catalog-raw.json",
        "hub": "https://www.viviennewestwood.com/en-gb/women/clothing/",
        "leaves": VW_WOMEN_RTW_LEAVES + [
        {"id": "vw-women-dresses", "label": "Dresses", "labelKo": "드레스",
         "url": "https://www.viviennewestwood.com/en-gb/women/clothing/dresses/",
         "collections": [*VW_WOMEN_PARENT, "vw-women-rtw", "vw-women-rtw-all"]},
        {"id": "vw-women-tops", "label": "Tops", "labelKo": "탑",
         "url": "https://www.viviennewestwood.com/en-gb/women/clothing/tops-and-shirts/",
         "collections": [*VW_WOMEN_PARENT, "vw-women-rtw", "vw-women-rtw-all"]},
        {"id": "vw-women-knitwear", "label": "Knitwear", "labelKo": "니트웨어",
         "url": "https://www.viviennewestwood.com/en-gb/women/clothing/knitwear/",
         "collections": [*VW_WOMEN_PARENT, "vw-women-rtw", "vw-women-rtw-all"]},
        {"id": "vw-women-coats", "label": "Coats & Jackets", "labelKo": "코트/재킷",
         "url": "https://www.viviennewestwood.com/en-gb/women/clothing/coats-and-jackets/",
         "collections": [*VW_WOMEN_PARENT, "vw-women-rtw", "vw-women-rtw-all"]},
        {"id": "vw-women-skirts", "label": "Skirts", "labelKo": "스커트",
         "url": "https://www.viviennewestwood.com/en-gb/women/clothing/skirts/",
         "collections": [*VW_WOMEN_PARENT, "vw-women-rtw", "vw-women-rtw-all"]},
        {"id": "vw-women-trousers", "label": "Trousers", "labelKo": "팬츠",
         "url": "https://www.viviennewestwood.com/en-gb/women/clothing/trousers-and-shorts/",
         "collections": [*VW_WOMEN_PARENT, "vw-women-rtw", "vw-women-rtw-all"]},
        {"id": "vw-women-sweats", "label": "Sweatshirts & T-shirts", "labelKo": "스웻/티셔츠",
         "url": "https://www.viviennewestwood.com/en-gb/women/clothing/sweatshirts-and-t-shirts/",
         "collections": [*VW_WOMEN_PARENT, "vw-women-rtw", "vw-women-rtw-all"]},
        {"id": "vw-women-corsets", "label": "Corsets", "labelKo": "코르셋",
         "url": "https://www.viviennewestwood.com/en-gb/women/clothing/corsets/",
         "collections": [*VW_WOMEN_PARENT, "vw-women-rtw", "vw-women-rtw-all"]},
    ],
    },
    "vw-women-bags": {
        "out": "vw-women-bags-catalog-raw.json",
        "hub": "https://www.viviennewestwood.com/en-gb/women/bags/",
        "leaves": VW_WOMEN_BAGS_LEAVES + [
        {"id": "vw-women-handbags", "label": "Handbags", "labelKo": "핸드백",
         "url": "https://www.viviennewestwood.com/en-gb/women/bags/handbags/",
         "collections": [*VW_WOMEN_BAGS_PARENT, "vw-women-bags-all"]},
        {"id": "vw-women-crossbody", "label": "Crossbody", "labelKo": "크로스바디",
         "url": "https://www.viviennewestwood.com/en-gb/women/bags/crossbody-bags/",
         "collections": [*VW_WOMEN_BAGS_PARENT, "vw-women-bags-all"]},
        {"id": "vw-women-clutches", "label": "Clutches", "labelKo": "클러치",
         "url": "https://www.viviennewestwood.com/en-gb/women/bags/clutches/",
         "collections": [*VW_WOMEN_BAGS_PARENT, "vw-women-bags-all"]},
        {"id": "vw-women-totes", "label": "Tote Bags", "labelKo": "토트백",
         "url": "https://www.viviennewestwood.com/en-gb/women/bags/totebags/",
         "collections": [*VW_WOMEN_BAGS_PARENT, "vw-women-bags-all"]},
        {"id": "vw-women-backpacks", "label": "Backpacks", "labelKo": "백팩",
         "url": "https://www.viviennewestwood.com/en-gb/women/bags/backpacks/",
         "collections": [*VW_WOMEN_BAGS_PARENT, "vw-women-bags-all"]},
    ],
    },
    "vw-women-shoes": {
        "out": "vw-women-shoes-catalog-raw.json",
        "hub": "https://www.viviennewestwood.com/en-gb/women/shoes/",
        "leaves": VW_WOMEN_SHOES_LEAVES + [
        {"id": "vw-women-boots", "label": "Boots", "labelKo": "부츠",
         "url": "https://www.viviennewestwood.com/en-gb/women/shoes/boots/",
         "collections": [*VW_WOMEN_SHOES_PARENT, "vw-women-shoes-all"]},
        {"id": "vw-women-flats", "label": "Flats", "labelKo": "플랫",
         "url": "https://www.viviennewestwood.com/en-gb/women/shoes/flats/",
         "collections": [*VW_WOMEN_SHOES_PARENT, "vw-women-shoes-all"]},
        {"id": "vw-women-pumps", "label": "Pumps", "labelKo": "펌프스",
         "url": "https://www.viviennewestwood.com/en-gb/women/shoes/pumps/",
         "collections": [*VW_WOMEN_SHOES_PARENT, "vw-women-shoes-all"]},
        {"id": "vw-women-sandals", "label": "Sandals", "labelKo": "샌들",
         "url": "https://www.viviennewestwood.com/en-gb/women/shoes/sandals/",
         "collections": [*VW_WOMEN_SHOES_PARENT, "vw-women-shoes-all"]},
        {"id": "vw-women-trainers", "label": "Trainers", "labelKo": "스니커즈",
         "url": "https://www.viviennewestwood.com/en-gb/women/shoes/trainers/",
         "collections": [*VW_WOMEN_SHOES_PARENT, "vw-women-shoes-all"]},
        {"id": "vw-women-platforms", "label": "Platforms", "labelKo": "플랫폼",
         "url": "https://www.viviennewestwood.com/en-gb/women/shoes/platforms/",
         "collections": [*VW_WOMEN_SHOES_PARENT, "vw-women-shoes-all"]},
    ],
    },
    "vw-women-jewellery": {
        "out": "vw-women-jewellery-catalog-raw.json",
        "hub": "https://www.viviennewestwood.com/en-gb/women/jewellery/",
        "leaves": VW_WOMEN_JEWELLERY_LEAVES + [
        {"id": "vw-women-earrings", "label": "Earrings", "labelKo": "귀걸이",
         "url": "https://www.viviennewestwood.com/en-gb/women/jewellery/earrings/",
         "collections": [*VW_WOMEN_JEWELLERY_PARENT, "vw-women-jewellery-all"]},
        {"id": "vw-women-necklaces", "label": "Necklaces", "labelKo": "목걸이",
         "url": "https://www.viviennewestwood.com/en-gb/women/jewellery/necklaces/",
         "collections": [*VW_WOMEN_JEWELLERY_PARENT, "vw-women-jewellery-all"]},
        {"id": "vw-women-rings", "label": "Rings", "labelKo": "반지",
         "url": "https://www.viviennewestwood.com/en-gb/women/jewellery/rings/",
         "collections": [*VW_WOMEN_JEWELLERY_PARENT, "vw-women-jewellery-all"]},
        {"id": "vw-women-bracelets", "label": "Bracelets", "labelKo": "팔찌",
         "url": "https://www.viviennewestwood.com/en-gb/women/jewellery/bracelets/",
         "collections": [*VW_WOMEN_JEWELLERY_PARENT, "vw-women-jewellery-all"]},
        {"id": "vw-women-other-jewellery", "label": "Other Jewellery", "labelKo": "기타 주얼리",
         "url": "https://www.viviennewestwood.com/en-gb/women/jewellery/other-jewellery/",
         "collections": [*VW_WOMEN_JEWELLERY_PARENT, "vw-women-jewellery-all"]},
    ],
    },
    "vw-women-accessories": {
        "out": "vw-women-accessories-catalog-raw.json",
        "hub": "https://www.viviennewestwood.com/en-gb/women/accessories/",
        "leaves": VW_WOMEN_ACCESSORIES_LEAVES + [
        {"id": "vw-women-belts", "label": "Belts", "labelKo": "벨트",
         "url": "https://www.viviennewestwood.com/en-gb/women/accessories/belts-and-harnesses/",
         "collections": [*VW_WOMEN_ACCESSORIES_PARENT, "vw-women-acc-all"]},
        {"id": "vw-women-scarves", "label": "Scarves", "labelKo": "스카프",
         "url": "https://www.viviennewestwood.com/en-gb/women/accessories/scarves-and-ponchos/",
         "collections": [*VW_WOMEN_ACCESSORIES_PARENT, "vw-women-acc-all"]},
        {"id": "vw-women-sunglasses", "label": "Sunglasses", "labelKo": "선글라스",
         "url": "https://www.viviennewestwood.com/en-gb/women/accessories/sunglasses/",
         "collections": [*VW_WOMEN_ACCESSORIES_PARENT, "vw-women-acc-all"]},
        {"id": "vw-women-wallets", "label": "Wallets", "labelKo": "지갑",
         "url": "https://www.viviennewestwood.com/en-gb/women/accessories/wallets-and-purses/",
         "collections": [*VW_WOMEN_ACCESSORIES_PARENT, "vw-women-acc-all"]},
        {"id": "vw-women-socks", "label": "Socks & Tights", "labelKo": "양말/타이즈",
         "url": "https://www.viviennewestwood.com/en-gb/women/accessories/socks-and-tights/",
         "collections": [*VW_WOMEN_ACCESSORIES_PARENT, "vw-women-acc-all"]},
    ],
    },
    "vw-women-watches": {
        "out": "vw-women-watches-catalog-raw.json",
        "hub": "https://www.viviennewestwood.com/en-gb/watches/",
        "leaves": VW_WOMEN_WATCHES_LEAVES,
    },
    "vw-men-rtw": {
        "out": "vw-men-rtw-catalog-raw.json",
        "hub": "https://www.viviennewestwood.com/en-gb/men/clothing/",
        "leaves": VW_MEN_RTW_LEAVES + [
        {"id": "vw-men-shirts", "label": "Shirts", "labelKo": "셔츠",
         "url": "https://www.viviennewestwood.com/en-gb/men/clothing/shirts/",
         "collections": [*VW_MEN_PARENT, "vw-men-rtw", "vw-men-rtw-all"]},
        {"id": "vw-men-knitwear", "label": "Knitwear", "labelKo": "니트웨어",
         "url": "https://www.viviennewestwood.com/en-gb/men/clothing/knitwear-and-sweatshirts/",
         "collections": [*VW_MEN_PARENT, "vw-men-rtw", "vw-men-rtw-all"]},
        {"id": "vw-men-trousers", "label": "Trousers", "labelKo": "팬츠",
         "url": "https://www.viviennewestwood.com/en-gb/men/clothing/trousers-and-shorts/",
         "collections": [*VW_MEN_PARENT, "vw-men-rtw", "vw-men-rtw-all"]},
        {"id": "vw-men-coats", "label": "Coats & Jackets", "labelKo": "코트/재킷",
         "url": "https://www.viviennewestwood.com/en-gb/men/clothing/coats-and-jackets/",
         "collections": [*VW_MEN_PARENT, "vw-men-rtw", "vw-men-rtw-all"]},
        {"id": "vw-men-tees", "label": "T-shirts & Polos", "labelKo": "티셔츠/폴로",
         "url": "https://www.viviennewestwood.com/en-gb/men/clothing/t-shirts-and-polos/",
         "collections": [*VW_MEN_PARENT, "vw-men-rtw", "vw-men-rtw-all"]},
    ],
    },
    "vw-men-bags": {
        "out": "vw-men-bags-catalog-raw.json",
        "hub": "https://www.viviennewestwood.com/en-gb/men/bags/",
        "leaves": VW_MEN_BAGS_LEAVES + [
        {"id": "vw-men-crossbody", "label": "Crossbody", "labelKo": "크로스바디",
         "url": "https://www.viviennewestwood.com/en-gb/men/bags/crossbody-bags/",
         "collections": [*VW_MEN_BAGS_PARENT, "vw-men-bags-all"]},
        {"id": "vw-men-totes", "label": "Tote Bags", "labelKo": "토트백",
         "url": "https://www.viviennewestwood.com/en-gb/men/bags/tote-bags/",
         "collections": [*VW_MEN_BAGS_PARENT, "vw-men-bags-all"]},
    ],
    },
    "vw-men-shoes": {
        "out": "vw-men-shoes-catalog-raw.json",
        "hub": "https://www.viviennewestwood.com/en-gb/men/shoes/",
        "leaves": VW_MEN_SHOES_LEAVES + [
        {"id": "vw-men-boots", "label": "Boots", "labelKo": "부츠",
         "url": "https://www.viviennewestwood.com/en-gb/men/shoes/boots/",
         "collections": [*VW_MEN_SHOES_PARENT, "vw-men-shoes-all"]},
        {"id": "vw-men-trainers", "label": "Trainers", "labelKo": "스니커즈",
         "url": "https://www.viviennewestwood.com/en-gb/men/shoes/trainers/",
         "collections": [*VW_MEN_SHOES_PARENT, "vw-men-shoes-all"]},
        {"id": "vw-men-lace-ups", "label": "Lace-up Shoes", "labelKo": "레이스업",
         "url": "https://www.viviennewestwood.com/en-gb/men/shoes/lace-up-shoes/",
         "collections": [*VW_MEN_SHOES_PARENT, "vw-men-shoes-all"]},
    ],
    },
    "vw-men-jewellery": {
        "out": "vw-men-jewellery-catalog-raw.json",
        "hub": "https://www.viviennewestwood.com/en-gb/men/jewellery/",
        "leaves": [
        {"id": "vw-men-jewellery-all", "label": "View All", "labelKo": "전체",
         "url": "https://www.viviennewestwood.com/en-gb/men/jewellery/",
         "collections": ["vivienne-westwood-accessories", "vw-accessories", "vw-men-jewellery", "vw-men-jewellery-all"]},
        {"id": "vw-men-earrings", "label": "Earrings", "labelKo": "귀걸이",
         "url": "https://www.viviennewestwood.com/en-gb/men/jewellery/earrings/",
         "collections": ["vivienne-westwood-accessories", "vw-accessories", "vw-men-jewellery", "vw-men-jewellery-all"]},
        {"id": "vw-men-necklaces", "label": "Necklaces", "labelKo": "목걸이",
         "url": "https://www.viviennewestwood.com/en-gb/men/jewellery/necklaces/",
         "collections": ["vivienne-westwood-accessories", "vw-accessories", "vw-men-jewellery", "vw-men-jewellery-all"]},
        {"id": "vw-men-rings", "label": "Rings", "labelKo": "반지",
         "url": "https://www.viviennewestwood.com/en-gb/men/jewellery/rings/",
         "collections": ["vivienne-westwood-accessories", "vw-accessories", "vw-men-jewellery", "vw-men-jewellery-all"]},
        {"id": "vw-men-bracelets", "label": "Bracelets", "labelKo": "팔찌",
         "url": "https://www.viviennewestwood.com/en-gb/men/jewellery/bracelets/",
         "collections": ["vivienne-westwood-accessories", "vw-accessories", "vw-men-jewellery", "vw-men-jewellery-all"]},
    ],
    },
    "vw-men-accessories": {
        "out": "vw-men-accessories-catalog-raw.json",
        "hub": "https://www.viviennewestwood.com/en-gb/men/accessories/",
        "leaves": VW_MEN_ACCESSORIES_LEAVES + [
        {"id": "vw-men-belts", "label": "Belts", "labelKo": "벨트",
         "url": "https://www.viviennewestwood.com/en-gb/men/accessories/belts-and-harnesses/",
         "collections": [*VW_MEN_ACCESSORIES_PARENT, "vw-men-acc-all"]},
        {"id": "vw-men-scarves", "label": "Scarves", "labelKo": "스카프",
         "url": "https://www.viviennewestwood.com/en-gb/men/accessories/scarves-and-ponchos/",
         "collections": [*VW_MEN_ACCESSORIES_PARENT, "vw-men-acc-all"]},
        {"id": "vw-men-sunglasses", "label": "Sunglasses", "labelKo": "선글라스",
         "url": "https://www.viviennewestwood.com/en-gb/men/accessories/sunglasses/",
         "collections": [*VW_MEN_ACCESSORIES_PARENT, "vw-men-acc-all"]},
        {"id": "vw-men-wallets", "label": "Wallets", "labelKo": "지갑",
         "url": "https://www.viviennewestwood.com/en-gb/men/accessories/wallets/",
         "collections": [*VW_MEN_ACCESSORIES_PARENT, "vw-men-acc-all"]},
    ],
    },
    "vw-worlds-end": {
        "out": "vw-worlds-end-catalog-raw.json",
        "hub": "https://www.viviennewestwood.com/en-gb/worlds-end/",
        "leaves": VW_WORLDS_END_LEAVES,
    },
}


# VW_COLOR_LEAVES_ADDED
VW_EXTRA_FILTER_LEAVES = {
  "vw-women-jewellery": [
    {"id":"vw-women-jew-gold","label":"Gold","labelKo":"골드","url":"https://www.viviennewestwood.com/en-gb/women/jewellery/gold/","collections":[*VW_WOMEN_JEWELLERY_PARENT,"vw-women-jewellery-all"]},
    {"id":"vw-women-jew-silver","label":"Silver","labelKo":"실버","url":"https://www.viviennewestwood.com/en-gb/women/jewellery/silver/","collections":[*VW_WOMEN_JEWELLERY_PARENT,"vw-women-jewellery-all"]},
    {"id":"vw-women-jew-pearl","label":"Pearl","labelKo":"펄","url":"https://www.viviennewestwood.com/en-gb/women/jewellery/pearl/","collections":[*VW_WOMEN_JEWELLERY_PARENT,"vw-women-jewellery-all"]},
  ],
  "vw-women-shoes": [
    {"id":"vw-women-shoes-black","label":"Black","labelKo":"블랙","url":"https://www.viviennewestwood.com/en-gb/women/shoes/black/","collections":[*VW_WOMEN_SHOES_PARENT,"vw-women-shoes-all"]},
    {"id":"vw-women-shoes-white","label":"White","labelKo":"화이트","url":"https://www.viviennewestwood.com/en-gb/women/shoes/white/","collections":[*VW_WOMEN_SHOES_PARENT,"vw-women-shoes-all"]},
  ],
  "vw-women-accessories": [
    {"id":"vw-women-acc-black","label":"Black","labelKo":"블랙","url":"https://www.viviennewestwood.com/en-gb/women/accessories/black/","collections":[*VW_WOMEN_ACCESSORIES_PARENT,"vw-women-acc-all"]},
    {"id":"vw-women-acc-gold","label":"Gold","labelKo":"골드","url":"https://www.viviennewestwood.com/en-gb/women/accessories/gold/","collections":[*VW_WOMEN_ACCESSORIES_PARENT,"vw-women-acc-all"]},
  ],
  "vw-men-shoes": [
    {"id":"vw-men-shoes-black","label":"Black","labelKo":"블랙","url":"https://www.viviennewestwood.com/en-gb/men/shoes/black/","collections":[*VW_MEN_SHOES_PARENT,"vw-men-shoes-all"]},
  ],
}
for _fam, _extra in VW_EXTRA_FILTER_LEAVES.items():
  if _fam in VW_FAMILY_SCRAPERS:
    VW_FAMILY_SCRAPERS[_fam]["leaves"] = list(VW_FAMILY_SCRAPERS[_fam]["leaves"]) + _extra

def vw_raw_paths() -> list[Path]:
    return sorted(RAW_DIR.glob("vw-*-catalog-raw.json"))


def merge_product_rows(existing_products: list[dict], new_rows: list[dict]) -> list[dict]:
    by_id = {p["id"]: p for p in existing_products if p.get("id")}
    for row in new_rows:
        prev = by_id.get(row["id"])
        if prev:
            row["collections"] = list(
                dict.fromkeys((prev.get("collections") or []) + (row.get("collections") or []))
            )
            if len(prev.get("images") or []) > len(row.get("images") or []):
                row["images"] = prev.get("images") or row["images"]
            if len(prev.get("sizes") or []) > len(row.get("sizes") or []):
                row["sizes"] = prev.get("sizes") or row["sizes"]
        by_id[row["id"]] = row
    return list(by_id.values())
