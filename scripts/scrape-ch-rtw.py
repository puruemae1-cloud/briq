#!/usr/bin/env python3
"""Scrape Chanel GB Ready-to-Wear PDPs into ch-rtw-catalog-raw.json + images.

Akamai: use curl_cffi impersonate=safari17_2_ios (desktop Chrome is denied).
Warm the RTW hub session before PDPs; re-warm on challenge pages.

Product discovery:
  1. GB sitemap fashion /p/P.../ URLs (~458)
  2. Hub editorial productId cards in __NEXT_DATA__
  3. Leaf assignment via PDP hierarchy under /ready-to-wear/l/... or categoryLabel
  4. ALL THE LOOKS: every imported RTW garment is also tagged ch-women-looks
     (look PLPs often have empty SSR grids; full RTW set = All the Looks)

Skips Ready-to-Wear Accessories and any SKU without a mapped shape leaf.
"""
from __future__ import annotations

import json
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from curl_cffi import requests as cffi_requests

ROOT = Path(__file__).resolve().parents[1]
OUT_RAW = ROOT / "src/data/ch/ch-rtw-catalog-raw.json"
PDP_CACHE = ROOT / "src/data/ch/ch-pdp-cache.json"
IMG_ROOT = ROOT / "public/products/ch-pdp"

BASE = "https://www.chanel.com"
HUB = f"{BASE}/gb/fashion/ready-to-wear/"
SITEMAP = f"{BASE}/gb/sitemap.xml"

# Official RTW leaf slug (URL path) → Briq collection id
LEAF_BY_SLUG: dict[str, str] = {
    "jackets": "ch-women-jackets",
    "dresses": "ch-women-dresses",
    "blouses-tops": "ch-women-blouses-tops",
    "cardigans-sweater": "ch-women-cardigans-sweaters",
    "skirts": "ch-women-skirts",
    "trousers-shorts": "ch-women-trousers-shorts",
    "swimwear": "ch-women-swimwear",
    "outerwear": "ch-women-outerwear",
}

LEAF_BY_CATEGORY_LABEL: dict[str, str] = {
    "Jackets": "ch-women-jackets",
    "Dresses": "ch-women-dresses",
    "Blouses & Tops": "ch-women-blouses-tops",
    "Cardigans & Sweaters": "ch-women-cardigans-sweaters",
    "Skirts": "ch-women-skirts",
    "Trousers & Shorts": "ch-women-trousers-shorts",
    "Swimwear": "ch-women-swimwear",
    "Outerwear": "ch-women-outerwear",
}

LEAF_META = {
    "ch-women-looks": {
        "label": "All the Looks",
        "labelKo": "전체 룩",
        "url": f"{HUB}l/1x1x9/the-looks/",
    },
    "ch-women-jackets": {
        "label": "Jackets",
        "labelKo": "재킷",
        "url": f"{HUB}l/1x1x9x3/jackets/",
    },
    "ch-women-dresses": {
        "label": "Dresses",
        "labelKo": "드레스",
        "url": f"{HUB}l/1x1x9x8/dresses/",
    },
    "ch-women-blouses-tops": {
        "label": "Blouses & Tops",
        "labelKo": "블라우스 & 탑",
        "url": f"{HUB}l/1x1x9x5/blouses-tops/",
    },
    "ch-women-cardigans-sweaters": {
        "label": "Cardigans & Sweaters",
        "labelKo": "가디건 & 스웨터",
        "url": f"{HUB}l/1x1x9x6/cardigans-sweater/",
    },
    "ch-women-skirts": {
        "label": "Skirts",
        "labelKo": "스커트",
        "url": f"{HUB}l/1x1x9x7/skirts/",
    },
    "ch-women-trousers-shorts": {
        "label": "Trousers & Shorts",
        "labelKo": "팬츠 & 쇼츠",
        "url": f"{HUB}l/1x1x9x4/trousers-shorts/",
    },
    "ch-women-swimwear": {
        "label": "Swimwear",
        "labelKo": "스윔웨어",
        "url": f"{HUB}l/1x1x9x10/swimwear/",
    },
    "ch-women-outerwear": {
        "label": "Outerwear",
        "labelKo": "아우터웨어",
        "url": f"{HUB}l/1x1x9x2/outerwear/",
    },
}

