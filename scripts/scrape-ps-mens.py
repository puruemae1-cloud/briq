#!/usr/bin/env python3
"""Scrape Paul Smith UK mens clothing / shoes / accessories / tailoring."""
from __future__ import annotations

import json
import re
import time
import uuid
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "src/data/ps"
RAW_PATH = OUT_DIR / "ps-catalog-raw.json"
IMG_ROOT = ROOT / "public/products/ps-pdp"

CLUSTER = "w78398634"
ELEVATE = f"https://{CLUSTER}.elevate-api.cloud/api/storefront/v3"
BASE = "https://www.paulsmith.com"

# Voyado landing-page category ids (UK storefront)
SECTIONS = [
    {"key": "clothing", "pageReference": "52", "path": "mens/clothing", "channel": "clothing"},
    {"key": "shoes", "pageReference": "285", "path": "mens/shoes", "channel": "shoes"},
    {"key": "accessories", "pageReference": "32", "path": "mens/accessories", "channel": "accessories"},
    {"key": "tailoring", "pageReference": "339", "path": "mens/tailoring", "channel": "tailoring"},
]

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/html,*/*",
    "Origin": BASE,
}


def fetch_bytes(url: str, data: bytes | None = None, retries: int = 4) -> bytes:
    headers = dict(UA)
    if data is not None:
        headers["Content-Type"] = "application/json"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read()
        except Exception as e:
            if attempt + 1 >= retries:
                raise
            time.sleep(1.2 * (attempt + 1))
            if isinstance(e, urllib.error.HTTPError) and e.code in (429, 503):
                time.sleep(2.5 * (attempt + 1))
    raise RuntimeError(f"fetch failed {url}")


def elevate_landing(page_ref: str, skip: int, limit: int = 60) -> dict:
    ck = str(uuid.uuid4())
    sk = str(uuid.uuid4())
    params = {
        "customerKey": ck,
        "sessionKey": sk,
        "market": "4",
        "locale": "en-GB",
        "touchpoint": "DESKTOP",
        "priceId": "23_GBP",
        "pageReference": str(page_ref),
        "limit": str(limit),
        "skip": str(skip),
        "templateId": "defaultTemplate",
    }
    url = f"{ELEVATE}/queries/landing-page?{urllib.parse.urlencode(params)}"
    body = json.dumps({"primaryList": {"include": True}}).encode()
    return json.loads(fetch_bytes(url, body).decode("utf-8", "ignore"))


def resolve_nuxt(vals, idx, stack=None):
    if stack is None:
        stack = set()
    if not isinstance(idx, int):
        return idx
    if idx in stack or idx < 0 or idx >= len(vals):
        return None
    stack.add(idx)
    v = vals[idx]
    if isinstance(v, list) and v and isinstance(v[0], str) and v[0] in (
        "Reactive",
        "ShallowReactive",
        "Ref",
        "ShallowRef",
        "EmptyRef",
    ):
        if v[0] == "EmptyRef":
            stack.discard(idx)
            return v[1] if len(v) > 1 else None
        out = resolve_nuxt(vals, v[1], stack)
        stack.discard(idx)
        return out
    if isinstance(v, dict):
        out = {}
        for k, ref in v.items():
            if isinstance(ref, int):
                out[k] = resolve_nuxt(vals, ref, stack)
            elif isinstance(ref, list):
                out[k] = [resolve_nuxt(vals, x, stack) if isinstance(x, int) else x for x in ref]
            else:
                out[k] = ref
        stack.discard(idx)
        return out
    if isinstance(v, list):
        out = [resolve_nuxt(vals, x, stack) if isinstance(x, int) else x for x in v]
        stack.discard(idx)
        return out
    stack.discard(idx)
    return v


def plp_products_from_response(data: dict) -> list[dict]:
    pl = data.get("primaryList") or {}
    out = []
    for group in pl.get("productGroups") or []:
        for p in group.get("products") or []:
            out.append(p)
    return out


def scrape_section(section: dict) -> list[dict]:
    page_ref = section["pageReference"]
    skip = 0
    # Official storefront uses limit=21 product groups per page.
    limit = 21
    by_key: dict[str, dict] = {}
    total = None
    stagnant = 0
    while True:
        data = elevate_landing(page_ref, skip=skip, limit=limit)
        pl = data.get("primaryList") or {}
        if total is None:
            total = int(pl.get("totalHits") or 0)
            print(f"[{section['key']}] totalHits={total}", flush=True)
        batch = plp_products_from_response(data)
        if not batch:
            break
        before = len(by_key)
        for p in batch:
            k = str(p.get("key") or "")
            if k:
                by_key[k] = p
        added = len(by_key) - before
        skip += limit
        print(
            f"[{section['key']}] unique={len(by_key)}/{total} (+{added}) skip={skip}",
            flush=True,
        )
        if added == 0:
            stagnant += 1
        else:
            stagnant = 0
        if len(by_key) >= total or stagnant >= 2 or skip > total + limit * 3:
            break
        time.sleep(0.12)
    return list(by_key.values())


def best_image_url(sources: list) -> str | None:
    if not sources:
        return None
    best = None
    best_w = -1
    for s in sources:
        if not isinstance(s, dict):
            continue
        w = int(s.get("width") or 0)
        url = s.get("url")
        if url and w >= best_w:
            best = url
            best_w = w
    return best


def plp_image_urls(p: dict) -> list[str]:
    info = p.get("imageInfo") or {}
    urls = []
    for img in info.get("images") or []:
        u = best_image_url(img.get("sources") or [])
        if u:
            # upgrade to wider still when possible
            u = re.sub(r"/w_\d+,", "/w_1200,", u)
            urls.append(u)
    thumb = info.get("thumbnail")
    if isinstance(thumb, str) and thumb and thumb not in urls:
        urls.insert(0, thumb)
    return urls[:8]


def custom_label(custom: dict | None, key: str) -> str | None:
    if not custom:
        return None
    arr = custom.get(key) or []
    if isinstance(arr, list) and arr:
        first = arr[0]
        if isinstance(first, dict):
            return first.get("label") or first.get("id")
    return None


def normalize_asset_url(url: str) -> str:
    u = (url or "").strip()
    if not u:
        return u
    # Already transformed PLP thumbs → bump width
    if "/w_" in u:
        return re.sub(r"/w_\d+,", "/w_1200,", u)
    # Raw asset path: .../paul-smith-products/v123/... → insert transform
    if "paul-smith-products/" in u and "/w_" not in u:
        return u.replace(
            "paul-smith-products/",
            "paul-smith-products/w_1200,c_scale/q_auto,f_jpg/",
            1,
        )
    return u


def download_images(handle: str, urls: list[str]) -> list[str]:
    dest = IMG_ROOT / handle
    dest.mkdir(parents=True, exist_ok=True)
    local = []
    for i, url in enumerate(urls[:6], start=1):
        path = dest / f"{i}.jpg"
        if path.exists() and path.stat().st_size > 800:
            local.append(f"/products/ps-pdp/{handle}/{i}.jpg")
            continue
        try:
            fetch_url = normalize_asset_url(url)
            data = fetch_bytes(fetch_url)
            if len(data) < 800:
                continue
            path.write_bytes(data)
            local.append(f"/products/ps-pdp/{handle}/{i}.jpg")
            time.sleep(0.03)
        except Exception as e:
            print("img fail", handle, i, e)
    return local


def scrape_pdp(uri: str) -> dict | None:
    uri = (uri or "").strip().lstrip("/")
    if not uri:
        return None
    url = f"{BASE}/uk/{uri}"
    try:
        html = fetch_bytes(url).decode("utf-8", "ignore")
    except Exception as e:
        print("pdp fail", uri, e)
        return None
    m = re.search(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return None
    try:
        vals = json.loads(m.group(1))
        root = resolve_nuxt(vals, 1)
        ps = (root.get("pinia") or {}).get("ProductStore") or {}
        entity = ps.get("entity") or {}
        if not entity:
            return None
        return {
            "uri": uri,
            "entity": entity,
            "content": ps.get("content") or {},
            "measurementChart": ps.get("measurementChart") or entity.get("measurementChart") or {},
            "configurableOptions": ps.get("configurableOptions") or [],
            "selectedPrice": ps.get("selectedPrice") or {},
            "sku": ps.get("sku"),
            "isOutOfStock": bool(ps.get("isOutOfStock")),
            "sourceUrl": url,
        }
    except Exception as e:
        print("pdp parse fail", uri, e)
        return None


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    existing: dict[str, dict] = {}
    if RAW_PATH.exists():
        try:
            existing = json.loads(RAW_PATH.read_text())
            print(f"loaded existing raw={len(existing)}")
        except Exception:
            existing = {}

    # 1) PLP crawl
    plp_by_key: dict[str, dict] = {}
    membership: dict[str, set[str]] = {}
    for section in SECTIONS:
        items = scrape_section(section)
        for p in items:
            key = str(p.get("key") or "")
            if not key:
                continue
            membership.setdefault(key, set()).add(section["channel"])
            prev = plp_by_key.get(key)
            if not prev:
                plp_by_key[key] = p
            # keep richer variant info if present
            elif len(p.get("variants") or []) > len(prev.get("variants") or []):
                plp_by_key[key] = p
        time.sleep(0.2)

    print(f"unique PLP products={len(plp_by_key)}")

    # 2) PDP enrich
    todos = []
    for key, p in plp_by_key.items():
        link = (p.get("link") or "").strip().lstrip("/")
        if key in existing and existing[key].get("entity") and existing[key].get("images"):
            # refresh membership/stock from PLP cheaply
            existing[key]["channels"] = sorted(membership.get(key, set()))
            existing[key]["plp"] = {
                "key": key,
                "title": p.get("title"),
                "link": link,
                "sellingPrice": p.get("sellingPrice"),
                "listPrice": p.get("listPrice"),
                "variants": p.get("variants") or [],
                "custom": p.get("custom") or {},
                "style": custom_label(p.get("custom"), "style"),
                "product_type": custom_label(p.get("custom"), "product_type"),
            }
            continue
        todos.append((key, p, link))

    print(f"PDP todo={len(todos)} cached={len(plp_by_key) - len(todos)}")

    def work(item):
        key, p, link = item
        pdp = scrape_pdp(link)
        handle = link.replace("/", "-") or key
        urls = []
        if pdp:
            for img in (pdp.get("content") or {}).get("images") or []:
                if isinstance(img, dict) and img.get("url"):
                    urls.append(img["url"])
        if not urls:
            urls = plp_image_urls(p)
        local = download_images(handle, urls)
        row = {
            "key": key,
            "handle": handle,
            "channels": sorted(membership.get(key, set())),
            "plp": {
                "key": key,
                "title": p.get("title"),
                "link": link,
                "sellingPrice": p.get("sellingPrice"),
                "listPrice": p.get("listPrice"),
                "variants": p.get("variants") or [],
                "custom": p.get("custom") or {},
                "style": custom_label(p.get("custom"), "style"),
                "product_type": custom_label(p.get("custom"), "product_type"),
            },
            "entity": (pdp or {}).get("entity") or {},
            "content": (pdp or {}).get("content") or {},
            "measurementChart": (pdp or {}).get("measurementChart") or {},
            "configurableOptions": (pdp or {}).get("configurableOptions") or [],
            "selectedPrice": (pdp or {}).get("selectedPrice") or {},
            "images": local,
            "sourceUrl": f"{BASE}/uk/{link}",
        }
        return key, row

    done = 0
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = [ex.submit(work, t) for t in todos]
        for fut in as_completed(futs):
            try:
                key, row = fut.result()
                existing[key] = row
                done += 1
                if done <= 5 or done % 25 == 0:
                    print(f"pdp {done}/{len(todos)} {row.get('handle')}", flush=True)
                if done % 20 == 0:
                    RAW_PATH.write_text(json.dumps(existing, ensure_ascii=False) + "\n")
            except Exception as e:
                print("worker fail", e)

    # ensure membership for all
    for key, p in plp_by_key.items():
        if key not in existing:
            link = (p.get("link") or "").strip().lstrip("/")
            handle = link.replace("/", "-") or key
            existing[key] = {
                "key": key,
                "handle": handle,
                "channels": sorted(membership.get(key, set())),
                "plp": {
                    "key": key,
                    "title": p.get("title"),
                    "link": link,
                    "sellingPrice": p.get("sellingPrice"),
                    "listPrice": p.get("listPrice"),
                    "variants": p.get("variants") or [],
                    "custom": p.get("custom") or {},
                    "style": custom_label(p.get("custom"), "style"),
                    "product_type": custom_label(p.get("custom"), "product_type"),
                },
                "entity": {},
                "content": {},
                "measurementChart": {},
                "configurableOptions": [],
                "selectedPrice": {},
                "images": download_images(handle, plp_image_urls(p)),
                "sourceUrl": f"{BASE}/uk/{link}",
            }
        else:
            existing[key]["channels"] = sorted(membership.get(key, set()))

    RAW_PATH.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {len(existing)} products → {RAW_PATH}")


if __name__ == "__main__":
    main()
