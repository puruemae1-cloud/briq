#!/usr/bin/env python3
"""Mulberry GB leaf catalogue config for Briq nav + weekly sync."""
from __future__ import annotations

BASE = "https://www.mulberry.com"

# Each leaf: id, labelKo, url, category (bags|accessories), collections (nav ids)
# Parents are also listed so /shop?sub=mb-women-bags expands to children.
LEAVES: list[dict] = [
    # —— Bags · Women ——
    {
        "id": "mb-women-bags-all",
        "labelKo": "전체",
        "url": f"{BASE}/gb/shop/women/bags",
        "category": "bags",
        "collections": ["mulberry-bags", "mb-women-bags", "mb-women-bags-all"],
    },
    {
        "id": "mb-women-crossbody",
        "labelKo": "크로스바디",
        "url": f"{BASE}/gb/shop/women/bags/crossbody-bags",
        "category": "bags",
        "collections": ["mulberry-bags", "mb-women-bags", "mb-women-crossbody"],
    },
    {
        "id": "mb-women-shoulder",
        "labelKo": "숄더백",
        "url": f"{BASE}/gb/shop/women/bags/shoulder-bags",
        "category": "bags",
        "collections": ["mulberry-bags", "mb-women-bags", "mb-women-shoulder"],
    },
    {
        "id": "mb-women-top-handle",
        "labelKo": "탑 핸들",
        "url": f"{BASE}/gb/shop/women/bags/top-handle-bags",
        "category": "bags",
        "collections": ["mulberry-bags", "mb-women-bags", "mb-women-top-handle"],
    },
    {
        "id": "mb-women-totes",
        "labelKo": "토트백",
        "url": f"{BASE}/gb/shop/women/bags/totes",
        "category": "bags",
        "collections": ["mulberry-bags", "mb-women-bags", "mb-women-totes"],
    },
    {
        "id": "mb-women-bucket",
        "labelKo": "버킷백",
        "url": f"{BASE}/gb/shop/women/bags/bucket-bags",
        "category": "bags",
        "collections": ["mulberry-bags", "mb-women-bags", "mb-women-bucket"],
    },
    {
        "id": "mb-women-mini",
        "labelKo": "미니 & 마이크로",
        "url": f"{BASE}/gb/shop/women/bags/mini-bags",
        "category": "bags",
        "collections": ["mulberry-bags", "mb-women-bags", "mb-women-mini"],
    },
    {
        "id": "mb-women-clutches",
        "labelKo": "클러치 & 이브닝",
        "url": f"{BASE}/gb/shop/women/bags/clutches",
        "category": "bags",
        "collections": ["mulberry-bags", "mb-women-bags", "mb-women-clutches"],
        "batch": 1,
    },
    {
        "id": "mb-women-backpacks",
        "labelKo": "백팩",
        "url": f"{BASE}/gb/shop/women/bags/backpacks",
        "category": "bags",
        "collections": ["mulberry-bags", "mb-women-bags", "mb-women-backpacks"],
    },
    # —— Bags · Women · Icons ——
    {
        "id": "mb-women-icons",
        "labelKo": "아이콘즈",
        "url": f"{BASE}/gb/shop/classics",
        "category": "bags",
        "collections": ["mulberry-bags", "mb-women-bags", "mb-women-icons"],
    },
    # —— Bags · Women · Travel ——
    {
        "id": "mb-women-travel-all",
        "labelKo": "전체",
        "url": f"{BASE}/gb/shop/women/travel",
        "category": "bags",
        "collections": ["mulberry-bags", "mb-women-travel", "mb-women-travel-all"],
    },
    {
        "id": "mb-women-travel-holdalls",
        "labelKo": "홀드올",
        "url": f"{BASE}/gb/shop/women/travel/holdalls",
        "category": "bags",
        "collections": ["mulberry-bags", "mb-women-travel", "mb-women-travel-holdalls"],
    },
    {
        "id": "mb-women-travel-luggage",
        "labelKo": "러기지",
        "url": f"{BASE}/gb/shop/women/travel/luggage",
        "category": "bags",
        "collections": ["mulberry-bags", "mb-women-travel", "mb-women-travel-luggage"],
    },
    {
        "id": "mb-women-travel-accessories",
        "labelKo": "트래블 액세서리",
        "url": f"{BASE}/gb/shop/women/travel/travel-accessories",
        "category": "accessories",
        "collections": ["mulberry-accessories", "mb-women-acc", "mb-women-travel", "mb-women-travel-accessories"],
    },
    # —— Bags · Men ——
    {
        "id": "mb-men-bags-all",
        "labelKo": "전체",
        "url": f"{BASE}/gb/shop/men/mens-bags",
        "category": "bags",
        "collections": ["mulberry-bags", "mb-men-bags", "mb-men-bags-all"],
    },
    {
        "id": "mb-men-holdalls",
        "labelKo": "홀드올",
        "url": f"{BASE}/gb/shop/men/mens-bags/holdalls",
        "category": "bags",
        "collections": ["mulberry-bags", "mb-men-bags", "mb-men-holdalls"],
    },
    {
        "id": "mb-men-backpacks",
        "labelKo": "백팩",
        "url": f"{BASE}/gb/shop/men/mens-bags/mens-backpacks",
        "category": "bags",
        "collections": ["mulberry-bags", "mb-men-bags", "mb-men-backpacks"],
    },
    {
        "id": "mb-men-briefcases",
        "labelKo": "브리프케이스",
        "url": f"{BASE}/gb/shop/men/mens-bags/mens-briefcases",
        "category": "bags",
        "collections": ["mulberry-bags", "mb-men-bags", "mb-men-briefcases"],
    },
    {
        "id": "mb-men-messenger",
        "labelKo": "메신저백",
        "url": f"{BASE}/gb/shop/men/mens-bags/mens-messenger-bags",
        "category": "bags",
        "collections": ["mulberry-bags", "mb-men-bags", "mb-men-messenger"],
    },
    # —— Bags · Men · Travel ——
    {
        "id": "mb-men-travel",
        "labelKo": "여행",
        "url": f"{BASE}/gb/shop/mens-travel",
        "category": "bags",
        "collections": ["mulberry-bags", "mb-men-bags", "mb-men-travel"],
    },
    # —— Accessories · Gifts (top-level hub) ——
    {
        "id": "mb-gifts",
        "labelKo": "선물용",
        "url": f"{BASE}/gb/shop/gifts",
        "category": "accessories",
        "collections": ["mulberry-accessories", "mb-gifts"],
    },
    # —— Accessories · Men · What's New ——
    {
        "id": "mb-men-whats-new",
        "labelKo": "신상품",
        "url": f"{BASE}/gb/shop/men/mens-whats-new",
        "category": "accessories",
        "collections": ["mulberry-accessories", "mb-men-acc", "mb-men-whats-new"],
        "weeklyPriority": True,
    },
    # —— Accessories · Men · Wallets ——
    {
        "id": "mb-men-wallets",
        "labelKo": "월렛",
        "url": f"{BASE}/gb/shop/men/mens-small-leather-goods/mens-wallets",
        "category": "accessories",
        "collections": ["mulberry-accessories", "mb-men-acc", "mb-men-wallets"],
    },
    # —— Accessories · Men ——
    {
        "id": "mb-men-accessories-all",
        "labelKo": "전체",
        "url": f"{BASE}/gb/shop/men/mens-accessories",
        "category": "accessories",
        "collections": ["mulberry-accessories", "mb-men-acc", "mb-men-accessories-all"],
    },
    {
        "id": "mb-men-keyrings",
        "labelKo": "키링",
        "url": f"{BASE}/gb/shop/men/mens-accessories/mens-keyrings",
        "category": "accessories",
        "collections": ["mulberry-accessories", "mb-men-acc", "mb-men-keyrings"],
    },
    {
        "id": "mb-men-organisers",
        "labelKo": "오거나이저",
        "url": f"{BASE}/gb/shop/men/mens-accessories/mens-organisers-inserts",
        "category": "accessories",
        "collections": ["mulberry-accessories", "mb-men-acc", "mb-men-organisers"],
    },
    {
        "id": "mb-men-sunglasses",
        "labelKo": "선글라스",
        "url": f"{BASE}/gb/shop/men/mens-accessories/mens-sunglasses",
        "category": "accessories",
        "collections": ["mulberry-accessories", "mb-men-acc", "mb-men-sunglasses"],
    },
    {
        "id": "mb-men-care",
        "labelKo": "레더 케어",
        "url": f"{BASE}/gb/shop/men/mens-accessories/care-products",
        "category": "accessories",
        "collections": ["mulberry-accessories", "mb-men-acc", "mb-men-care"],
    },
    # —— Accessories · Men · Lifestyle (shared home hub) ——
    {
        "id": "mb-men-lifestyle",
        "labelKo": "라이프스타일",
        "url": f"{BASE}/gb/shop/home",
        "category": "accessories",
        "collections": ["mulberry-accessories", "mb-men-acc", "mb-men-lifestyle", "mb-lifestyle"],
    },
    # —— Accessories · Men · Gifts ——
    {
        "id": "mb-gifts-him",
        "labelKo": "선물용",
        "url": f"{BASE}/gb/shop/men/gifts-for-him",
        "category": "accessories",
        "collections": ["mulberry-accessories", "mb-men-acc", "mb-gifts-him"],
    },
    # —— Accessories · Women · What's New ——
    {
        "id": "mb-women-whats-new",
        "labelKo": "신상품",
        "url": f"{BASE}/gb/shop/women/whats-new",
        "category": "accessories",
        "collections": ["mulberry-accessories", "mb-women-acc", "mb-women-whats-new"],
        "weeklyPriority": True,
    },
    # —— Accessories · Women · Purses ——
    {
        "id": "mb-women-purses",
        "labelKo": "퍼스",
        "url": f"{BASE}/gb/shop/women/small-leather-goods/purses",
        "category": "accessories",
        "collections": ["mulberry-accessories", "mb-women-acc", "mb-women-purses"],
    },
    # —— Accessories · Women · Lifestyle ——
    {
        "id": "mb-women-lifestyle",
        "labelKo": "라이프스타일",
        "url": f"{BASE}/gb/shop/home",
        "category": "accessories",
        "collections": ["mulberry-accessories", "mb-women-acc", "mb-women-lifestyle", "mb-lifestyle"],
    },
    # —— Accessories · Women · Gifts ——
    {
        "id": "mb-gifts-her",
        "labelKo": "선물용",
        "url": f"{BASE}/gb/shop/women/gifts-for-her",
        "category": "accessories",
        "collections": ["mulberry-accessories", "mb-women-acc", "mb-gifts-her"],
    },
]


def leaf_by_id(leaf_id: str) -> dict | None:
    for leaf in LEAVES:
        if leaf["id"] == leaf_id:
            return leaf
    return None


def leaves_for_batch(batch: int | None = None) -> list[dict]:
    if batch is None:
        return list(LEAVES)
    return [x for x in LEAVES if x.get("batch") == batch]


def all_leaf_ids() -> list[str]:
    return [x["id"] for x in LEAVES]
