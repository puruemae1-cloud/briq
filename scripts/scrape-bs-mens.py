#!/usr/bin/env python3
"""Scrape Belstaff UK mens collections → raw JSON + PDP images."""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "src/data/bs/bs-catalog-raw.json"
IMG_ROOT = ROOT / "public/products/bs-pdp"
CHART_CACHE = ROOT / "src/data/bs/bs-sizechart-cache.json"

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
}

COLLECTIONS = [
    ("men-new-arrivals", "new"),
    ("men-outerwear", "outerwear"),
    ("men-clothing", "clothing"),
    ("men-footwear", "footwear"),
    ("men-accessories", "accessories"),
]

MEASURE_KO = {
    "Chest": "가슴",
    "Waist": "허리",
    "Hip": "엉덩이",
    "Overarm": "팔 길이",
    "Sleeve": "소매",
    "Inside Leg": "인심",
    "Inseam": "인심",
    "Foot Length": "발 길이",
    "Thigh": "허벅지",
}


def fetch(url: str, accept: str = "*/*", retries: int = 6) -> bytes:
    for i in range(retries):
        req = urllib.request.Request(
            url,
            headers={**UA, "Accept": accept, "Referer": "https://belstaff.com/"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            body = e.read() if hasattr(e, "read") else b""
            if e.code == 429:
                wait = 8 + i * 6
                print(f"  429 {url} wait {wait}s", flush=True)
                time.sleep(wait)
                continue
            raise
        except Exception as e:
            print(f"  err {e} retry {i}", flush=True)
            time.sleep(2 + i)
    raise RuntimeError(f"failed {url}")


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


def parse_size_chart_html(html: str) -> dict | None:
    """Parse the primary (non Big & Tall) size-guide table from a Belstaff PDP."""
    m = re.search(
        r'id="size-guide-drawer-guide-panel"[\s\S]*?<table class="drw-SizeGuide_Table">([\s\S]*?)</table>',
        html,
    )
    if not m:
        m = re.search(
            r'<table class="drw-SizeGuide_Table">([\s\S]*?)</table>', html
        )
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
            else:
                text = unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", cell))).strip()
                if text and not text.lower().startswith("measure"):
                    labels.append(text)

        if is_header:
            continue
        if not measure:
            continue
        if not measure_keys:
            measure_keys = list(measure.keys())
        row = [*labels, *[measure.get(k, "—") for k in measure_keys]]
        rows.append(row)

    if not rows or not measure_keys:
        return None

    n_label = len(rows[0]) - len(measure_keys)
    if len(headers) < n_label:
        defaults = ["UK", "US", "EU/IT", "사이즈"]
        headers = (headers + defaults)[:n_label]
    else:
        headers = headers[:n_label]

    out_headers = [*headers, *[MEASURE_KO.get(k, k) for k in measure_keys]]

    # Put alpha/size column first when present
    if "사이즈" in out_headers:
        si = out_headers.index("사이즈")
        if si > 0:

            def rot(vals: list[str]) -> list[str]:
                return [vals[si], *[vals[i] for i in range(len(vals)) if i != si]]

            out_headers = rot(out_headers)
            rows = [rot(r) for r in rows]

    return {
        "headers": out_headers,
        "rows": rows,
        "measureKeys": measure_keys,
    }


def fetch_size_chart(handle: str) -> dict | None:
    html = fetch(
        f"https://belstaff.com/products/{handle}", "text/html"
    ).decode("utf-8", "replace")
    return parse_size_chart_html(html)


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
        if idx == 1 or idx % 25 == 0 or idx == total:
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


def scrape() -> dict:
    by_handle: dict[str, dict] = {}
    collections_meta: dict[str, list[str]] = {}
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    IMG_ROOT.mkdir(parents=True, exist_ok=True)

    # warm cookies / rate limit
    print("Warm home…", flush=True)
    fetch("https://belstaff.com/", "text/html")
    time.sleep(2)

    for shopify_handle, channel in COLLECTIONS:
        print(f"Scraping {shopify_handle} → {channel}", flush=True)
        raw_list = paginate_collection(shopify_handle)
        handles = []
        for raw in raw_list:
            h = raw.get("handle") or ""
            if not h:
                continue
            if (raw.get("product_type") or "") == "Gift Cards":
                continue
            if "gift-card" in h or "e-gift" in h:
                continue
            handles.append(h)
            tags = tag_list(raw.get("tags"))
            images = []
            for img in raw.get("images") or []:
                src = img.get("src") or ""
                if src:
                    images.append(src)
            variants = []
            for v in raw.get("variants") or []:
                price = v.get("price")
                try:
                    price_f = float(price)
                except Exception:
                    price_f = 0.0
                compare = v.get("compare_at_price")
                try:
                    compare_f = float(compare) if compare not in (None, "", "0.00") else None
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
            color = (
                tag_value(tags, "Colour Title :")
                or tag_value(tags, "Colour Title:")
                or (raw.get("options") or [{}])
            )
            if isinstance(color, list):
                # options fallback
                color = None
                for opt in raw.get("options") or []:
                    if str(opt.get("name") or "").lower() in {"colour", "color"}:
                        vals = opt.get("values") or []
                        color = vals[0] if vals else None
            entry = {
                "id": raw.get("id"),
                "handle": h,
                "title": raw.get("title") or "",
                "body_html": raw.get("body_html") or "",
                "product_type": raw.get("product_type") or "",
                "tags": tags,
                "published_at": raw.get("published_at"),
                "created_at": raw.get("created_at"),
                "images": images,
                "options": raw.get("options") or [],
                "variants": variants,
                "colorName": color or "Default",
                "channels": [channel],
            }
            if h in by_handle:
                existing = by_handle[h]
                for c in entry["channels"]:
                    if c not in existing["channels"]:
                        existing["channels"].append(c)
                # refresh stock/price/images
                existing["title"] = entry["title"]
                existing["body_html"] = entry["body_html"]
                existing["tags"] = entry["tags"]
                existing["images"] = entry["images"] or existing.get("images")
                existing["variants"] = entry["variants"]
                existing["options"] = entry["options"]
                existing["colorName"] = entry["colorName"]
                existing["product_type"] = entry["product_type"]
                existing["published_at"] = entry.get("published_at") or existing.get(
                    "published_at"
                )
            else:
                by_handle[h] = entry
        collections_meta[shopify_handle] = handles
        print(f"  → {len(handles)} (unique so far {len(by_handle)})", flush=True)

    products = list(by_handle.values())

    # Size charts: one representative per product_type
    chart_cache: dict[str, dict] = {}
    if CHART_CACHE.exists():
        chart_cache = json.loads(CHART_CACHE.read_text())
    by_type: dict[str, list[dict]] = {}
    for p in products:
        by_type.setdefault(p["product_type"] or "unknown", []).append(p)

    print("Fetching size charts by product_type…", flush=True)
    for ptype, members in sorted(by_type.items(), key=lambda x: x[0]):
        if ptype in chart_cache and chart_cache[ptype].get("rows"):
            print(f"  cache hit {ptype}", flush=True)
            continue
        # prefer in-stock
        pick = next(
            (m for m in members if any(v.get("available") for v in m["variants"])),
            members[0],
        )
        print(f"  chart {ptype} via {pick['handle']}", flush=True)
        try:
            time.sleep(1.2)
            chart = fetch_size_chart(pick["handle"])
            if chart:
                chart_cache[ptype] = chart
                CHART_CACHE.write_text(
                    json.dumps(chart_cache, ensure_ascii=False, indent=2) + "\n"
                )
                print(f"    rows={len(chart['rows'])}", flush=True)
            else:
                print("    no chart", flush=True)
        except Exception as e:
            print(f"    chart err {e}", flush=True)

    for p in products:
        p["sizeChart"] = chart_cache.get(p["product_type"] or "")

    payload = {
        "scrapedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "collections": collections_meta,
        "products": products,
    }
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAW_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {RAW_PATH.relative_to(ROOT)} ({len(products)} products)", flush=True)

    print("Downloading images…", flush=True)
    saved, skipped = download_images(products)
    print(f"Images saved={saved} skipped={skipped}", flush=True)
    return payload


if __name__ == "__main__":
    scrape()
