#!/usr/bin/env python3
"""Scrape Belstaff Icons / Motorcycle / Sale → merge into bs-catalog-raw + images + details."""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "src/data/bs/bs-catalog-raw.json"
IMG_ROOT = ROOT / "public/products/bs-pdp"
CHART_CACHE = ROOT / "src/data/bs/bs-sizechart-cache.json"
DETAILS_ITEM = ROOT / "src/data/bs/bs-details-by-item.json"
DETAILS_HANDLE = ROOT / "src/data/bs/bs-details-cache.json"

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
}

# (shopify collection handle, internal channel)
COLLECTIONS = [
    ("men-icons", "men-icons"),
    ("women-icons", "women-icons"),
    ("men-motorcycle", "men-motorcycle"),
    ("women-motorcycle", "women-motorcycle"),
    ("mens-sale", "mens-sale"),
    ("womens-sale", "womens-sale"),
]

MEASURE_KO = {
    "Chest": "가슴",
    "Bust": "가슴",
    "Waist": "허리",
    "Hip": "엉덩이",
    "Overarm": "팔 길이",
    "Sleeve": "소매",
    "Inside Leg": "인심",
    "Inseam": "인심",
    "Foot Length": "발 길이",
    "Thigh": "허벅지",
}

WOMEN_CHANNELS = {"women-icons", "women-motorcycle", "womens-sale"}


