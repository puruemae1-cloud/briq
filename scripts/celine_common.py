#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMG_ROOT = ROOT / "public" / "products" / "ce-pdp"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"
)
BASE = "https://www.celine.com"


def slugify(text: str, *, max_len: int = 80) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", (text or "").strip()).strip("-").lower()
    return s[:max_len].strip("-") or "item"


def _abs_url(url: str) -> str:
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return urllib.parse.urljoin(BASE, url)


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def load_json(path: Path, default):
    if path.is_file():
        return json.loads(path.read_text())
    return default


def fetch_size_guide_html(size_guide_url: str) -> str:
    if not size_guide_url:
        return ""
    req = urllib.request.Request(
        _abs_url(size_guide_url),
        headers={
            "User-Agent": UA,
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "ignore")


def extract_size_guide(size_guide_html: str) -> dict:
    if not size_guide_html:
        return {}
    headers = re.findall(r"<th[^>]*>\s*<span[^>]*>(.*?)</span>", size_guide_html, re.I | re.S)
    headers = [clean_html_text(h) for h in headers if clean_html_text(h)]
    rows: list[list[str]] = []
    for tr in re.findall(r"<tr[^>]*role=\"row\"[^>]*>(.*?)</tr>", size_guide_html, re.I | re.S):
        cells = re.findall(r"<td[^>]*role=\"cell\"[^>]*>(.*?)</td>", tr, re.I | re.S)
        vals: list[str] = []
        for cell in cells:
            cm_match = re.search(
                r"<span[^>]*data-msizestable-cm[^>]*>(.*?)</span>",
                cell,
                re.I | re.S,
            )
            plain_match = re.search(r"<span[^>]*>(.*?)</span>", cell, re.I | re.S)
            chosen = cm_match.group(1) if cm_match else (plain_match.group(1) if plain_match else "")
            txt = clean_html_text(chosen)
            if txt:
                vals.append(txt)
        if vals:
            rows.append(vals)
    return {
        "headers": headers,
        "rows": rows,
        "html": size_guide_html,
    }


def clean_html_text(text: str) -> str:
    s = re.sub(r"<br\s*/?>", "\n", text or "", flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("&nbsp;", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def normalize_image_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    base = raw.split("?")[0]
    if "image.celine.com/asset/" in base:
        return f"{base}?V2"
    return base


def filter_product_images(sku: str, remote_urls: list[str]) -> list[str]:
    sku_norm = (sku or "").strip().upper().replace(".", "-")
    out: list[str] = []
    seen: set[str] = set()
    for raw in remote_urls:
        url = normalize_image_url(raw)
        if not url or url in seen:
            continue
        seen.add(url)
        if sku_norm and sku_norm in url.upper():
            out.append(url)
    if out:
        return out
    return [normalize_image_url(u) for u in remote_urls if normalize_image_url(u)]


def download_image(url: str, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        normalize_image_url(url),
        headers={"User-Agent": UA},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        data = r.read()
    if len(data) < 800:
        return False
    dest.write_bytes(data)
    return True


def materialize_images(sku: str, remote_urls: list[str]) -> list[str]:
    folder = slugify(sku.replace(".", "-"))
    out: list[str] = []
    seen: set[str] = set()
    for i, raw in enumerate(remote_urls, start=1):
        url = normalize_image_url(raw)
        if not url or url in seen:
            continue
        seen.add(url)
        rel = f"/products/ce-pdp/{folder}/{i}.jpg"
        dest = IMG_ROOT / folder / f"{i}.jpg"
        try:
            if not dest.exists() or dest.stat().st_size < 800:
                ok = download_image(url, dest)
                if not ok:
                    continue
            out.append(rel)
        except Exception:
            continue
    return out


def with_browser(callback, *, headed: bool = False):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.webkit.launch(headless=not headed)
        ctx = browser.new_context(
            locale="en-GB",
            viewport={"width": 1440, "height": 1600},
            user_agent=UA,
            extra_http_headers={"Accept-Language": "en-GB,en;q=0.9"},
        )
        page = ctx.new_page()
        try:
            return callback(page)
        finally:
            browser.close()


def accept_cookies(page) -> None:
    for sel in (
        "#onetrust-accept-btn-handler",
        'button:has-text("ACCEPT ALL")',
        'button:has-text("Accept All")',
    ):
        try:
            page.locator(sel).first.click(timeout=1500)
            page.wait_for_timeout(200)
            return
        except Exception:
            pass


def scrape_plp_cards(page, url: str) -> list[dict]:
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    accept_cookies(page)
    page.wait_for_timeout(200)

    stable_rounds = 0
    last_count = -1
    for _ in range(18):
        try:
            for sel in (
                'button:has-text("Load more")',
                'button:has-text("Show more")',
                'button:has-text("View more")',
                'a:has-text("Load more")',
                '[data-testid="load-more"]',
            ):
                btn = page.locator(sel).first
                if btn.count() and btn.is_visible():
                    btn.click(timeout=1200)
                    page.wait_for_timeout(220)
                    break
        except Exception:
            pass
        try:
            page.mouse.wheel(0, 22000)
        except Exception:
            pass
        page.wait_for_timeout(120)
        count = page.locator("[data-pid]").count()
        if count == last_count:
            stable_rounds += 1
            if stable_rounds >= 2:
                break
        else:
            stable_rounds = 0
            last_count = count
    cards = page.eval_on_selector_all(
        "[data-pid]",
        """
        els => {
          const out = [];
          const seen = new Set();
          for (const el of els) {
            const pid = (el.getAttribute('data-pid') || '').trim();
            const a = el.querySelector('a[href*=".html"], a[href*="/en-gb/"]');
            if (!pid || !a) continue;
            const href = a.href || '';
            if (!href || seen.has(pid)) continue;
            seen.add(pid);
            const text = (el.textContent || '').replace(/\\s+/g, ' ').trim();
            const m = text.match(/([0-9][0-9,]*)\\s*GBP/i) || text.match(/£\\s*([0-9][0-9,]*(?:\\.[0-9]{2})?)/);
            out.push({
              id: pid,
              href,
              text,
              gbpPrice: m ? Number(m[1].replace(/,/g, '')) : null,
            });
          }
          return out;
        }
        """,
    )
    return cards or []


def paginated_plp_urls(url: str, *, pages: int = 6, page_size: int = 24) -> list[str]:
    """Emit SFCC-style start/sz pagination URLs for a PLP hub."""
    base = url.split("#")[0]
    out = [base]
    joiner = "&" if "?" in base else "?"
    for i in range(1, max(1, pages)):
        start = i * page_size
        out.append(f"{base}{joiner}start={start}&sz={page_size}")
    # de-dupe preserving order
    seen: set[str] = set()
    uniq: list[str] = []
    for u in out:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq


def scrape_pdp(page, url: str) -> dict:
    page.goto(url, wait_until="domcontentloaded", timeout=90000)
    accept_cookies(page)
    page.wait_for_timeout(400)
    data = page.evaluate(
        """
        () => {
          const text = (sel) => {
            const el = document.querySelector(sel);
            return (el?.textContent || '').replace(/\\s+/g, ' ').trim();
          };
          const allText = (sel) =>
            Array.from(document.querySelectorAll(sel))
              .map((el) => (el.textContent || '').replace(/\\s+/g, ' ').trim())
              .filter(Boolean);
          const images = Array.from(document.querySelectorAll('img'))
            .map((img) => ({
              src: img.currentSrc || img.src || '',
              alt: img.alt || '',
              w: img.naturalWidth || 0,
              h: img.naturalHeight || 0,
            }))
            .filter((x) => x.src && x.src.includes('image.celine.com/asset/'))
            .map((x) => x.src);
          const uniqImages = Array.from(new Set(images));
          const details = Array.from(document.querySelectorAll('.o-product__descriptions .m-accordion__item')).map((item) => {
            const btn = item.querySelector('button');
            const panel = item.querySelector('.m-accordion__panel');
            return {
              label: (btn?.textContent || '').replace(/\\s+/g, ' ').trim(),
              body: (panel?.textContent || '').replace(/\\s+/g, ' ').trim(),
              html: panel?.innerHTML || '',
            };
          });
          const sizes = Array.from(document.querySelectorAll('.m-selector__list button, .m-selector__list [data-value], .m-selector button'))
            .map((el) => (el.textContent || '').replace(/\\s+/g, ' ').trim())
            .filter((t) => /^(XXXS|XXS|XS|S|M|L|XL|XXL|XXXL|[0-9]{2}(?:\\.[0-9])?)$/i.test(t));
          const sizeGuideBtn = document.querySelector('#main-size-guide');
          return {
            sku: document.documentElement.getAttribute('data-sku') || text('.product-id'),
            categoryLabel: document.documentElement.getAttribute('data-category') || '',
            title: text('h1'),
            priceText: text('.o-product__price, .a-price, [data-gtm-track-interaction-type="add to cart"]'),
            color: text('.m-selector__current-value, .o-product__current-color, .o-product__color-name'),
            availability: document.body.innerText.includes('AVAILABLE NOW'),
            images: uniqImages,
            details,
            sizes: Array.from(new Set(sizes)),
            breadcrumb: allText('.m-breadcrumb a, .m-breadcrumb span'),
            sizeGuideUrl: sizeGuideBtn?.getAttribute('data-size-guide-url') || '',
          };
        }
        """,
    )
    return data or {}


def parse_gbp(text: str | None) -> float:
    m = re.search(r"([0-9][0-9,]*)\s*GBP", text or "", re.I)
    if not m:
        return 0.0
    return float(m.group(1).replace(",", ""))


def scrape_leaf_rows(leaf: dict, *, headed: bool = False, limit: int = 0, skip_ids: set[str] | None = None) -> list[dict]:
    skip = {str(x).strip().lower() for x in (skip_ids or set()) if str(x).strip()}
    pages = int(leaf.get("pages") or 5)
    page_size = int(leaf.get("pageSize") or 24)

    def run(page):
        seen_cards: dict[str, dict] = {}
        empty_pages = 0
        for plp_url in paginated_plp_urls(leaf["url"], pages=pages, page_size=page_size):
            before = len(seen_cards)
            for card in scrape_plp_cards(page, plp_url):
                cid = str(card.get("id") or "").strip()
                if not cid:
                    continue
                key = cid.lower()
                if key in seen_cards:
                    continue
                seen_cards[key] = card
            gained = len(seen_cards) - before
            if gained == 0:
                empty_pages += 1
                if empty_pages >= 2:
                    break
            else:
                empty_pages = 0
        cards = list(seen_cards.values())
        rows = []
        seen = 0
        for card in cards:
            cid = str(card.get("id") or "").strip()
            if cid and cid.lower() in skip:
                continue
            seen += 1
            if limit and seen > limit:
                break
            pdp = scrape_pdp(page, card["href"])
            sku = (pdp.get("sku") or card.get("id") or "").strip()
            remote_images = filter_product_images(sku or card["id"], pdp.get("images") or [])
            local_images = materialize_images(sku or card["id"], remote_images)
            size_guide_url = pdp.get("sizeGuideUrl") or ""
            size_guide_html = fetch_size_guide_html(size_guide_url) if size_guide_url else ""
            size_guide = extract_size_guide(size_guide_html)
            sizes = pdp.get("sizes") or []
            if not sizes and size_guide.get("rows"):
                sizes = [str(row[0]).strip() for row in size_guide["rows"] if row]
            rows.append(
                {
                    "id": sku or card["id"],
                    "sku": sku or card["id"],
                    "title": (pdp.get("title") or "").strip(),
                    "gbpPrice": parse_gbp(pdp.get("priceText")) or float(card.get("gbpPrice") or 0),
                    "url": card["href"],
                    "leafId": leaf["id"],
                    "leafLabel": leaf.get("label") or "",
                    "leafLabelKo": leaf.get("leafLabelKo") or leaf.get("labelKo") or "",
                    "collections": list(dict.fromkeys(leaf.get("collections") or [leaf["id"]])),
                    "color": {"label": pdp.get("color") or ""},
                    "details": pdp.get("details") or [],
                    "sizes": sizes,
                    "sizeGuideUrl": size_guide_url,
                    "sizeGuide": size_guide,
                    "images": local_images,
                    "remoteImages": remote_images,
                    "availability": bool(pdp.get("availability")),
                    "breadcrumb": pdp.get("breadcrumb") or [],
                    "categoryLabel": pdp.get("categoryLabel") or "",
                }
            )
        return rows

    return with_browser(run, headed=headed)
