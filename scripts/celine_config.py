#!/usr/bin/env python3
"""Shared Celine pipeline configuration."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "src/data/ce"

CE_MEN_PARENT = ["celine", "ce-men"]
CE_WOMEN_PARENT = ["celine", "ce-women"]

CE_MEN_RTW_LEAVES = [
    {
        "id": "ce-men-rtw-all",
        "label": "View All",
        "labelKo": "전체",
        "url": "https://www.celine.com/en-gb/men/ready-to-wear/?nav=E001-VIEW-ALL",
        "collections": [*CE_MEN_PARENT, "ce-men-rtw-all"],
    },
    {
        "id": "ce-men-shirts",
        "label": "Shirts",
        "labelKo": "셔츠",
        "url": "https://www.celine.com/en-gb/men/ready-to-wear/shirts/",
        "collections": [*CE_MEN_PARENT, "ce-men-shirts"],
    },
    {
        "id": "ce-men-tshirts-tops",
        "label": "T-Shirts and Tops",
        "labelKo": "티셔츠 & 탑",
        "url": "https://www.celine.com/en-gb/men/ready-to-wear/t-shirts-and-sweatshirts/",
        "collections": [*CE_MEN_PARENT, "ce-men-tshirts-tops"],
    },
    {
        "id": "ce-men-sweatshirts",
        "label": "Sweatshirts",
        "labelKo": "스웨트셔츠",
        "url": "https://www.celine.com/en-gb/men/ready-to-wear/sweatshirts/",
        "collections": [*CE_MEN_PARENT, "ce-men-sweatshirts"],
    },
    {
        "id": "ce-men-knitwear",
        "label": "Knitwear",
        "labelKo": "니트웨어",
        "url": "https://www.celine.com/en-gb/men/ready-to-wear/knitwear/",
        "collections": [*CE_MEN_PARENT, "ce-men-knitwear"],
    },
    {
        "id": "ce-men-denim",
        "label": "Denim",
        "labelKo": "데님",
        "url": "https://www.celine.com/en-gb/men/ready-to-wear/denim/",
        "collections": [*CE_MEN_PARENT, "ce-men-denim"],
    },
    {
        "id": "ce-men-pants-shorts",
        "label": "Pants and Shorts",
        "labelKo": "팬츠 & 쇼츠",
        "url": "https://www.celine.com/en-gb/men/ready-to-wear/pants-and-shorts/",
        "collections": [*CE_MEN_PARENT, "ce-men-pants-shorts"],
    },
    {
        "id": "ce-men-tailoring",
        "label": "Tailoring",
        "labelKo": "테일러링",
        "url": "https://www.celine.com/en-gb/men/ready-to-wear/tailoring/",
        "collections": [*CE_MEN_PARENT, "ce-men-tailoring"],
    },
    {
        "id": "ce-men-coats",
        "label": "Coats",
        "labelKo": "코트",
        "url": "https://www.celine.com/en-gb/men/ready-to-wear/coats-and-blousons/",
        "collections": [*CE_MEN_PARENT, "ce-men-coats"],
    },
    {
        "id": "ce-men-jackets",
        "label": "Jackets",
        "labelKo": "재킷",
        "url": "https://www.celine.com/en-gb/men/ready-to-wear/jackets-and-trousers/",
        "collections": [*CE_MEN_PARENT, "ce-men-jackets"],
    },
    {
        "id": "ce-men-leather",
        "label": "Leather",
        "labelKo": "레더",
        "url": "https://www.celine.com/en-gb/men/ready-to-wear/leather/",
        "collections": [*CE_MEN_PARENT, "ce-men-leather"],
    },
]

CE_WOMEN_RTW_LEAVES = [
    {
        "id": "ce-women-rtw-all",
        "label": "View All",
        "labelKo": "전체",
        "url": "https://www.celine.com/en-gb/women/ready-to-wear/?nav=A001-VIEW-ALL",
        "collections": [*CE_WOMEN_PARENT, "ce-women-rtw-all"],
    },
    {
        "id": "ce-women-coats",
        "label": "Coats",
        "labelKo": "코트",
        "url": "https://www.celine.com/en-gb/women/ready-to-wear/coats/",
        "collections": [*CE_WOMEN_PARENT, "ce-women-coats"],
    },
    {
        "id": "ce-women-jackets",
        "label": "Jackets",
        "labelKo": "재킷",
        "url": "https://www.celine.com/en-gb/women/ready-to-wear/jackets/",
        "collections": [*CE_WOMEN_PARENT, "ce-women-jackets"],
    },
    {
        "id": "ce-women-knitwear",
        "label": "Knitwear",
        "labelKo": "니트웨어",
        "url": "https://www.celine.com/en-gb/women/ready-to-wear/knitwear/",
        "collections": [*CE_WOMEN_PARENT, "ce-women-knitwear"],
    },
    {
        "id": "ce-women-shirts-blouses",
        "label": "Shirts and Blouses",
        "labelKo": "셔츠 & 블라우스",
        "url": "https://www.celine.com/en-gb/women/ready-to-wear/shirts-and-tops/",
        "collections": [*CE_WOMEN_PARENT, "ce-women-shirts-blouses"],
    },
    {
        "id": "ce-women-tops-tshirts",
        "label": "Tops and T-Shirts",
        "labelKo": "탑 & 티셔츠",
        "url": "https://www.celine.com/en-gb/women/ready-to-wear/t-shirts-and-sweatshirts/",
        "collections": [*CE_WOMEN_PARENT, "ce-women-tops-tshirts"],
    },
    {
        "id": "ce-women-dresses",
        "label": "Dresses",
        "labelKo": "드레스",
        "url": "https://www.celine.com/en-gb/women/ready-to-wear/dresses-and-skirts/",
        "collections": [*CE_WOMEN_PARENT, "ce-women-dresses"],
    },
    {
        "id": "ce-women-skirts",
        "label": "Skirts",
        "labelKo": "스커트",
        "url": "https://www.celine.com/en-gb/women/ready-to-wear/skirts/",
        "collections": [*CE_WOMEN_PARENT, "ce-women-skirts"],
    },
    {
        "id": "ce-women-pants-shorts",
        "label": "Pants and Shorts",
        "labelKo": "팬츠 & 쇼츠",
        "url": "https://www.celine.com/en-gb/women/ready-to-wear/pants-and-shorts/",
        "collections": [*CE_WOMEN_PARENT, "ce-women-pants-shorts"],
    },
    {
        "id": "ce-women-denim",
        "label": "Denim",
        "labelKo": "데님",
        "url": "https://www.celine.com/en-gb/women/ready-to-wear/denim/",
        "collections": [*CE_WOMEN_PARENT, "ce-women-denim"],
    },
    {
        "id": "ce-women-leather",
        "label": "Leather",
        "labelKo": "레더",
        "url": "https://www.celine.com/en-gb/women/ready-to-wear/leather-and-shearling/",
        "collections": [*CE_WOMEN_PARENT, "ce-women-leather"],
    },
    {
        "id": "ce-women-swimwear",
        "label": "Swimwear",
        "labelKo": "스윔웨어",
        "url": "https://www.celine.com/en-gb/women/ready-to-wear/swimwear-and-lingerie/",
        "collections": [*CE_WOMEN_PARENT, "ce-women-swimwear"],
    },
]

CE_WOMEN_BAGS_PARENT = ["celine-bags", "ce-women-bags"]
CE_WOMEN_BAGS_LEAVES = [
    {
        "id": "ce-women-bags-all",
        "label": "View All",
        "labelKo": "전체",
        "url": "https://www.celine.com/en-gb/women/handbags/?nav=A003-VIEW-ALL",
        "collections": [*CE_WOMEN_BAGS_PARENT, "ce-women-bags-all"],
    },
    {
        "id": "ce-women-shoulder-bags",
        "label": "Shoulder Bags",
        "labelKo": "숄더백",
        "url": "https://www.celine.com/en-gb/women/handbags/shoulder-bags/",
        "collections": [*CE_WOMEN_BAGS_PARENT, "ce-women-shoulder-bags"],
    },
    {
        "id": "ce-women-cross-body-bags",
        "label": "Cross Body Bags",
        "labelKo": "크로스바디 백",
        "url": "https://www.celine.com/en-gb/women/handbags/cross-body-bags/",
        "collections": [*CE_WOMEN_BAGS_PARENT, "ce-women-cross-body-bags"],
    },
    {
        "id": "ce-women-tote-bags",
        "label": "Tote Bags",
        "labelKo": "토트백",
        "url": "https://www.celine.com/en-gb/women/handbags/tote-bags/",
        "collections": [*CE_WOMEN_BAGS_PARENT, "ce-women-tote-bags"],
    },
    {
        "id": "ce-women-bucket-bags",
        "label": "Bucket Bags",
        "labelKo": "버킷백",
        "url": "https://www.celine.com/en-gb/women/handbags/bucket-bags/",
        "collections": [*CE_WOMEN_BAGS_PARENT, "ce-women-bucket-bags"],
    },
    {
        "id": "ce-women-clutches",
        "label": "Clutches",
        "labelKo": "클러치",
        "url": "https://www.celine.com/en-gb/women/handbags/clutches/",
        "collections": [*CE_WOMEN_BAGS_PARENT, "ce-women-clutches"],
    },
    {
        "id": "ce-women-mini-bags",
        "label": "Mini Bags",
        "labelKo": "미니백",
        "url": "https://www.celine.com/en-gb/women/handbags/mini-bags/",
        "collections": [*CE_WOMEN_BAGS_PARENT, "ce-women-mini-bags"],
    },
    {
        "id": "ce-women-triomphe-canvas",
        "label": "Triomphe Canvas",
        "labelKo": "트리옹프 캔버스",
        "url": "https://www.celine.com/en-gb/women/handbags/triomphe-canvas/",
        "collections": [*CE_WOMEN_BAGS_PARENT, "ce-women-triomphe-canvas"],
    },
    {
        "id": "ce-women-luggage",
        "label": "Luggage",
        "labelKo": "러기지",
        "url": "https://www.celine.com/en-gb/women/handbags/luggage/",
        "collections": [*CE_WOMEN_BAGS_PARENT, "ce-women-luggage"],
    },
    {
        "id": "ce-women-16",
        "label": "16",
        "labelKo": "16",
        "url": "https://www.celine.com/en-gb/women/handbags/16/",
        "collections": [*CE_WOMEN_BAGS_PARENT, "ce-women-16"],
    },
    {
        "id": "ce-women-ava",
        "label": "AVA",
        "labelKo": "AVA",
        "url": "https://www.celine.com/en-gb/women/handbags/ava/",
        "collections": [*CE_WOMEN_BAGS_PARENT, "ce-women-ava"],
    },
    {
        "id": "ce-women-triomphe",
        "label": "Triomphe",
        "labelKo": "트리옹프",
        "url": "https://www.celine.com/en-gb/women/handbags/triomphe/",
        "collections": [*CE_WOMEN_BAGS_PARENT, "ce-women-triomphe"],
    },
]


CE_MEN_BAGS_PARENT = ["celine-bags", "ce-men-bags"]
CE_MEN_BAGS_LEAVES = [
    {
        "id": "ce-men-bags-all",
        "label": "View All",
        "labelKo": "전체",
        "url": "https://www.celine.com/en-gb/men/bags/?nav=E003-VIEW-ALL",
        "collections": [*CE_MEN_BAGS_PARENT, "ce-men-bags-all"],
    },
    {
        "id": "ce-men-cross-body-bags",
        "label": "Cross Body Bags",
        "labelKo": "크로스바디 백",
        "url": "https://www.celine.com/en-gb/men/bags/cross-body-bags/",
        "collections": [*CE_MEN_BAGS_PARENT, "ce-men-cross-body-bags"],
    },
    {
        "id": "ce-men-tote-bags",
        "label": "Tote Bags",
        "labelKo": "토트백",
        "url": "https://www.celine.com/en-gb/men/bags/tote-bags/",
        "collections": [*CE_MEN_BAGS_PARENT, "ce-men-tote-bags"],
    },
    {
        "id": "ce-men-backpacks",
        "label": "Backpacks",
        "labelKo": "백팩",
        "url": "https://www.celine.com/en-gb/men/bags/backpacks-1/",
        "collections": [*CE_MEN_BAGS_PARENT, "ce-men-backpacks"],
    },
    {
        "id": "ce-men-belt-bags",
        "label": "Belt Bags",
        "labelKo": "벨트백",
        "url": "https://www.celine.com/en-gb/men/bags/belt-bags-and-mini-bags/",
        "collections": [*CE_MEN_BAGS_PARENT, "ce-men-belt-bags"],
    },
    {
        "id": "ce-men-travel-bags",
        "label": "Business & Travel",
        "labelKo": "비즈니스/트래블",
        "url": "https://www.celine.com/en-gb/men/bags/business-and-travel-bags-2/",
        "collections": [*CE_MEN_BAGS_PARENT, "ce-men-travel-bags"],
    },
    {
        "id": "ce-men-luggage",
        "label": "Luggage",
        "labelKo": "러기지",
        "url": "https://www.celine.com/en-gb/men/bags/luggage/",
        "collections": [*CE_MEN_BAGS_PARENT, "ce-men-luggage"],
    },
    {
        "id": "ce-men-triomphe-canvas",
        "label": "Triomphe Canvas",
        "labelKo": "트리옹프 캔버스",
        "url": "https://www.celine.com/en-gb/men/bags/triomphe-canvas/",
        "collections": [*CE_MEN_BAGS_PARENT, "ce-men-triomphe-canvas"],
    },
]

CE_MEN_SHOES_PARENT = ["celine-shoes", "ce-men-shoes"]
CE_MEN_SHOES_LEAVES = [
    {
        "id": "ce-men-shoes-all",
        "label": "View All",
        "labelKo": "전체",
        "url": "https://www.celine.com/en-gb/men/shoes/?nav=E002-VIEW-ALL",
        "collections": [*CE_MEN_SHOES_PARENT, "ce-men-shoes-all"],
    },
    {
        "id": "ce-men-boots",
        "label": "Boots",
        "labelKo": "부츠",
        "url": "https://www.celine.com/en-gb/men/shoes/boots/",
        "collections": [*CE_MEN_SHOES_PARENT, "ce-men-boots"],
    },
    {
        "id": "ce-men-sneakers",
        "label": "Sneakers",
        "labelKo": "스니커즈",
        "url": "https://www.celine.com/en-gb/men/shoes/sneakers/",
        "collections": [*CE_MEN_SHOES_PARENT, "ce-men-sneakers"],
    },
    {
        "id": "ce-men-loafers",
        "label": "Loafers",
        "labelKo": "로퍼",
        "url": "https://www.celine.com/en-gb/men/shoes/loafers/",
        "collections": [*CE_MEN_SHOES_PARENT, "ce-men-loafers"],
    },
    {
        "id": "ce-men-sandals",
        "label": "Sandals",
        "labelKo": "샌들",
        "url": "https://www.celine.com/en-gb/men/shoes/sandals/",
        "collections": [*CE_MEN_SHOES_PARENT, "ce-men-sandals"],
    },
    {
        "id": "ce-men-lace-ups",
        "label": "Buckles & Lace-ups",
        "labelKo": "레이스업",
        "url": "https://www.celine.com/en-gb/men/shoes/buckles-and-lace-ups/",
        "collections": [*CE_MEN_SHOES_PARENT, "ce-men-lace-ups"],
    },
]

CE_WOMEN_SHOES_PARENT = ["celine-shoes", "ce-women-shoes"]
CE_WOMEN_SHOES_LEAVES = [
    {
        "id": "ce-women-shoes-all",
        "label": "View All",
        "labelKo": "전체",
        "url": "https://www.celine.com/en-gb/women/shoes/?nav=A002-VIEW-ALL",
        "collections": [*CE_WOMEN_SHOES_PARENT, "ce-women-shoes-all"],
    },
    {
        "id": "ce-women-boots",
        "label": "Boots",
        "labelKo": "부츠",
        "url": "https://www.celine.com/en-gb/women/shoes/boots-and-ankle-boots/",
        "collections": [*CE_WOMEN_SHOES_PARENT, "ce-women-boots"],
    },
    {
        "id": "ce-women-sandals",
        "label": "Sandals",
        "labelKo": "샌들",
        "url": "https://www.celine.com/en-gb/women/shoes/sandals/",
        "collections": [*CE_WOMEN_SHOES_PARENT, "ce-women-sandals"],
    },
    {
        "id": "ce-women-pumps",
        "label": "Pumps",
        "labelKo": "펌프스",
        "url": "https://www.celine.com/en-gb/women/shoes/pumps/",
        "collections": [*CE_WOMEN_SHOES_PARENT, "ce-women-pumps"],
    },
    {
        "id": "ce-women-ballet",
        "label": "Ballet",
        "labelKo": "발레",
        "url": "https://www.celine.com/en-gb/women/shoes/ballet/",
        "collections": [*CE_WOMEN_SHOES_PARENT, "ce-women-ballet"],
    },
    {
        "id": "ce-women-loafers",
        "label": "Loafers & Flats",
        "labelKo": "로퍼/플랫",
        "url": "https://www.celine.com/en-gb/women/shoes/loafers-and-flats/",
        "collections": [*CE_WOMEN_SHOES_PARENT, "ce-women-loafers"],
    },
    {
        "id": "ce-women-sneakers",
        "label": "Sneakers",
        "labelKo": "스니커즈",
        "url": "https://www.celine.com/en-gb/women/shoes/sneakers/",
        "collections": [*CE_WOMEN_SHOES_PARENT, "ce-women-sneakers"],
    },
]


CE_WOMEN_ACC_PARENT = ["celine-accessories", "ce-women-accessories"]
CE_WOMEN_ACC_LEAVES = [
    {
        "id": "ce-women-acc-all",
        "label": "View All",
        "labelKo": "전체",
        "url": "https://www.celine.com/en-gb/women/accessories/?nav=A007-VIEW-ALL",
        "collections": [*CE_WOMEN_ACC_PARENT, "ce-women-acc-all"],
    },
    {
        "id": "ce-women-scarves",
        "label": "Scarves & Shawls",
        "labelKo": "스카프/숄",
        "url": "https://www.celine.com/en-gb/women/accessories/scarves-and-shawls/",
        "collections": [*CE_WOMEN_ACC_PARENT, "ce-women-scarves"],
    },
    {
        "id": "ce-women-silk-scarves",
        "label": "Silk Scarves",
        "labelKo": "실크 스카프",
        "url": "https://www.celine.com/en-gb/women/accessories/silk-scarves/",
        "collections": [*CE_WOMEN_ACC_PARENT, "ce-women-silk-scarves"],
    },
    {
        "id": "ce-women-belts",
        "label": "Belts",
        "labelKo": "벨트",
        "url": "https://www.celine.com/en-gb/women/accessories/belts/",
        "collections": [*CE_WOMEN_ACC_PARENT, "ce-women-belts"],
    },
    {
        "id": "ce-women-hats",
        "label": "Hats & Gloves",
        "labelKo": "모자/장갑",
        "url": "https://www.celine.com/en-gb/women/accessories/hats-and-gloves/",
        "collections": [*CE_WOMEN_ACC_PARENT, "ce-women-hats"],
    },
    {
        "id": "ce-women-hair",
        "label": "Hair Accessories",
        "labelKo": "헤어 악세서리",
        "url": "https://www.celine.com/en-gb/women/accessories/hair-accessories/",
        "collections": [*CE_WOMEN_ACC_PARENT, "ce-women-hair"],
    },
]
CE_MEN_ACC_PARENT = ["celine-accessories", "ce-men-accessories"]
CE_MEN_ACC_LEAVES = [
    {
        "id": "ce-men-acc-all",
        "label": "View All",
        "labelKo": "전체",
        "url": "https://www.celine.com/en-gb/men/accessories/?nav=E007-VIEW-ALL",
        "collections": [*CE_MEN_ACC_PARENT, "ce-men-acc-all"],
    },
    {
        "id": "ce-men-scarves",
        "label": "Silks & Scarves",
        "labelKo": "실크/스카프",
        "url": "https://www.celine.com/en-gb/men/accessories/silks-and-scarves/",
        "collections": [*CE_MEN_ACC_PARENT, "ce-men-scarves"],
    },
    {
        "id": "ce-men-belts",
        "label": "Belts",
        "labelKo": "벨트",
        "url": "https://www.celine.com/en-gb/men/accessories/belts/",
        "collections": [*CE_MEN_ACC_PARENT, "ce-men-belts"],
    },
    {
        "id": "ce-men-hats",
        "label": "Hats",
        "labelKo": "모자",
        "url": "https://www.celine.com/en-gb/men/accessories/hats-and-soft-accessories/",
        "collections": [*CE_MEN_ACC_PARENT, "ce-men-hats"],
    },
]


CE_WOMEN_JEW_PARENT = ["celine-accessories", "ce-women-jewellery"]
CE_WOMEN_JEW_LEAVES = [
    {
        "id": "ce-women-jewellery-all",
        "label": "View All",
        "labelKo": "전체",
        "url": "https://www.celine.com/en-gb/women/jewellery/?nav=A005-VIEW-ALL",
        "collections": [*CE_WOMEN_JEW_PARENT, "ce-women-jewellery-all"],
    },
    {
        "id": "ce-women-earrings",
        "label": "Earrings",
        "labelKo": "귀걸이",
        "url": "https://www.celine.com/en-gb/women/jewellery/earrings/",
        "collections": [*CE_WOMEN_JEW_PARENT, "ce-women-earrings"],
    },
    {
        "id": "ce-women-rings",
        "label": "Rings",
        "labelKo": "반지",
        "url": "https://www.celine.com/en-gb/women/jewellery/rings/",
        "collections": [*CE_WOMEN_JEW_PARENT, "ce-women-rings"],
    },
    {
        "id": "ce-women-necklaces",
        "label": "Necklaces",
        "labelKo": "목걸이",
        "url": "https://www.celine.com/en-gb/women/jewellery/necklaces/",
        "collections": [*CE_WOMEN_JEW_PARENT, "ce-women-necklaces"],
    },
    {
        "id": "ce-women-bracelets",
        "label": "Bracelets",
        "labelKo": "팔찌",
        "url": "https://www.celine.com/en-gb/women/jewellery/bracelets/",
        "collections": [*CE_WOMEN_JEW_PARENT, "ce-women-bracelets"],
    },
    {
        "id": "ce-women-fine-jewellery",
        "label": "Fine Jewellery",
        "labelKo": "파인 주얼리",
        "url": "https://www.celine.com/en-gb/women/jewellery/fine-jewellery/",
        "collections": [*CE_WOMEN_JEW_PARENT, "ce-women-fine-jewellery"],
    },
    {
        "id": "ce-women-jew-triomphe",
        "label": "Triomphe",
        "labelKo": "트리옹프",
        "url": "https://www.celine.com/en-gb/women/jewellery/triomphe/",
        "collections": [*CE_WOMEN_JEW_PARENT, "ce-women-jew-triomphe"],
    },
]
CE_WOMEN_SUN_PARENT = ["celine-accessories", "ce-women-sunglasses"]
CE_WOMEN_SUN_LEAVES = [{
    "id": "ce-women-sunglasses-all",
    "label": "View All",
    "labelKo": "전체",
    "url": "https://www.celine.com/en-gb/women/sunglasses/?nav=A006-VIEW-ALL",
    "collections": [*CE_WOMEN_SUN_PARENT, "ce-women-sunglasses-all"],
}]
CE_WOMEN_SLG_PARENT = ["celine-accessories", "ce-women-slg"]
CE_WOMEN_SLG_LEAVES = [
    {
        "id": "ce-women-slg-all",
        "label": "View All",
        "labelKo": "전체",
        "url": "https://www.celine.com/en-gb/women/small-leather-goods/?nav=A004-VIEW-ALL",
        "collections": [*CE_WOMEN_SLG_PARENT, "ce-women-slg-all"],
    },
    {
        "id": "ce-women-card-holders",
        "label": "Card Holders",
        "labelKo": "카드홀더",
        "url": "https://www.celine.com/en-gb/women/small-leather-goods/coin-and-card-holders/",
        "collections": [*CE_WOMEN_SLG_PARENT, "ce-women-card-holders"],
    },
    {
        "id": "ce-women-wallets",
        "label": "Wallets",
        "labelKo": "지갑",
        "url": "https://www.celine.com/en-gb/women/small-leather-goods/wallets/",
        "collections": [*CE_WOMEN_SLG_PARENT, "ce-women-wallets"],
    },
    {
        "id": "ce-women-woc",
        "label": "Wallets on Chain",
        "labelKo": "체인 지갑",
        "url": "https://www.celine.com/en-gb/women/small-leather-goods/wallets-on-chain/",
        "collections": [*CE_WOMEN_SLG_PARENT, "ce-women-woc"],
    },
    {
        "id": "ce-women-pouches",
        "label": "Pouches",
        "labelKo": "파우치",
        "url": "https://www.celine.com/en-gb/women/small-leather-goods/pouches-and-tech-accessories/",
        "collections": [*CE_WOMEN_SLG_PARENT, "ce-women-pouches"],
    },
]


CE_MEN_JEW_PARENT = ["celine-accessories", "ce-men-jewellery"]
CE_MEN_JEW_LEAVES = [{"id": "ce-men-jewellery-all", "label": "View All", "labelKo": "전체",
    "url": "https://www.celine.com/en-gb/men/jewellery/?nav=E005-VIEW-ALL",
    "collections": [*CE_MEN_JEW_PARENT, "ce-men-jewellery-all"]}]
CE_MEN_SUN_PARENT = ["celine-accessories", "ce-men-sunglasses"]
CE_MEN_SUN_LEAVES = [{"id": "ce-men-sunglasses-all", "label": "View All", "labelKo": "전체",
    "url": "https://www.celine.com/en-gb/men/sunglasses/?nav=E006-VIEW-ALL",
    "collections": [*CE_MEN_SUN_PARENT, "ce-men-sunglasses-all"]}]
CE_MEN_SLG2_PARENT = ["celine-accessories", "ce-men-slg"]
CE_MEN_SLG_LEAVES = [{"id": "ce-men-slg-all", "label": "View All", "labelKo": "전체",
    "url": "https://www.celine.com/en-gb/men/small-leather-goods/?nav=E004-VIEW-ALL",
    "collections": [*CE_MEN_SLG2_PARENT, "ce-men-slg-all"]}]

CE_FAMILY_SCRAPERS = {
    "ce-men-rtw": {
        "out": "ce-men-rtw-catalog-raw.json",
        "hub": "https://www.celine.com/en-gb/men/ready-to-wear/?nav=E001-VIEW-ALL",
        "leaves": CE_MEN_RTW_LEAVES,
    },
    "ce-men-bags": {
        "out": "ce-men-bags-catalog-raw.json",
        "hub": "https://www.celine.com/en-gb/men/bags/?nav=E003-VIEW-ALL",
        "leaves": CE_MEN_BAGS_LEAVES,
    },
    "ce-men-shoes": {
        "out": "ce-men-shoes-catalog-raw.json",
        "hub": "https://www.celine.com/en-gb/men/shoes/?nav=E002-VIEW-ALL",
        "leaves": CE_MEN_SHOES_LEAVES,
    },
    "ce-women-rtw": {
        "out": "ce-women-rtw-catalog-raw.json",
        "hub": "https://www.celine.com/en-gb/women/ready-to-wear/?nav=A001-VIEW-ALL",
        "leaves": CE_WOMEN_RTW_LEAVES,
    },
    "ce-women-bags": {
        "out": "ce-women-bags-catalog-raw.json",
        "hub": "https://www.celine.com/en-gb/women/handbags/?nav=A003-VIEW-ALL",
        "leaves": CE_WOMEN_BAGS_LEAVES,
    },
    "ce-women-shoes": {
        "out": "ce-women-shoes-catalog-raw.json",
        "hub": "https://www.celine.com/en-gb/women/shoes/?nav=A002-VIEW-ALL",
        "leaves": CE_WOMEN_SHOES_LEAVES,
    },
    "ce-women-accessories": {
        "out": "ce-women-accessories-catalog-raw.json",
        "hub": "https://www.celine.com/en-gb/women/accessories/?nav=A007-VIEW-ALL",
        "leaves": CE_WOMEN_ACC_LEAVES,
    },
    "ce-men-accessories": {
        "out": "ce-men-accessories-catalog-raw.json",
        "hub": "https://www.celine.com/en-gb/men/accessories/?nav=E007-VIEW-ALL",
        "leaves": CE_MEN_ACC_LEAVES,
    },
    "ce-women-jewellery": {
        "out": "ce-women-jewellery-catalog-raw.json",
        "hub": "https://www.celine.com/en-gb/women/jewellery/?nav=A005-VIEW-ALL",
        "leaves": CE_WOMEN_JEW_LEAVES,
    },
    "ce-women-sunglasses": {
        "out": "ce-women-sunglasses-catalog-raw.json",
        "hub": "https://www.celine.com/en-gb/women/sunglasses/?nav=A006-VIEW-ALL",
        "leaves": CE_WOMEN_SUN_LEAVES,
    },
    "ce-women-slg": {
        "out": "ce-women-slg-catalog-raw.json",
        "hub": "https://www.celine.com/en-gb/women/small-leather-goods/?nav=A004-VIEW-ALL",
        "leaves": CE_WOMEN_SLG_LEAVES,
    },
    "ce-men-jewellery": {
        "out": "ce-men-jewellery-catalog-raw.json",
        "hub": "https://www.celine.com/en-gb/men/jewellery/?nav=E005-VIEW-ALL",
        "leaves": CE_MEN_JEW_LEAVES,
    },
    "ce-men-sunglasses": {
        "out": "ce-men-sunglasses-catalog-raw.json",
        "hub": "https://www.celine.com/en-gb/men/sunglasses/?nav=E006-VIEW-ALL",
        "leaves": CE_MEN_SUN_LEAVES,
    },
    "ce-men-slg": {
        "out": "ce-men-slg-catalog-raw.json",
        "hub": "https://www.celine.com/en-gb/men/small-leather-goods/?nav=E004-VIEW-ALL",
        "leaves": CE_MEN_SLG_LEAVES,
    },
}


def celine_raw_paths() -> list[Path]:
    return sorted(RAW_DIR.glob("ce-*-catalog-raw.json"))


def merge_product_rows(existing_products: list[dict], new_rows: list[dict]) -> list[dict]:
    from celine_common import is_blocked_pdp_title

    by_id = {p["id"]: p for p in existing_products if p.get("id")}
    for row in new_rows:
        prev = by_id.get(row["id"])
        if row.get("membershipOnly"):
            if not prev:
                continue
            prev = dict(prev)
            prev["collections"] = list(
                dict.fromkeys((prev.get("collections") or []) + (row.get("collections") or []))
            )
            # If product was only under rtw-all, promote subcategory when leaf is specific.
            leaf = row.get("leafId") or ""
            if leaf and leaf not in {"ce-women-rtw-all", "ce-men-rtw-all"} and not (
                prev.get("leafId") and prev.get("leafId") not in {"ce-women-rtw-all", "ce-men-rtw-all"}
            ):
                # keep existing leafId if already a specific leaf; else adopt
                if (prev.get("leafId") or "") in {"", "ce-women-rtw-all", "ce-men-rtw-all"}:
                    prev["leafId"] = leaf
            by_id[row["id"]] = prev
            continue
        new_blocked = is_blocked_pdp_title(row.get("title")) or bool(row.get("scrapeBlocked"))
        prev_good = bool(prev) and not is_blocked_pdp_title((prev or {}).get("title"))
        if new_blocked and prev_good:
            # Never let a WAF/blocked scrape overwrite a known-good PDP.
            prev = dict(prev)
            prev["collections"] = list(
                dict.fromkeys((prev.get("collections") or []) + (row.get("collections") or []))
            )
            by_id[row["id"]] = prev
            continue
        if prev:
            row["collections"] = list(
                dict.fromkeys((prev.get("collections") or []) + (row.get("collections") or []))
            )
            if len(prev.get("images") or []) > len(row.get("images") or []):
                row["images"] = prev.get("images") or row["images"]
            if len(prev.get("sizes") or []) > len(row.get("sizes") or []):
                row["sizes"] = prev.get("sizes") or row["sizes"]
            if prev.get("sizeGuide", {}).get("rows") and not row.get("sizeGuide", {}).get("rows"):
                row["sizeGuide"] = prev.get("sizeGuide") or row.get("sizeGuide") or {}
            # Prefer previous non-blocked title if new title is still bad.
            if is_blocked_pdp_title(row.get("title")) and prev.get("title"):
                row["title"] = prev["title"]
            if not row.get("title") and prev.get("title"):
                row["title"] = prev["title"]
            if row.get("availability") is None and prev.get("availability") is not None:
                row["availability"] = prev.get("availability")
        by_id[row["id"]] = row
    return list(by_id.values())
