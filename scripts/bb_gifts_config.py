"""Burberry Gifts hub (버버리 선물추천) → Briq collection map."""

from __future__ import annotations

# (briq_id, label_en, plp_path, briq_top_category, parent_group)
# Sourced from https://uk.burberry.com/c/gifts/ (For Her / Him / Children / Home).
GIFTS_COLLECTIONS: list[tuple[str, str, str, str, str]] = [
    # For Her
    (
        "bb-gifts-her",
        "For Her",
        "/l/womens-gifts/",
        "accessories",
        "bb-gifts-her",
    ),
    (
        "bb-gifts-her-scarves",
        "Scarves",
        "/l/womens-accessories/scarves/",
        "accessories",
        "bb-gifts-her",
    ),
    (
        "bb-gifts-her-jewellery",
        "Jewellery",
        "/l/womens-accessories/jewellery/",
        "accessories",
        "bb-gifts-her",
    ),
    (
        "bb-gifts-her-fragrance",
        "Fragrance",
        "/l/beauty/womens-fragrances/",
        "accessories",
        "bb-gifts-her",
    ),
    (
        "bb-gifts-her-personalised",
        "Personalised Gifts",
        "/l/womens-gifts/personalised/",
        "accessories",
        "bb-gifts-her",
    ),
    (
        "bb-gifts-her-personalised-scarves",
        "Personalised Scarves",
        "/l/womens-accessories/scarves/personalised/",
        "accessories",
        "bb-gifts-her",
    ),
    (
        "bb-gifts-her-classics",
        "Burberry Classics",
        "/l/womens-clothing/classics/",
        "accessories",
        "bb-gifts-her",
    ),
    # For Him
    (
        "bb-gifts-him",
        "For Him",
        "/l/mens-gifts/",
        "accessories",
        "bb-gifts-him",
    ),
    (
        "bb-gifts-him-scarves",
        "Scarves",
        "/l/mens-accessories/scarves/",
        "accessories",
        "bb-gifts-him",
    ),
    (
        "bb-gifts-him-ties-cufflinks",
        "Ties & Cufflinks",
        "/l/mens-accessories/ties-cufflinks/",
        "accessories",
        "bb-gifts-him",
    ),
    (
        "bb-gifts-him-fragrance",
        "Fragrance",
        "/l/mens-fragrances/",
        "accessories",
        "bb-gifts-him",
    ),
    (
        "bb-gifts-him-personalised",
        "Personalised Gifts",
        "/l/mens-gifts/personalised/",
        "accessories",
        "bb-gifts-him",
    ),
    (
        "bb-gifts-him-personalised-scarves",
        "Personalised Scarves",
        "/l/mens-accessories/scarves/personalised/",
        "accessories",
        "bb-gifts-him",
    ),
    (
        "bb-gifts-him-classics",
        "Burberry Classics",
        "/l/mens-clothing/classics/",
        "accessories",
        "bb-gifts-him",
    ),
    # For Children
    (
        "bb-gifts-children",
        "For Children",
        "/l/childrens-gifts/",
        "accessories",
        "bb-gifts-children",
    ),
    (
        "bb-gifts-children-girls-scarves",
        "Girls’ Scarves",
        "/l/girls-clothes/scarves/",
        "accessories",
        "bb-gifts-children",
    ),
    (
        "bb-gifts-children-boys-scarves",
        "Boys’ Scarves",
        "/l/boys-clothes/scarves/",
        "accessories",
        "bb-gifts-children",
    ),
    (
        "bb-gifts-children-baby",
        "Baby Gifts",
        "/l/childrens-gifts/baby-gifts/",
        "accessories",
        "bb-gifts-children",
    ),
    (
        "bb-gifts-children-newborn",
        "Newborn Gifts",
        "/l/childrens-gifts/newborn/",
        "accessories",
        "bb-gifts-children",
    ),
    (
        "bb-gifts-children-accessories",
        "Accessories",
        "/l/childrens-accessories/",
        "accessories",
        "bb-gifts-children",
    ),
    # For the Home
    (
        "bb-gifts-home",
        "For the Home",
        "/l/home-accessories/",
        "accessories",
        "bb-gifts-home",
    ),
]