SHAPE_LEAVES = set(LEAF_BY_SLUG.values())
PARENT_COLS = ["chanel", "ch-women", "ch-women-rtw", "ch-women-looks"]

HTML_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
}

WARM_EVERY = 12
MAX_RETRIES = 4
PDP_PAUSE = 1.2
CHALLENGE_COOLDOWN = 3.0
HARD_BLOCK_SLEEP = 12.0
# Prefer iOS Safari; rotate if Akamai soft-blocks the session.
IMPERSONATES = ("safari17_2_ios", "safari18_0_ios")
PROBE_SKU_URL = (
    "https://www.chanel.com/gb/fashion/p/P82545K11942UA557/jacket-mixed-fibres/"
)
PROXY_LIST_URL = (
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http"
    "&timeout=5000&country=gb,us,de,nl,fr&ssl=yes&anonymity=all"
)
# Proxies that successfully served Chanel PDPs in this environment.
SEED_PROXIES = [
    "95.211.64.139:8888",
    "38.76.9.0:999",
    "38.51.207.118:999",
    "154.18.255.99:1111",
]
PROXY_QUICK_TIMEOUT = 8
PROXY_VALIDATE_TIMEOUT = 12

_print_lock = Lock()
_session_lock = Lock()


def log(msg: str) -> None:
    with _print_lock:
        print(msg, flush=True)


def fetch_proxy_candidates(limit: int = 60) -> list[str]:
    """Public HTTP proxies — local IP is Akamai-banned on /fashion/p/."""
    out: list[str] = []
    # Seed with proxies known to work for Chanel PDPs
    seeds = list(SEED_PROXIES)
    try:
        s = cffi_requests.Session()
        resp = s.get(PROXY_LIST_URL, impersonate="chrome124", timeout=30)
        for line in resp.text.splitlines():
            line = line.strip()
            if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}:\d+", line):
                out.append(line)
    except Exception as e:
        log(f"proxy list fetch failed: {e}")
    merged: list[str] = []
    seen: set[str] = set()
    for p in seeds + out:
        if p not in seen:
            seen.add(p)
            merged.append(p)
    return merged[:limit]


def normalize_img_url(u: str | None) -> str:
    if not u:
        return ""
    u = u.strip()
    if u.startswith("//"):
        u = "https:" + u
    elif u.startswith("/"):
        u = BASE + u
    # Chanel SSR often emits `.../as///f_auto//-ID.jpg`
    while "///" in u:
        u = u.replace("///", "/")
    u = re.sub(r"(?<!:)/{2,}", "/", u)
    return u


def parse_gbp(price: str | float | int | None) -> float | None:
    if price is None:
        return None
    if isinstance(price, (int, float)):
        return float(price)
    s = str(price)
    m = re.search(r"([\d,]+(?:\.\d+)?)", s.replace("\xa0", " "))
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


def extract_next_data(html: str) -> dict | None:
    m = re.search(
        r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        html,
        flags=re.S,
    )
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def is_challenge(html: str, status: int) -> bool:
    if status in (403, 429, 503):
        return True
    if status != 200:
        return True
    if "__NEXT_DATA__" in html:
        return False
    if "sec-if-cpt-container" in html or "Access Denied" in html:
        return True
    return len(html) < 8000


