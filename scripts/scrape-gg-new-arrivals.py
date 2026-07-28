#!/usr/bin/env python3
"""Scrape Galvin Green men-new / women-new Shopify collections, download images, build catalog."""
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


def color_from_handle_group(handles: list[str], handle: str, tags: list[str]) -> str:
    if len(handles) <= 1:
        return (
            color_from_handle_suffix(handle)
            or color_from_tags_ordered(handle, tags)
            or "Default"
        )
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
    if remainder:
        return title_case_color(remainder)
    return (
        color_from_handle_suffix(handle)
        or color_from_tags_ordered(handle, tags)
        or "Default"
    )


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


def assign_colors(products: list[dict]) -> None:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for p in products:
        groups[(p["styleName"], p["collection"])].append(p)
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
    all_products: list[dict] = []
    collections_meta: dict[str, list[str]] = {}

    for shopify_handle, briq_coll in COLLECTIONS:
        print(f"Scraping {shopify_handle} → {briq_coll}")
        raw_list = paginate_collection(shopify_handle)
        handles = []
        for raw in raw_list:
            norm = normalize_product(raw, briq_coll)
            all_products.append(norm)
            handles.append(norm["handle"])
        collections_meta[shopify_handle] = handles
        print(f"  → {len(handles)} products")

    assign_colors(all_products)

    payload = {
        "scrapedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "collections": collections_meta,
        "products": all_products,
    }
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAW_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {RAW_PATH.relative_to(ROOT)} ({len(all_products)} colorways)")

    print("Downloading images…")
    saved, skipped = download_images(all_products)
    print(f"  images saved={saved} skipped_existing={skipped}")

    return {
        "men": len(collections_meta.get("men-new") or []),
        "women": len(collections_meta.get("women-new") or []),
        "total": len(all_products),
        "saved": saved,
        "skipped": skipped,
    }


def main() -> None:
    stats = scrape_and_write()
    print("Building gg-catalog.ts …")
    subprocess.check_call([sys.executable, str(ROOT / "scripts/build-gg-catalog.py")], cwd=str(ROOT))
    print(
        f"Done. men={stats['men']} women={stats['women']} "
        f"colorways={stats['total']} images_new={stats['saved']}"
    )


if __name__ == "__main__":
    main()
