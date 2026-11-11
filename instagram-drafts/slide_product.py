#!/usr/bin/env python3
"""Refuse a carousel that mixes a second product in because the color matches."""

import gzip
import json
from pathlib import Path
from urllib.parse import urlsplit

from slide_layout import read_slide_record

ROOT = Path(__file__).resolve().parents[1]

# Longest prefix first so axo- is not read as ax-.
PREFIXES = (
    ("axo-", "ax"),
    ("axa-", "ax"),
    ("axg-", "ax"),
    ("ax-", "ax"),
    ("cw-", "cw"),
    ("gg-", "gg"),
    ("bb-", "bb"),
    ("lu-", "lu"),
    ("ps-", "ps"),
    ("bs-", "bs"),
    ("gc-", "gc"),
    ("bv-", "bv"),
    ("ch-", "ch"),
    ("ce-", "ce"),
    ("vw-", "vw"),
    ("al-", "al"),
    ("pr-", "pr"),
    ("lv-", "lv"),
    ("di-", "di"),
    ("mb-", "mb"),
    ("ms-", "ms"),
    ("mc-", "mc"),
    ("ys-", "ys"),
    ("iw-", "iw"),
    ("om-", "om"),
    ("th-", "th"),
    ("td-", "td"),
    ("pp-", "pp"),
    ("rx-", "rx"),
    ("nq-", "nq"),
)

# Words that name a product type. A caption that contains two of these groups
# is describing two products, which is how a same-color bag was added to a loafer post.
TYPE_WORDS = {
    "shoes": (
        "로퍼",
        "스니커즈",
        "스니커",
        "부츠",
        "샌들",
        "펌프스",
        "슬립온",
        "더비",
        "옥스퍼드",
        "뮬",
        "플랫슈즈",
    ),
    "bags": (
        "캐리어",
        "수트케이스",
        "여행 가방",
        "가방",
        "토트",
        "클러치",
        "백팩",
        "숄더백",
        "호보",
        "버킷백",
        "파우치",
    ),
    "watches": ("손목시계", "시계", "워치"),
}

CATALOG_CATEGORIES = {"shoes", "bags", "watches", "accessories", "luxury", "sports"}


def catalog_key(product_id):
    lowered = (product_id or "").lower()
    for prefix, key in PREFIXES:
        if lowered.startswith(prefix):
            return key
    return ""


def normalize_image_path(path):
    text = str(path or "").strip().split("?", 1)[0].replace("\\", "/")
    if "://" in text:
        text = urlsplit(text).path
    if "/public/" in text:
        text = text.split("/public/", 1)[1]
    return text.lstrip("/")


def types_in_text(text):
    found = set()
    haystack = text or ""
    for category, words in TYPE_WORDS.items():
        if any(word in haystack for word in words):
            found.add(category)
    return found


def conflicting_types(keyword, caption):
    """Categories named together. Empty when the text stays on one product type."""
    found = types_in_text(f"{keyword or ''}\n{caption or ''}")
    if len(found) > 1:
        return found
    return set()


def owned_image_paths(product):
    paths = set()

    def add(value):
        if isinstance(value, str) and value.strip():
            paths.add(normalize_image_path(value))

    add(product.get("image"))
    add(product.get("hoverImage"))
    for item in product.get("images") or []:
        add(item if isinstance(item, str) else (item or {}).get("src") or (item or {}).get("image"))
    for section in product.get("storySections") or []:
        if isinstance(section, dict):
            add(section.get("image"))
    for variant in product.get("variants") or []:
        if not isinstance(variant, dict):
            continue
        add(variant.get("image"))
        add(variant.get("hoverImage"))
        for item in variant.get("images") or []:
            add(item if isinstance(item, str) else (item or {}).get("src") or (item or {}).get("image"))
    paths.discard("")
    return paths


def catalog_file(product_id):
    key = catalog_key(product_id)
    if not key:
        raise ValueError(f"unknown product id {product_id}")
    ship = Path("/Users/jeonghyunlee/briq-ship")
    candidates = [
        ship / "src" / "data" / key / f"{key}-catalog.json",
        ship / "src" / "data" / key / f"{key}-bags-catalog.json",
        ship / "src" / "data" / key / f"{key}-catalog.ts",
        ROOT / "src" / "data" / key / f"{key}-catalog.json",
        ROOT / "src" / "data" / key / f"{key}-bags-catalog.json",
        ROOT / "src" / "data" / key / f"{key}-catalog.ts",
        ROOT / "catalog-dist" / key / f"{key}-catalog.json",
        ROOT / "catalog-dist" / key / f"{key}-catalog.json.gz",
    ]
    for path in candidates:
        if path.is_file() and path.stat().st_size > 100:
            return path
    raise ValueError(f"catalog for {product_id} is not on disk")


