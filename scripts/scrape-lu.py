#!/usr/bin/env python3
"""Scrape London Undercover Shopify collections → umbrella + lifestyle raws + images.

Umbrella collections → src/data/lu/lu-pdp-raw.json (+ lu-collections-raw.json)
Lifestyle collections → src/data/lu/lu-lifestyle-pdp-raw.json

Replaces raw each run so discontinued colourways drop out.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from studio_whiten import save_product_image  # noqa: E402

UMBRELLA_RAW = ROOT / "src/data/lu/lu-pdp-raw.json"
COLLECTIONS_RAW = ROOT / "src/data/lu/lu-collections-raw.json"
LIFESTYLE_RAW = ROOT / "src/data/lu/lu-lifestyle-pdp-raw.json"
IMG_ROOT = ROOT / "public/products/lu-pdp"

BASE = "https://londonundercover.co.uk"
UA = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
}

# (shopify handle, briq umbrella cat id)
UMBRELLA_COLLECTIONS = [
    ("auto-compact-umbrella", "auto-compact"),
    ("telescopic-umbrellas", "telescopic"),
    ("full-length-umbrellas", "full-length"),
    ("solid-stick", "full-length"),
    ("city-gent", "full-length"),
    ("classic-umbrella", "full-length"),
]

# (shopify handle, briq lifestyle leaf)
LIFESTYLE_COLLECTIONS = [
    ("everyday", "everyday"),
    ("grooming", "grooming"),
    ("home", "home"),
    ("stationery", "stationery"),
    ("bags", "bags"),
]


def fetch(url: str, accept: str = "*/*", retries: int = 8) -> bytes:
    for i in range(retries):
        req = urllib.request.Request(
            url,
            headers={**UA, "Accept": accept, "Referer": f"{BASE}/"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 10 + i * 6
                print(f"  429 wait {wait}s", flush=True)
                time.sleep(wait)
                continue
            raise
        except Exception as e:
            print(f"  err {e} retry {i}", flush=True)
            time.sleep(2 + i)
    raise RuntimeError(url)


def paginate(handle: str) -> list[dict]:
    out: list[dict] = []
    page = 1
    while page <= 20:
        url = f"{BASE}/collections/{handle}/products.json?limit=250&page={page}"
        print(f"  fetch {handle} p{page}", flush=True)
        time.sleep(1.8)
        data = json.loads(fetch(url, "application/json").decode("utf-8", "replace"))
        batch = data.get("products") or []
        print(f"    n={len(batch)}", flush=True)
        if not batch:
            break
        out.extend(batch)
        if len(batch) < 250:
            break
        page += 1
    return out


def cdn_url(src: str, width: int = 1200) -> str:
    if not src:
        return src
    if src.startswith("//"):
        src = "https:" + src
    if "width=" in src:
        return src
    sep = "&" if "?" in src else "?"
    return f"{src}{sep}width={width}"


def download_images(handles_products: list[dict]) -> tuple[int, int]:
    saved = skipped = 0
    IMG_ROOT.mkdir(parents=True, exist_ok=True)
    total = len(handles_products)
    for idx, p in enumerate(handles_products, 1):
        handle = p.get("handle") or ""
        if not handle:
            continue
        folder = IMG_ROOT / handle
        folder.mkdir(parents=True, exist_ok=True)
        urls = []
        for im in p.get("images") or []:
            src = im.get("src") if isinstance(im, dict) else None
            if src:
                urls.append(src)
        urls = urls[:8]
        if idx == 1 or idx % 25 == 0 or idx == total:
            print(f"  images {idx}/{total} {handle}", flush=True)
        for i, src in enumerate(urls, 1):
            dest = folder / f"{i}.jpg"
            if dest.exists() and dest.stat().st_size > 2000:
                skipped += 1
                continue
            try:
                data = fetch(cdn_url(src, 1200))
                if len(data) < 500:
                    continue
                save_product_image(dest, data)
                saved += 1
            except Exception as e:
                print(f"  warn image {handle}/{i}: {e}", flush=True)
            time.sleep(0.03)
    return saved, skipped


def normalize(raw: dict, *, briq_cats: list[str] | None = None, life_cols: list[str] | None = None) -> dict:
    variants = raw.get("variants") or []
    available = any(bool(v.get("available")) for v in variants)
    out = {
        "id": raw.get("id"),
        "title": raw.get("title") or "",
        "body_html": raw.get("body_html") or "",
        "vendor": raw.get("vendor") or "",
        "product_type": raw.get("product_type") or "",
        "created_at": raw.get("created_at"),
        "handle": raw.get("handle") or "",
        "updated_at": raw.get("updated_at"),
        "published_at": raw.get("published_at"),
        "template_suffix": raw.get("template_suffix"),
        "published_scope": raw.get("published_scope"),
        "tags": raw.get("tags") or "",
        "variants": variants,
        "options": raw.get("options") or [],
        "images": raw.get("images") or [],
        "image": raw.get("image"),
        "collectionAvailable": available,
    }
    if briq_cats is not None:
        out["briqCats"] = briq_cats
    if life_cols is not None:
        out["briqLifestyleCols"] = life_cols
    return out


def merge_cat(existing: list[str] | None, new: str) -> list[str]:
    cols = list(existing or [])
    if new not in cols:
        cols.append(new)
    return cols


def scrape_umbrellas() -> dict[str, dict]:
    by_id: dict[str, dict] = {}
    cats_map: dict[str, list[str]] = {}
    products_list: list[dict] = []
    seen_handles: set[str] = set()

    print("Warm LU…", flush=True)
    fetch(f"{BASE}/", "text/html")
    time.sleep(1)

    for handle, cat in UMBRELLA_COLLECTIONS:
        print(f"Umbrella {handle} → {cat}", flush=True)
        for raw in paginate(handle):
            pid = str(raw.get("id") or "")
            h = raw.get("handle") or ""
            if not pid or not h:
                continue
            if h in seen_handles and pid in by_id:
                by_id[pid]["briqCats"] = merge_cat(by_id[pid].get("briqCats"), cat)
                cats_map[pid] = by_id[pid]["briqCats"]
                continue
            seen_handles.add(h)
            if pid in by_id:
                by_id[pid]["briqCats"] = merge_cat(by_id[pid].get("briqCats"), cat)
                # refresh stock/images
                fresh = normalize(raw, briq_cats=by_id[pid]["briqCats"])
                by_id[pid] = fresh
            else:
                by_id[pid] = normalize(raw, briq_cats=[cat])
            cats_map[pid] = by_id[pid]["briqCats"]
            products_list.append({"id": pid, "handle": h, "title": raw.get("title")})

    # dedupe products_list by id for collections-raw
    uniq = {str(p["id"]): p for p in products_list}
    COLLECTIONS_RAW.parent.mkdir(parents=True, exist_ok=True)
    COLLECTIONS_RAW.write_text(
        json.dumps(
            {
                "scrapedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "products": list(uniq.values()),
                "cats": cats_map,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    UMBRELLA_RAW.write_text(
        json.dumps(by_id, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote umbrellas {len(by_id)}", flush=True)
    return by_id


def scrape_lifestyle() -> dict[str, dict]:
    by_id: dict[str, dict] = {}
    print("Lifestyle…", flush=True)
    for handle, col in LIFESTYLE_COLLECTIONS:
        print(f"Lifestyle {handle} → {col}", flush=True)
        for raw in paginate(handle):
            pid = str(raw.get("id") or "")
            if not pid or not raw.get("handle"):
                continue
            if pid in by_id:
                by_id[pid]["briqLifestyleCols"] = merge_cat(
                    by_id[pid].get("briqLifestyleCols"), col
                )
                fresh = normalize(
                    raw, life_cols=by_id[pid]["briqLifestyleCols"]
                )
                by_id[pid] = fresh
            else:
                by_id[pid] = normalize(raw, life_cols=[col])
    LIFESTYLE_RAW.write_text(
        json.dumps(by_id, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote lifestyle {len(by_id)}", flush=True)
    return by_id


def main() -> None:
    umbrellas = scrape_umbrellas()
    lifestyle = scrape_lifestyle()
    # images for anything missing locally
    need = []
    for bucket in (umbrellas, lifestyle):
        for p in bucket.values():
            h = p.get("handle") or ""
            folder = IMG_ROOT / h
            if not folder.exists() or not any(folder.glob("*.jpg")):
                need.append(p)
    print(f"Downloading images for {len(need)} SKUs…", flush=True)
    if need:
        saved, skipped = download_images(need)
        print(f"Images saved={saved} skipped={skipped}", flush=True)


if __name__ == "__main__":
    main()
