#!/usr/bin/env python3
"""Guard Vivienne Westwood accessories/jewellery coverage on Briq.

The shop filter used to ignore `vwCollections`, so only products whose
primary `subcategory` was a hub *-all id appeared on
`/shop?category=accessories&sub=vivienne-westwood-accessories`
(~77 = women jewellery-all + women acc-all + men acc-all). Scraped
jewellery + accessories inventory is much larger (~400 colourways).

Usage:
  python3 scripts/check-vw-accessories-coverage.py
  python3 scripts/check-vw-accessories-coverage.py --fail
  python3 scripts/check-vw-accessories-coverage.py --fail --skip-live
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from vw_common import scrape_plp_cards  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

RAW_FILES = [
    ROOT / "src/data/vw/vw-women-jewellery-catalog-raw.json",
    ROOT / "src/data/vw/vw-women-accessories-catalog-raw.json",
    ROOT / "src/data/vw/vw-men-jewellery-catalog-raw.json",
    ROOT / "src/data/vw/vw-men-accessories-catalog-raw.json",
]
CATALOG = ROOT / "src/data/vw/vw-catalog.json"
OFFICIAL_WOMEN_JEW = "https://www.viviennewestwood.com/en-gb/women/jewellery/"
ACC_COLS = {
    "vivienne-westwood-accessories",
    "vw-accessories",
    "vw-women-accessories",
    "vw-women-acc-all",
    "vw-women-jewellery",
    "vw-women-jewellery-all",
    "vw-men-accessories",
    "vw-men-acc-all",
    "vw-men-jewellery",
    "vw-men-jewellery-all",
}
# Soft floors — hub View All pages are ~28; full leaf scrape is much larger.
MIN_RAW_UNION = 200
MIN_CATALOG_ACC = 200
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


def live_women_jewellery_count() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_context(user_agent=UA, locale="en-GB").new_page()
        try:
            cards = scrape_plp_cards(page, OFFICIAL_WOMEN_JEW)
            return len(cards)
        finally:
            browser.close()


def raw_union_count() -> int:
    seen: set[str] = set()
    for path in RAW_FILES:
        if not path.is_file():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for p in payload.get("products") or []:
            pid = str(p.get("pid") or p.get("id") or "").strip()
            if pid:
                seen.add(pid)
    return len(seen)


def catalog_accessories_count() -> int:
    if not CATALOG.is_file():
        return 0
    products = json.loads(CATALOG.read_text(encoding="utf-8"))
    n = 0
    for p in products:
        cols = set(p.get("vwCollections") or [])
        if not (cols & ACC_COLS):
            continue
        if p.get("category") == "accessories":
            n += 1
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fail", action="store_true")
    ap.add_argument("--skip-live", action="store_true")
    args = ap.parse_args()

    errors: list[str] = []
    raw_n = raw_union_count()
    if raw_n < MIN_RAW_UNION:
        errors.append(
            f"VW accessories/jewellery raw union has {raw_n} products "
            f"(need ≥{MIN_RAW_UNION})"
        )

    live_n = 0
    if not args.skip_live:
        try:
            live_n = live_women_jewellery_count()
        except Exception as e:
            errors.append(f"live VW women jewellery PLP failed: {e}")
    else:
        live_n = 28

    # Hub View All is ~28; raw union must stay well above a single hub page.
    if live_n and raw_n < max(MIN_RAW_UNION, int(live_n * 4)):
        errors.append(
            f"accessories/jewellery raw union={raw_n} too low vs live hub≈{live_n}"
        )

    cat_n = catalog_accessories_count()
    if cat_n < MIN_CATALOG_ACC:
        errors.append(
            f"catalog vivienne-westwood-accessories tagged products is {cat_n} "
            f"(need ≥{MIN_CATALOG_ACC}); check vwCollections tagging / shop filter"
        )

    products_ts = (ROOT / "src/data/products.ts").read_text(encoding="utf-8")
    if "p.vwCollections?.some" not in products_ts:
        errors.append(
            "getProductsByCategory must filter on p.vwCollections "
            "(otherwise accessories/jewellery stay stuck near hub *-all counts)"
        )

    if errors:
        for e in errors:
            print(f"ERROR: {e}", flush=True)
        if args.fail:
            return 1
        return 0

    print(
        f"OK VW accessories coverage — rawUnion={raw_n} liveWomenJew≈{live_n} "
        f"catalogTagged={cat_n}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
