#!/usr/bin/env python3
"""Weekly refresh of Briq homepage / category banners with luxury product photos.

Sources official product galleries already on the `product-images` CDN
(Gucci / Burberry / Chanel / Arc'teryx …).

PC homepage frames are panoramic (hero ~4:1, look-banners ~3:1). Selection
prefers wide outfit / product stills and rejects face-only headshots and
empty grey product crops that used to dominate the desktop strip.

  python3 scripts/weekly-banner-refresh.py
  python3 scripts/weekly-banner-refresh.py --only rot-luxury --seed 42
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
    "rot-hero-1.jpg": ["luxury", "fashion"],
    "rot-hero-2.jpg": ["luxury", "fashion"],
    "rot-hero-3.jpg": ["fashion", "street"],
    "rot-hero-4.jpg": ["luxury", "fashion"],
    "rot-event-1.jpg": ["fashion", "luxury"],
    "rot-event-2.jpg": ["street", "fashion"],
    "rot-event-3.jpg": ["luxury", "fashion"],
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
    "rot-cw-1.jpg": ["watches"],
    "rot-cw-2.jpg": ["watches"],
    "rot-cw-3.jpg": ["watches"],
    "rot-cw-alt.jpg": ["watches"],
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

# Homepage look/hero strips for apparel — never crop shoe/bag close-ups into these.
CLOTHING_SLOTS = {
    n
    for n in SLOT_THEMES
    if n.startswith("rot-hero-")
    or n.startswith("rot-event-")
    or n.startswith("rot-luxury-")
    or n.startswith("rot-cloth-")
}

# Product stills — shoes / bags / accessories must stay readable after the PC crop.
PRODUCT_SLOTS = {
    n
    for n in SLOT_THEMES
    if n.startswith("rot-shoe-")
    or n.startswith("rot-bag-")
    or n.startswith("rot-acc-")
    or n.startswith("shop-shoe-")
    or n.startswith("shop-bag-")
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


def theme_match(product: dict, themes: list[str]) -> bool:
    blob = product_blob(product)
    checks = {
        "luxury": any(
            x in blob
            for x in ("gucci", "버버리", "burberry", "chanel", "샤넬", "luxury", "gc-", "bb-", "ch-")
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
                "arc'teryx",
                "arcteryx",
                "axa-",
                "paul smith",
                "belstaff",
            )
        ),
        "street": any(x in blob for x in ("street", "hoodie", "tee", "sneaker", "trainer")),
        "bags": any(
            x in blob
            for x in ("bag", "handbag", "가방", "tote", "backpack", "clutch", "crossbody")
        ),
        "shoes": any(
            x in blob
            for x in ("shoe", "sneaker", "boot", "loafer", "heel", "슈즈", "footwear", "sandal")
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
        "watches": any(x in blob for x in ("watch", "시계", "christopher ward", "cw-")),
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


def collect_candidates() -> tuple[dict[str, list[tuple[str, str]]], set[str]]:
    """theme → list of (product_id, image_path), plus clothing product ids."""
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
    for path in catalogs:
        for product in load_catalog(path):
            pid = str(product.get("id") or "")
            if is_clothing_product(product):
                clothing_ids.add(pid)
            look_imgs = product_images(product, prefer_on_model=True)
            look_imgs = [i for i in look_imgs if is_likely_on_model(i)] or look_imgs[:2]
            pack_imgs = product_images(product, prefer_on_model=False)
            pack_only = [
                i for i in pack_imgs if re.search(r"/1\.jpe?g(?:\?|$)", i.lower())
            ]
            pack_imgs = (pack_only or pack_imgs)[:2]
            if not look_imgs and not pack_imgs:
                continue
            product_themes = {"shoes", "bags", "accessories", "watches"}
            for theme in list(by_theme):
                if not theme_match(product, [theme]):
                    continue
                imgs = pack_imgs if theme in product_themes else look_imgs
                if not imgs:
                    imgs = pack_imgs or look_imgs
                for img in imgs[:3]:
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
    print(f"clothing_ids={len(clothing_ids)}", flush=True)
    return by_theme, clothing_ids


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


def pick_for_slot(
    slot: str,
    themes: list[str],
    pool: dict[str, list[tuple[str, str]]],
    rng: random.Random,
    used: set[str],
    seed: int,
    clothing_ids: set[str] | None = None,
) -> list[tuple[str, str]]:
    options: list[tuple[str, str]] = []
    for t in themes:
        options.extend(pool.get(t) or [])
    options = [o for o in options if o[1] not in used]
    if slot in CLOTHING_SLOTS and clothing_ids:
        clothed = [o for o in options if o[0] in clothing_ids]
        options = clothed
    brand_only = any(t.startswith("brand:") for t in themes)
    if not options and not brand_only:
        # fallback any luxury/fashion
        for t in ("luxury", "fashion", "outdoor"):
            options.extend(pool.get(t) or [])
        options = [o for o in options if o[1] not in used]
        if slot in CLOTHING_SLOTS and clothing_ids:
            options = [o for o in options if o[0] in clothing_ids]
    if not options:
        return []
    # Deterministic weekly shuffle per slot, then prefer wider local photos.
    digest = hashlib.sha1(f"{seed}:{slot}".encode()).hexdigest()
    slot_rng = random.Random(digest)
    slot_rng.shuffle(options)
    if slot in CLOTHING_SLOTS:
        luxury = slot.startswith("rot-luxury-")
        # Luxury: packshot garments. Other apparel: lookbook frame #2.
        options.sort(
            key=lambda o: (
                0 if luxury and re.search(r"/1\.jpe?g$", o[1], re.I) else 1,
                0 if (not luxury) and re.search(r"/2\.jpe?g$", o[1], re.I) else 1,
                0 if "/look" in o[1].lower() else 1,
            )
        )
    elif slot in PRODUCT_SLOTS:
        # Prefer primary packshots; never lead with /3 detail macros.
        options.sort(
            key=lambda o: (
                2 if re.search(r"/[3-9]\.jpe?g$", o[1], re.I) else 0,
                1 if is_likely_detail_frame(o[1]) else 0,
                0 if re.search(r"/1\.jpe?g$", o[1], re.I) else 1,
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
    if slot in PRODUCT_SLOTS:
        return "product"
    return "torso"


def clothing_source_ok(source, img: str, *, luxury_only: bool = False) -> tuple[bool, str]:
    """Accept outfit / garment stills; reject headshots and unreadable macros."""
    ratio = aspect_ratio(source)
    if ratio < 0.62:
        return False, f"too-tall {ratio:.2f}"
    if is_extreme_closeup(source):
        return False, "extreme-closeup"
    if is_likely_detail_frame(img):
        return False, "detail-frame"
    if is_face_dominant(source):
        return False, "face-dominant"
    # Signature clothing rail: garment stills only — no on-model face banners.
    if luxury_only and has_on_model_face(source):
        return False, "luxury-no-face"
    fill = subject_fill_ratio(source)
    if fill > 0.88:
        return False, f"macro-fill {fill:.2f}"
    if fill < 0.08:
        return False, f"empty {fill:.2f}"
    return True, "ok"


def product_source_ok(source, img: str) -> tuple[bool, str]:
    """Shoes / bags / accessories must read as the full product after PC crop."""
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
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    seed = args.seed or week_seed()
    rng = random.Random(seed)
    print(f"week_seed={seed}", flush=True)

    slots = [s for s in referenced_slots() if s in SLOT_THEMES]
    if args.only:
        needles = [n.strip() for n in args.only.split(",") if n.strip()]
        slots = [s for s in slots if any(n in s for n in needles)]
    if args.limit:
        slots = slots[: args.limit]
    print(f"slots={len(slots)}", flush=True)

    pool, clothing_ids = collect_candidates()
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
        picks = pick_for_slot(slot, themes, pool, rng, used, seed, clothing_ids)
        if not picks:
            print(f"{i}/{len(slots)} {slot} FAIL no-candidate", flush=True)
            fail += 1
            continue
        # PC look/hero banners are panoramic — prefer wide outfit / product
        # stills; reject face-only headshots and empty grey product frames.
        tries = 100 if kind in {"look", "hero"} else 12
        chosen: tuple[str, str, Image.Image] | None = None
        last_err = ""
        bias = slot_vertical_bias(slot)
        for pid, img in picks[:tries]:
            source = fetch_image(img)
            if source is None:
                last_err = f"fetch {img}"
                continue
            ratio = aspect_ratio(source)
            if slot in CLOTHING_SLOTS:
                ok_src, why = clothing_source_ok(
                    source, img, luxury_only=slot.startswith("rot-luxury-")
                )
                if not ok_src:
                    last_err = f"{why} {ratio:.2f} {img}"
                    continue
            elif slot in PRODUCT_SLOTS:
                ok_src, why = product_source_ok(source, img)
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
        try:
            focal = export_banner_set(
                source,
                desktop_path=BANNER_DIR / slot,
                tablet_path=TABLET_DIR / slot,
                mobile_path=MOBILE_DIR / slot,
                shop=kind == "shop",
                kind=kind,
                require_face=False,
                vertical_bias=bias,
            )
        except Exception as e:
            recovered = False
            if kind in {"look", "hero"}:
                for pid2, img2 in picks[:tries]:
                    if img2 == img:
                        continue
                    source2 = fetch_image(img2)
                    if source2 is None:
                        continue
                    if slot in CLOTHING_SLOTS:
                        ok_src, _ = clothing_source_ok(
                            source2,
                            img2,
                            luxury_only=slot.startswith("rot-luxury-"),
                        )
                        if not ok_src:
                            continue
                    elif slot in PRODUCT_SLOTS:
                        ok_src, _ = product_source_ok(source2, img2)
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
                            vertical_bias=bias,
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
        new_slots[slot] = {
            "sourceProductId": pid,
            "sourceImage": img,
            "focal": focal.css,
            "shop": kind == "shop",
            "kind": kind,
            "sourceAspect": round(aspect_ratio(source), 3),
        }
        ok += 1
        if i <= 12 or i % 10 == 0 or i == len(slots):
            print(
                f"{i}/{len(slots)} {slot} ok {kind} {source.size[0]}x{source.size[1]} "
                f"focal={focal.css} src={img}",
                flush=True,
            )
        time.sleep(0.02)

    if not args.dry_run:
        merged = {**prev_slots, **new_slots}
        # Drop stale keys only on full weekly runs (no --only filter)
        if not args.only:
            keep = set(referenced_slots()) | set(SLOT_THEMES)
            merged = {k: v for k, v in merged.items() if k in keep}
        manifest = {
            "refreshedAt": datetime.now(timezone.utc).isoformat(),
            "weekSeed": seed,
            "slots": merged,
        }
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        print(f"wrote {MANIFEST}", flush=True)

    print(f"done ok={ok} fail={fail}", flush=True)
    return 0 if ok > 0 and fail < ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
