#!/usr/bin/env python3
"""Scrape Prada GB men's ready-to-wear (~430) in stages.

Hub: https://www.prada.com/gb/en/mens/ready-to-wear/c/10130EU
PLP set = Algolia CategoriesEnriched ``10130EU|false|false``.

  python3 scripts/scrape-pr-mens-rtw.py --stage 1 --stages 5
  python3 scripts/scrape-pr-mens-rtw.py --stage 2 --stages 5
"""
from __future__ import annotations

import argparse
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
from pr_sizes import (  # noqa: E402
    assert_no_mixed_rtw_sizes,
    rtw_sizes,
    sizes_from_hit,
    sizes_from_pdp_html,
)

OUT_RAW = ROOT / "src/data/pr/pr-mens-rtw-catalog-raw.json"
PDP_CACHE = ROOT / "src/data/pr/pr-mens-rtw-pdp-cache.json"
SEED = ROOT / "src/data/pr/pr-mens-rtw-hub-seed.json"
IMG_ROOT = ROOT / "public/products/pr-pdp"
PROGRESS = ROOT / "src/data/pr/pr-mens-rtw-stage-progress.json"

BASE = "https://www.prada.com"
HUB_URL = f"{BASE}/gb/en/mens/ready-to-wear/c/10130EU"
HUB_CID = "10130EU"
HUB_ENRICHED = f"{HUB_CID}|false|false"

ALGOLIA_APP = "OCPT799JD8"
ALGOLIA_KEY = "ff0caf66bf2f4d3b10b59c95711ddaf8"
ALGOLIA_INDEX = "PLP_COLOR_PRADA_Online_GB"

# Official leaf PLPs under men's ready-to-wear
LEAVES: list[tuple[str, str, str, str]] = [
    ("pr-men-denim", "Denim", "10131EU", "denim"),
    ("pr-men-jackets-coats", "Jackets and coats", "10132EU", "jackets-and-coats"),
    (
        "pr-men-jogging-suits-sweatshirts",
        "Jogging suits and sweatshirts",
        "10133EU",
        "jogging-suits-and-sweatshirts",
    ),
    ("pr-men-knitwear", "Knitwear", "10134EU", "knitwear"),
    ("pr-men-leather", "Leather clothing", "10135EU", "leather-clothing"),
    ("pr-men-outerwear", "Outerwear", "10136EU", "outerwear"),
    ("pr-men-pajamas-underwear", "Pajamas and underwear", "10137EU", "pajamas-and-underwear"),
    ("pr-men-shirts", "Shirts", "10138EU", "shirts"),
    ("pr-men-suits", "Suits", "10139EU", "suits"),
    ("pr-men-swimwear", "Swimwear", "10140EU", "swimwear"),
    ("pr-men-trousers-bermudas", "Trousers and bermudas", "10141EU", "trousers-and-bermudas"),
    ("pr-men-tshirts-polos", "T-shirts and polo shirts", "10142EU", "t-shirts-and-polo-shirts"),
]
LEAF_BY_CID = {cid: lid for lid, _label, cid, _slug in LEAVES}
SLUG_BY_LID = {lid: slug for lid, _label, _cid, slug in LEAVES}
BC_TO_LEAF = {
    "Denim": "pr-men-denim",
    "Jackets and coats": "pr-men-jackets-coats",
    "Jogging suits and sweatshirts": "pr-men-jogging-suits-sweatshirts",
    "Knitwear": "pr-men-knitwear",
    "Leather clothing": "pr-men-leather",
    "Outerwear": "pr-men-outerwear",
    "Pajamas and underwear": "pr-men-pajamas-underwear",
    "Shirts": "pr-men-shirts",
    "Suits": "pr-men-suits",
    "Swimwear": "pr-men-swimwear",
    "Trousers and bermudas": "pr-men-trousers-bermudas",
    "T-shirts and polo shirts": "pr-men-tshirts-polos",
}

PARENT_COLS = ["prada", "prada-luxury", "pr-men", "pr-men-rtw"]
MAX_WORKERS = 4
IMG_WORKERS = 4
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
    if not u:
        return ""
    u = abs_url(u.strip().split()[0].rstrip(","))
    if "/_jcr_content/renditions/" in u:
        u = u.split("/_jcr_content/renditions/")[0]
    m = re.search(r"(https?://\S+?\.jpg)", u, re.I)
    return m.group(1) if m else (u if u.lower().endswith(".jpg") else "")


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
            r = s.post(
                url, headers=headers, json=body, impersonate="chrome124", timeout=60
            )
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
        print(f"  hub page {page + 1}/{nb_pages} (+{len(batch)})", flush=True)
        page += 1
        if page >= nb_pages:
            break
        time.sleep(0.08)
    return hits


