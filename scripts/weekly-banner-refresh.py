#!/usr/bin/env python3
"""Weekly refresh of Briq sports banners only.

Default: only SPORTS_SLOTS rotate (golf / cycle / swim / run / tennis + related
shop & sports-brand chips). Every other banner stays fixed — either an
explicitly locked creative in LOCKED_BANNERS, or the last committed frame.

  python3 scripts/weekly-banner-refresh.py              # sports only (CI default)
  python3 scripts/weekly-banner-refresh.py --all        # emergency full refresh
  python3 scripts/weekly-banner-refresh.py --only rot-golf --seed 42
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from banner_smart_crop import (  # noqa: E402
    aspect_ratio,
    export_banner_set,
    has_on_model_face,
    is_extreme_closeup,
    is_face_dominant,
    subject_fill_ratio,
)

BANNER_DIR = ROOT / "public" / "banners"
MOBILE_DIR = BANNER_DIR / "m"
TABLET_DIR = BANNER_DIR / "t"
MANIFEST = ROOT / "src/data/banner-refresh-manifest.json"
MEDIA = "https://cdn.jsdelivr.net/gh/puruemae1-cloud/briq@product-images/public"

UA = (
    "Mozilla/5.0 (compatible; BriqBannerBot/1.0; +https://briq.kr)"
)

# Slot filename → theme buckets used to pick catalog on-model frames.
SLOT_THEMES: dict[str, list[str]] = {
    # London B&W panoramas (external curated pool — see LONDON_BW_SOURCES)
    "rot-hero-1.jpg": ["london-bw"],
    "rot-hero-2.jpg": ["london-bw"],
    "rot-hero-3.jpg": ["london-bw"],
    "rot-hero-4.jpg": ["london-bw"],
    # Non-apparel edit — watches / shoes / accessories / bags (forced B&W)
    "rot-event-1.jpg": ["watches", "shoes", "accessories", "bags"],
    "rot-event-2.jpg": ["watches", "shoes", "accessories", "bags"],
    "rot-event-3.jpg": ["watches", "shoes", "accessories", "bags"],
    "rot-luxury-1.jpg": ["luxury"],
    "rot-luxury-2.jpg": ["luxury"],
    "rot-luxury-3.jpg": ["luxury"],
    "rot-cloth-1.jpg": ["fashion"],
    "rot-cloth-2.jpg": ["fashion"],
    "rot-cloth-3.jpg": ["fashion"],
    "rot-bag-1.jpg": ["bags"],
    "rot-bag-2.jpg": ["bags"],
    "rot-bag-3.jpg": ["bags"],
    "rot-shoe-1.jpg": ["shoes"],
    "rot-shoe-2.jpg": ["shoes"],
    "rot-shoe-3.jpg": ["shoes"],
    "rot-acc-1.jpg": ["accessories"],
    "rot-acc-2.jpg": ["accessories"],
    "rot-acc-3.jpg": ["accessories"],
    "rot-watch-1.jpg": ["watches"],
    "rot-watch-2.jpg": ["watches"],
    "rot-watch-3.jpg": ["watches"],
    "rot-cw-1.jpg": ["brand:christopher-ward"],
    "rot-cw-2.jpg": ["brand:christopher-ward"],
    "rot-cw-3.jpg": ["brand:christopher-ward"],
    "rot-cw-alt.jpg": ["brand:christopher-ward"],
    "rot-golf-1.jpg": ["golf"],
    "rot-golf-2.jpg": ["golf"],
    "rot-golf-3.jpg": ["golf"],
    "rot-cycle-1.jpg": ["outdoor"],
    "rot-cycle-2.jpg": ["outdoor"],
    "rot-cycle-3.jpg": ["outdoor"],
    "rot-swim-1.jpg": ["outdoor"],
    "rot-swim-2.jpg": ["outdoor"],
    "rot-swim-3.jpg": ["outdoor"],
    "rot-run-1.jpg": ["outdoor"],
    "rot-run-2.jpg": ["outdoor"],
    "rot-run-3.jpg": ["outdoor"],
    "rot-tennis-1.jpg": ["outdoor"],
    "rot-tennis-2.jpg": ["outdoor"],
    "rot-tennis-3.jpg": ["outdoor"],
    "shop-lux-w-1.jpg": ["luxury"],
    "shop-lux-w-2.jpg": ["luxury"],
    "shop-lux-m-1.jpg": ["luxury"],
    "shop-lux-m-2.jpg": ["luxury"],
    "shop-cloth-1.jpg": ["fashion"],
    "shop-cloth-w-1.jpg": ["fashion"],
    "shop-cloth-m-1.jpg": ["fashion"],
    "shop-bag-1.jpg": ["bags"],
    "shop-shoe-lux-w-1.jpg": ["shoes"],
    "shop-shoe-lux-m-1.jpg": ["shoes"],
    "shop-shoe-train-w-1.jpg": ["outdoor"],
    "shop-shoe-train-m-1.jpg": ["outdoor"],
    "shop-golf-1.jpg": ["golf"],
    "shop-run-1.jpg": ["outdoor"],
    # Brand category heroes (shop strip aspect) — one brand per key
    "brand-gucci-1.jpg": ["brand:gucci"],
    "brand-gucci-2.jpg": ["brand:gucci"],
    "brand-gucci-3.jpg": ["brand:gucci"],
    "brand-burberry-1.jpg": ["brand:burberry"],
    "brand-burberry-2.jpg": ["brand:burberry"],
    "brand-burberry-3.jpg": ["brand:burberry"],
    "brand-chanel-1.jpg": ["brand:chanel"],
    "brand-chanel-2.jpg": ["brand:chanel"],
    "brand-chanel-3.jpg": ["brand:chanel"],
    "brand-arcteryx-1.jpg": ["brand:arcteryx"],
    "brand-arcteryx-2.jpg": ["brand:arcteryx"],
    "brand-arcteryx-3.jpg": ["brand:arcteryx"],
    "brand-paul-smith-1.jpg": ["brand:paul-smith"],
    "brand-paul-smith-2.jpg": ["brand:paul-smith"],
    "brand-paul-smith-3.jpg": ["brand:paul-smith"],
    "brand-belstaff-1.jpg": ["brand:belstaff"],
    "brand-belstaff-2.jpg": ["brand:belstaff"],
    "brand-belstaff-3.jpg": ["brand:belstaff"],
    "brand-galvin-green-1.jpg": ["brand:galvin-green"],
    "brand-galvin-green-2.jpg": ["brand:galvin-green"],
    "brand-galvin-green-3.jpg": ["brand:galvin-green"],
    "brand-christopher-ward-1.jpg": ["brand:christopher-ward"],
    "brand-christopher-ward-2.jpg": ["brand:christopher-ward"],
    "brand-christopher-ward-3.jpg": ["brand:christopher-ward"],
    "brand-london-undercover-1.jpg": ["brand:london-undercover"],
    "brand-london-undercover-2.jpg": ["brand:london-undercover"],
    "brand-london-undercover-3.jpg": ["brand:london-undercover"],
}

SHOP_SLOTS = {
    n for n in SLOT_THEMES if n.startswith("shop-") or n.startswith("brand-")
}

# Homepage apparel rails — never crop shoe/bag close-ups into these.
CLOTHING_SLOTS = {
    n
    for n in SLOT_THEMES
    if n.startswith("rot-luxury-") or n.startswith("rot-cloth-")
}

# Hero: B&W London skyline panoramas (not product photography).
# Homepage "London to Your Door" uses a locked creative at
# public/banners/hero-london-door.jpg (+ t/ m/) — never rotated here.
HERO_LONDON_SLOTS = {n for n in SLOT_THEMES if n.startswith("rot-hero-")}
FIXED_HOME_HERO = "hero-london-door.jpg"
assert FIXED_HOME_HERO not in SLOT_THEMES, "locked home hero must not be in SLOT_THEMES"

# Legacy rot-event-* pool (shop / secondary rails). Homepage "Now in London"
# is locked at public/banners/event-now-london.jpg (+ t/ m/).
EVENT_EDIT_SLOTS = {n for n in SLOT_THEMES if n.startswith("rot-event-")}
FIXED_EVENT_BANNER = "event-now-london.jpg"
assert FIXED_EVENT_BANNER not in SLOT_THEMES, "locked event banner must not be in SLOT_THEMES"

# Homepage watches rail uses locked Christopher Ward C12 Loco open-balance creative.
FIXED_WATCH_BANNER = "watches-bel-canto.jpg"
assert FIXED_WATCH_BANNER not in SLOT_THEMES, "locked watch banner must not be in SLOT_THEMES"

# Homepage 100 Collection banner — locked Gucci Primavera hero.
FIXED_COLLECTION_100_BANNER = "collection-100-gucci.jpg"
assert FIXED_COLLECTION_100_BANNER not in SLOT_THEMES, "locked collection-100 banner must not be in SLOT_THEMES"

# Homepage bags rail — locked Chanel Spring 2018 campaign creative.
FIXED_BAG_BANNER = "bags-chanel-campaign.jpg"
assert FIXED_BAG_BANNER not in SLOT_THEMES, "locked bag banner must not be in SLOT_THEMES"

# Homepage shoes rail — locked fur-mule creative.
FIXED_SHOES_BANNER = "shoes-fur-mule.jpg"
assert FIXED_SHOES_BANNER not in SLOT_THEMES, "locked shoes banner must not be in SLOT_THEMES"

# Homepage luxury / Heritage & Modern rail — locked Flight Mode creative.
FIXED_LUXURY_BANNER = "luxury-heritage-modern.jpg"
assert FIXED_LUXURY_BANNER not in SLOT_THEMES, "locked luxury banner must not be in SLOT_THEMES"

# Homepage accessories / The Finishing Edit — locked Chanel N°5 signatures creative.
FIXED_ACCESSORIES_BANNER = "accessories-finishing-edit.jpg"
assert FIXED_ACCESSORIES_BANNER not in SLOT_THEMES, "locked accessories banner must not be in SLOT_THEMES"

# Christopher Ward brand page top banner — locked moonphase creative.
FIXED_CW_BRAND_BANNER = "brand-christopher-ward-moonphase.jpg"
assert FIXED_CW_BRAND_BANNER not in SLOT_THEMES, "locked CW brand banner must not be in SLOT_THEMES"

# Chanel brand heroes — locked creatives (watches vs bags/shoes/accessories).
FIXED_CHANEL_WATCH_BANNER = "brand-chanel-premiere.jpg"
FIXED_CHANEL_BRAND_BANNER = "brand-chanel-como-bag.jpg"
assert FIXED_CHANEL_WATCH_BANNER not in SLOT_THEMES, "locked Chanel watch banner must not be in SLOT_THEMES"
assert FIXED_CHANEL_BRAND_BANNER not in SLOT_THEMES, "locked Chanel brand banner must not be in SLOT_THEMES"

# Burberry brand hero — locked scarf campaign creative.
FIXED_BURBERRY_BRAND_BANNER = "brand-burberry-scarf.jpg"
assert FIXED_BURBERRY_BRAND_BANNER not in SLOT_THEMES, "locked Burberry brand banner must not be in SLOT_THEMES"

# Prada brand hero — locked Linea Rossa campaign creative.
FIXED_PRADA_BRAND_BANNER = "brand-prada-linea-rossa.jpg"
assert FIXED_PRADA_BRAND_BANNER not in SLOT_THEMES, "locked Prada brand banner must not be in SLOT_THEMES"

# Arc'teryx brand hero — locked Who We Are ridge creative.
FIXED_ARC_BRAND_BANNER = "brand-arcteryx-ridge.jpg"
assert FIXED_ARC_BRAND_BANNER not in SLOT_THEMES, "locked Arc'teryx brand banner must not be in SLOT_THEMES"

# Gucci handbags brand hero — locked Primavera / GG Marmont bedroom creative.
FIXED_GUCCI_BAGS_BRAND_BANNER = "brand-gucci-handbags.jpg"
assert FIXED_GUCCI_BAGS_BRAND_BANNER not in SLOT_THEMES, "locked Gucci bags brand banner must not be in SLOT_THEMES"

# Dior bags brand hero — locked All Bags forest bench creative.
FIXED_DIOR_BAGS_BRAND_BANNER = "brand-dior-bags.jpg"
assert FIXED_DIOR_BAGS_BRAND_BANNER not in SLOT_THEMES, "locked Dior bags brand banner must not be in SLOT_THEMES"

# Dior men's RTW brand hero — locked all-ready-to-wear boat campaign.
FIXED_DIOR_MENS_RTW_BRAND_BANNER = "brand-dior-mens-rtw.jpg"
assert FIXED_DIOR_MENS_RTW_BRAND_BANNER not in SLOT_THEMES, "locked Dior mens RTW brand banner must not be in SLOT_THEMES"

# Dior women's RTW brand hero — locked all-ready-to-wear grass campaign.
FIXED_DIOR_WOMENS_RTW_BRAND_BANNER = "brand-dior-womens-rtw.jpg"
assert FIXED_DIOR_WOMENS_RTW_BRAND_BANNER not in SLOT_THEMES, "locked Dior womens RTW brand banner must not be in SLOT_THEMES"

# Dior accessories brand hero — locked necklaces / Rose des Vents campaign.
FIXED_DIOR_ACCESSORIES_BRAND_BANNER = "brand-dior-accessories.jpg"
assert FIXED_DIOR_ACCESSORIES_BRAND_BANNER not in SLOT_THEMES, "locked Dior accessories brand banner must not be in SLOT_THEMES"

# Dior watches brand hero — locked All Pieces / La D de Dior pastel campaign.
FIXED_DIOR_WATCHES_BRAND_BANNER = "brand-dior-watches.jpg"
assert FIXED_DIOR_WATCHES_BRAND_BANNER not in SLOT_THEMES, "locked Dior watches brand banner must not be in SLOT_THEMES"

# Locked homepage / brand creatives — never rotated or dropped from manifest.
LOCKED_BANNERS = {
    FIXED_HOME_HERO,
    FIXED_EVENT_BANNER,
    FIXED_WATCH_BANNER,
    FIXED_COLLECTION_100_BANNER,
    FIXED_BAG_BANNER,
    FIXED_SHOES_BANNER,
    FIXED_LUXURY_BANNER,
    FIXED_ACCESSORIES_BANNER,
    FIXED_CW_BRAND_BANNER,
    FIXED_CHANEL_WATCH_BANNER,
    FIXED_CHANEL_BRAND_BANNER,
    FIXED_BURBERRY_BRAND_BANNER,
    FIXED_PRADA_BRAND_BANNER,
    FIXED_ARC_BRAND_BANNER,
    FIXED_GUCCI_BAGS_BRAND_BANNER,
    FIXED_DIOR_BAGS_BRAND_BANNER,
    FIXED_DIOR_MENS_RTW_BRAND_BANNER,
    FIXED_DIOR_WOMENS_RTW_BRAND_BANNER,
    FIXED_DIOR_ACCESSORIES_BRAND_BANNER,
    FIXED_DIOR_WATCHES_BRAND_BANNER,
}

# Curated free London panoramas (Wikimedia / Unsplash) — converted to B&W on export.
# Mood reference: Andrew Prokos Parliament & Big Ben skyline (style only; not copied).
LONDON_BW_SOURCES: list[dict[str, str]] = [
    {
        "id": "london-parliament-thames",
        "url": "https://upload.wikimedia.org/wikipedia/commons/7/7e/Big_Ben_and_houses_of_parliament_London.jpg",
    },
    {
        "id": "london-westminster-dome",
        "url": "https://commons.wikimedia.org/wiki/Special:FilePath/Palace_of_Westminster_from_the_dome_on_Methodist_Central_Hall.jpg?width=2560",
    },
    {
        "id": "london-tower-bridge",
        "url": "https://commons.wikimedia.org/wiki/Special:FilePath/Tower_Bridge_from_Shad_Thames.jpg?width=2560",
    },
    {
        "id": "london-westminster-bridge",
        "url": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?auto=format&fit=crop&w=2800&q=85",
    },
    {
        "id": "london-thames-dusk",
        "url": "https://images.unsplash.com/photo-1486299267070-83823f5448dd?auto=format&fit=crop&w=2800&q=85",
    },
    {
        "id": "london-big-ben-river",
        "url": "https://images.unsplash.com/photo-1486297678162-eb2a19b0a32d?auto=format&fit=crop&w=2800&q=85",
    },
    {
        "id": "london-eye-thames",
        "url": "https://images.unsplash.com/photo-1505761671935-60b3a7427bad?auto=format&fit=crop&w=2800&q=85",
    },
]

# Sports imagery stays on sports / outdoor rails and Galvin Green chips only.
# Arc'teryx brand hero is locked (brand-arcteryx-ridge.jpg) — do not rotate
# unused brand-arcteryx-{1,2,3} slots.
SPORTS_SLOTS = {
    n
    for n in SLOT_THEMES
    if n.startswith("rot-golf-")
    or n.startswith("rot-cycle-")
    or n.startswith("rot-swim-")
    or n.startswith("rot-run-")
    or n.startswith("rot-tennis-")
    or n.startswith("shop-golf-")
    or n.startswith("shop-run-")
    or n.startswith("shop-shoe-train-")
    or n.startswith("brand-galvin-green-")
}

# Product stills — shoes / bags / accessories / watches must stay readable after the PC crop.
PRODUCT_SLOTS = {
    n
    for n in SLOT_THEMES
    if n.startswith("rot-shoe-")
    or n.startswith("rot-bag-")
    or n.startswith("rot-acc-")
    or n.startswith("rot-watch-")
    or n.startswith("rot-cw-")
    or n.startswith("shop-shoe-")
    or n.startswith("shop-bag-")
}

WATCH_SLOTS = {
    n
    for n in SLOT_THEMES
    if n.startswith("rot-watch-") or n.startswith("rot-cw-")
}

BRAND_MATCH: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    # id prefixes, blob needles
    "gucci": (("gc-",), ("gucci", "구찌")),
    "burberry": (("bb-",), ("burberry", "버버리")),
    "chanel": (("ch-",), ("chanel", "샤넬")),
    "arcteryx": (("axa-", "ax-"), ("arcteryx", "arc'teryx", "아크테릭스")),
    "paul-smith": (("ps-",), ("paul smith", "paul-smith", "폴 스미스")),
    "belstaff": (("bs-",), ("belstaff", "벨스타프")),
    "galvin-green": (("gg-",), ("galvin", "갈빈")),
    "christopher-ward": (("cw-",), ("christopher ward", "christopher-ward", "크리스토퍼")),
    "london-undercover": (("lu-",), ("london undercover", "london-undercover", "언더커버")),
}


def week_seed(now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    return int(now.strftime("%G%V"))  # ISO year+week


def load_catalog(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    if path.suffix == ".ts":
        return load_catalog_ts(path)
    data = json.loads(path.read_text())
    if isinstance(data, list):
        rows = [p for p in data if isinstance(p, dict)]
    elif isinstance(data, dict) and isinstance(data.get("products"), list):
        rows = [p for p in data["products"] if isinstance(p, dict)]
    else:
        return []
    # Christopher Ward raw feed uses sku + absolute image URLs
    out: list[dict] = []
    for p in rows:
        pid = str(p.get("id") or "")
        if not pid and p.get("sku"):
            p = {
                **p,
                "id": f"cw-{p['sku']}",
                "brand": "Christopher Ward",
            }
        out.append(p)
    return out


def load_catalog_ts(path: Path) -> list[dict]:
    """Best-effort extract of product image paths from hand/generated TS catalogues."""
    text = path.read_text()
    out: list[dict] = []
    # Split on product-like id fields
    parts = re.split(r'\bid:\s*"', text)
    for part in parts[1:]:
        m = re.match(r'([^"]+)"', part)
        if not m:
            continue
        pid = m.group(1)
        block = part[:4000]
        imgs = re.findall(r'(/products/[A-Za-z0-9._/-]+\.jpe?g)', block)
        seen: set[str] = set()
        uniq: list[str] = []
        for img in imgs:
            if img in seen:
                continue
            seen.add(img)
            uniq.append(img)
        if not uniq:
            continue
        brand = ""
        if pid.startswith("lu-") or "london" in pid:
            brand = "london undercover"
        out.append(
            {
                "id": pid,
                "image": uniq[0],
                "images": uniq[:8],
                "hoverImage": uniq[1] if len(uniq) > 1 else uniq[0],
                "brand": brand,
            }
        )
    return out


def product_images(product: dict, *, prefer_on_model: bool = True) -> list[str]:
    """Gallery paths. Clothing lookbooks prefer hover/2; product stills keep packshot/1."""
    out: list[str] = []
    seen: set[str] = set()

    def add(src: object) -> None:
        if not isinstance(src, str):
            return
        if not (src.startswith("/products/") or src.startswith("https://")):
            return
        if src in seen:
            return
        seen.add(src)
        out.append(src)

    for key in ("hoverImage", "image"):
        add(product.get(key))
    for src in product.get("images") or []:
        add(src)
    if prefer_on_model and len(out) >= 2:
        # On-model is rarely the first packshot — prefer [1:] when available
        return out[1:] + out[:1]
    return out


def product_blob(product: dict) -> str:
    return " ".join(
        [
            str(product.get("category") or ""),
            str(product.get("subcategory") or ""),
            " ".join(product.get("tags") or []),
            " ".join(product.get("chCollections") or []),
            " ".join(product.get("bbCollections") or []),
            " ".join(product.get("gcCollections") or []),
            " ".join(product.get("axCollections") or []),
            str(product.get("brand") or ""),
            str(product.get("nameKo") or ""),
            str(product.get("name") or ""),
            str(product.get("id") or ""),
            str(product.get("sku") or ""),
        ]
    ).lower()


def is_clothing_product(product: dict) -> bool:
    blob = product_blob(product)
    if any(
        x in blob
        for x in (
            "children",
            "kids",
            "baby",
            "infant",
            "bloomers",
            "childrens",
            "키즈",
            "아동",
        )
    ):
        return False
    if any(
        x in blob
        for x in (
            "bag",
            "handbag",
            "가방",
            "shoe",
            "sneaker",
            "boot",
            "loafer",
            "heel",
            "watch",
            "시계",
            "wallet",
            "sunglass",
            "fragrance",
            "perfume",
            "makeup",
            "lipstick",
            "jewellery",
            "jewelry",
            "earring",
            "necklace",
            "bracelet",
            "scarf",
            "umbrella",
            "rug",
        )
    ):
        return False
    return any(
        x in blob
        for x in (
            "rtw",
            "clothing",
            "ready-to-wear",
            "의류",
            "jacket",
            "coat",
            "dress",
            "sweater",
            "shirt",
            "hoodie",
            "trench",
            "knit",
            "blouse",
            "cape",
            "parka",
            "cardigan",
            "polo",
            "suit",
            "blazer",
            "outerwear",
            "가디건",
            "코트",
            "재킷",
            "원피스",
        )
    )


def is_sports_product(product: dict) -> bool:
    """True for golf / Arc'teryx / training — keep these off fashion homepage rails."""
    pid = str(product.get("id") or "").lower()
    if pid.startswith(("axa-", "ax-", "axg-", "axo-", "gg-")):
        return True
    blob = product_blob(product)
    return any(
        x in blob
        for x in (
            "golf",
            "골프",
            "galvin",
            "arcteryx",
            "arc'teryx",
            "아크테릭스",
            "running",
            "러너",
            "tennis",
            "swim",
            "cycling",
            "스포츠",
            "training shoe",
            "골프웨어",
        )
    )


