#!/usr/bin/env python3
"""Scrape Chanel GB sunglasses into ch-sunglasses-catalog-raw.json + images.

Official See All Sunglasses PLP:
  https://www.chanel.com/gb/eyewear/sunglasses/c/2x1x1/

Reuses ChanelClient + image helpers from scrape-ch-rtw.py (Akamai/proxy).
SKU pattern: A{digits}X… under /gb/eyewear/p/ (not fashion handbags/jewellery).
"""
from __future__ import annotations

import importlib.util
import json
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_RAW = ROOT / "src/data/ch/ch-sunglasses-catalog-raw.json"
PDP_CACHE = ROOT / "src/data/ch/ch-sunglasses-pdp-cache.json"
IMG_ROOT = ROOT / "public/products/ch-pdp"

BASE = "https://www.chanel.com"
HUB = f"{BASE}/gb/eyewear/"
PLP = f"{BASE}/gb/eyewear/sunglasses/c/2x1x1/"
SITEMAP = f"{BASE}/gb/sitemap.xml"

LEAF_ID = "ch-women-sunglasses"
PARENT_COLS = ["chanel", "chanel-accessories", "ch-sunglasses", LEAF_ID]

PDP_PAUSE = 1.2
HARD_BLOCK_SLEEP = 12.0
MAX_PLP_PAGES = 20

_spec = importlib.util.spec_from_file_location(
    "scrape_ch_rtw", ROOT / "scripts" / "scrape-ch-rtw.py"
)
assert _spec and _spec.loader
_rtw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_rtw)

ChanelClient = _rtw.ChanelClient
extract_next_data = _rtw.extract_next_data
is_challenge = _rtw.is_challenge
normalize_img_url = _rtw.normalize_img_url
parse_gbp = _rtw.parse_gbp
availability_map = _rtw.availability_map
wait_for_pdp_access = _rtw.wait_for_pdp_access
log = _rtw.log


def order_eyewear_images(images: list[dict]) -> list[str]:
    preferred = (
        "PACKSHOT_DEFAULT",
        "PACKSHOT_ALTERNATIVE",
        "PACKSHOT_EXTRA",
        "PACKSHOT_OTHER",
        "PACKSHOT_ARTISTIQUE_VUE1",
        "PACKSHOT_ARTISTIQUE_VUE2",
        "LOOK",
        "EDITORIAL",
    )
    scored: list[tuple[int, int, str]] = []
    seen: set[str] = set()
    for i, im in enumerate(images or []):
        if not isinstance(im, dict):
            continue
        src = normalize_img_url(im.get("source") or im.get("url") or "")
        if not src or src in seen:
            continue
        seen.add(src)
        typ = (im.get("typology") or "").upper()
        try:
            rank = preferred.index(typ)
        except ValueError:
            rank = 50
        scored.append((rank, i, src))
    scored.sort()
    return [u for _, _, u in scored]


def is_eyewear_sku(sku: str) -> bool:
    s = (sku or "").upper()
    # Eyewear PDPs use A{n}X… codes (e.g. A71778X08101S011653NOCCI).
    return bool(re.fullmatch(r"A\d+X[A-Z0-9]+", s))


def fetch_page(client: ChanelClient, url: str, referer: str = HUB) -> tuple[int, str]:
    headers = {**_rtw.HTML_HEADERS, "Referer": referer}
    last_status, last_text = 0, ""
    for attempt in range(1, 4):
        try:
            with _rtw._session_lock:
                r = client.session.get(
                    url,
                    impersonate=client.impersonate,
                    timeout=90,
                    headers=headers,
                    proxies=client.proxies,
                )
                client._req_count += 1
                last_status, last_text = r.status_code, r.text
        except Exception as e:
            log(f"  GET error {url}: {e}")
            time.sleep(1.0 * attempt)
            if client._proxy:
                client.rotate_proxy()
            else:
                client.ensure_proxy()
            continue
        if last_status == 404:
            return last_status, last_text
        if "__NEXT_DATA__" in last_text and len(last_text) > 20000:
            return last_status, last_text
        if last_status == 200 and "/gb/eyewear/p/" in last_text:
            return last_status, last_text
        log(
            f"  soft-block {last_status} on {url} "
            f"(attempt {attempt}, len={len(last_text)})"
        )
        time.sleep(1.5)
        if not client._proxy:
            client.ensure_proxy()
        else:
            client.soft_refresh()
            client.warm()
    return last_status, last_text


