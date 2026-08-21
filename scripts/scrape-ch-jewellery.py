#!/usr/bin/env python3
"""Scrape Chanel GB costume jewellery into ch-jewellery-catalog-raw.json + images.

Official leaves (Costume Jewellery hub https://www.chanel.com/gb/fashion/costume-jewellery/c/1x1x3/):
  Earrings / Necklaces / Bracelets & Cuffs / Brooches / Rings

Reuses ChanelClient + image helpers from scrape-ch-rtw.py (Akamai/proxy).
SKU prefixes: AB* (costume jewellery; not bags A0* / shoes G*).
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
OUT_RAW = ROOT / "src/data/ch/ch-jewellery-catalog-raw.json"
PDP_CACHE = ROOT / "src/data/ch/ch-jewellery-pdp-cache.json"
IMG_ROOT = ROOT / "public/products/ch-pdp"

BASE = "https://www.chanel.com"
HUB = f"{BASE}/gb/fashion/costume-jewellery/c/1x1x3/"
SITEMAP = f"{BASE}/gb/sitemap.xml"

PARENT_COLS = ["chanel", "chanel-accessories", "ch-jewellery"]

# (collection id, EN label, KO label, PLP URL)
LEAVES: list[tuple[str, str, str, str]] = [
    (
        "ch-women-earrings",
        "Earrings",
        "이어링",
        f"{BASE}/gb/fashion/costume-jewellery/c/1x1x3x2/earrings/",
    ),
    (
        "ch-women-necklaces",
        "Necklaces",
        "네크리스",
        f"{BASE}/gb/fashion/costume-jewellery/c/1x1x3x3/necklaces/",
    ),
    (
        "ch-women-bracelets-cuffs",
        "Bracelets & Cuffs",
        "브레이슬릿 & 커프",
        f"{BASE}/gb/fashion/costume-jewellery/c/1x1x3x1/bracelets-cuffs/",
    ),
    (
        "ch-women-brooches",
        "Brooches",
        "브로치",
        f"{BASE}/gb/fashion/costume-jewellery/c/1x1x3x4/brooches/",
    ),
    (
        "ch-women-rings",
        "Rings",
        "링",
        f"{BASE}/gb/fashion/costume-jewellery/c/1x1x3x6/rings/",
    ),
]

LEAF_IDS = [c for c, *_ in LEAVES]
LEAF_META = {
    cid: {"label": en, "labelKo": ko, "url": url} for cid, en, ko, url in LEAVES
}
LEAF_BY_SLUG = {
    "earrings": "ch-women-earrings",
    "necklaces": "ch-women-necklaces",
    "bracelets-cuffs": "ch-women-bracelets-cuffs",
    "brooches": "ch-women-brooches",
    "rings": "ch-women-rings",
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


def order_jewellery_images(images: list[dict]) -> list[str]:
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


order_images = order_jewellery_images


def is_jewellery_sku(sku: str) -> bool:
    s = (sku or "").upper()
    return bool(re.fullmatch(r"AB[A-Z0-9]+", s))


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
    return {s for s in skus if is_jewellery_sku(s)}


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


def discover_sitemap_jewellery_skus(client: ChanelClient) -> dict[str, str]:
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
        r"https://www\.chanel\.com/gb/fashion/p/(AB[^/\s\"<]+)/",
        text,
        flags=re.I,
    ):
        sku = m.group(1)
        if not is_jewellery_sku(sku):
            continue
        by_sku.setdefault(sku, m.group(0).rstrip("/") + "/")
    log(f"sitemap AB* SKUs: {len(by_sku)}")
    return by_sku


def _label_is_rings(label: str) -> bool:
    # Do NOT use bare "ring" — it matches "earrings".
    return bool(re.search(r"\brings?\b", label or ""))


def leaf_from_hierarchy(prod: dict) -> str | None:
    for h in prod.get("hierarchy") or []:
        url = (h.get("url") or "").lower()
        label = (h.get("label") or h.get("title") or "").lower()
        for slug, cid in LEAF_BY_SLUG.items():
            if f"/{slug}/" in url or url.rstrip("/").endswith(f"/{slug}"):
                return cid
        if "/1x1x3x2/" in url or "earring" in label:
            return "ch-women-earrings"
        if "/1x1x3x3/" in url or "necklace" in label or "choker" in label:
            return "ch-women-necklaces"
        if "/1x1x3x1/" in url or "bracelet" in label or "cuff" in label:
            return "ch-women-bracelets-cuffs"
        if "/1x1x3x4/" in url or "brooch" in label:
            return "ch-women-brooches"
        if "/1x1x3x6/" in url or _label_is_rings(label):
            return "ch-women-rings"
    cat = (prod.get("categoryLabel") or "").lower()
    if "earring" in cat:
        return "ch-women-earrings"
    if "necklace" in cat or "choker" in cat:
        return "ch-women-necklaces"
    if "bracelet" in cat or "cuff" in cat:
        return "ch-women-bracelets-cuffs"
    if "brooch" in cat:
        return "ch-women-brooches"
    if _label_is_rings(cat):
        return "ch-women-rings"
    return None


def resolve_jewellery_leaf(prod: dict, forced_leaves: set[str] | None = None) -> str | None:
    """Prefer PDP hierarchy over PLP membership (rings PLP mixed hub SKUs)."""
    hier = leaf_from_hierarchy(prod)
    if hier:
        return hier
    forced = set(forced_leaves or [])
    return next((cid for cid in LEAF_IDS if cid in forced), None)


def parse_jewellery_pdp(html: str, url: str, forced_leaves: set[str]) -> dict | None:
    nd = extract_next_data(html)
    if not nd:
        return None
    data = (nd.get("props") or {}).get("pageProps", {}).get("data") or {}
    prod = data.get("product")
    if not isinstance(prod, dict):
        return None

    sku = str(prod.get("sku") or prod.get("id") or "").strip()
    if not sku or not is_jewellery_sku(sku):
        return {"_skip": True, "reason": f"not-jewellery-sku:{sku}", "sku": sku, "url": url}

    gbp = parse_gbp(prod.get("price"))
    if gbp is None or gbp <= 0:
        return {
            "_skip": True,
            "sku": sku,
            "reason": f"bad price {prod.get('price')!r}",
            "url": url,
        }

    primary = resolve_jewellery_leaf(prod, forced_leaves)
    if not primary:
        return {
            "_skip": True,
            "sku": sku,
            "reason": f"unmapped leaf categoryLabel={prod.get('categoryLabel')!r}",
            "url": url,
            "categoryLabel": prod.get("categoryLabel"),
            "hierarchy": prod.get("hierarchy"),
        }
    # Single official leaf — do not keep polluted PLP tags (esp. rings hub mix).
    leaves = {primary}

    top_status, stock_by_id = availability_map(data.get("availability"))
    variants_out: list[dict] = []
    any_in = False
    for v in prod.get("variants") or []:
        if not isinstance(v, dict):
            continue
        size = str(v.get("orliSize") or v.get("size") or "").strip() or "UNI"
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
    if not variants_out:
        variants_out.append(
            {
                "id": sku,
                "size": "UNI",
                "orliSize": "UNI",
                "sku": sku,
                "inStock": top_status == "IN_STOCK",
                "sellableOnline": True,
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
        "kind": "jewellery",
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
        "https://www.chanel.com/gb/fashion/p/ABH668B25242UB742/"
    )

    client = ChanelClient()
    if not client._proxy:
        client.ensure_proxy()
        client.warm()

    leaf_to_skus: dict[str, set[str]] = {}
    sku_leaves: dict[str, set[str]] = defaultdict(set)
    sku_urls: dict[str, str] = {}

    log("discovering jewellery PLPs…")
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

    sitemap = discover_sitemap_jewellery_skus(client)
    # Prefer leaf-tagged SKUs only — hub pages mix related SKUs and inflate Akamai load.
    for sku in list(sku_leaves):
        sku_urls[sku] = sitemap.get(sku) or f"{BASE}/gb/fashion/p/{sku}/"

    todo = sorted(sku_urls.items())
    log(f"unique jewellery SKUs to scrape: {len(todo)} (leaf-tagged={len(sku_leaves)})")

    cache = load_cache()
    products: list[dict] = []
    skipped: list[dict] = []
    failed: list[dict] = []
    leaf_counts: Counter[str] = Counter()

    if not wait_for_pdp_access(client):
        log(
            "WARN: PDP access blocked (Akamai/proxy) — skipping new PDPs; "
            "keeping existing catalogue raw/cache so weekly stock sync can finish"
        )
        return 0

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
            and cached.get("kind") == "jewellery"
            and not cached.get("_skip")
        ):
            primary = resolve_jewellery_leaf(cached, forced) or cached["leaf"]
            leaves = {primary}
            cached["leaf"] = primary
            cached["leaves"] = sorted(leaves)
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
                if not wait_for_pdp_access(client, max_wait_s=90):
                    failed.append(
                        {"sku": sku, "url": url, "status": status, "reason": "akamai"}
                    )
                    consecutive_blocks = 0
                    i += 1
                else:
                    consecutive_blocks = 0
            continue

        consecutive_blocks = 0
        parsed = parse_jewellery_pdp(html, url, forced)
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
                and cached.get("kind") == "jewellery"
                and cached.get("gbpPrice")
                and cached.get("leaf")
                and not cached.get("_skip")
            ):
                by_id[sku] = cached
                leaf_counts[cached["leaf"]] += 1
        if by_id:
            log(f"PLP empty — recovered {len(by_id)} jewellery from PDP cache")

    products = sorted(by_id.values(), key=lambda p: p["sku"])

    collections_meta = {}
    for cid, meta in LEAF_META.items():
        n = sum(1 for p in products if cid in (p.get("collections") or []))
        collections_meta[cid] = {**meta, "count": n}

    payload = {
        "scrapedAt": datetime.now(timezone.utc).isoformat(),
        "source": HUB,
        "note": "Chanel GB costume jewellery by official PLP leaves; multi-leaf SKUs keep all tags.",
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
        log(f"ERROR: 0 jewellery scraped — leaving existing raw untouched ({OUT_RAW})")
        return 1
    OUT_RAW.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    log(f"Wrote {len(products)} jewellery → {OUT_RAW}")
    log(f"leafCounts={dict(leaf_counts)}")
    return 0 if products else 1


if __name__ == "__main__":
    raise SystemExit(main())
