#!/usr/bin/env python3
"""Scrape Prada GB women's accessories (non-SLG) + PDP images.

Source hub: https://www.prada.com/gb/en/womens/accessories/c/10079EU
PLP membership uses Algolia CategoriesEnriched ``10079EU|false|false``.
Skips small leather goods (10340EU hub — scraped separately).
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
from urllib.parse import quote

from curl_cffi import requests as cffi_requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pr_download_image import download_image  # noqa: E402

OUT_RAW = ROOT / "src/data/pr/pr-womens-accessories-catalog-raw.json"
PDP_CACHE = ROOT / "src/data/pr/pr-womens-accessories-pdp-cache.json"
IMG_ROOT = ROOT / "public/products/pr-pdp"

BASE = "https://www.prada.com"
HUB_URL = f"{BASE}/gb/en/womens/accessories/c/10079EU"
HUB_CID = "10079EU"
HUB_ENRICHED = f"{HUB_CID}|false|false"

ALGOLIA_APP = "OCPT799JD8"
ALGOLIA_KEY = "ff0caf66bf2f4d3b10b59c95711ddaf8"
ALGOLIA_INDEX = "PLP_COLOR_PRADA_Online_GB"

# Official leaf PLPs under women's accessories (prada.com GB hub menu)
LEAVES: list[tuple[str, str, str]] = [
    ("pr-women-sunglasses", "Sunglasses", "10086EU"),
    ("pr-women-silks-scarves", "Silks and scarves", "10085EU"),
    ("pr-women-hats-gloves", "Hats and gloves", "10082EU"),
    ("pr-women-headbands-hair", "Headbands and hair accessories", "10083EU"),
    ("pr-women-bag-charms", "Bag charms and keychains", "10084EU"),
    ("pr-women-jewels", "Jewels", "10621EU"),
    ("pr-women-belts", "Belts", "10080EU"),
    ("pr-women-pouches", "Pouches", "10705EU"),
]
LEAF_BY_CID = {cid: lid for lid, _label, cid in LEAVES}
BC_TO_LEAF = {
    "Sunglasses": "pr-women-sunglasses",
    "Silks and scarves": "pr-women-silks-scarves",
    "Hats and gloves": "pr-women-hats-gloves",
    "Headbands and hair accessories": "pr-women-headbands-hair",
    "Bag charms and keychains": "pr-women-bag-charms",
    "Jewels": "pr-women-jewels",
    "Belts": "pr-women-belts",
    "Pouches": "pr-women-pouches",
}
LEAF_SLUG = {
    "pr-women-sunglasses": "sunglasses",
    "pr-women-silks-scarves": "silks-and-scarves",
    "pr-women-hats-gloves": "hats-and-gloves",
    "pr-women-headbands-hair": "headbands-and-hair-accessories",
    "pr-women-bag-charms": "bag-charms-and-keychains",
    "pr-women-jewels": "jewels",
    "pr-women-belts": "belts",
    "pr-women-pouches": "pouches",
}

SLG_BC = {
    "Small wallets",
    "Card holders",
    "Large wallets",
    "High-Tech accessories",
    "Wallets on chain",
}
SLG_CIDS = {"10340EU", "10341EU", "10342EU", "10343EU", "10344EU", "11063EU"}

PARENT_COLS = ["prada", "prada-accessories", "pr-women-accessories"]
MAX_WORKERS = 6
IMG_WORKERS = 10
MAX_IMAGES = 10


def session() -> cffi_requests.Session:
    return cffi_requests.Session()


def headers_html(referer: str = HUB_URL) -> dict:
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


def clean_dam_url(u: str | None) -> str:
    """Normalize to original dam JPEG (strip srcset / cq5dam / junk)."""
    if not u:
        return ""
    u = abs_url(u.strip().rstrip(","))
    # srcset may concatenate several candidates — take first URL fragment
    if "http" in u[8:]:
        # already has scheme; if somehow doubled, keep up to first space
        u = u.split()[0]
    u = u.split()[0].rstrip(",")
    # strip rendition path → original asset
    if "/_jcr_content/renditions/" in u:
        u = u.split("/_jcr_content/renditions/")[0]
    if not u.lower().endswith(".jpg"):
        # try to cut at .jpg
        m = re.search(r"(https?://\S+?\.jpg)", u, re.I)
        if m:
            u = m.group(1)
    return u


def media_url(path_or_url: str) -> str:
    return clean_dam_url(path_or_url)


def shot_key(u: str) -> str:
    u = clean_dam_url(u)
    fn = (u or "").split("/")[-1]
    m = re.match(r"(.+?)(?:\.jpg)?$", fn, re.I)
    return m.group(1) if m else fn


def algolia_query(s: cffi_requests.Session, params: str) -> dict:
    url = f"https://{ALGOLIA_APP}-dsn.algolia.net/1/indexes/*/queries"
    headers = {
        "X-Algolia-Application-Id": ALGOLIA_APP,
        "X-Algolia-API-Key": ALGOLIA_KEY,
        "Content-Type": "application/json",
    }
    body = {"requests": [{"indexName": ALGOLIA_INDEX, "params": params}]}
    for attempt in range(4):
        try:
            r = s.post(url, headers=headers, json=body, impersonate="chrome124", timeout=60)
            r.raise_for_status()
            return (r.json().get("results") or [{}])[0]
        except Exception as e:
            if attempt == 3:
                raise
            time.sleep(1.2 * (attempt + 1))
            print(f"  algolia retry: {e}", flush=True)
    return {}


def fetch_hub_hits(s: cffi_requests.Session) -> list[dict]:
    hits: list[dict] = []
    page = 0
    while True:
        params = (
            f"query=&hitsPerPage=100&page={page}"
            f"&facetFilters={quote(json.dumps([f'CategoriesEnriched:{HUB_ENRICHED}']))}"
        )
        res = algolia_query(s, params)
        batch = res.get("hits") or []
        hits.extend(batch)
        nb_pages = int(res.get("nbPages") or 1)
        print(f"  hub algolia page {page + 1}/{nb_pages} (+{len(batch)})", flush=True)
        page += 1
        if page >= nb_pages:
            break
        time.sleep(0.1)
    return hits


def color_en(hit: dict) -> str:
    raw = ((hit.get("Color") or {}).get("en_GB") or "").split("|||")[0].strip()
    return raw


def norm_size_key(label: str) -> str:
    return label.strip().upper().replace(",", ".")


def shoe_size_sort_key(label: str) -> tuple:
    s = norm_size_key(label)
    if s in {"TU", "OS", "ONE SIZE", "ONESIZE"}:
        return (0, 0, s)
    m = re.match(r"^(\d+(?:\.\d+)?)(?:/(\d+(?:\.\d+)?))?$", s)
    if m:
        return (1, float(m.group(1)), s)
    return (2, 0, s)


def sizes_from_hit(hit: dict) -> list[dict]:
    in_stock_labels = {
        norm_size_key(str(sz.get("label") or ""))
        for sz in (hit.get("availableSizes") or [])
        if str(sz.get("label") or "").strip()
    }
    code_by_label: dict[str, str] = {}
    for src in (hit.get("availableSizesStore") or [], hit.get("availableSizes") or []):
        for sz in src:
            label = str(sz.get("label") or "").strip()
            if label:
                code_by_label.setdefault(norm_size_key(label), str(sz.get("code") or ""))
    all_labels: list[str] = []
    seen: set[str] = set()

    def add_label(raw: str) -> None:
        label = raw.strip()
        if not label:
            return
        key = norm_size_key(label)
        if key in seen:
            return
        seen.add(key)
        all_labels.append(label)

    for label in (hit.get("SizeGroupStore") or {}).get("en_GB") or []:
        add_label(str(label))
    for sz in hit.get("availableSizesStore") or []:
        add_label(str(sz.get("label") or ""))
    for sz in hit.get("availableSizes") or []:
        add_label(str(sz.get("label") or ""))
    out = [
        {
            "size": label,
            "code": code_by_label.get(norm_size_key(label), ""),
            "inStock": norm_size_key(label) in in_stock_labels,
        }
        for label in all_labels
    ]
    out.sort(key=lambda x: shoe_size_sort_key(x["size"]))
    return out


def is_slg_hit(hit: dict) -> bool:
    bc = ((hit.get("Breadcrumbs") or {}).get("level_3") or {}).get("en_GB") or ""
    if bc in SLG_BC:
        return True
    cats = set(hit.get("Categories") or [])
    return bool(cats & SLG_CIDS)


def infer_leaf_from_name(name: str) -> str | None:
    n = (name or "").lower()
    if "sunglass" in n or "eyewear" in n:
        return "pr-women-sunglasses"
    if any(x in n for x in ("scarf", "silk", "bandana", "stole")):
        return "pr-women-silks-scarves"
    if any(x in n for x in ("glove", "beanie", "hat", "cap")):
        return "pr-women-hats-gloves"
    if any(x in n for x in ("hair clip", "headband", "scrunchie", "barrette")):
        return "pr-women-headbands-hair"
    if any(x in n for x in ("keychain", "key ring", "charm", "key holder")):
        return "pr-women-bag-charms"
    if any(x in n for x in ("ring", "necklace", "bracelet", "earring", "brooch")):
        return "pr-women-jewels"
    if "belt" in n:
        return "pr-women-belts"
    if "pouch" in n or "case" in n:
        return "pr-women-pouches"
    return None


def collections_for(hit: dict) -> list[str]:
    cols = set(PARENT_COLS)
    cats = hit.get("Categories") or []
    for cid in cats:
        lid = LEAF_BY_CID.get(cid)
        if lid:
            cols.add(lid)
    if not any(c in LEAF_BY_CID.values() for c in cols):
        bc = ((hit.get("Breadcrumbs") or {}).get("level_3") or {}).get("en_GB") or ""
        fallback = BC_TO_LEAF.get(bc)
        if fallback:
            cols.add(fallback)
    if not any(c in LEAF_BY_CID.values() for c in cols):
        name = ((hit.get("ProductName") or {}).get("en_GB") or "")
        inferred = infer_leaf_from_name(name)
        if inferred:
            cols.add(inferred)
    if not any(c in LEAF_BY_CID.values() for c in cols):
        cols.add("pr-women-pouches")
    return sorted(cols)


def primary_leaf(cols: list[str], hit: dict) -> str:
    bc = ((hit.get("Breadcrumbs") or {}).get("level_3") or {}).get("en_GB") or ""
    mapped = BC_TO_LEAF.get(bc)
    if mapped and mapped in cols:
        return mapped
    for lid, _label, _cid in LEAVES:
        if lid in cols:
            return lid
    name = ((hit.get("ProductName") or {}).get("en_GB") or "")
    return infer_leaf_from_name(name) or "pr-women-pouches"


def parse_pdp(html: str, sku: str) -> dict:
    desc = ""
    m = re.search(
        r'<meta\s+name="description"\s+content="([^"]+)"',
        html,
        re.I,
    )
    if m:
        desc = m.group(1).strip()
    if not desc:
        m = re.search(
            r'whitespace-pre-wrap">([^<]{40,800})</p>',
            html,
        )
        if m:
            desc = re.sub(r"\s+", " ", m.group(1)).strip()

    details: list[str] = []
    # bullets after Product code
    block = ""
    i = html.find("Product code:")
    if i >= 0:
        block = html[i : i + 4000]
        for li in re.findall(r"<li>(.*?)</li>", block, re.S | re.I):
            text = re.sub(r"<[^>]+>", " ", li)
            text = re.sub(r"\s+", " ", text).strip()
            if not text or text.lower().startswith("product code"):
                continue
            if text.lower().startswith("height:") or text.lower().startswith("width:"):
                continue
            if text.lower().startswith("length:") or text.lower().startswith("depth:"):
                continue
            details.append(text)

    dims: dict[str, str] = {}
    for label in ("Height", "Width", "Length", "Depth"):
        mm = re.search(rf"{label}:\s*([0-9.]+)\s*cm", html, re.I)
        if mm:
            dims[label.lower()] = f"{mm.group(1)} cm"

    materials_care: list[str] = []
    m = re.search(
        r'data-element="materials-and-care-accordion".{0,200}?</button></h2>'
        r'<div[^>]*data-element="accordion-content"[^>]*>(.*?)</div>',
        html,
        re.S | re.I,
    )
    if m:
        for li in re.findall(r"<li>(.*?)</li>", m.group(1), re.S | re.I):
            text = re.sub(r"<[^>]+>", " ", li)
            text = re.sub(r"\s+", " ", text).strip()
            if text:
                materials_care.append(text)
        # also paragraphs
        for p in re.findall(r"<p[^>]*>(.*?)</p>", m.group(1), re.S | re.I):
            text = re.sub(r"<[^>]+>", " ", p)
            text = re.sub(r"\s+", " ", text).strip()
            if text and len(text) > 3:
                materials_care.append(text)

    # Gallery: collect unique dam JPG bases (ignore cq5dam / srcset noise)
    found = re.findall(
        r"https://www\.prada\.com/content/dam/pradabkg_products/[^\"'\s,]+\.jpg",
        html,
        re.I,
    )
    bases: list[str] = []
    seen_keys: set[str] = set()
    for raw in found:
        u = clean_dam_url(raw)
        if not u or sku not in u:
            continue
        k = shot_key(u)
        if k in seen_keys:
            continue
        seen_keys.add(k)
        bases.append(u)

    def rank(path: str) -> tuple[int, str]:
        fn = path.split("/")[-1].upper()
        order = [
            "_SLF.JPG",
            "_SLR.JPG",
            "_SLB.JPG",
            "_SLD.JPG",
            "_SLDA.JPG",
            "_SLO.JPG",
            "_MDL.JPG",
            "_MDLA.JPG",
            "_MDLB.JPG",
            "_MDF.JPG",
        ]
        for i, suf in enumerate(order):
            if fn.endswith(suf):
                return (i, fn)
        return (50, fn)

    bases = sorted(bases, key=rank)
    images = bases

    price = None
    pm = re.search(r"£\s*([\d,]+(?:\.\d+)?)", html)
    if pm:
        try:
            price = float(pm.group(1).replace(",", ""))
        except ValueError:
            pass

    title = ""
    tm = re.search(r'<meta\s+name="og:title"\s+content="([^"]+)"', html, re.I)
    if tm:
        title = tm.group(1).strip()
        title = re.sub(r"\s*\|\s*PRADA.*$", "", title, flags=re.I).strip()
        # strip leading colour word duplicated in og title sometimes
        title = re.sub(
            r"^(Black|White|Forest|Beige|Brown|Blue|Red|Pink|Green|Grey|Gray|Navy|Ivory|Camel|Silver|Gold)\s+",
            "",
            title,
            flags=re.I,
        ).strip()

    return {
        "description": desc,
        "details": details,
        "dimensions": dims,
        "materialsCare": materials_care,
        "images": images,
        "gbpPrice": price,
        "title": title,
    }


def fetch_pdp(s: cffi_requests.Session, url: str, sku: str) -> dict:
    try:
        r = s.get(url, headers=headers_html(), impersonate="chrome124", timeout=90)
        if r.status_code != 200:
            return {}
        return parse_pdp(r.text, sku)
    except Exception as e:
        print(f"  pdp fail {sku}: {e}", flush=True)
        return {}


def hit_to_seed(hit: dict) -> dict:
    sku = hit.get("objectID") or hit.get("ParentVariant") or ""
    name = ((hit.get("ProductName") or {}).get("en_GB") or sku).strip()
    price = (hit.get("Price") or {}).get("Value")
    url_path = ((hit.get("UrlReconstructed") or {}).get("en_GB") or "").strip()
    if url_path and not url_path.startswith("/gb/"):
        url_path = "/gb/en" + url_path
    source = abs_url(url_path) if url_path else ""
    imgs = hit.get("Images") or {}
    plp = media_url(imgs.get("PLPBKG") or "")
    hover = media_url(imgs.get("HoverBKG") or "")
    cols = collections_for(hit)
    length = (hit.get("ProductLength") or {}).get("Value")
    width = (hit.get("ProductWidth") or {}).get("Value")
    height = (hit.get("ProductHeight") or {}).get("Value")
    dims = {}
    if height:
        dims["height"] = f"{height} cm"
    if width:
        dims["width"] = f"{width} cm"
    if length:
        dims["length"] = f"{length} cm"
    material = ((hit.get("MaterialGroup") or {}).get("en_GB") or "").strip()
    avail = hit.get("Availability") or ""
    parent = (hit.get("ParentProduct") or "").strip() or sku.rsplit("_", 1)[0]
    color_code = ((hit.get("Color") or {}).get("Code") or "").strip()
    color_hex = ""
    raw_color = ((hit.get("Color") or {}).get("en_GB") or "")
    if "|||" in raw_color:
        color_hex = raw_color.split("|||")[-1].strip()
    sizes = sizes_from_hit(hit)
    other = hit.get("OtherColors") or []
    return {
        "id": sku,
        "productCode": sku,
        "sku": sku,
        "parentProduct": parent,
        "officialNameEn": name,
        "title": name,
        "color": color_en(hit),
        "colorCode": color_code,
        "colorHex": color_hex,
        "otherColors": other,
        "url": source,
        "gbpPrice": float(price) if price is not None else None,
        "plpImage": plp,
        "plpHoverUrl": hover,
        "collections": cols,
        "leaf": primary_leaf(cols, hit),
        "sizes": sizes,
        "inStock": any(s["inStock"] for s in sizes)
        if sizes
        else avail != "Red",
        "availability": avail,
        "dimensions": dims,
        "material": material,
        "kind": "womens-accessories",
        "algolia": {
            "categories": hit.get("Categories"),
            "categoriesEnriched": hit.get("CategoriesEnriched"),
            "breadcrumbs": hit.get("Breadcrumbs"),
        },
    }


def main() -> None:
    OUT_RAW.parent.mkdir(parents=True, exist_ok=True)
    IMG_ROOT.mkdir(parents=True, exist_ok=True)

    cache: dict = {}
    if PDP_CACHE.exists():
        cache = json.loads(PDP_CACHE.read_text())

    s = session()
    s.get(HUB_URL, headers=headers_html(), impersonate="chrome124", timeout=90)

    print("=== Prada women's accessories hub (Algolia)", flush=True)
    hits = [h for h in fetch_hub_hits(s) if not is_slg_hit(h)]
    print(f"Hub SKUs (excl. SLG): {len(hits)}", flush=True)

    seeds = {h["objectID"]: hit_to_seed(h) for h in hits if h.get("objectID")}
    cache_lock = Lock()

    def enrich(sku: str) -> dict:
        local = session()
        row = dict(seeds[sku])
        cached = cache.get(sku) or {}
        pdp = cached.get("pdp") or {}
        # Repair any srcset-corrupted URLs from earlier runs
        if pdp.get("images"):
            repaired = []
            seen = set()
            for u in pdp["images"]:
                cu = clean_dam_url(u if isinstance(u, str) else "")
                k = shot_key(cu)
                if cu and k not in seen and " " not in cu and "," not in cu:
                    seen.add(k)
                    repaired.append(cu)
            pdp = {**pdp, "images": repaired}
        if not pdp.get("images") or not pdp.get("description"):
            if row.get("url"):
                pdp = fetch_pdp(local, row["url"], sku) or pdp
        images = [clean_dam_url(u) for u in (pdp.get("images") or [])]
        images = [u for u in images if u and " " not in u and "," not in u]
        # ensure PLP still + hover present
        for u in (row.get("plpImage"), row.get("plpHoverUrl")):
            if u and shot_key(u) not in {shot_key(x) for x in images}:
                # insert still-life first
                if u == row.get("plpImage"):
                    images = [u] + images
                else:
                    images.append(u)
        # dedupe
        out_imgs: list[str] = []
        seen: set[str] = set()
        for u in images:
            k = shot_key(u)
            if not u or k in seen:
                continue
            seen.add(k)
            out_imgs.append(u)

        gbp = row.get("gbpPrice")
        if gbp is None and pdp.get("gbpPrice") is not None:
            gbp = pdp["gbpPrice"]

        official_name = row.get("officialNameEn") or row.get("title") or sku
        dims = dict(row.get("dimensions") or {})
        dims.update(pdp.get("dimensions") or {})

        enriched = {
            **row,
            "officialNameEn": official_name,
            "title": official_name,
            "gbpPrice": float(gbp) if gbp is not None else None,
            "description": pdp.get("description") or "",
            "details": pdp.get("details") or [],
            "materialsCare": pdp.get("materialsCare") or [],
            "dimensions": dims,
            "images": out_imgs[:MAX_IMAGES],
            "plpHoverUrl": row.get("plpHoverUrl") or "",
            "scrapedAt": datetime.now(timezone.utc).isoformat(),
        }
        with cache_lock:
            cache[sku] = {
                "pdp": {
                    "description": enriched["description"],
                    "details": enriched["details"],
                    "materialsCare": enriched["materialsCare"],
                    "dimensions": enriched["dimensions"],
                    "images": enriched["images"],
                    "gbpPrice": enriched["gbpPrice"],
                    "title": enriched["title"],
                },
                "updatedAt": enriched["scrapedAt"],
            }
        return enriched

    products: list[dict] = []
    codes = sorted(seeds.keys())
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(enrich, c): c for c in codes}
        done = 0
        for fut in as_completed(futs):
            products.append(fut.result())
            done += 1
            if done % 20 == 0 or done == len(codes):
                print(f"enriched {done}/{len(codes)}", flush=True)
                with cache_lock:
                    PDP_CACHE.write_text(json.dumps(cache, ensure_ascii=False))

    products.sort(key=lambda p: p["id"])

    def dl_one(prod: dict) -> tuple[str, list[str]]:
        local = session()
        code = prod["id"]
        local_paths: list[str] = []
        for i, url in enumerate(prod.get("images") or [], start=1):
            dest = IMG_ROOT / code / f"{i}.jpg"
            if download_image(local, url, dest):
                local_paths.append(f"/products/pr-pdp/{code}/{i}.jpg")
            if i >= MAX_IMAGES:
                break
        return code, local_paths

    print("Downloading images…", flush=True)
    local_map: dict[str, list[str]] = {}
    with ThreadPoolExecutor(max_workers=IMG_WORKERS) as ex:
        futs = [ex.submit(dl_one, p) for p in products]
        done = 0
        for fut in as_completed(futs):
            code, local = fut.result()
            local_map[code] = local
            done += 1
            if done % 30 == 0 or done == len(products):
                print(f"images {done}/{len(products)}", flush=True)

    for p in products:
        locs = local_map.get(p["id"]) or []
        p["localImages"] = locs
        if locs:
            p["localImage"] = locs[0]
        hover_url = p.get("plpHoverUrl") or ""
        local_hover = None
        if hover_url and locs:
            hk = shot_key(hover_url)
            for i, remote in enumerate(p.get("images") or []):
                if shot_key(remote) == hk and i < len(locs):
                    local_hover = locs[i]
                    break
        if not local_hover and len(locs) > 1:
            # prefer MDL / hover-like second frame
            local_hover = locs[1]
        if local_hover:
            p["localHover"] = local_hover

    plp_meta = {
        "pr-women-accessories": {
            "label": "Women's accessories",
            "categoryCode": HUB_CID,
            "count": len(products),
            "url": HUB_URL,
        }
    }
    for lid, label, cid in LEAVES:
        n = sum(1 for p in products if lid in (p.get("collections") or []))
        plp_meta[lid] = {
            "label": label,
            "categoryCode": cid,
            "url": f"{BASE}/gb/en/womens/accessories/{LEAF_SLUG[lid]}/c/{cid}",
            "count": n,
        }

    payload = {
        "scrapedAt": datetime.now(timezone.utc).isoformat(),
        "source": HUB_URL,
        "collections": plp_meta,
        "count": len(products),
        "products": products,
    }
    OUT_RAW.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    PDP_CACHE.write_text(json.dumps(cache, ensure_ascii=False))
    print(f"Wrote {OUT_RAW} ({len(products)} products)", flush=True)
    for lid, label, _cid in LEAVES:
        n = sum(1 for p in products if lid in p["collections"])
        print(f"  {lid}: {n}", flush=True)
    with_img = sum(1 for p in products if p.get("localImages"))
    print(f"with local images: {with_img}/{len(products)}", flush=True)


if __name__ == "__main__":
    main()