def _parse_ts_catalog(path):
    import re

    text = path.read_text(encoding="utf-8", errors="ignore")
    products = []
    for m in re.finditer(r'id:\s*"([^"]+)"([\s\S]*?)(?=\n\s*id:\s*"|$)', text):
        block = m.group(0)

        def g(k: str):
            mm = re.search(rf'{k}:\s*"([^"]*)"', block)
            return mm.group(1) if mm else None

        def gi(k: str):
            mm = re.search(rf"{k}:\s*([0-9][0-9_,.]*)", block)
            return float(mm.group(1).replace(",", "")) if mm else None

        images = re.findall(r'"(/products/[^"]+\.(?:jpg|jpeg|png|webp))"', block)
        products.append(
            {
                "id": m.group(1),
                "name": g("name"),
                "nameKo": g("nameKo"),
                "brand": g("brand"),
                "price": int(gi("price") or 0),
                "category": g("category") or "",
                "descriptionKo": g("descriptionKo") or "",
                "image": images[0] if images else (g("image") or ""),
                "images": images,
            }
        )
    return products


def load_catalog(path):
    if str(path).endswith(".ts"):
        products = _parse_ts_catalog(Path(path))
        if not products:
            raise ValueError(f"catalog {path} has no product list")
        return products
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("products", "items"):
            if isinstance(data.get(key), list):
                return data[key]
        flat = []
        for value in data.values():
            if isinstance(value, list):
                flat.extend(value)
        if flat:
            return flat
    raise ValueError(f"catalog {path} has no product list")


def load_product(product_id):
    wanted = (product_id or "").strip()
    for product in load_catalog(catalog_file(wanted)):
        if product.get("id") == wanted:
            return product
    raise ValueError(f"product {wanted} is not in the catalog")


def carousel_slides(cover):
    folder = Path(cover).resolve().parent
    slides = sorted(path for path in folder.glob("[0-9][0-9].jpg") if path.is_file())
    cover_path = Path(cover).resolve()
    if cover_path not in slides:
        slides.insert(0, cover_path)
    return slides


def assert_carousel_is_one_product(product_id, keyword, caption, cover, product=None):
    """Raise unless every slide photo belongs to this one product.

    Color, weave, and material are not checked. A second item that looks the
    same is still a different product.
    """
    product_id = (product_id or "").strip()
    if not product_id:
        raise ValueError(
            "pass the one product id. A matching color is not a reason to add another item."
        )
    mixed = conflicting_types(keyword, caption)
    if mixed:
        names = ", ".join(sorted(mixed))
        raise ValueError(
            f"caption describes more than one product type ({names}). "
            "One post, one product. Do not add another item because the color matches."
        )
    product = product if product is not None else load_product(product_id)
    if product.get("id") != product_id:
        raise ValueError(f"loaded product {product.get('id')} is not {product_id}")
    category = (product.get("category") or "").strip()
    keyword_types = types_in_text(keyword)
    if keyword_types and category in CATALOG_CATEGORIES and category not in keyword_types:
        raise ValueError(
            f"keyword is {', '.join(sorted(keyword_types))}, but {product_id} is {category}. "
            "Do not substitute a same-colored product from another category."
        )
    owned = owned_image_paths(product)
    if not owned:
        raise ValueError(f"{product_id} has no catalog photos to publish")
    slides = carousel_slides(cover)
    if len(slides) < 1:
        raise ValueError("carousel has no slides")
    for path in slides:
        record = read_slide_record(path)
        stamped = record["product_id"]
        source = normalize_image_path(record["source"])
        if not stamped or not source:
            raise ValueError(
                f"{path.name} is not stamped with its product. "
                "Re-render it with save_slide(product_id, source, category) "
                "using a photo listed on that product. Matching color is not enough."
            )
        if stamped != product_id:
            raise ValueError(
                f"{path.name} is {stamped}, not {product_id}. "
                "One carousel, one product. Matching color or weave is not the same product."
            )
        if record["category"] and category and record["category"] != category:
            raise ValueError(
                f"{path.name} is category {record['category']}, not {category}."
            )
        if source not in owned:
            raise ValueError(
                f"{path.name} uses {source}, which is not a photo of {product_id}. "
                "Same color is not the same product."
            )
    return product_id