def extract_skus_from_html(html: str) -> set[str]:
    skus = set(re.findall(r"/gb/eyewear/p/([A-Z0-9]+)/", html, flags=re.I))
    skus |= set(
        re.findall(r"\\?/gb\\?/eyewear\\?/p\\?/([A-Z0-9]+)\\?/", html, flags=re.I)
    )
    return {s for s in skus if is_eyewear_sku(s)}


def discover_plp_skus(client: ChanelClient, url: str) -> set[str]:
    found: set[str] = set()
    pages = [url]
    for n in range(2, MAX_PLP_PAGES + 1):
        pages.append(f"{url.rstrip('/')}/page-{n}/")

    for page_url in pages:
        status, html = fetch_page(client, page_url)
        if status == 404:
            break
        if status != 200 or len(html) < 5000:
            if page_url == url:
                log(f"  PLP blocked {page_url} status={status} len={len(html)}")
            break
        ids = extract_skus_from_html(html)
        before = len(found)
        found |= ids
        log(f"  PLP {page_url} → +{len(found) - before} (total {len(found)})")
        if not ids and page_url != url:
            break
        if page_url != url and len(found) == before:
            break
        time.sleep(0.5)
    return found


def discover_sitemap_eyewear_skus(client: ChanelClient) -> dict[str, str]:
    status, text = client.get_html(SITEMAP, max_attempts=2)
    if status != 200:
        try:
            r = client.session.get(
                SITEMAP,
                impersonate=client.impersonate,
                timeout=90,
                headers=_rtw.HTML_HEADERS,
            )
            status, text = r.status_code, r.text
        except Exception:
            return {}
    by_sku: dict[str, str] = {}
    for m in re.finditer(
        r"https://www\.chanel\.com/gb/eyewear/p/(A[^/\s\"<]+)/",
        text,
        flags=re.I,
    ):
        sku = m.group(1)
        if not is_eyewear_sku(sku):
            continue
        by_sku.setdefault(sku, m.group(0).rstrip("/") + "/")
    log(f"sitemap eyewear SKUs: {len(by_sku)}")
    return by_sku


