#!/usr/bin/env python3
"""Scrape Burberry Women PLPs + PDPs into src/data/bb/bb-catalog-raw.json."""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bb_women_config import BASE, WOMEN_COLLECTIONS, UA  # noqa: E402
from studio_whiten import save_product_image  # noqa: E402

RAW_PATH = ROOT / "src/data/bb/bb-catalog-raw.json"
PDP_CACHE = ROOT / "src/data/bb/bb-pdp-cache.json"
IMG_ROOT = ROOT / "public/products/bb-pdp"

PAGE_LIMIT = 100
MAX_WORKERS = 8
IMG_PER_COLOUR = 6

# Weekly sync sets BB_REFRESH_STOCK=1 so PDP sizes/prices/stock re-fetch
# while keeping already-downloaded local images.
REFRESH_STOCK = os.environ.get("BB_REFRESH_STOCK", "").strip().lower() in {
    "1",
    "true",
    "yes",
}

def fetch(url: str, retries: int = 4) -> str:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": UA,
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "en-GB,en;q=0.9",
                },
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.2 * (attempt + 1))
    raise RuntimeError(f"fetch failed {url}: {last}")


def parse_preloaded(html: str) -> dict:
    marker = "window.__PRELOADED_STATE__ ="
    start = html.find(marker)
    if start < 0:
        raise ValueError("no PRELOADED_STATE")
    start += len(marker)
    end = html.find("</script>", start)
    blob = html[start:end].strip().rstrip(";")
    blob = re.sub(r"\bundefined\b", "null", blob)
    blob = re.sub(r"\bNaN\b", "null", blob)
    return json.loads(blob)


def plp_items(data: dict) -> tuple[list[dict], int]:
    for page in (data.get("pages") or {}).get("entities", {}).values():
        products = (page.get("components") or {}).get("products")
        if not products:
            continue
        block = products[0]
        total = int(block.get("productCount") or 0)
        buckets = block.get("products") or []
        if not buckets:
            return [], total
        items = buckets[0].get("items") or []
        return items, total
    props_total = 0
    for page in (data.get("pages") or {}).get("entities", {}).values():
        props = page.get("properties") or {}
        if "productCount" in props:
            props_total = int(props["productCount"] or 0)
    return [], props_total


def scrape_collection(coll_id: str, path: str) -> list[dict]:
    out: list[dict] = []
    offset = 0
    total = None
    while True:
        sep = "&" if "?" in path else "?"
        url = f"{BASE}{path}{sep}limit={PAGE_LIMIT}&offset={offset}"
        print(f"  PLP {coll_id} offset={offset}", flush=True)
        try:
            html = fetch(url)
            data = parse_preloaded(html)
        except Exception as e:  # noqa: BLE001
            print(f"  ! skip {coll_id} @ {offset}: {e}", flush=True)
            break
        items, page_total = plp_items(data)
        if total is None:
            total = page_total
            print(f"  → {coll_id} total={total}", flush=True)
        if not items:
            break
        for it in items:
            pid = str(it.get("id") or "")
            if not pid:
                continue
            price = ((it.get("price") or {}).get("current") or {}).get("value")
            old = ((it.get("price") or {}).get("old") or {}).get("value")
            media = (
                ((it.get("media") or {}).get("defaults") or {}).get("image") or {}
            )
            image = media.get("imageDefault") or media.get("key") or ""
            out.append(
                {
                    "id": pid,
                    "title": (it.get("content") or {}).get("title")
                    or (it.get("content") or {}).get("defaultTitle")
                    or "",
                    "url": it.get("url") or "",
                    "color": it.get("color") or "",
                    "gbpPrice": float(price) if price is not None else None,
                    "gbpListPrice": float(old) if old is not None else None,
                    "image": image,
                    "label": (it.get("content") or {}).get("label"),
                    "numberOfColours": it.get("numberOfColours"),
                    "soldOut": bool((it.get("types") or {}).get("isSoldOut")),
                }
            )
        offset += len(items)
        if total is not None and offset >= total:
            break
        if len(items) < PAGE_LIMIT:
            break
        time.sleep(0.25)
    return out