class ChanelClient:
    def __init__(self) -> None:
        self.session = cffi_requests.Session()
        self._req_count = 0
        self._imp_idx = 0
        self._proxy: str | None = None
        self._proxy_pool: list[str] = []
        self._proxy_idx = 0
        self._dead_proxies: set[str] = set()
        # Prefer direct IP when Akamai allows it (common on residential / some CI).
        if self.probe_direct():
            log("PDP direct access OK — proxy disabled until blocked")
        else:
            log("PDP direct blocked — selecting proxy")
            self._proxy_pool = fetch_proxy_candidates()
            self.pick_working_proxy()
        self.warm()

    @property
    def impersonate(self) -> str:
        return IMPERSONATES[self._imp_idx % len(IMPERSONATES)]

    @property
    def proxies(self) -> dict[str, str] | None:
        if not self._proxy:
            return None
        url = f"http://{self._proxy}"
        return {"http": url, "https": url}

    def probe_direct(self) -> bool:
        try:
            self.session.get(
                HUB,
                impersonate=self.impersonate,
                timeout=45,
                headers=HTML_HEADERS,
            )
            p = self.session.get(
                PROBE_SKU_URL,
                impersonate=self.impersonate,
                timeout=45,
                headers={**HTML_HEADERS, "Referer": HUB},
            )
            ok = not is_challenge(p.text, p.status_code)
            if ok:
                log(f"direct PDP OK ({len(p.text)} bytes)")
            return ok
        except Exception as e:
            log(f"direct PDP probe failed: {e}")
            return False

    def rotate_impersonate(self) -> None:
        self._imp_idx = (self._imp_idx + 1) % len(IMPERSONATES)
        self.session = cffi_requests.Session()
        log(f"rotate impersonate → {self.impersonate}")

    def clear_proxy(self) -> None:
        """Drop proxy and open a fresh direct session."""
        self._proxy = None
        self.session = cffi_requests.Session()
        self._req_count = 0
        log("cleared proxy → trying direct again")
        try:
            self.session.get(
                HUB,
                impersonate=self.impersonate,
                timeout=60,
                headers=HTML_HEADERS,
            )
        except Exception:
            pass

    def soft_refresh(self) -> None:
        """New TLS session on the same proxy — clears soft Akamai challenges."""
        self.session = cffi_requests.Session()
        self._req_count = 0
        try:
            self.session.get(
                HUB,
                impersonate=self.impersonate,
                timeout=60,
                headers=HTML_HEADERS,
                proxies=self.proxies,
            )
        except Exception:
            pass

    def rotate_proxy(self, mark_dead: bool = True) -> None:
        if mark_dead and self._proxy:
            self._dead_proxies.add(self._proxy)
        self.session = cffi_requests.Session()
        # Prefer quick try without full validate — validate burns minutes
        tried = 0
        while tried < 15 and self._proxy_idx < len(self._proxy_pool):
            cand = self._proxy_pool[self._proxy_idx]
            self._proxy_idx += 1
            tried += 1
            if cand in self._dead_proxies:
                continue
            self._proxy = cand
            log(f"try proxy {cand}")
            try:
                r = self.session.get(
                    PROBE_SKU_URL,
                    impersonate=self.impersonate,
                    timeout=PROXY_QUICK_TIMEOUT,
                    headers={**HTML_HEADERS, "Referer": HUB},
                    proxies=self.proxies,
                )
                if not is_challenge(r.text, r.status_code):
                    log(f"proxy OK {cand} (quick {len(r.text)} bytes)")
                    self._req_count = 0
                    return
            except Exception as e:
                log(f"proxy fail {cand}: {e}")
                self._dead_proxies.add(cand)
                self.session = cffi_requests.Session()
                continue
            self._dead_proxies.add(cand)
            self.session = cffi_requests.Session()
        # Proxies exhausted — fall back to direct (often recovers after cooldown).
        self.clear_proxy()
        if self.probe_direct():
            log("recovered via direct after proxy exhaustion")
            return
        # Fall back to full validation pass on a refreshed pool
        self._proxy_pool = fetch_proxy_candidates(80)
        self._proxy_idx = 0
        self.pick_working_proxy(validate=True)
        log("WARN: exhausted quick proxies — used validated pick")

    def ensure_proxy(self) -> None:
        """Load a working proxy when direct access starts failing."""
        if self._proxy:
            return
        if not self._proxy_pool:
            self._proxy_pool = fetch_proxy_candidates()
            self._proxy_idx = 0
        self.pick_working_proxy()

    def pick_working_proxy(self, validate: bool = True) -> None:
        def _try_pool() -> bool:
            while self._proxy_idx < len(self._proxy_pool):
                cand = self._proxy_pool[self._proxy_idx]
                self._proxy_idx += 1
                if cand in self._dead_proxies:
                    continue
                self._proxy = cand
                log(f"try proxy {cand}")
                if not validate or self.validate_proxy():
                    return True
                self._dead_proxies.add(cand)
                self.session = cffi_requests.Session()
            return False

        if _try_pool():
            return
        log("refreshing proxy pool…")
        self._proxy_pool = fetch_proxy_candidates(80)
        self._proxy_idx = 0
        if _try_pool():
            return
        self._proxy = None
        log("WARN: no working proxy in pool")

    def validate_proxy(self) -> bool:
        if not self._proxy:
            return False
        try:
            r = self.session.get(
                HUB,
                impersonate=self.impersonate,
                timeout=PROXY_VALIDATE_TIMEOUT,
                headers=HTML_HEADERS,
                proxies=self.proxies,
            )
            if r.status_code != 200 or len(r.text) < 20000:
                return False
            p = self.session.get(
                PROBE_SKU_URL,
                impersonate=self.impersonate,
                timeout=PROXY_VALIDATE_TIMEOUT,
                headers={**HTML_HEADERS, "Referer": HUB},
                proxies=self.proxies,
            )
            ok = not is_challenge(p.text, p.status_code)
            if ok:
                log(f"proxy OK {self._proxy} (pdp {len(p.text)} bytes)")
            return ok
        except Exception as e:
            log(f"proxy fail {self._proxy}: {e}")
            return False

    def warm(self) -> None:
        with _session_lock:
            try:
                r = self.session.get(
                    HUB,
                    impersonate=self.impersonate,
                    timeout=90,
                    headers=HTML_HEADERS,
                    proxies=self.proxies,
                )
                log(
                    f"warm hub → {r.status_code} ({len(r.text)} bytes) "
                    f"[{self.impersonate}] proxy={self._proxy}"
                )
                if is_challenge(r.text, r.status_code):
                    # hub should work without proxy too
                    r = self.session.get(
                        HUB,
                        impersonate=self.impersonate,
                        timeout=90,
                        headers=HTML_HEADERS,
                    )
                    log(f"warm hub direct → {r.status_code} ({len(r.text)} bytes)")
            except Exception as e:
                log(f"warm hub error: {e}")
                try:
                    r = self.session.get(
                        HUB,
                        impersonate=self.impersonate,
                        timeout=90,
                        headers=HTML_HEADERS,
                    )
                    log(f"warm hub fallback → {r.status_code}")
                except Exception as e2:
                    log(f"warm hub fallback error: {e2}")
            self._req_count = 0

    def get_html(
        self, url: str, referer: str = HUB, max_attempts: int | None = None
    ) -> tuple[int, str]:
        headers = {**HTML_HEADERS, "Referer": referer}
        last_status, last_text = 0, ""
        attempts = max_attempts if max_attempts is not None else MAX_RETRIES
        is_pdp = "/fashion/p/" in url or "/p/" in url
        for attempt in range(1, attempts + 1):
            if self._req_count >= WARM_EVERY:
                self.warm()
            use_proxy = bool(is_pdp and self._proxy)
            try:
                with _session_lock:
                    r = self.session.get(
                        url,
                        impersonate=self.impersonate,
                        timeout=90,
                        headers=headers,
                        proxies=self.proxies if use_proxy else None,
                    )
                    self._req_count += 1
                    last_status, last_text = r.status_code, r.text
            except Exception as e:
                log(f"  GET error {url}: {e} (attempt {attempt})")
                time.sleep(1.2 * attempt)
                if use_proxy:
                    # Dead tunnel — try direct before burning more proxies.
                    self.clear_proxy()
                    if not self.probe_direct():
                        self.ensure_proxy()
                elif is_pdp:
                    self.soft_refresh()
                else:
                    self.rotate_impersonate()
                self.warm()
                continue
            if not is_challenge(last_text, last_status):
                return last_status, last_text
            log(
                f"  challenge {last_status} on {url} "
                f"(attempt {attempt}, len={len(last_text)}, proxy={self._proxy})"
            )
            if attempt < attempts:
                time.sleep(CHALLENGE_COOLDOWN)
                if use_proxy:
                    if attempt == 1 and len(last_text) < 8000:
                        self.soft_refresh()
                    else:
                        self.clear_proxy()
                        if not self.probe_direct():
                            self.ensure_proxy()
                elif is_pdp:
                    # Soft challenge on direct — refresh session, then proxy.
                    if attempt == 1:
                        self.soft_refresh()
                    else:
                        self.ensure_proxy()
                else:
                    self.rotate_impersonate()
                    self.warm()
        return last_status, last_text

    def get_bytes(self, url: str, referer: str = HUB) -> bytes | None:
        # Image CDN is not IP-banned — hit it directly.
        headers = {
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.9",
            "Referer": referer,
        }
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                with _session_lock:
                    r = self.session.get(
                        url,
                        impersonate=self.impersonate,
                        timeout=90,
                        headers=headers,
                    )
                    self._req_count += 1
                if r.status_code == 200 and len(r.content) > 2048:
                    ctype = (r.headers.get("content-type") or "").lower()
                    if "image" in ctype or url.lower().endswith(
                        (".jpg", ".jpeg", ".png", ".webp")
                    ):
                        return bytes(r.content)
                if r.status_code in (403, 429):
                    time.sleep(1.0 * attempt)
                    continue
            except Exception as e:
                log(f"  img error {url}: {e}")
                time.sleep(0.8 * attempt)
        return None


