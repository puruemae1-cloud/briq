#!/usr/bin/env python3
"""Scrape Galvin Green Shopify collections (New Arrivals + Bestsellers), download images, build catalog."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "src/data/gg/gg-catalog-raw.json"
IMG_ROOT = ROOT / "public/products/gg-pdp"

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "en-GB,en;q=0.9",
}

COLLECTIONS = [
    ("men-new", "gg-new-men"),
    ("women-new", "gg-new-women"),
    ("our-bestsellers-men", "gg-bestsellers-men"),
    ("our-bestsellers-women", "gg-bestsellers-women"),
]

COLOR_TAGS = [
    "Crystal Blue",
    "Royal Blue",
    "Moonlight Blue",
    "Delphinium Blue",
    "Storm Blue",
    "Forged Iron",
    "Pink Fuchsia",
    "Black",
    "Navy",
    "Orange",
    "White",
    "Sand",
    "Beige",
    "Grey",
    "Gray",
    "Blue",
    "Pink",
    "Fuchsia",
    "Red",
    "Yellow",
    "Green",
    "Olive",
    "Brown",
    "Ivory",
    "Cream",
    "Charcoal",
    "Stone",
    "Khaki",
    "Lime",
    "Teal",
    "Coral",
    "Purple",
    "Silver",
    "Gold",
]


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read()
    return json.loads(body.decode("utf-8", "replace"))


def paginate_collection(handle: str) -> list[dict]:
    products: list[dict] = []
    page = 1
    while True:
        url = (
            f"https://www.galvingreen.com/en-gb/collections/{handle}/products.json"
            f"?limit=250&page={page}"
        )
        print(f"  fetch {handle} page={page} …", flush=True)
        data = fetch_json(url)
        batch = data.get("products") or []
        if not batch:
            break
        products.extend(batch)
        if len(batch) < 250:
            break
        page += 1
        time.sleep(0.2)
    return products


def title_case_color(slug: str) -> str:
    return " ".join(w.capitalize() for w in slug.replace("_", "-").split("-") if w)


def longest_common_prefix(strings: list[str]) -> str:
    if not strings:
        return ""
    prefix = strings[0]
    for s in strings[1:]:
        while prefix and not s.startswith(prefix):
            prefix = prefix[:-1]
        if not prefix:
            break
    return prefix


COLOR_WORDS = {
    w
    for ct in COLOR_TAGS
    for w in ct.lower().replace(" ", "-").split("-")
} | {
    "crystal",
    "royal",
    "moonlight",
    "delphinium",
    "storm",
    "forged",
    "iron",
    "fuchsia",
}


def color_from_handle_suffix(handle: str) -> str | None:
    """Trailing handle tokens that look like colour names (e.g. …-black-orange)."""
    parts = handle.split("-")
    if len(parts) < 2:
        return None
    trail: list[str] = []
    for p in reversed(parts[1:]):
        if p in COLOR_WORDS:
            trail.append(p)
        else:
            break
    if not trail:
        return None
    trail.reverse()
    return title_case_color("-".join(trail))


def color_from_tags_ordered(handle: str, tags: list[str]) -> str | None:
    present = [ct for ct in COLOR_TAGS if ct in (tags or [])]
    if not present:
        return None

    def pos(ct: str) -> int:
        slug = ct.lower().replace(" ", "-")
        i = handle.find(slug)
        return i if i >= 0 else 10_000

    present.sort(key=pos)
    return " ".join(present)


HANDLE_PRODUCT_TOKENS = {
    "waterproof",
    "windproof",
    "water",
    "repellent",
    "repellant",
    "breathable",
    "insulating",
    "thermal",
    "golf",
    "jacket",
    "vest",
    "pants",
    "trousers",
    "shorts",
    "shirt",
    "skirt",
    "hoodie",
    "sweatshirt",
    "mid",
    "layer",
    "base",
    "top",
    "bottom",
    "hat",
    "cap",
    "visor",
    "belt",
    "gloves",
    "neck",
    "warmer",
    "short",
    "sleeve",
    "sleeveless",
    "long",
    "half",
    "full",
    "zip",
    "uv",
    "protection",
    "with",
    "inner",
    "and",
    "for",
}


def clean_color_remainder(remainder: str) -> str | None:
    """Drop garment-type tokens left when colourway handles diverge."""
    parts = [p for p in remainder.split("-") if p]
    color_parts = [p for p in parts if p not in HANDLE_PRODUCT_TOKENS]
    if not color_parts:
        return None
    # Need at least one recognisable colour word
    if not any(p in COLOR_WORDS for p in color_parts):
        return None
    return "-".join(color_parts)


def color_from_handle_group(handles: list[str], handle: str, tags: list[str]) -> str:
    tagged = color_from_tags_ordered(handle, tags)
    suffix = color_from_handle_suffix(handle)

    if len(handles) <= 1:
        return suffix or tagged or "Default"

    prefix = longest_common_prefix(handles)
    while prefix and not prefix.endswith("-"):
        if all(len(h) > len(prefix) and h[len(prefix)] == "-" for h in handles):
            break
        prefix = prefix[:-1]
    if prefix.endswith("-"):
        remainder = handle[len(prefix) :]
    else:
        cut = prefix.rfind("-")
        if cut > 0:
            prefix = prefix[: cut + 1]
            remainder = handle[len(prefix) :]
        else:
            remainder = ""
    remainder = remainder.strip("-")
    cleaned = clean_color_remainder(remainder) if remainder else None
    if cleaned:
        return title_case_color(cleaned)
    return suffix or tagged or (title_case_color(remainder) if remainder else "Default")


def normalize_product(raw: dict, collection: str) -> dict:
    title = raw.get("title") or ""
    style_name = title.split(" - ")[0].strip() if title else ""
    tags = raw.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    images = []
    for img in (raw.get("images") or [])[:12]:
        src = img.get("src") or ""
        if src:
            images.append(src)

    variants = []
    for v in raw.get("variants") or []:
        size = v.get("option1") or v.get("title") or ""
        variants.append(
            {
                "id": v.get("id"),
                "sku": v.get("sku") or "",
                "size": size,
                "price": v.get("price"),
                "compare_at_price": v.get("compare_at_price"),
                "available": bool(v.get("available")),
            }
        )

    return {
        "id": raw.get("id"),
        "handle": raw.get("handle"),
        "title": title,
        "body_html": raw.get("body_html") or "",
        "tags": tags,
        "published_at": raw.get("published_at"),
        "images": images,
        "variants": variants,
        "styleName": style_name,
        "colorName": "",  # filled after grouping
        "collection": collection,
    }


def gender_key(p: dict) -> str:
    cols = p.get("collections") or [p.get("collection") or ""]
    if any("women" in (c or "") for c in cols):
        return "women"
    return "men"


def assign_colors(products: list[dict]) -> None:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for p in products:
        groups[(p["styleName"], gender_key(p))].append(p)
    for members in groups.values():
        handles = [m["handle"] for m in members]
        for m in members:
            m["colorName"] = color_from_handle_group(handles, m["handle"], m.get("tags") or [])


def cdn_url(src: str, width: int = 1200) -> str:
    if not src:
        return src
    # Shopify CDN: append width param if none
    if "width=" in src:
        return src
    sep = "&" if "?" in src else "?"
    return f"{src}{sep}width={width}"


def download_images(products: list[dict]) -> tuple[int, int]:
    saved = 0
    skipped = 0
    IMG_ROOT.mkdir(parents=True, exist_ok=True)
    total = len(products)
    for idx, p in enumerate(products, 1):
        handle = p["handle"]
        folder = IMG_ROOT / handle
        folder.mkdir(parents=True, exist_ok=True)
        urls = (p.get("images") or [])[:6]
        if idx == 1 or idx % 10 == 0 or idx == total:
            print(f"  images {idx}/{total} ({handle})", flush=True)
        for i, src in enumerate(urls, 1):
            dest = folder / f"{i}.jpg"
            if dest.exists() and dest.stat().st_size > 2000:
                skipped += 1
                continue
            url = cdn_url(src, 1200)
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA["User-Agent"]})
                with urllib.request.urlopen(req, timeout=30) as r:
                    data = r.read()
                if len(data) < 500:
                    continue
                dest.write_bytes(data)
                saved += 1
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                print(f"  warn image {handle}/{i}: {e}", flush=True)
            time.sleep(0.02)
    return saved, skipped


def scrape_and_write() -> dict:
    by_handle: dict[str, dict] = {}
    collections_meta: dict[str, list[str]] = {}

    for shopify_handle, briq_coll in COLLECTIONS:
        print(f"Scraping {shopify_handle} → {briq_coll}")
        raw_list = paginate_collection(shopify_handle)
        handles = []
        for raw in raw_list:
            norm = normalize_product(raw, briq_coll)
            h = norm["handle"]
            handles.append(h)
            if h in by_handle:
                existing = by_handle[h]
                cols = existing.setdefault("collections", [existing["collection"]])
                if briq_coll not in cols:
                    cols.append(briq_coll)
                # Prefer freshest stock/price/images from this pass
                existing["title"] = norm["title"]
                existing["body_html"] = norm["body_html"]
                existing["tags"] = norm["tags"]
                existing["images"] = norm["images"] or existing.get("images")
                existing["variants"] = norm["variants"]
                existing["styleName"] = norm["styleName"]
                existing["published_at"] = norm.get("published_at") or existing.get(
                    "published_at"
                )
            else:
                norm["collections"] = [briq_coll]
                by_handle[h] = norm
        collections_meta[shopify_handle] = handles
        print(f"  → {len(handles)} products")

    all_products = list(by_handle.values())
    assign_colors(all_products)

    payload = {
        "scrapedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "collections": collections_meta,
        "products": all_products,
    }
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAW_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {RAW_PATH.relative_to(ROOT)} ({len(all_products)} unique colorways)")

    print("Downloading images…")
    saved, skipped = download_images(all_products)
    print(f"  images saved={saved} skipped_existing={skipped}")

    return {
        "men_new": len(collections_meta.get("men-new") or []),
        "women_new": len(collections_meta.get("women-new") or []),
        "men_best": len(collections_meta.get("our-bestsellers-men") or []),
        "women_best": len(collections_meta.get("our-bestsellers-women") or []),
        "total": len(all_products),
        "saved": saved,
        "skipped": skipped,
    }


def main() -> None:
    stats = scrape_and_write()
    print("Building gg-catalog.ts …")
    subprocess.check_call([sys.executable, str(ROOT / "scripts/build-gg-catalog.py")], cwd=str(ROOT))
    print(
        f"Done. new men/women={stats['men_new']}/{stats['women_new']} "
        f"best men/women={stats['men_best']}/{stats['women_best']} "
        f"unique={stats['total']} images_new={stats['saved']}"
    )


if __name__ == "__main__":
    main()