def parse_eyewear_pdp(html: str, url: str) -> dict | None:
    nd = extract_next_data(html)
    if not nd:
        return None
    data = (nd.get("props") or {}).get("pageProps", {}).get("data") or {}
    prod = data.get("product")
    if not isinstance(prod, dict):
        return None

    sku = str(prod.get("sku") or prod.get("id") or "").strip()
    if not sku or not is_eyewear_sku(sku):
        return {"_skip": True, "reason": f"not-eyewear-sku:{sku}", "sku": sku, "url": url}

    gbp = parse_gbp(prod.get("price"))
    if gbp is None or gbp <= 0:
        return {
            "_skip": True,
            "sku": sku,
            "reason": f"bad price {prod.get('price')!r}",
            "url": url,
        }

    # Eyewear "variants" in NEXT_DATA are frame measurement maps, not buyable sizes.
    top_status, _stock = availability_map(data.get("availability"))
    details = prod.get("details") if isinstance(prod.get("details"), dict) else {}
    imgs = prod.get("images") if isinstance(prod.get("images"), list) else []

    return {
        "id": sku,
        "productCode": sku,
        "sku": sku,
        "title": prod.get("title") or "",
        "priceLabel": prod.get("price"),
        "gbpPrice": gbp,
        "categoryLabel": prod.get("categoryLabel"),
        "collection": prod.get("collection"),
        "collectionCode": prod.get("collectionCode"),
        "url": url,
        "hierarchy": prod.get("hierarchy") or [],
        "details": {
            "color": details.get("color"),
            "description": details.get("description"),
            "fabrics": details.get("fabrics"),
            "reference": details.get("reference"),
            "dimensions": details.get("dimensions"),
            "eyeLensColor": details.get("eyeLensColor"),
            "freeStat": details.get("freeStat"),
            "treatment": details.get("treatment"),
        },
        "images": order_eyewear_images(imgs),
        "imageMeta": [
            {
                "typology": im.get("typology"),
                "viewAngle": im.get("viewAngle"),
                "viewLabel": im.get("viewLabel"),
                "source": normalize_img_url(im.get("source")),
                "id": im.get("id"),
            }
            for im in imgs
            if isinstance(im, dict) and im.get("source")
        ],
        "sizes": [{"size": "UNI", "orliSize": "UNI", "sku": sku, "inStock": True}],
        "availabilityStatus": top_status,
        "inStock": top_status == "IN_STOCK" or True,
        "new": bool(prod.get("new")),
        "collections": list(PARENT_COLS),
        "leaf": LEAF_ID,
        "leaves": [LEAF_ID],
        "kind": "sunglasses",
    }


def download_images(client: ChanelClient, sku: str, urls: list[str]) -> list[str]:
    dest = IMG_ROOT / sku.lower()
    dest.mkdir(parents=True, exist_ok=True)
    local: list[str] = []
    for i, url in enumerate(urls[:12], start=1):
        path = dest / f"{i}.jpg"
        web = f"/products/ch-pdp/{sku.lower()}/{i}.jpg"
        if path.exists() and path.stat().st_size > 2048:
            local.append(web)
            continue
        data = client.get_bytes(url, referer=HUB)
        if not data:
            log(f"  skip img {sku} #{i}")
            continue
        path.write_bytes(data)
        local.append(web)
        time.sleep(0.05)
    return local


def enrich_images(client: ChanelClient, parsed: dict) -> dict:
    sku = parsed["sku"]
    locals_ = download_images(client, sku, parsed.get("images") or [])
    parsed["localImages"] = locals_
    if locals_:
        parsed["localImage"] = locals_[0]
        if len(locals_) > 1:
            parsed["localHover"] = locals_[1]
    return parsed


def load_cache() -> dict:
    if PDP_CACHE.exists():
        try:
            return json.loads(PDP_CACHE.read_text())
        except Exception:
            return {}
    return {}


def save_cache(cache: dict) -> None:
    PDP_CACHE.parent.mkdir(parents=True, exist_ok=True)
    PDP_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n")


