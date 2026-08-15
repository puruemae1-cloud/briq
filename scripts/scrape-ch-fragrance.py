#!/usr/bin/env python3
"""Scrape Chanel GB fragrance into ch-fragrance-catalog-raw.json + images.

Official hub: https://www.chanel.com/gb/fragrance/
Shopable PLPs (Women / Men / Les Exclusifs / Les Eaux + sitemap PDPs).

All land under Accessories → 샤넬 → 향수 (ch-fragrance).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from ch_hybris_details import (  # noqa: E402
    enrich_from_html,
    extract_image_urls,
    parse_editorial,
    parse_title_parts,
)

OUT_RAW = ROOT / "src/data/ch/ch-fragrance-catalog-raw.json"
PDP_CACHE = ROOT / "src/data/ch/ch-fragrance-pdp-cache.json"
IMG_ROOT = ROOT / "public/products/ch-pdp"

BASE = "https://www.chanel.com"
HUB = f"{BASE}/gb/fragrance/"
SITEMAP = f"{BASE}/gb/sitemap.xml"

LEAF_ID = "ch-fragrance"
PARENT_COLS = ["chanel", "chanel-accessories", LEAF_ID]

PLPS: list[tuple[str, str, str]] = [
    ("women", "Women", f"{BASE}/gb/fragrance/women/c/7x1x1/"),
    ("men", "Men", f"{BASE}/gb/fragrance/men/c/7x1x2/"),
    (
        "les-exclusifs",
        "Les Exclusifs de CHANEL",
        f"{BASE}/gb/fragrance/les-exclusifs-de-chanel/c/7x1x8/",
    ),
    (
        "les-eaux",
        "Les Eaux de CHANEL",
        f"{BASE}/gb/fragrance/les-eaux-de-chanel/",
    ),
]

PDP_PAUSE = 0.35
HARD_BLOCK_SLEEP = 3.0
MAX_PLP_PAGES = 25
PDP_RE = re.compile(
    r"/gb/fragrance/p/([A-Z0-9]{4,12})/([^/\"'?\s<>]+)",
    flags=re.I,
)
SKU_RE = re.compile(r"^[A-Z0-9]{4,12}$", flags=re.I)

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
log = _rtw.log


def is_fragrance_sku(sku: str) -> bool:
    s = (sku or "").upper()
    if not SKU_RE.fullmatch(s):
        return False
    # Drop fashion / jewellery / watch / eyewear codes.
    if re.match(r"^(A\d|AB|AP|G\d|H\d|J\d|P\d{2}[A-Z])", s):
        if re.fullmatch(r"\d{5,8}", s):
            return True
        return False
    return bool(re.fullmatch(r"\d{5,8}", s) or re.fullmatch(r"[A-Z]?\d{5,8}", s))


def is_gift_or_skip_url(url: str, slug: str = "") -> bool:
    blob = f"{url} {slug}".lower()
    return any(
        x in blob
        for x in (
            "e-gift-card",
            "gift-card",
            "egift",
            "virtual-gift",
        )
    )


def pdp_url(sku: str, slug: str = "") -> str:
    slug = (slug or "").strip("/") or "product"
    return f"{BASE}/gb/fragrance/p/{sku.upper()}/{slug}/"


def to_cn_url(url: str) -> str:
    return (url or "").replace("://www.chanel.com/", "://www.chanel.cn/")


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
    urls = extract_image_urls(html, sku, limit=16)
    if urls:
        return urls
    sku_l = sku.lower()
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
        if sku_l not in fl:
            continue
        if fl in seen:
            continue
        seen.add(fl)
        files.append(fn)

    def rank(fn: str) -> tuple[int, str]:
        f = fn.lower()
        if "packshot" in f or "still-life" in f or "product" in f:
            return (0, f)
        if "fsh-" in f:
            return (1, f)
        return (2, f)

    files.sort(key=rank)
    return [
        "https://www.chanel.com/images/t_one/q_auto:good,f_auto,fl_lossy,dpr_1.1/"
        f"w_1240/{fn}"
        for fn in files[:12]
    ]


def parse_next_fragrance(html: str, url: str, sku_hint: str) -> dict | None:
    nd = extract_next_data(html)
    if not nd:
        return None
    data = (nd.get("props") or {}).get("pageProps", {}).get("data") or {}
    prod = data.get("product")
    if not isinstance(prod, dict):
        return None

    sku = str(prod.get("sku") or prod.get("id") or sku_hint or "").strip().upper()
    if not sku or not is_fragrance_sku(sku):
        return {
            "_skip": True,
            "reason": f"not-fragrance-sku:{sku}",
            "sku": sku,
            "url": url,
            "kind": "fragrance",
        }

    gbp = parse_gbp(prod.get("price"))
    if gbp is None or gbp <= 0:
        return {
            "_skip": True,
            "sku": sku,
            "reason": f"bad price {prod.get('price')!r}",
            "url": url,
            "kind": "fragrance",
        }

    details = prod.get("details") if isinstance(prod.get("details"), dict) else {}
    imgs = prod.get("images") if isinstance(prod.get("images"), list) else []
    image_urls = []
    seen: set[str] = set()
    for im in imgs:
        if not isinstance(im, dict):
            continue
        src = normalize_img_url(im.get("source") or im.get("url") or "")
        if src and src not in seen:
            seen.add(src)
            image_urls.append(src)

    return {
        "id": sku,
        "productCode": sku,
        "sku": sku,
        "title": prod.get("title") or "",
        "titleShort": prod.get("title") or "",
        "subtitle": (details.get("subtitle") if isinstance(details, dict) else None),
        "priceLabel": prod.get("price"),
        "gbpPrice": gbp,
        "categoryLabel": prod.get("categoryLabel") or "Fragrance",
        "collection": prod.get("collection"),
        "collectionCode": prod.get("collectionCode"),
        "url": url,
        "hierarchy": prod.get("hierarchy") or [],
        "details": {
            "color": details.get("color"),
            "description": details.get("description"),
            "fabrics": details.get("fabrics"),
            "reference": details.get("reference") or sku,
            "dimensions": details.get("dimensions"),
            "volume": details.get("volume") or details.get("size"),
        },
        "images": image_urls,
        "sizes": [{"size": "UNI", "orliSize": "UNI", "sku": sku, "inStock": True}],
        "inStock": True,
        "new": bool(prod.get("new")),
        "collections": list(PARENT_COLS),
        "leaf": LEAF_ID,
        "leaves": [LEAF_ID],
        "kind": "fragrance",
    }


def parse_hybris_fragrance(html: str, url: str, sku_hint: str) -> dict | None:
    ld_list = _ld_products(html)
    ld = ld_list[0] if ld_list else {}
    sku = (sku_hint or "").upper()
    if not sku:
        m = re.search(r"/fragrance/p/([A-Z0-9]{4,12})/", url, flags=re.I)
        sku = (m.group(1) if m else "").upper()
    if not sku or not is_fragrance_sku(sku):
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
            "kind": "fragrance",
        }

    titles = parse_title_parts(html)
    title = titles.get("title") or str(ld.get("name") or "").strip()
    subtitle = titles.get("subtitle") or ""
    color = titles.get("color") or str(ld.get("color") or "").strip()
    desc = parse_editorial(html) or str(ld.get("description") or "").strip()
    images = _hybris_image_urls(html, sku)
    if not images and ld.get("image"):
        images = [
            str(ld.get("image")).replace("www.chanel.cn", "www.chanel.com")
        ]

    extra = enrich_from_html(html, sku)
    details = extra.get("details") if isinstance(extra.get("details"), dict) else {}
    if desc and not details.get("editorial"):
        details["editorial"] = desc
    if subtitle:
        details["subtitle"] = subtitle
    if color:
        details.setdefault("color", color)
    details.setdefault("reference", sku)
    parts = extra.get("titleParts") if isinstance(extra.get("titleParts"), dict) else {}
    official = extra.get("officialName") or title
    title_short = parts.get("title") or title
    subtitle = parts.get("subtitle") or subtitle
    if official:
        title = official

    slug = ""
    m_slug = re.search(r"/fragrance/p/[^/]+/([^/\"'?]+)", url, flags=re.I)
    if m_slug:
        slug = m_slug.group(1).lower()

    cat = "Fragrance"
    low = f"{title} {slug} {url}".lower()
    if "exclusif" in low:
        cat = "Les Exclusifs de CHANEL"
    elif "eaux-de-chanel" in low or "les-eaux" in low:
        cat = "Les Eaux de CHANEL"

    return {
        "id": sku,
        "productCode": sku,
        "sku": sku,
        "title": title,
        "titleShort": title_short,
        "subtitle": subtitle,
        "priceLabel": f"£{gbp:,.0f}" if gbp >= 1 else str(offers.get("price") or ""),
        "gbpPrice": gbp,
        "categoryLabel": cat,
        "collection": None,
        "collectionCode": None,
        "url": url if url.startswith("http") else pdp_url(sku, slug),
        "hierarchy": [
            {"label": "Fragrance", "url": "/gb/fragrance/"},
            {"label": cat, "url": ""},
        ],
        "details": details,
        "images": extra.get("images") or images,
        "sizes": [{"size": "UNI", "orliSize": "UNI", "sku": sku, "inStock": True}],
        "inStock": True,
        "new": False,
        "collections": list(PARENT_COLS),
        "leaf": LEAF_ID,
        "leaves": [LEAF_ID],
        "kind": "fragrance",
    }


def parse_fragrance_pdp(html: str, url: str, sku_hint: str = "") -> dict | None:
    if "__NEXT_DATA__" in (html or ""):
        parsed = parse_next_fragrance(html, url, sku_hint)
        if parsed:
            return parsed
    return parse_hybris_fragrance(html, url, sku_hint)


def fetch_pdp_html(client: ChanelClient, url: str) -> tuple[int, str]:
    """Fragrance GB PDPs are Akamai-blocked; chanel.cn /gb/ is the working Hybris mirror."""
    cn = to_cn_url(url)
    try:
        with _rtw._session_lock:
            r = client.session.get(
                cn,
                impersonate=client.impersonate,
                timeout=20,
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
    return 0, ""


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


def extract_skus_from_html(html: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for m in PDP_RE.finditer(html or ""):
        sku, slug = m.group(1).upper(), m.group(2)
        if is_fragrance_sku(sku) and not is_gift_or_skip_url(pdp_url(sku, slug), slug):
            found.setdefault(sku, pdp_url(sku, slug))
    return found


def discover_plp_skus(client: ChanelClient) -> dict[str, str]:
    found: dict[str, str] = {}
    extra_hub: list[str] = []
    st, hub_html = fetch_plp_html(client, HUB)
    if st == 200:
        found.update(extract_skus_from_html(hub_html))
        for m in re.finditer(
            r"https://www\.chanel\.com/gb/fragrance/[^\"'\s<>]+", hub_html or ""
        ):
            u = m.group(0).split("?")[0]
            if "/p/" in u:
                continue
            if "/c/" not in u and not re.search(
                r"/fragrance/(?:les-eaux-de-chanel|les-exclusifs-de-chanel)/?$",
                u,
                flags=re.I,
            ):
                continue
            extra_hub.append(u)
    urls = [u for _, _, u in PLPS] + extra_hub
    seen_pages: set[str] = set()
    for url in urls:
        url = url.rstrip("/") + "/"
        if url in seen_pages:
            continue
        seen_pages.add(url)
        log(f"PLP {url}")
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
            new_n = sum(1 for sku in batch if sku not in found)
            found.update(batch)
            leaf_n += len(batch)
            log(
                f"  {page} → +{len(batch)} new={new_n} "
                f"(leaf ~{leaf_n} total {len(found)})"
            )
            if page != url and new_n == 0:
                break
            if page != url and new_n < 3:
                break
            time.sleep(0.25)
    log(f"PLP fragrance SKUs: {len(found)}")
    return found


def discover_sitemap_fragrance_skus(client: ChanelClient) -> dict[str, str]:
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
        if not is_fragrance_sku(sku):
            continue
        if is_gift_or_skip_url(pdp_url(sku, slug), slug):
            continue
        by_sku.setdefault(sku, pdp_url(sku, slug))
    log(f"sitemap fragrance SKUs: {len(by_sku)}")
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
    if not row.get("gbpPrice") or row.get("kind") != "fragrance":
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
            "Chanel GB fragrance hub — Women + Men + Les Exclusifs + Les Eaux "
            "under Accessories→샤넬→향수."
        ),
        "leaves": [
            {
                "id": LEAF_ID,
                "label": "Fragrance",
                "labelKo": "향수",
                "url": HUB,
            }
        ],
        "leafCounts": dict(leaf_counts),
        "skipped": skipped,
        "failed": failed,
        "products": products,
    }
    OUT_RAW.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    log(f"wrote {len(products)} fragrance → {OUT_RAW}")
    log(f"leafCounts={dict(leaf_counts)} skipped={len(skipped)} failed={len(failed)}")


def bind_client() -> ChanelClient:
    _rtw.HUB = HUB
    _rtw.PROBE_SKU_URL = (
        "https://www.chanel.com/gb/fragrance/p/113530/n5-eau-de-parfum-spray/"
    )
    _rtw.IMPERSONATES = ("safari18_0_ios",)
    _rtw.SEED_PROXIES = []

    _orig_probe = _rtw.ChanelClient.probe_direct
    _skip_once = {"v": True}

    def _probe(self) -> bool:
        if _skip_once["v"]:
            _skip_once["v"] = False
            log("skip init proxy hunt — fragrance uses CN/COM dual fetch")
            return True
        return _orig_probe(self)

    def _no_proxy(self) -> None:
        log("skip public-proxy hunt")

    _rtw.ChanelClient.probe_direct = _probe
    _rtw.ChanelClient.ensure_proxy = _no_proxy
    _rtw.ChanelClient.rotate_proxy = lambda self, mark_dead=True: self.clear_proxy()
    return ChanelClient()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--discover-only", action="store_true")
    args = ap.parse_args()

    IMG_ROOT.mkdir(parents=True, exist_ok=True)
    OUT_RAW.parent.mkdir(parents=True, exist_ok=True)

    client = bind_client()
    sku_urls = discover_sitemap_fragrance_skus(client)
    existing_preview = load_existing_products()
    if existing_preview:
        log("resume: skip PLP crawl, sitemap + existing raw")
    else:
        plp_urls = discover_plp_skus(client)
        for sku, url in plp_urls.items():
            sku_urls.setdefault(sku, url)
    log(f"unique fragrance SKUs: {len(sku_urls)}")
    if args.discover_only:
        sample = list(sku_urls.items())[:12]
        for sku, url in sample:
            log(f"  {sku} {url}")
        return 0 if sku_urls else 1

    existing = load_existing_products()
    log(f"existing fragrance in raw: {len(existing)}")
    if not sku_urls and not existing:
        log("ERROR: no fragrance SKUs discovered")
        return 1

    cache = load_cache()
    products: list[dict] = []
    skipped: list[dict] = []
    failed: list[dict] = []

    kept = 0
    seeded = {}
    for sku, row in {**cache, **existing}.items():
        su = str(sku).upper()
        row = dict(row) if isinstance(row, dict) else {}
        row["leaf"] = LEAF_ID
        row["leaves"] = [LEAF_ID]
        row["collections"] = list(PARENT_COLS)
        row["kind"] = "fragrance"
        if not is_complete(row):
            continue
        if su in seeded:
            continue
        seeded[su] = row
        products.append(row)
        cache[su] = row
        kept += 1
    log(f"kept complete existing/cache: {kept}")
    if products:
        write_raw(products, [], [])

    have = {p["sku"].upper() for p in products}
    todo = sorted((sku, url) for sku, url in sku_urls.items() if sku.upper() not in have)
    log(f"new fragrance SKUs to scrape: {len(todo)} (hub total {len(sku_urls)})")

    consecutive_blocks = 0
    sku_tries: dict[str, int] = {}
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
            tries = sku_tries.get(sku, 0) + 1
            sku_tries[sku] = tries
            log(
                f"[{i}/{len(todo)}] blocked {sku} "
                f"(sku_try={tries} streak={consecutive_blocks})"
            )
            time.sleep(HARD_BLOCK_SLEEP)
            if tries < 2 and consecutive_blocks < 12:
                try:
                    client.rotate_impersonate()
                except Exception:
                    pass
                i -= 1
                continue
            failed.append(
                {"sku": sku, "url": url, "status": status, "reason": "akamai"}
            )
            log(f"[{i}/{len(todo)}] skip-blocked {sku} — continue")
            consecutive_blocks = 0
            time.sleep(4.0)
            continue

        consecutive_blocks = 0
        # Related sizes on this PDP should also be scraped.
        related = extract_skus_from_html(html)
        for rsku, rurl in related.items():
            if rsku not in sku_urls:
                sku_urls[rsku] = rurl
                if rsku not in have and all(t[0] != rsku for t in todo):
                    todo.append((rsku, rurl))

        parsed = parse_fragrance_pdp(html, url, sku_hint=sku)
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

        parsed["sku"] = sku
        parsed["id"] = sku
        parsed["productCode"] = sku
        parsed["leaf"] = LEAF_ID
        parsed["leaves"] = [LEAF_ID]
        parsed["collections"] = list(PARENT_COLS)
        parsed["kind"] = "fragrance"

        cache[sku] = parsed
        parsed = enrich_images(client, parsed)
        cache[sku] = parsed
        products.append(parsed)
        log(
            f"[{i}/{len(todo)}] OK {sku} £{parsed['gbpPrice']} "
            f"imgs={len(parsed.get('localImages') or [])} "
            f"title={parsed.get('title')!r}"
        )
        save_cache(cache)
        if len(products) % 15 == 0:
            write_raw(products, skipped, failed)
        time.sleep(PDP_PAUSE)

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
        log("ERROR: 0 fragrance scraped")
        return 1
    write_raw(products, skipped, failed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
