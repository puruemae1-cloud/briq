#!/usr/bin/env python3
"""Scrape Gucci UK men's shoes + PDP images.

Mirrors scrape-gc-womens-shoes.py / scrape-gc-mens-handbags.py: productgrid
leaves + modern PLP supplement + catalog API + DarkGray images into
public/products/gc-pdp/. Writes gc-mens-shoes-catalog-raw.json.

Official hub:
https://www.gucci.com/uk/en_gb/ca/men/shoes-for-men-c-men-shoes
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

OUT_RAW = ROOT / "src/data/gc/gc-mens-shoes-catalog-raw.json"
PDP_CACHE = ROOT / "src/data/gc/gc-pdp-cache.json"
IMG_ROOT = ROOT / "public/products/gc-pdp"

BASE = "https://www.gucci.com"
GRID = f"{BASE}/uk/en_gb/c/productgrid"
CATALOG = "https://prod-catalog-api.guccidigital.io/v1/products"
ORIGIN = "https://www.gucci.com"
WARM_URL = f"{BASE}/uk/en_gb/ca/men/shoes-for-men-c-men-shoes"

# Official Shoes leaves (Gucci UK men shoes nav) → Briq collection ids
# categoryCode is the URL segment after -c-
COLLECTIONS: list[tuple[str, str, str]] = [
    ("gc-men-sneakers", "Trainers", "men-shoes-sneakers"),
    (
        "gc-men-loafers-moccasins",
        "Loafers & Moccasins",
        "men-shoes-moccasins-and-loafers",
    ),
    (
        "gc-men-slides-sandals",
        "Slides & Sandals",
        "men-shoes-sandals",
    ),
    ("gc-men-driving", "Driving shoes", "men-shoes-drivers"),
    ("gc-men-lace-ups", "Lace Up Shoes", "men-shoes-lace-ups"),
    (
        "gc-men-boots",
        "Boots & Ankle Boots",
        "men-shoes-boots",
    ),
]

ALL_SHOES_CODE = "men-shoes"
PARENT_COLL = "gc-men-shoes"
PARENT_COLLS = ("gc-men-shoes", "gc-shoes-mens", "gucci-shoes")
MAX_WORKERS = 6
IMG_WORKERS = 8

# Official modern PLP paths (hub + 6 leaves)
MODERN_PLP_PATHS: list[tuple[str, str]] = [
    (PARENT_COLL, "/uk/en_gb/ca/men/shoes-for-men-c-men-shoes"),
    (
        "gc-men-sneakers",
        "/uk/en_gb/ca/men/shoes-for-men/sneakers-for-men-c-men-shoes-sneakers",
    ),
    (
        "gc-men-loafers-moccasins",
        "/uk/en_gb/ca/men/shoes-for-men/"
        "loafers-moccasins-for-men-c-men-shoes-moccasins-and-loafers",
    ),
    (
        "gc-men-slides-sandals",
        "/uk/en_gb/ca/men/shoes-for-men/"
        "slides-sandals-for-men-c-men-shoes-sandals",
    ),
    (
        "gc-men-driving",
        "/uk/en_gb/ca/men/shoes-for-men/driving-for-men-c-men-shoes-drivers",
    ),
    (
        "gc-men-lace-ups",
        "/uk/en_gb/ca/men/shoes-for-men/"
        "lace-up-shoes-for-men-c-men-shoes-lace-ups",
    ),
    (
        "gc-men-boots",
        "/uk/en_gb/ca/men/shoes-for-men/"
        "boots-ankle-boot-for-men-c-men-shoes-boots",
    ),
]


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
    """Keep DarkGray studio crops — matches gucci.com shoes PLP/PDP look."""
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
            # Do not whiten — DarkGray studio mats must match gucci.com.
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


def normalize_shoe_size(size: str) -> str:
    """Catalog uses 40+ for half sizes; official chart / PDP use 40.5."""
    s = (size or "").strip()
    if s.endswith("+") and s[:-1].replace(".", "", 1).isdigit():
        return f"{s[:-1]}.5"
    return s


def extract_sizes(catalog: dict | None) -> list[dict]:
    """Return unique shoe size rows as IT sizes.

    Men's catalog API sizeDescription is UK (= official SIZE); convert to IT
    via UK + 34 so PDP labels match women's IT convention.
    """
    out: list[dict] = []
    seen: set[str] = set()
    for v in (catalog or {}).get("variants") or []:
        raw = str(v.get("sizeDescription") or "").strip()
        if not raw or raw.upper() in {"U", "OS", "ONE SIZE", "NS"}:
            continue
        # Catalog UK → IT (half sizes: 4+ → 4.5 → IT 38.5)
        s = raw
        if s.endswith("+") and s[:-1].replace(".", "", 1).isdigit():
            s = f"{s[:-1]}.5"
        try:
            uk = float(s)
            it = uk + 34.0
            size = str(int(it)) if it == int(it) else f"{it:.1f}".rstrip("0").rstrip(".")
        except ValueError:
            size = s
        key = size.upper()
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "size": size,
                "sizeUk": s if size != s else None,
                "ggSizeCode": v.get("ggSizeCode"),
                "sku": v.get("sku"),
            }
        )

    def sort_key(row: dict) -> tuple:
        s = row["size"]
        try:
            return (0, float(s))
        except ValueError:
            return (1, s.upper())

    out.sort(key=sort_key)
    return out


def expand_membership(cols: set[str]) -> set[str]:
    out = set(cols)
    out.update(PARENT_COLLS)
    return out


def fetch_modern_plp_style_codes(
    s: cffi_requests.Session, category_path: str, max_page: int = 10
) -> list[str]:
    """Collect styleCodes from the Next.js PLP RSC payload.

    Legacy /c/productgrid can under-count vs the live PLP — scan until two
    consecutive pages add nothing.
    """
    seen: dict[str, None] = {}
    stagnant = 0
    for page in range(0, max_page + 1):
        url = f"{BASE}{category_path}" + (f"?page={page}" if page else "")
        try:
            r = s.get(
                url,
                headers={
                    **headers_html(),
                    "Accept": "text/x-component",
                    "RSC": "1",
                },
                impersonate="chrome124",
                timeout=90,
            )
            if r.status_code != 200:
                stagnant += 1
                if stagnant >= 2 and page > 0:
                    break
                continue
            text = r.text
        except Exception as e:
            print(f"  modern PLP page={page} fail: {e}", flush=True)
            stagnant += 1
            if stagnant >= 2 and page > 0:
                break
            continue

        before = len(seen)
        for pat in (
            r'styleCode":"([0-9A-Za-z]+)"',
            r'styleCode\\":\\"([0-9A-Za-z]+)\\"',
            r"-p-([0-9A-Za-z]{10,20})",
        ):
            for m in re.finditer(pat, text):
                code = m.group(1)
                if "99999" in code or len(code) < 10:
                    continue
                seen.setdefault(code, None)
        added = len(seen) - before
        print(
            f"  modern PLP page={page} +{added} (total {len(seen)})",
            flush=True,
        )
        if page > 0 and added == 0:
            stagnant += 1
            if stagnant >= 2:
                break
        else:
            stagnant = 0
    return list(seen.keys())


def leaf_from_pdp_url(url: str) -> str | None:
    """Map a mens-shoe PDP URL path segment to a Briq leaf collection id."""
    u = (url or "").lower()
    if "sneaker" in u or "trainer" in u:
        return "gc-men-sneakers"
    if "loafer" in u or "moccasin" in u:
        return "gc-men-loafers-moccasins"
    if "driver" in u or "driving" in u:
        return "gc-men-driving"
    if "lace-up" in u or "lace_up" in u or "oxford" in u or "derby" in u:
        return "gc-men-lace-ups"
    if "boot" in u:
        return "gc-men-boots"
    if "sandal" in u or "slide" in u or "thong" in u:
        return "gc-men-slides-sandals"
    return None


def resolve_pdp_link(
    s: cffi_requests.Session, code: str, title: str, sibling_url: str = ""
) -> str:
    """Best-effort PDP path for SKUs absent from the legacy productgrid."""
    guesses: list[str] = []
    if sibling_url:
        guesses.append(re.sub(r"-p-[0-9A-Za-z]+$", f"-p-{code}", sibling_url))
    slug = re.sub(r"[^a-z0-9]+", "-", (title or "").lower()).strip("-") or "product"
    for folder in (
        "sneakers-for-men",
        "loafers-moccasins-for-men",
        "slides-sandals-for-men",
        "driving-for-men",
        "lace-up-shoes-for-men",
        "boots-ankle-boot-for-men",
    ):
        guesses.append(
            f"/uk/en_gb/pr/men/shoes-for-men/{folder}/{slug}-p-{code}"
        )
    for path in guesses:
        url = path if path.startswith("http") else BASE + path
        try:
            r = s.get(
                url,
                headers=headers_html(),
                impersonate="chrome124",
                timeout=60,
                allow_redirects=True,
            )
            if r.status_code == 200 and code in r.url:
                return r.url.replace(BASE, "") if r.url.startswith(BASE) else r.url
        except Exception:
            continue
    return ""


def stub_card_from_catalog(
    s: cffi_requests.Session,
    catalog: dict | None,
    code: str,
    sibling_url: str = "",
    title_fallback: str = "",
) -> dict:
    """Minimal productgrid-shaped card so enrich() can proceed for modern-only SKUs."""
    en = (
        pick_translation(catalog or {}, "en_GB")
        or pick_translation(catalog or {}, "en")
        or {}
    )
    name = en.get("name") or title_fallback or code
    variant = en.get("variationDescription") or ""
    gbp = gbp_from_catalog(catalog or {})
    price_label = None
    if gbp is not None:
        price_label = f"£ {int(gbp)}" if float(gbp).is_integer() else f"£ {gbp}"
    link = resolve_pdp_link(s, code, name, sibling_url=sibling_url)
    return {
        "productCode": code,
        "productName": name,
        "variant": variant,
        "price": price_label,
        "rawPrice": gbp,
        "productLink": link,
        "showOutOfStockLabel": False,
        "inStockEntry": True,
        "label": None,
        "isDiyProduct": False,
    }


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

    print(f"=== {PARENT_COLL} ({ALL_SHOES_CODE})", flush=True)
    all_items = fetch_grid_category(s, ALL_SHOES_CODE)
    plp_meta[PARENT_COLL] = {
        "label": "Shoes / View All",
        "categoryCode": ALL_SHOES_CODE,
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

    # Supplement from modern Next.js PLP (productgrid can under-count).
    sibling_url = ""
    for _c, it in cards.items():
        if it.get("productLink"):
            sibling_url = it["productLink"]
            if not sibling_url.startswith("http"):
                sibling_url = abs_url(
                    sibling_url
                    if sibling_url.startswith("/uk/")
                    else f"/uk/en_gb{sibling_url}"
                )
            break

    for coll_id, plp_path in MODERN_PLP_PATHS:
        print(f"=== modern PLP {coll_id}", flush=True)
        modern_codes = fetch_modern_plp_style_codes(s, plp_path)
        if not modern_codes:
            continue
        missing_modern = [c for c in modern_codes if c not in cards]
        print(
            f"  modern {coll_id}: {len(modern_codes)} "
            f"(+{len(missing_modern)} missing from productgrid)",
            flush=True,
        )
        extra = expand_membership(
            {coll_id} if coll_id != PARENT_COLL else {PARENT_COLL}
        )
        for code in modern_codes:
            membership.setdefault(code, set()).update(extra)
        for code in missing_modern:
            catalog = fetch_catalog(s, code)
            cards[code] = stub_card_from_catalog(
                s, catalog, code, sibling_url=sibling_url
            )
            # Infer leaf from PDP URL when leaf modern PLPs return empty RSC.
            link = cards[code].get("productLink") or ""
            leaf = leaf_from_pdp_url(link)
            if leaf and coll_id == PARENT_COLL:
                membership.setdefault(code, set()).update(expand_membership({leaf}))
            cache[code] = {
                "catalog": catalog,
                "pdpImages": [],
                "updatedAt": datetime.now(timezone.utc).isoformat(),
            }
        if coll_id in plp_meta:
            plp_meta[coll_id]["count"] = max(
                plp_meta[coll_id].get("count") or 0, len(modern_codes)
            )
            plp_meta[coll_id]["modernPlpCount"] = len(modern_codes)
        else:
            plp_meta[coll_id] = {
                "label": coll_id,
                "categoryCode": "",
                "count": len(modern_codes),
                "modernPlpCount": len(modern_codes),
            }

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
            "collections": sorted(membership.get(code) or []),
            "inStock": in_stock,
            "label": item.get("label"),
            "sizes": sizes,
            "translationEn": en,
            "translationKo": ko,
            "kind": "mens-shoes",
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