def color_en(hit: dict) -> str:
    return ((hit.get("Color") or {}).get("en_GB") or "").split("|||")[0].strip()


def collections_for(hit: dict) -> list[str]:
    cols = set(PARENT_COLS)
    for cid in hit.get("Categories") or []:
        lid = LEAF_BY_CID.get(cid)
        if lid:
            cols.add(lid)
    if not any(c.startswith("pr-men-") and c != "pr-men-rtw" for c in cols):
        bc = ((hit.get("Breadcrumbs") or {}).get("level_3") or {}).get("en_GB") or ""
        if BC_TO_LEAF.get(bc):
            cols.add(BC_TO_LEAF[bc])
    return sorted(cols)


def primary_leaf(cols: list[str], hit: dict) -> str:
    bc = ((hit.get("Breadcrumbs") or {}).get("level_3") or {}).get("en_GB") or ""
    mapped = BC_TO_LEAF.get(bc)
    if mapped and mapped in cols:
        return mapped
    for lid, _label, _cid, _slug in LEAVES:
        if lid in cols:
            return lid
    return "pr-men-rtw"


def parse_pdp(html: str, sku: str) -> dict:
    desc = ""
    m = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', html, re.I)
    if m:
        desc = m.group(1).strip()
    details: list[str] = []
    i = html.find("Product code:")
    if i >= 0:
        for li in re.findall(r"<li>(.*?)</li>", html[i : i + 5000], re.S | re.I):
            text = re.sub(r"<[^>]+>", " ", li)
            text = re.sub(r"\s+", " ", text).strip()
            if not text or text.lower().startswith("product code"):
                continue
            if text.lower().startswith(("height:", "width:", "length:", "depth:")):
                continue
            details.append(text)

    materials_care: list[str] = []
    m = re.search(
        r'data-element="materials-and-care-accordion".{0,200}?</button></h2>'
        r'<div[^>]*data-element="accordion-content"[^>]*>(.*?)</div>',
        html,
        re.S | re.I,
    )
    if m:
        for li in re.findall(r"<li>(.*?)</li>", m.group(1), re.S | re.I):
            text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", li)).strip()
            if text:
                materials_care.append(text)

    found = re.findall(
        r"https://www\.prada\.com/content/dam/pradabkg_products/[^\"'\s,]+\.jpg",
        html,
        re.I,
    )
    bases: list[str] = []
    seen: set[str] = set()
    for raw in found:
        u = clean_dam_url(raw)
        if not u or sku not in u:
            continue
        k = shot_key(u)
        if k in seen:
            continue
        seen.add(k)
        bases.append(u)

    def rank(path: str) -> tuple[int, str]:
        fn = path.split("/")[-1].upper()
        order = [
            "_SLF.JPG",
            "_SLR.JPG",
            "_SLB.JPG",
            "_MDL.JPG",
            "_MDLA.JPG",
            "_MDLB.JPG",
            "_MDF.JPG",
        ]
        for idx, suf in enumerate(order):
            if fn.endswith(suf):
                return (idx, fn)
        return (50, fn)

    images = sorted(bases, key=rank)

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
        title = re.sub(r"\s*\|\s*PRADA.*$", "", tm.group(1).strip(), flags=re.I).strip()

    out = {
        "description": desc,
        "details": details,
        "materialsCare": materials_care,
        "images": images,
        "gbpPrice": price,
        "title": title,
    }
    pdp_sizes = sizes_from_pdp_html(html)
    if pdp_sizes:
        out["sizes"] = pdp_sizes
    return out


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
    imgs = hit.get("Images") or {}
    cols = collections_for(hit)
    material = ((hit.get("MaterialGroup") or {}).get("en_GB") or "").strip()
    sizes = sizes_from_hit(hit)
    return {
        "id": sku,
        "productCode": sku,
        "sku": sku,
        "officialNameEn": name,
        "title": name,
        "color": color_en(hit),
        "url": abs_url(url_path),
        "gbpPrice": float(price) if price is not None else None,
        "plpImage": media_url(imgs.get("PLPBKG") or ""),
        "plpHoverUrl": media_url(imgs.get("HoverBKG") or ""),
        "collections": cols,
        "leaf": primary_leaf(cols, hit),
        "sizes": sizes,
        "inStock": any(s["inStock"] for s in sizes)
        if sizes
        else (hit.get("Availability") or "") != "Red",
        "availability": hit.get("Availability") or "",
        "material": material,
        "kind": "mens-rtw",
        "algolia": {
            "categories": hit.get("Categories"),
            "breadcrumbs": hit.get("Breadcrumbs"),
        },
    }


def stage_slice(n: int, stage: int, stages: int) -> tuple[int, int]:
    stage = max(1, min(stage, stages))
    start = ((stage - 1) * n) // stages
    end = (stage * n) // stages
    return start, end


