"""Celine accessories leaf ID canonicalization + title-based membership.

Keeps shop nav IDs (categories.ts) aligned with scrape leafIds and backfills
products that only landed on *-acc-all / *-jewellery-all / etc.
"""

from __future__ import annotations

import re
from typing import Iterable

# Legacy scrape IDs → shop nav IDs
CE_LEAF_CANONICAL: dict[str, str] = {
    "ce-women-hair": "ce-women-hair-accessories",
    "ce-women-silk-scarves": "ce-women-silk-squares-accessories",
    "ce-women-pouches": "ce-women-pouches-tech-accessories",
    "ce-women-woc": "ce-women-wallets-on-chain",
    "ce-women-card-holders": "ce-women-coin-card-holders",
    "ce-men-scarves": "ce-men-silks-scarves",
    "ce-men-hats": "ce-men-hats-soft-accessories",
    "ce-women-boots": "ce-women-boots-ankle-boots",
    "ce-women-ballet": "ce-women-ballerinas",
    "ce-men-cross-body-bags": "ce-men-crossbody-bags",
}

# Hub / view-all IDs that should be promoted away when a specific leaf arrives
CE_HUB_LEAF_IDS: frozenset[str] = frozenset(
    {
        "ce-women-rtw-all",
        "ce-men-rtw-all",
        "ce-women-acc-all",
        "ce-men-acc-all",
        "ce-women-jewellery-all",
        "ce-men-jewellery-all",
        "ce-women-sunglasses-all",
        "ce-men-sunglasses-all",
        "ce-women-slg-all",
        "ce-men-slg-all",
        "ce-women-bags-all",
        "ce-men-bags-all",
        "ce-women-shoes-all",
        "ce-men-shoes-all",
    }
)

_BELT_RE = re.compile(
    r"\b(belt|buckle\b.*\bstrap|strap\b.*\bbuckle)\b",
    re.I,
)
_HAIR_RE = re.compile(
    r"\b(scrunchy|scrunchie|headband|hair\s*clip|barrette|claw\s*clip|hair\s*tie)\b",
    re.I,
)
_HAT_RE = re.compile(
    r"\b(hat|cap|beanie|beret|bucket\s*hat|glove|gloves|mitt)\b",
    re.I,
)
_SILK_RE = re.compile(
    r"\b(silk\s*twill|silk\s*square|square\s*in\s*silk|bandana|lavalliere|foulard)\b",
    re.I,
)
_SCARF_RE = re.compile(
    r"\b(scarf|shawl|stole|muffler|alpaca|cashmere\s*scarf)\b",
    re.I,
)
_BAG_CHARM_RE = re.compile(r"\bbag\s*charm|\bcharm\b.*\bbag\b|\bkey\s*ring\b", re.I)
_EARRING_RE = re.compile(r"\b(earrings?|ear\s*cuffs?|hoops?|studs?)\b", re.I)
_NECKLACE_RE = re.compile(r"\b(necklaces?|pendants?|chokers?|gourmettes?)\b", re.I)
_BRACELET_RE = re.compile(r"\b(bracelets?|cuffs?|bangles?)\b", re.I)
_RING_RE = re.compile(r"\b(rings?|signets?)\b", re.I)
_CHARM_RE = re.compile(r"\b(celine\s*charms?|^charms?\b)", re.I)
_WALLET_RE = re.compile(r"\b(wallet|purse|billfold)\b", re.I)
_CARD_RE = re.compile(r"\b(card\s*holder|coin\s*purse|coin\s*holder|card\s*case)\b", re.I)
_POUCH_RE = re.compile(r"\b(pouch|phone\s*case|airpods|tech\s*access)\b", re.I)
_WOC_RE = re.compile(r"\b(wallet\s*on\s*chain|woc)\b", re.I)
_SUN_ROUND = re.compile(r"\bround\b|\bs\d{3}\b.*round", re.I)
_SUN_CAT = re.compile(r"\bcat[\s-]?eye\b", re.I)
_SUN_AVI = re.compile(r"\baviator\b", re.I)
_SUN_MASK = re.compile(r"\bmask\b", re.I)
_SUN_RECT = re.compile(r"\brectang|\bsquare\s*frame\b", re.I)


def canonicalize_leaf_id(leaf: str) -> str:
    leaf = (leaf or "").strip()
    return CE_LEAF_CANONICAL.get(leaf, leaf)


