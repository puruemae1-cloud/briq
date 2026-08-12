#!/usr/bin/env python3
"""Scrape Chanel GB shoes into ch-shoes-catalog-raw.json + images.

Official leaves (Shoes hub https://www.chanel.com/gb/fashion/shoes/c/1x1x5/):
  Pumps & Slingbacks / Ballet Flats & Mary Janes / Elegant Sandals /
  Casual Sandals / Loafers / Boots / Sneakers

Reuses ChanelClient + image helpers from scrape-ch-rtw.py (Akamai/proxy).
SKU prefixes: G* (not RTW P* / bags A*).
"""
from __future__ import annotations

import importlib.util
import json
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_RAW = ROOT / "src/data/ch/ch-shoes-catalog-raw.json"
PDP_CACHE = ROOT / "src/data/ch/ch-shoes-pdp-cache.json"
IMG_ROOT = ROOT / "public/products/ch-pdp"

BASE = "https://www.chanel.com"
HUB = f"{BASE}/gb/fashion/shoes/c/1x1x5/"
SITEMAP = f"{BASE}/gb/sitemap.xml"

PARENT_COLS = ["chanel", "chanel-shoes", "ch-shoes"]

# (collection id, EN label, KO label, PLP URL)
LEAVES: list[tuple[str, str, str, str]] = [
    (
        "ch-women-pumps-slingbacks",
        "Pumps & Slingbacks",
        "펌프스 & 슬링백",
        f"{BASE}/gb/fashion/shoes/c/1x1x5x5/slingbacks-and-pumps/",
    ),
    (
        "ch-women-ballet-mary-janes",
        "Ballet Flats & Mary Janes",
        "발레 플랫 & 메리제인",
        f"{BASE}/gb/fashion/shoes/c/1x1x5x3/ballet-flats/",
    ),
    (
        "ch-women-elegant-sandals",
        "Elegant Sandals",
        "엘레강트 샌들",
        f"{BASE}/gb/fashion/elegant-sandals/c/1x3x28/",
    ),
    (
        "ch-women-casual-sandals",
        "Casual Sandals",
        "캐주얼 샌들",
        f"{BASE}/gb/fashion/shoes/c/1x1x5x4/casual-sandals/",
    ),
    (
        "ch-women-loafers",
        "Loafers",
        "로퍼",
        f"{BASE}/gb/fashion/shoes/c/1x1x5x7/moccasins/",
    ),
    (
        "ch-women-boots",
        "Boots",
        "부츠",
        f"{BASE}/gb/fashion/shoes/c/1x1x5x2/short-boots/",
    ),
    (
        "ch-women-sneakers",
        "Sneakers",
        "스니커즈",
        f"{BASE}/gb/fashion/shoes/c/1x1x5x8/sneakers/",
    ),
]

LEAF_IDS = [c for c, *_ in LEAVES]
LEAF_META = {
    cid: {"label": en, "labelKo": ko, "url": url} for cid, en, ko, url in LEAVES
}
LEAF_BY_SLUG = {
    "slingbacks-and-pumps": "ch-women-pumps-slingbacks",
    "ballet-flats": "ch-women-ballet-mary-janes",
    "elegant-sandals": "ch-women-elegant-sandals",
    "casual-sandals": "ch-women-casual-sandals",
    "moccasins": "ch-women-loafers",
    "short-boots": "ch-women-boots",
    "sneakers": "ch-women-sneakers",
}

PDP_PAUSE = 1.2
HARD_BLOCK_SLEEP = 12.0
MAX_PLP_PAGES = 12

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


