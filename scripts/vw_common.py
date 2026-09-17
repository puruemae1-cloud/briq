#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import time
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMG_ROOT = ROOT / "public" / "products" / "vw-pdp"
BASE = "https://www.viviennewestwood.com"


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
    if "demandware.static" not in raw and "/images/" not in raw:
        return raw.split("?")[0]
    parsed = urllib.parse.urlparse(raw)
    qs = urllib.parse.parse_qs(parsed.query)
    qs["sw"] = ["1200"]
    qs["sh"] = ["1600"]
    qs["sm"] = ["fit"]
    qs["q"] = ["85"]
    new_query = urllib.parse.urlencode({k: v[0] for k, v in qs.items()})
    return urllib.parse.urlunparse(parsed._replace(query=new_query))


def filter_product_images(sku: str, remote_urls: list[str]) -> list[str]:
    sku_norm = slugify((sku or "").replace(".", "-").replace("_", "-"))
    sku_bits = [b for b in re.split(r"[-_]+", (sku or "").upper()) if len(b) >= 4]
    out: list[str] = []
    seen: set[str] = set()
    for raw in remote_urls:
        url = normalize_image_url(raw)
        if not url or url in seen:
            continue
        seen.add(url)
        upper = url.upper()
        if sku_bits and any(bit in upper for bit in sku_bits):
            out.append(url)
    if out:
        return out
    return [normalize_image_url(u) for u in remote_urls if normalize_image_url(u)]


