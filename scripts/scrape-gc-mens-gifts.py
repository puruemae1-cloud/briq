#!/usr/bin/env python3
"""Scrape Gucci UK Gifts for Him PLPs + PDP images for *new* SKUs only.

Existing catalogue productCodes are recorded with mens-gifts membership only
(no second PDP / no re-download). Official hub:
https://www.gucci.com/uk/en_gb/ca/gifts/gifts-for-men-c-gifts-for-him

Leaves (categoryCode → Briq id) from hub Category filters + Personalised:
  gifts-gifts-for-him-bags                     → gc-men-gifts-bags
  gifts-gifts-for-him-belts                    → gc-men-gifts-belts
  gifts-gifts-for-him-jewellery-and-watches    → gc-men-gifts-jewellery-watches
  gifts-gifts-for-him-shoes                    → gc-men-gifts-shoes
  gifts-gifts-for-him-small-accessories        → gc-men-gifts-small-accessories
  gifts-for-him-small-leathergoods             → gc-men-gifts-small-leathergoods
  gifts-for-him-sunglasses                     → gc-men-gifts-sunglasses
  gifts-for-him-watches                        → gc-men-gifts-watches
  monogramming-gifts-for-him                   → gc-men-gifts-personalised

Hub PLP (gifts-for-him) tags parent membership for full ~240 coverage.
Does not remove / replace top-level gc-gifts* — this is 남성용 → 선물용.
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

OUT_RAW = ROOT / "src/data/gc/gc-mens-gifts-catalog-raw.json"
CATALOG_JSON = ROOT / "src/data/gc/gc-catalog.json"
PDP_CACHE = ROOT / "src/data/gc/gc-pdp-cache.json"
IMG_ROOT = ROOT / "public/products/gc-pdp"

BASE = "https://www.gucci.com"
GRID = f"{BASE}/uk/en_gb/c/productgrid"
CATALOG = "https://prod-catalog-api.guccidigital.io/v1/products"
ORIGIN = "https://www.gucci.com"
WARM_URL = f"{BASE}/uk/en_gb/ca/gifts/gifts-for-men-c-gifts-for-him"

# (briq_id, label, categoryCode)
COLLECTIONS: list[tuple[str, str, str]] = [
    ("gc-men-gifts-bags", "Bags", "gifts-gifts-for-him-bags"),
    ("gc-men-gifts-belts", "Belts", "gifts-gifts-for-him-belts"),
    (
        "gc-men-gifts-jewellery-watches",
        "Jewellery and Watches",
        "gifts-gifts-for-him-jewellery-and-watches",
    ),
    ("gc-men-gifts-shoes", "Shoes", "gifts-gifts-for-him-shoes"),
    (
        "gc-men-gifts-small-accessories",
        "Small Accessories",
        "gifts-gifts-for-him-small-accessories",
    ),
    (
        "gc-men-gifts-small-leathergoods",
        "Small Leathergoods",
        "gifts-for-him-small-leathergoods",
    ),
    ("gc-men-gifts-sunglasses", "Sunglasses", "gifts-for-him-sunglasses"),
    ("gc-men-gifts-watches", "Watches", "gifts-for-him-watches"),
    (
        "gc-men-gifts-personalised",
        "Personalised Gifts",
        "monogramming-gifts-for-him",
    ),
]

HUB_CODE = "gifts-for-him"
PARENT_COLL = "gc-men-gifts"
PARENT_COLLS = (
    "gc-men-gifts",
    "gc-accessories-mens",
    "gucci-accessories",
)

LEAF_IDS = [c[0] for c in COLLECTIONS]

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
                    url, headers=headers_json(WARM_URL), impersonate="chrome124", timeout=90
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
        time.sleep(0.12)
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


def extract_sizes(catalog: dict | None) -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    for v in (catalog or {}).get("variants") or []:
        size = str(v.get("sizeDescription") or "").strip()
        if not size:
            continue
        key = size.upper()
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "size": size,
                "ggSizeCode": v.get("ggSizeCode"),
                "sku": v.get("sku"),
            }
        )

    def sort_key(row: dict) -> tuple:
        s = row["size"]
        if s.upper() in {"U", "OS", "ONE SIZE", "NS"}:
            return (2, s.upper())
        if re.search(r"\d", s):
            m = re.search(r"(\d+(?:\.\d+)?)", s)
            return (0, float(m.group(1)) if m else 0)
        return (1, s.upper())

    out.sort(key=sort_key)
    return out


def expand_membership(cols: set[str]) -> set[str]:
    out = set(cols)
    out.update(PARENT_COLLS)
    return out


def load_existing_skus() -> set[str]:
    if not CATALOG_JSON.exists():
        return set()
    data = json.loads(CATALOG_JSON.read_text())
    return {str(p.get("sku") or "").upper() for p in data if p.get("sku")}


def main() -> None:
    OUT_RAW.parent.mkdir(parents=True, exist_ok=True)
    IMG_ROOT.mkdir(parents=True, exist_ok=True)

    existing = load_existing_skus()
    print(f"Existing GC catalogue SKUs: {len(existing)}", flush=True)

    cache: dict = {}
    if PDP_CACHE.exists():
        cache = json.loads(PDP_CACHE.read_text())

    s = session()
    s.get(WARM_URL, headers=headers_html(), impersonate="chrome124", timeout=90)

    membership: dict[str, set[str]] = {}
    cards: dict[str, dict] = {}
    plp_meta: dict[str, dict] = {}
    failed: list[str] = []

    # Hub first — parent membership for full gifts-for-him coverage.
    print(f"=== {PARENT_COLL} hub ({HUB_CODE})", flush=True)
    try:
        hub_items = fetch_grid_category(s, HUB_CODE)
    except Exception as e:
        print(f"FAIL {HUB_CODE}: {e}", flush=True)
        failed.append(HUB_CODE)
        hub_items = []
    plp_meta[PARENT_COLL] = {
        "label": "Gifts for Him",
        "categoryCodes": [HUB_CODE],
        "count": 0,
    }
    hub_extra = expand_membership(set())
    for it in hub_items:
        code = it["productCode"]
        membership.setdefault(code, set()).update(hub_extra)
        if code not in cards:
            cards[code] = it
        else:
            prev_card = cards[code]
            if len(collect_grid_images(it)) > len(collect_grid_images(prev_card)):
                cards[code] = {**prev_card, **it}

    for coll_id, label, cat_code in COLLECTIONS:
        print(f"=== {coll_id} ({cat_code})", flush=True)
        try:
            items = fetch_grid_category(s, cat_code)
        except Exception as e:
            print(f"FAIL {cat_code}: {e}", flush=True)
            failed.append(cat_code)
            items = []
        plp_meta[coll_id] = {
            "label": label,
            "categoryCodes": [cat_code],
            "count": 0,
        }
        extra = expand_membership({coll_id})
        for it in items:
            code = it["productCode"]
            membership.setdefault(code, set()).update(extra)
            if code not in cards:
                cards[code] = it
            else:
                prev_card = cards[code]
                if len(collect_grid_images(it)) > len(collect_grid_images(prev_card)):
                    cards[code] = {**prev_card, **it}

    for coll_id in [PARENT_COLL, *LEAF_IDS]:
        n = sum(1 for cols in membership.values() if coll_id in cols)
        if coll_id in plp_meta:
            plp_meta[coll_id]["count"] = n

    codes = sorted(cards.keys())
    new_codes = [c for c in codes if c.upper() not in existing]
    tag_codes = [c for c in codes if c.upper() in existing]
    print(
        f"Unique mens-gifts colourways: {len(codes)} "
        f"(tag existing={len(tag_codes)}, enrich new={len(new_codes)})",
        flush=True,
    )

    cache_lock = Lock()

    def lean_tag_row(code: str) -> dict:
        item = cards[code]
        cols = expand_membership(membership.get(code) or set())
        gbp = item.get("rawPrice")
        plink = item.get("productLink") or ""
        if plink.startswith("/uk/"):
            source_url = abs_url(plink)
        elif plink:
            source_url = abs_url(f"/uk/en_gb{plink}")
        else:
            source_url = ""
        return {
            "id": code,
            "productCode": code,
            "title": item.get("productName") or code,
            "variant": item.get("variant") or "",
            "url": source_url,
            "gbpPrice": float(gbp) if gbp is not None else None,
            "priceLabel": item.get("price"),
            "image": "",
            "images": [],
            "collections": sorted(cols),
            "inStock": not bool(item.get("showOutOfStockLabel")),
            "label": item.get("label"),
            "isDiyProduct": bool(item.get("isDiyProduct")),
            "sizes": [],
            "kind": "mens-gifts",
            "tagOnly": True,
            "scrapedAt": datetime.now(timezone.utc).isoformat(),
        }

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

        cols = expand_membership(membership.get(code) or set())
        sizes = extract_sizes(catalog)

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
            "collections": sorted(cols),
            "inStock": in_stock,
            "label": item.get("label"),
            "isDiyProduct": bool(item.get("isDiyProduct")),
            "flagPersonalization": bool((catalog or {}).get("flagPersonalization")),
            "sizes": sizes,
            "translationEn": en,
            "translationKo": ko,
            "kind": "mens-gifts",
            "tagOnly": False,
            "scrapedAt": datetime.now(timezone.utc).isoformat(),
        }
        with cache_lock:
            cache[code] = {
                "catalog": catalog,
                "pdpImages": pdp_imgs,
                "updatedAt": row["scrapedAt"],
            }
        return row

    products: list[dict] = [lean_tag_row(c) for c in tag_codes]

    if new_codes:
        print(f"Enriching {len(new_codes)} new mens-gift SKUs…", flush=True)
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futs = {ex.submit(enrich, c): c for c in new_codes}
            done = 0
            for fut in as_completed(futs):
                products.append(fut.result())
                done += 1
                if done % 25 == 0 or done == len(new_codes):
                    print(f"enriched {done}/{len(new_codes)}", flush=True)
                    with cache_lock:
                        PDP_CACHE.write_text(json.dumps(cache, ensure_ascii=False))

    products.sort(key=lambda p: p["id"])

    new_products = [p for p in products if not p.get("tagOnly")]

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

    print(f"Downloading images for {len(new_products)} new SKUs…", flush=True)
    local_map: dict[str, list[str]] = {}
    if new_products:
        with ThreadPoolExecutor(max_workers=IMG_WORKERS) as ex:
            futs = [ex.submit(dl_one, p) for p in new_products]
            done = 0
            for fut in as_completed(futs):
                code, local = fut.result()
                local_map[code] = local
                done += 1
                if done % 40 == 0 or done == len(new_products):
                    print(f"images {done}/{len(new_products)}", flush=True)

    for p in products:
        if p.get("tagOnly"):
            continue
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
        "tagOnlyCount": len(tag_codes),
        "newCount": len(new_codes),
        "failedCategoryCodes": failed,
        "note": (
            "Official gifts-for-him hub Category filters + personalised. "
            "Existing SKUs are tagOnly under gc-men-gifts*; keep top-level gc-gifts."
        ),
        "products": products,
    }
    OUT_RAW.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    PDP_CACHE.write_text(json.dumps(cache, ensure_ascii=False))
    print(
        f"Wrote {OUT_RAW} ({len(products)} products; "
        f"tagged={len(tag_codes)} new={len(new_codes)})",
        flush=True,
    )
    for coll_id in [PARENT_COLL, *LEAF_IDS]:
        n = sum(1 for p in products if coll_id in p["collections"])
        print(f"  {coll_id}: {n}", flush=True)
    if failed:
        print(f"Failed PLPs: {failed}", flush=True)


if __name__ == "__main__":
    main()