def order_shoe_images(images: list[dict]) -> list[str]:
    """Prefer closed front / default packshots for shoes."""
    preferred = (
        "PACKSHOT_DEFAULT",
        "PACKSHOT_ARTISTIQUE_VUE1",
        "PACKSHOT_ARTISTIQUE_VUE2",
        "PACKSHOT_ARTISTIQUE_VUE3",
        "PACKSHOT_ARTISTIQUE_VUE4",
        "PACKSHOT_ARTISTIQUE_VUE5",
        "PACKSHOT_ALTERNATIVE",
        "PACKSHOT_EXTRA",
        "PACKSHOT_OTHER",
        "PACKSHOT_ARTISTIQUE_VUE1_LARGE",
        "LOOK",
        "EDITORIAL",
    )
    scored: list[tuple[int, int, int, str]] = []
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
        angle = (im.get("viewAngle") or "").upper()
        angle_rank = {"FRONT": 0, "SIDE": 1, "BACK": 2, "DETAIL": 3}.get(angle, 5)
        scored.append((rank, angle_rank, i, src))
    scored.sort()
    return [u for _, _, _, u in scored]


order_images = order_shoe_images


def is_shoe_sku(sku: str) -> bool:
    s = (sku or "").upper()
    return bool(re.fullmatch(r"G[A-Z0-9]+", s))


def fetch_page(client: ChanelClient, url: str, referer: str = HUB) -> tuple[int, str]:
    """Fetch PLP/HTML preferring proxy when available (Akamai soft-blocks direct PLPs)."""
    headers = {**_rtw.HTML_HEADERS, "Referer": referer}
    last_status, last_text = 0, ""
    for attempt in range(1, 5):
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
        if last_status == 200 and "/gb/fashion/p/" in last_text and len(last_text) > 20000:
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
    skus = set(re.findall(r"/gb/fashion/p/([A-Z][A-Z0-9]+)/", html, flags=re.I))
    skus |= set(
        re.findall(r"\\?/gb\\?/fashion\\?/p\\?/([A-Z][A-Z0-9]+)\\?/", html, flags=re.I)
    )
    return {s for s in skus if is_shoe_sku(s)}


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


def discover_sitemap_shoe_skus(client: ChanelClient) -> dict[str, str]:
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
        r"https://www\.chanel\.com/gb/fashion/p/(G[^/\s\"<]+)/",
        text,
        flags=re.I,
    ):
        sku = m.group(1)
        if not is_shoe_sku(sku):
            continue
        by_sku.setdefault(sku, m.group(0).rstrip("/") + "/")
    log(f"sitemap G* SKUs: {len(by_sku)}")
    return by_sku


def leaf_from_hierarchy(prod: dict) -> str | None:
    for h in prod.get("hierarchy") or []:
        url = (h.get("url") or "").lower()
        label = (h.get("label") or h.get("title") or "").lower()
        for slug, cid in LEAF_BY_SLUG.items():
            if f"/{slug}/" in url or url.rstrip("/").endswith(f"/{slug}"):
                return cid
        if "/1x1x5x5/" in url or "slingback" in label or "pump" in label:
            return "ch-women-pumps-slingbacks"
        if "/1x1x5x3/" in url or "ballet" in label or "mary jane" in label:
            return "ch-women-ballet-mary-janes"
        if "/1x3x28/" in url or "elegant sandal" in label:
            return "ch-women-elegant-sandals"
        if "/1x1x5x4/" in url or "casual sandal" in label or "espadrille" in label:
            return "ch-women-casual-sandals"
        if "/1x1x5x7/" in url or "loafer" in label or "moccasin" in label:
            return "ch-women-loafers"
        if "/1x1x5x2/" in url or "boot" in label:
            return "ch-women-boots"
        if "/1x1x5x8/" in url or "sneaker" in label:
            return "ch-women-sneakers"
    cat = (prod.get("categoryLabel") or "").lower()
    if "slingback" in cat or "pump" in cat:
        return "ch-women-pumps-slingbacks"
    if "ballet" in cat or "mary jane" in cat:
        return "ch-women-ballet-mary-janes"
    if "elegant" in cat and "sandal" in cat:
        return "ch-women-elegant-sandals"
    if "casual" in cat and "sandal" in cat:
        return "ch-women-casual-sandals"
    if "loafer" in cat or "moccasin" in cat:
        return "ch-women-loafers"
    if "boot" in cat:
        return "ch-women-boots"
    if "sneaker" in cat:
        return "ch-women-sneakers"
    return None