def looks_logo_branded(product_id: str, img: str, product: dict | None = None) -> bool:
    """Heuristic: monogram / crest / check garments read as branded close-ups."""
    blob = f"{product_id} {img} {product_blob(product) if product else ''}".lower()
    return any(
        x in blob
        for x in (
            "logo",
            "monogram",
            "gg",
            "check",
            "horseferry",
            "interlocking",
            "crest",
            "embroider",
            "jacquard",
            "stripe",
            "zebra",
            "signature",
        )
    )


def is_luxury_fashion_id(pid: str) -> bool:
    return pid.lower().startswith(("gc-", "bb-", "ch-", "ps-"))


def theme_match(product: dict, themes: list[str]) -> bool:
    blob = product_blob(product)
    checks = {
        "luxury": any(
            x in blob
            for x in (
                "gucci",
                "버버리",
                "burberry",
                "chanel",
                "샤넬",
                "prada",
                "프라다",
                "luxury",
                "gc-",
                "bb-",
                "ch-",
                "pr-",
            )
        ),
        "fashion": any(
            x in blob
            for x in (
                "rtw",
                "clothing",
                "ready-to-wear",
                "의류",
                "jacket",
                "coat",
                "dress",
                "sweater",
                "shirt",
                "hoodie",
                "paul smith",
                "belstaff",
                "prada",
                "프라다",
            )
        )
        and not any(
            x in blob
            for x in (
                "arcteryx",
                "arc'teryx",
                "axa-",
                "galvin",
                "golf",
                "골프",
            )
        ),
        "street": any(x in blob for x in ("street", "hoodie", "tee", "sneaker", "trainer")),
        "bags": (
            str(product.get("category") or "").lower() == "bags"
            or any(
                x in blob
                for x in (
                    "handbag",
                    "가방",
                    "tote",
                    "backpack",
                    "clutch",
                    "crossbody",
                    "duffel",
                    "duffle",
                    "trolley",
                    "luggage",
                )
            )
        )
        and str(product.get("category") or "").lower()
        not in {"shoes", "watches", "accessories"},
        # Strict: shoe banners must only use category=shoes products.
        # Avoid substring traps like "shoe" in "horseshoe" or "heel" in "wheel".
        "shoes": str(product.get("category") or "").lower() == "shoes"
        and not any(
            x in blob
            for x in (
                "backpack",
                "handbag",
                "bucket hat",
                "bucket-hat",
                "모자",
                " hat",
                "hat ",
                "-hat",
            )
        ),
        "accessories": (
            any(
                x in blob
                for x in (
                    "accessor",
                    "jewellery",
                    "jewelry",
                    "sunglass",
                    "scarf",
                    "belt",
                    "wallet",
                    "지갑",
                    "악세서",
                    "주얼",
                    "necktie",
                    "tie ",
                    "glove",
                    "cufflink",
                    "keyring",
                    "keychain",
                    "cap",
                    "hat",
                )
            )
            and not any(
                x in blob
                for x in (
                    "fragrance",
                    "perfume",
                    "parfum",
                    "eau de",
                    "toilette",
                    "makeup",
                    "lipstick",
                    "beauty",
                    "skincare",
                    "향수",
                    "메이크업",
                    "크림",
                    "phone case",
                    "iphone",
                    "airpods",
                    "smartphone",
                    "폰케이스",
                    "basket",
                    "pastry",
                    "kitchen",
                    "homeware",
                    "candle",
                    "mug",
                    "shoe",
                    "sneaker",
                    "boot",
                    "loafer",
                    "sandal",
                    "heel",
                    "footwear",
                    "슈즈",
                    "bag",
                    "handbag",
                    "가방",
                    "jacket",
                    "coat",
                    "shirt",
                    "hoodie",
                )
            )
        ),
        # Strict: real watches only — never "Black Watch" tartan umbrellas or
        # jewellery that shares a "jewellery & watches" hub tag.
        "watches": (
            (
                str(product.get("category") or "").lower() == "watches"
                or str(product.get("id") or "").lower().startswith("cw-")
                or str(product.get("subcategory") or "")
                .lower()
                .startswith(("gc-watches", "ch-watches", "cw-"))
                or any(
                    str(c).lower().startswith(("gc-watches", "ch-watches", "cw-"))
                    for c in (
                        *(product.get("gcCollections") or []),
                        *(product.get("chCollections") or []),
                        *(product.get("tags") or []),
                    )
                )
            )
            and not any(
                x in blob
                for x in (
                    "umbrella",
                    "우산",
                    "parasol",
                    "black-watch-tartan",
                    "black_watch_tartan",
                    "watch-tartan",
                    "watch tartan",
                    "시계 타탄",
                )
            )
            and not (
                str(product.get("category") or "").lower() == "accessories"
                and not (
                    str(product.get("subcategory") or "")
                    .lower()
                    .startswith(("gc-watches", "ch-watches"))
                    or any(
                        str(c).lower().startswith("gc-watches")
                        for c in (product.get("gcCollections") or [])
                    )
                )
            )
            and not any(
                x in str(product.get("subcategory") or "").lower()
                for x in (
                    "jewellery",
                    "jewelry",
                    "gold-jewellery",
                    "silver-jewellery",
                    "fine-jewellery",
                )
            )
        ),
        "golf": any(x in blob for x in ("golf", "골프", "galvin")),
        "outdoor": any(
            x in blob for x in ("arc'teryx", "arcteryx", "outdoor", "running", "hike", "axa-", "ax-")
        ),
    }
    for t in themes:
        if t.startswith("brand:"):
            brand = t.split(":", 1)[1]
            if brand_match(product, brand):
                return True
            continue
        if checks.get(t, False):
            return True
    return False


