#!/usr/bin/env python3
"""Mulberry GB scrape helpers (Playwright — site blocks naive HTTP)."""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMG_ROOT = ROOT / "public" / "products" / "mb-pdp"
RAW_DIR = ROOT / "src" / "data" / "mb"
BASE = "https://www.mulberry.com"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"
)


def slugify(text: str, *, max_len: int = 80) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", (text or "").strip()).strip("-").lower()
    return s[:max_len].strip("-") or "item"


def abs_url(url: str) -> str:
    if not url:
        return ""
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


def clean_text(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = s.replace("\xa0", " ").replace("&amp;", "&").replace("&nbsp;", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_gbp(text: str) -> float:
    m = re.search(r"£\s*([0-9,]+(?:\.[0-9]+)?)", text or "")
    if not m:
        m = re.search(r"([0-9,]+(?:\.[0-9]+)?)", text or "")
    if not m:
        return 0.0
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return 0.0


def _accept_cookies(page) -> None:
    try:
        page.locator("#onetrust-accept-btn-handler").click(timeout=2500)
        page.wait_for_timeout(400)
    except Exception:
        pass


def _new_page(playwright):
    browser = playwright.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent=UA, locale="en-GB")
    page = ctx.new_page()
    return browser, page


def product_url_from_link(link: str) -> str:
    """Normalise Mulberry relative/absolute PDP links to https://www.mulberry.com/gb/..."""
    link = (link or "").split("?")[0].strip()
    if not link:
        return ""
    if link.startswith("http://") or link.startswith("https://"):
        href = link
    elif link.startswith("/gb/"):
        href = abs_url(link)
    elif link.startswith("/"):
        # Algolia returns /shop/... without the /gb locale prefix.
        href = abs_url("/gb" + link)
    else:
        href = abs_url("/gb/" + link.lstrip("/"))
    return href.split("?")[0]


def algolia_image_url(image_field: str) -> str:
    """Build a CDN URL from an Algolia `image` token (e.g. HH0197_771A110_L?v=)."""
    raw = (image_field or "").split("?")[0].strip()
    if not raw:
        return ""
    if raw.startswith("http://") or raw.startswith("https://"):
        return normalize_image(raw)
    code = raw if raw.startswith("G_") else f"G_{raw}"
    return normalize_image(f"https://images.mulberry.com/i/mulberrygroup/{code}")


def _algolia_paginate(req_url: str, body_text: str) -> tuple[list[dict], int]:
    """Fetch every Algolia page for a captured PLP query. Returns (hits, nbHits)."""
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(req_url).query)
    app = (qs.get("x-algolia-application-id") or [None])[0]
    key = (qs.get("x-algolia-api-key") or [None])[0]
    if not app or not key:
        raise RuntimeError("Algolia credentials missing from intercepted request URL")

    body = json.loads(body_text)
    requests = body.get("requests") or []
    if not requests:
        raise RuntimeError("Algolia body has no requests")
    index = requests[0].get("indexName") or "UK_EN"
    base_params = requests[0].get("params") or ""
    flat = {k: v[0] for k, v in urllib.parse.parse_qs(base_params).items()}
    flat["hitsPerPage"] = "72"

    endpoint = f"https://{app}-dsn.algolia.net/1/indexes/*/queries"
    all_hits: list[dict] = []
    nb_hits = 0
    nb_pages = 1
    for page_n in range(40):
        flat["page"] = str(page_n)
        req_body = {
            "requests": [
                {"indexName": index, "params": urllib.parse.urlencode(flat)}
            ]
        }
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(req_body).encode(),
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-Algolia-Application-Id": app,
                "X-Algolia-API-Key": key,
                "User-Agent": UA,
            },
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            out = json.loads(resp.read().decode())
        r0 = (out.get("results") or [{}])[0]
        hits = r0.get("hits") or []
        nb_hits = int(r0.get("nbHits") or 0)
        nb_pages = int(r0.get("nbPages") or 0) or 1
        all_hits.extend(hits)
        if page_n + 1 >= nb_pages:
            break
    return all_hits, nb_hits


