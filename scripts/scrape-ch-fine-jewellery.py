#!/usr/bin/env python3
"""Scrape Chanel GB Fine Jewellery into ch-fine-jewellery-catalog-raw.json + images.

Official hub: https://www.chanel.com/gb/fine-jewellery/
Shopable PDPs: /gb/fine-jewellery/p/J*/

Excludes High Jewellery SKUs already imported via scrape-ch-high-jewellery.py
so High / Fine stay disjoint under Accessories → 샤넬.
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
OUT_RAW = ROOT / "src/data/ch/ch-fine-jewellery-catalog-raw.json"
PDP_CACHE = ROOT / "src/data/ch/ch-fine-jewellery-pdp-cache.json"
HIGH_RAW = ROOT / "src/data/ch/ch-high-jewellery-catalog-raw.json"
IMG_ROOT = ROOT / "public/products/ch-pdp"

BASE = "https://www.chanel.com"
HUB = f"{BASE}/gb/fine-jewellery/"
SITEMAP = f"{BASE}/gb/sitemap.xml"
LEAF_ID = "ch-fine-jewellery"
PARENT_COLS = ["chanel", "chanel-accessories", LEAF_ID]

# Official GB Fine Jewellery product-type + bridal PLPs (see hub nav).
PLPS: list[tuple[str, str, str]] = [
    ("rings", "Rings", f"{BASE}/gb/fine-jewellery/rings/c/3x1x2/"),
    ("necklaces", "Necklaces", f"{BASE}/gb/fine-jewellery/necklaces/c/3x1x1/"),
    ("bracelets", "Bracelets", f"{BASE}/gb/fine-jewellery/bracelets/c/3x1x3/"),
    ("earrings", "Earrings", f"{BASE}/gb/fine-jewellery/earrings/c/3x1x4/"),
    ("brooches", "Brooches", f"{BASE}/gb/fine-jewellery/brooches/c/3x1x5/"),
    (
        "engagement-rings",
        "Engagement Rings",
        f"{BASE}/gb/fine-jewellery/bridal/c/3x1x2x1/engagement-rings/",
    ),
    (
        "wedding-rings",
        "Wedding Rings",
        f"{BASE}/gb/fine-jewellery/bridal/c/3x1x2x2/wedding-rings/",
    ),
    ("new", "New", f"{BASE}/gb/fine-jewellery/new-fine-jewelry/c/3x3x26/"),
    ("collections", "Collections", f"{BASE}/gb/fine-jewellery/collection/c/3x2/"),
]

PDP_PAUSE = 1.0
HARD_BLOCK_SLEEP = 8.0
MAX_PLP_PAGES = 12
PDP_RE = re.compile(
    r"/gb/fine-jewellery/p/(J[0-9]+)/([^/\"'?\s<>]+)",
    flags=re.I,
)
SKU_RE = re.compile(r"^J[0-9]+$", flags=re.I)

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


def is_fine_jewellery_sku(sku: str) -> bool:
    return bool(SKU_RE.fullmatch((sku or "").upper()))


def load_high_jewellery_skus() -> set[str]:
    if not HIGH_RAW.exists():
        return set()
    try:
        rows = json.loads(HIGH_RAW.read_text()).get("products") or []
    except Exception:
        return set()
    return {
        str(p.get("sku") or p.get("id") or "").upper()
        for p in rows
        if isinstance(p, dict) and is_fine_jewellery_sku(str(p.get("sku") or p.get("id") or ""))
    }


def order_fj_images(images: list[dict]) -> list[str]:
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


order_images = order_fj_images


def pdp_url(sku: str, slug: str = "") -> str:
    sku = sku.upper()
    if slug:
        return f"{BASE}/gb/fine-jewellery/p/{sku}/{slug.strip('/')}/"
    return f"{BASE}/gb/fine-jewellery/p/{sku}/"


def extract_pdps_from_html(html: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for m in PDP_RE.finditer(html or ""):
        sku = m.group(1).upper()
        slug = m.group(2)
        if is_fine_jewellery_sku(sku):
            found.setdefault(sku, pdp_url(sku, slug))
    return found


def walk_pdps(obj, out: dict[str, str]) -> None:
    if isinstance(obj, dict):
        sku = str(obj.get("sku") or obj.get("id") or "").strip()
        url = str(
            obj.get("url") or obj.get("pdpUrl") or obj.get("path") or obj.get("href") or ""
        )
        if is_fine_jewellery_sku(sku):
            sku_u = sku.upper()
            if "/fine-jewellery/p/" in url:
                out.setdefault(sku_u, BASE + url if url.startswith("/") else url)
            else:
                m = PDP_RE.search(url)
                if m:
                    out.setdefault(m.group(1).upper(), pdp_url(m.group(1), m.group(2)))
                else:
                    out.setdefault(sku_u, pdp_url(sku_u))
        for v in obj.values():
            walk_pdps(v, out)
    elif isinstance(obj, list):
        for x in obj:
            walk_pdps(x, out)


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
        if last_status == 200 and len(last_text) > 50000:
            return last_status, last_text
        if "__NEXT_DATA__" in last_text and len(last_text) > 20000:
            return last_status, last_text
        if last_status == 200 and "/gb/fine-jewellery/p/" in last_text and len(last_text) > 20000:
            return last_status, last_text
        log(
            f"  soft-block {last_status} on {url} "
            f"(attempt {attempt}, len={len(last_text)})"
        )
        time.sleep(1.2)
        if not client._proxy:
            client.ensure_proxy()
        else:
            client.soft_refresh()
            client.warm()
    return last_status, last_text


def _label_is_rings(label: str) -> bool:
    return bool(re.search(r"\brings?\b", label or "", flags=re.I))


def shape_from_product(prod: dict) -> str:
    blob = " ".join(
        [
            str(prod.get("title") or ""),
            str(prod.get("categoryLabel") or ""),
            str((prod.get("details") or {}).get("description") or "")
            if isinstance(prod.get("details"), dict)
            else "",
        ]
    ).lower()
    url_blob = " ".join(
        str(h.get("url") or "") for h in (prod.get("hierarchy") or []) if isinstance(h, dict)
    ).lower()
    label_blob = " ".join(
        str(h.get("label") or h.get("title") or "")
        for h in (prod.get("hierarchy") or [])
        if isinstance(h, dict)
    ).lower()
    text = f"{blob} {url_blob} {label_blob}"
    if "earring" in text or "earcuff" in text:
        return "earrings"
    if "necklace" in text or "choker" in text:
        return "necklaces"
    if "bracelet" in text or "cuff" in text:
        return "bracelets"
    if "brooch" in text:
        return "brooches"
    if _label_is_rings(text):
        return "rings"
    return "other"


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


def _datalayer_product(html: str) -> dict:
    m = re.search(
        r'"ecommerce"\s*:\s*\{\s*"detail"\s*:\s*\{\s*"products"\s*:\s*(\[.*?\])',
        html or "",
        flags=re.S,
    )
    if not m:
        return {}
    try:
        rows = json.loads(m.group(1))
    except json.JSONDecodeError:
        return {}
    return rows[0] if rows and isinstance(rows[0], dict) else {}


def _fj_image_urls(html: str, sku: str) -> list[str]:
    sku_l = sku.lower()
    files: list[str] = []
    seen: set[str] = set()
    for m in re.finditer(
        r"https://www\.chanel\.(?:com|cn)/images/[^\"\s>]+", html or ""
    ):
        u = m.group(0).rstrip("\\").split("?")[0].replace("www.chanel.cn", "www.chanel.com")
        if sku_l not in u.lower() or not re.search(r"\.(?:jpg|jpeg|png|webp)$", u, re.I):
            continue
        fn = u.rsplit("/", 1)[-1]
        if fn in seen:
            continue
        seen.add(fn)
        files.append(fn)

    def rank(fn: str) -> tuple[int, str]:
        f = fn.lower()
        if "packshot-default" in f:
            return (0, f)
        if "trois-quart" in f or "packshot-face" in f:
            return (1, f)
        if "fermoir" in f or "clasp" in f:
            return (2, f)
        if "packshot-other" in f or "packshot-alternative" in f:
            return (3, f)
        if "portee" in f:
            return (4, f)
        return (5, f)

    files.sort(key=rank)
    return [
        "https://www.chanel.com/images/t_one/q_auto:good,f_auto,fl_lossy,dpr_1.1/"
        f"w_1240/{fn}"
        for fn in files[:12]
    ]


def _hybris_sizes(html: str) -> list[str]:
    sizes: list[str] = []
    seen: set[str] = set()
    for raw in re.findall(
        r'data-size="([^"]+)"|data-orli-size="([^"]+)"',
        html or "",
        flags=re.I,
    ):
        val = next((x for x in raw if x), "").strip()
        if not val or val.upper() in seen:
            continue
        seen.add(val.upper())
        sizes.append(val)
    return sizes


def parse_fj_pdp(html: str, url: str) -> dict | None:
    """Fine jewellery PDPs are Hybris (JSON-LD), not fashion Next.js."""
    ld_list = _ld_products(html)
    ld = ld_list[0] if ld_list else {}
    dl = _datalayer_product(html)

    sku = str(ld.get("sku") or dl.get("id") or "").strip().upper()
    if not sku:
        m = re.search(r"/fine-jewellery/p/(J[0-9]+)/", url, flags=re.I)
        sku = (m.group(1) if m else "").upper()
    if not sku or not is_fine_jewellery_sku(sku):
        return None

    offers = ld.get("offers") if isinstance(ld.get("offers"), dict) else {}
    gbp = parse_gbp(offers.get("price") or dl.get("price") or ld.get("price"))
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
        }

    title = str(ld.get("name") or dl.get("name") or "").strip()
    color = str(ld.get("color") or "").strip()
    material = str(ld.get("material") or "").strip()
    desc = str(ld.get("description") or "").strip()
    sub = str(dl.get("category") or "").strip()
    sub_cat = ""
    m_sub = re.search(r'"sub_category"\s*:\s*"([^"]+)"', html or "")
    if m_sub:
        sub_cat = m_sub.group(1)
    collection_name = str(dl.get("dimension18") or dl.get("dimension19") or "").strip()

    shape = shape_from_product(
        {
            "title": title,
            "categoryLabel": sub_cat or sub,
            "details": {"description": desc},
            "hierarchy": [{"label": sub_cat}],
        }
    )

    images = _fj_image_urls(html, sku)
    if not images and ld.get("image"):
        images = [str(ld.get("image"))]

    avail = str(offers.get("availability") or "")
    in_stock = "OutOfStock" not in avail
    sizes = _hybris_sizes(html) or ["UNI"]
    variants_out = [
        {
            "id": f"{sku}-{sz}" if sz.upper() != "UNI" else sku,
            "size": sz,
            "orliSize": sz,
            "sku": f"{sku}-{sz}" if sz.upper() != "UNI" else sku,
            "inStock": in_stock,
            "sellableOnline": "InStock" in avail,
        }
        for sz in sizes
    ]

    price_label = f"£{gbp:,.0f}" if gbp >= 1 else str(offers.get("price") or "")
    cols = sorted(set(PARENT_COLS))

    return {
        "id": sku,
        "productCode": sku,
        "sku": sku,
        "title": title,
        "priceLabel": price_label,
        "gbpPrice": gbp,
        "categoryLabel": sub_cat or "Fine Jewellery",
        "collection": collection_name.title() if collection_name else None,
        "collectionCode": None,
        "url": url,
        "hierarchy": [
            {"label": "Fine Jewellery", "url": "/gb/fine-jewellery/"},
            {"label": sub_cat or "Fine Jewellery", "url": ""},
        ],
        "details": {
            "color": color,
            "description": desc,
            "fabrics": material,
            "reference": sku,
            "dimensions": None,
        },
        "images": images,
        "imageMeta": [
            {"typology": "PACKSHOT_DEFAULT" if i == 0 else "PACKSHOT_OTHER", "source": src}
            for i, src in enumerate(images)
        ],
        "sizes": variants_out,
        "availabilityStatus": "IN_STOCK" if in_stock else "OUT_OF_STOCK",
        "inStock": in_stock,
        "new": False,
        "collections": cols,
        "leaf": LEAF_ID,
        "leaves": [LEAF_ID],
        "shape": shape,
        "kind": "fine-jewellery",
    }


def to_cn_url(url: str) -> str:
    return (url or "").replace("://www.chanel.com/", "://www.chanel.cn/", 1)


def fetch_pdp_html(client: ChanelClient, url: str) -> tuple[int, str]:
    """Prefer chanel.cn /gb/ mirror (GBP); fall back to www.chanel.com."""
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
            st, text = r.status_code, r.text
        if st == 200 and len(text) > 20000 and (
            "application/ld+json" in text or "£" in text or '"price"' in text
        ):
            return st, text
        log(f"  CN weak {cn} st={st} len={len(text)}")
    except Exception as e:
        log(f"  CN GET error: {e}")
    status, html = client.get_html(url, referer=HUB, max_attempts=1)
    return status, html


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


def discover_sitemap_skus(client: ChanelClient) -> dict[str, str]:
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
        by_sku.setdefault(sku, pdp_url(sku, slug))
    log(f"sitemap fine-jewellery SKUs: {len(by_sku)}")
    return by_sku


def discover_plp_skus(client: ChanelClient) -> dict[str, str]:
    found: dict[str, str] = {}
    jobs = [("hub", "Hub", HUB)] + [(a, b, c) for a, b, c in PLPS]
    for cid, label, url in jobs:
        log(f"PLP {cid} ({label})")
        pages = [url] + [f"{url.rstrip('/')}/page-{n}/" for n in range(2, MAX_PLP_PAGES + 1)]
        for page in pages:
            st, html = fetch_page(client, page, referer=HUB)
            if st == 404:
                break
            if st != 200 or len(html) < 5000:
                if page == url:
                    log(f"  blocked {page} status={st} len={len(html)}")
                break
            batch = extract_pdps_from_html(html)
            nd = extract_next_data(html)
            if nd:
                walk_pdps(nd, batch)
            before = len(found)
            found.update(batch)
            log(f"  {page} → +{len(found) - before} (total {len(found)})")
            if page != url and not batch:
                break
            time.sleep(0.35)
    return found


def write_raw(
    products: list[dict],
    skipped: list[dict],
    failed: list[dict],
    leaf_counts: Counter[str],
) -> None:
    by_id = {p["sku"]: p for p in products if p.get("sku")}
    products = sorted(by_id.values(), key=lambda p: p["sku"])
    payload = {
        "scrapedAt": datetime.now(timezone.utc).isoformat(),
        "hub": HUB,
        "note": (
            "Chanel GB Fine Jewellery from official hub/PLPs + sitemap; "
            "High Jewellery SKUs excluded (kept under ch-high-jewellery)."
        ),
        "leafCounts": dict(leaf_counts),
        "skipped": skipped,
        "failed": failed,
        "products": products,
    }
    OUT_RAW.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    log(f"wrote {len(products)} fine-jewellery → {OUT_RAW}")
    log(f"leafCounts={dict(leaf_counts)} skipped={len(skipped)} failed={len(failed)}")


def main() -> int:
    IMG_ROOT.mkdir(parents=True, exist_ok=True)
    OUT_RAW.parent.mkdir(parents=True, exist_ok=True)

    _rtw.HUB = HUB
    _rtw.PROBE_SKU_URL = (
        "https://www.chanel.com/gb/fine-jewellery/p/J13701/coco-crush-necklace/"
    )
    _rtw.IMPERSONATES = ("safari18_0_ios",)
    _rtw.SEED_PROXIES = []

    # Prefer chanel.cn /gb/ mirror — public proxies burn minutes and still 403.
    _orig_probe = _rtw.ChanelClient.probe_direct
    _skip_once = {"v": True}

    def _probe(self) -> bool:
        if _skip_once["v"]:
            _skip_once["v"] = False
            log("skip init proxy hunt — Fine Jewellery uses chanel.cn /gb/ fallback")
            return True
        return _orig_probe(self)

    def _no_proxy(self) -> None:
        log("skip public-proxy hunt")

    _rtw.ChanelClient.probe_direct = _probe
    _rtw.ChanelClient.ensure_proxy = _no_proxy
    _rtw.ChanelClient.rotate_proxy = lambda self, mark_dead=True: self.clear_proxy()

    high_skus = load_high_jewellery_skus()
    log(f"excluding {len(high_skus)} high-jewellery SKUs from Fine import")

    client = ChanelClient()

    # Prefer sitemap (complete). Skip PLP crawl without a working proxy.
    sku_urls: dict[str, str] = {}
    sku_urls.update(discover_sitemap_skus(client))
    log("sitemap-only discovery (PLP crawl skipped)")

    # Drop High Jewellery duplicates.
    for sku in list(sku_urls):
        if sku in high_skus:
            sku_urls.pop(sku, None)

    if not sku_urls:
        log("ERROR: no fine-jewellery SKUs discovered")
        return 1

    todo = sorted(sku_urls.items())
    log(f"unique fine-jewellery SKUs to scrape: {len(todo)}")

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

        cached = cache.get(sku)
        if (
            isinstance(cached, dict)
            and cached.get("gbpPrice")
            and cached.get("kind") == "fine-jewellery"
            and not cached.get("_skip")
        ):
            cached["leaf"] = LEAF_ID
            cached["leaves"] = [LEAF_ID]
            cached["collections"] = sorted(set(PARENT_COLS))
            if not cached.get("localImages"):
                cached = enrich_images(client, cached)
            cache[sku] = cached
            save_cache(cache)
            products.append(cached)
            leaf_counts[LEAF_ID] += 1
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
                    f"({len(products)} this run)"
                )
                failed.append({"sku": sku, "url": url, "status": status, "reason": "akamai"})
                break
            i -= 1
            continue

        consecutive_blocks = 0
        parsed = parse_fj_pdp(html, url)
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
            f"[{i}/{len(todo)}] OK {sku} £{parsed['gbpPrice']} "
            f"sizes={len(parsed.get('sizes') or [])} "
            f"imgs={len(parsed.get('localImages') or [])}"
        )
        save_cache(cache)
        time.sleep(0.4)

    # Keep previously cached OK products even if this run aborted early.
    by_id = {p["sku"]: p for p in products if p.get("sku")}
    for sku, row in cache.items():
        if (
            isinstance(row, dict)
            and row.get("gbpPrice")
            and row.get("kind") == "fine-jewellery"
            and not row.get("_skip")
            and sku not in high_skus
            and sku not in by_id
        ):
            by_id[sku] = row
    products = list(by_id.values())
    leaf_counts = Counter(p.get("leaf") for p in products if p.get("leaf"))

    save_cache(cache)
    if not products:
        log("ERROR: 0 fine-jewellery scraped")
        return 1
    write_raw(products, skipped, failed, leaf_counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
