#!/usr/bin/env python3
"""Scrape Dior GB Jewelry & Timepieces → Dior Icons curated hub (~14 SKUs).

Discovery landing (not a standard PLP) — pulls Algolia namespaces from
__NEXT_DATA__ and materialises rows that merge into di-catalog via
di-icons-catalog-raw.json (collections union with jewelry/timepieces).

  PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \\
    python3 scripts/scrape-di-icons.py
  python3 scripts/merge-di-catalog-ko.py
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from di_common import (  # noqa: E402
    BASE,
    ICONS_LEAVES,
    IMG_ROOT,
    LANG,
    PARENT_COLS_ICONS,
    UA,
    algolia_merch_hits_by_codes,
    clean_dior_description,
    download_image,
    extract_next_data,
    gallery_urls_from_merch_hit,
    image_urls_from_hit,
    slugify,
)

OUT_RAW = ROOT / "src/data/di/di-icons-catalog-raw.json"
OUT_LEAVES = ROOT / "src/data/di/di-icons-leaves.json"
HUB = f"{BASE}/{LANG}/fashion/jewelry-timepieces/dior-icons"


def log(msg: str) -> None:
    print(msg, flush=True)


def oid_to_code(oid: str) -> str:
    s = (oid or "").replace("prd-", "").replace("_", "")
    if len(s) > 4:
        return f"{s[:-4]}_{s[-4:]}"
    return s


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


def hits_from_hub(page) -> list[dict]:
    page.goto(HUB, wait_until="domcontentloaded", timeout=120000)
    accept_cookies(page)
    time.sleep(2.5)
    for _ in range(8):
        page.mouse.wheel(0, 4000)
        time.sleep(0.4)
    pp = ((extract_next_data(page.content()) or {}).get("props") or {}).get(
        "pageProps"
    ) or {}
    by_code: dict[str, dict] = {}
    qpd = pp.get("queriesProductsDictionnary") or {}
    for ns, block in qpd.items():
        if "dior-icons" not in str(ns):
            continue
        for h in block.get("hits") or []:
            oid = (h.get("objectID") or "").strip()
            code = (h.get("code") or h.get("sku") or oid_to_code(oid)).strip()
            if not code:
                continue
            if "_" not in code and len(code) > 4:
                code = oid_to_code(code)
            # Normalise PLP-shaped hit for image_urls_from_hit / merch
            hit = dict(h)
            hit["code"] = code
            if not hit.get("productLink"):
                hit["productLink"] = {"uri": f"/{LANG}/fashion/products/{code}"}
            by_code[code] = hit
            log(f"  ns={ns} {code} {(h.get('title') or '')[:40]}")
    # Fallback: partialFiltersState objectIDs only
    if not by_code:
        pfs = pp.get("partialFiltersState") or {}
        for r in ((pfs.get("result") or {}).get("results") or []):
            oid = (r.get("objectID") or "").strip()
            code = oid_to_code(oid)
            if code:
                by_code[code] = {
                    "code": code,
                    "objectID": oid,
                    "productLink": {"uri": f"/{LANG}/fashion/products/{code}"},
                }
    log(f"hub unique={len(by_code)}")
    return list(by_code.values())


def hit_to_row(hit: dict, leaf: dict, merch: dict | None) -> dict:
    code = (hit.get("code") or "").strip()
    title = (hit.get("title") or hit.get("title_int") or hit.get("titleInt") or "").strip()
    subtitle = (
        hit.get("subtitle") or hit.get("subtitle_int") or hit.get("subtitleInt") or ""
    ).strip()
    price = hit.get("price") or {}
    gbp = price.get("value") if isinstance(price, dict) else None
    if gbp is None and isinstance(price, dict) and price.get("amount") is not None:
        try:
            gbp = float(price["amount"])
        except (TypeError, ValueError):
            gbp = None
    link = (hit.get("productLink") or {}).get("uri") or f"/{LANG}/fashion/products/{code}"
    remote = image_urls_from_hit(hit)
    desc = ""
    if merch:
        title = (merch.get("title") or merch.get("name") or title).strip() or title
        desc = clean_dior_description(merch.get("description") or "")
        gal = gallery_urls_from_merch_hit(merch)
        if gal:
            merged, seen = [], set()
            for u in list(gal) + remote:
                b = u.split("?")[0]
                if b in seen:
                    continue
                seen.add(b)
                merged.append(u)
            remote = merged
        mp = merch.get("price") or {}
        if isinstance(mp, dict) and mp.get("value") is not None:
            gbp = mp.get("value")
    local = materialize_images(code, remote)
    if not desc and subtitle:
        desc = f"{title}. {subtitle}".strip(". ")
    return {
        "id": code,
        "sku": hit.get("sku") or code,
        "title": title,
        "subtitle": subtitle,
        "gbpPrice": gbp,
        "url": f"{BASE}{link}" if link.startswith("/") else link,
        "leafId": leaf["id"],
        "leafLabel": leaf["label"],
        "leafLabelKo": leaf["labelKo"],
        "collections": [*PARENT_COLS_ICONS, leaf["id"]],
        "color": hit.get("color") or {},
        "details": {
            "paragraphs": [desc] if desc else [],
            "bullets": [subtitle] if subtitle else [],
            "specs": [],
        },
        "images": local,
        "remoteImages": remote,
    }


def main() -> None:
    leaf = ICONS_LEAVES[0]
    OUT_LEAVES.write_text(json.dumps(ICONS_LEAVES, indent=2, ensure_ascii=False) + "\n")

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.webkit.launch(headless=True)
        ctx = browser.new_context(
            user_agent=UA,
            locale="en-GB",
            viewport={"width": 1440, "height": 900},
        )
        page = ctx.new_page()
        hits = hits_from_hub(page)
        browser.close()

    codes = [(h.get("code") or "").strip() for h in hits]
    codes = [c for c in codes if c]
    merch: dict[str, dict] = {}
    try:
        merch = algolia_merch_hits_by_codes(codes)
        log(f"algolia merch {len(merch)}/{len(codes)}")
    except Exception as e:
        log(f"WARN algolia: {e}")

    products = [hit_to_row(h, leaf, merch.get((h.get("code") or "").strip())) for h in hits]
    OUT_RAW.write_text(
        json.dumps(
            {
                "scrapedAt": datetime.now(timezone.utc).isoformat(),
                "hub": HUB,
                "leaves": ICONS_LEAVES,
                "products": products,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
    log(f"DONE products={len(products)} → {OUT_RAW}")


if __name__ == "__main__":
    main()