def brand_match(product: dict, brand: str) -> bool:
    rules = BRAND_MATCH.get(brand)
    if not rules:
        return False
    prefixes, needles = rules
    pid = str(product.get("id") or "").lower()
    if any(pid.startswith(p) for p in prefixes):
        return True
    blob = product_blob(product)
    return any(n in blob for n in needles)


def is_likely_detail_frame(path: str) -> bool:
    """Later gallery stills are often fabric/hardware close-ups."""
    return bool(re.search(r"/(?:[4-9]|1[0-9])\.jpe?g(?:\?|$)", path.lower()))


def is_likely_on_model(path: str) -> bool:
    """Heuristic: gallery/hover frames and non-packshot filenames."""
    name = path.lower()
    if any(x in name for x in ("/1.jpg", "/thumb.jpg", "packshot", "still-life")):
        # still allow if it's a hover path elsewhere
        if "hover" in name:
            return True
        return False
    return True


def collect_candidates() -> tuple[dict[str, list[tuple[str, str]]], set[str], set[str]]:
    """theme → candidates, clothing product ids, sports product ids."""
    catalogs = [
        ROOT / "src/data/gc/gc-catalog.json",
        ROOT / "src/data/bb/bb-catalog.json",
        ROOT / "src/data/ch/ch-catalog.json",
        ROOT / "src/data/ax/ax-apparel-catalog.json",
        ROOT / "src/data/ax/ax-gear-catalog.json",
        ROOT / "src/data/gg/gg-catalog.json",
        ROOT / "src/data/ps/ps-catalog.json",
        ROOT / "src/data/bs/bs-catalog.json",
        ROOT / "src/data/cw/cw-catalog-raw.json",
        ROOT / "src/data/lu/lu-catalog.ts",
        ROOT / "src/data/pr/pr-catalog.json",
    ]
    themes = {
        "luxury",
        "fashion",
        "street",
        "bags",
        "shoes",
        "accessories",
        "watches",
        "golf",
        "outdoor",
        *[f"brand:{k}" for k in BRAND_MATCH],
    }
    by_theme: dict[str, list[tuple[str, str]]] = {t: [] for t in themes}
    clothing_ids: set[str] = set()
    sports_ids: set[str] = set()
    for path in catalogs:
        for product in load_catalog(path):
            pid = str(product.get("id") or "")
            if is_clothing_product(product):
                clothing_ids.add(pid)
            if is_sports_product(product):
                sports_ids.add(pid)
            look_imgs = product_images(product, prefer_on_model=True)
            look_imgs = [i for i in look_imgs if is_likely_on_model(i)] or look_imgs[:2]
            pack_imgs = product_images(product, prefer_on_model=False)
            pack_only = [
                i for i in pack_imgs if re.search(r"/1\.jpe?g(?:\?|$)", i.lower())
            ]
            pack_imgs = (pack_only or pack_imgs)[:2]
            if not look_imgs and not pack_imgs:
                continue
            # Watches: packshot dials. Everything else: campaign / lifestyle first.
            packshot_first_themes = {"watches"}
            for theme in list(by_theme):
                if not theme_match(product, [theme]):
                    continue
                if theme in packshot_first_themes:
                    imgs = pack_imgs or look_imgs
                else:
                    imgs = look_imgs or pack_imgs
                if not imgs:
                    imgs = pack_imgs or look_imgs
                for img in imgs[:4]:
                    by_theme[theme].append((pid, img))
    for theme, rows in by_theme.items():
        seen: set[str] = set()
        uniq = []
        for pid, img in rows:
            if img in seen:
                continue
            seen.add(img)
            uniq.append((pid, img))
        by_theme[theme] = uniq
        if uniq or theme.startswith("brand:"):
            print(f"candidates {theme}={len(uniq)}", flush=True)
    print(f"clothing_ids={len(clothing_ids)} sports_ids={len(sports_ids)}", flush=True)
    return by_theme, clothing_ids, sports_ids