def canonicalize_collections(cols: Iterable[str]) -> list[str]:
    out: list[str] = []
    for c in cols or []:
        canon = canonicalize_leaf_id(str(c))
        if canon and canon not in out:
            out.append(canon)
    return out


def is_hub_leaf(leaf: str) -> bool:
    return canonicalize_leaf_id(leaf) in CE_HUB_LEAF_IDS


def infer_women_acc_leaf(title: str) -> str | None:
    t = title or ""
    if _BELT_RE.search(t):
        return "ce-women-belts"
    if _HAIR_RE.search(t):
        return "ce-women-hair-accessories"
    if _HAT_RE.search(t):
        return "ce-women-hats"
    if _SILK_RE.search(t):
        return "ce-women-silk-squares-accessories"
    if _SCARF_RE.search(t):
        return "ce-women-scarves"
    if _BAG_CHARM_RE.search(t):
        return "ce-women-bag-charms"
    return None


def infer_men_acc_leaf(title: str) -> str | None:
    t = title or ""
    if _BELT_RE.search(t):
        return "ce-men-belts"
    if _HAT_RE.search(t):
        return "ce-men-hats-soft-accessories"
    if _SILK_RE.search(t) or _SCARF_RE.search(t):
        return "ce-men-silks-scarves"
    return None


def infer_jewellery_leaf(title: str, *, women: bool) -> str | None:
    t = title or ""
    prefix = "ce-women-" if women else "ce-men-"
    # Charms line first (titles often "Charms … Necklace")
    if _CHARM_RE.search(t) and not _EARRING_RE.search(t):
        # Standalone charm pendants / charms PLP — not earrings
        if re.search(r"\b(charm|charms)\b", t, re.I) and not re.search(
            r"\b(necklace|bracelet|ring|earring|hoop|stud)\b", t, re.I
        ):
            return f"{prefix}charms"
    if _EARRING_RE.search(t):
        return f"{prefix}earrings"
    if _NECKLACE_RE.search(t):
        return f"{prefix}necklaces"
    if _BRACELET_RE.search(t):
        return f"{prefix}bracelets" if women else "ce-men-bracelets-rings"
    if _RING_RE.search(t):
        return f"{prefix}rings"
    if _CHARM_RE.search(t):
        return f"{prefix}charms"
    return None


def infer_slg_leaf(title: str, *, women: bool) -> str | None:
    t = title or ""
    if women:
        if _WOC_RE.search(t):
            return "ce-women-wallets-on-chain"
        if _CARD_RE.search(t):
            return "ce-women-coin-card-holders"
        if _POUCH_RE.search(t):
            return "ce-women-pouches-tech-accessories"
        if _WALLET_RE.search(t):
            return "ce-women-wallets"
        return None
    if _CARD_RE.search(t):
        return "ce-men-card-holders"
    if _POUCH_RE.search(t):
        return "ce-men-tech-accessories"
    if re.search(r"\bcoin\b", t, re.I):
        return "ce-men-coin-holders"
    if _WALLET_RE.search(t):
        return "ce-men-wallets"
    return None


def infer_sunglasses_leaf(title: str, *, women: bool) -> str | None:
    t = title or ""
    prefix = "ce-women-sunglasses-" if women else "ce-men-sunglasses-"
    if _SUN_CAT.search(t):
        return f"{prefix}cat-eye" if women else None
    if _SUN_AVI.search(t):
        return f"{prefix}aviator"
    if _SUN_MASK.search(t):
        return f"{prefix}mask"
    if _SUN_ROUND.search(t):
        return f"{prefix}round"
    if _SUN_RECT.search(t):
        return f"{prefix}rectangular"
    return None