def _scrape_plp_dom(page, *, max_scroll: int = 28) -> list[dict]:
    """Legacy DOM fallback when Algolia interception fails."""
    for _ in range(max_scroll):
        page.mouse.wheel(0, 4200)
        page.wait_for_timeout(550)
    items = page.eval_on_selector_all(
        ".list-item.product",
        """els => els.map(el => {
          const a = el.querySelector('a.link-product, a.list-item__figure, a[href]');
          const title = (el.querySelector('.list-item__title')||{}).innerText||'';
          const price = (el.querySelector('.list-item__price')||{}).innerText||'';
          const img = el.querySelector('img');
          return {
            href: a && a.getAttribute('href'),
            title: (title||'').trim(),
            priceText: (price||'').trim(),
            image: img && (img.getAttribute('src')||img.getAttribute('data-src')||img.currentSrc||'')
          };
        })""",
    )
    out: list[dict] = []
    seen: set[str] = set()
    for it in items or []:
        href = product_url_from_link(it.get("href") or "")
        if not href or "/gb/" not in href:
            continue
        if any(
            x in href
            for x in (
                "/customer-services",
                "/stores",
                "/account",
                "/wishlist",
                "/mlb/",
                "/madetolast",
                "/cookie",
                "/privacy",
                "/legal",
            )
        ):
            continue
        if href in seen:
            continue
        seen.add(href)
        title = clean_text(it.get("title") or "")
        if not title:
            continue
        out.append(
            {
                "url": href,
                "title": title,
                "gbpPrice": parse_gbp(it.get("priceText") or ""),
                "plpImage": it.get("image") or "",
            }
        )
    return out


def scrape_plp(url: str, *, max_scroll: int = 28) -> list[dict]:
    """Return PLP colourway cards: title, price, href, image.

    Mulberry GB PLPs are Algolia-backed (72 hits/page). DOM scroll alone stops at
    the first page, so we intercept the PLP query and paginate all nbPages.
    """
    from playwright.sync_api import sync_playwright

    meta: dict[str, str] = {}
    dom_fallback: list[dict] = []

    with sync_playwright() as p:
        browser, page = _new_page(p)
        try:

            def on_request(req) -> None:
                if meta.get("body"):
                    return
                if (
                    "algolia.net" in req.url
                    and "/queries" in req.url
                    and req.post_data
                    and "hitsPerPage=72" in req.post_data
                    and "filters=" in req.post_data
                ):
                    meta["req_url"] = req.url
                    meta["body"] = req.post_data

            page.on("request", on_request)
            page.goto(abs_url(url), wait_until="domcontentloaded", timeout=120000)
            _accept_cookies(page)
            for _ in range(48):
                if meta.get("body"):
                    break
                page.wait_for_timeout(250)
            if not meta.get("body"):
                print(
                    "WARN Mulberry PLP: Algolia not intercepted — falling back to DOM",
                    flush=True,
                )
                dom_fallback = _scrape_plp_dom(page, max_scroll=max_scroll)
        finally:
            browser.close()

    if not meta.get("body"):
        return dom_fallback

    hits, nb_hits = _algolia_paginate(meta["req_url"], meta["body"])
    out: list[dict] = []
    seen: set[str] = set()
    for hit in hits:
        href = product_url_from_link(hit.get("link") or "")
        if not href or "/gb/" not in href:
            continue
        if href in seen:
            continue
        seen.add(href)
        title = clean_text(hit.get("name") or "")
        if not title:
            continue
        try:
            gbp = float(hit.get("price") or 0)
        except (TypeError, ValueError):
            gbp = 0.0
        out.append(
            {
                "url": href,
                "title": title,
                "gbpPrice": gbp,
                "plpImage": algolia_image_url(hit.get("image") or ""),
                "colour": clean_text(hit.get("colour") or ""),
                "objectID": str(hit.get("objectID") or ""),
            }
        )

    if nb_hits and len(out) < max(1, int(nb_hits * 0.9)):
        raise RuntimeError(
            f"Mulberry PLP incomplete for {url}: got {len(out)} cards, "
            f"Algolia nbHits={nb_hits} (need ≥90%)"
        )
    print(f"Algolia PLP {url} → {len(out)} cards (nbHits={nb_hits})", flush=True)
    return out


