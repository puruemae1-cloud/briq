#!/usr/bin/env python3
"""Guard Mulberry women-bags PLP coverage vs official Algolia catalogue size.

Mulberry GB PLPs are Algolia-paginated (72/page). A DOM-only scrape silently
caps at 72 and the Briq shop then under-lists colourways. This check fails the
weekly sync when:
  1. mb-women-bags-all raw PLP has < 90% of live Algolia nbHits, or
  2. Built catalog colourway cards for mb-women-bags would stay under 300.

Usage:
  python3 scripts/check-mb-plp-coverage.py
  python3 scripts/check-mb-plp-coverage.py --fail
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from mulberry_common import scrape_plp  # noqa: E402

RAW = ROOT / "src" / "data" / "mb" / "mb-women-bags-all-catalog-raw.json"
CATALOG = ROOT / "src" / "data" / "mb" / "mb-catalog.json"
OFFICIAL_URL = "https://www.mulberry.com/gb/shop/women/bags"
# Soft floor — official women bags is ~348 colourways; stay within 90%.
MIN_RAW_RATIO = 0.9
MIN_CATALOG_COLOURWAYS = 300
WOMEN_BAG_COLS = {
    "mb-women-bags",
    "mb-women-bags-all",
    "mb-women-crossbody",
    "mb-women-shoulder",
    "mb-women-top-handle",
    "mb-women-totes",
    "mb-women-bucket",
    "mb-women-mini",
    "mb-women-clutches",
    "mb-women-backpacks",
    "mb-women-icons",
}


def count_catalog_colourways() -> int:
    if not CATALOG.is_file():
        return 0
    products = json.loads(CATALOG.read_text(encoding="utf-8"))
    cards = 0
    for p in products:
        cols = set(p.get("mbCollections") or [])
        if not (cols & WOMEN_BAG_COLS):
            continue
        if p.get("category") and p.get("category") != "bags":
            continue
        variants = p.get("variants") or []
        if not variants:
            cards += 1
            continue
        keys: set[str] = set()
        for v in variants:
            vcols = set(v.get("mbCollections") or cols)
            if not (vcols & WOMEN_BAG_COLS):
                continue
            key = v.get("colorKey") or v.get("sourceUrl")
            if key:
                keys.add(str(key))
        cards += len(keys) or 1
    return cards


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fail", action="store_true")
    ap.add_argument("--skip-live", action="store_true", help="Skip live Algolia fetch")
    args = ap.parse_args()

    errors: list[str] = []

    raw_n = 0
    if RAW.is_file():
        raw = json.loads(RAW.read_text(encoding="utf-8"))
        raw_n = len(raw.get("products") or [])
    else:
        errors.append(f"missing raw file {RAW.relative_to(ROOT)}")

    live_n = 0
    if not args.skip_live:
        try:
            cards = scrape_plp(OFFICIAL_URL)
            live_n = len(cards)
        except Exception as e:
            errors.append(f"live Algolia PLP failed: {e}")
    else:
        live_n = 348  # documented official floor when offline

    if live_n and raw_n < int(live_n * MIN_RAW_RATIO):
        errors.append(
            f"mb-women-bags-all raw has {raw_n} products; "
            f"official Algolia women bags ≈ {live_n} (need ≥{int(live_n * MIN_RAW_RATIO)})"
        )

    cat_n = count_catalog_colourways()
    if cat_n and cat_n < MIN_CATALOG_COLOURWAYS:
        errors.append(
            f"catalog women-bag colourways={cat_n} (need ≥{MIN_CATALOG_COLOURWAYS}); "
            "ensure expandMbColourwayCards + full Algolia scrape"
        )
    elif not cat_n and CATALOG.is_file():
        errors.append("catalog has 0 women-bag colourways")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", flush=True)
        if args.fail:
            return 1
        return 0

    print(
        f"OK MB PLP coverage — raw={raw_n} live≈{live_n} catalogColourways={cat_n}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
