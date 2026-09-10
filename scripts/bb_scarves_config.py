"""Burberry Scarves hub (악세서리 → 버버리 → 스카프) → Briq collection map.

Sourced from https://int.burberry.com/c/scarves/ (Women / Men / Children).
Discover (Virtual Scarf Try On) is intentionally omitted.
"""

from __future__ import annotations

# (briq_id, label_en, plp_path, briq_top_category, parent_group)
SCARVES_COLLECTIONS: list[tuple[str, str, str, str, str]] = [
    # Women
    (
        "bb-scarves-women",
        "Women",
        "/l/womens-accessories/scarves/",
        "accessories",
        "bb-scarves-women",
    ),
    (
        "bb-scarves-women-cashmere",
        "Cashmere Scarves",
        "/l/womens-accessories/scarves/cashmere/",
        "accessories",
        "bb-scarves-women",
    ),
    (
        "bb-scarves-women-wool",
        "Wool Scarves",
        "/l/womens-accessories/scarves/wool/",
        "accessories",
        "bb-scarves-women",
    ),
    (
        "bb-scarves-women-silk",
        "Silk Scarves",
        "/l/womens-accessories/scarves/silk/",
        "accessories",
        "bb-scarves-women",
    ),
    (
        "bb-scarves-women-lightweight",
        "Lightweight Scarves",
        "/l/womens-accessories/scarves/lightweight/",
        "accessories",
        "bb-scarves-women",
    ),
    (
        "bb-scarves-women-personalised",
        "Personalised Scarves",
        "/l/womens-accessories/scarves/personalised/",
        "accessories",
        "bb-scarves-women",
    ),
    # Men
    (
        "bb-scarves-men",
        "Men",
        "/l/mens-accessories/scarves/",
        "accessories",
        "bb-scarves-men",
    ),
    (
        "bb-scarves-men-cashmere",
        "Cashmere Scarves",
        "/l/mens-accessories/scarves/cashmere/",
        "accessories",
        "bb-scarves-men",
    ),
    (
        "bb-scarves-men-wool",
        "Wool Scarves",
        "/l/mens-accessories/scarves/wool/",
        "accessories",
        "bb-scarves-men",
    ),
    (
        "bb-scarves-men-lightweight",
        "Lightweight Scarves",
        "/l/mens-accessories/scarves/lightweight/",
        "accessories",
        "bb-scarves-men",
    ),
    (
        "bb-scarves-men-personalised",
        "Personalised Scarves",
        "/l/mens-accessories/scarves/personalised/",
        "accessories",
        "bb-scarves-men",
    ),
    # Children
    (
        "bb-scarves-kids",
        "Children",
        "/l/childrens-accessories/scarves/",
        "accessories",
        "bb-scarves-kids",
    ),
    (
        "bb-scarves-kids-girls",
        "Girls’ Scarves",
        "/l/girls-clothes/scarves/",
        "accessories",
        "bb-scarves-kids",
    ),
    (
        "bb-scarves-kids-boys",
        "Boys’ Scarves",
        "/l/boys-clothes/scarves/",
        "accessories",
        "bb-scarves-kids",
    ),
]
