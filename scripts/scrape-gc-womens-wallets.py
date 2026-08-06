#!/usr/bin/env python3
"""Scrape Gucci UK women's wallets & small accessories + PDP images.

Mirrors scrape-gc-handbags.py / scrape-gc-womens-shoes.py: productgrid leaves +
catalog API + DarkGray images into public/products/gc-pdp/.
Writes gc-wallets-catalog-raw.json.

Official PLP:
https://www.gucci.com/uk/en_gb/ca/women/wallets-and-small-accessories-for-women-c-women-accessories-wallets
"""
from __future__ import annotations

import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from curl_cffi import requests as cffi_requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from plp_hover import (  # noqa: E402
    first_alternate_gallery_src,
    gucci_lifestyle_index,
    pick_hover_local,
)

OUT_RAW = ROOT / "src/data/gc/gc-wallets-catalog-raw.json"
PDP_CACHE = ROOT / "src/data/gc/gc-pdp-cache.json"
IMG_ROOT = ROOT / "public/products/gc-pdp"

BASE = "https://www.gucci.com"
GRID = f"{BASE}/uk/en_gb/c/productgrid"
CATALOG = "https://prod-catalog-api.guccidigital.io/v1/products"
ORIGIN = "https://www.gucci.com"
WARM_URL = (
    f"{BASE}/uk/en_gb/ca/women/"
    "wallets-and-small-accessories-for-women-c-women-accessories-wallets"
)

# Official wallet / small-accessory leaves → Briq collection ids
# categoryCode is the URL segment after -c-
COLLECTIONS: list[tuple[str, str, str]] = [
    ("gc-women-long-wallets", "Long Wallets", "women-accessories-wallets-1"),
    ("gc-women-chain-wallets", "Chain Wallets", "women-chain-strap-wallets"),
    (
        "gc-women-compact-wallets",
        "Compact wallets",
        "women-accessories-wallets-small-wallets",
    ),
    ("gc-women-card-holders", "Card Holders", "women-accessories-wallets-2"),
    (
        "gc-women-bag-charms-keychains",
        "Bag charms and keychains",
        "women-bag-charms-key-holders",
    ),
    ("gc-women-pouches", "Pouches", "women-accessories-wallets-pouches"),
    ("gc-women-tech-accessories", "Tech Accessories", "women-tech-accessories"),
]

ALL_WALLETS_CODE = "women-accessories-wallets"
PARENT_COLL = "gc-women-wallets"
PARENT_COLLS = (
    "gc-women-wallets",
    "gc-accessories-womens",
    "gucci-accessories",
)
MAX_WORKERS = 6
IMG_WORKERS = 8


def session() -> cffi_requests.Session:
    return cffi_requests.Session()


def headers_json(referer: str = f"{BASE}/uk/en_gb/") -> dict:
    return {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-GB,en;q=0.9",
        "Referer": referer,
        "X-Requested-With": "XMLHttpRequest",
        "Origin": ORIGIN,
    }


def headers_html(referer: str = f"{BASE}/uk/en_gb/") -> dict:
    return {
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-GB,en;q=0.9",
        "Referer": referer,
    }


def abs_url(u: str | None) -> str:
    if not u:
        return ""
    if u.startswith("//"):
        return "https:" + u
    if u.startswith("/"):
        return BASE + u
    return u


def upgrade_media_url(u: str) -> str:
    """Prefer large DarkGray centre crop — matches gucci.com leather-goods mats."""
    u = abs_url(u)
    if "media.gucci.com/style/" not in u:
        return u
    return re.sub(
        r"/style/[^/]+/",
        "/style/DarkGray_Center_0_0_1200x1200/",
        u,
        count=1,
    )


def extract_shot_key(u: str) -> str:
    fn = u.split("/")[-1]
    m = re.match(r"(\d+_[A-Z0-9]+_\d+_\d+)", fn)
    return m.group(1) if m else fn