def fetch_image(rel: str) -> Image.Image | None:
    from io import BytesIO

    if rel.startswith("https://"):
        try:
            req = urllib.request.Request(rel, headers={"User-Agent": UA, "Accept": "image/*"})
            with urllib.request.urlopen(req, timeout=45) as r:
                data = r.read()
            if len(data) >= 2000:
                return Image.open(BytesIO(data)).convert("RGB")
        except Exception:
            return None
        return None

    urls = [
        f"{MEDIA}{rel}",
        f"https://raw.githubusercontent.com/puruemae1-cloud/briq/product-images/public{rel}",
    ]
    local = ROOT / "public" / rel.lstrip("/")
    if local.is_file() and local.stat().st_size > 2000:
        try:
            return Image.open(local).convert("RGB")
        except Exception:
            pass
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "image/*"})
            with urllib.request.urlopen(req, timeout=45) as r:
                data = r.read()
            if len(data) < 2000:
                continue
            return Image.open(BytesIO(data)).convert("RGB")
        except Exception:
            continue
    return None


def to_black_and_white(im: Image.Image) -> Image.Image:
    """Match Briq hero tone: rich B&W with slight contrast lift."""
    from PIL import ImageEnhance, ImageOps

    bw = ImageOps.grayscale(im.convert("RGB")).convert("RGB")
    bw = ImageEnhance.Contrast(bw).enhance(1.12)
    bw = ImageEnhance.Brightness(bw).enhance(0.96)
    return bw