def discover_sitemap_skus(client: ChanelClient) -> dict[str, str]:
    # Sitemap works directly
    status, text = client.get_html(SITEMAP, max_attempts=2)
    if is_challenge(text, status):
        # try without treating as pdp
        try:
            r = client.session.get(
                SITEMAP, impersonate=client.impersonate, timeout=90, headers=HTML_HEADERS
            )
            status, text = r.status_code, r.text
        except Exception:
            pass
    if status != 200:
        log(f"WARN sitemap status {status}")
        return {}
    by_sku: dict[str, str] = {}
    for u in re.findall(r"https://www\.chanel\.com/gb/fashion/p/P[^<\s\"]+", text):
        m = re.search(r"/p/(P[^/]+)/", u)
        if not m:
            continue
        sku = m.group(1)
        by_sku.setdefault(sku, u.rstrip("/").split("#")[0] + "/")
    log(f"sitemap P* SKUs: {len(by_sku)}")
    return by_sku


def discover_hub_product_ids(client: ChanelClient) -> set[str]:
    status, text = client.get_html(HUB)
    if status != 200:
        return set()
    nd = extract_next_data(text)
    if not nd:
        return set()
    raw = json.dumps(nd)
    ids = set(re.findall(r'"productId"\s*:\s*"(P[^"]+)"', raw))
    log(f"hub productIds: {len(ids)}")
    return ids


