#!/usr/bin/env python3
"""Fill missing Galvin Green colourways for styles already in Briq.

PLP scrapes only list one colour per style when siblings sit outside the
collection. For each style in gg-catalog-raw.json, search Shopify for the
exact product title and add any missing colourway handles (same gender).
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "src/data/gg/gg-catalog-raw.json"

_spec = importlib.util.spec_from_file_location(
    "scrape_gg", ROOT / "scripts/scrape-gg-new-arrivals.py"
)
_scrape = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_scrape)

UA = _scrape.UA
assign_colors = _scrape.assign_colors
download_images = _scrape.download_images
gender_key = _scrape.gender_key
normalize_product = _scrape.normalize_product


def fetch_json(url: str) -> dict | list:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def search_handles(title: str) -> list[dict]:
    """Return Shopify suggest products matching exact title."""
    url = (
        "https://www.galvingreen.com/en-gb/search/suggest.json?"
        + urllib.parse.urlencode(
            {
                "q": title,
                "resources[type]": "product",
                "resources[limit]": 20,
                "resources[options][unavailable_products]": "last",
            }
        )
    )
    try:
        data = fetch_json(url)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return []
    products = (
        ((data or {}).get("resources") or {}).get("results") or {}
    ).get("products") or []
    out = []
    for p in products:
        if (p.get("title") or "").strip() != title.strip():
            continue
        out.append(p)
    return out


def gender_from_suggest(p: dict) -> str | None:
    tags = p.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    lower = {t.lower() for t in tags}
    if "women" in lower or "women's" in lower:
        return "women"
    if "men" in lower or "men's" in lower:
        return "men"
    # Fall back to title / type heuristics
    title = (p.get("title") or "").lower()
    if "women" in title:
        return "women"
    return None


def is_outlet_only(p: dict) -> bool:
    """Skip discontinued / broken outlet colourways only — not B2B outlet tags."""
    tags = p.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    lower = {t.lower() for t in tags}
    if "missing_converted_color_metadata" in lower:
        return True
    # Exact "Outlet" clearance (not "Outlet/Rea - B2B" which appears on active SKUs)
    if "outlet" in lower:
        return True
    return False


def fetch_product_js(handle: str) -> dict | None:
    url = f"https://www.galvingreen.com/en-gb/products/{handle}.js"
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": UA["User-Agent"],
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        pass
    # Fallback: products.json (available may be missing — treat as True if present)
    try:
        data = fetch_json(f"https://www.galvingreen.com/en-gb/products/{handle}.json")
        product = (data or {}).get("product") or {}
        if not product:
            return None
        # Shape like product.js for js_to_raw_product
        images = []
        for img in product.get("images") or []:
            src = img.get("src") if isinstance(img, dict) else None
            if src:
                images.append(src)
        variants = []
        for v in product.get("variants") or []:
            price = v.get("price")
            variants.append(
                {
                    "id": v.get("id"),
                    "sku": v.get("sku") or "",
                    "option1": v.get("option1") or v.get("title"),
                    "title": v.get("title"),
                    "price": float(price) * 100
                    if isinstance(price, str)
                    else (price or 0),
                    "compare_at_price": (
                        float(v["compare_at_price"]) * 100
                        if v.get("compare_at_price")
                        else None
                    ),
                    "available": bool(v["available"])
                    if v.get("available") is not None
                    else True,
                }
            )
        return {
            "id": product.get("id"),
            "handle": product.get("handle"),
            "title": product.get("title"),
            "description": product.get("body_html") or "",
            "tags": product.get("tags") or [],
            "published_at": product.get("published_at"),
            "images": images,
            "variants": variants,
        }
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError, TypeError, ValueError):
        return None


def js_to_raw_product(js: dict, collection: str) -> dict:
    """Convert Shopify product.js payload into our normalize_product shape."""
    images = []
    for img in (js.get("images") or [])[:12]:
        if isinstance(img, str) and img:
            images.append(img if img.startswith("http") else f"https:{img}")
        elif isinstance(img, dict) and img.get("src"):
            src = img["src"]
            images.append(src if src.startswith("http") else f"https:{src}")

    # featured_image / media fallback
    if not images and js.get("featured_image"):
        src = js["featured_image"]
        if isinstance(src, str):
            images.append(src if src.startswith("http") else f"https:{src}")

    variants = []
    for v in js.get("variants") or []:
        price = v.get("price")
        # product.js prices are often integer cents
        if isinstance(price, (int, float)) and price > 999:
            price_str = f"{price / 100:.2f}"
        else:
            price_str = str(price) if price is not None else "0"
        cap = v.get("compare_at_price")
        if isinstance(cap, (int, float)) and cap and cap > 999:
            cap_str = f"{cap / 100:.2f}"
        elif cap:
            cap_str = str(cap)
        else:
            cap_str = None
        variants.append(
            {
                "id": v.get("id"),
                "sku": v.get("sku") or "",
                "size": v.get("option1") or v.get("title") or "",
                "price": price_str,
                "compare_at_price": cap_str,
                "available": bool(v.get("available")),
            }
        )

    tags = js.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    title = js.get("title") or ""
    style_name = title.split(" - ")[0].strip() if title else ""

    return {
        "id": js.get("id"),
        "handle": js.get("handle"),
        "title": title,
        "body_html": js.get("description") or "",
        "tags": tags,
        "published_at": js.get("published_at"),
        "images": images,
        "variants": variants,
        "styleName": style_name,
        "colorName": "",
        "collection": collection,
        "collections": [collection],
    }


def enrich() -> dict:
    if not RAW_PATH.exists():
        raise SystemExit(f"Missing {RAW_PATH}")

    raw = json.loads(RAW_PATH.read_text())
    products: list[dict] = raw.get("products") or []
    by_handle = {p["handle"]: p for p in products if p.get("handle")}

    # Group by (exact title, gender) using existing rows
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for p in products:
        title = (p.get("title") or "").strip()
        if not title:
            continue
        groups[(title, gender_key(p))].append(p)

    added = 0
    skipped_outlet = 0
    searched = 0
    new_products: list[dict] = []

    for (title, gender), members in sorted(groups.items(), key=lambda x: x[0][0]):
        searched += 1
        # Inherit all collections already on this style
        style_cols: list[str] = []
        for m in members:
            for c in m.get("collections") or [m.get("collection")]:
                if c and c not in style_cols:
                    style_cols.append(c)
        primary_coll = style_cols[0] if style_cols else "gg-new-men"

        existing_handles = {m["handle"] for m in members}
        suggest = search_handles(title)
        time.sleep(0.12)

        for sp in suggest:
            handle = sp.get("handle")
            if not handle or handle in existing_handles or handle in by_handle:
                continue
            sg = gender_from_suggest(sp)
            if sg and sg != gender:
                continue
            if is_outlet_only(sp):
                skipped_outlet += 1
                continue

            js = fetch_product_js(handle)
            time.sleep(0.08)
            if not js:
                print(f"  warn: no product.js for {handle}")
                continue
            # Skip if zero sizes available AND outlet-ish clearance price
            any_stock = any(bool(v.get("available")) for v in (js.get("variants") or []))
            if not any_stock and is_outlet_only(sp):
                skipped_outlet += 1
                continue

            norm = js_to_raw_product(js, primary_coll)
            # Attach full style collection membership
            norm["collections"] = list(style_cols) or [primary_coll]
            norm["collection"] = primary_coll
            # Prefer Shopify title from js
            if (norm.get("title") or "").strip() != title:
                # Title mismatch after fetch — skip
                continue

            products.append(norm)
            by_handle[handle] = norm
            new_products.append(norm)
            existing_handles.add(handle)
            added += 1
            print(f"  + {handle}  ← {title} ({gender}) cols={norm['collections']}")

        if searched % 10 == 0:
            print(f"… scanned {searched}/{len(groups)} styles, added={added}")

    assign_colors(products)

    if new_products:
        print(f"Downloading images for {len(new_products)} new colourways…")
        saved, skipped = download_images(new_products)
        print(f"  images saved={saved} skipped_existing={skipped}")

    raw["scrapedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    raw["products"] = products
    raw["colorEnrichment"] = {
        "added": added,
        "skippedOutlet": skipped_outlet,
        "stylesScanned": searched,
        "at": raw["scrapedAt"],
    }
    RAW_PATH.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("Rebuilding gg-catalog.ts …")
    subprocess.check_call(
        [sys.executable, str(ROOT / "scripts/build-gg-catalog.py")],
        cwd=str(ROOT),
    )

    return {
        "added": added,
        "skipped_outlet": skipped_outlet,
        "styles": searched,
        "total": len(products),
    }


if __name__ == "__main__":
    stats = enrich()
    print(
        f"Done. styles={stats['styles']} added_colours={stats['added']} "
        f"skipped_outlet={stats['skipped_outlet']} total_colorways={stats['total']}"
    )
