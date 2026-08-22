#!/usr/bin/env python3
"""Scrape Prada GB women's ready-to-wear (~682) in stages.

Hub: https://www.prada.com/gb/en/womens/ready-to-wear/c/10048EU
PLP set = Algolia CategoriesEnriched ``10048EU|false|false``.

  python3 scripts/scrape-pr-womens-rtw.py --stage 1 --stages 5
  python3 scripts/scrape-pr-womens-rtw.py --stage 2 --stages 5
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

OUT_RAW = ROOT / "src/data/pr/pr-womens-rtw-catalog-raw.json"
PDP_CACHE = ROOT / "src/data/pr/pr-womens-rtw-pdp-cache.json"
SEED = ROOT / "src/data/pr/pr-womens-rtw-hub-seed.json"
IMG_ROOT = ROOT / "public/products/pr-pdp"
PROGRESS = ROOT / "src/data/pr/pr-womens-rtw-stage-progress.json"

BASE = "https://www.prada.com"
HUB_URL = f"{BASE}/gb/en/womens/ready-to-wear/c/10048EU"
HUB_CID = "10048EU"
HUB_ENRICHED = f"{HUB_CID}|false|false"

ALGOLIA_APP = "OCPT799JD8"
ALGOLIA_KEY = "ff0caf66bf2f4d3b10b59c95711ddaf8"
ALGOLIA_INDEX = "PLP_COLOR_PRADA_Online_GB"

# Official leaf PLPs under women's ready-to-wear
LEAVES: list[tuple[str, str, str]] = [
    ("pr-women-knitwear", "Knitwear", "10054EU"),
    ("pr-women-shirts-tops", "Shirts and tops", "10058EU"),
    ("pr-women-tshirts-sweatshirts", "T-shirts and sweatshirts", "10061EU"),
    ("pr-women-dresses", "Dresses", "10050EU"),
    ("pr-women-skirts", "Skirts", "10059EU"),
    ("pr-women-trousers-shorts", "Trousers and shorts", "10060EU"),
    ("pr-women-denim", "Denim", "10049EU"),
    ("pr-women-jackets-coats", "Jackets and coats", "10052EU"),
    ("pr-women-outerwear", "Outerwear", "10056EU"),
    ("pr-women-leather", "Leather clothing", "11083EU"),
    ("pr-women-swimwear", "Swimwear", "10610EU"),
    ("pr-women-pajamas-underwear", "Pajamas and underwear", "10057EU"),
]
LEAF_BY_CID = {cid: lid for lid, _label, cid in LEAVES}
BC_TO_LEAF = {
    "Knitwear": "pr-women-knitwear",
    "Shirts and tops": "pr-women-shirts-tops",
    "T-shirts and sweatshirts": "pr-women-tshirts-sweatshirts",
    "Dresses": "pr-women-dresses",
    "Skirts": "pr-women-skirts",
    "Trousers and shorts": "pr-women-trousers-shorts",
    "Denim": "pr-women-denim",
    "Jackets and coats": "pr-women-jackets-coats",
    "Outerwear": "pr-women-outerwear",
    "Leather clothing": "pr-women-leather",
    "Swimwear": "pr-women-swimwear",
    "Pajamas and underwear": "pr-women-pajamas-underwear",
}

PARENT_COLS = ["prada", "prada-luxury", "pr-women", "pr-women-rtw"]
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
    if not any(c.startswith("pr-women-") and c != "pr-women-rtw" for c in cols):
        bc = ((hit.get("Breadcrumbs") or {}).get("level_3") or {}).get("en_GB") or ""
        if BC_TO_LEAF.get(bc):
            cols.add(BC_TO_LEAF[bc])
    return sorted(cols)


def primary_leaf(cols: list[str], hit: dict) -> str:
    bc = ((hit.get("Breadcrumbs") or {}).get("level_3") or {}).get("en_GB") or ""
    mapped = BC_TO_LEAF.get(bc)
    if mapped and mapped in cols:
        return mapped
    for lid, _label, _cid in LEAVES:
        if lid in cols:
            return lid
    return "pr-women-rtw"


def sizes_from_hit(hit: dict) -> list[dict]:
    out = []
    for sz in hit.get("availableSizes") or []:
        label = str(sz.get("label") or "").strip()
        if not label:
            continue
        out.append(
            {
                "size": label,
                "code": str(sz.get("code") or ""),
                "inStock": True,
            }
        )
    # stable order XS→XL then numeric
    order = {"XXS": 0, "XS": 1, "S": 2, "M": 3, "L": 4, "XL": 5, "XXL": 6}
    out.sort(key=lambda x: (order.get(x["size"].upper(), 50), x["size"]))
    return out


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
        for i, suf in enumerate(order):
            if fn.endswith(suf):
                return (i, fn)
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

    return {
        "description": desc,
        "details": details,
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


def download_image(s: cffi_requests.Session, url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 2000:
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(3):
        try:
            r = s.get(
                url,
                headers={"Accept": "image/jpeg,image/*,*/*", "Referer": f"{BASE}/"},
                impersonate="chrome124",
                timeout=90,
            )
            if r.status_code != 200 or len(r.content) < 1500:
                raise RuntimeError(f"bad {r.status_code}")
            dest.write_bytes(r.content)
            return True
        except Exception:
            time.sleep(0.8 * (attempt + 1))
    return False


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
        "sizes": sizes_from_hit(hit),
        "inStock": (hit.get("Availability") or "") != "Red",
        "availability": hit.get("Availability") or "",
        "material": material,
        "kind": "womens-rtw",
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", type=int, default=1)
    ap.add_argument("--stages", type=int, default=5)
    ap.add_argument("--refresh-seed", action="store_true")
    args = ap.parse_args()

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

    # existing raw products to merge
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
        "pr-women-rtw": {
            "label": "Women's ready-to-wear",
            "categoryCode": HUB_CID,
            "hubCount": len(seeds),
            "url": HUB_URL,
        }
    }
    for lid, label, cid in LEAVES:
        n = sum(1 for p in merged if lid in (p.get("collections") or []))
        slug = {
            "pr-women-knitwear": "knitwear",
            "pr-women-shirts-tops": "shirts-and-tops",
            "pr-women-tshirts-sweatshirts": "t-shirts-and-sweatshirts",
            "pr-women-dresses": "dresses",
            "pr-women-skirts": "skirts",
            "pr-women-trousers-shorts": "trousers-and-shorts",
            "pr-women-denim": "denim",
            "pr-women-jackets-coats": "jackets-and-coats",
            "pr-women-outerwear": "outerwear",
            "pr-women-leather": "leather-clothing",
            "pr-women-swimwear": "swimwear",
            "pr-women-pajamas-underwear": "pajamas-and-underwear",
        }[lid]
        plp_meta[lid] = {
            "label": label,
            "categoryCode": cid,
            "count": n,
            "url": f"{BASE}/gb/en/womens/ready-to-wear/{slug}/c/{cid}",
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
    for lid, label, _ in LEAVES:
        n = sum(1 for p in merged if lid in (p.get("collections") or []))
        if n:
            print(f"  {lid}: {n}", flush=True)


if __name__ == "__main__":
    main()