def fetch_london_source(entry: dict[str, str]) -> Image.Image | None:
    url = entry.get("url") or ""
    if not url:
        return None
    cache_dir = ROOT / "public" / "banners" / "_cache" / "london-bw"
    cache_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", entry.get("id") or "london")[:80]
    cache_path = cache_dir / f"{safe}.jpg"
    if cache_path.is_file() and cache_path.stat().st_size > 20_000:
        try:
            return to_black_and_white(Image.open(cache_path).convert("RGB"))
        except Exception:
            pass
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = resp.read()
        if len(data) < 5000:
            return None
        cache_path.write_bytes(data)
        return to_black_and_white(Image.open(cache_path).convert("RGB"))
    except Exception as e:
        print(f"  london fetch fail {entry.get('id')}: {e}", flush=True)
        return None


def pick_london_for_slot(
    slot: str, seed: int, used: set[str]
) -> tuple[str, str, Image.Image] | None:
    digest = hashlib.sha1(f"{seed}:{slot}:london".encode()).hexdigest()
    slot_rng = random.Random(digest)
    order = list(LONDON_BW_SOURCES)
    slot_rng.shuffle(order)
    # Prefer wide panoramas for the PC hero strip (aspect ≥ ~1.4)
    scored: list[tuple[float, dict[str, str], Image.Image]] = []
    for entry in order:
        sid = entry["id"]
        if sid in used:
            continue
        im = fetch_london_source(entry)
        if im is None:
            continue
        ar = aspect_ratio(im)
        scored.append((ar, entry, im))
    scored.sort(key=lambda x: (-x[0], x[1]["id"]))
    for ar, entry, im in scored:
        if ar < 1.2 and any(a >= 1.2 for a, _, _ in scored):
            continue
        return entry["id"], f"london-bw:{entry['id']}", im
    if scored:
        entry, im = scored[0][1], scored[0][2]
        return entry["id"], f"london-bw:{entry['id']}", im
    for entry in order:
        im = fetch_london_source(entry)
        if im is not None:
            return entry["id"], f"london-bw:{entry['id']}", im
    return None


