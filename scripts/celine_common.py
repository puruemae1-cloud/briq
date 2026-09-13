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
SFCC_VARIATION = (
    "https://www.celine.com/on/demandware.store/"
    "Sites-CELINE_GB-Site/en_GB/Product-Variation"
)


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
    # Prefer expanding country-value spans (shoes) into full columns.
    country_order = ["EU/FR", "UK", "US", "JP", "CN", "KR"]
    expanded_rows: list[list[str]] = []
    for tr in re.findall(r"<tr[^>]*role=\"row\"[^>]*>(.*?)</tr>", size_guide_html, re.I | re.S):
        it_m = re.search(
            r"<td[^>]*role=\"cell\"[^>]*>\s*<span>(.*?)</span>",
            tr,
            re.I | re.S,
        )
        country_vals = re.findall(
            r'data-msizestable-country-value="([^"]+)"\s*(?:hidden)?\s*>(.*?)</span>',
            tr,
            re.I | re.S,
        )
        if it_m and country_vals:
            it_size = clean_html_text(it_m.group(1))
            by_c = {k: clean_html_text(v) for k, v in country_vals}
            if any(by_c.get(c) for c in country_order):
                expanded_rows.append([it_size] + [by_c.get(c, "") for c in country_order])
                continue
        # Fallback: plain cells (belts / RTW / single conversion column).
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
            expanded_rows.append(vals)

    if expanded_rows and all(len(r) >= 7 for r in expanded_rows):
        return {
            "headers": ["CELINE SHOES (IT)", "EU/FR", "UK", "US", "JP", "CN", "KR"],
            "rows": expanded_rows,
            "html": size_guide_html,
        }

    headers = re.findall(r"<th[^>]*>\s*<span[^>]*>(.*?)</span>", size_guide_html, re.I | re.S)
    headers = [clean_html_text(h) for h in headers if clean_html_text(h)]
    # Collapse select-label noise in thead.
    headers = [re.sub(r"\s+", " ", h).strip() for h in headers]
    return {
        "headers": headers,
        "rows": expanded_rows,
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


def fetch_sfcc_availability(pid: str) -> dict | None:
    """Official GB stock via SFCC Product-Variation (works when HTML WAF blocks).

    Returns dict with availability bool, confidence, and selectable sizes — or None
    when the endpoint fails.
    """
    sku = (pid or "").strip()
    if not sku:
        return None
    url = f"{SFCC_VARIATION}?{urllib.parse.urlencode({'pid': sku})}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=28) as resp:
            data = json.loads(resp.read().decode("utf-8", "ignore"))
    except Exception:
        return None
    prod = data.get("product") if isinstance(data, dict) else None
    if not isinstance(prod, dict):
        return None
    avail_block = prod.get("availability") if isinstance(prod.get("availability"), dict) else {}
    msgs = " ".join(str(m) for m in (avail_block.get("messages") or []))
    selectable_sizes: list[str] = []
    for va in prod.get("variationAttributes") or []:
        if not isinstance(va, dict):
            continue
        attr = str(va.get("attributeId") or "").lower()
        if attr not in {"size", "sizechart", "sizes"}:
            continue
        for val in va.get("values") or []:
            if not isinstance(val, dict):
                continue
            label = str(val.get("displayValue") or val.get("value") or val.get("id") or "").strip()
            if val.get("selectable") or val.get("inStock") is True:
                if label:
                    selectable_sizes.append(label)
    explicit_oos = bool(
        re.search(r"sold out|out of stock|not available", msgs, re.I)
        or prod.get("available") is False
        or prod.get("inStock") is False
    )
    explicit_in = bool(
        prod.get("available") is True
        or prod.get("inStock") is True
        or selectable_sizes
        or re.search(r"\bin stock\b|\bavailable\b", msgs, re.I)
    )
    if explicit_oos and not selectable_sizes:
        return {
            "availability": False,
            "availabilityConfidence": "sfcc_oos",
            "sizes": selectable_sizes,
            "messages": msgs,
        }
    if explicit_in:
        return {
            "availability": True,
            "availabilityConfidence": "sfcc",
            "sizes": selectable_sizes,
            "messages": msgs,
        }
    return {
        "availability": None,
        "availabilityConfidence": "sfcc_unknown",
        "sizes": selectable_sizes,
        "messages": msgs,
    }


def apply_sfcc_availability(row: dict) -> dict:
    """Prefer SFCC stock over fragile HTML body-text heuristics."""
    row = dict(row)
    pid = str(row.get("sku") or row.get("id") or "").strip()
    info = fetch_sfcc_availability(pid)
    if not info:
        return row
    if info.get("availability") is not None:
        row["availability"] = info["availability"]
        row["availabilityConfidence"] = info.get("availabilityConfidence") or "sfcc"
    # Fill missing sizes from selectable SFCC values when HTML scrape was empty.
    if info.get("sizes") and not (row.get("sizes") or []):
        row["sizes"] = list(info["sizes"])
    return row


def is_blocked_pdp_title(title: str | None) -> bool:
    """True when Akamai/WAF HTML was scraped instead of a real PDP."""
    t = (title or "").strip().lower()
    return t in {"access denied", "access denied.", "forbidden", "403"} or t.startswith(
        "access denied"
    )


def title_from_plp_card(card: dict) -> str:
    """Best-effort product name from PLP card text (before price)."""
    text = str(card.get("text") or "").strip()
    if not text:
        return ""
    # Strip trailing "1 234 GBP" / "£1,234" style prices from PLP blobs.
    text = re.sub(
        r"(?i)(?:£\s*)?[0-9][0-9,]*(?:\.[0-9]{2})?\s*GBP.*$",
        "",
        text,
    ).strip()
    text = re.sub(r"(?i)^CELINE\s+", "", text).strip()
    if is_blocked_pdp_title(text):
        return ""
    return text[:160]


def title_from_pdp_url(url: str) -> str:
    """Recover English title from Celine PDP slug when scrape is blocked."""
    path = (url or "").split("?")[0].rstrip("/")
    slug = path.rsplit("/", 1)[-1]
    slug = re.sub(r"\.html?$", "", slug, flags=re.I)
    parts = [p for p in slug.split("-") if p]
    # Drop trailing SKU token(s): last hyphen chunk that contains a digit and
    # looks like a maison code (has a dot colourway or is long), e.g. AA0FP2K77.38NO.
    # Never strip material words like "cashmere".
    cut = None
    for i in range(len(parts) - 1, -1, -1):
        tok = parts[i]
        if re.search(r"\d", tok) and ("." in tok or len(tok) >= 6):
            cut = i
            break
    if cut is not None and cut > 0:
        parts = parts[:cut]
    slug = " ".join(parts).strip()
    if not slug or is_blocked_pdp_title(slug):
        return ""
    out = []
    for w in slug.split():
        if w.isupper() and len(w) <= 5:
            out.append(w)
        else:
            out.append(w.capitalize())
    return " ".join(out)


def is_blocked_pdp(pdp: dict, *, title: str | None = None) -> bool:
    t = title if title is not None else (pdp.get("title") or "")
    if is_blocked_pdp_title(str(t)):
        return True
    # Empty PDP body with no commerce signals
    if not (pdp.get("details") or pdp.get("images") or pdp.get("sku") or pdp.get("priceText")):
        if is_blocked_pdp_title(str(t)) or not str(t).strip():
            return True
    return False


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
          const bodyText = (document.body?.innerText || '');
          const soldOutRe = /sold out|out of stock|notify me when available|currently unavailable|no longer available/i;
          const availableRe = /available now|in stock|add to (bag|cart|basket)|ajouter au panier/i;
          const sizeBtns = Array.from(document.querySelectorAll(
            '.m-selector__list button, .m-selector button, [data-attr="size"] button, button[data-attr-value]'
          ));
          const sizeStates = sizeBtns.map((b) => {
            const t = (b.textContent || '').replace(/\\s+/g, ' ').trim();
            const disabled = !!(
              b.disabled ||
              b.getAttribute('aria-disabled') === 'true' ||
              /is-disabled|disabled|unavailable|sold-?out|oos/i.test(b.className || '')
            );
            return { t, disabled };
          }).filter((x) => /^(XXXS|XXS|XS|S|M|L|XL|XXL|XXXL|OS|U|[0-9]{2}(?:\\.[0-9])?)$/i.test(x.t));
          const enabledSizes = sizeStates.filter((x) => !x.disabled);
          const addBtn = document.querySelector(
            'button[data-gtm-track-interaction-type="add to cart"], button.add-to-cart, .o-product__add-to-cart button, form[action*="Cart"] button, button[name="add"]'
          );
          const addEnabled = !!(addBtn && !addBtn.disabled && !/disabled|sold/i.test(addBtn.className || ''));
          const addText = (addBtn?.textContent || '').replace(/\\s+/g, ' ').trim();
          let schemaInStock = null;
          for (const s of document.querySelectorAll('script[type="application/ld+json"]')) {
            try {
              const raw = JSON.parse(s.textContent || 'null');
              const stack = Array.isArray(raw) ? raw.slice() : [raw];
              while (stack.length) {
                const node = stack.pop();
                if (!node || typeof node !== 'object') continue;
                const avail = node.availability || node.itemAvailability;
                if (typeof avail === 'string') {
                  if (/InStock|LimitedAvailability|OnlineOnly/i.test(avail)) schemaInStock = true;
                  if (/OutOfStock|SoldOut|Discontinued/i.test(avail)) schemaInStock = false;
                }
                for (const v of Object.values(node)) {
                  if (v && typeof v === 'object') stack.push(v);
                }
              }
            } catch (e) {}
          }
          const explicitSoldOut = soldOutRe.test(bodyText) || /notify me|sold out/i.test(addText);
          const explicitAvailable =
            availableRe.test(bodyText) ||
            addEnabled ||
            enabledSizes.length > 0 ||
            schemaInStock === true;
          let availability = null;
          let availabilityConfidence = 'unknown';
          if (explicitSoldOut && !enabledSizes.length && schemaInStock !== true) {
            availability = false;
            availabilityConfidence = 'sold_out';
          } else if (schemaInStock === false && !enabledSizes.length && !addEnabled) {
            availability = false;
            availabilityConfidence = 'schema_oos';
          } else if (explicitAvailable) {
            availability = true;
            availabilityConfidence = enabledSizes.length ? 'sizes' : (addEnabled ? 'add_to_bag' : 'copy');
          } else if (schemaInStock === true) {
            availability = true;
            availabilityConfidence = 'schema';
          }
          return {
            sku: document.documentElement.getAttribute('data-sku') || text('.product-id'),
            categoryLabel: document.documentElement.getAttribute('data-category') || '',
            title: text('h1'),
            priceText: text('.o-product__price, .a-price, [data-gtm-track-interaction-type="add to cart"]'),
            color: text('.m-selector__current-value, .o-product__current-color, .o-product__color-name'),
            availability,
            availabilityConfidence,
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
                # Still record leaf membership so category leaves (e.g. leather)
                # stay populated even when the PDP was scraped under another leaf.
                rows.append(
                    {
                        "id": cid,
                        "sku": cid,
                        "title": "",
                        "gbpPrice": float(card.get("gbpPrice") or 0) or None,
                        "url": card.get("href") or "",
                        "leafId": leaf["id"],
                        "leafLabel": leaf.get("label") or "",
                        "leafLabelKo": leaf.get("leafLabelKo") or leaf.get("labelKo") or "",
                        "collections": list(dict.fromkeys(leaf.get("collections") or [leaf["id"]])),
                        "color": {},
                        "details": [],
                        "sizes": [],
                        "sizeGuideUrl": "",
                        "sizeGuide": {},
                        "images": [],
                        "remoteImages": [],
                        "availability": None,
                        "membershipOnly": True,
                        "breadcrumb": [],
                        "categoryLabel": "",
                    }
                )
                continue
            seen += 1
            if limit and seen > limit:
                break
            pdp = scrape_pdp(page, card["href"])
            sku = (pdp.get("sku") or card.get("id") or "").strip()
            title = (pdp.get("title") or "").strip()
            blocked = is_blocked_pdp(pdp, title=title)
            if blocked:
                # Prefer PLP / URL name over "Access Denied" so weekly sync
                # cannot poison the catalogue with WAF HTML.
                title = (
                    title_from_plp_card(card)
                    or title_from_pdp_url(card.get("href") or "")
                    or title
                )
            if is_blocked_pdp_title(title):
                print(f"skip blocked PDP {card.get('href')}", flush=True)
                continue
            remote_images = filter_product_images(sku or card["id"], pdp.get("images") or [])
            local_images = materialize_images(sku or card["id"], remote_images)
            # If WAF blocked image scrape but we already have local files, keep going.
            if blocked and not local_images:
                folder = slugify((sku or card["id"]).replace(".", "-"))
                cached = sorted((IMG_ROOT / folder).glob("*.jpg"))
                local_images = [f"/products/ce-pdp/{folder}/{p.name}" for p in cached]
            size_guide_url = pdp.get("sizeGuideUrl") or ""
            size_guide_html = fetch_size_guide_html(size_guide_url) if size_guide_url else ""
            size_guide = extract_size_guide(size_guide_html)
            sizes = pdp.get("sizes") or []
            if not sizes and size_guide.get("rows"):
                sizes = [str(row[0]).strip() for row in size_guide["rows"] if row]
            row = {
                    "id": sku or card["id"],
                    "sku": sku or card["id"],
                    "title": title,
                    "gbpPrice": parse_gbp(pdp.get("priceText")) or float(card.get("gbpPrice") or 0),
                    "url": card["href"],
                    "leafId": leaf["id"],
                    "leafLabel": leaf.get("label") or "",
                    "leafLabelKo": leaf.get("leafLabelKo") or leaf.get("labelKo") or "",
                    "collections": list(dict.fromkeys(leaf.get("collections") or [leaf["id"]])),
                    "color": {"label": pdp.get("color") or ""},
                    "details": [] if blocked else (pdp.get("details") or []),
                    "sizes": sizes,
                    "sizeGuideUrl": size_guide_url,
                    "sizeGuide": size_guide,
                    "images": local_images,
                    "remoteImages": remote_images,
                    # WAF / unknown → None (never force sold-out). Only False when
                    # the PDP scrape returned an explicit out-of-stock signal.
                    "availability": (
                        None
                        if blocked
                        else (
                            None
                            if pdp.get("availability") is None
                            else bool(pdp.get("availability"))
                        )
                    ),
                    "availabilityConfidence": (
                        "blocked"
                        if blocked
                        else (pdp.get("availabilityConfidence") or "unknown")
                    ),
                    "scrapeBlocked": bool(blocked),
                    "breadcrumb": pdp.get("breadcrumb") or [],
                    "categoryLabel": pdp.get("categoryLabel") or "",
                }
            # Prefer official SFCC stock (reliable even when HTML WAF interferes).
            try:
                row = apply_sfcc_availability(row)
                time.sleep(0.12)
            except Exception:
                pass
            rows.append(row)
        return rows

    return with_browser(run, headed=headed)
