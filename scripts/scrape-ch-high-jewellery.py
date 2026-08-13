#!/usr/bin/env python3
"""Scrape Chanel GB High Jewellery into ch-high-jewellery-catalog-raw.json + images.

Official hub: https://www.chanel.com/gb/high-jewellery/
Shopable creations live on collection pages as /gb/fine-jewellery/p/J*/ PDPs.

Costume jewellery (AB*) stays in scrape-ch-jewellery.py — do not mix.
Fine Jewellery sitemap (COCO CRUSH etc.) is a different section — only SKUs
linked from the high-jewellery hub / collection pages are imported.
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
OUT_RAW = ROOT / "src/data/ch/ch-high-jewellery-catalog-raw.json"
PDP_CACHE = ROOT / "src/data/ch/ch-high-jewellery-pdp-cache.json"
IMG_ROOT = ROOT / "public/products/ch-pdp"

BASE = "https://www.chanel.com"
HUB = f"{BASE}/gb/high-jewellery/"
SITEMAP = f"{BASE}/gb/sitemap.xml"
LEAF_ID = "ch-high-jewellery"
PARENT_COLS = ["chanel", "chanel-accessories", LEAF_ID]

# Official GB high-jewellery collection pages (hub tiles). Editorial-only
# collections (no /p/ PDPs) are crawled but yield zero shopable SKUs.
COLLECTIONS: list[tuple[str, str, str, str]] = [
    (
        "ch-hj-camelia",
        "Camélia",
        "카멜리아",
        f"{BASE}/gb/high-jewellery/camelia-collection/",
    ),
    (
        "ch-hj-comete",
        "Comète",
        "코메뜨",
        f"{BASE}/gb/high-jewellery/comete-collection/",
    ),
    (
        "ch-hj-lion",
        "Lion",
        "라이온",
        f"{BASE}/gb/high-jewellery/lion-collection/",
    ),
    (
        "ch-hj-plume",
        "Plume de CHANEL",
        "플룸 드 샤넬",
        f"{BASE}/gb/high-jewellery/plume-de-chanel-collection/",
    ),
    (
        "ch-hj-ruban",
        "Ruban",
        "루반",
        f"{BASE}/gb/high-jewellery/ruban-collection/",
    ),
    (
        "ch-hj-n5",
        "N°5",
        "N°5",
        f"{BASE}/gb/high-jewellery/signatures-collection-n5/",
    ),
    (
        "ch-hj-n5-haute",
        "N°5 Collection",
        "N°5 컬렉션",
        f"{BASE}/gb/high-jewellery/n5-collection/",
    ),
    (
        "ch-hj-sport",
        "Sport",
        "스포츠",
        f"{BASE}/gb/high-jewellery/sport-collection/",
    ),
    (
        "ch-hj-tweed",
        "Tweed",
        "트위드",
        f"{BASE}/gb/high-jewellery/tweed-collection/",
    ),
    (
        "ch-hj-1932",
        "1932 Allure Céleste",
        "1932 알뤼르 셀레스트",
        f"{BASE}/gb/high-jewellery/1932-collection-allure-celeste-necklace/",
    ),
    (
        "ch-hj-bijoux-de-diamants",
        "Bijoux de Diamants",
        "비주 드 디아망",
        f"{BASE}/gb/high-jewellery/bijoux-de-diamants/",
    ),
    (
        "ch-hj-reach-for-the-stars",
        "Reach for the Stars",
        "리치 포 더 스타즈",
        f"{BASE}/gb/high-jewellery/collection-reach-for-the-stars/",
    ),
]

COL_META = {
    cid: {"label": en, "labelKo": ko, "url": url} for cid, en, ko, url in COLLECTIONS
}
COL_BY_SLUG = {
    url.rstrip("/").rsplit("/", 1)[-1]: cid for cid, _en, _ko, url in COLLECTIONS
}

PDP_PAUSE = 1.2
HARD_BLOCK_SLEEP = 12.0
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
availability_map = _rtw.availability_map
wait_for_pdp_access = _rtw.wait_for_pdp_access
log = _rtw.log


def is_high_jewellery_sku(sku: str) -> bool:
    return bool(SKU_RE.fullmatch((sku or "").upper()))


def order_hj_images(images: list[dict]) -> list[str]:
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


order_images = order_hj_images


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
        if is_high_jewellery_sku(sku):
            found.setdefault(sku, pdp_url(sku, slug))
    return found


def walk_pdps(obj, out: dict[str, str]) -> None:
    if isinstance(obj, dict):
        sku = str(obj.get("sku") or obj.get("id") or "").strip()
        url = str(
            obj.get("url") or obj.get("pdpUrl") or obj.get("path") or obj.get("href") or ""
        )
        if is_high_jewellery_sku(sku):
            sku_u = sku.upper()
            if "/fine-jewellery/p/" in url:
                out.setdefault(
                    sku_u,
                    BASE + url if url.startswith("/") else url,
                )
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


def collection_id_from_url(url: str) -> str | None:
    slug = (url or "").rstrip("/").rsplit("/", 1)[-1].lower()
    return COL_BY_SLUG.get(slug)


def discover_collection_urls(html: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    pats = [
        r"https://www\.chanel\.com/gb/high-jewellery/([a-z0-9\-]+)/?",
        r"/gb/high-jewellery/([a-z0-9\-]+)/?",
    ]
    skip = {"savoir-faire", "high-jewellery"}
    for pat in pats:
        for m in re.finditer(pat, html or "", flags=re.I):
            slug = m.group(1).lower()
            if slug in skip:
                continue
            url = f"{BASE}/gb/high-jewellery/{slug}/"
            if url not in seen:
                seen.add(url)
                found.append(url)
    # Keep known official collection order first.
    ordered: list[str] = []
    known = {url for *_rest, url in COLLECTIONS}
    for url in [u for *_r, u in COLLECTIONS] + found:
        if url not in ordered:
            ordered.append(url)
    return ordered


def fetch_page(client: ChanelClient, url: str, referer: str = HUB) -> tuple[int, str]:
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
        # Editorial collection pages are large but have no /p/ PDP links.
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
        time.sleep(1.5)
        if not client._proxy:
            client.ensure_proxy()
        else:
            client.soft_refresh()
            client.warm()
    return last_status, last_text


def _label_is_rings(label: str) -> bool:
    return bool(re.search(r"\brings?\b", label or "", flags=re.I))


def shape_from_product(prod: dict) -> str:
    """Earrings / necklaces / bracelets / brooches / rings — size-chart only."""
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
    if "earring" in text:
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


def _hj_image_urls(html: str, sku: str) -> list[str]:
    sku_l = sku.lower()
    files: list[str] = []
    seen: set[str] = set()
    for m in re.finditer(r"https://www\.chanel\.com/images/[^\"\s>]+", html or ""):
        u = m.group(0).rstrip("\\").split("?")[0]
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
    urls: list[str] = []
    for fn in files[:12]:
        urls.append(
            "https://www.chanel.com/images/t_one/q_auto:good,f_auto,fl_lossy,dpr_1.1/"
            f"w_1240/{fn}"
        )
    return urls


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


def parse_hj_pdp(
    html: str, url: str, collection_ids: set[str]
) -> dict | None:
    """Fine jewellery PDPs are Hybris (JSON-LD), not fashion Next.js."""
    ld_list = _ld_products(html)
    ld = ld_list[0] if ld_list else {}
    dl = _datalayer_product(html)

    sku = str(ld.get("sku") or dl.get("id") or "").strip().upper()
    if not sku:
        m = re.search(r"/fine-jewellery/p/(J[0-9]+)/", url, flags=re.I)
        sku = (m.group(1) if m else "").upper()
    if not sku or not is_high_jewellery_sku(sku):
        # Fashion Next.js fallback (should not hit for high jewellery).
        nd = extract_next_data(html)
        if nd:
            data = (nd.get("props") or {}).get("pageProps", {}).get("data") or {}
            prod = data.get("product") if isinstance(data, dict) else None
            if isinstance(prod, dict):
                sku = str(prod.get("sku") or prod.get("id") or "").strip()
                if sku and is_high_jewellery_sku(sku):
                    gbp = parse_gbp(prod.get("price"))
                    if gbp is None or gbp <= 0:
                        return {
                            "_skip": True,
                            "sku": sku,
                            "reason": f"bad price {prod.get('price')!r}",
                            "url": url,
                        }
                    details = (
                        prod.get("details") if isinstance(prod.get("details"), dict) else {}
                    )
                    return {
                        "id": sku,
                        "productCode": sku,
                        "sku": sku,
                        "title": prod.get("title") or "",
                        "priceLabel": prod.get("price"),
                        "gbpPrice": gbp,
                        "categoryLabel": prod.get("categoryLabel"),
                        "collection": prod.get("collection"),
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
                        "imageMeta": [],
                        "sizes": [
                            {
                                "id": sku,
                                "size": "UNI",
                                "orliSize": "UNI",
                                "sku": sku,
                                "inStock": True,
                                "sellableOnline": True,
                            }
                        ],
                        "availabilityStatus": "IN_STOCK",
                        "inStock": True,
                        "new": bool(prod.get("new")),
                        "collections": sorted(set([*PARENT_COLS, *collection_ids])),
                        "leaf": LEAF_ID,
                        "leaves": [LEAF_ID],
                        "hjCollections": sorted(collection_ids),
                        "shape": shape_from_product(prod),
                        "kind": "high-jewellery",
                    }
        return None

    offers = ld.get("offers") if isinstance(ld.get("offers"), dict) else {}
    gbp = parse_gbp(offers.get("price") or dl.get("price") or ld.get("price"))
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

    images = _hj_image_urls(html, sku)
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
    cols = sorted(set([*PARENT_COLS, *collection_ids]))

    return {
        "id": sku,
        "productCode": sku,
        "sku": sku,
        "title": title,
        "priceLabel": price_label,
        "gbpPrice": gbp,
        "categoryLabel": sub_cat or "High Jewellery",
        "collection": collection_name.title() if collection_name else None,
        "collectionCode": None,
        "url": url,
        "hierarchy": [
            {"label": "Fine Jewellery", "url": "/gb/fine-jewellery/"},
            {"label": sub_cat or "High Jewellery", "url": ""},
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
        "hjCollections": sorted(collection_ids),
        "shape": shape,
        "kind": "high-jewellery",
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


def discover_hub_skus(client: ChanelClient) -> tuple[dict[str, str], dict[str, set[str]]]:
    sku_urls: dict[str, str] = {}
    sku_cols: dict[str, set[str]] = defaultdict(set)

    log("discovering high-jewellery hub + collections…")
    status, hub_html = fetch_page(client, HUB, referer=f"{BASE}/gb/")
    if status != 200 or len(hub_html) < 5000:
        log(f"  hub blocked status={status} len={len(hub_html)}")
        status, hub_html = client.get_html(HUB, referer=f"{BASE}/gb/", max_attempts=3)

    for sku, url in extract_pdps_from_html(hub_html).items():
        sku_urls.setdefault(sku, url)
    nd = extract_next_data(hub_html)
    if nd:
        walk_pdps(nd, sku_urls)

    col_urls = discover_collection_urls(hub_html)
    if not col_urls:
        col_urls = [url for *_r, url in COLLECTIONS]
    log(f"  collection pages: {len(col_urls)}")

    for url in col_urls:
        cid = collection_id_from_url(url)
        st, html = fetch_page(client, url, referer=HUB)
        if st != 200 or len(html) < 5000:
            log(f"  COL blocked {url} status={st} len={len(html)}")
            continue
        found = extract_pdps_from_html(html)
        nd = extract_next_data(html)
        if nd:
            walk_pdps(nd, found)
        log(f"  COL {url.split('/')[-2]} → {len(found)} SKUs")
        for sku, pdp in found.items():
            sku_urls.setdefault(sku, pdp)
            if cid:
                sku_cols[sku].add(cid)
        time.sleep(0.35)

    log(f"unique high-jewellery SKUs: {len(sku_urls)}")
    return sku_urls, sku_cols


def main() -> int:
    IMG_ROOT.mkdir(parents=True, exist_ok=True)
    OUT_RAW.parent.mkdir(parents=True, exist_ok=True)

    _rtw.HUB = HUB
    _rtw.PROBE_SKU_URL = (
        "https://www.chanel.com/gb/fine-jewellery/p/J12778/bouton-de-camelia-supple-choker/"
    )
    _rtw.IMPERSONATES = ("safari18_0_ios",)

    client = ChanelClient()
    if not client._proxy:
        # Fine-jewellery PDPs 403 after hub crawling — keep a proxy ready.
        client.ensure_proxy()
        client.warm()

    sku_urls, sku_cols = discover_hub_skus(client)
    if not sku_urls:
        log("ERROR: no high-jewellery SKUs from hub/collections")
        return 1

    todo = sorted(sku_urls.items())
    log(f"unique high-jewellery SKUs to scrape: {len(todo)}")

    cache = load_cache()
    products: list[dict] = []
    skipped: list[dict] = []
    failed: list[dict] = []
    leaf_counts: Counter[str] = Counter()
    col_counts: Counter[str] = Counter()

    if not wait_for_pdp_access(client):
        log("ERROR: PDP access never recovered — aborting")
        return 1

    consecutive_blocks = 0
    i = 0
    while i < len(todo):
        sku, url = todo[i]
        i += 1
        forced_cols = set(sku_cols.get(sku) or [])

        cached = cache.get(sku)
        if (
            isinstance(cached, dict)
            and cached.get("gbpPrice")
            and cached.get("kind") == "high-jewellery"
            and not cached.get("_skip")
        ):
            cached["leaf"] = LEAF_ID
            cached["leaves"] = [LEAF_ID]
            cached["hjCollections"] = sorted(forced_cols or cached.get("hjCollections") or [])
            cached["collections"] = sorted(
                set([*PARENT_COLS, *(cached.get("hjCollections") or [])])
            )
            if not cached.get("localImages"):
                cached = enrich_images(client, cached)
            cache[sku] = cached
            save_cache(cache)
            products.append(cached)
            leaf_counts[LEAF_ID] += 1
            for c in cached.get("hjCollections") or []:
                col_counts[c] += 1
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
        parsed = parse_hj_pdp(html, url, forced_cols)
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
        for c in parsed.get("hjCollections") or []:
            col_counts[c] += 1
        log(
            f"[{i}/{len(todo)}] OK {sku} {parsed.get('shape')} "
            f"£{parsed['gbpPrice']} sizes={len(parsed.get('sizes') or [])} "
            f"imgs={len(parsed.get('localImages') or [])}"
        )
        save_cache(cache)
        time.sleep(PDP_PAUSE)

    save_cache(cache)

    by_id: dict[str, dict] = {}
    for p in products:
        by_id[p["sku"]] = p

    if not by_id:
        for sku, cached in cache.items():
            if (
                isinstance(cached, dict)
                and cached.get("kind") == "high-jewellery"
                and cached.get("gbpPrice")
                and not cached.get("_skip")
            ):
                by_id[sku] = cached
                leaf_counts[LEAF_ID] += 1
        if by_id:
            log(f"empty scrape — recovered {len(by_id)} high-jewellery from PDP cache")

    products = sorted(by_id.values(), key=lambda p: p["sku"])

    collections_meta = {}
    for cid, meta in COL_META.items():
        n = sum(1 for p in products if cid in (p.get("hjCollections") or []))
        collections_meta[cid] = {**meta, "count": n}

    payload = {
        "scrapedAt": datetime.now(timezone.utc).isoformat(),
        "source": HUB,
        "note": (
            "Chanel GB High Jewellery from official hub collection pages; "
            "shopable PDPs under /gb/fine-jewellery/p/J*."
        ),
        "collections": collections_meta,
        "count": len(products),
        "skippedCount": len(skipped),
        "failedCount": len(failed),
        "leafCounts": dict(leaf_counts),
        "collectionCounts": dict(col_counts),
        "products": products,
        "skipped": skipped[:80],
        "failed": failed[:50],
    }
    if not products and OUT_RAW.exists():
        log(f"ERROR: 0 high-jewellery scraped — leaving existing raw untouched ({OUT_RAW})")
        return 1
    OUT_RAW.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    log(f"Wrote {len(products)} high-jewellery → {OUT_RAW}")
    log(f"leafCounts={dict(leaf_counts)} collectionCounts={dict(col_counts)}")
    return 0 if products else 1


if __name__ == "__main__":
    raise SystemExit(main())