def pick_for_slot(
    slot: str,
    themes: list[str],
    pool: dict[str, list[tuple[str, str]]],
    rng: random.Random,
    used: set[str],
    seed: int,
    clothing_ids: set[str] | None = None,
    sports_ids: set[str] | None = None,
) -> list[tuple[str, str]]:
    if slot in HERO_LONDON_SLOTS:
        return []  # handled separately via pick_london_for_slot
    options: list[tuple[str, str]] = []
    for t in themes:
        options.extend(pool.get(t) or [])
    options = [o for o in options if o[1] not in used]
    # Sports products only feed sports / outdoor / golf brand slots.
    if sports_ids and slot not in SPORTS_SLOTS:
        options = [o for o in options if o[0] not in sports_ids]
    # Event edit: never clothing
    if slot in EVENT_EDIT_SLOTS and clothing_ids:
        options = [o for o in options if o[0] not in clothing_ids]
    if slot in CLOTHING_SLOTS and clothing_ids:
        clothed = [o for o in options if o[0] in clothing_ids]
        options = clothed
    if slot in WATCH_SLOTS:
        # Hard ban: London Undercover "Black Watch" tartan umbrellas etc.
        options = [
            o
            for o in options
            if not any(
                x in f"{o[0]} {o[1]}".lower()
                for x in (
                    "umbrella",
                    "우산",
                    "parasol",
                    "watch-tartan",
                    "watch_tartan",
                    "watch tartan",
                    "lu-",
                )
            )
        ]
    brand_only = any(t.startswith("brand:") for t in themes)
    if not options and not brand_only:
        # fallback — event stays non-apparel; shoe/bag product slots stay in-theme
        if slot in EVENT_EDIT_SLOTS:
            for t in ("watches", "shoes", "accessories", "bags"):
                options.extend(pool.get(t) or [])
        elif slot.startswith("rot-shoe-") or slot.startswith("shop-shoe-"):
            options.extend(pool.get("shoes") or [])
        elif slot.startswith("rot-bag-") or slot.startswith("shop-bag-"):
            options.extend(pool.get("bags") or [])
        else:
            for t in ("luxury", "fashion"):
                options.extend(pool.get(t) or [])
        options = [o for o in options if o[1] not in used]
        if sports_ids and slot not in SPORTS_SLOTS:
            options = [o for o in options if o[0] not in sports_ids]
        if slot in EVENT_EDIT_SLOTS and clothing_ids:
            options = [o for o in options if o[0] not in clothing_ids]
        if slot in CLOTHING_SLOTS and clothing_ids:
            options = [o for o in options if o[0] in clothing_ids]
    if not options:
        return []
    # Deterministic weekly shuffle per slot, then prefer wider local photos.
    digest = hashlib.sha1(f"{seed}:{slot}".encode()).hexdigest()
    slot_rng = random.Random(digest)
    slot_rng.shuffle(options)
    if slot in EVENT_EDIT_SLOTS:
        # Rotate themes so weekly edit mixes watches / shoes / bags / accessories.
        theme_order = ["watches", "shoes", "accessories", "bags"]
        m = re.search(r"(\d+)", slot)
        slot_i = int(m.group(1)) if m else 1
        preferred = theme_order[(slot_i - 1 + seed) % len(theme_order)]
        pref_set = set(pool.get(preferred) or [])
        pref = [o for o in options if o in pref_set]
        rest = [o for o in options if o not in pref_set]
        options = pref + rest
        options.sort(
            key=lambda o: (
                0 if o in pref_set else 1,
                0 if re.search(r"/1\.jpe?g$", o[1], re.I) else 1,
            )
        )
    elif slot in CLOTHING_SLOTS:
        # Prefer on-model / campaign gallery frames over packshot /1.jpg
        options.sort(
            key=lambda o: (
                0 if is_likely_on_model(o[1]) else 2,
                0 if re.search(r"/[23]\.jpe?g$", o[1], re.I) else 1,
                1 if re.search(r"/1\.jpe?g$", o[1], re.I) else 0,
                0 if "/look" in o[1].lower() else 1,
            )
        )
    elif slot in PRODUCT_SLOTS:
        # Shoes / bags / accessories: lifestyle over grey packshots
        options.sort(
            key=lambda o: (
                0 if is_likely_on_model(o[1]) else 2,
                1 if re.search(r"/1\.jpe?g$", o[1], re.I) else 0,
                1 if is_likely_detail_frame(o[1]) else 0,
                0 if re.search(r"/[23]\.jpe?g$", o[1], re.I) else 1,
            )
        )
    return options


