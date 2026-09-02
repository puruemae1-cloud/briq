#!/usr/bin/env python3
"""Scrape Dior GB Men's Essentials hub and route SKUs into shoes / RTW / accessories.

Hub mixes categories:
  https://www.dior.com/en_gb/fashion/mens-fashion/dior-essentials

Routing (Algolia category.lvl1 + fallbacks):
  Shoes      → Shoes → Dior → 남성용
  Clothing   → Luxury → Dior → 남성용 (RTW)
  Everything else → Accessories → Dior → 남성용

  PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \\
    python3 scripts/scrape-di-men-essentials.py
  python3 scripts/merge-di-catalog-ko.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from di_common import (  # noqa: E402
    BASE,
    IMG_ROOT,
    MEN_ESSENTIALS_HUB,
    MEN_ESSENTIALS_LEAF,
    UA,
    algolia_merch_hits_by_codes,
    classify_di_men_essentials,
    clean_dior_description,
    download_image,
    extract_next_data,
    gallery_urls_from_merch_hit,
    image_urls_from_hit,
    plp_hits_from_next,
    slugify,
)

OUT_RAW = ROOT / "src/data/di/di-men-essentials-catalog-raw.json"
PDP_CACHE = ROOT / "src/data/di/di-men-essentials-pdp-cache.json"
HUB = MEN_ESSENTIALS_HUB


def log(msg: str) -> None:
    print(msg, flush=True)


def accept_cookies(page) -> None:
    for sel in (
        "#onetrust-accept-btn-handler",
        'button:has-text("Accept All")',
        'button:has-text("Accept")',
    ):
        try:
            page.locator(sel).first.click(timeout=2500)
            time.sleep(0.8)
            return
        except Exception:
            pass


def load_json(path: Path, default):
    if path.is_file():
        return json.loads(path.read_text())
    return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def scrape_plp_hits(page) -> list[dict]:
    leaf = MEN_ESSENTIALS_LEAF
    url = leaf["url"]
    log(f"PLP {leaf['id']} {url}")
    page.goto(url, wait_until="domcontentloaded", timeout=120000)
    accept_cookies(page)
    time.sleep(2.2)
    for _ in range(16):
        page.mouse.wheel(0, 5000)
        time.sleep(0.5)
    html = page.content()
    data = extract_next_data(html) or {}
    hits = plp_hits_from_next(data)
    pag = ((data.get("props") or {}).get("pageProps") or {}).get("pagination") or {}
    next_url = pag.get("next")
    page_i = 1
    while next_url and page_i < 40:
        page_i += 1
        log(f"  page {page_i} {next_url}")
        page.goto(next_url, wait_until="domcontentloaded", timeout=120000)
        time.sleep(1.6)
        for _ in range(8):
            page.mouse.wheel(0, 4000)
            time.sleep(0.4)
        data2 = extract_next_data(page.content()) or {}
        more = plp_hits_from_next(data2)
        if not more:
            break
        hits.extend(more)
        pag2 = ((data2.get("props") or {}).get("pageProps") or {}).get("pagination") or {}
        next_url = pag2.get("next")
    by_code: dict[str, dict] = {}
    for h in hits:
        code = (h.get("code") or h.get("objectID") or "").strip()
        if not code:
            continue
        by_code[code] = h
    log(f"  hits={len(by_code)}")
    return list(by_code.values())


def materialize_images(code: str, urls: list[str]) -> list[str]:
    folder = slugify(code)
    out: list[str] = []
    for i, url in enumerate(urls, start=1):
        if not url:
            continue
        rel = f"/products/di-pdp/{folder}/{i}.jpg"
        dest = IMG_ROOT / folder / f"{i}.jpg"
        try:
            if not dest.exists() or dest.stat().st_size < 800:
                download_image(url, dest)
            if dest.exists() and dest.stat().st_size > 800:
                out.append(rel)
        except Exception as e:
            log(f"  WARN img {code} #{i}: {e}")
    return out


def hit_to_row(hit: dict, pdp: dict | None, merch: dict | None) -> dict:
    code = (hit.get("code") or "").strip()
    title = (hit.get("title") or hit.get("titleInt") or "").strip()
    subtitle = (hit.get("subtitle") or hit.get("subtitleInt") or "").strip()
    price = hit.get("price") or {}
    gbp = price.get("value") if isinstance(price, dict) else None
    link = (hit.get("productLink") or {}).get("uri") or f"/en_gb/fashion/products/{code}"
    source_url = f"{BASE}{link}" if link.startswith("/") else link
    remote_imgs = image_urls_from_hit(hit)
    if pdp and pdp.get("gallery"):
        merged: list[str] = []
        seen: set[str] = set()
        for u in list(pdp["gallery"]) + remote_imgs:
            b = u.split("?")[0]
            if b in seen:
                continue
            seen.add(b)
            merged.append(u)
        remote_imgs = merged
    local_imgs = materialize_images(code, remote_imgs)
    desc = clean_dior_description((pdp or {}).get("description") or "")
    if not desc and subtitle:
        desc = f"{title}. {subtitle}".strip(". ")
    title = (pdp or {}).get("title") or title
    if title.lower().startswith("page unavailable"):
        title = (hit.get("title") or hit.get("titleInt") or "").strip()

    bucket, collections, leaf = classify_di_men_essentials(
        title=title,
        subtitle=subtitle,
        url=source_url,
        merch=merch,
    )
    # Keep hub provenance without creating a shop nav leaf.
    collections = list(dict.fromkeys([*collections, "di-men-essentials"]))

    return {
        "id": code,
        "sku": hit.get("sku") or code,
        "title": title,
        "subtitle": subtitle,
        "gbpPrice": gbp,
        "url": source_url,
        "leafId": leaf["id"],
        "leafLabel": leaf["label"],
        "leafLabelKo": leaf["labelKo"],
        "essentialsBucket": bucket,
        "collections": collections,
        "color": hit.get("color") or {},
        "details": {
            "paragraphs": [desc] if desc else [],
            "bullets": [subtitle] if subtitle else [],
            "specs": [],
        },
        "images": local_imgs,
        "remoteImages": remote_imgs,
        "algoliaCategory": (merch or {}).get("category"),
        "productFamily": (merch or {}).get("product_family"),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-pdp", type=int, default=0)
    ap.add_argument("--skip-pdp", action="store_true")
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()

    existing = load_json(OUT_RAW, {"products": []})
    by_id: dict[str, dict] = {
        p["id"]: p for p in existing.get("products") or [] if p.get("id")
    }
    pdp_cache = load_json(PDP_CACHE, {})

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.webkit.launch(headless=not args.headed)
        ctx = browser.new_context(
            user_agent=UA,
            locale="en-GB",
            viewport={"width": 1440, "height": 900},
        )
        page = ctx.new_page()
        page.goto(HUB, wait_until="domcontentloaded", timeout=120000)
        accept_cookies(page)
        time.sleep(2)

        hits = scrape_plp_hits(page)
        codes = [(h.get("code") or "").strip() for h in hits]
        codes = [c for c in codes if c]
        merch: dict[str, dict] = {}
        if not args.skip_pdp:
            try:
                merch = algolia_merch_hits_by_codes(codes)
                log(f"  algolia merch {len(merch)}/{len(codes)}")
            except Exception as e:
                log(f"  WARN algolia: {e}")

        buckets: Counter[str] = Counter()
        for i, hit in enumerate(hits, start=1):
            code = (hit.get("code") or "").strip()
            if not code:
                continue
            link = (hit.get("productLink") or {}).get("uri") or ""
            pdp = pdp_cache.get(code)
            mh = merch.get(code)
            if mh and not args.skip_pdp:
                desc = clean_dior_description(mh.get("description") or "")
                gal = gallery_urls_from_merch_hit(mh)
                if desc or gal:
                    pdp = {
                        "title": mh.get("title") or mh.get("name") or "",
                        "description": desc,
                        "reference": code,
                        "gallery": gal,
                        "sourceUrl": f"{BASE}{link}" if link.startswith("/") else link,
                        "fetchedAt": datetime.now(timezone.utc).isoformat(),
                        "source": "algolia-merch",
                        "material": mh.get("material"),
                        "madein": mh.get("madein"),
                        "characteristics": mh.get("characteristics"),
                        "category": mh.get("category"),
                        "product_family": mh.get("product_family"),
                    }
                    pdp_cache[code] = pdp
            elif not args.skip_pdp and (
                not pdp or not clean_dior_description(pdp.get("description") or "")
            ):
                if not args.max_pdp or i <= args.max_pdp:
                    log(f"  [{i}/{len(hits)}] no merch for {code} — PLP only")

            row = hit_to_row(hit, pdp, mh or pdp)
            buckets[str(row.get("essentialsBucket") or "?")] += 1
            prev = by_id.get(code)
            if prev:
                cols = list(
                    dict.fromkeys(
                        (prev.get("collections") or []) + (row.get("collections") or [])
                    )
                )
                row["collections"] = cols
                if len(prev.get("images") or []) > len(row.get("images") or []):
                    row["images"] = prev["images"]
                if not (row.get("details") or {}).get("paragraphs"):
                    row["details"] = prev.get("details") or row["details"]
            by_id[code] = row
            if i % 15 == 0:
                log(f"  progress {i}/{len(hits)} saved={len(by_id)} buckets={dict(buckets)}")
                save_json(PDP_CACHE, pdp_cache)
                save_json(
                    OUT_RAW,
                    {
                        "scrapedAt": datetime.now(timezone.utc).isoformat(),
                        "hub": HUB,
                        "leaf": MEN_ESSENTIALS_LEAF,
                        "bucketCounts": dict(buckets),
                        "products": list(by_id.values()),
                    },
                )

        save_json(PDP_CACHE, pdp_cache)
        save_json(
            OUT_RAW,
            {
                "scrapedAt": datetime.now(timezone.utc).isoformat(),
                "hub": HUB,
                "leaf": MEN_ESSENTIALS_LEAF,
                "bucketCounts": dict(buckets),
                "products": list(by_id.values()),
            },
        )
        browser.close()

    log(f"DONE products={len(by_id)} buckets={dict(buckets)} → {OUT_RAW}")


if __name__ == "__main__":
    main()
