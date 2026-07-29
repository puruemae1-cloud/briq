"""Burberry Women → Briq collection map (shared by scrape + build)."""

from __future__ import annotations

# (briq_id, label_en, plp_path, briq_top_category, parent_group)
# parent_group used for nav nesting hints only.
COLLECTIONS: list[tuple[str, str, str, str, str]] = [
    # Luxury — Latest
    ("bb-women-new", "New", "/l/womens-clothing/new-arrivals/", "luxury", "bb-women-latest"),
    (
        "bb-women-summer-styles",
        "Summer Styles",
        "/l/womens-clothing/summer-styles/",
        "luxury",
        "bb-women-latest",
    ),
    (
        "bb-women-classics",
        "Burberry Classics",
        "/l/womens-clothing/classics/",
        "luxury",
        "bb-women-latest",
    ),
    # Luxury — Coats & Jackets
    (
        "bb-women-coats-jackets",
        "Coats & Jackets",
        "/l/womens-coats-jackets/",
        "luxury",
        "bb-women-coats-jackets",
    ),
    ("bb-women-coats", "Coats", "/l/womens-coats-jackets/coats/", "luxury", "bb-women-coats-jackets"),
    (
        "bb-women-jackets",
        "Jackets",
        "/l/womens-coats-jackets/jackets/",
        "luxury",
        "bb-women-coats-jackets",
    ),
    (
        "bb-women-trench-coats",
        "Trench Coats",
        "/l/womens-coats-jackets/trench-coats/",
        "luxury",
        "bb-women-coats-jackets",
    ),
    (
        "bb-women-quilted-jackets",
        "Quilted Jackets",
        "/l/womens-coats-jackets/quilts/",
        "luxury",
        "bb-women-coats-jackets",
    ),
    (
        "bb-women-puffer-jackets",
        "Puffer Jackets",
        "/l/womens-coats-jackets/puffers/",
        "luxury",
        "bb-women-coats-jackets",
    ),
    (
        "bb-women-ponchos-capes",
        "Ponchos & Capes",
        "/l/womens-clothing/capes-ponchos/",
        "luxury",
        "bb-women-coats-jackets",
    ),
    # Luxury — Clothes
    ("bb-women-clothes", "Clothes", "/l/womens-clothing/", "luxury", "bb-women-clothes"),
    (
        "bb-women-knitwear",
        "Knitwear",
        "/l/womens-clothing/knitwear/",
        "luxury",
        "bb-women-clothes",
    ),
    (
        "bb-women-polos-tshirts",
        "Polos & T-shirts",
        "/l/womens-clothing/t-shirts-polos/",
        "luxury",
        "bb-women-clothes",
    ),
    (
        "bb-women-shirts-tops",
        "Shirts & Tops",
        "/l/womens-clothing/shirts-tops/",
        "luxury",
        "bb-women-clothes",
    ),
    ("bb-women-dresses", "Dresses", "/l/womens-clothing/dresses/", "luxury", "bb-women-clothes"),
    ("bb-women-skirts", "Skirts", "/l/womens-clothing/skirts/", "luxury", "bb-women-clothes"),
    (
        "bb-women-hoodies-sweatshirts",
        "Hoodies & Sweatshirts",
        "/l/womens-clothing/sweatshirts/",
        "luxury",
        "bb-women-clothes",
    ),
    (
        "bb-women-blazers-tailoring",
        "Blazers & Tailoring",
        "/l/womens-clothing/blazers-tailored-trousers/",
        "luxury",
        "bb-women-clothes",
    ),
    (
        "bb-women-trousers-shorts",
        "Trousers & Shorts",
        "/l/womens-clothing/trousers-shorts/",
        "luxury",
        "bb-women-clothes",
    ),
    (
        "bb-women-activewear",
        "Activewear",
        "/l/womens-clothing/leggings-activewear/",
        "luxury",
        "bb-women-clothes",
    ),
    ("bb-women-denim", "Denim", "/l/womens-clothing/denim/", "luxury", "bb-women-clothes"),
    (
        "bb-women-swimwear",
        "Swimwear",
        "/l/womens-clothing/swimwear/",
        "luxury",
        "bb-women-clothes",
    ),
    # Bags
    ("bb-women-bags", "Bags", "/l/womens-bags/", "bags", "bb-women-bags"),
    ("bb-women-mini-bags", "Mini Bags", "/l/womens-bags/mini/", "bags", "bb-women-bags"),
    ("bb-women-tote-bags", "Tote Bags", "/l/womens-bags/tote/", "bags", "bb-women-bags"),
    (
        "bb-women-crossbody-bags",
        "Crossbody Bags",
        "/l/womens-bags/crossbody/",
        "bags",
        "bb-women-bags",
    ),
    (
        "bb-women-shoulder-bags",
        "Shoulder Bags",
        "/l/womens-bags/shoulder/",
        "bags",
        "bb-women-bags",
    ),
    (
        "bb-women-top-handle-bags",
        "Top Handle Bags",
        "/l/womens-bags/top-handle/",
        "bags",
        "bb-women-bags",
    ),
    ("bb-women-backpacks", "Backpacks", "/l/womens-bags/backpacks/", "bags", "bb-women-bags"),
    # Shoes
    ("bb-women-shoes", "Shoes", "/l/womens-shoes/", "shoes", "bb-women-shoes"),
    ("bb-women-sneakers", "Sneakers", "/l/womens-shoes/sneakers/", "shoes", "bb-women-shoes"),
    ("bb-women-sandals", "Sandals", "/l/womens-shoes/sandals/", "shoes", "bb-women-shoes"),
    (
        "bb-women-loafers-ballerinas",
        "Loafers & Ballerinas",
        "/l/womens-shoes/loafers-ballerinas/",
        "shoes",
        "bb-women-shoes",
    ),
    ("bb-women-boots", "Boots", "/l/womens-shoes/boots/", "shoes", "bb-women-shoes"),
    ("bb-women-pumps", "Pumps", "/l/womens-shoes/pumps/", "shoes", "bb-women-shoes"),
    # Accessories
    (
        "bb-women-scarves",
        "Scarves",
        "/l/womens-accessories/scarves/",
        "accessories",
        "bb-women-accessories",
    ),
    (
        "bb-women-belts",
        "Belts",
        "/l/womens-accessories/belts/",
        "accessories",
        "bb-women-accessories",
    ),
    (
        "bb-women-sunglasses",
        "Sunglasses",
        "/l/womens-accessories/sunglasses/",
        "accessories",
        "bb-women-accessories",
    ),
    (
        "bb-women-caps-hats",
        "Caps & Bucket Hats",
        "/l/womens-accessories/hats-gloves/",
        "accessories",
        "bb-women-accessories",
    ),
    ("bb-women-umbrellas", "Umbrellas", "/l/umbrellas/", "accessories", "bb-women-accessories"),
    (
        "bb-women-jewellery",
        "Jewellery",
        "/l/womens-accessories/jewellery/",
        "accessories",
        "bb-women-accessories",
    ),
    (
        "bb-women-home",
        "Home",
        "/l/home-accessories/",
        "accessories",
        "bb-women-accessories",
    ),
    (
        "bb-women-socks-tights",
        "Socks & Tights",
        "/l/womens-accessories/socks-tights/",
        "accessories",
        "bb-women-accessories",
    ),
    (
        "bb-women-tech-travel",
        "Tech & Travel",
        "/l/womens-accessories/tech-travel/",
        "accessories",
        "bb-women-accessories",
    ),
    (
        "bb-women-key-charms",
        "Key & Bag Charms",
        "/l/womens-accessories/key-charms/",
        "accessories",
        "bb-women-accessories",
    ),
    # Wallets
    (
        "bb-women-wallets",
        "Wallets & Card Cases",
        "/l/womens-accessories/wallets/",
        "accessories",
        "bb-women-wallets",
    ),
    (
        "bb-women-card-cases",
        "Card Cases",
        "/l/womens-accessories/wallets/benefit=card_cases/",
        "accessories",
        "bb-women-wallets",
    ),
    (
        "bb-women-long-wallets",
        "Long Wallets",
        "/l/womens-accessories/wallets/benefit=long_wallets/",
        "accessories",
        "bb-women-wallets",
    ),
    (
        "bb-women-compact-wallets",
        "Compact Wallets",
        "/l/womens-accessories/wallets/benefit=compact_wallets/",
        "accessories",
        "bb-women-wallets",
    ),
    (
        "bb-women-chain-strap-wallets",
        "Chain Strap Wallets",
        "/l/womens-accessories/wallets/benefit=chain_strap_wallets/",
        "accessories",
        "bb-women-wallets",
    ),
    # Gifts
    ("bb-women-gifts", "Gifts", "/l/womens-gifts/", "accessories", "bb-women-gifts"),
    (
        "bb-women-fragrance",
        "Fragrance",
        "/l/beauty/womens-fragrances/",
        "accessories",
        "bb-women-gifts",
    ),
    (
        "bb-women-personalised-gifts",
        "Personalised Gifts",
        "/l/womens-gifts/personalised/",
        "accessories",
        "bb-women-gifts",
    ),
    (
        "bb-women-personalised-scarves",
        "Personalised Scarves",
        "/l/womens-accessories/scarves/personalised/",
        "accessories",
        "bb-women-gifts",
    ),
]

