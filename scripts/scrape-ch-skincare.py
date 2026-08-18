#!/usr/bin/env python3
"""Scrape Chanel GB skincare into ch-skincare-catalog-raw.json + images.

Official hub: https://www.chanel.com/gb/skincare/
Leaves match shopable product-type /c/ PLPs (6x1x*) — Cleansers, Serums,
Moisturisers, Eye & Lip Care, Body, Masks, Oils, Protection, Toners, Mists.
Collection hubs (6x2x*) are skipped so SKUs are not duplicated.

All land under Accessories → 샤넬 → 스킨케어.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import time
from collections import Counter, defaultdict
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

OUT_RAW = ROOT / "src/data/ch/ch-skincare-catalog-raw.json"
PDP_CACHE = ROOT / "src/data/ch/ch-skincare-pdp-cache.json"
IMG_ROOT = ROOT / "public/products/ch-pdp"

BASE = "https://www.chanel.com"
HUB = f"{BASE}/gb/skincare/"
SITEMAP = f"{BASE}/gb/sitemap.xml"

PARENT_ID = "ch-skincare"
PARENT_COLS = ["chanel", "chanel-accessories", PARENT_ID]

# Official GB product-type PLPs. Korean labels follow chanel.com/kr/skincare.
# Hub "Shop by category" order first, then remaining 6x1x* codes.
# (id, EN, KO, url, group_id) — skincare has no nested children, group = leaf.
LEAVES: list[tuple[str, str, str, str, str]] = [
    (
        "ch-skincare-cleansers",
        "Cleansers & Makeup Removers",
        "클렌저/메이크업 리무버",
        f"{BASE}/gb/skincare/cleansers-makeup-removers/c/6x1x4/",
        "ch-skincare-cleansers",
    ),
    (
        "ch-skincare-serums",
        "Serums & Concentrates",
        "세럼",
        f"{BASE}/gb/skincare/serums-concentrates/c/6x1x3/",
        "ch-skincare-serums",
    ),
    (
        "ch-skincare-moisturisers",
        "Moisturisers",
        "모이스처라이저",
        f"{BASE}/gb/skincare/moisturisers/c/6x1x5/",
        "ch-skincare-moisturisers",
    ),
    (
        "ch-skincare-eyes-lips",
        "Eye & Lip Care",
        "아이 & 립 케어",
        f"{BASE}/gb/skincare/eyes-lips/c/6x1x2/",
        "ch-skincare-eyes-lips",
    ),
    (
        "ch-skincare-body",
        "Body Care",
        "바디/핸드 케어",
        f"{BASE}/gb/skincare/body-care/c/6x1x1/",
        "ch-skincare-body",
    ),
    (
        "ch-skincare-masks",
        "Masks & Scrubs",
        "마스크 & 스크럽",
        f"{BASE}/gb/skincare/masks-scrubs/c/6x1x7/",
        "ch-skincare-masks",
    ),
    (
        "ch-skincare-oils",
        "Oils",
        "오일",
        f"{BASE}/gb/skincare/oils/c/6x1x8/",
        "ch-skincare-oils",
    ),
    (
        "ch-skincare-protection",
        "Protection",
        "선 프로텍션",
        f"{BASE}/gb/skincare/protection/c/6x1x6/",
        "ch-skincare-protection",
    ),
    (
        "ch-skincare-toners",
        "Toners & Lotions",
        "토너/로션",
        f"{BASE}/gb/skincare/toners-lotions/c/6x1x9/",
        "ch-skincare-toners",
    ),
    (
        "ch-skincare-mists",
        "Mists",
        "미스트",
        f"{BASE}/gb/skincare/mists/c/6x1x10/",
        "ch-skincare-mists",
    ),
]

LEAF_IDS = [c for c, *_ in LEAVES]
LEAF_META = {
    cid: {"label": en, "labelKo": ko, "url": url, "group": group}
    for cid, en, ko, url, group in LEAVES
}
GROUP_IDS: list[str] = []
# Hub shop-by-category order (already the LEAVES order).
PRIMARY_ORDER = list(LEAF_IDS)
LEAF_BY_CAT_CODE: dict[str, tuple[str, str]] = {}
for _cid, _en, _ko, _url, _group in LEAVES:
    _m = re.search(r"/c/([^/]+)/", _url)
    if _m:
        LEAF_BY_CAT_CODE[_m.group(1).lower()] = (_cid, _group)

PDP_PAUSE = 0.2
HARD_BLOCK_SLEEP = 3.0
MAX_PLP_PAGES = 20
PDP_RE = re.compile(
    r"/gb/skincare/p/([A-Z0-9]{4,12})/([^/\"'?\s<>]+)",
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


def is_skincare_sku(sku: str) -> bool:
    s = (sku or "").upper()
    if not SKU_RE.fullmatch(s):
        return False
    # Fashion / jewellery / watch / eyewear prefixes.
    if re.match(r"^(A\d|AB|AP|G\d|H\d|J\d|P\d{2}[A-Z])", s):
        return bool(re.fullmatch(r"\d{5,8}", s))
    return bool(re.fullmatch(r"\d{5,8}", s) or re.fullmatch(r"[A-Z]?\d{5,8}", s))


def is_gift_or_skip_url(url: str, slug: str = "") -> bool:
    blob = f"{url} {slug}".lower()
    return any(
        x in blob
        for x in ("e-gift-card", "gift-card", "egift", "virtual-gift")
    )


def pdp_url(sku: str, slug: str = "") -> str:
    slug = (slug or "").strip("/") or "product"
    return f"{BASE}/gb/skincare/p/{sku.upper()}/{slug}/"


def slug_from_url(url: str) -> str:
    m = re.search(r"/skincare/p/[A-Z0-9]+/([^/?#]+)", url or "", flags=re.I)
    return (m.group(1) if m else "").strip("/").lower()


def leaves_from_html(html: str) -> list[str]:
    """Most-specific official PLP code mentioned on a PDP (shade pages share it)."""
    best_code = ""
    for code in LEAF_BY_CAT_CODE:
        if len(code) < len(best_code):
            continue
        if re.search(rf"/skincare/[^\"'\\s]+/c/{re.escape(code)}/", html or "", flags=re.I):
            best_code = code
    if not best_code:
        return []
    cid, group = LEAF_BY_CAT_CODE[best_code]
    return sorted({cid, group})


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
        if "packshot-default" in f or "packshot_default" in f:
            return (0, f)
        if "packshot" in f or "still-life" in f or "product" in f:
            return (1, f)
        return (2, f)

    files.sort(key=rank)
    return [
        "https://www.chanel.com/images/t_one/q_auto:good,f_auto,fl_lossy,dpr_1.1/"
        f"w_1240/{fn}"
        for fn in files[:12]
    ]


def collections_for(leaves: list[str]) -> list[str]:
    cols = set(PARENT_COLS)
    for leaf in leaves:
        cols.add(leaf)
        group = (LEAF_META.get(leaf) or {}).get("group")
        if group:
            cols.add(group)
    return sorted(cols)


def primary_leaf(leaves: list[str]) -> str:
    for cid in PRIMARY_ORDER:
        if cid in leaves:
            return cid
    return PARENT_ID


def parse_hybris_skincare(
    html: str, url: str, sku_hint: str, leaves: list[str]
) -> dict | None:
    ld_list = _ld_products(html)
    ld = ld_list[0] if ld_list else {}
    sku = (sku_hint or "").upper()
    if not sku:
        m = re.search(r"/skincare/p/([A-Z0-9]{4,12})/", url, flags=re.I)
        sku = (m.group(1) if m else "").upper()
    if not sku or not is_skincare_sku(sku):
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
            "kind": "skincare",
        }

    titles = parse_title_parts(html)
    title = titles.get("title") or str(ld.get("name") or "").strip()
    subtitle = titles.get("subtitle") or ""
    color = titles.get("color") or str(ld.get("color") or "").strip()
    desc = parse_editorial(html) or str(ld.get("description") or "").strip()
    images = _hybris_image_urls(html, sku)
    if not images and ld.get("image"):
        images = [str(ld.get("image")).replace("www.chanel.cn", "www.chanel.com")]

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
    m_slug = re.search(r"/skincare/p/[^/]+/([^/\"'?]+)", url, flags=re.I)
    if m_slug:
        slug = m_slug.group(1).lower()

    leaf = primary_leaf(leaves)
    return {
        "id": sku,
        "productCode": sku,
        "sku": sku,
        "title": title,
        "titleShort": title_short,
        "subtitle": subtitle,
        "priceLabel": f"£{gbp:,.0f}" if gbp >= 1 else str(offers.get("price") or ""),
        "gbpPrice": gbp,
        "categoryLabel": (LEAF_META.get(leaf) or {}).get("label") or "Skincare",
        "collection": None,
        "collectionCode": None,
        "url": url if url.startswith("http") else pdp_url(sku, slug),
        "hierarchy": [
            {"label": "Skincare", "url": "/gb/skincare/"},
            {"label": (LEAF_META.get(leaf) or {}).get("label") or "Skincare", "url": ""},
        ],
        "details": details,
        "images": extra.get("images") or images,
        "sizes": [{"size": "UNI", "orliSize": "UNI", "sku": sku, "inStock": True}],
        "inStock": True,
        "new": False,
        "collections": collections_for(leaves),
        "leaf": leaf,
        "leaves": sorted(set(leaves)),
        "kind": "skincare",
    }


def parse_skincare_pdp(
    html: str, url: str, sku_hint: str = "", leaves: list[str] | None = None
) -> dict | None:
    return parse_hybris_skincare(html, url, sku_hint, leaves or [PARENT_ID])


def fetch_pdp_html(client: ChanelClient, url: str) -> tuple[int, str]:
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
        if is_skincare_sku(sku) and not is_gift_or_skip_url(pdp_url(sku, slug), slug):
            found.setdefault(sku, pdp_url(sku, slug))
    return found


def extract_plp_grid_skus(html: str) -> dict[str, str]:
    """Official PLP product tiles only — skip recs/editorials also in the HTML."""
    found: dict[str, str] = {}
    for href in re.findall(
        r'data-test="product_link"[^>]*href="([^"]+)"', html or "", flags=re.I
    ):
        m = PDP_RE.search(href) or PDP_RE.search(f"{BASE}{href}")
        if not m:
            continue
        sku, slug = m.group(1).upper(), m.group(2)
        if is_skincare_sku(sku) and not is_gift_or_skip_url(pdp_url(sku, slug), slug):
            found.setdefault(sku, pdp_url(sku, slug))
    if found:
        return found
    return extract_skus_from_html(html)


def discover_sitemap_skus(client: ChanelClient) -> dict[str, str]:
    text = ""
    for url in (SITEMAP, to_cn_url(SITEMAP)):
        try:
            with _rtw._session_lock:
                r = client.session.get(
                    url,
                    impersonate=client.impersonate,
                    timeout=90,
                    headers=_rtw.HTML_HEADERS,
                )
            if r.status_code == 200 and len(r.text) > 1000:
                text = r.text
                log(f"sitemap via {url} len={len(text)}")
                break
            log(f"sitemap weak {url} st={r.status_code} len={len(r.text)}")
        except Exception as e:
            log(f"sitemap error {url}: {e}")
    if not text:
        return {}
    by_sku: dict[str, str] = {}
    for m in PDP_RE.finditer(text or ""):
        sku = m.group(1).upper()
        slug = m.group(2)
        if not is_skincare_sku(sku):
            continue
        if is_gift_or_skip_url(pdp_url(sku, slug), slug):
            continue
        by_sku.setdefault(sku, pdp_url(sku, slug))
    log(f"sitemap skincare SKUs: {len(by_sku)}")
    return by_sku


def discover_plp_membership(
    client: ChanelClient, sku_urls: dict[str, str]
) -> dict[str, set[str]]:
    membership: dict[str, set[str]] = defaultdict(set)
    slug_leaves: dict[str, set[str]] = defaultdict(set)
    for cid, en, _ko, url, group in LEAVES:
        log(f"PLP {en} {url}")
        pages = [url] + [
            f"{url.rstrip('/')}/page-{n}/" for n in range(2, MAX_PLP_PAGES + 1)
        ]
        leaf_skus: set[str] = set()
        for page in pages:
            st, html = fetch_plp_html(client, page)
            if st == 404:
                break
            if st != 200 or len(html) < 5000:
                if page == url:
                    log(f"  weak {page} st={st} len={len(html)}")
                break
            batch = extract_plp_grid_skus(html)
            new_n = 0
            for sku, purl in batch.items():
                sku_urls.setdefault(sku, purl)
                if sku not in leaf_skus:
                    new_n += 1
                leaf_skus.add(sku)
                membership[sku].add(cid)
                membership[sku].add(group)
                slug = slug_from_url(purl) or slug_from_url(sku_urls.get(sku, ""))
                if slug:
                    slug_leaves[slug].add(cid)
                    slug_leaves[slug].add(group)
            log(f"  {page.split('/gb/')[-1]} → +{len(batch)} new={new_n} leaf={len(leaf_skus)}")
            if page != url and new_n == 0:
                break
            time.sleep(0.2)
        log(f"  => {cid} {len(leaf_skus)}")
    # Same product family (shared PDP slug) inherits the PLP leaf — shade SKUs
    # are usually missing from PLPs which only list a default shade.
    inherited = 0
    for sku, url in list(sku_urls.items()):
        if sku in membership:
            continue
        slug = slug_from_url(url)
        if slug and slug in slug_leaves:
            membership[sku].update(slug_leaves[slug])
            inherited += 1
    log(f"slug-inherited shade SKUs: {inherited}")
    # Hub leftover SKUs stay on the skincare parent (no nested catch-all leaf).
    st, hub_html = fetch_plp_html(client, HUB)
    if st == 200:
        for sku, purl in extract_skus_from_html(hub_html).items():
            sku_urls.setdefault(sku, purl)
            if sku not in membership:
                membership[sku].add(PARENT_ID)
    unmatched = 0
    for sku in sku_urls:
        if sku not in membership:
            membership[sku].add(PARENT_ID)
            unmatched += 1
    log(f"membership SKUs: {len(membership)} unmatched→parent={unmatched}")
    return membership


def fetch_image_bytes(client: ChanelClient, url: str, referer: str) -> bytes | None:
    headers = {
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9",
        "Referer": referer,
    }
    try:
        with _rtw._session_lock:
            r = client.session.get(
                url,
                impersonate=client.impersonate,
                timeout=12,
                headers=headers,
            )
            client._req_count += 1
        if r.status_code == 200 and len(r.content) > 2048:
            return bytes(r.content)
    except Exception:
        return None
    return None


def download_images(client: ChanelClient, sku: str, urls: list[str]) -> list[str]:
    dest = IMG_ROOT / sku.lower()
    dest.mkdir(parents=True, exist_ok=True)
    local: list[str] = []
    for i, url in enumerate(urls[:4], start=1):
        path = dest / f"{i}.jpg"
        web = f"/products/ch-pdp/{sku.lower()}/{i}.jpg"
        if path.exists() and path.stat().st_size > 2048:
            local.append(web)
            continue
        data = fetch_image_bytes(client, url, HUB)
        if not data:
            cn = url.replace("www.chanel.com", "www.chanel.cn")
            data = fetch_image_bytes(client, cn, to_cn_url(HUB))
        if not data:
            log(f"  skip img {sku} #{i}")
            continue
        path.write_bytes(data)
        local.append(web)
        time.sleep(0.03)
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
    if not row.get("gbpPrice") or row.get("kind") != "skincare":
        return False
    imgs = row.get("localImages") or []
    if not imgs:
        return False
    for p in imgs:
        path = ROOT / "public" / str(p).lstrip("/")
        if path.is_file() and path.stat().st_size > 2048:
            return True
    return False


def apply_leaves(row: dict, leaves: list[str]) -> dict:
    row = dict(row)
    leaf = primary_leaf(leaves)
    row["leaf"] = leaf
    row["leaves"] = sorted(set(leaves))
    row["collections"] = collections_for(leaves)
    row["kind"] = "skincare"
    row["categoryLabel"] = (LEAF_META.get(leaf) or {}).get("label") or "Skincare"
    return row


def write_raw(
    products: list[dict],
    skipped: list[dict],
    failed: list[dict],
) -> None:
    by_id = {p["sku"].upper(): p for p in products if p.get("sku")}
    products = sorted(by_id.values(), key=lambda p: p["sku"])
    leaf_counts = Counter()
    for p in products:
        for leaf in p.get("leaves") or [p.get("leaf") or PARENT_ID]:
            leaf_counts[leaf] += 1
    payload = {
        "scrapedAt": datetime.now(timezone.utc).isoformat(),
        "hub": HUB,
        "note": (
            "Chanel GB skincare hub — official product-type PLPs under "
            "Accessories→샤넬→스킨케어."
        ),
        "leaves": [
            {
                "id": cid,
                "label": en,
                "labelKo": ko,
                "url": url,
                "group": group,
            }
            for cid, en, ko, url, group in LEAVES
        ],
        "leafCounts": dict(leaf_counts),
        "skipped": skipped,
        "failed": failed,
        "products": products,
    }
    OUT_RAW.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    log(f"wrote {len(products)} skincare → {OUT_RAW}")
    log(f"leafCounts={dict(leaf_counts)} skipped={len(skipped)} failed={len(failed)}")


def bind_client() -> ChanelClient:
    _rtw.HUB = HUB
    _rtw.PROBE_SKU_URL = (
        "https://www.chanel.com/gb/skincare/p/133325/"
        "hydra-beauty-micro-serum/"
    )
    _rtw.IMPERSONATES = ("safari18_0_ios",)
    _rtw.SEED_PROXIES = []

    _orig_probe = _rtw.ChanelClient.probe_direct
    _skip_once = {"v": True}

    def _probe(self) -> bool:
        if _skip_once["v"]:
            _skip_once["v"] = False
            log("skip init proxy hunt — skincare uses CN/COM dual fetch")
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
    sku_urls = discover_sitemap_skus(client)
    membership = discover_plp_membership(client, sku_urls)
    log(f"unique skincare SKUs: {len(sku_urls)}")
    if args.discover_only:
        for sku, url in list(sku_urls.items())[:12]:
            log(f"  {sku} {sorted(membership.get(sku) or [])} {url}")
        return 0 if sku_urls else 1

    existing = load_existing_products()
    log(f"existing skincare in raw: {len(existing)}")
    if not sku_urls and not existing:
        log("ERROR: no skincare SKUs discovered")
        return 1

    cache = load_cache()
    products: list[dict] = []
    skipped: list[dict] = []
    failed: list[dict] = []

    kept = 0
    seeded: dict[str, dict] = {}
    for sku, row in {**cache, **existing}.items():
        su = str(sku).upper()
        leaves = sorted(membership.get(su) or row.get("leaves") or [PARENT_ID])
        row = apply_leaves(row if isinstance(row, dict) else {}, leaves)
        if not is_complete(row) or su in seeded:
            continue
        seeded[su] = row
        products.append(row)
        cache[su] = row
        kept += 1
    log(f"kept complete existing/cache: {kept}")
    if products:
        write_raw(products, [], [])

    have = {p["sku"].upper() for p in products}

    def _todo_key(item: tuple[str, str]) -> tuple[int, str]:
        sku = item[0]
        leaves = membership.get(sku) or set()
        specific = bool(set(leaves) - {PARENT_ID})
        return (0 if specific else 1, sku)

    todo = sorted(
        ((sku, url) for sku, url in sku_urls.items() if sku.upper() not in have),
        key=_todo_key,
    )
    log(f"new skincare SKUs to scrape: {len(todo)} (hub total {len(sku_urls)})")

    consecutive_blocks = 0
    sku_tries: dict[str, int] = {}
    i = 0
    while i < len(todo):
        sku, url = todo[i]
        i += 1
        leaves = sorted(membership.get(sku) or [])

        cached = cache.get(sku)
        if isinstance(cached, dict) and is_complete(cached):
            products.append(apply_leaves(cached, leaves or [PARENT_ID]))
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
        html_leaves = leaves_from_html(html)
        if html_leaves and not leaves:
            membership[sku].update(html_leaves)
            leaves = sorted(membership[sku])
        elif not leaves:
            leaves = [PARENT_ID]
            membership[sku].update(leaves)

        related = extract_skus_from_html(html)
        slug = slug_from_url(url)
        specific = set(leaves) - {PARENT_ID}
        for rsku, rurl in related.items():
            sku_urls.setdefault(rsku, rurl)
            # Only same-slug shade/size variants inherit this PLP leaf.
            # Cross-sell SKUs on a PDP must not steal another category.
            rslug = slug_from_url(rurl)
            if specific and slug and rslug == slug:
                membership[rsku].update(leaves)
            if rsku not in have and all(t[0] != rsku for t in todo):
                todo.append((rsku, rurl))

        parsed = parse_skincare_pdp(html, url, sku_hint=sku, leaves=leaves)
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
        parsed = apply_leaves(parsed, leaves)

        cache[sku] = parsed
        parsed = enrich_images(client, parsed)
        cache[sku] = parsed
        products.append(parsed)
        log(
            f"[{i}/{len(todo)}] OK {sku} £{parsed['gbpPrice']} "
            f"leaf={parsed.get('leaf')} imgs={len(parsed.get('localImages') or [])} "
            f"title={parsed.get('title')!r}"
        )
        save_cache(cache)
        if len(products) % 20 == 0:
            write_raw(products, skipped, failed)
        time.sleep(PDP_PAUSE)

    by_id = {p["sku"].upper(): p for p in products if p.get("sku")}
    for sku, row in cache.items():
        su = str(sku).upper()
        if su in by_id:
            continue
        if su in sku_urls and is_complete(row):
            by_id[su] = apply_leaves(row, sorted(membership.get(su) or row.get("leaves") or [PARENT_ID]))
    for sku, row in list(by_id.items()):
        leaves = sorted(membership.get(sku) or row.get("leaves") or [PARENT_ID])
        by_id[sku] = apply_leaves(row, leaves)
    products = list(by_id.values())

    save_cache(cache)
    if not products:
        log("ERROR: 0 skincare scraped")
        return 1
    write_raw(products, skipped, failed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
