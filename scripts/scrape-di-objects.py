#!/usr/bin/env python3
"""Scrape Dior GB Maison → Objects via Playwright WebKit.

Stages (~205 items, pause between stages for machine stability):
  1 — Books + Notebooks
  2 — Desk Accessories + Paperweights + Leisure
  3 — Candleholders & Candles
  4 — Small Objects + Trinket Trays
  5 — Trays (+ fill All Objects gaps)

  python3 -m playwright install webkit
  python3 scripts/scrape-di-objects.py --stage 1
  # then pause / reboot if needed before stage 2…
  python3 scripts/build-di-catalog-from-ko-algolia.py   # or merge builder
  python3 scripts/check-catalog-korean.py --brand di --fail
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from di_common import (  # noqa: E402
    BASE,
    IMG_ROOT,
    LANG,
    PARENT_COLS_OBJECTS,
    OBJECTS_LEAVES,
    UA,
    algolia_merch_hits_by_codes,
    clean_dior_description,
    download_image,
    extract_next_data,
    gallery_urls_from_merch_hit,
    image_urls_from_hit,
    plp_hits_from_next,
    slugify,
)

OUT_RAW = ROOT / "src/data/di/di-objects-catalog-raw.json"
OUT_LEAVES = ROOT / "src/data/di/di-objects-leaves.json"
PDP_CACHE = ROOT / "src/data/di/di-objects-pdp-cache.json"

PDP_PAUSE = 1.0


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


def scrape_plp_hits(page, leaf: dict) -> list[dict]:
    url = leaf["url"]
    log(f"PLP {leaf['id']} {url}")
    page.goto(url, wait_until="domcontentloaded", timeout=120000)
    accept_cookies(page)
    time.sleep(2.5)
    for _ in range(12):
        page.mouse.wheel(0, 5000)
        time.sleep(0.6)
    html = page.content()
    data = extract_next_data(html) or {}
    hits = plp_hits_from_next(data)
    # follow pagination if present
    pag = ((data.get("props") or {}).get("pageProps") or {}).get("pagination") or {}
    next_url = pag.get("next")
    page_i = 1
    while next_url and page_i < 20:
        page_i += 1
        log(f"  page {page_i} {next_url}")
        page.goto(next_url, wait_until="domcontentloaded", timeout=120000)
        time.sleep(2)
        for _ in range(6):
            page.mouse.wheel(0, 4000)
            time.sleep(0.5)
        data2 = extract_next_data(page.content()) or {}
        more = plp_hits_from_next(data2)
        if not more:
            break
        hits.extend(more)
        pag2 = ((data2.get("props") or {}).get("pageProps") or {}).get("pagination") or {}
        next_url = pag2.get("next")
    cat_filter = (leaf.get("categoryFilter") or "").strip().lower()
    # dedupe by code
    by_code: dict[str, dict] = {}
    for h in hits:
        code = (h.get("code") or h.get("objectID") or "").strip()
        if not code:
            continue
        if cat_filter:
            blob = json.dumps(
                {
                    "c": h.get("category"),
                    "ci": h.get("categoryInt"),
                    "cats": h.get("categories"),
                    "t": h.get("title"),
                    "s": h.get("subtitle"),
                    "tags": h.get("tagsKeys"),
                },
                ensure_ascii=False,
            ).lower()
            if cat_filter not in blob and "paperweight" not in blob:
                continue
        by_code[code] = h
    log(f"  unique hits {len(by_code)}" + (f" (filter={cat_filter})" if cat_filter else ""))
    return list(by_code.values())


def parse_pdp(page, product_path: str) -> dict:
    """Visit PDP and pull description + extra gallery frames."""
    url = product_path if product_path.startswith("http") else f"{BASE}{product_path}"
    page.goto(url, wait_until="domcontentloaded", timeout=90000)
    time.sleep(2.2)
    title = ""
    try:
        title = (page.locator("h1").first.inner_text(timeout=3000) or "").strip()
    except Exception:
        pass
    if title.lower().startswith("page unavailable") or "요청" in title:
        return {
            "title": "",
            "description": "",
            "reference": "",
            "gallery": [],
            "sourceUrl": url,
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
            "unavailable": True,
        }
    # Click Description accordion / tab to reveal copy
    for sel in (
        'button:has-text("Description")',
        '[data-testid*="description"]',
        'text=Description',
    ):
        try:
            page.locator(sel).first.click(timeout=2000)
            time.sleep(0.5)
            break
        except Exception:
            pass
    body = ""
    try:
        body = page.inner_text("body")
    except Exception:
        pass
    ref = ""
    rm = re.search(r"Reference:\s*([A-Z0-9_]+)", body)
    if rm:
        ref = rm.group(1).strip()

    desc = ""
    # Prefer the long editorial blurb that follows the Reference line.
    m = re.search(
        r"Reference:\s*[A-Z0-9_]+\s*(?:\n[^\n]{0,80})*\n+([A-Z“\"].{80,}?)(?:\n(?:You may also|Delivery estimated|Express payment)|$)",
        body,
        re.S,
    )
    if m:
        desc = re.sub(r"\s+", " ", m.group(1)).strip()
    if not desc or len(desc) < 40:
        # Fallback: longest prose-looking line on the page
        candidates = []
        for line in body.splitlines():
            s = line.strip()
            if len(s) < 60:
                continue
            if s.startswith(("£", "Go to", "Shop", "New", "Reference")):
                continue
            if s in ("Description", "Size & Fit", "Delivery & Returns", "Contact & In-Store Availability"):
                continue
            if re.search(r"[.!?].{20,}", s):
                candidates.append(s)
        if candidates:
            desc = max(candidates, key=len)

    imgs = page.eval_on_selector_all(
        "img",
        """els => els.map(e => e.currentSrc || e.src || e.getAttribute("data-src") || "")
           .filter(u => u && (u.includes("christiandior.com") || u.includes("dam-broadcast.com")))""",
    )
    seen = set()
    gallery = []
    for u in imgs or []:
        base = u.split("?")[0]
        if base in seen:
            continue
        if "logo" in base.lower():
            continue
        seen.add(base)
        if "christiandior.com/is/image" in base:
            gallery.append(f"{base}?$r2x3_default$&wid=1334&hei=2000&bfc=on&qlt=90")
        else:
            gallery.append(u)
    return {
        "title": title,
        "description": desc,
        "reference": ref,
        "gallery": gallery[:16],
        "sourceUrl": url,
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
    }


def materialize_images(code: str, remote_urls: list[str]) -> list[str]:
    sku_dir = IMG_ROOT / slugify(code.replace("_", "-"))
    local: list[str] = []
    for i, url in enumerate(remote_urls[:12], start=1):
        ext = ".jpg"
        dest = sku_dir / f"{i}{ext}"
        if download_image(url, dest):
            local.append(f"/products/di-pdp/{sku_dir.name}/{i}{ext}")
    return local


def hit_to_row(hit: dict, leaf: dict, pdp: dict | None) -> dict:
    code = (hit.get("code") or "").strip()
    title = (hit.get("title") or hit.get("titleInt") or "").strip()
    subtitle = (hit.get("subtitle") or hit.get("subtitleInt") or "").strip()
    price = hit.get("price") or {}
    gbp = price.get("value") if isinstance(price, dict) else None
    link = (hit.get("productLink") or {}).get("uri") or f"/en_gb/fashion/products/{code}"
    remote_imgs = image_urls_from_hit(hit)
    if pdp and pdp.get("gallery"):
        # prefer merch/PDP gallery order, fall back to PLP
        merged = []
        seen = set()
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
        "collections": [*PARENT_COLS_OBJECTS, leaf["id"]],
        "color": hit.get("color") or {},
        "details": {
            "paragraphs": [desc] if desc else [],
            "bullets": [subtitle] if subtitle else [],
            "specs": [],
        },
        "images": local_imgs,
        "remoteImages": remote_imgs,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", type=str, default="1", help="1 | 2 | 3 | 4 | 5 | all")
    ap.add_argument("--max-pdp", type=int, default=0, help="cap PDP enrich (0=all)")
    ap.add_argument("--skip-pdp", action="store_true")
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()

    leaves = [
        L
        for L in OBJECTS_LEAVES
        if args.stage == "all" or L.get("stage") == str(args.stage)
    ]
    # stage 1 should not include "all" leaf
    if args.stage == "1":
        leaves = [L for L in leaves if L["id"] in ("di-books", "di-notebooks")]
    elif args.stage == "2":
        leaves = [
            L
            for L in leaves
            if L["id"] in ("di-desk-accessories", "di-leisure")
        ]
    elif args.stage == "3":
        leaves = [L for L in leaves if L["id"] == "di-candleholders-candles"]
    elif args.stage == "4":
        leaves = [
            L for L in leaves if L["id"] in ("di-small-objects", "di-trinket-trays")
        ]
    elif args.stage == "5":
        leaves = [
            L
            for L in leaves
            if L["id"] in ("di-trays", "di-objects-all", "di-paperweights")
        ]

    save_json(OUT_LEAVES, OBJECTS_LEAVES)
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
        # warm session on first leaf hub
        page.goto(
            f"{BASE}/{LANG}/fashion/maison/objects/all-products",
            wait_until="domcontentloaded",
            timeout=120000,
        )
        accept_cookies(page)
        time.sleep(2)

        for leaf in leaves:
            hits = scrape_plp_hits(page, leaf)
            codes = [(h.get("code") or "").strip() for h in hits]
            codes = [c for c in codes if c]
            # Prefer Algolia merch (survives Akamai PDP blocks) for copy + DAM gallery.
            merch: dict[str, dict] = {}
            if not args.skip_pdp:
                try:
                    merch = algolia_merch_hits_by_codes(codes)
                    log(f"  algolia merch {len(merch)}/{len(codes)}")
                except Exception as e:
                    log(f"  WARN algolia: {e}")
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
                        }
                        pdp_cache[code] = pdp
                elif not args.skip_pdp and (
                    not pdp or not clean_dior_description(pdp.get("description") or "")
                ):
                    if args.max_pdp and i > args.max_pdp:
                        pass
                    else:
                        try:
                            log(f"  [{i}/{len(hits)}] PDP {code}")
                            pdp = parse_pdp(page, link or f"/{LANG}/fashion/products/{code}")
                            pdp_cache[code] = pdp
                            if i % 10 == 0:
                                save_json(PDP_CACHE, pdp_cache)
                            time.sleep(PDP_PAUSE)
                        except Exception as e:
                            log(f"  WARN PDP {code}: {e}")
                            pdp = pdp_cache.get(code)
                row = hit_to_row(hit, leaf, pdp)
                # merge leaf memberships if product already seen
                prev = by_id.get(code)
                if prev:
                    cols = list(
                        dict.fromkeys(
                            (prev.get("collections") or []) + (row.get("collections") or [])
                        )
                    )
                    row["collections"] = cols
                    if not row.get("images") and prev.get("images"):
                        row["images"] = prev["images"]
                    if not (row.get("details") or {}).get("paragraphs"):
                        row["details"] = prev.get("details") or row["details"]
                by_id[code] = row
            save_json(PDP_CACHE, pdp_cache)
            save_json(
                OUT_RAW,
                {
                    "scrapedAt": datetime.now(timezone.utc).isoformat(),
                    "stage": args.stage,
                    "hub": f"{BASE}/{LANG}/fashion/maison/objects/all-products",
                    "leaves": OBJECTS_LEAVES,
                    "products": list(by_id.values()),
                },
            )
            log(f"saved raw products={len(by_id)}")

        browser.close()

    log(f"DONE stage={args.stage} products={len(by_id)} → {OUT_RAW}")


if __name__ == "__main__":
    main()