def slot_kind(slot: str) -> str:
    if slot in SHOP_SLOTS:
        return "shop"
    if slot.startswith("rot-hero-"):
        return "hero"
    return "look"


def slot_vertical_bias(slot: str) -> str:
    # Watches stay product-centred; shoes/bags/acc use torso/lower for lifestyle.
    if slot in WATCH_SLOTS:
        return "product"
    if slot in PRODUCT_SLOTS:
        return "torso"
    return "torso"


def clothing_source_ok(source, img: str, *, luxury_only: bool = False) -> tuple[bool, str]:
    """Accept natural on-model / campaign outfit frames; reject headshot macros."""
    del luxury_only  # kept for call-site compat; lifestyle faces are allowed
    ratio = aspect_ratio(source)
    if ratio < 0.50:
        return False, f"too-tall {ratio:.2f}"
    if is_extreme_closeup(source):
        return False, "extreme-closeup"
    if is_likely_detail_frame(img):
        return False, "detail-frame"
    if is_face_dominant(source):
        return False, "face-dominant"
    fill = subject_fill_ratio(source)
    if fill > 0.92:
        return False, f"macro-fill {fill:.2f}"
    if fill < 0.06:
        return False, f"empty {fill:.2f}"
    return True, "ok"


def product_source_ok(source, img: str) -> tuple[bool, str]:
    """Watch / flat stills — full product readable, no outfit lookbooks."""
    ratio = aspect_ratio(source)
    low = img.lower()
    if any(x in low for x in ("parfum", "perfume", "fragrance", "lipstick", "makeup")):
        return False, "beauty-not-acc"
    if is_likely_detail_frame(img):
        return False, "detail-frame"
    if ratio < 0.55:
        return False, f"too-tall {ratio:.2f}"
    if is_extreme_closeup(source):
        return False, "extreme-closeup"
    if is_face_dominant(source) or has_on_model_face(source):
        return False, "outfit-lookbook"
    fill = subject_fill_ratio(source)
    if fill < 0.10:
        return False, f"empty {fill:.2f}"
    if fill > 0.88:
        return False, f"macro-fill {fill:.2f}"
    return True, "ok"


def lifestyle_product_source_ok(source, img: str) -> tuple[bool, str]:
    """Shoes / bags / accessories: campaign, on-model, or staged still-life."""
    ratio = aspect_ratio(source)
    low = img.lower()
    if any(x in low for x in ("parfum", "perfume", "fragrance", "lipstick", "makeup")):
        return False, "beauty-not-acc"
    if is_likely_detail_frame(img):
        return False, "detail-frame"
    if ratio < 0.48:
        return False, f"too-tall {ratio:.2f}"
    if is_extreme_closeup(source):
        return False, "extreme-closeup"
    if is_face_dominant(source):
        return False, "face-dominant"
    fill = subject_fill_ratio(source)
    if fill < 0.06:
        return False, f"empty {fill:.2f}"
    if fill > 0.94:
        return False, f"macro-fill {fill:.2f}"
    return True, "ok"


def event_edit_source_ok(source, img: str, pid: str, clothing_ids: set[str]) -> tuple[bool, str]:
    """Now in London: watches / shoes / accessories / bags — no apparel."""
    if pid in clothing_ids:
        return False, "clothing"
    if "watch" in img.lower() or pid.lower().startswith("cw-"):
        ok, why = product_source_ok(source, img)
        if ok:
            return True, "ok"
        ratio = aspect_ratio(source)
        if ratio >= 0.55 and not is_face_dominant(source):
            return True, "ok-watch"
        return False, why
    return lifestyle_product_source_ok(source, img)


