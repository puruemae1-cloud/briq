"""Burberry Beauty hub (악세서리 → 버버리 → 뷰티) → Briq collection map.

Sourced from https://int.burberry.com/c/beauty/
Make-up + Fragrances (Women’s / Men’s / Signatures / Goddess / Her / Hero).
"""

from __future__ import annotations

# (briq_id, label_en, plp_path, briq_top_category, parent_group)
BEAUTY_COLLECTIONS: list[tuple[str, str, str, str, str]] = [
    # Make-up
    (
        "bb-beauty-makeup",
        "Make-up",
        "/l/beauty/make-up/",
        "accessories",
        "bb-beauty-makeup",
    ),
    (
        "bb-beauty-makeup-face",
        "Face",
        "/l/beauty/make-up/face/",
        "accessories",
        "bb-beauty-makeup",
    ),
    (
        "bb-beauty-makeup-lips",
        "Lips",
        "/l/beauty/make-up/lips/",
        "accessories",
        "bb-beauty-makeup",
    ),
    (
        "bb-beauty-makeup-eyes",
        "Eyes",
        "/l/beauty/make-up/eyes/",
        "accessories",
        "bb-beauty-makeup",
    ),
    # Fragrances
    (
        "bb-beauty-fragrances",
        "Fragrances",
        "/l/beauty/fragrances/",
        "accessories",
        "bb-beauty-fragrances",
    ),
    (
        "bb-beauty-fragrances-women",
        "Women’s Fragrances",
        "/l/beauty/womens-fragrances/",
        "accessories",
        "bb-beauty-fragrances",
    ),
    (
        "bb-beauty-fragrances-men",
        "Men’s Fragrances",
        "/l/mens-fragrances/",
        "accessories",
        "bb-beauty-fragrances",
    ),
    (
        "bb-beauty-fragrances-signatures",
        "Burberry Signatures",
        "/l/beauty/fragrances/style=signatures/",
        "accessories",
        "bb-beauty-fragrances",
    ),
    (
        "bb-beauty-fragrances-signatures-men",
        "Burberry Signatures (Men)",
        "/l/mens-fragrances/style=signatures/",
        "accessories",
        "bb-beauty-fragrances",
    ),
    (
        "bb-beauty-fragrances-goddess",
        "Burberry Goddess",
        "/l/beauty/fragrances/style=goddess/",
        "accessories",
        "bb-beauty-fragrances",
    ),
    (
        "bb-beauty-fragrances-her",
        "Burberry Her",
        "/l/beauty/fragrances/style=her/",
        "accessories",
        "bb-beauty-fragrances",
    ),
    (
        "bb-beauty-fragrances-hero",
        "Burberry Hero",
        "/l/beauty/fragrances/style=hero/",
        "accessories",
        "bb-beauty-fragrances",
    ),
]
