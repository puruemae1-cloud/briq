#!/usr/bin/env python3
"""Guard Vivienne Westwood bags coverage vs official PLP + Briq category tagging.

VW bag style leaves (crossbody/totes/clutches/…) used to be filed as
`category=accessories` because `leaf_to_category` only checked for the
substring `bags`. That hid most colourways from
`/shop?category=bags&sub=vivienne-westwood-bags` (stuck near ~31 while
scraped bag inventory is much larger).

Usage:
  python3 scripts/check-vw-bags-coverage.py
  python3 scripts/check-vw-bags-coverage.py --fail
  python3 scripts/check-vw-bags-coverage.py --fail --skip-live
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

RAW_W = ROOT / "src/data/vw/vw-women-bags-catalog-raw.json"
RAW_M = ROOT / "src/data/vw/vw-men-bags-catalog-raw.json"
CATALOG = ROOT / "src/data/vw/vw-catalog.json"
OFFICIAL_WOMEN = "https://www.viviennewestwood.com/en-gb/women/bags/"
BAG_COLS = {
    "vivienne-westwood-bags",
    "vw-bags",
    "vw-women-bags",
    "vw-women-bags-all",
    "vw-men-bags",
    "vw-men-bags-all",
}
# Soft floors — official View All is ~28; hub must keep subcategory bags too.
MIN_RAW_BAGS_ALL = 24
MIN_CATALOG_BAGS = 50
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


def live_women_bags_count() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_context(user_agent=UA, locale="en-GB").new_page()
        try:
            cards = scrape_plp_cards(page, OFFICIAL_WOMEN)
            return len(cards)
        finally:
            browser.close()


def raw_bags_all_count(path: Path) -> int:
    if not path.is_file():
        return 0
    payload = json.loads(path.read_text(encoding="utf-8"))
    products = payload.get("products") or []
    return sum(
        1
        for p in products
        if str(p.get("leafId") or "").endswith("bags-all")
    )


def catalog_bags_count() -> tuple[int, int]:
    """Return (category=bags count, misfiled accessories count)."""
    if not CATALOG.is_file():
        return 0, 0
    products = json.loads(CATALOG.read_text(encoding="utf-8"))
    bags = 0
    misfiled = 0
    for p in products:
        cols = set(p.get("vwCollections") or [])
        if not (cols & BAG_COLS):
            continue
        if p.get("category") == "bags":
            bags += 1
        else:
            misfiled += 1
    return bags, misfiled


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fail", action="store_true")
    ap.add_argument("--skip-live", action="store_true")
    args = ap.parse_args()

    errors: list[str] = []
    raw_w = raw_bags_all_count(RAW_W)
    raw_m = raw_bags_all_count(RAW_M)
    if raw_w < MIN_RAW_BAGS_ALL:
        errors.append(
            f"vw-women-bags-all raw has {raw_w} products (need ≥{MIN_RAW_BAGS_ALL})"
        )

    live_n = 0
    if not args.skip_live:
        try:
            live_n = live_women_bags_count()
        except Exception as e:
            errors.append(f"live VW women bags PLP failed: {e}")
    else:
        live_n = 28

    if live_n and raw_w < int(live_n * 0.85):
        errors.append(
            f"women bags-all raw={raw_w} below 85% of live PLP≈{live_n}"
        )

    bags_n, misfiled = catalog_bags_count()
    if bags_n < MIN_CATALOG_BAGS:
        errors.append(
            f"catalog vivienne-westwood-bags with category=bags is {bags_n} "
            f"(need ≥{MIN_CATALOG_BAGS}); check leaf_to_category"
        )
    if misfiled:
        errors.append(
            f"{misfiled} bag-collection products still filed as non-bags "
            "(crossbody/totes/clutches must be category=bags)"
        )

    products_ts = (ROOT / "src/data/products.ts").read_text(encoding="utf-8")
    if "p.vwCollections?.some" not in products_ts:
        errors.append(
            "getProductsByCategory must filter on p.vwCollections "
            "(otherwise bag style leaves stay hidden on vivienne-westwood-bags)"
        )

    if errors:
        for e in errors:
            print(f"ERROR: {e}", flush=True)
        if args.fail:
            return 1
        return 0

    print(
        f"OK VW bags coverage — rawWomenAll={raw_w} rawMenAll={raw_m} "
        f"liveWomen≈{live_n} catalogBags={bags_n}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