def collect_grid_images(item: dict) -> list[str]:
    urls: list[str] = []
    for key in ("primaryImage", "alternateImage"):
        img = item.get(key) or {}
        src = (
            img.get("datasrcstandardretina")
            or img.get("datasrcstandard")
            or img.get("src")
            or img.get("datasrc")
        )
        if src:
            urls.append(upgrade_media_url(src))
    for img in item.get("alternateGalleryImages") or []:
        src = (
            img.get("datasrcstandardretina")
            or img.get("datasrcstandard")
            or img.get("src")
            or img.get("datasrc")
        )
        if src:
            urls.append(upgrade_media_url(src))
    out: list[str] = []
    seen: set[str] = set()
    for u in urls:
        k = extract_shot_key(u)
        if k in seen:
            continue
        seen.add(k)
        out.append(u)
    return out


def fetch_grid_category(s: cffi_requests.Session, code: str) -> list[dict]:
    items: list[dict] = []
    page = 0
    while True:
        url = f"{GRID}?categoryCode={code}&show=Page&page={page}"
        for attempt in range(4):
            try:
                r = s.get(
                    url, headers=headers_json(), impersonate="chrome124", timeout=90
                )
                if "json" not in (r.headers.get("content-type") or ""):
                    raise RuntimeError(f"non-json for {code} page={page}")
                data = r.json()
                break
            except Exception as e:
                if attempt == 3:
                    raise
                time.sleep(1.5 * (attempt + 1))
                print(f"  retry {code} p{page}: {e}", flush=True)
        batch = ((data.get("products") or {}).get("items")) or []
        items.extend(batch)
        pages = int(data.get("numberOfPages") or 1)
        print(f"  {code} page {page + 1}/{pages} (+{len(batch)})", flush=True)
        page += 1
        if page >= pages:
            break
        time.sleep(0.15)
    return items


def fetch_catalog(s: cffi_requests.Session, code: str) -> dict | None:
    url = f"{CATALOG}/{code}?country=uk&language=en_gb"
    for attempt in range(4):
        try:
            r = s.get(
                url,
                headers={
                    "Accept": "application/json",
                    "Origin": ORIGIN,
                    "Referer": f"{BASE}/uk/en_gb/",
                },
                impersonate="chrome124",
                timeout=60,
            )
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if attempt == 3:
                print(f"  catalog fail {code}: {e}", flush=True)
                return None
            time.sleep(1.2 * (attempt + 1))
    return None


def fetch_pdp_images(s: cffi_requests.Session, product_link: str) -> list[str]:
    if not product_link:
        return []
    path = product_link if product_link.startswith("/uk/") else f"/uk/en_gb{product_link}"
    url = BASE + path
    try:
        r = s.get(url, headers=headers_html(), impersonate="chrome124", timeout=90)
        if r.status_code != 200:
            return []
        html = r.text
    except Exception:
        return []
    found = re.findall(
        r"//media\.gucci\.com/style/DarkGray_Center_0_0_(?:1200|2400)x(?:1200|2400)/\d+/[A-Za-z0-9_\-\.]+\.jpg",
        html,
    )
    if not found:
        found = re.findall(
            r"//media\.gucci\.com/style/[^\"'\s]+/\d+/[A-Za-z0-9_\-\.]+\.jpg",
            html,
        )
    out: list[str] = []
    seen: set[str] = set()
    for u in found:
        if "_150x150/" in u or "_600x314/" in u:
            continue
        uu = upgrade_media_url(u)
        k = extract_shot_key(uu)
        if k in seen:
            continue
        seen.add(k)
        out.append(uu)
    return out