def refresh_sizes_from_algolia() -> None:
    if not OUT_RAW.exists():
        raise SystemExit(f"Missing {OUT_RAW}")

    payload = json.loads(OUT_RAW.read_text())
    products: list[dict] = payload.get("products") or []
    if not products:
        raise SystemExit("No products in raw catalogue")

    s = session()
    headers = {
        "X-Algolia-Application-Id": ALGOLIA_APP,
        "X-Algolia-API-Key": ALGOLIA_KEY,
    }
    updated = 0
    for i, row in enumerate(products, start=1):
        sku = row.get("id") or row.get("sku")
        if not sku:
            continue
        try:
            hit = s.get(
                f"https://{ALGOLIA_APP}-dsn.algolia.net/1/indexes/"
                f"{ALGOLIA_INDEX}/{quote(sku)}",
                headers=headers,
                impersonate="chrome124",
                timeout=45,
            ).json()
        except Exception as e:
            print(f"  skip {sku}: {e}", flush=True)
            continue
        if not hit.get("objectID"):
            continue
        pdp_html = ""
        url = row.get("url") or ""
        if url:
            try:
                pr = s.get(
                    url,
                    headers=headers_html(),
                    impersonate="chrome124",
                    timeout=90,
                )
                if pr.status_code == 200:
                    pdp_html = pr.text
            except Exception as e:
                print(f"  pdp skip {sku}: {e}", flush=True)
        sizes = rtw_sizes(hit, pdp_html or None)
        row["sizes"] = sizes
        row["inStock"] = (
            any(sz["inStock"] for sz in sizes)
            if sizes
            else (hit.get("Availability") or "") != "Red"
        )
        updated += 1
        if i % 50 == 0 or i == len(products):
            print(f"  refreshed sizes {i}/{len(products)}", flush=True)
        time.sleep(0.05)

    payload["products"] = products
    assert_no_mixed_rtw_sizes(products, context="men's RTW size refresh")
    payload["sizesRefreshedAt"] = datetime.now(timezone.utc).isoformat()
    OUT_RAW.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"Refreshed sizes for {updated} products → {OUT_RAW}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", type=int, default=1)
    ap.add_argument("--stages", type=int, default=5)
    ap.add_argument("--refresh-seed", action="store_true")
    ap.add_argument(
        "--refresh-sizes",
        action="store_true",
        help="Re-fetch PDP picker sizes (+ Algolia stock) for products already in raw",
    )
    args = ap.parse_args()

    if args.refresh_sizes:
        refresh_sizes_from_algolia()
        return

    OUT_RAW.parent.mkdir(parents=True, exist_ok=True)
    IMG_ROOT.mkdir(parents=True, exist_ok=True)

    cache: dict = {}
    if PDP_CACHE.exists():
        cache = json.loads(PDP_CACHE.read_text())

    s = session()
    s.get(HUB_URL, headers=headers_html(), impersonate="chrome124", timeout=90)

    if args.refresh_seed or not SEED.exists():
        print("=== fetching hub seed (Algolia)", flush=True)
        hits = fetch_hub_hits(s)
        seeds = [hit_to_seed(h) for h in hits if h.get("objectID")]
        seeds.sort(key=lambda x: x["id"])
        SEED.write_text(
            json.dumps(
                {
                    "scrapedAt": datetime.now(timezone.utc).isoformat(),
                    "source": HUB_URL,
                    "count": len(seeds),
                    "products": seeds,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        print(f"Wrote seed {len(seeds)} → {SEED}", flush=True)
    else:
        seeds = json.loads(SEED.read_text())["products"]
        print(f"Loaded seed {len(seeds)} from {SEED}", flush=True)

    start, end = stage_slice(len(seeds), args.stage, args.stages)
    batch = seeds[start:end]
    print(
        f"=== STAGE {args.stage}/{args.stages}: products [{start}:{end}] "
        f"({len(batch)} SKUs)",
        flush=True,
    )

    existing: dict[str, dict] = {}
    if OUT_RAW.exists():
        for p in json.loads(OUT_RAW.read_text()).get("products") or []:
            if p.get("id"):
                existing[p["id"]] = p

    cache_lock = Lock()

    def enrich(seed: dict) -> dict:
        sku = seed["id"]
        local = session()
        row = dict(seed)
        cached = cache.get(sku) or {}
        pdp = cached.get("pdp") or {}
        if pdp.get("images"):
            repaired = []
            seen = set()
            for u in pdp["images"]:
                cu = clean_dam_url(u if isinstance(u, str) else "")
                k = shot_key(cu)
                if cu and k not in seen and " " not in cu:
                    seen.add(k)
                    repaired.append(cu)
            pdp = {**pdp, "images": repaired}
        if not pdp.get("images") or not pdp.get("description"):
            if row.get("url"):
                pdp = fetch_pdp(local, row["url"], sku) or pdp
        images = [clean_dam_url(u) for u in (pdp.get("images") or [])]
        images = [u for u in images if u and " " not in u]
        for u in (row.get("plpImage"), row.get("plpHoverUrl")):
            if u and shot_key(u) not in {shot_key(x) for x in images}:
                images = [u, *images] if u == row.get("plpImage") else [*images, u]
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

        enriched = {
            **row,
            "officialNameEn": official_name,
            "title": official_name,
            "gbpPrice": float(gbp) if gbp is not None else None,
            "description": pdp.get("description") or "",
            "details": pdp.get("details") or [],
            "materialsCare": pdp.get("materialsCare") or [],
            "images": out_imgs[:MAX_IMAGES],
            "scrapedAt": datetime.now(timezone.utc).isoformat(),
            "stage": args.stage,
        }
        if pdp.get("sizes"):
            enriched["sizes"] = pdp["sizes"]
            enriched["inStock"] = any(sz.get("inStock") for sz in pdp["sizes"])
        with cache_lock:
            cache[sku] = {
                "pdp": {
                    "description": enriched["description"],
                    "details": enriched["details"],
                    "materialsCare": enriched["materialsCare"],
                    "images": enriched["images"],
                    "gbpPrice": enriched["gbpPrice"],
                    "title": enriched["title"],
                },
                "updatedAt": enriched["scrapedAt"],
            }
        return enriched

    products: list[dict] = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(enrich, seed): seed["id"] for seed in batch}
        done = 0
        for fut in as_completed(futs):
            products.append(fut.result())
            done += 1
            if done % 15 == 0 or done == len(batch):
                print(f"enriched {done}/{len(batch)}", flush=True)
                with cache_lock:
                    PDP_CACHE.write_text(json.dumps(cache, ensure_ascii=False))

    products.sort(key=lambda p: p["id"])

    def dl_one(prod: dict) -> tuple[str, list[str]]:
        local = session()
        code = prod["id"]
        folder = re.sub(r"[^A-Za-z0-9_-]+", "_", code)
        local_paths: list[str] = []
        for i, url in enumerate(prod.get("images") or [], start=1):
            dest = IMG_ROOT / folder / f"{i}.jpg"
            if download_image(local, url, dest):
                local_paths.append(f"/products/pr-pdp/{folder}/{i}.jpg")
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
            if done % 20 == 0 or done == len(products):
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
            local_hover = locs[1]
        if local_hover:
            p["localHover"] = local_hover
        existing[p["id"]] = p

    merged = sorted(existing.values(), key=lambda x: x["id"])
    plp_meta = {
        "pr-men-rtw": {
            "label": "Men's ready-to-wear",
            "categoryCode": HUB_CID,
            "hubCount": len(seeds),
            "url": HUB_URL,
        }
    }
    for lid, label, cid, slug in LEAVES:
        n = sum(1 for p in merged if lid in (p.get("collections") or []))
        plp_meta[lid] = {
            "label": label,
            "categoryCode": cid,
            "count": n,
            "url": f"{BASE}/gb/en/mens/ready-to-wear/{slug}/c/{cid}",
        }

    payload = {
        "scrapedAt": datetime.now(timezone.utc).isoformat(),
        "source": HUB_URL,
        "stage": args.stage,
        "stages": args.stages,
        "stageRange": [start, end],
        "collections": plp_meta,
        "count": len(merged),
        "products": merged,
    }
    assert_no_mixed_rtw_sizes(merged, context="men's RTW scrape")
    OUT_RAW.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    PDP_CACHE.write_text(json.dumps(cache, ensure_ascii=False))
    progress = {
        "updatedAt": payload["scrapedAt"],
        "hubTotal": len(seeds),
        "stages": args.stages,
        "completedStages": sorted(
            {
                *(
                    json.loads(PROGRESS.read_text()).get("completedStages") or []
                    if PROGRESS.exists()
                    else []
                ),
                args.stage,
            }
        ),
        "rawCount": len(merged),
        "stageCounts": {
            **(
                json.loads(PROGRESS.read_text()).get("stageCounts") or {}
                if PROGRESS.exists()
                else {}
            ),
            str(args.stage): len(batch),
        },
    }
    PROGRESS.write_text(json.dumps(progress, ensure_ascii=False, indent=2))
    with_img = sum(1 for p in products if p.get("localImages"))
    print(
        f"STAGE {args.stage}/{args.stages} done — "
        f"batch {len(products)} (images {with_img}), raw total {len(merged)}",
        flush=True,
    )
    for lid, label, _cid, _slug in LEAVES:
        n = sum(1 for p in merged if lid in (p.get("collections") or []))
        if n:
            print(f"  {lid}: {n}", flush=True)


if __name__ == "__main__":
    main()
