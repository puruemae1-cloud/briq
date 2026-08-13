#!/usr/bin/env python3
"""Scrape Chanel GB other accessories into ch-other-acc-catalog-raw.json + images.

Official leaves (hub https://www.chanel.com/gb/fashion/other-accessories/c/1x1x4/):
  Headwear / Belts / Scarves / Camellias / Winter Accessories / Summer Accessories

Reuses ChanelClient + image helpers from scrape-ch-rtw.py (Akamai/proxy).
SKUs: AAB* / AAC* / classic A##### (belts); not jewellery ABH/ABI, SLG AP*, shoes G*, eyewear A#X.
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
OUT_RAW = ROOT / "src/data/ch/ch-other-acc-catalog-raw.json"
PDP_CACHE = ROOT / "src/data/ch/ch-other-acc-pdp-cache.json"
IMG_ROOT = ROOT / "public/products/ch-pdp"

BASE = "https://www.chanel.com"
HUB = f"{BASE}/gb/fashion/other-accessories/c/1x1x4/"
SITEMAP = f"{BASE}/gb/sitemap.xml"

PARENT_COLS = ["chanel", "chanel-accessories", "ch-other-accessories"]

# Official GB other-accessories leaves (not nested 1x1x4xN — dedicated fashion axes).
LEAVES: list[tuple[str, str, str, str]] = [
    (
        "ch-women-headwear",
        "Headwear",
        "헤드웨어",
        f"{BASE}/gb/fashion/headwear/c/1x1x11/",
    ),
    (
        "ch-women-belts",
        "Belts",
        "벨트",
        f"{BASE}/gb/fashion/belts/c/1x1x6/",
    ),
    (
        "ch-women-scarves",
        "Scarves",
        "스카프",
        f"{BASE}/gb/fashion/scarves/c/1x1x8/",
    ),
    (
        "ch-women-camellias",
        "Camellias",
        "카멜리아",
        f"{BASE}/gb/fashion/camellias/c/1x1x7/",
    ),
    (
        "ch-women-winter-accessories",
        "Winter Accessories",
        "윈터 악세서리",
        f"{BASE}/gb/fashion/winter-accessories/c/1x3x25/",
    ),
    (
        "ch-women-summer-accessories",
        "Summer Accessories",
        "서머 악세서리",
        f"{BASE}/gb/fashion/summer-accessories/c/1x3x23x1/other-accessories/",
    ),
]

EXTRA_LEAF_PLPS: list[tuple[str, str]] = []

LEAF_IDS = [c for c, *_ in LEAVES]
LEAF_META = {
    cid: {"label": en, "labelKo": ko, "url": url} for cid, en, ko, url in LEAVES
}
LEAF_BY_SLUG = {
    "headwear": "ch-women-headwear",
    "belts": "ch-women-belts",
    "scarves": "ch-women-scarves",
    "camellias": "ch-women-camellias",
    "winter-accessories": "ch-women-winter-accessories",
    "summer-accessories": "ch-women-summer-accessories",
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


def order_other_acc_images(images: list[dict]) -> list[str]:
    """Prefer closed front packshots (same preference as handbags)."""
    preferred = (
        "PACKSHOT_ARTISTIQUE_VUE1",
        "PACKSHOT_DEFAULT",
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
        angle_rank = {"FRONT": 0, "BACK": 1, "DETAIL": 2}.get(angle, 5)
        scored.append((rank, angle_rank, i, src))
    scored.sort()
    return [u for _, _, _, u in scored]


order_images = order_other_acc_images


def is_other_acc_sku(sku: str) -> bool:
    s = (sku or "").upper()
    if re.fullmatch(r"A\d+X[A-Z0-9]+", s):
        return False
    if re.fullmatch(r"AP[A-Z0-9]+", s):
        return False
    if re.fullmatch(r"G[A-Z0-9]+", s):
        return False
    if re.fullmatch(r"AS[A-Z0-9]+", s):
        return False
    if re.fullmatch(r"AB[HI][A-Z0-9]+", s):
        return False
    return bool(re.fullmatch(r"A[A-Z0-9]+", s))


def fetch_page(client: ChanelClient, url: str, referer: str = HUB) -> tuple[int, str]:
    """Fetch PLP HTML. Direct first; proxy only if a validated tunnel is already set."""
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
        if last_status == 200 and "/gb/fashion/p/" in last_text:
            return last_status, last_text
        log(
            f"  soft-block {last_status} on {url} "
            f"(attempt {attempt}, len={len(last_text)})"
        )
        time.sleep(1.5)
        client.soft_refresh()
        client.warm()
    return last_status, last_text


def extract_skus_from_html(html: str) -> set[str]:
    skus = set(re.findall(r"/gb/fashion/p/([A-Z][A-Z0-9]+)/", html, flags=re.I))
    skus |= set(
        re.findall(r"\\?/gb\\?/fashion\\?/p\\?/([A-Z][A-Z0-9]+)\\?/", html, flags=re.I)
    )
    return {s for s in skus if is_other_acc_sku(s)}


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


def leaves_from_slug(slug: str) -> set[str]:
    s = (slug or "").lower()
    leaves: set[str] = set()
    if re.search(r"camellia", s):
        leaves.add("ch-women-camellias")
    if re.search(r"belt", s):
        leaves.add("ch-women-belts")
    if re.search(r"hat|beret|\bcap\b|cloche|beanie", s):
        leaves.add("ch-women-headwear")
    if re.search(r"scarf|shawl|bandeau|muffler", s):
        leaves.add("ch-women-scarves")
    if re.search(r"glove|muffler|collar|cashmere|beanie|travel|blanket|pillow", s):
        leaves.add("ch-women-winter-accessories")
    if re.search(r"beach|surf|straw|raffia|ponytail|hair|cup", s):
        leaves.add("ch-women-summer-accessories")
    return leaves


def discover_sitemap_other_acc(client: ChanelClient) -> tuple[dict[str, str], dict[str, set[str]]]:
    """SKU → PDP URL and slug-inferred leaves (PLPs are often Akamai-blocked)."""
    # Separate session so sitemap cookies do not clobber a working PDP proxy.
    try:
        import curl_cffi.requests as _req

        r = _req.Session().get(
            SITEMAP,
            impersonate="safari17_2_ios",
            timeout=60,
            headers=_rtw.HTML_HEADERS,
        )
        status, text = r.status_code, r.text
    except Exception:
        status, text = 0, ""
    if status != 200 or len(text) < 1000:
        try:
            r = client.session.get(
                SITEMAP,
                impersonate=client.impersonate,
                timeout=90,
                headers=_rtw.HTML_HEADERS,
                proxies=client.proxies,
            )
            status, text = r.status_code, r.text
        except Exception:
            return {}, {}
    by_sku: dict[str, str] = {}
    sku_leaves: dict[str, set[str]] = defaultdict(set)
    for m in re.finditer(
        r"https://www\.chanel\.com/gb/fashion/p/(A[A-Z0-9]+)/([^/<\"\s]+)/?",
        text,
        flags=re.I,
    ):
        sku = m.group(1)
        slug = m.group(2)
        if not re.match(r"^A(AB|AC|73)", sku, re.I):
            continue
        by_sku.setdefault(sku, m.group(0).rstrip("/") + "/")
        sku_leaves[sku] |= leaves_from_slug(slug)
    log(
        f"sitemap other-acc SKUs: {len(by_sku)} "
        f"slug-tagged={sum(1 for v in sku_leaves.values() if v)}"
    )
    return by_sku, sku_leaves


def leaf_from_hierarchy(prod: dict) -> str | None:
    for h in prod.get("hierarchy") or []:
        url = (h.get("url") or "").lower()
        label = (h.get("label") or h.get("title") or "").lower()
        for slug, cid in LEAF_BY_SLUG.items():
            if f"/{slug}/" in url or url.rstrip("/").endswith(f"/{slug}"):
                return cid
        if "/1x1x11/" in url or "headwear" in label or label in {"hat", "hats", "cap"}:
            return "ch-women-headwear"
        if "/1x1x6/" in url or "belt" in label:
            return "ch-women-belts"
        if "/1x1x8/" in url or "scarf" in label or "scarves" in label or "bandeau" in label:
            return "ch-women-scarves"
        if "/1x1x7/" in url or "camellia" in label:
            return "ch-women-camellias"
        if "/1x3x25/" in url or "winter accessor" in label or "travel" in label:
            return "ch-women-winter-accessories"
        if "/1x3x23" in url or "summer accessor" in label:
            return "ch-women-summer-accessories"
    cat = (prod.get("categoryLabel") or "").lower()
    if "headwear" in cat or cat in {"hat", "hats", "cap"}:
        return "ch-women-headwear"
    if "belt" in cat:
        return "ch-women-belts"
    if "scarf" in cat or "scarves" in cat or "bandeau" in cat:
        return "ch-women-scarves"
    if "camellia" in cat:
        return "ch-women-camellias"
    if "winter" in cat or "travel" in cat:
        return "ch-women-winter-accessories"
    if "summer" in cat:
        return "ch-women-summer-accessories"
    return None


def resolve_other_acc_leaves(
    prod: dict, forced_leaves: set[str] | None = None, url: str = ""
) -> tuple[str | None, set[str]]:
    """Keep official PLP tags; prefer hierarchy for primary."""
    forced = {c for c in (forced_leaves or set()) if c in LEAF_IDS}
    hier = leaf_from_hierarchy(prod)
    if hier:
        forced.add(hier)
    if not forced:
        slug = (url or prod.get("url") or "").rstrip("/").split("/")[-1]
        forced |= leaves_from_slug(slug)
    primary = hier if hier in LEAF_IDS else next((c for c in LEAF_IDS if c in forced), None)
    return primary, forced


def parse_other_acc_pdp(html: str, url: str, forced_leaves: set[str]) -> dict | None:
    nd = extract_next_data(html)
    if not nd:
        return None
    data = (nd.get("props") or {}).get("pageProps", {}).get("data") or {}
    prod = data.get("product")
    if not isinstance(prod, dict):
        return None

    sku = str(prod.get("sku") or prod.get("id") or "").strip()
    if not sku or not is_other_acc_sku(sku):
        return {
            "_skip": True,
            "reason": f"not-other-acc-sku:{sku}",
            "sku": sku,
            "url": url,
        }

    gbp = parse_gbp(prod.get("price"))
    if gbp is None or gbp <= 0:
        return {
            "_skip": True,
            "sku": sku,
            "reason": f"bad price {prod.get('price')!r}",
            "url": url,
        }

    primary, leaves = resolve_other_acc_leaves(prod, forced_leaves, url)
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
        "kind": "other-acc",
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
    # Keep RTW probe SKU — connectivity check only; guessed other-acc slugs 404.
    # safari17 is IP-banned; safari18 still serves PDPs.
    _rtw.IMPERSONATES = ("safari18_0_ios",)
    _rtw.SEED_PROXIES = []

    def _no_proxy(self) -> None:
        return None

    _rtw.ChanelClient.ensure_proxy = _no_proxy

    client = ChanelClient()

    leaf_to_skus: dict[str, set[str]] = {}
    sku_leaves: dict[str, set[str]] = defaultdict(set)
    sku_urls: dict[str, str] = {}

    log("seeding other-accessories from sitemap (PLPs are Akamai-blocked)")
    sitemap, sitemap_leaves = discover_sitemap_other_acc(client)
    hub_ids: set[str] = set()
    for sku in hub_ids:
        if sku not in sku_leaves and not re.match(r"^A(AB|AC|73)", sku, re.I):
            continue
        sku_urls.setdefault(sku, sitemap.get(sku) or f"{BASE}/gb/fashion/p/{sku}/")

    for sku, leaves in sku_leaves.items():
        sku_urls[sku] = sitemap.get(sku) or f"{BASE}/gb/fashion/p/{sku}/"

    for sku, url in sitemap.items():
        sku_urls.setdefault(sku, url)
        sku_leaves[sku] |= sitemap_leaves.get(sku) or set()

    if not sku_urls:
        log("ERROR: no other-acc SKUs from PLP or sitemap")
        return 1

    todo = sorted(sku_urls.items())
    log(
        f"unique other-acc SKUs to scrape: {len(todo)} "
        f"(leaf-tagged={len(sku_leaves)} hub={len(hub_ids)})"
    )

    cache = load_cache()
    products: list[dict] = []
    skipped: list[dict] = []
    failed: list[dict] = []
    leaf_counts: Counter[str] = Counter()

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
            and cached.get("kind") == "other-acc"
            and not cached.get("_skip")
        ):
            primary, leaves = resolve_other_acc_leaves(cached, forced, url)
            primary = primary or cached.get("leaf")
            if not primary:
                continue
            cached["leaf"] = primary
            cached["leaves"] = sorted(leaves or {primary})
            cached["collections"] = sorted(set([*PARENT_COLS, *cached["leaves"]]))
            if not cached.get("localImages"):
                cached = enrich_images(client, cached)
            cache[sku] = cached
            save_cache(cache)
            products.append(cached)
            leaf_counts[cached["leaf"]] += 1
            continue

        status, html = fetch_page(client, url, referer=HUB)
        if is_challenge(html, status):
            consecutive_blocks += 1
            log(
                f"[{i}/{len(todo)}] blocked {sku} "
                f"(streak={consecutive_blocks}, proxy={client._proxy})"
            )
            time.sleep(HARD_BLOCK_SLEEP)
            if consecutive_blocks >= 4:
                failed.append(
                    {"sku": sku, "url": url, "status": status, "reason": "akamai"}
                )
                consecutive_blocks = 0
                continue
            i -= 1
            continue

        consecutive_blocks = 0
        parsed = parse_other_acc_pdp(html, url, forced)
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

    by_id: dict[str, dict] = {p["sku"]: p for p in products if p.get("sku")}
    for sku, row in cache.items():
        if (
            isinstance(row, dict)
            and row.get("gbpPrice")
            and row.get("kind") == "other-acc"
            and not row.get("_skip")
            and sku not in by_id
        ):
            by_id[sku] = row
    products = list(by_id.values())
    products.sort(key=lambda p: p["sku"])
    leaf_counts = Counter(p.get("leaf") for p in products if p.get("leaf"))

    payload = {
        "scrapedAt": datetime.now(timezone.utc).isoformat(),
        "hub": HUB,
        "note": (
            "Chanel GB other accessories by official PLP leaves "
            "(Headwear / Belts / Scarves / Camellias / Winter / Summer)."
        ),
        "leaves": [
            {"id": cid, "label": en, "labelKo": ko, "url": url}
            for cid, en, ko, url in LEAVES
        ],
        "leafCounts": dict(leaf_counts),
        "skipped": skipped,
        "failed": failed,
        "products": products,
    }
    OUT_RAW.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    log(f"wrote {len(products)} other-acc → {OUT_RAW}")
    log(f"leafCounts={dict(leaf_counts)}")
    log(f"skipped={len(skipped)} failed={len(failed)}")
    return 0 if products else 1


if __name__ == "__main__":
    raise SystemExit(main())