def fetch(url: str, accept: str = "*/*", retries: int = 8) -> bytes:
    for i in range(retries):
        req = urllib.request.Request(
            url,
            headers={**UA, "Accept": accept, "Referer": "https://belstaff.com/"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 10 + i * 6
                print(f"  429 wait {wait}s", flush=True)
                time.sleep(wait)
                continue
            raise
        except Exception as e:
            print(f"  err {e} retry {i}", flush=True)
            time.sleep(2 + i)
    raise RuntimeError(url)


def paginate_collection(handle: str) -> list[dict]:
    products: list[dict] = []
    page = 1
    while page <= 20:
        url = (
            f"https://belstaff.com/collections/{handle}/products.json"
            f"?limit=250&page={page}"
        )
        print(f"  fetch {handle} page={page}", flush=True)
        time.sleep(2.5)
        data = json.loads(fetch(url, "application/json").decode("utf-8", "replace"))
        batch = data.get("products") or []
        print(f"    n={len(batch)}", flush=True)
        if not batch:
            break
        products.extend(batch)
        if len(batch) < 250:
            break
        page += 1
    return products


def tag_list(tags) -> list[str]:
    if isinstance(tags, list):
        return [str(t).strip() for t in tags if str(t).strip()]
    if isinstance(tags, str):
        return [t.strip() for t in tags.split(",") if t.strip()]
    return []


def tag_value(tags: list[str], prefix: str) -> str | None:
    for t in tags:
        if t.startswith(prefix):
            return t[len(prefix) :].strip()
    return None


def is_mens_bleed(ptype: str, tags: list[str], channel: str) -> bool:
    """Skip men's SKUs that bleed into women collections."""
    if channel not in WOMEN_CHANNELS:
        return False
    if (ptype or "").endswith("- M"):
        return True
    lower = {t.lower() for t in tags}
    if "men" in lower or "menswear" in lower:
        if "women" not in lower and "womenswear" not in lower:
            if not any("women" in t for t in lower):
                return True
    return False


def parse_size_chart_html(html: str) -> dict | None:
    m = re.search(
        r'id="size-guide-drawer-guide-panel"[\s\S]*?<table class="drw-SizeGuide_Table">([\s\S]*?)</table>',
        html,
    )
    if not m:
        m = re.search(r'<table class="drw-SizeGuide_Table">([\s\S]*?)</table>', html)
    if not m:
        return None
    table = m.group(1)
    headers: list[str] = []
    rows: list[list[str]] = []
    measure_keys: list[str] = []
    for row_html in re.findall(r"<tr[^>]*>([\s\S]*?)</tr>", table):
        cells_raw = re.findall(r"<t[hd][^>]*>([\s\S]*?)</t[hd]>", row_html)
        if not cells_raw:
            continue
        labels: list[str] = []
        measure: dict[str, str] | None = None
        is_header = False
        for cell in cells_raw:
            heads = re.findall(r'drw-SizeGuide_HeadingText[^>]*>\s*([^<]+)', cell)
            pills = re.findall(r'drw-SizeGuide_Pill[^>]*>\s*([^<]+)', cell)
            keys = re.findall(r'ListKey">\s*([^<]+)', cell)
            vals = re.findall(r'cm-value="([^"]+)"', cell)
            if heads:
                is_header = True
                h = unescape(heads[0].strip())
                h = re.sub(r"\s*-\s*CM$", "", h, flags=re.I).strip()
                if h.lower().startswith("measure"):
                    continue
                headers.append("사이즈" if h.lower() == "size" else h)
            elif keys and vals:
                measure = {k.strip(): v.strip() for k, v in zip(keys, vals)}
            elif pills:
                labels.append(unescape(pills[0].strip()))
        if is_header or not measure:
            continue
        if not measure_keys:
            measure_keys = list(measure.keys())
        rows.append([*labels, *[measure.get(k, "—") for k in measure_keys]])
    if not rows or not measure_keys:
        return None
    n_label = len(rows[0]) - len(measure_keys)
    if len(headers) < n_label:
        defaults = ["UK", "US", "EU/IT", "사이즈"]
        headers = (headers + defaults)[:n_label]
    else:
        headers = headers[:n_label]
    out_headers = [*headers, *[MEASURE_KO.get(k, k) for k in measure_keys]]
    if "사이즈" in out_headers:
        si = out_headers.index("사이즈")
        if si > 0:

            def rot(vals: list[str]) -> list[str]:
                return [vals[si], *[vals[i] for i in range(len(vals)) if i != si]]

            out_headers = rot(out_headers)
            rows = [rot(r) for r in rows]
    return {"headers": out_headers, "rows": rows, "measureKeys": measure_keys}


def parse_accordion(html: str, accordion_id: str) -> list[str]:
    m = re.search(
        rf'id="{re.escape(accordion_id)}"[\s\S]*?<ul class="prd-Accordion_List">([\s\S]*?)</ul>',
        html,
    )
    if not m:
        return []
    items = []
    for li in re.findall(r"<li[^>]*>([\s\S]*?)</li>", m.group(1)):
        t = unescape(re.sub(r"<[^>]+>", " ", li))
        t = re.sub(r"\s+", " ", t).strip()
        if t:
            items.append(t)
    return items


def fetch_pdp_extras(handle: str) -> tuple[dict | None, dict]:
    html = fetch(f"https://belstaff.com/products/{handle}", "text/html").decode(
        "utf-8", "replace"
    )
    chart = parse_size_chart_html(html)
    details = parse_accordion(html, "product-accordion-detail")
    care = parse_accordion(html, "product-accordion-care")
    fit = []
    m = re.search(
        r'aria-controls="(product-accordion-[^"]+)"[^>]*>\s*Size and fit', html
    )
    if m:
        fit = parse_accordion(html, m.group(1))
    return chart, {"details": details, "care": care, "fit": fit}


def cdn_url(src: str, width: int = 1200) -> str:
    if not src:
        return src
    if src.startswith("//"):
        src = "https:" + src
    if "width=" in src:
        return src
    sep = "&" if "?" in src else "?"
    return f"{src}{sep}width={width}"


def download_images(products: list[dict]) -> tuple[int, int]:
    saved = skipped = 0
    IMG_ROOT.mkdir(parents=True, exist_ok=True)
    total = len(products)
    for idx, p in enumerate(products, 1):
        handle = p["handle"]
        folder = IMG_ROOT / handle
        folder.mkdir(parents=True, exist_ok=True)
        urls = (p.get("images") or [])[:8]
        if idx == 1 or idx % 20 == 0 or idx == total:
            print(f"  images {idx}/{total} {handle}", flush=True)
        for i, src in enumerate(urls, 1):
            dest = folder / f"{i}.jpg"
            if dest.exists() and dest.stat().st_size > 2000:
                skipped += 1
                continue
            try:
                data = fetch(cdn_url(src, 1200), "*/*")
                if len(data) < 500:
                    continue
                dest.write_bytes(data)
                saved += 1
            except Exception as e:
                print(f"  warn image {handle}/{i}: {e}", flush=True)
            time.sleep(0.03)
    return saved, skipped


def item_code_of(p: dict) -> str:
    for t in p.get("tags") or []:
        if t.startswith("Item Code"):
            return t.split(":", 1)[-1].strip()
    return "handle:" + p["handle"]


def scrape() -> None:
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    IMG_ROOT.mkdir(parents=True, exist_ok=True)

    existing: dict[str, dict] = {}
    collections_meta: dict[str, list[str]] = {}
    if RAW_PATH.exists():
        prev = json.loads(RAW_PATH.read_text())
        for p in prev.get("products") or []:
            if p.get("handle"):
                existing[p["handle"]] = p
        collections_meta = dict(prev.get("collections") or {})

    print("Warm…", flush=True)
    fetch("https://belstaff.com/pages/find-your-icon", "text/html")
    time.sleep(2)

    touched: list[str] = []
    for shopify_handle, channel in COLLECTIONS:
        print(f"Scraping {shopify_handle} → {channel}", flush=True)
        raw_list = paginate_collection(shopify_handle)
        handles: list[str] = []
        skipped_bleed = 0
        for raw in raw_list:
            h = raw.get("handle") or ""
            if not h:
                continue
            if (raw.get("product_type") or "") == "Gift Cards":
                continue
            if "gift-card" in h or "e-gift" in h:
                continue
            tags = tag_list(raw.get("tags"))
            ptype = raw.get("product_type") or ""
            if is_mens_bleed(ptype, tags, channel):
                skipped_bleed += 1
                continue
            handles.append(h)
            touched.append(h)
            images = [
                img.get("src") for img in (raw.get("images") or []) if img.get("src")
            ]
            variants = []
            for v in raw.get("variants") or []:
                try:
                    price_f = float(v.get("price") or 0)
                except Exception:
                    price_f = 0.0
                compare = v.get("compare_at_price")
                try:
                    compare_f = (
                        float(compare) if compare not in (None, "", "0.00") else None
                    )
                except Exception:
                    compare_f = None
                variants.append(
                    {
                        "id": v.get("id"),
                        "sku": v.get("sku") or "",
                        "title": v.get("title") or "",
                        "option1": v.get("option1"),
                        "option2": v.get("option2"),
                        "option3": v.get("option3"),
                        "price": price_f,
                        "compare_at_price": compare_f,
                        "available": bool(v.get("available")),
                    }
                )
            color = tag_value(tags, "Colour Title :") or tag_value(
                tags, "Colour Title:"
            )
            if not color:
                for opt in raw.get("options") or []:
                    if str(opt.get("name") or "").lower() in {"colour", "color"}:
                        vals = opt.get("values") or []
                        color = vals[0] if vals else None
            if h in existing:
                e = existing[h]
                cols = e.setdefault("channels", [])
                if channel not in cols:
                    cols.append(channel)
                e["title"] = raw.get("title") or e.get("title")
                e["body_html"] = raw.get("body_html") or e.get("body_html")
                e["tags"] = tags
                e["images"] = images or e.get("images")
                e["variants"] = variants
                e["options"] = raw.get("options") or e.get("options")
                e["colorName"] = color or e.get("colorName") or "Default"
                e["product_type"] = ptype or e.get("product_type")
                e["published_at"] = raw.get("published_at") or e.get("published_at")
            else:
                existing[h] = {
                    "id": raw.get("id"),
                    "handle": h,
                    "title": raw.get("title") or "",
                    "body_html": raw.get("body_html") or "",
                    "product_type": ptype,
                    "tags": tags,
                    "published_at": raw.get("published_at"),
                    "created_at": raw.get("created_at"),
                    "images": images,
                    "options": raw.get("options") or [],
                    "variants": variants,
                    "colorName": color or "Default",
                    "channels": [channel],
                }
        collections_meta[shopify_handle] = handles
        print(
            f"  → {len(handles)} (bleed skipped={skipped_bleed}, unique total={len(existing)})",
            flush=True,
        )

    touched_set = set(touched)
    chart_cache = json.loads(CHART_CACHE.read_text()) if CHART_CACHE.exists() else {}
    item_cache = json.loads(DETAILS_ITEM.read_text()) if DETAILS_ITEM.exists() else {}
    handle_cache = (
        json.loads(DETAILS_HANDLE.read_text()) if DETAILS_HANDLE.exists() else {}
    )

    by_type: dict[str, list[dict]] = defaultdict(list)
    for h in touched_set:
        p = existing[h]
        by_type[p.get("product_type") or "unknown"].append(p)

    print("Size charts for new product types…", flush=True)
    for ptype, members in sorted(by_type.items()):
        if ptype in chart_cache and chart_cache[ptype].get("rows"):
            print(f"  cache hit {ptype}", flush=True)
            continue
        pick = next(
            (
                m
                for m in members
                if any(v.get("available") for v in m.get("variants") or [])
            ),
            members[0],
        )
        print(f"  chart {ptype} via {pick['handle']}", flush=True)
        try:
            time.sleep(1.3)
            chart, _det = fetch_pdp_extras(pick["handle"])
            if chart:
                chart_cache[ptype] = chart
                CHART_CACHE.write_text(
                    json.dumps(chart_cache, ensure_ascii=False, indent=2) + "\n"
                )
                print(f"    rows={len(chart['rows'])}", flush=True)
            else:
                print("    no chart", flush=True)
        except Exception as e:
            print(f"    fail {e}", flush=True)

    by_item: dict[str, list[dict]] = defaultdict(list)
    for h in touched_set:
        by_item[item_code_of(existing[h])].append(existing[h])

    print(f"Details for {len(by_item)} item codes…", flush=True)
    i = 0
    for code, members in sorted(by_item.items()):
        i += 1
        if item_cache.get(code, {}).get("details") or any(
            m.get("details") for m in members
        ):
            det = item_cache.get(code)
            if not det:
                src = next((m for m in members if m.get("details")), None)
                if src:
                    det = {
                        "details": src.get("details") or [],
                        "care": src.get("care") or [],
                        "fit": src.get("fit") or [],
                    }
            if det:
                for m in members:
                    if not m.get("details"):
                        m["details"] = det.get("details") or []
                        m["care"] = det.get("care") or []
                        m["fit"] = det.get("fit") or []
            continue
        pick = next(
            (
                m
                for m in members
                if any(v.get("available") for v in m.get("variants") or [])
            ),
            members[0],
        )
        print(f"  details {i}/{len(by_item)} {code} via {pick['handle']}", flush=True)
        try:
            time.sleep(1.2)
            _chart, det = fetch_pdp_extras(pick["handle"])
            item_cache[code] = det
            handle_cache[pick["handle"]] = det
            for m in members:
                m["details"] = det.get("details") or []
                m["care"] = det.get("care") or []
                m["fit"] = det.get("fit") or []
            print(f"    n={len(det.get('details') or [])}", flush=True)
        except Exception as e:
            print(f"    fail {e}", flush=True)
        if i % 15 == 0:
            DETAILS_ITEM.write_text(
                json.dumps(item_cache, ensure_ascii=False, indent=2) + "\n"
            )

    for h in touched_set:
        p = existing[h]
        p["sizeChart"] = chart_cache.get(p.get("product_type") or "") or p.get(
            "sizeChart"
        )
        code = item_code_of(p)
        det = item_cache.get(code) or handle_cache.get(h) or {}
        if det.get("details") and not p.get("details"):
            p["details"] = det.get("details") or []
            p["care"] = det.get("care") or []
            p["fit"] = det.get("fit") or []

    DETAILS_ITEM.write_text(json.dumps(item_cache, ensure_ascii=False, indent=2) + "\n")
    DETAILS_HANDLE.write_text(
        json.dumps(handle_cache, ensure_ascii=False, indent=2) + "\n"
    )
    CHART_CACHE.write_text(json.dumps(chart_cache, ensure_ascii=False, indent=2) + "\n")

    products = list(existing.values())
    payload = {
        "scrapedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "collections": collections_meta,
        "products": products,
    }
    RAW_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote raw ({len(products)} products)", flush=True)

    # Only download images for newly touched SKUs missing local files
    need_img = []
    for h in touched_set:
        p = existing[h]
        folder = IMG_ROOT / h
        if not folder.exists() or not any(folder.glob("*.jpg")):
            need_img.append(p)
    print(f"Downloading images for {len(need_img)} SKUs…", flush=True)
    if need_img:
        saved, skipped = download_images(need_img)
        print(f"Images saved={saved} skipped={skipped}", flush=True)
    else:
        print("Images all present", flush=True)


if __name__ == "__main__":
    scrape()