def leaf_from_product(prod: dict) -> str | None:
    """Map PDP to a shape leaf under official RTW nav (not collection the-looks)."""
    for h in prod.get("hierarchy") or []:
        url = (h.get("url") or "").lower()
        if "/ready-to-wear/l/" not in url:
            continue
        # skip bare the-looks parent 1x1x9 (All the Looks PLP) — use shape leaves
        for slug, cid in LEAF_BY_SLUG.items():
            if f"/{slug}/" in url or url.rstrip("/").endswith(f"/{slug}"):
                return cid
    label = (prod.get("categoryLabel") or "").strip()
    return LEAF_BY_CATEGORY_LABEL.get(label)


def order_images(images: list[dict]) -> list[str]:
    """Prefer studio garment packshots (STOCKMAN) over lifestyle model shots.

    Chanel RTW PDPs usually ship:
      PACKSHOT_DEFAULT / ALTERNATIVE / OTHER — on-model lifestyle / look photos
      PACKSHOT_STOCKMAN — studio garment views (FRONT / BACK / DETAIL)

    Briq PLP thumbnails must show the garment, not the lookbook model.
    """
    preferred = (
        "PACKSHOT_STOCKMAN",
        "PACKSHOT_OTHER",
        "PACKSHOT_ALTERNATIVE",
        "PACKSHOT_DEFAULT",
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
        # FRONT before BACK / DETAIL within STOCKMAN
        angle_rank = {"FRONT": 0, "BACK": 1, "DETAIL": 2}.get(angle, 5)
        scored.append((rank, angle_rank, i, src))
    scored.sort()
    return [u for _, _, _, u in scored]


def availability_map(avail: dict | None) -> tuple[str | None, dict[str, bool]]:
    if not avail or not isinstance(avail, dict):
        return None, {}
    top = None
    a = avail.get("availability")
    if isinstance(a, dict):
        top = a.get("status")
    by_id: dict[str, bool] = {}
    for v in avail.get("variants") or []:
        if not isinstance(v, dict):
            continue
        vid = v.get("id")
        st = ((v.get("availability") or {}) if isinstance(v.get("availability"), dict) else {}).get(
            "status"
        )
        if vid:
            by_id[str(vid)] = st == "IN_STOCK"
    return top, by_id


def parse_pdp(html: str, url: str) -> dict | None:
    nd = extract_next_data(html)
    if not nd:
        return None
    data = (nd.get("props") or {}).get("pageProps", {}).get("data") or {}
    prod = data.get("product")
    if not isinstance(prod, dict):
        return None
    sku = str(prod.get("sku") or prod.get("id") or "").strip()
    if not sku.startswith("P"):
        return None  # look pages etc.

    leaf = leaf_from_product(prod)
    if not leaf:
        return {
            "_skip": True,
            "sku": sku,
            "reason": f"unmapped categoryLabel={prod.get('categoryLabel')!r}",
            "url": url,
            "categoryLabel": prod.get("categoryLabel"),
            "hierarchy": prod.get("hierarchy"),
        }

    gbp = parse_gbp(prod.get("price"))
    if gbp is None or gbp <= 0:
        return {
            "_skip": True,
            "sku": sku,
            "reason": f"bad price {prod.get('price')!r}",
            "url": url,
        }

    top_status, stock_by_id = availability_map(data.get("availability"))
    variants_out: list[dict] = []
    any_in = False
    for v in prod.get("variants") or []:
        if not isinstance(v, dict):
            continue
        size = str(v.get("orliSize") or "").strip()
        if not size:
            continue
        vid = str(v.get("id") or f"{sku}{size}")
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
    if top_status == "IN_STOCK" and not any_in and not variants_out:
        any_in = True
    elif top_status == "IN_STOCK" and variants_out and not any_in:
        # trust per-size map; product-level IN_STOCK without sizes stays True
        pass

    details = prod.get("details") if isinstance(prod.get("details"), dict) else {}
    look = prod.get("look") if isinstance(prod.get("look"), dict) else None
    cols = sorted(
        {
            leaf,
            *PARENT_COLS,
        }
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
        "inStock": any_in or (top_status == "IN_STOCK" and not variants_out),
        "look": look,
        "new": bool(prod.get("new")),
        "collections": cols,
        "leaf": leaf,
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


def wait_for_pdp_access(client: ChanelClient, max_wait_s: float = 600) -> bool:
    """Ensure we have a proxy that can fetch PDPs."""
    started = time.time()
    attempt = 0
    while time.time() - started < max_wait_s:
        attempt += 1
        status, html = client.get_html(PROBE_SKU_URL, max_attempts=1)
        if not is_challenge(html, status):
            log(f"PDP access OK (attempt {attempt}, proxy={client._proxy})")
            return True
        log(f"PDP blocked on proxy={client._proxy}; rotating…")
        if client._proxy:
            client.rotate_proxy()
        else:
            client.ensure_proxy()
        client.warm()
        time.sleep(2)
    return False


def enrich_images(client: ChanelClient, parsed: dict) -> dict:
    sku = parsed["sku"]
    locals_ = download_images(client, sku, parsed.get("images") or [])
    parsed["localImages"] = locals_
    if locals_:
        parsed["localImage"] = locals_[0]
        if len(locals_) > 1:
            parsed["localHover"] = locals_[1]
    return parsed


def main() -> int:
    IMG_ROOT.mkdir(parents=True, exist_ok=True)
    OUT_RAW.parent.mkdir(parents=True, exist_ok=True)

    client = ChanelClient()
    sitemap = discover_sitemap_skus(client)
    hub_ids = discover_hub_product_ids(client)

    # Prefer sitemap canonical URLs; invent path for hub-only ids
    todo: dict[str, str] = dict(sitemap)
    for pid in hub_ids:
        todo.setdefault(pid, f"{BASE}/gb/fashion/p/{pid}/")

    cache = load_cache()
    products: list[dict] = []
    skipped: list[dict] = []
    failed: list[dict] = []
    leaf_counts: Counter[str] = Counter()

    items = sorted(todo.items())
    log(f"scraping {len(items)} PDPs…")

    if not wait_for_pdp_access(client):
        log("ERROR: PDP access never recovered — aborting")
        return 1

    consecutive_blocks = 0
    i = 0
    while i < len(items):
        sku, url = items[i]
        i += 1
        cached = cache.get(sku)
        if (
            isinstance(cached, dict)
            and cached.get("gbpPrice")
            and cached.get("leaf")
            and not cached.get("_skip")
        ):
            # Fill missing images if needed
            if not cached.get("localImages"):
                cached = enrich_images(client, cached)
                cache[sku] = cached
                save_cache(cache)
            products.append(cached)
            leaf_counts[cached["leaf"]] += 1
            if i % 50 == 0:
                log(f"  cache hit progress {i}/{len(items)}")
            continue

        status, html = client.get_html(url, max_attempts=3)
        if is_challenge(html, status):
            consecutive_blocks += 1
            log(
                f"[{i}/{len(items)}] blocked {sku} "
                f"(streak={consecutive_blocks}, proxy={client._proxy}) — recovering"
            )
            client.clear_proxy()
            time.sleep(HARD_BLOCK_SLEEP)
            if not client.probe_direct():
                client.ensure_proxy()
            client.warm()
            # retry same SKU
            i -= 1
            if consecutive_blocks >= 12:
                log("Too many consecutive blocks — re-validating PDP access")
                if not wait_for_pdp_access(client, max_wait_s=600):
                    failed.append(
                        {"sku": sku, "url": url, "status": status, "reason": "akamai"}
                    )
                    consecutive_blocks = 0
                    i += 1  # skip this one after long wait failed
                else:
                    consecutive_blocks = 0
            continue

        consecutive_blocks = 0
        parsed = parse_pdp(html, url)
        if not parsed:
            failed.append({"sku": sku, "url": url, "status": status, "reason": "parse"})
            log(f"[{i}/{len(items)}] FAIL {sku} parse")
            continue
        if parsed.get("_skip"):
            skipped.append(parsed)
            cache[sku] = parsed
            log(f"[{i}/{len(items)}] skip {sku}: {parsed.get('reason')}")
            save_cache(cache)
            time.sleep(PDP_PAUSE)
            continue

        # Persist text first so a later image failure still keeps the PDP
        cache[sku] = parsed
        save_cache(cache)
        parsed = enrich_images(client, parsed)
        cache[sku] = parsed
        products.append(parsed)
        leaf_counts[parsed["leaf"]] += 1
        log(
            f"[{i}/{len(items)}] OK {sku} {parsed['leaf']} "
            f"£{parsed['gbpPrice']} imgs={len(parsed.get('localImages') or [])} "
            f"stock={parsed['inStock']}"
        )
        save_cache(cache)
        time.sleep(PDP_PAUSE)

    save_cache(cache)


    # Deduplicate by sku
    by_id: dict[str, dict] = {}
    for p in products:
        by_id[p["sku"]] = p
    products = sorted(by_id.values(), key=lambda p: p["sku"])

    collections_meta = {}
    for cid, meta in LEAF_META.items():
        n = sum(1 for p in products if cid in (p.get("collections") or []))
        collections_meta[cid] = {**meta, "count": n}

    payload = {
        "scrapedAt": datetime.now(timezone.utc).isoformat(),
        "source": HUB,
        "note": (
            "All the Looks (ch-women-looks) includes every imported RTW shape "
            "product — look PLP grids are often empty in SSR; garments also keep "
            "their primary shape leaf from hierarchy/categoryLabel."
        ),
        "collections": collections_meta,
        "count": len(products),
        "skippedCount": len(skipped),
        "failedCount": len(failed),
        "leafCounts": dict(leaf_counts),
        "skipped": skipped[:200],
        "failed": failed,
        "products": products,
    }
    OUT_RAW.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    log(
        f"Wrote {len(products)} products → {OUT_RAW} "
        f"(skipped={len(skipped)} failed={len(failed)})"
    )
    log(f"leafCounts={dict(leaf_counts)}")
    return 0 if products else 1


if __name__ == "__main__":
    raise SystemExit(main())