def parse_shoe_pdp(html: str, url: str, forced_leaves: set[str]) -> dict | None:
    nd = extract_next_data(html)
    if not nd:
        return None
    data = (nd.get("props") or {}).get("pageProps", {}).get("data") or {}
    prod = data.get("product")
    if not isinstance(prod, dict):
        return None

    sku = str(prod.get("sku") or prod.get("id") or "").strip()
    if not sku or not is_shoe_sku(sku):
        return {"_skip": True, "reason": f"not-shoe-sku:{sku}", "sku": sku, "url": url}

    gbp = parse_gbp(prod.get("price"))
    if gbp is None or gbp <= 0:
        return {
            "_skip": True,
            "sku": sku,
            "reason": f"bad price {prod.get('price')!r}",
            "url": url,
        }

    hier_leaf = leaf_from_hierarchy(prod)
    leaves = set(forced_leaves)
    if hier_leaf:
        leaves.add(hier_leaf)
    primary = next((cid for cid in LEAF_IDS if cid in leaves), None)
    if not primary:
        return {
            "_skip": True,
            "sku": sku,
            "reason": f"unmapped leaf categoryLabel={prod.get('categoryLabel')!r}",
            "url": url,
            "categoryLabel": prod.get("categoryLabel"),
            "hierarchy": prod.get("hierarchy"),
        }

    top_status, stock_by_id = availability_map(data.get("availability"))
    variants_out: list[dict] = []
    any_in = False
    for v in prod.get("variants") or []:
        if not isinstance(v, dict):
            continue
        size = str(v.get("orliSize") or v.get("size") or "").strip()
        if not size:
            continue
        vid = str(v.get("id") or f"{sku}-{size}")
        in_stock = bool(stock_by_id.get(vid, False))
        if in_stock:
            any_in = True
        variants_out.append(
            {
                "id": vid,
                "size": size,
                "orliSize": size,
                "sku": vid,
                "inStock": in_stock,
                "sellableOnline": bool(v.get("sellableOnline")),
            }
        )
    if top_status == "IN_STOCK" and not any_in:
        any_in = True

    details = prod.get("details") if isinstance(prod.get("details"), dict) else {}
    cols = sorted(set([*PARENT_COLS, *leaves]))

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
        },
        "images": order_images(prod.get("images") or []),
        "imageMeta": [
            {
                "typology": im.get("typology"),
                "viewAngle": im.get("viewAngle"),
                "viewLabel": im.get("viewLabel"),
                "source": normalize_img_url(im.get("source")),
                "id": im.get("id"),
            }
            for im in (prod.get("images") or [])
            if isinstance(im, dict) and im.get("source")
        ],
        "sizes": variants_out,
        "availabilityStatus": top_status,
        "inStock": any_in or top_status == "IN_STOCK",
        "new": bool(prod.get("new")),
        "collections": cols,
        "leaf": primary,
        "leaves": sorted(leaves),
        "kind": "shoe",
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
        "https://www.chanel.com/gb/fashion/p/G45509B24977UB332/"
    )

    client = ChanelClient()
    if not client._proxy:
        client.ensure_proxy()
        client.warm()

    leaf_to_skus: dict[str, set[str]] = {}
    sku_leaves: dict[str, set[str]] = defaultdict(set)
    sku_urls: dict[str, str] = {}

    log("discovering shoe PLPs…")
    for cid, en, _ko, url in LEAVES:
        log(f"leaf {cid} ({en})")
        ids = discover_plp_skus(client, url)
        if not ids and not client._proxy:
            client.ensure_proxy()
            client.warm()
            ids = discover_plp_skus(client, url)
        if not ids:
            client.soft_refresh()
            client.warm()
            ids = discover_plp_skus(client, url)
        leaf_to_skus[cid] = ids
        for sku in ids:
            sku_leaves[sku].add(cid)
            sku_urls.setdefault(sku, f"{BASE}/gb/fashion/p/{sku}/")
        time.sleep(0.8)

    sitemap = discover_sitemap_shoe_skus(client)
    # Prefer leaf-tagged SKUs only — hub pages mix related SKUs and inflate Akamai load.
    for sku in list(sku_leaves):
        sku_urls[sku] = sitemap.get(sku) or f"{BASE}/gb/fashion/p/{sku}/"

    todo = sorted(sku_urls.items())
    log(f"unique shoe SKUs to scrape: {len(todo)} (leaf-tagged={len(sku_leaves)})")

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
        forced = set(sku_leaves.get(sku) or [])

        cached = cache.get(sku)
        if (
            isinstance(cached, dict)
            and cached.get("gbpPrice")
            and cached.get("leaf")
            and cached.get("kind") == "shoe"
            and not cached.get("_skip")
        ):
            leaves = set(cached.get("leaves") or []) | forced
            if leaves:
                cached["leaves"] = sorted(leaves)
                primary = next((cid for cid in LEAF_IDS if cid in leaves), cached["leaf"])
                cached["leaf"] = primary
                cached["collections"] = sorted(set([*PARENT_COLS, *leaves]))
            if not cached.get("localImages"):
                cached = enrich_images(client, cached)
                cache[sku] = cached
                save_cache(cache)
            products.append(cached)
            leaf_counts[cached["leaf"]] += 1
            continue

        status, html = client.get_html(url, referer=HUB, max_attempts=3)
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
        parsed = parse_shoe_pdp(html, url, forced)
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
        leaf_counts[parsed["leaf"]] += 1
        log(
            f"[{i}/{len(todo)}] OK {sku} {parsed['leaf']} "
            f"£{parsed['gbpPrice']} sizes={len(parsed.get('sizes') or [])} "
            f"imgs={len(parsed.get('localImages') or [])}"
        )
        save_cache(cache)
        time.sleep(PDP_PAUSE)

    save_cache(cache)

    by_id: dict[str, dict] = {}
    for p in products:
        by_id[p["sku"]] = p

    # If PLPs were fully blocked, fall back to previously cached shoes so we
    # never wipe a good raw catalog with an empty scrape.
    if not by_id:
        for sku, cached in cache.items():
            if (
                isinstance(cached, dict)
                and cached.get("kind") == "shoe"
                and cached.get("gbpPrice")
                and cached.get("leaf")
                and not cached.get("_skip")
            ):
                by_id[sku] = cached
                leaf_counts[cached["leaf"]] += 1
        if by_id:
            log(f"PLP empty — recovered {len(by_id)} shoes from PDP cache")

    products = sorted(by_id.values(), key=lambda p: p["sku"])

    collections_meta = {}
    for cid, meta in LEAF_META.items():
        n = sum(1 for p in products if cid in (p.get("collections") or []))
        collections_meta[cid] = {**meta, "count": n}

    payload = {
        "scrapedAt": datetime.now(timezone.utc).isoformat(),
        "source": HUB,
        "note": "Chanel GB shoes by official PLP leaves; multi-leaf SKUs keep all tags.",
        "collections": collections_meta,
        "count": len(products),
        "skippedCount": len(skipped),
        "failedCount": len(failed),
        "leafCounts": dict(leaf_counts),
        "products": products,
        "skipped": skipped[:50],
        "failed": failed[:50],
    }
    if not products and OUT_RAW.exists():
        log(f"ERROR: 0 shoes scraped — leaving existing raw untouched ({OUT_RAW})")
        return 1
    OUT_RAW.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    log(f"Wrote {len(products)} shoes → {OUT_RAW}")
    log(f"leafCounts={dict(leaf_counts)}")
    return 0 if products else 1


if __name__ == "__main__":
    raise SystemExit(main())