def enrich_row_membership(row: dict) -> dict:
    """Canonicalize IDs and infer specific leaf membership from title when on a hub."""
    row = dict(row)
    leaf = canonicalize_leaf_id(str(row.get("leafId") or ""))
    cols = canonicalize_collections(row.get("collections") or [])
    title = str(row.get("title") or "")

    inferred: str | None = None
    if leaf in {"ce-women-acc-all", "ce-women-accessories", "ce-women-other-accessories", ""} or any(
        c in {"ce-women-acc-all", "ce-women-accessories"} for c in cols
    ):
        if leaf in CE_HUB_LEAF_IDS or leaf in {"", "ce-women-accessories", "ce-women-other-accessories"}:
            inferred = infer_women_acc_leaf(title)
    if not inferred and (
        leaf in {"ce-men-acc-all", "ce-men-accessories", "ce-men-other-accessories"}
        or any(c in {"ce-men-acc-all", "ce-men-accessories"} for c in cols)
    ):
        if leaf in CE_HUB_LEAF_IDS or leaf in {"", "ce-men-accessories", "ce-men-other-accessories"}:
            inferred = infer_men_acc_leaf(title)

    if not inferred and (
        leaf in {"ce-women-jewellery-all", "ce-women-jewellery", "ce-women-fine-jewellery"}
        or any("jewellery" in c for c in cols if "men" not in c)
    ):
        if is_hub_leaf(leaf) or leaf in {"ce-women-jewellery", "ce-women-fine-jewellery"}:
            inferred = infer_jewellery_leaf(title, women=True)

    if not inferred and (
        leaf in {"ce-men-jewellery-all", "ce-men-jewellery"}
        or any(c.startswith("ce-men-jewellery") for c in cols)
    ):
        if is_hub_leaf(leaf) or leaf == "ce-men-jewellery":
            inferred = infer_jewellery_leaf(title, women=False)

    if not inferred and (
        leaf in {"ce-women-slg-all", "ce-women-slg"}
        or any(c in {"ce-women-slg-all", "ce-women-slg"} for c in cols)
    ):
        if is_hub_leaf(leaf) or leaf == "ce-women-slg":
            inferred = infer_slg_leaf(title, women=True)

    if not inferred and (
        leaf in {"ce-men-slg-all", "ce-men-slg"}
        or any(c in {"ce-men-slg-all", "ce-men-slg"} for c in cols)
    ):
        if is_hub_leaf(leaf) or leaf == "ce-men-slg":
            inferred = infer_slg_leaf(title, women=False)

    if not inferred and (
        leaf in {"ce-women-sunglasses-all", "ce-women-sunglasses"}
        or any(c in {"ce-women-sunglasses-all", "ce-women-sunglasses"} for c in cols)
    ):
        if is_hub_leaf(leaf) or leaf == "ce-women-sunglasses":
            inferred = infer_sunglasses_leaf(title, women=True)

    if not inferred and (
        leaf in {"ce-men-sunglasses-all", "ce-men-sunglasses"}
        or any(c in {"ce-men-sunglasses-all", "ce-men-sunglasses"} for c in cols)
    ):
        if is_hub_leaf(leaf) or leaf == "ce-men-sunglasses":
            inferred = infer_sunglasses_leaf(title, women=False)

    # Always canonicalize current leaf
    if leaf:
        leaf = canonicalize_leaf_id(leaf)

    if inferred:
        leaf = inferred
        parents: list[str] = ["celine-accessories"]
        if inferred.startswith("ce-women-"):
            if "jewellery" in inferred or inferred.endswith(
                ("earrings", "necklaces", "bracelets", "rings", "charms")
            ):
                parents += ["ce-women-jewellery", "ce-women-jewellery-all", inferred]
            elif "sunglasses" in inferred:
                parents += ["ce-women-sunglasses", "ce-women-sunglasses-all", inferred]
            elif any(
                x in inferred
                for x in ("wallet", "slg", "pouch", "card", "coin")
            ):
                parents += ["ce-women-slg", "ce-women-slg-all", inferred]
            else:
                parents += ["ce-women-accessories", "ce-women-acc-all", inferred]
        else:
            if "jewellery" in inferred or inferred.endswith(
                ("earrings", "necklaces", "bracelets-rings", "rings", "charms")
            ):
                parents += ["ce-men-jewellery", "ce-men-jewellery-all", inferred]
            elif "sunglasses" in inferred:
                parents += ["ce-men-sunglasses", "ce-men-sunglasses-all", inferred]
            elif any(x in inferred for x in ("wallet", "slg", "tech", "card", "coin")):
                parents += ["ce-men-slg", "ce-men-slg-all", inferred]
            else:
                parents += ["ce-men-accessories", "ce-men-acc-all", inferred]
        cols = list(dict.fromkeys(cols + parents))

    if leaf:
        row["leafId"] = leaf
        if leaf not in cols:
            cols.append(leaf)
    row["collections"] = cols
    return row