# Parent-only ids (no direct PLP) — used for shop chip expansion.
GROUP_IDS = [
    "burberry",
    "bb-women",
    "bb-women-latest",
    "burberry-bags",
    "burberry-shoes",
    "burberry-accessories",
    "bb-women-accessories",
]

BASE = "https://uk.burberry.com"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)


def collection_by_id() -> dict[str, tuple[str, str, str, str]]:
    return {cid: (label, path, top, parent) for cid, label, path, top, parent in COLLECTIONS}


def primary_category_for_collections(cols: list[str]) -> tuple[str, str]:
    """Return (CategoryId, primary SubcategoryId) for a colourway."""
    by = collection_by_id()
    # Prefer most specific leaf: bags/shoes/accessories before broad luxury view-alls.
    priority_tops = ("bags", "shoes", "accessories", "luxury")
    ranked: list[tuple[int, str, str]] = []
    for c in cols:
        if c not in by:
            continue
        label, path, top, parent = by[c]
        # Prefer leaf paths (longer) over view-all parents
        specificity = path.count("/")
        top_rank = priority_tops.index(top) if top in priority_tops else 99
        ranked.append((top_rank, -specificity, c))
    if not ranked:
        return "luxury", "bb-women-clothes"
    ranked.sort()
    primary = ranked[0][2]
    return by[primary][2], primary