def download_image(request, url: str, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    resp = request.get(normalize_image_url(url), timeout=90000)
    if not resp.ok:
        return False
    data = resp.body()
    if len(data) < 800:
        return False
    dest.write_bytes(data)
    return True


def materialize_images(request, sku: str, remote_urls: list[str]) -> list[str]:
    folder = slugify((sku or "item").replace(".", "-"))
    out: list[str] = []
    seen: set[str] = set()
    for i, raw in enumerate(remote_urls, start=1):
        url = normalize_image_url(raw)
        if not url or url in seen:
            continue
        seen.add(url)
        rel = f"/products/vw-pdp/{folder}/{i}.jpg"
        dest = IMG_ROOT / folder / f"{i}.jpg"
        try:
            if not dest.exists() or dest.stat().st_size < 800:
                ok = download_image(request, url, dest)
                if not ok:
                    continue
            out.append(rel)
        except Exception:
            continue
    return out


def with_browser(callback, *, headed: bool = False, engine: str = "chromium"):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        launcher = p.chromium if engine == "chromium" else p.webkit
        browser = launcher.launch(headless=not headed)
        ctx = browser.new_context(
            locale="en-GB",
            viewport={"width": 1440, "height": 1600},
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
        'button:has-text("Accept all cookies")',
    ):
        try:
            page.locator(sel).first.click(timeout=2500)
            page.wait_for_timeout(600)
            return
        except Exception:
            pass


def dismiss_popups(page) -> None:
    accept_cookies(page)
    for sel in (
        ".b-dialog.m-welcome_banner button",
        '[data-id="welcomeBannerModal"] button[aria-label="Close"]',
        'button:has-text("No thanks")',
        '[data-ref="closeBtn"]',
    ):
        try:
            loc = page.locator(sel).first
            if loc.count():
                loc.click(timeout=2000)
                page.wait_for_timeout(500)
                return
        except Exception:
            pass


def parse_gbp(text: str | None) -> float:
    if not text:
        return 0.0
    m = re.search(r"£\s*([0-9][0-9,]*(?:\.[0-9]{2})?)", text)
    if m:
        return float(m.group(1).replace(",", ""))
    m = re.search(r"([0-9][0-9,]*)\s*GBP", text, re.I)
    if m:
        return float(m.group(1).replace(",", ""))
    return 0.0


def sku_from_url(url: str) -> str:
    path = urllib.parse.urlparse(url).path
    name = path.rsplit("/", 1)[-1]
    if name.endswith(".html"):
        name = name[:-5]
    return name.strip()


def scrape_plp_cards(page, url: str) -> list[dict]:
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    dismiss_popups(page)
    page.wait_for_timeout(200)

    stable_rounds = 0
    last_count = -1
    for _ in range(28):
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
                    btn.click(timeout=1500)
                    page.wait_for_timeout(250)
                    break
        except Exception:
            pass
        try:
            page.mouse.wheel(0, 22000)
        except Exception:
            pass
        page.wait_for_timeout(180)
        count = page.locator("[data-pid]").count()
        if count == last_count:
            stable_rounds += 1
            if stable_rounds >= 3:
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
            const a = el.querySelector('a[href*=".html"]');
            if (!pid || !a) continue;
            const href = a.href || '';
            if (!href || seen.has(pid)) continue;
            seen.add(pid);
            const text = (el.textContent || '').replace(/\\s+/g, ' ').trim();
            const m = text.match(/£\\s*([0-9][0-9,]*(?:\\.[0-9]{2})?)/);
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


def scrape_pdp(page, url: str) -> dict:
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    dismiss_popups(page)
    page.wait_for_timeout(400)

    for label in ("Description", "Composition", "Care Instructions"):
        try:
            page.locator(f'button:has-text("{label}")').first.click(timeout=800)
            page.wait_for_timeout(80)
        except Exception:
            pass

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
          const ld = Array.from(document.querySelectorAll('script[type="application/ld+json"]'))
            .map((s) => {
              try { return JSON.parse(s.textContent || ''); } catch (e) { return null; }
            })
            .filter(Boolean);
          const product = ld.find((x) => x['@type'] === 'Product') || {};
          const offers = product.offers || {};
          const offerList = Array.isArray(offers) ? offers : [offers];
          const primaryOffer = offerList.find((o) => o && o.price) || offerList[0] || {};
          const imagesFromLd = Array.isArray(product.image) ? product.image : (product.image ? [product.image] : []);
          const imagesFromDom = Array.from(document.querySelectorAll('img'))
            .map((img) => img.currentSrc || img.src || '')
            .filter((src) => src.includes('/images/') && src.includes('demandware'));
          const uniqImages = Array.from(new Set([...imagesFromLd, ...imagesFromDom]));
          const details = Array.from(document.querySelectorAll('.b-product_accordion-button')).map((btn) => {
            const label = (btn.textContent || '').replace(/\\s+/g, ' ').trim();
            const panelId = btn.getAttribute('aria-controls') || '';
            const panel = panelId ? document.getElementById(panelId) : null;
            return {
              label,
              body: (panel?.textContent || '').replace(/\\s+/g, ' ').trim(),
              html: panel?.innerHTML || '',
            };
          }).filter((x) => x.label);
          // Prefer official size swatches — generic button text is "XS Size: XS" and
          // fails ^XS$ matching, which previously collapsed clothing to OS.
          const sizeBtns = Array.from(
            document.querySelectorAll(
              '[id="variation-label-size"], [aria-labelledby*="variation-label-size"]'
            )
          );
          let sizeRoot = document.querySelector('.b-variations_item.m-size, .b-variations_item.m-swatch.m-size');
          if (!sizeRoot) {
            sizeRoot = document.querySelector('[aria-labelledby*="variation-label-size"]');
          }
          const swatches = sizeRoot
            ? Array.from(sizeRoot.querySelectorAll('button.b-variation_swatch[data-tau-size-id], button.b-variation_swatch'))
            : Array.from(document.querySelectorAll('button.b-variation_swatch[data-tau-size-id]'));
          const sizeEntries = swatches.map((btn) => {
            const aria = (btn.getAttribute('aria-label') || '').trim();
            const title = (btn.getAttribute('title') || '').replace(/\\(not available\\)/i, '').trim();
            const span = (btn.querySelector('.b-variation_swatch-value')?.childNodes[0]?.textContent || '').trim();
            const raw = aria || span || title;
            const m = String(raw).match(/^(XXXS|XXS|XS|S|M|L|XL|XXL|XXXL|3XL|4XL|One Size|OS|\\d{2}(?:\\.\\d)?)$/i);
            const size = m
              ? (m[1].toUpperCase() === 'ONE SIZE' ? 'OS' : m[1].toUpperCase() === '3XL' ? 'XXXL' : m[1].toUpperCase())
              : '';
            const disabled = btn.classList.contains('m-disabled')
              || btn.getAttribute('aria-disabled') === 'true';
            return size ? { size, inStock: !disabled } : null;
          }).filter(Boolean);
          let sizes = [...new Set(sizeEntries.map((x) => x.size))];
          const sizeStock = Object.fromEntries(sizeEntries.map((x) => [x.size, x.inStock]));
          if (!sizes.length) {
            const sizeCandidates = Array.from(document.querySelectorAll('button, option, [data-value]'))
              .map((el) => (el.textContent || '').replace(/\\s+/g, ' ').trim())
              .filter(Boolean);
            sizes = Array.from(new Set(sizeCandidates.map((t) => {
              const m = t.match(/Size:\\s*(\\d+(?:\\.\\d+)?)/i);
              if (m) return m[1];
              const letter = t.match(/\\b(XXXS|XXS|XS|S|M|L|XL|XXL|XXXL|3XL|One Size|OS)\\b/i);
              if (letter) {
                const v = letter[1].toUpperCase();
                return v === 'ONE SIZE' ? 'OS' : v === '3XL' ? 'XXXL' : v;
              }
              if (/^\\d{2}(?:\\.\\d)?$/.test(t)) return t;
              return '';
            }).filter(Boolean)));
          }
          let sizeGuideUrl = '';
          const guideBtn = document.querySelector('.b-size_guide_link, button[data-tau="size_guide_cta"]');
          if (guideBtn) {
            try {
              const cfg = JSON.parse(guideBtn.getAttribute('data-modal-config') || '{}');
              sizeGuideUrl = cfg.url || '';
            } catch (e) {}
            if (!sizeGuideUrl) sizeGuideUrl = guideBtn.getAttribute('href') || '';
          }
          const availabilityText = String(primaryOffer.availability || '');
          const inStock = availabilityText.includes('InStock') || /add to bag/i.test(document.body.innerText);
          const urlSku = location.pathname.split('/').pop().replace('.html', '');
          const skuCandidate = product.sku || urlSku;
          const sku = /\\d{2,}W[-_]/i.test(String(skuCandidate)) || String(skuCandidate).includes('-')
            ? String(skuCandidate)
            : urlSku;
          return {
            sku,
            title: product.name || text('h1'),
            priceText: primaryOffer.price ? `£${primaryOffer.price}` : text('.price, .sales .value, [itemprop="price"]'),
            color: text('.color-value, .product-color, .selected-color'),
            availability: inStock,
            images: uniqImages,
            details,
            sizes,
            sizeStock,
            sizeGuideUrl,
            breadcrumb: allText('.breadcrumb a, nav[aria-label*="breadcrumb"] a, [class*="breadcrumb"] a'),
            categoryLabel: (product.category || text('.breadcrumb li:last-child, .breadcrumb span:last-child')),
          };
        }
        """,
    )
    return data or {}


_SIZE_GUIDE_CACHE: dict[str, dict | None] = {}

_ROW_LABEL_KO = {
    "united kingdom": "UK",
    "uk": "UK",
    "usa": "US",
    "us": "US",
    "italy/eu": "IT / EU",
    "italy": "IT",
    "eu": "EU",
    "australia": "AU",
    "france": "FR",
    "germany": "DE",
    "japan": "JP",
    "korea": "KR",
    "chest": "가슴 (cm)",
    "bust": "가슴 (cm)",
    "waist": "허리 (cm)",
    "hip": "힙 (cm)",
    "hips": "힙 (cm)",
    "bottom": "밑단 (cm)",
    "shoulder": "어깨 (cm)",
    "sleeve": "소매 (cm)",
    "length": "총기장 (cm)",
    "inseam": "인심 (cm)",
}


def fetch_size_guide_chart(page, guide_url: str) -> dict | None:
    """Parse official VW size-guide asset into Briq sizeChart shape."""
    url = (guide_url or "").strip()
    if not url:
        return None
    abs_url = _abs_url(url)
    if abs_url in _SIZE_GUIDE_CACHE:
        return _SIZE_GUIDE_CACHE[abs_url]
    try:
        page.goto(abs_url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(400)
        tables = page.evaluate(
            """
            () => [...document.querySelectorAll('table')].map((t) =>
              [...t.querySelectorAll('tr')].map((tr) =>
                [...tr.querySelectorAll('th,td')].map((c) =>
                  (c.textContent || '').replace(/\\s+/g, ' ').trim()
                )
              )
            )
            """
        )
        title = page.title() or ""
    except Exception:
        _SIZE_GUIDE_CACHE[abs_url] = None
        return None

    chart = tables_to_size_chart(tables or [], title=title, source_url=abs_url)
    _SIZE_GUIDE_CACHE[abs_url] = chart
    return chart


def tables_to_size_chart(tables: list, *, title: str = "", source_url: str = "") -> dict | None:
    best = None
    for table in tables:
        rows = [r for r in table if any(str(c).strip() for c in r)]
        if len(rows) < 2 or len(rows[0]) < 3:
            continue
        headers = ["구분", *[str(c).strip() for c in rows[0][1:]]]
        body = []
        for r in rows[1:]:
            if not r or not str(r[0]).strip():
                continue
            label = str(r[0]).strip()
            key = label.lower()
            label_ko = _ROW_LABEL_KO.get(key, label)
            # Skip duplicate header rows like "SWEATSHIRTS / XXS XS ..."
            if all(re.match(r"^(XXXS|XXS|XS|S|M|L|XL|XXL|XXXL|3XL|\d+)$", str(c).strip(), re.I) for c in r[1:] if str(c).strip()):
                if not any(ch.isdigit() for ch in "".join(str(c) for c in r[1:])):
                    continue
            vals = [str(c).strip() for c in r[1 : len(headers)]]
            while len(vals) < len(headers) - 1:
                vals.append("")
            body.append([label_ko, *vals[: len(headers) - 1]])
        if len(body) >= 2:
            best = {"headers": headers, "rows": body}
            break
    if not best:
        return None
    title_ko = "비비안 웨스트우드 사이즈 가이드"
    if "men" in (title + source_url).lower():
        title_ko = "비비안 웨스트우드 남성 사이즈 가이드"
    elif "women" in (title + source_url).lower() or "womens" in (title + source_url).lower():
        title_ko = "비비안 웨스트우드 여성 사이즈 가이드"
    return {
        "id": slugify(Path(urllib.parse.urlparse(source_url).path).stem or "vw-size"),
        "titleKo": title_ko,
        "noteKo": "비비안 웨스트우드 공식 사이즈 가이드 기준입니다.",
        "headers": best["headers"],
        "rows": best["rows"],
        "sourceUrl": source_url,
    }


def scrape_leaf_rows(leaf: dict, *, headed: bool = False, limit: int = 0, skip_ids: set | None = None) -> list[dict]:
    skip = {str(x).strip().lower() for x in (skip_ids or set()) if str(x).strip()}
    def run(page):
        cards = scrape_plp_cards(page, leaf["url"])
        rows = []
        seen = 0
        for card in cards:
            cid = str(card.get("id") or "").strip()
            if not cid:
                cid = sku_from_url(card.get("href") or "")
            if cid and cid.lower() in skip:
                continue
            seen += 1
            if limit and seen > limit:
                break
            pdp = scrape_pdp(page, card["href"])
            sku = (pdp.get("sku") or card.get("id") or sku_from_url(card["href"])).strip()
            remote_images = filter_product_images(sku or card["id"], pdp.get("images") or [])
            local_images = materialize_images(page.request, sku or card["id"], remote_images)
            size_chart = None
            guide = (pdp.get("sizeGuideUrl") or "").strip()
            if guide:
                try:
                    size_chart = fetch_size_guide_chart(page, guide)
                except Exception:
                    size_chart = None
            rows.append(
                {
                    "id": sku or card["id"],
                    "sku": sku or card["id"],
                    "title": (pdp.get("title") or "").strip(),
                    "gbpPrice": parse_gbp(pdp.get("priceText")) or float(card.get("gbpPrice") or 0),
                    "url": card["href"],
                    "leafId": leaf["id"],
                    "leafLabel": leaf.get("label") or "",
                    "leafLabelKo": leaf.get("labelKo") or "",
                    "collections": list(dict.fromkeys(leaf.get("collections") or [leaf["id"]])),
                    "color": {"label": pdp.get("color") or ""},
                    "details": pdp.get("details") or [],
                    "sizes": pdp.get("sizes") or [],
                    "sizeStock": pdp.get("sizeStock") or {},
                    "sizeGuideUrl": guide,
                    "sizeChart": size_chart,
                    "images": local_images,
                    "remoteImages": remote_images,
                    "availability": bool(pdp.get("availability")),
                    "breadcrumb": pdp.get("breadcrumb") or [],
                    "categoryLabel": pdp.get("categoryLabel") or "",
                }
            )
        return rows

    return with_browser(run, headed=headed)