def extract_pdp(html: str, product_id: str) -> dict:
    data = parse_preloaded(html)
    entities = (data.get("pages") or {}).get("entities", {})
    page = None
    page_key = None
    for key, val in entities.items():
        if product_id in key:
            page = val
            page_key = key
            break
    if page is None and entities:
        page_key, page = next(iter(entities.items()))
    if not page:
        raise ValueError("no page entity")
    props = page.get("properties") or {}
    product = props.get("product") or {}
    comps = page.get("components") or {}
    swatches = (comps.get("swatches") or {}).get("items") or []
    gallery = comps.get("gallery") or {}
    images: list[str] = []
    for item in gallery.get("items") or gallery.get("fullScreenItems") or []:
        img = (item.get("image") or {}) if isinstance(item, dict) else {}
        src = img.get("imageDefault") or img.get("key")
        if src and src not in images:
            images.append(src)
    accordion = []
    for opt in (comps.get("fitDetailsPanel") or {}).get("accordionOptions") or []:
        texts = []
        for row in opt.get("content") or []:
            t = row.get("text") if isinstance(row, dict) else None
            if t:
                texts.append(t)
        accordion.append({"name": opt.get("name"), "label": opt.get("label"), "texts": texts})
    return {
        "id": str(product.get("id") or product_id),
        "name": (product.get("nameEn") or product.get("name") or "").replace("\u200b", "").strip(),
        "description": product.get("description") or "",
        "color": product.get("color") or "",
        "gbpPrice": float(((product.get("price") or {}).get("current") or {}).get("value") or 0)
        or None,
        "gbpListPrice": (
            float(((product.get("price") or {}).get("old") or {}).get("value"))
            if ((product.get("price") or {}).get("old") or {}).get("value") is not None
            else None
        ),
        "sizes": product.get("sizes") or [],
        "measurements": product.get("measurements"),
        "materialComposition": product.get("materialComposition"),
        "careInstructions": product.get("careInstructions"),
        "features": product.get("features"),
        "sizeMappingType": product.get("sizeMappingType"),
        "relatedGenders": product.get("relatedGenders") or [],
        "swatches": [
            {
                "id": str(s.get("id")),
                "url": s.get("url"),
                "label": s.get("label"),
                "name": (s.get("name") or "").replace("\u200b", "").strip(),
                "image": s.get("image"),
            }
            for s in swatches
            if s.get("id")
        ],
        "images": images,
        "accordion": accordion,
        "url": page_key or f"-p{product_id}",
    }