def main() -> int:
    IMG_ROOT.mkdir(parents=True, exist_ok=True)
    OUT_RAW.parent.mkdir(parents=True, exist_ok=True)

    _rtw.HUB = HUB
    _rtw.PROBE_SKU_URL = (
        "https://www.chanel.com/gb/eyewear/p/A40888X09955L439559KUNI/"
        "pilot-sunglasses/"
    )

    client = ChanelClient()
    if not client._proxy:
        client.ensure_proxy()
        client.warm()

    log("discovering sunglasses PLP (See All)…")
    ids = discover_plp_skus(client, PLP)
    if not ids and not client._proxy:
        client.ensure_proxy()
        client.warm()
        ids = discover_plp_skus(client, PLP)

    sitemap = discover_sitemap_eyewear_skus(client)
    sku_urls: dict[str, str] = {}
    for sku in ids:
        sku_urls[sku] = sitemap.get(sku) or f"{BASE}/gb/eyewear/p/{sku}/"

    todo = sorted(sku_urls.items())
    log(f"unique sunglasses SKUs to scrape: {len(todo)}")

    cache = load_cache()
    products: list[dict] = []
    skipped: list[dict] = []
    failed: list[dict] = []
    leaf_counts: Counter[str] = Counter()

    if not wait_for_pdp_access(client):
        log("ERROR: PDP access never recovered — aborting")
        return 1

    consecutive_blocks = 0
    i = 0
    while i < len(todo):
        sku, url = todo[i]
        i += 1

        cached = cache.get(sku)
        if (
            isinstance(cached, dict)
            and cached.get("gbpPrice")
            and cached.get("leaf")
            and cached.get("kind") == "sunglasses"
            and not cached.get("_skip")
        ):
            cached["leaf"] = LEAF_ID
            cached["leaves"] = [LEAF_ID]
            cached["collections"] = list(PARENT_COLS)
            if not cached.get("localImages"):
                cached = enrich_images(client, cached)
            cache[sku] = cached
            save_cache(cache)
            products.append(cached)
            leaf_counts[LEAF_ID] += 1
            continue

        status, html = client.get_html(url, referer=PLP, max_attempts=3)
        if is_challenge(html, status):
            consecutive_blocks += 1
            log(
                f"[{i}/{len(todo)}] blocked {sku} "
                f"(streak={consecutive_blocks}, proxy={client._proxy})"
            )
            client.clear_proxy()
            time.sleep(HARD_BLOCK_SLEEP)
            if not client.probe_direct():
                client.ensure_proxy()
            client.warm()
            i -= 1
            if consecutive_blocks >= 12:
                if not wait_for_pdp_access(client, max_wait_s=600):
                    failed.append(
                        {"sku": sku, "url": url, "status": status, "reason": "akamai"}
                    )
                    consecutive_blocks = 0
                    i += 1
                else:
                    consecutive_blocks = 0
            continue

        consecutive_blocks = 0
        parsed = parse_eyewear_pdp(html, url)
        if not parsed:
            failed.append({"sku": sku, "url": url, "status": status, "reason": "parse"})
            log(f"[{i}/{len(todo)}] FAIL {sku} parse")
            continue
        if parsed.get("_skip"):
            skipped.append(parsed)
            cache[sku] = parsed
            save_cache(cache)
            log(f"[{i}/{len(todo)}] skip {sku}: {parsed.get('reason')}")
            time.sleep(PDP_PAUSE)
            continue

        cache[sku] = parsed
        save_cache(cache)
        parsed = enrich_images(client, parsed)
        cache[sku] = parsed
        products.append(parsed)
        leaf_counts[LEAF_ID] += 1
        log(
            f"[{i}/{len(todo)}] OK {sku} {parsed['leaf']} "
            f"£{parsed['gbpPrice']} imgs={len(parsed.get('localImages') or [])}"
        )
        save_cache(cache)
        time.sleep(PDP_PAUSE)

    save_cache(cache)

    by_id: dict[str, dict] = {}
    for p in products:
        by_id[p["sku"]] = p
    products = list(by_id.values())
    products.sort(key=lambda p: p["sku"])

    payload = {
        "scrapedAt": datetime.now(timezone.utc).isoformat(),
        "hub": HUB,
        "plp": PLP,
        "note": "Chanel GB eyewear — See All Sunglasses PLP.",
        "leaves": [
            {
                "id": LEAF_ID,
                "label": "Sunglasses",
                "labelKo": "선글라스",
                "url": PLP,
            }
        ],
        "leafCounts": dict(leaf_counts),
        "skipped": skipped,
        "failed": failed,
        "products": products,
    }
    OUT_RAW.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    log(f"wrote {len(products)} sunglasses → {OUT_RAW}")
    log(f"leafCounts={dict(leaf_counts)}")
    log(f"skipped={len(skipped)} failed={len(failed)}")
    return 0 if products else 1


if __name__ == "__main__":
    raise SystemExit(main())
