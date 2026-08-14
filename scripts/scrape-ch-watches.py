#!/usr/bin/env python3
"""Scrape Chanel GB Watches into ch-watches-catalog-raw.json + images.

Official hub: https://www.chanel.com/gb/watches/
Shopable collection leaves (Hybris /c/4x2xN/):
  J12 / Première / BOY·FRIEND / Monsieur / Code Coco

PDPs: /gb/watches/p/H*/ — GBP via chanel.cn /gb/ mirror when GB is Akamai-blocked.
Editorial Fine Watchmaking pages (gem-set, artistic-craft, …) have no H* PDPs.
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
OUT_RAW = ROOT / "src/data/ch/ch-watches-catalog-raw.json"
PDP_CACHE = ROOT / "src/data/ch/ch-watches-pdp-cache.json"
IMG_ROOT = ROOT / "public/products/ch-pdp"

BASE = "https://www.chanel.com"
HUB = f"{BASE}/gb/watches/"
SITEMAP = f"{BASE}/gb/sitemap.xml"
PARENT_COLS = ["chanel-watches", "ch-watches"]

# Official GB Watches collection PLPs (hub Collections).
LEAVES: list[tuple[str, str, str, str]] = [
    (
        "ch-watches-j12",
        "J12",
        "J12",
        f"{BASE}/gb/watches/j12/c/4x2x1/",
    ),
    (
        "ch-watches-premiere",
        "Première",
        "프리미에르",
        f"{BASE}/gb/watches/premiere/c/4x2x2/",
    ),
    (
        "ch-watches-boy-friend",
        "BOY·FRIEND",
        "보이·프렌드",
        f"{BASE}/gb/watches/boy-friend/c/4x2x3/",
    ),
    (
        "ch-watches-monsieur",
        "Monsieur",
        "무슈",
        f"{BASE}/gb/watches/monsieur/c/4x2x6/",
    ),
    (
        "ch-watches-code-coco",
        "Code Coco",
        "코드 코코",
        f"{BASE}/gb/watches/code-coco/c/4x2x8/",
    ),
]

LEAF_IDS = [c for c, *_ in LEAVES]
LEAF_META = {
    cid: {"label": en, "labelKo": ko, "url": url} for cid, en, ko, url in LEAVES
}
LEAF_BY_PATH = {
    "j12": "ch-watches-j12",
    "premiere": "ch-watches-premiere",
    "boy-friend": "ch-watches-boy-friend",
    "monsieur": "ch-watches-monsieur",
    "code-coco": "ch-watches-code-coco",
}

PDP_PAUSE = 1.0
HARD_BLOCK_SLEEP = 8.0
MAX_PLP_PAGES = 8
PDP_RE = re.compile(
    r"/gb/watches/p/(H[0-9A-Z]+)/([^/\"'?\s<>]+)",
    flags=re.I,
)
SKU_RE = re.compile(r"^H[0-9A-Z]+$", flags=re.I)

_spec = importlib.util.spec_from_file_location(
    "scrape_ch_rtw", ROOT / "scripts" / "scrape-ch-rtw.py"
)
assert _spec and _spec.loader
_rtw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_rtw)

ChanelClient = _rtw.ChanelClient
is_challenge = _rtw.is_challenge
parse_gbp = _rtw.parse_gbp
log = _rtw.log


def is_watch_sku(sku: str) -> bool:
    return bool(SKU_RE.fullmatch((sku or "").upper()))


def pdp_url(sku: str, slug: str = "") -> str:
    slug = (slug or sku.lower()).strip("/") or sku.lower()
    return f"{BASE}/gb/watches/p/{sku.upper()}/{slug}/"


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


def _watch_image_urls(html: str, sku: str) -> list[str]:
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
        if sku_l not in u.lower() or not re.search(
            r"\.(?:jpg|jpeg|png|webp)$", u, re.I
        ):
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
        if "packshot-profil" in f or "profil" in f:
            return (1, f)
        if "packshot-dos" in f or "-dos-" in f:
            return (2, f)
        if "packshot-other" in f or "packshot-alternative" in f:
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


def leaf_from_breadcrumb(html: str, url: str) -> str | None:
    for slug, leaf in LEAF_BY_PATH.items():
        if f"/gb/watches/{slug}/" in (html or "") or f"/watches/{slug}/" in url:
            # Prefer breadcrumb / PLP link over incidental mentions.
            if re.search(
                rf'/gb/watches/{re.escape(slug)}/c/',
                html or "",
                flags=re.I,
            ):
                return leaf
    # Breadcrumb name match
    m = re.search(
        r'"@id"\s*:\s*"/gb/watches/(j12|premiere|boy-friend|monsieur|code-coco)/',
        html or "",
        flags=re.I,
    )
    if m:
        return LEAF_BY_PATH.get(m.group(1).lower())
    return None


def parse_watch_pdp(html: str, url: str, leaf_hint: str | None = None) -> dict | None:
    ld_list = _ld_products(html)
    ld = ld_list[0] if ld_list else {}
    dl = _datalayer_product(html)

    sku = str(ld.get("sku") or dl.get("id") or "").strip().upper()
    if not sku:
        m = re.search(r"/watches/p/(H[0-9A-Z]+)/", url, flags=re.I)
        sku = (m.group(1) if m else "").upper()
    if not sku or not is_watch_sku(sku):
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
            "kind": "watches",
        }

    title = str(ld.get("name") or dl.get("name") or "").strip()
    color = str(ld.get("color") or "").strip()
    material = str(ld.get("material") or "").strip()
    desc = str(ld.get("description") or "").strip()
    variant = str(dl.get("variant") or "").strip()
    collection_name = str(
        dl.get("dimension18") or dl.get("dimension19") or dl.get("brand") or ""
    ).strip()
    leaf = leaf_hint or leaf_from_breadcrumb(html, url)
    if not leaf:
        # Fallback from title / category crumbs
        low = f"{title} {desc}".lower()
        if "j12" in low:
            leaf = "ch-watches-j12"
        elif "première" in low or "premiere" in low:
            leaf = "ch-watches-premiere"
        elif "boy" in low and "friend" in low:
            leaf = "ch-watches-boy-friend"
        elif "monsieur" in low:
            leaf = "ch-watches-monsieur"
        elif "code coco" in low or "code-coco" in low:
            leaf = "ch-watches-code-coco"
        else:
            leaf = "ch-watches-j12"

    images = _watch_image_urls(html, sku)
    if not images and ld.get("image"):
        img = str(ld.get("image")).replace("www.chanel.cn", "www.chanel.com")
        images = [img]

    avail = str(offers.get("availability") or "")
    # Watches are often boutique-only ("not buyable") but still catalogued with GBP.
    in_stock = "OutOfStock" not in avail
    leaf_label = LEAF_META.get(leaf, {}).get("label") or "Watches"
    cols = sorted(set([*PARENT_COLS, leaf]))
    price_label = f"£{gbp:,.0f}" if gbp >= 1 else str(offers.get("price") or "")

    return {
        "id": sku,
        "productCode": sku,
        "sku": sku,
        "title": title,
        "priceLabel": price_label,
        "gbpPrice": gbp,
        "categoryLabel": leaf_label,
        "collection": collection_name.title() if collection_name else leaf_label,
        "collectionCode": None,
        "url": url if url.startswith("http") else pdp_url(sku),
        "hierarchy": [
            {"label": "Watches", "url": "/gb/watches/"},
            {"label": leaf_label, "url": LEAF_META.get(leaf, {}).get("url") or ""},
        ],
        "details": {
            "color": color,
            "description": desc,
            "fabrics": material,
            "reference": sku,
            "dimensions": variant or None,
        },
        "images": images,
        "imageMeta": [
            {
                "typology": "PACKSHOT_DEFAULT" if i == 0 else "PACKSHOT_OTHER",
                "source": src,
            }
            for i, src in enumerate(images)
        ],
        "sizes": [
            {
                "id": sku,
                "size": "UNI",
                "orliSize": "UNI",
                "sku": sku,
                "inStock": in_stock,
                "sellableOnline": "InStock" in avail,
            }
        ],
        "availabilityStatus": "IN_STOCK" if in_stock else "OUT_OF_STOCK",
        "inStock": in_stock,
        "new": False,
        "collections": cols,
        "leaf": leaf,
        "leaves": [leaf],
        "shape": leaf,
        "kind": "watches",
    }


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
            # CN CDN fallback
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
    log(f"sitemap watch SKUs: {len(by_sku)}")
    return by_sku


def discover_leaf_membership(client: ChanelClient) -> dict[str, str]:
    """Map SKU → leaf from official collection PLPs (paginated)."""
    membership: dict[str, str] = {}
    for leaf, en, _ko, url in LEAVES:
        log(f"PLP {leaf} ({en})")
        pages = [url] + [
            f"{url.rstrip('/')}/page-{n}/" for n in range(2, MAX_PLP_PAGES + 1)
        ]
        found = 0
        for page in pages:
            st, html = fetch_plp_html(client, page)
            if st != 200 or len(html) < 5000:
                log(f"  weak {page} st={st} len={len(html)}")
                break
            batch = {m.group(1).upper() for m in PDP_RE.finditer(html or "")}
            if not batch and page != url:
                break
            for sku in batch:
                membership.setdefault(sku, leaf)
            found += len(batch)
            log(f"  {page} → +{len(batch)} (leaf total ~{found})")
            if page != url and not batch:
                break
            time.sleep(0.3)
    log(f"leaf membership SKUs: {len(membership)}")
    return membership


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
            "Chanel GB Watches from official Collections PLPs + sitemap "
            "(J12 / Première / BOY·FRIEND / Monsieur / Code Coco)."
        ),
        "leafCounts": dict(leaf_counts),
        "skipped": skipped,
        "failed": failed,
        "products": products,
    }
    OUT_RAW.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    log(f"wrote {len(products)} watches → {OUT_RAW}")
    log(f"leafCounts={dict(leaf_counts)} skipped={len(skipped)} failed={len(failed)}")


def main() -> int:
    IMG_ROOT.mkdir(parents=True, exist_ok=True)
    OUT_RAW.parent.mkdir(parents=True, exist_ok=True)

    _rtw.HUB = HUB
    _rtw.PROBE_SKU_URL = (
        "https://www.chanel.com/gb/watches/p/H11684/j12-watch-calibre-12-1-38-mm/"
    )
    _rtw.IMPERSONATES = ("safari18_0_ios",)
    _rtw.SEED_PROXIES = []

    _orig_probe = _rtw.ChanelClient.probe_direct
    _skip_once = {"v": True}

    def _probe(self) -> bool:
        if _skip_once["v"]:
            _skip_once["v"] = False
            log("skip init proxy hunt — Watches uses chanel.cn /gb/ fallback")
            return True
        return _orig_probe(self)

    def _no_proxy(self) -> None:
        log("skip public-proxy hunt")

    _rtw.ChanelClient.probe_direct = _probe
    _rtw.ChanelClient.ensure_proxy = _no_proxy
    _rtw.ChanelClient.rotate_proxy = lambda self, mark_dead=True: self.clear_proxy()

    client = ChanelClient()

    membership = discover_leaf_membership(client)
    sku_urls = discover_sitemap_skus(client)
    # Ensure PLP-only SKUs (if any) are included.
    for sku, leaf in membership.items():
        sku_urls.setdefault(sku, pdp_url(sku))

    if not sku_urls:
        log("ERROR: no watch SKUs discovered")
        return 1

    todo = sorted(sku_urls.items())
    log(f"unique watch SKUs to scrape: {len(todo)}")

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
        leaf_hint = membership.get(sku)

        cached = cache.get(sku)
        if (
            isinstance(cached, dict)
            and cached.get("gbpPrice")
            and cached.get("kind") == "watches"
            and not cached.get("_skip")
        ):
            if leaf_hint:
                cached["leaf"] = leaf_hint
                cached["leaves"] = [leaf_hint]
                cached["collections"] = sorted(set([*PARENT_COLS, leaf_hint]))
            if not cached.get("localImages"):
                cached = enrich_images(client, cached)
            cache[sku] = cached
            save_cache(cache)
            products.append(cached)
            leaf_counts[cached.get("leaf") or "unknown"] += 1
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
                failed.append(
                    {"sku": sku, "url": url, "status": status, "reason": "akamai"}
                )
                break
            i -= 1
            continue

        consecutive_blocks = 0
        parsed = parse_watch_pdp(html, url, leaf_hint=leaf_hint)
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
        leaf_counts[parsed.get("leaf") or "unknown"] += 1
        log(
            f"[{i}/{len(todo)}] OK {sku} £{parsed['gbpPrice']} "
            f"leaf={parsed.get('leaf')} "
            f"imgs={len(parsed.get('localImages') or [])}"
        )
        save_cache(cache)
        time.sleep(0.35)

    by_id = {p["sku"]: p for p in products if p.get("sku")}
    for sku, row in cache.items():
        if (
            isinstance(row, dict)
            and row.get("gbpPrice")
            and row.get("kind") == "watches"
            and not row.get("_skip")
            and sku not in by_id
        ):
            if membership.get(sku):
                row["leaf"] = membership[sku]
                row["leaves"] = [membership[sku]]
                row["collections"] = sorted(set([*PARENT_COLS, membership[sku]]))
            by_id[sku] = row
    products = list(by_id.values())
    leaf_counts = Counter(p.get("leaf") for p in products if p.get("leaf"))

    save_cache(cache)
    if not products:
        log("ERROR: 0 watches scraped")
        return 1
    write_raw(products, skipped, failed, leaf_counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