def scrape_pdp(url: str) -> dict:
    """Scrape one colourway PDP."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser, page = _new_page(p)
        try:
            page.goto(abs_url(url), wait_until="domcontentloaded", timeout=120000)
            _accept_cookies(page)
            page.wait_for_timeout(2800)
            # Expand description / details accordions when present
            for label in ("Description", "Details"):
                try:
                    page.locator(f".accordion-title:has-text('{label}')").first.click(timeout=1200)
                    page.wait_for_timeout(350)
                except Exception:
                    pass
            data = page.evaluate(
                """() => {
                  const meta = {};
                  for (const m of document.querySelectorAll('meta')) {
                    const k = m.getAttribute('property') || m.getAttribute('name');
                    const v = m.getAttribute('content');
                    if (k && v) meta[k] = v;
                  }
                  const h1 = (document.querySelector('h1')||{}).innerText||'';
                  const colourLabel = meta['product:color'] || '';
                  const swatches = [...document.querySelectorAll('.colour-swatch a, [class*="swatch"] a, .product-colours a')]
                    .map(a => ({
                      href: a.getAttribute('href')||'',
                      label: (a.getAttribute('aria-label')||a.getAttribute('title')||a.innerText||'').trim(),
                    }))
                    .filter(x => x.href);
                  const imgs = [...document.querySelectorAll('img')]
                    .map(i => i.src || i.getAttribute('data-src') || '')
                    .filter(s => s.includes('images.mulberry.com') && !s.includes('$largeThumb$') && !s.includes('w=200') && !s.includes('w=304') && !s.includes('_IS'));
                  const uniq = [...new Set(imgs.map(s => s.split('?')[0]))].slice(0, 12);
                  const descEl = document.querySelector('#description-pdp-accordion-component-tab, .accordion-navigation.active .content');
                  const description = (descEl && descEl.innerText || '').trim();
                  // Details panel: click may activate another content block
                  let details = '';
                  for (const nav of document.querySelectorAll('.accordion-navigation')) {
                    const title = (nav.querySelector('.accordion-title')||{}).innerText||'';
                    if (/^details$/i.test((title||'').trim())) {
                      const body = nav.querySelector('.content');
                      details = (body && body.innerText || '').trim();
                    }
                  }
                  const dims = [...document.querySelectorAll('li, p, dd')]
                    .map(e => (e.innerText||'').trim())
                    .filter(t => {
                      const low = t.toLowerCase();
                      return (low.includes('cm') || low.includes('height') || low.includes('width') || low.includes('depth') || low.includes('dimension') || low.includes('strap')) && t.length < 180;
                    })
                    .slice(0, 30);
                  const sizes = [...document.querySelectorAll('select[name*="size"] option, [class*="size"] button, [data-size]')]
                    .map(e => (e.innerText||e.value||e.getAttribute('data-size')||'').trim())
                    .filter(t => {
                      const low = (t||'').toLowerCase();
                      return t && t.length < 12 && !low.includes('select') && !low.includes('size') && !low.includes('choose');
                    });
                  const tables = [...document.querySelectorAll('table')].map(tb => {
                    const headers = [...tb.querySelectorAll('th')].map(th => th.innerText.trim());
                    const rows = [...tb.querySelectorAll('tr')].map(tr =>
                      [...tr.querySelectorAll('td')].map(td => td.innerText.trim())
                    ).filter(r => r.length);
                    return {headers, rows};
                  }).filter(t => t.headers.length || t.rows.length);
                  return {
                    h1, meta, colourLabel, swatches, imgs: uniq, description, details, dims, sizes: [...new Set(sizes)], tables
                  };
                }"""
            )
        finally:
            browser.close()

    meta = data.get("meta") or {}
    title = clean_text(meta.get("og:title") or "") or clean_text(
        (data.get("h1") or "").split("|")[1] if "|" in (data.get("h1") or "") else (data.get("h1") or "")
    )
    # Colour from h1 "Mulberry | Style | Colour | Women"
    colour = clean_text(meta.get("product:color") or data.get("colourLabel") or "")
    if not colour:
        parts = [clean_text(x) for x in (data.get("h1") or "").split("|")]
        if len(parts) >= 3:
            colour = parts[2]
    gbp = 0.0
    try:
        gbp = float(meta.get("og:price:amount") or 0)
    except ValueError:
        gbp = 0.0
    if not gbp:
        gbp = parse_gbp(page_price_fallback(data))

    images = []
    for src in data.get("imgs") or []:
        u = src.split("?")[0]
        if u and u not in images:
            images.append(u)
    images = [normalize_image(u) for u in images]

    sku = ""
    for img in images:
        m = re.search(r"/([A-Z0-9]+_[A-Z0-9]+_[A-Z0-9]+)", img)
        if m:
            sku = m.group(1)
            break
    # Keep gallery frames for this colourway SKU only (drop related-product thumbs)
    if sku:
        prefix = "_".join(sku.split("_")[:2])  # G_RL8971
        filtered = [u for u in images if prefix in u]
        if filtered:
            images = filtered[:8]

    description = clean_text(data.get("description") or "")
    details = clean_text(data.get("details") or "")
    if description.lower().startswith("description"):
        description = description.split("\n", 1)[-1].strip()
    if not description and data.get("dims"):
        description = " · ".join(clean_text(x) for x in (data.get("dims") or [])[:8])

    size_chart = None
    tables = data.get("tables") or []
    if tables:
        tb = tables[0]
        size_chart = {
            "headers": tb.get("headers") or [],
            "rows": tb.get("rows") or [],
        }

    return {
        "url": abs_url(url),
        "title": title,
        "colour": colour,
        "gbpPrice": gbp,
        "images": images,
        "description": description,
        "details": details,
        "dims": [clean_text(x) for x in (data.get("dims") or [])][:20],
        "sizes": data.get("sizes") or [],
        "sizeChart": size_chart,
        "swatches": [
            {"url": abs_url(s.get("href") or ""), "label": clean_text(s.get("label") or "")}
            for s in (data.get("swatches") or [])
            if s.get("href")
        ],
        "sku": sku,
        "availability": True,
    }


def page_price_fallback(_data: dict) -> str:
    return ""


def normalize_image(url: str) -> str:
    if not url:
        return ""
    # Request a stable mid-size asset
    base = url.split("?")[0]
    return base + "?w=1200"


def download_images(sku_slug: str, urls: list[str], *, limit: int = 8) -> list[str]:
    """Download remote images into public/products/mb-pdp/<slug>/N.jpg."""
    dest = IMG_ROOT / sku_slug
    dest.mkdir(parents=True, exist_ok=True)
    local: list[str] = []
    for i, url in enumerate(urls[:limit], start=1):
        path = dest / f"{i}.jpg"
        if not path.is_file():
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": UA, "Referer": BASE + "/"},
                )
                with urllib.request.urlopen(req, timeout=60) as r:
                    path.write_bytes(r.read())
                time.sleep(0.15)
            except Exception as e:
                print(f"WARN image {url}: {e}", flush=True)
                continue
        local.append(f"/products/mb-pdp/{sku_slug}/{i}.jpg")
    return local