def referenced_slots() -> list[str]:
    text = ""
    for rel in (
        "src/data/home-banners.ts",
        "src/data/shop-heroes.ts",
        "src/data/brand-heroes.ts",
        "src/app/shop/page.tsx",
        "src/components/Collection100.tsx",
    ):
        p = ROOT / rel
        if p.is_file():
            text += p.read_text()
    names = sorted(set(re.findall(r"/banners/(?!m/|t/)([A-Za-z0-9._-]+\.jpg)", text)))
    # Brand heroes are always refreshed even if only referenced via TS maps
    for n in SLOT_THEMES:
        if n.startswith("brand-"):
            names.append(n)
    return sorted(set(names))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="Only refresh N slots (debug)")
    ap.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Override week seed (force a new shuffle mid-week)",
    )
    ap.add_argument(
        "--only",
        type=str,
        default="",
        help="Only refresh slots whose filename contains this substring",
    )
    ap.add_argument(
        "--all",
        action="store_true",
        help="Refresh every SLOT_THEMES entry (not just sports). Opt-in only.",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    seed = args.seed or week_seed()
    rng = random.Random(seed)
    print(f"week_seed={seed}", flush=True)

    slots = [s for s in referenced_slots() if s in SLOT_THEMES]
    # Default: sports rails only — locked homepage/brand creatives never rotate.
    if not args.all and not args.only:
        slots = [s for s in slots if s in SPORTS_SLOTS]
        print(
            f"mode=sports-only locked={len(LOCKED_BANNERS)} sports_slots={len(SPORTS_SLOTS)}",
            flush=True,
        )
    elif args.all:
        print("mode=all (emergency full refresh)", flush=True)
    if args.only:
        needles = [n.strip() for n in args.only.split(",") if n.strip()]
        slots = [s for s in slots if any(n in s for n in needles)]
    if args.limit:
        slots = slots[: args.limit]
    print(f"slots={len(slots)}", flush=True)

    pool, clothing_ids, sports_ids = collect_candidates()
    used: set[str] = set()
    prev_slots: dict = {}
    if MANIFEST.is_file():
        try:
            prev_slots = dict(json.loads(MANIFEST.read_text()).get("slots") or {})
        except Exception:
            prev_slots = {}

    new_slots: dict = {}
    BANNER_DIR.mkdir(parents=True, exist_ok=True)
    MOBILE_DIR.mkdir(parents=True, exist_ok=True)
    TABLET_DIR.mkdir(parents=True, exist_ok=True)

    ok = fail = 0
    for i, slot in enumerate(slots, start=1):
        themes = SLOT_THEMES.get(slot) or ["luxury"]
        kind = slot_kind(slot)
        bias = slot_vertical_bias(slot)

        # --- Homepage hero: B&W London panoramas ---
        if slot in HERO_LONDON_SLOTS:
            london = pick_london_for_slot(slot, seed, used)
            if london is None:
                print(f"{i}/{len(slots)} {slot} FAIL no-london-source", flush=True)
                fail += 1
                continue
            pid, img, source = london
            if args.dry_run:
                print(
                    f"{i}/{len(slots)} {slot} <- {pid} {img} "
                    f"({source.size} {aspect_ratio(source):.2f})",
                    flush=True,
                )
                used.add(pid)
                ok += 1
                continue
            try:
                focal = export_banner_set(
                    source,
                    desktop_path=BANNER_DIR / slot,
                    tablet_path=TABLET_DIR / slot,
                    mobile_path=MOBILE_DIR / slot,
                    shop=False,
                    kind="hero",
                    require_face=False,
                    vertical_bias="torso",
                )
            except Exception as e:
                print(f"{i}/{len(slots)} {slot} FAIL crop {e}", flush=True)
                fail += 1
                continue
            used.add(pid)
            new_slots[slot] = {
                "sourceProductId": pid,
                "sourceImage": img,
                "focal": focal.css,
                "shop": False,
                "kind": "hero",
                "tone": "bw-london",
                "sourceAspect": round(aspect_ratio(source), 3),
            }
            ok += 1
            print(
                f"{i}/{len(slots)} {slot} ok hero-london {source.size[0]}x{source.size[1]} "
                f"focal={focal.css} src={img}",
                flush=True,
            )
            continue

        picks = pick_for_slot(
            slot, themes, pool, rng, used, seed, clothing_ids, sports_ids
        )
        if not picks:
            print(f"{i}/{len(slots)} {slot} FAIL no-candidate", flush=True)
            fail += 1
            continue
        # PC look/hero banners are panoramic — prefer wide outfit / product
        # stills; reject face-only headshots and empty grey product frames.
        tries = 100 if kind in {"look", "hero"} or slot in EVENT_EDIT_SLOTS else 12
        chosen: tuple[str, str, Image.Image] | None = None
        last_err = ""
        for pid, img in picks[:tries]:
            source = fetch_image(img)
            if source is None:
                last_err = f"fetch {img}"
                continue
            ratio = aspect_ratio(source)
            if slot in EVENT_EDIT_SLOTS:
                ok_src, why = event_edit_source_ok(source, img, pid, clothing_ids)
                if not ok_src:
                    last_err = f"{why} {ratio:.2f} {img}"
                    continue
                source = to_black_and_white(source)
            elif slot in CLOTHING_SLOTS:
                ok_src, why = clothing_source_ok(
                    source, img, luxury_only=slot.startswith("rot-luxury-")
                )
                if not ok_src:
                    last_err = f"{why} {ratio:.2f} {img}"
                    continue
            elif slot in PRODUCT_SLOTS:
                if slot in WATCH_SLOTS:
                    ok_src, why = product_source_ok(source, img)
                else:
                    ok_src, why = lifestyle_product_source_ok(source, img)
                if not ok_src:
                    last_err = f"{why} {ratio:.2f} {img}"
                    continue
            elif kind in {"look", "hero"} and ratio < 0.55:
                last_err = f"too-tall {ratio:.2f} {img}"
                continue
            chosen = (pid, img, source)
            break
        if chosen is None:
            print(f"{i}/{len(slots)} {slot} FAIL {last_err or 'no-image'}", flush=True)
            fail += 1
            continue
        pid, img, source = chosen
        if args.dry_run:
            print(
                f"{i}/{len(slots)} {slot} <- {pid} {img} ({source.size} {aspect_ratio(source):.2f})",
                flush=True,
            )
            used.add(img)
            ok += 1
            continue
        event_bias = "product" if slot in EVENT_EDIT_SLOTS else bias
        try:
            focal = export_banner_set(
                source,
                desktop_path=BANNER_DIR / slot,
                tablet_path=TABLET_DIR / slot,
                mobile_path=MOBILE_DIR / slot,
                shop=kind == "shop",
                kind=kind,
                require_face=False,
                vertical_bias=event_bias,
            )
        except Exception as e:
            recovered = False
            if kind in {"look", "hero"} or slot in EVENT_EDIT_SLOTS:
                for pid2, img2 in picks[:tries]:
                    if img2 == img:
                        continue
                    source2 = fetch_image(img2)
                    if source2 is None:
                        continue
                    if slot in EVENT_EDIT_SLOTS:
                        ok_src, _ = event_edit_source_ok(
                            source2, img2, pid2, clothing_ids
                        )
                        if not ok_src:
                            continue
                        source2 = to_black_and_white(source2)
                    elif slot in CLOTHING_SLOTS:
                        ok_src, _ = clothing_source_ok(
                            source2,
                            img2,
                            luxury_only=slot.startswith("rot-luxury-"),
                        )
                        if not ok_src:
                            continue
                    elif slot in PRODUCT_SLOTS:
                        if slot in WATCH_SLOTS:
                            ok_src, _ = product_source_ok(source2, img2)
                        else:
                            ok_src, _ = lifestyle_product_source_ok(source2, img2)
                        if not ok_src:
                            continue
                    try:
                        focal = export_banner_set(
                            source2,
                            desktop_path=BANNER_DIR / slot,
                            tablet_path=TABLET_DIR / slot,
                            mobile_path=MOBILE_DIR / slot,
                            shop=False,
                            kind=kind,
                            require_face=False,
                            vertical_bias=event_bias,
                        )
                        pid, img, source = pid2, img2, source2
                        recovered = True
                        break
                    except Exception:
                        continue
            if not recovered:
                print(f"{i}/{len(slots)} {slot} FAIL crop {e}", flush=True)
                fail += 1
                continue
        used.add(img)
        entry = {
            "sourceProductId": pid,
            "sourceImage": img,
            "focal": focal.css,
            "shop": kind == "shop",
            "kind": kind,
            "sourceAspect": round(aspect_ratio(source), 3),
        }
        if slot in EVENT_EDIT_SLOTS:
            entry["tone"] = "bw-non-apparel"
        new_slots[slot] = entry
        ok += 1
        if i <= 12 or i % 10 == 0 or i == len(slots) or slot in EVENT_EDIT_SLOTS:
            print(
                f"{i}/{len(slots)} {slot} ok {kind} {source.size[0]}x{source.size[1]} "
                f"focal={focal.css} src={img}",
                flush=True,
            )
        time.sleep(0.02)

    if not args.dry_run:
        merged = {**prev_slots, **new_slots}
        # Drop stale keys only on intentional full (--all) runs.
        # Sports-only / --only runs must keep locked + frozen non-sports frames.
        if args.all and not args.only:
            keep = set(referenced_slots()) | set(SLOT_THEMES) | LOCKED_BANNERS
            merged = {k: v for k, v in merged.items() if k in keep}
        # Always ensure locked creatives are retained in the manifest index.
        for name in LOCKED_BANNERS:
            if name not in merged and name in prev_slots:
                merged[name] = prev_slots[name]
            elif name not in merged:
                merged[name] = {
                    "locked": True,
                    "note": "fixed creative — not rotated by weekly sports refresh",
                }
        manifest = {
            "refreshedAt": datetime.now(timezone.utc).isoformat(),
            "weekSeed": seed,
            "mode": "all" if args.all else ("only" if args.only else "sports-only"),
            "slots": merged,
        }
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        print(f"wrote {MANIFEST}", flush=True)

    print(f"done ok={ok} fail={fail}", flush=True)
    return 0 if ok > 0 and fail < ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
