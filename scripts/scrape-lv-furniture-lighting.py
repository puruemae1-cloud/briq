#!/usr/bin/env python3
"""Scrape Louis Vuitton GB Home → Furniture & Lighting via Playwright.

Akamai blocks Chromium/curl. Default engine is WebKit (Safari) which usually
passes when Safari itself can open LV.

  python3 -m playwright install webkit
  python3 scripts/scrape-lv-furniture-lighting.py --discover-only
  python3 scripts/scrape-lv-furniture-lighting.py

  python3 scripts/build-lv-catalog.py
  python3 scripts/check-catalog-korean.py --brand lv --fail
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lv_common import (  # noqa: E402
    BASE,
    LANG,
    IMG_ROOT,
    discover_furniture_leaves,
    download_image,
    extract_next_data,
    leaf_id_from_slug,
    normalize_image_list,
    slugify,
)

OUT_RAW = ROOT / "src/data/lv/lv-furniture-catalog-raw.json"
OUT_LEAVES = ROOT / "src/data/lv/lv-furniture-leaves.json"
PDP_CACHE = ROOT / "src/data/lv/lv-furniture-pdp-cache.json"
PROFILE_DIR = ROOT / ".cache" / "lv-playwright-profile"

HUB_URL = (
    f"{BASE}/{LANG}/home-lifestyle-and-library/furniture-and-lighting/"
    "all-furniture-and-lighting/_/N-t1p0t69l"
)

DEFAULT_LEAVES: list[dict[str, str]] = [
    {
        "id": "lv-furniture-lighting-all",
        "slug": "all-furniture-and-lighting",
        "code": "t1p0t69l",
        "label": "All Furniture and Lighting",
        "labelKo": "전체",
        "url": HUB_URL,
    },
]

PARENT_COLS = [
    "louis-vuitton",
    "louis-vuitton-accessories",
    "lv-home-lifestyle",
    "lv-furniture-lighting",
]

# Known / likely furniture sub-PLPs (filled further by discovery).
SEED_SUBLEAVES: list[tuple[str, str, str]] = [
    ("lv-seating", "Seating", "시팅"),
    ("lv-tables", "Tables", "테이블"),
    ("lv-lighting", "Lighting", "라이트닝"),
    ("lv-storage", "Storage", "수납 · 사이드보드"),
]

PDP_PAUSE = 1.2
CHALLENGE_WAIT_S = 120


class ListHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.paras: list[str] = []
        self.bullets: list[str] = []
        self._buf: list[str] = []
        self._in_li = False
        self._in_p = False

    def handle_starttag(self, tag, attrs):
        if tag == "li":
            self._in_li = True
            self._buf = []
        elif tag == "p":
            self._in_p = True
            self._buf = []

    def handle_endtag(self, tag):
        if tag == "li" and self._in_li:
            text = re.sub(r"\s+", " ", "".join(self._buf)).strip()
            if text:
                self.bullets.append(text)
            self._in_li = False
        elif tag == "p" and self._in_p:
            text = re.sub(r"\s+", " ", "".join(self._buf)).strip()
            if text:
                self.paras.append(text)
            self._in_p = False

    def handle_data(self, data):
        if self._in_li or self._in_p:
            self._buf.append(data)


def parse_html_body(html: str) -> tuple[list[str], list[str]]:
    p = ListHTMLParser()
    try:
        p.feed(html or "")
    except Exception:
        pass
    return p.paras, p.bullets


def log(msg: str) -> None:
    print(msg, flush=True)


def launch_browser(headed: bool, persist: bool, engine: str = "webkit"):
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    # Safari works for the user; Chromium is often blocked by LV Akamai.
    browser_type = pw.webkit if engine == "webkit" else pw.chromium
    launch_kwargs = {
        "headless": not headed,
    }
    ua = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.4 Safari/605.1.15"
        if engine == "webkit"
        else (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        )
    )

    if persist and engine == "chromium":
        # Persistent context is Chromium-only in Playwright.
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        ctx = pw.chromium.launch_persistent_context(
            str(PROFILE_DIR),
            headless=not headed,
            locale="en-GB",
            viewport={"width": 1440, "height": 900},
            user_agent=ua,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        return pw, ctx, page, True

    browser = browser_type.launch(**launch_kwargs)
    ctx = browser.new_context(
        locale="en-GB",
        viewport={"width": 1440, "height": 900},
        user_agent=ua,
    )
    page = ctx.new_page()
    return pw, browser, page, False


def page_is_denied(html: str) -> bool:
    low = (html or "").lower()
    return "access denied" in low or "accès refusé" in low


def wait_for_real_page(page, timeout_s: int = CHALLENGE_WAIT_S) -> str:
    """Wait until Akamai challenge / waiting room clears.

    In headed mode, Access Denied does NOT abort immediately — the script
    pauses so you can open the same URL in Safari (or refresh the WebKit
    window), then press Enter to keep waiting.
    """
    deadline = time.time() + timeout_s
    denied_streak = 0
    while time.time() < deadline:
        html = page.content()
        title = page.title() or ""
        if page_is_denied(html):
            denied_streak += 1
            log(
                f"  Access Denied (streak {denied_streak}). "
                "창을 닫지 마세요 — 계속 Denied면 Safari로 LV 접속 가능 여부를 확인하세요."
            )
            # Don't abort on first flash; some challenges briefly show denied.
            if denied_streak >= 4:
                log("")
                log("=== LV가 이 브라우저를 막고 있습니다 ===")
                log("1) Safari에서 https://uk.louisvuitton.com 을 열고 상품이 보이는지 확인")
                log("2) 보이면 Safari는 그대로 두고, 이 스크립트 창에서 주소창 URL을 새로고침")
                log("3) 안 보이면 15~30분 쉬었다가 다시 실행")
                log("준비되면 이 터미널에서 Enter (계속 대기). 포기하려면 q + Enter")
                try:
                    ans = input().strip().lower()
                except EOFError:
                    ans = "q"
                if ans in {"q", "quit", "exit"}:
                    raise RuntimeError(
                        "LV Access Denied — Safari에서도 막히면 나중에 다시 시도하세요."
                    )
                denied_streak = 0
                deadline = time.time() + timeout_s
                try:
                    page.reload(wait_until="domcontentloaded", timeout=60000)
                except Exception:
                    pass
                page.wait_for_timeout(2000)
                continue
            page.wait_for_timeout(3000)
            continue
        denied_streak = 0
        challenge = (
            "sec-if-cpt" in html
            or "lv-waiting" in html
            or "behavioral-content" in html
        )
        has_shop = (
            "__NEXT_DATA__" in html
            or "nvprod" in html.lower()
            or page.locator('a[href*="/products/"]').count() > 0
            or page.locator(
                "[data-testid*='product'], .lv-product-card, .productItem"
            ).count()
            > 0
            or page.locator("h1").count() > 0
        )
        if has_shop and not challenge:
            log("  page ready")
            return html
        if challenge:
            log("  waiting for Akamai challenge… (브라우저 창을 닫지 마세요)")
        else:
            log(f"  waiting for products… title={title!r} len={len(html)}")
        page.wait_for_timeout(2500)
        try:
            page.mouse.wheel(0, 800)
        except Exception:
            pass
    raise RuntimeError(
        "Timed out waiting for LV catalogue HTML. "
        "브라우저 창에 보안 확인이 보이면 클릭한 뒤 다시 실행하세요."
    )


def keep_open_if_headed(headed: bool, reason: str) -> None:
    """Prevent the window from vanishing before the user can read it."""
    if not headed:
        return
    log("")
    log(f"=== 창을 유지합니다: {reason} ===")
    log("Chromium 창에서 화면을 확인하세요.")
    log("확인이 끝나면 이 터미널로 돌아와 Enter 를 누르세요 (창이 닫힙니다).")
    try:
        input()
    except EOFError:
        log("(입력 불가 — 90초 대기 후 종료)")
        time.sleep(90)


def attach_api_sniffer(page) -> list[dict]:
    """Capture JSON catalog payloads from LV APIs."""
    hits: list[dict] = []

    def on_response(resp) -> None:
        try:
            url = resp.url
            if resp.status != 200:
                return
            if not any(
                k in url
                for k in (
                    "search-merch",
                    "catalog",
                    "products",
                    "product",
                    "plp",
                    "eco-eu",
                )
            ):
                return
            ctype = (resp.headers.get("content-type") or "").lower()
            if "json" not in ctype and "javascript" not in ctype:
                return
            data = resp.json()
            hits.append({"url": url, "data": data})
        except Exception:
            return

    page.on("response", on_response)
    return hits


def walk_products(node, out: list[dict], *, depth: int = 0) -> None:
    if depth > 16 or node is None:
        return
    if isinstance(node, dict):
        pid = (
            node.get("identifier")
            or node.get("productId")
            or node.get("id")
            or node.get("sku")
        )
        name = node.get("name") or node.get("title") or node.get("displayName")
        url = (
            node.get("url")
            or node.get("productUrl")
            or node.get("link")
            or node.get("pdpUrl")
        )
        price = (
            node.get("price")
            or node.get("salePrice")
            or node.get("listPrice")
            or node.get("prices")
        )
        looks_product = bool(pid and name) and (
            "nvprod" in str(pid).lower()
            or (isinstance(url, str) and "/products/" in url)
            or node.get("productType")
            or node.get("macroCategory")
        )
        if looks_product:
            gbp = None
            if isinstance(price, dict):
                gbp = (
                    price.get("value")
                    or price.get("amount")
                    or (price.get("currencyValue") or {}).get("value")
                )
            elif isinstance(price, list) and price:
                first = price[0]
                if isinstance(first, dict):
                    gbp = first.get("value") or first.get("amount")
            elif isinstance(price, (int, float)):
                gbp = price
            out.append(
                {
                    "id": str(pid),
                    "title": str(name).strip(),
                    "url": url,
                    "gbpPrice": gbp,
                }
            )
        for v in node.values():
            walk_products(v, out, depth=depth + 1)
    elif isinstance(node, list):
        for item in node:
            walk_products(item, out, depth=depth + 1)


def normalize_product_url(url: str | None) -> str | None:
    if not url:
        return None
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("/"):
        return f"{BASE}{url}"
    if url.startswith("http"):
        return url
    return f"{BASE}/{LANG}/{url.lstrip('/')}"


def extract_plp_from_html(html: str) -> list[dict]:
    products: list[dict] = []
    data = extract_next_data(html)
    if data:
        walk_products(data, products)

    for m in re.finditer(
        rf'(?:https://uk\.louisvuitton\.com)?/{LANG}/[^"\']*?/products/([^/"\']+)/_/(?:[^"\'?\s]+)',
        html,
        re.I,
    ):
        slug = m.group(1)
        full = m.group(0)
        url = normalize_product_url(full)
        if not any(p.get("url") == url for p in products):
            products.append(
                {
                    "id": slug,
                    "title": slug.replace("-", " ").title(),
                    "url": url,
                }
            )

    for m in re.finditer(r"\bnvprod[a-z0-9]+\b", html, re.I):
        pid = m.group(0)
        if not any(p.get("id") == pid for p in products):
            products.append({"id": pid, "title": pid, "url": None})

    seen: set[str] = set()
    uniq: list[dict] = []
    for p in products:
        key = str(p.get("url") or p.get("id"))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(p)
    return uniq


def extract_plp_from_api(hits: list[dict]) -> list[dict]:
    products: list[dict] = []
    for hit in hits:
        walk_products(hit.get("data"), products)
    seen: set[str] = set()
    uniq: list[dict] = []
    for p in products:
        key = str(p.get("url") or p.get("id"))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(p)
    return uniq


def extract_json_ld_product(html: str) -> dict:
    out: dict = {}
    for m in re.finditer(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>([\s\S]*?)</script>',
        html,
        re.I,
    ):
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        nodes = data if isinstance(data, list) else [data]
        for node in nodes:
            if not isinstance(node, dict):
                continue
            types = node.get("@type")
            type_l = (
                [types]
                if isinstance(types, str)
                else list(types or [])
                if isinstance(types, list)
                else []
            )
            if any(str(t).lower() == "product" for t in type_l):
                out = node
                break
        if out:
            break
    return out


def extract_pdp_details(html: str) -> dict:
    data = extract_next_data(html) or {}
    page = (data.get("props") or {}).get("pageProps") or {}
    product = (
        page.get("product")
        or (page.get("initialData") or {}).get("product")
        or page.get("productDetailed")
        or {}
    )
    if not isinstance(product, dict) or not (
        product.get("name") or product.get("description") or product.get("medias")
    ):
        # Deep-search pageProps for a product-like dict
        found: list[dict] = []

        def walk(node, depth=0):
            if depth > 10 or node is None:
                return
            if isinstance(node, dict):
                if node.get("name") and (
                    node.get("description")
                    or node.get("longDescription")
                    or node.get("medias")
                    or node.get("images")
                ):
                    found.append(node)
                for v in node.values():
                    walk(v, depth + 1)
            elif isinstance(node, list):
                for v in node[:50]:
                    walk(v, depth + 1)

        walk(page)
        if found:
            product = found[0]
    if not isinstance(product, dict):
        product = {}

    ld = extract_json_ld_product(html)

    title = (
        product.get("name")
        or product.get("title")
        or ld.get("name")
        or page.get("title")
        or ""
    )
    if not title:
        m = re.search(
            r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)',
            html,
            re.I,
        ) or re.search(
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:title["\']',
            html,
            re.I,
        )
        if m:
            title = m.group(1)
        else:
            m = re.search(r"<h1[^>]*>([^<]+)</h1>", html, re.I)
            if m:
                title = m.group(1)
    title = re.sub(r"\s*\|\s*Louis Vuitton.*$", "", str(title), flags=re.I).strip()

    desc_html = (
        product.get("description")
        or product.get("longDescription")
        or product.get("detailedDescription")
        or product.get("details")
        or ld.get("description")
        or ""
    )
    if isinstance(desc_html, dict):
        desc_html = desc_html.get("html") or desc_html.get("content") or ""
    if not desc_html:
        m = re.search(
            r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)',
            html,
            re.I,
        ) or re.search(
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']description["\']',
            html,
            re.I,
        )
        if m:
            desc_html = m.group(1)

    paras, bullets = parse_html_body(str(desc_html))
    if not paras and isinstance(desc_html, str) and desc_html.strip():
        # plain text description
        text = re.sub(r"<[^>]+>", " ", desc_html)
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            paras = [text]

    images: list[str] = []
    for key in ("images", "medias", "gallery", "visuals", "assets", "image"):
        block = product.get(key)
        if isinstance(block, str):
            images.append(block)
        elif isinstance(block, list):
            for item in block:
                if isinstance(item, str) and item.startswith("http"):
                    images.append(item)
                elif isinstance(item, dict):
                    u = item.get("url") or item.get("src") or item.get("href")
                    if u:
                        images.append(str(u))
    if isinstance(ld.get("image"), str):
        images.append(ld["image"])
    elif isinstance(ld.get("image"), list):
        images.extend(str(x) for x in ld["image"] if x)

    # og:image / img CDN fallbacks
    for m in re.finditer(
        r'(https://[^"\']+(?:louisvuitton|/images/is/image/lv)[^"\']+\.(?:jpg|jpeg|png|webp)[^"\']*)',
        html,
        re.I,
    ):
        u = m.group(1)
        if "favicon" in u.lower():
            continue
        if u not in images:
            images.append(u)
    # also catch Scene7 urls without extension in path
    for m in re.finditer(
        r'(https://uk\.louisvuitton\.com/images/is/image/lv/[^"\'\s]+)',
        html,
        re.I,
    ):
        u = m.group(1)
        if u not in images:
            images.append(u)

    gbp = None
    price = product.get("price") or product.get("salePrice") or product.get("listPrice")
    if isinstance(price, dict):
        gbp = price.get("value") or price.get("amount")
    elif isinstance(price, (int, float)):
        gbp = price
    else:
        m = re.search(r"[£]\s*([\d,]+(?:\.\d+)?)", html)
        if m:
            gbp = float(m.group(1).replace(",", ""))

    specs: list[dict[str, str]] = []
    for key in ("specifications", "attributes", "characteristics", "detailsList"):
        block = product.get(key)
        if isinstance(block, list):
            for row in block:
                if isinstance(row, dict):
                    label = row.get("label") or row.get("name") or row.get("key")
                    val = row.get("value") or row.get("text")
                    if label and val:
                        specs.append({"label": str(label), "value": str(val)})

    sku = product.get("sku") or product.get("identifier") or product.get("productId")

    return {
        "title": str(title).strip(),
        "descriptionHtml": str(desc_html),
        "paragraphs": paras,
        "bullets": bullets,
        "images": normalize_image_list(images, limit=40),
        "gbpPrice": gbp,
        "sku": sku,
        "specs": specs,
    }


def download_gallery(images: list[str], folder: Path) -> list[str]:
    paths: list[str] = []
    cleaned = normalize_image_list(list(images or []), limit=24)
    for i, url in enumerate(cleaned, start=1):
        dest = folder / f"{i}.jpg"
        try:
            ok = download_image(url, dest)
        except Exception as e:
            log(f"    image skip: {e}")
            ok = False
        if ok:
            rel = "/" + dest.relative_to(ROOT / "public").as_posix()
            paths.append(rel)
            if len(paths) >= 16:
                break
    return paths


def fetch_html(page, url: str, api_hits: list[dict]) -> str:
    api_hits.clear()
    log(f"  goto {url}")
    page.goto(url, wait_until="domcontentloaded", timeout=90000)
    return wait_for_real_page(page)


def build_leaf_list(hub_html: str) -> list[dict]:
    leaves = {x["id"]: dict(x) for x in DEFAULT_LEAVES}
    for row in discover_furniture_leaves(hub_html):
        lid = row["id"]
        if lid not in leaves:
            row.setdefault("label", row["slug"].replace("-", " ").title())
            row.setdefault("labelKo", row["label"])
            leaves[lid] = row

    # Map discovered slugs onto seeded Korean labels when possible.
    slug_to_seed = {
        "seating": ("lv-seating", "Seating", "시팅"),
        "chairs": ("lv-seating", "Seating", "시팅"),
        "sofas": ("lv-seating", "Seating", "시팅"),
        "tables": ("lv-tables", "Tables", "테이블"),
        "lighting": ("lv-lighting", "Lighting", "라이트닝"),
        "lamps": ("lv-lighting", "Lighting", "라이트닝"),
        "storage": ("lv-storage", "Storage", "수납 · 사이드보드"),
        "sideboards": ("lv-storage", "Storage", "수납 · 사이드보드"),
    }
    for leaf in list(leaves.values()):
        slug = (leaf.get("slug") or "").lower()
        for key, (lid, en, ko) in slug_to_seed.items():
            if key in slug and leaf["id"] != "lv-furniture-lighting-all":
                leaf["id"] = lid
                leaf["label"] = en
                leaf["labelKo"] = ko
                leaves[lid] = leaf

    return list({v["id"]: v for v in leaves.values()}.values())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--discover-only", action="store_true")
    ap.add_argument(
        "--headed",
        action="store_true",
        default=True,
        help="Show Chromium window (default on — needed for Akamai)",
    )
    ap.add_argument("--headless", action="store_true", help="Force headless (often blocked)")
    ap.add_argument(
        "--persist",
        action="store_true",
        help=f"Reuse browser profile at {PROFILE_DIR}",
    )
    ap.add_argument("--max-pdp", type=int, default=0, help="Limit PDPs (0=all)")
    ap.add_argument(
        "--engine",
        choices=("webkit", "chromium"),
        default="webkit",
        help="Browser engine (default: webkit/Safari — Chromium is often blocked by LV)",
    )
    args = ap.parse_args()
    headed = not args.headless

    log(f"Starting Playwright {args.engine}…")
    log("브라우저 창이 뜹니다. 에러가 나도 Enter 치기 전까지 창이 유지됩니다.")
    if args.engine == "webkit":
        log("Safari 엔진(WebKit) 사용 — LV가 Chromium만 막는 경우에 유효합니다.")
    pw, browser_or_ctx, page, persistent = launch_browser(
        headed, args.persist, engine=args.engine
    )
    api_hits = attach_api_sniffer(page)
    exit_code = 1

    try:
        try:
            hub_html = fetch_html(page, HUB_URL, api_hits)
        except Exception as e:
            log(f"ERROR: {e}")
            try:
                shot = ROOT / ".cache" / "lv-last-screen.png"
                shot.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(shot), full_page=True)
                log(f"screenshot → {shot}")
            except Exception:
                pass
            keep_open_if_headed(headed, str(e))
            return 1

        leaf_list = build_leaf_list(hub_html)
        OUT_LEAVES.write_text(
            json.dumps(leaf_list, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        log(f"Leaves: {len(leaf_list)} → {OUT_LEAVES.relative_to(ROOT)}")
        for leaf in leaf_list:
            log(f"  {leaf['id']}: {leaf.get('url')}")
        if args.discover_only:
            keep_open_if_headed(headed, "discover-only 완료 — 페이지가 정상인지 확인")
            return 0

        cache: dict = {}
        if PDP_CACHE.is_file():
            cache = json.loads(PDP_CACHE.read_text(encoding="utf-8"))

        all_products: list[dict] = []
        seen_ids: set[str] = set()

        for leaf in leaf_list:
            leaf_id = leaf["id"]
            url = leaf["url"]
            log(f"\n=== {leaf_id} ===")
            try:
                html = fetch_html(page, url, api_hits)
            except Exception as e:
                log(f"  skip leaf: {e}")
                continue

            plp = extract_plp_from_html(html)
            plp_api = extract_plp_from_api(api_hits)
            by_key: dict[str, dict] = {}
            for row in plp + plp_api:
                key = str(row.get("url") or row.get("id"))
                by_key[key] = {
                    **by_key.get(key, {}),
                    **{k: v for k, v in row.items() if v},
                }
            plp = list(by_key.values())
            log(f"  PLP candidates: {len(plp)} (html+api)")

            if args.max_pdp:
                plp = plp[: args.max_pdp]

            for row in plp:
                pdp_url = normalize_product_url(row.get("url"))
                pid_hint = str(row.get("id") or "")
                if not pdp_url and pid_hint.startswith("nvprod"):
                    href = page.locator(f'a[href*="{pid_hint}"]').first
                    try:
                        if href.count():
                            pdp_url = normalize_product_url(href.get_attribute("href"))
                    except Exception:
                        pass
                if not pdp_url:
                    log(f"  skip no URL for {pid_hint}")
                    continue

                if pdp_url in cache:
                    details = cache[pdp_url]
                else:
                    try:
                        pdp_html = fetch_html(page, pdp_url, api_hits)
                        details = extract_pdp_details(pdp_html)
                        details["url"] = pdp_url
                        cache[pdp_url] = details
                        time.sleep(PDP_PAUSE)
                    except Exception as e:
                        log(f"  PDP fail {pdp_url}: {e}")
                        continue

                title = details.get("title") or row.get("title") or row.get("id")
                sku = details.get("sku") or row.get("id") or slugify(str(title))
                sku_s = str(sku)
                if sku_s in seen_ids:
                    for existing in all_products:
                        if existing["id"] == sku_s:
                            cols = set(existing.get("collections") or [])
                            cols.add(leaf_id)
                            existing["collections"] = sorted(cols)
                    continue
                seen_ids.add(sku_s)

                folder = IMG_ROOT / slugify(sku_s)
                images = download_gallery(details.get("images") or [], folder)
                product = {
                    "id": sku_s,
                    "title": title,
                    "gbpPrice": details.get("gbpPrice") or row.get("gbpPrice"),
                    "url": pdp_url,
                    "leafId": leaf_id,
                    "leafLabel": leaf.get("label"),
                    "leafLabelKo": leaf.get("labelKo"),
                    "collections": [*PARENT_COLS, leaf_id],
                    "details": {
                        "paragraphs": details.get("paragraphs") or [],
                        "bullets": details.get("bullets") or [],
                        "specs": details.get("specs") or [],
                        "descriptionHtml": details.get("descriptionHtml") or "",
                    },
                    "images": images,
                }
                all_products.append(product)
                log(f"  + {product['id']} ({len(images)} imgs) £{product.get('gbpPrice')}")

        PDP_CACHE.write_text(
            json.dumps(cache, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        payload = {
            "scrapedAt": datetime.now(timezone.utc).isoformat(),
            "hub": HUB_URL,
            "leaves": leaf_list,
            "products": all_products,
        }
        OUT_RAW.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        log(f"\nWrote {len(all_products)} products → {OUT_RAW.relative_to(ROOT)}")
        if not all_products:
            keep_open_if_headed(
                headed,
                "상품 0개 — Chromium 화면에 Access Denied / 보안체크가 있는지 확인",
            )
            exit_code = 1
        else:
            exit_code = 0
        return exit_code
    finally:
        try:
            browser_or_ctx.close()
        except Exception:
            pass
        try:
            pw.stop()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