def download_images(product_id: str, urls: list[str]) -> list[str]:
    dest = IMG_ROOT / product_id
    dest.mkdir(parents=True, exist_ok=True)
    local: list[str] = []
    for i, url in enumerate(urls[:IMG_PER_COLOUR], start=1):
        if not url:
            continue
        # Scene7: request a stable jpeg
        if "burberry.com/is/image" in url and "?" not in url:
            fetch_url = f"{url}?$BBY_V2_SL_3x4$&wid=1200&hei=1600&fmt=jpg"
        else:
            fetch_url = url
        out = dest / f"{i}.jpg"
        rel = f"/products/bb-pdp/{product_id}/{i}.jpg"
        if out.exists() and out.stat().st_size > 1000:
            local.append(rel)
            continue
        try:
            req = urllib.request.Request(fetch_url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as resp:
                save_product_image(out, resp.read())
            local.append(rel)
        except Exception as e:  # noqa: BLE001
            print(f"  img fail {product_id}#{i}: {e}", flush=True)
    return local


def enrich_one(
    product_id: str,
    path: str,
    cache: dict,
    *,
    refresh_stock: bool | None = None,
) -> dict:
    """Fetch PDP into cache. Reuses local images when possible.

    When refresh_stock (or BB_REFRESH_STOCK) is on, always re-hit the PDP so
    size-level isInStock / prices update for weekly sync.
    """
    do_refresh = REFRESH_STOCK if refresh_stock is None else refresh_stock
    cached = cache.get(product_id)
    if (
        not do_refresh
        and cached
        and cached.get("sizes") is not None
        and cached.get("localImages")
    ):
        return cached

    url = path if path.startswith("http") else f"{BASE}{path}"
    html = fetch(url)
    pdp = extract_pdp(html, product_id)
    # Prefer canonical url from page key
    if pdp.get("url") and not pdp["url"].startswith("http"):
        pdp["sourceUrl"] = f"{BASE}{pdp['url']}"
    else:
        pdp["sourceUrl"] = url
    imgs = pdp.get("images") or []
    if cached and cached.get("localImages") and do_refresh:
        # Keep disk images; only refresh stock/price/copy from PDP.
        pdp["localImages"] = cached["localImages"]
    else:
        pdp["localImages"] = download_images(product_id, imgs)
    cache[product_id] = pdp
    return pdp


def main() -> None:
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    IMG_ROOT.mkdir(parents=True, exist_ok=True)

    existing = {}
    if RAW_PATH.exists():
        existing = json.loads(RAW_PATH.read_text())
    old_products = {
        str(p["id"]): p for p in (existing.get("products") or []) if p.get("id")
    }

    cache: dict = {}
    if PDP_CACHE.exists():
        cache = json.loads(PDP_CACHE.read_text())

    membership: dict[str, set[str]] = {}
    # Keep non-women hubs so a women-only run does not wipe later scrapes
    _keep_prefixes = (
        "bb-men-",
        "bb-kids-",
        "bb-gifts-",
        "bb-scarves-",
        "bb-beauty-",
        "bb-bags-collections",
    )
    for pid, prod in old_products.items():
        cols = [
            c
            for c in (prod.get("collections") or [])
            if any(str(c).startswith(p) for p in _keep_prefixes)
        ]
        if cols:
            membership[pid] = set(cols)

    plp_meta: dict[str, dict] = {
        k: v
        for k, v in (existing.get("collections") or {}).items()
        if any(str(k).startswith(p) for p in _keep_prefixes)
    }

    for coll_id, label, path, top, _parent in WOMEN_COLLECTIONS:
        items = scrape_collection(coll_id, path)
        plp_meta[coll_id] = {
            "label": label,
            "path": path,
            "category": top,
            "count": len(items),
        }
        for it in items:
            pid = it["id"]
            membership.setdefault(pid, set()).add(coll_id)
            # keep richest plp card
            prev = plp_meta.setdefault("_cards", {}).setdefault(pid, it)
            if not prev.get("gbpPrice") and it.get("gbpPrice"):
                plp_meta["_cards"][pid] = it
            elif it.get("title") and len(it["title"]) > len(prev.get("title") or ""):
                plp_meta["_cards"][pid] = {**prev, **it}

    cards: dict[str, dict] = plp_meta.pop("_cards", {})
    # Only enrich colourways linked to women collections (men preserved separately)
    product_ids = sorted(
        pid
        for pid, cols in membership.items()
        if any(str(c).startswith("bb-women-") for c in cols)
    )
    print(f"Unique colourways from PLPs: {len(product_ids)}", flush=True)

    # Discover sibling colours from PDPs and ensure they are enriched too
    def job(pid: str) -> tuple[str, dict | None, str | None]:
        card = cards.get(pid) or {}
        path = card.get("url") or f"-p{pid}"
        if not path.startswith("/"):
            path = "/" + path
        try:
            pdp = enrich_one(pid, path, cache)
            return pid, pdp, None
        except Exception as e:  # noqa: BLE001
            return pid, None, str(e)

    # First pass
    errors = []
    done = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(job, pid): pid for pid in product_ids}
        for fut in as_completed(futs):
            pid, pdp, err = fut.result()
            done += 1
            if done % 25 == 0 or done == len(product_ids):
                PDP_CACHE.write_text(json.dumps(cache, ensure_ascii=False))
                print(f"  PDP {done}/{len(product_ids)}", flush=True)
            if err:
                errors.append({"id": pid, "error": err})

    # Second pass: sibling swatches not on any scraped PLP
    extra_ids: list[str] = []
    for pid in list(product_ids):
        pdp = cache.get(pid) or {}
        for sw in pdp.get("swatches") or []:
            sid = str(sw.get("id"))
            if sid and sid not in membership:
                membership[sid] = set(membership.get(pid) or [])
                cards.setdefault(
                    sid,
                    {
                        "id": sid,
                        "title": sw.get("name") or "",
                        "url": sw.get("url") or f"-p{sid}",
                        "color": sw.get("label") or "",
                        "image": sw.get("image") or "",
                    },
                )
                extra_ids.append(sid)

    extra_ids = sorted(set(extra_ids))
    if extra_ids:
        print(f"Sibling colourways to enrich: {len(extra_ids)}", flush=True)
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futs = {ex.submit(job, pid): pid for pid in extra_ids}
            for i, fut in enumerate(as_completed(futs), start=1):
                pid, pdp, err = fut.result()
                if i % 25 == 0 or i == len(extra_ids):
                    PDP_CACHE.write_text(json.dumps(cache, ensure_ascii=False))
                    print(f"  sibling PDP {i}/{len(extra_ids)}", flush=True)
                if err:
                    errors.append({"id": pid, "error": err})

    products = []
    for pid, cols in sorted(membership.items()):
        card = cards.get(pid) or {}
        pdp = cache.get(pid) or {}
        prev = old_products.get(pid) or {}
        local_imgs = pdp.get("localImages") or prev.get("images") or []
        products.append(
            {
                "id": pid,
                "title": pdp.get("name") or card.get("title") or prev.get("title") or "",
                "url": pdp.get("sourceUrl")
                or prev.get("url")
                or (f"{BASE}{card['url']}" if card.get("url") else ""),
                "color": pdp.get("color") or card.get("color") or prev.get("color") or "",
                "gbpPrice": pdp.get("gbpPrice")
                or card.get("gbpPrice")
                or prev.get("gbpPrice"),
                "gbpListPrice": pdp.get("gbpListPrice")
                or card.get("gbpListPrice")
                or prev.get("gbpListPrice"),
                "image": (local_imgs[0] if local_imgs else None)
                or card.get("image")
                or prev.get("image")
                or "",
                "images": local_imgs or prev.get("images") or [],
                "remoteImages": pdp.get("images") or prev.get("remoteImages") or [],
                "sizes": pdp.get("sizes") or prev.get("sizes") or [],
                "swatches": pdp.get("swatches") or prev.get("swatches") or [],
                "description": pdp.get("description") or prev.get("description") or "",
                "accordion": pdp.get("accordion") or prev.get("accordion") or [],
                "measurements": pdp.get("measurements") or prev.get("measurements"),
                "materialComposition": pdp.get("materialComposition")
                or prev.get("materialComposition"),
                "collections": sorted(cols),
                "label": card.get("label") or prev.get("label"),
            }
        )

    payload = {
        "scrapedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": BASE,
        "collectionCounts": {k: v["count"] for k, v in plp_meta.items()},
        "collections": plp_meta,
        "productCount": len(products),
        "errors": errors,
        "products": products,
    }
    RAW_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    PDP_CACHE.write_text(json.dumps(cache, ensure_ascii=False))
    print(
        f"Wrote {RAW_PATH} products={len(products)} errors={len(errors)}",
        flush=True,
    )


if __name__ == "__main__":
    main()