def download_image(s: cffi_requests.Session, url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 2000:
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(3):
        try:
            r = s.get(
                url,
                headers={
                    "Accept": "image/jpeg,image/*,*/*",
                    "Referer": f"{BASE}/",
                },
                impersonate="chrome124",
                timeout=90,
            )
            if r.status_code != 200 or len(r.content) < 1500:
                raise RuntimeError(f"bad image {r.status_code} {len(r.content)}")
            if r.content[:3] != b"\xff\xd8\xff":
                raise RuntimeError("not jpeg")
            # Keep DarkGray studio mats — do not whiten.
            dest.write_bytes(r.content)
            return True
        except Exception:
            time.sleep(0.8 * (attempt + 1))
    return False


def pick_translation(catalog: dict, lang: str) -> dict | None:
    for t in catalog.get("translations") or []:
        if t.get("language") == lang:
            return t
    return None


def gbp_from_catalog(catalog: dict) -> float | None:
    for p in catalog.get("prices") or []:
        if p.get("country") == "gb" and p.get("currency", "").lower() == "gbp":
            try:
                return float(p["price"]) / 100.0
            except (TypeError, ValueError, KeyError):
                pass
    return None


def main() -> None:
    OUT_RAW.parent.mkdir(parents=True, exist_ok=True)
    IMG_ROOT.mkdir(parents=True, exist_ok=True)

    cache: dict = {}
    if PDP_CACHE.exists():
        cache = json.loads(PDP_CACHE.read_text())

    s = session()
    s.get(WARM_URL, headers=headers_html(), impersonate="chrome124", timeout=90)

    membership: dict[str, set[str]] = {}
    cards: dict[str, dict] = {}
    plp_meta: dict[str, dict] = {}

    print(f"=== {PARENT_COLL} ({ALL_WALLETS_CODE})", flush=True)
    all_items = fetch_grid_category(s, ALL_WALLETS_CODE)
    plp_meta[PARENT_COLL] = {
        "label": "Wallets & Small Accessories / View All",
        "categoryCode": ALL_WALLETS_CODE,
        "count": len({it["productCode"] for it in all_items}),
    }
    for it in all_items:
        code = it["productCode"]
        membership.setdefault(code, set()).update(PARENT_COLLS)
        cards[code] = it

    for coll_id, label, cat_code in COLLECTIONS:
        print(f"=== {coll_id} ({cat_code})", flush=True)
        items = fetch_grid_category(s, cat_code)
        plp_meta[coll_id] = {
            "label": label,
            "categoryCode": cat_code,
            "count": len({it["productCode"] for it in items}),
        }
        for it in items:
            code = it["productCode"]
            membership.setdefault(code, set()).update({coll_id, *PARENT_COLLS})
            if code not in cards:
                cards[code] = it
            else:
                prev = cards[code]
                if len(collect_grid_images(it)) > len(collect_grid_images(prev)):
                    cards[code] = {**prev, **it}

    codes = sorted(cards.keys())
    print(f"Unique colourways: {len(codes)}", flush=True)
    cache_lock = Lock()

    def enrich(code: str) -> dict:
        local_s = session()
        item = cards[code]
        cached = cache.get(code) or {}
        catalog = cached.get("catalog")
        if not catalog:
            catalog = fetch_catalog(local_s, code)
        pdp_imgs = cached.get("pdpImages") or []
        if not pdp_imgs:
            pdp_imgs = fetch_pdp_images(local_s, item.get("productLink") or "")
            mm = re.match(r"(\d{6})([A-Z0-9]{5})(\d{4})", code)
            if mm:
                style_prefix = f"{mm.group(1)}_{mm.group(2)}_{mm.group(3)}"
                filtered = [u for u in pdp_imgs if style_prefix in u]
                if filtered:
                    pdp_imgs = filtered

        grid_imgs = collect_grid_images(item)
        images: list[str] = []
        seen: set[str] = set()
        for u in pdp_imgs + grid_imgs:
            k = extract_shot_key(u)
            if k in seen:
                continue
            seen.add(k)
            images.append(u)

        plp_hover_url = first_alternate_gallery_src(item)
        if plp_hover_url:
            plp_hover_url = upgrade_media_url(plp_hover_url)
        life_idx = gucci_lifestyle_index(images)
        if not plp_hover_url and life_idx is not None:
            plp_hover_url = images[life_idx]

        gbp = item.get("rawPrice")
        if gbp is None and catalog:
            gbp = gbp_from_catalog(catalog)

        en = pick_translation(catalog or {}, "en_GB") or pick_translation(
            catalog or {}, "en"
        )
        ko = pick_translation(catalog or {}, "ko")

        in_stock = not bool(item.get("showOutOfStockLabel"))
        if item.get("inStockEntry") is False:
            in_stock = False

        plink = item.get("productLink") or ""
        if plink.startswith("/uk/"):
            source_url = abs_url(plink)
        elif plink:
            source_url = abs_url(f"/uk/en_gb{plink}")
        else:
            source_url = ""

        row = {
            "id": code,
            "productCode": code,
            "title": item.get("productName") or (en or {}).get("name") or code,
            "variant": item.get("variant")
            or (en or {}).get("variationDescription")
            or "",
            "url": source_url,
            "gbpPrice": float(gbp) if gbp is not None else None,
            "priceLabel": item.get("price"),
            "image": images[0] if images else "",
            "images": images,
            "plpHoverUrl": plp_hover_url or "",
            "collections": sorted(membership.get(code) or []),
            "inStock": in_stock,
            "label": item.get("label"),
            "isDiyProduct": bool(item.get("isDiyProduct")),
            "flagPersonalization": bool((catalog or {}).get("flagPersonalization")),
            # Full catalog lives in gc-pdp-cache.json — keep raw lean for git.
            "translationEn": en,
            "translationKo": ko,
            "kind": "wallets",
            "scrapedAt": datetime.now(timezone.utc).isoformat(),
        }
        with cache_lock:
            cache[code] = {
                "catalog": catalog,
                "pdpImages": pdp_imgs,
                "updatedAt": row["scrapedAt"],
            }
        return row

    products: list[dict] = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(enrich, c): c for c in codes}
        done = 0
        for fut in as_completed(futs):
            products.append(fut.result())
            done += 1
            if done % 25 == 0 or done == len(codes):
                print(f"enriched {done}/{len(codes)}", flush=True)
                with cache_lock:
                    PDP_CACHE.write_text(json.dumps(cache, ensure_ascii=False))

    products.sort(key=lambda p: p["id"])

    def dl_one(prod: dict) -> tuple[str, list[str]]:
        local_s = session()
        code = prod["id"]
        local: list[str] = []
        for i, url in enumerate(prod.get("images") or [], start=1):
            dest = IMG_ROOT / code / f"{i}.jpg"
            if download_image(local_s, url, dest):
                local.append(f"/products/gc-pdp/{code}/{i}.jpg")
            if i >= 12:
                break
        return code, local

    print("Downloading images…", flush=True)
    local_map: dict[str, list[str]] = {}
    with ThreadPoolExecutor(max_workers=IMG_WORKERS) as ex:
        futs = [ex.submit(dl_one, p) for p in products]
        done = 0
        for fut in as_completed(futs):
            code, local = fut.result()
            local_map[code] = local
            done += 1
            if done % 40 == 0 or done == len(products):
                print(f"images {done}/{len(products)}", flush=True)

    for p in products:
        locs = local_map.get(p["id"]) or []
        p["localImages"] = locs
        if locs:
            p["localImage"] = locs[0]
        hover_url = p.get("plpHoverUrl") or ""
        local_hover = None
        if hover_url and locs:
            hk = extract_shot_key(hover_url)
            for i, remote in enumerate(p.get("images") or []):
                if extract_shot_key(remote) == hk and i < len(locs):
                    local_hover = locs[i]
                    break
        if not local_hover and locs:
            local_hover = pick_hover_local(
                locs, remote_images=p.get("images") or []
            )
        if local_hover:
            p["localHover"] = local_hover

    payload = {
        "scrapedAt": datetime.now(timezone.utc).isoformat(),
        "source": WARM_URL,
        "collections": plp_meta,
        "count": len(products),
        "products": products,
    }
    OUT_RAW.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    PDP_CACHE.write_text(json.dumps(cache, ensure_ascii=False))
    print(f"Wrote {OUT_RAW} ({len(products)} products)", flush=True)
    for coll_id, label, _ in COLLECTIONS:
        n = sum(1 for p in products if coll_id in p["collections"])
        print(f"  {coll_id}: {n}", flush=True)


if __name__ == "__main__":
    main()
