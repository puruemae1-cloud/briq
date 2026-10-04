"""Keep headwear / scarves / gloves out of the bags category.

Brand bag listings (Mulberry travel, Dior bag accessories) also list caps and
scarves; scripts that let any bag leaf win would file them under bags. Keep the
patterns in sync with NON_BAG_RE / BAG_RE in scripts/build-catalog-dist.mjs.
"""
from __future__ import annotations

import re

NON_BAG_RE = re.compile(
    r"\b(caps?|baseball|hats?|beanies?|berets?|scarf|scarves|gloves?|mittens?|snoods?"
    r"|headbands?|bandanas?|balaclavas?|stoles?)\b|모자|비니|버킷\s?햇|베레모|스카프|머플러|장갑",
    re.I,
)
BAG_RE = re.compile(
    r"\b(bags?|totes?|pouch(es)?|clutch(es)?|backpacks?|satchels?|crossbody|holdall|duffel|duffle"
    r"|wallets?|purses?)\b|가방|백팩|핸드백|토트|파우치|클러치",
    re.I,
)
BAG_TAGS = {"bags", "handbags", "가방", "핸드백"}


def is_non_bag(product: dict) -> bool:
    text = f"{product.get('name') or ''} {product.get('nameKo') or ''}"
    return bool(NON_BAG_RE.search(text)) and not BAG_RE.search(text)


def demote_non_bag(product: dict) -> bool:
    """Move a misfiled non-bag product from bags to accessories (in place)."""
    if product.get("category") != "bags" or not is_non_bag(product):
        return False
    product["category"] = "accessories"
    tags = [t for t in product.get("tags") or [] if t not in BAG_TAGS]
    if "accessories" not in tags:
        tags.append("accessories")
    product["tags"] = tags
    return True
