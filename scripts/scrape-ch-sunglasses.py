#!/usr/bin/env python3
"""Scrape Chanel GB eyewear into ch-sunglasses-catalog-raw.json + images.

Official hub: https://www.chanel.com/gb/eyewear/
Shopable PLPs:
  Sunglasses  /gb/eyewear/sunglasses/c/2x1x1/
  Optical     /gb/eyewear/optical/c/2x1x2/
  Blue light  /gb/eyewear/blue-light-glasses/c/2x1x3/

All land under Accessories → 샤넬 → 선글라스 (ch-women-sunglasses).
Existing SKUs already in raw/cache are kept; only missing PDPs are fetched.
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
SITEMAP = f"{BASE}/gb/sitemap.xml"

LEAF_ID = "ch-women-sunglasses"
PARENT_COLS = ["chanel", "chanel-accessories", "ch-sunglasses", LEAF_ID]

PLPS: list[tuple[str, str, str]] = [
    ("sunglasses", "Sunglasses", f"{BASE}/gb/eyewear/sunglasses/c/2x1x1/"),
    ("optical", "Optical", f"{BASE}/gb/eyewear/optical/c/2x1x2/"),
    (
        "blue-light",
        "Blue Light Glasses",
        f"{BASE}/gb/eyewear/blue-light-glasses/c/2x1x3/",
    ),
]

PDP_PAUSE = 0.8
HARD_BLOCK_SLEEP = 8.0
MAX_PLP_PAGES = 20
PDP_RE = re.compile(
    r"/gb/eyewear/p/(A\d+X[A-Z0-9]+)/([^/\"'?\s<>]+)",
    flags=re.I,
)
SKU_RE = re.compile(r"^A\d+X[A-Z0-9]+$", flags=re.I)

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
log = _rtw.log


def is_eyewear_sku(sku: str) -> bool:
    return bool(SKU_RE.fullmatch((sku or "").upper()))


def pdp_url(sku: str, slug: str = "") -> str:
    slug = (slug or "").strip("/") or "product"
    return f"{BASE}/gb/eyewear/p/{sku.upper()}/{slug}/"


def to_cn_url(url: str) -> str:
    return (url or "").replace("://www.chanel.com/", "://www.chanel.cn/")


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


def _ld_products(html: str) -> list[dict]:
    out: list[dict] = []
    for raw in re.findall(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
        html or "",
        flags=re.S | re.I,
    ):
        try:
            obj = json.loads(raw.strip())
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and obj.get("@type") == "Product":
            out.append(obj)
        elif isinstance(obj, list):
            out.extend(
                x for x in obj if isinstance(x, dict) and x.get("@type") == "Product"
            )
    return out


def _hybris_image_urls(html: str, sku: str) -> list[str]:
    sku_l = sku.lower()
    # Match URL-sku stem (before optional colour/size suffix) for packshots.
    stem = sku_l
    files: list[str] = []
    seen: set[str] = set()
    for m in re.finditer(
        r"https://www\.chanel\.(?:com|cn)/images/[^\"\s>]+", html or ""
    ):
        u = (
            m.group(0)
            .rstrip("\\")
            .split("?")[0]
            .replace("www.chanel.cn", "www.chanel.com")
        )
        if not re.search(r"\.(?:jpg|jpeg|png|webp)$", u, re.I):
            continue
        fn = u.rsplit("/", 1)[-1]
        fl = fn.lower()
        if stem not in fl:
            continue
        # Drop other colourway packshots that only share the A#####X prefix.
        if fl in seen:
            continue
        seen.add(fl)
        files.append(fn)

    def rank(fn: str) -> tuple[int, str]:
        f = fn.lower()
        if "packshot-default" in f:
            return (0, f)
        if "packshot-alternative" in f:
            return (1, f)
        if "packshot-other" in f:
            return (2, f)
        if "packshot-extra" in f:
            return (3, f)
        if "portee" in f or "worn" in f:
            return (4, f)
        return (5, f)

    files.sort(key=rank)
    return [
        "https://www.chanel.com/images/t_one/q_auto:good,f_auto,fl_lossy,dpr_1.1/"
        f"w_1240/{fn}"
        for fn in files[:12]
    ]


def parse_next_eyewear(html: str, url: str, sku_hint: str) -> dict | None:
    nd = extract_next_data(html)
    if not nd:
        return None
    data = (nd.get("props") or {}).get("pageProps", {}).get("data") or {}
    prod = data.get("product")
    if not isinstance(prod, dict):
        return None

    sku = str(prod.get("sku") or prod.get("id") or sku_hint or "").strip().upper()
    if not sku or not is_eyewear_sku(sku):
        return {
            "_skip": True,
            "reason": f"not-eyewear-sku:{sku}",
            "sku": sku,
            "url": url,
            "kind": "sunglasses",
        }

    gbp = parse_gbp(prod.get("price"))
    if gbp is None or gbp <= 0:
        return {
            "_skip": True,
            "sku": sku,
            "reason": f"bad price {prod.get('price')!r}",
            "url": url,
            "kind": "sunglasses",
        }

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


def parse_hybris_eyewear(html: str, url: str, sku_hint: str) -> dict | None:
    ld_list = _ld_products(html)
    ld = ld_list[0] if ld_list else {}
    sku = (sku_hint or "").upper()
    if not sku:
        m = re.search(r"/eyewear/p/(A\d+X[A-Z0-9]+)/", url, flags=re.I)
        sku = (m.group(1) if m else "").upper()
    if not sku or not is_eyewear_sku(sku):
        return None

    offers = ld.get("offers") if isinstance(ld.get("offers"), dict) else {}
    gbp = parse_gbp(offers.get("price") or ld.get("price"))
    if gbp is None or gbp <= 0:
        m_gbp = re.search(r"£\s*([\d,]+(?:\.\d+)?)", html or "")
        if m_gbp:
            gbp = parse_gbp(m_gbp.group(1))
    if gbp is None or gbp <= 0:
        return {
            "_skip": True,
            "sku": sku,
            "reason": f"bad price {offers.get('price')!r}",
            "url": url,
            "kind": "sunglasses",
        }

    title = str(ld.get("name") or "").strip()
    color = str(ld.get("color") or "").strip()
    material = str(ld.get("material") or "").strip()
    desc = str(ld.get("description") or "").strip()
    images = _hybris_image_urls(html, sku)
    if not images and ld.get("image"):
        images = [
            str(ld.get("image")).replace("www.chanel.cn", "www.chanel.com")
        ]

    slug = ""
    m_slug = re.search(r"/eyewear/p/[^/]+/([^/\"'?]+)", url, flags=re.I)
    if m_slug:
        slug = m_slug.group(1).lower()
    cat = "Sunglasses"
    if "eyeglass" in slug or "optical" in slug:
        cat = "Optical"
    elif "blue-light" in slug:
        cat = "Blue Light Glasses"

    return {
        "id": sku,
        "productCode": sku,
        "sku": sku,
        "title": title,
        "priceLabel": f"£{gbp:,.0f}" if gbp >= 1 else str(offers.get("price") or ""),
        "gbpPrice": gbp,
        "categoryLabel": cat,
        "collection": None,
        "collectionCode": None,
        "url": url if url.startswith("http") else pdp_url(sku, slug),
        "hierarchy": [
            {"label": "Eyewear", "url": "/gb/eyewear/"},
            {"label": cat, "url": ""},
        ],
        "details": {
            "color": color,
            "description": desc if desc and desc.lower() != color.lower() else "",
            "fabrics": material,
            "reference": sku,
            "dimensions": None,
            "eyeLensColor": None,
            "freeStat": None,
            "treatment": None,
        },
        "images": images,
        "imageMeta": [
            {
                "typology": "PACKSHOT_DEFAULT" if i == 0 else "PACKSHOT_OTHER",
                "source": src,
            }
            for i, src in enumerate(images)
        ],
        "sizes": [{"size": "UNI", "orliSize": "UNI", "sku": sku, "inStock": True}],
        "availabilityStatus": "IN_STOCK",
        "inStock": True,
        "new": False,
        "collections": list(PARENT_COLS),
        "leaf": LEAF_ID,
        "leaves": [LEAF_ID],
        "kind": "sunglasses",
    }


def parse_eyewear_pdp(html: str, url: str, sku_hint: str = "") -> dict | None:
    if "__NEXT_DATA__" in (html or ""):
        parsed = parse_next_eyewear(html, url, sku_hint)
        if parsed:
            return parsed
    return parse_hybris_eyewear(html, url, sku_hint)


def fetch_pdp_html(client: ChanelClient, url: str) -> tuple[int, str]:
    """Prefer COM (Next.js details); fall back to CN Hybris GBP mirror."""
    status, html = client.get_html(url, referer=HUB, max_attempts=1)
    if (
        not is_challenge(html, status)
        and len(html) > 20000
        and ("__NEXT_DATA__" in html or "application/ld+json" in html)
    ):
        return status, html

    cn = to_cn_url(url)
    log(f"  CN fallback {cn}")
    try:
        with _rtw._session_lock:
            r = client.session.get(
                cn,
                impersonate=client.impersonate,
                timeout=90,
                headers={**_rtw.HTML_HEADERS, "Referer": to_cn_url(HUB)},
            )
            client._req_count += 1
            st, text = r.status_code, r.text
        if st == 200 and len(text) > 20000 and (
            "application/ld+json" in text or "£" in text or "__NEXT_DATA__" in text
        ):
            return st, text
        log(f"  CN weak st={st} len={len(text)}")
    except Exception as e:
        log(f"  CN GET error: {e}")
    return status, html


def fetch_plp_html(client: ChanelClient, url: str) -> tuple[int, str]:
    cn = to_cn_url(url)
    try:
        with _rtw._session_lock:
            r = client.session.get(
                cn,
                impersonate=client.impersonate,
                timeout=90,
                headers={**_rtw.HTML_HEADERS, "Referer": to_cn_url(HUB)},
            )
            client._req_count += 1
            if r.status_code == 200 and len(r.text) > 10000:
                return r.status_code, r.text
    except Exception as e:
        log(f"  CN PLP error: {e}")
    return client.get_html(url, referer=HUB, max_attempts=1)


def extract_skus_from_html(html: str) -> set[str]:
    return {m.group(1).upper() for m in PDP_RE.finditer(html or "") if is_eyewear_sku(m.group(1))}


def discover_plp_skus(client: ChanelClient) -> dict[str, str]:
    found: dict[str, str] = {}
    for cid, label, url in PLPS:
        log(f"PLP {cid} ({label})")
        pages = [url] + [
            f"{url.rstrip('/')}/page-{n}/" for n in range(2, MAX_PLP_PAGES + 1)
        ]
        leaf_n = 0
        for page in pages:
            st, html = fetch_plp_html(client, page)
            if st == 404:
                break
            if st != 200 or len(html) < 5000:
                if page == url:
                    log(f"  weak {page} st={st} len={len(html)}")
                break
            batch = extract_skus_from_html(html)
            # Also capture slug URLs when present.
            for m in PDP_RE.finditer(html or ""):
                sku, slug = m.group(1).upper(), m.group(2)
                if is_eyewear_sku(sku):
                    found.setdefault(sku, pdp_url(sku, slug))
            before = leaf_n
            leaf_n += len(batch)
            log(f"  {page} → +{len(batch)} (leaf ~{leaf_n})")
            if page != url and not batch:
                break
            if page != url and len(batch) == 0 and before == leaf_n:
                break
            time.sleep(0.3)
    log(f"PLP eyewear SKUs: {len(found)}")
    return found


def discover_sitemap_eyewear_skus(client: ChanelClient) -> dict[str, str]:
    status, text = client.get_html(SITEMAP, max_attempts=2)
    if status != 200 or len(text) < 1000:
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
    for m in PDP_RE.finditer(text or ""):
        sku = m.group(1).upper()
        slug = m.group(2)
        if not is_eyewear_sku(sku):
            continue
        by_sku.setdefault(sku, pdp_url(sku, slug))
    log(f"sitemap eyewear SKUs: {len(by_sku)}")
    return by_sku


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
            cn = url.replace("www.chanel.com", "www.chanel.cn")
            data = client.get_bytes(cn, referer=to_cn_url(HUB))
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


def load_existing_products() -> dict[str, dict]:
    by: dict[str, dict] = {}
    if OUT_RAW.exists():
        try:
            for p in json.loads(OUT_RAW.read_text()).get("products") or []:
                sku = str(p.get("sku") or "").upper()
                if sku and p.get("gbpPrice") and not p.get("_skip"):
                    by[sku] = p
        except Exception:
            pass
    return by


def is_complete(row: dict) -> bool:
    if not isinstance(row, dict) or row.get("_skip"):
        return False
    if not row.get("gbpPrice") or row.get("kind") != "sunglasses":
        return False
    imgs = row.get("localImages") or []
    if not imgs:
        return False
    for p in imgs:
        path = ROOT / "public" / str(p).lstrip("/")
        if path.is_file() and path.stat().st_size > 2048:
            return True
    return False


def write_raw(
    products: list[dict],
    skipped: list[dict],
    failed: list[dict],
) -> None:
    by_id = {p["sku"].upper(): p for p in products if p.get("sku")}
    products = sorted(by_id.values(), key=lambda p: p["sku"])
    leaf_counts = Counter(p.get("leaf") or LEAF_ID for p in products)
    payload = {
        "scrapedAt": datetime.now(timezone.utc).isoformat(),
        "hub": HUB,
        "note": (
            "Chanel GB eyewear hub — Sunglasses + Optical + Blue Light Glasses "
            "under Accessories→샤넬→선글라스; existing SKUs kept, new only scraped."
        ),
        "leaves": [
            {
                "id": LEAF_ID,
                "label": "Sunglasses",
                "labelKo": "선글라스",
                "url": f"{BASE}/gb/eyewear/sunglasses/c/2x1x1/",
            }
        ],
        "leafCounts": dict(leaf_counts),
        "skipped": skipped,
        "failed": failed,
        "products": products,
    }
    OUT_RAW.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    log(f"wrote {len(products)} sunglasses → {OUT_RAW}")
    log(f"leafCounts={dict(leaf_counts)} skipped={len(skipped)} failed={len(failed)}")


def main() -> int:
    IMG_ROOT.mkdir(parents=True, exist_ok=True)
    OUT_RAW.parent.mkdir(parents=True, exist_ok=True)

    _rtw.HUB = HUB
    _rtw.PROBE_SKU_URL = (
        "https://www.chanel.com/gb/eyewear/p/A40888X09955L439559KUNI/"
        "pilot-sunglasses/"
    )
    _rtw.IMPERSONATES = ("safari18_0_ios",)
    _rtw.SEED_PROXIES = []

    _orig_probe = _rtw.ChanelClient.probe_direct
    _skip_once = {"v": True}

    def _probe(self) -> bool:
        if _skip_once["v"]:
            _skip_once["v"] = False
            log("skip init proxy hunt — eyewear uses CN/COM dual fetch")
            return True
        return _orig_probe(self)

    def _no_proxy(self) -> None:
        log("skip public-proxy hunt")

    _rtw.ChanelClient.probe_direct = _probe
    _rtw.ChanelClient.ensure_proxy = _no_proxy
    _rtw.ChanelClient.rotate_proxy = lambda self, mark_dead=True: self.clear_proxy()

    client = ChanelClient()

    existing = load_existing_products()
    log(f"existing sunglasses in raw: {len(existing)}")

    # Sitemap is the authoritative full eyewear list (stable full SKUs).
    # PLP HTML sometimes truncates SKUs mid-token — do not use for identity.
    sku_urls = discover_sitemap_eyewear_skus(client)
    plp_urls = discover_plp_skus(client)
    log(f"PLP SKUs seen={len(plp_urls)} (informative only; sitemap drives scrape)")
    # If a sitemap SKU lacks a slug URL somehow, keep generic.
    for sku in list(sku_urls):
        if not sku_urls[sku].rstrip("/").count("/") >= 6:
            sku_urls[sku] = pdp_url(sku)

    if not sku_urls and not existing:
        log("ERROR: no eyewear SKUs discovered")
        return 1

    cache = load_cache()
    # Drop truncated cache keys that are not full eyewear SKUs on the hub.
    for bad in [k for k in list(cache) if k.upper() not in sku_urls and k.upper() not in existing]:
        log(f"drop stale/truncated cache key {bad}")
        cache.pop(bad, None)
    products: list[dict] = []
    skipped: list[dict] = []
    failed: list[dict] = []

    # Seed with complete existing products (dedupe).
    kept = 0
    for sku, row in existing.items():
        row = dict(row)
        row["leaf"] = LEAF_ID
        row["leaves"] = [LEAF_ID]
        row["collections"] = list(PARENT_COLS)
        row["kind"] = "sunglasses"
        if is_complete(row):
            products.append(row)
            cache[sku] = row
            kept += 1
        elif (
            isinstance(cache.get(sku), dict)
            and is_complete(cache[sku])
        ):
            products.append(cache[sku])
            kept += 1
    log(f"kept complete existing: {kept}")

    have = {p["sku"].upper() for p in products}
    todo = sorted(
        (sku, url) for sku, url in sku_urls.items() if sku.upper() not in have
    )
    log(f"new eyewear SKUs to scrape: {len(todo)} (hub total {len(sku_urls)})")

    consecutive_blocks = 0
    i = 0
    while i < len(todo):
        sku, url = todo[i]
        i += 1

        cached = cache.get(sku)
        if isinstance(cached, dict) and is_complete(cached):
            cached["leaf"] = LEAF_ID
            cached["leaves"] = [LEAF_ID]
            cached["collections"] = list(PARENT_COLS)
            products.append(cached)
            continue

        status, html = fetch_pdp_html(client, url)
        if is_challenge(html, status) or len(html) < 8000:
            consecutive_blocks += 1
            log(
                f"[{i}/{len(todo)}] blocked {sku} "
                f"(streak={consecutive_blocks})"
            )
            time.sleep(HARD_BLOCK_SLEEP)
            if consecutive_blocks >= 5:
                log(
                    f"block streak={consecutive_blocks} — writing partial "
                    f"({len(products)} products)"
                )
                failed.append(
                    {"sku": sku, "url": url, "status": status, "reason": "akamai"}
                )
                break
            i -= 1
            continue

        consecutive_blocks = 0
        parsed = parse_eyewear_pdp(html, url, sku_hint=sku)
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

        # Canonicalize to discovery SKU (URL) so we don't duplicate colour suffixes.
        parsed["sku"] = sku
        parsed["id"] = sku
        parsed["productCode"] = sku
        parsed["leaf"] = LEAF_ID
        parsed["leaves"] = [LEAF_ID]
        parsed["collections"] = list(PARENT_COLS)

        cache[sku] = parsed
        save_cache(cache)
        parsed = enrich_images(client, parsed)
        cache[sku] = parsed
        products.append(parsed)
        log(
            f"[{i}/{len(todo)}] OK {sku} £{parsed['gbpPrice']} "
            f"imgs={len(parsed.get('localImages') or [])} "
            f"title={parsed.get('title')!r}"
        )
        save_cache(cache)
        time.sleep(PDP_PAUSE)

    # Merge any leftover complete cache rows for SKUs still on hub.
    by_id = {p["sku"].upper(): p for p in products if p.get("sku")}
    for sku, row in cache.items():
        su = str(sku).upper()
        if su in by_id:
            continue
        if su in sku_urls and is_complete(row):
            row["leaf"] = LEAF_ID
            row["leaves"] = [LEAF_ID]
            row["collections"] = list(PARENT_COLS)
            by_id[su] = row
    products = list(by_id.values())

    save_cache(cache)
    if not products:
        log("ERROR: 0 sunglasses scraped")
        return 1
    write_raw(products, skipped, failed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
