#!/usr/bin/env python3
"""Scrape Celine GB men's ready-to-wear into raw catalog JSON.

Example:
  python3 scripts/scrape-celine-men-rtw.py --limit 3
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from celine_common import load_json, save_json, scrape_leaf_rows
from celine_config import CE_MEN_RTW_LEAVES, merge_product_rows

ROOT = Path(__file__).resolve().parents[1]
OUT_RAW = ROOT / "src/data/ce/ce-men-rtw-catalog-raw.json"
LEAVES = CE_MEN_RTW_LEAVES


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--leaf", default="all", help="leaf id or all")
    ap.add_argument("--limit", type=int, default=0, help="limit PDPs per leaf")
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()

    leaves = LEAVES if args.leaf == "all" else [x for x in LEAVES if x["id"] == args.leaf]
    if not leaves:
        raise SystemExit(f"unknown leaf: {args.leaf}")

    existing = load_json(OUT_RAW, {"products": []})
    products = existing.get("products") or []

    for leaf in leaves:
        rows = scrape_leaf_rows(leaf, headed=args.headed, limit=args.limit)
        products = merge_product_rows(products, rows)

        save_json(
            OUT_RAW,
            {
                "scrapedAt": datetime.now(timezone.utc).isoformat(),
                "brand": "Celine",
                "hub": "https://www.celine.com/en-gb/men/ready-to-wear/?nav=E001-VIEW-ALL",
                "leaves": LEAVES,
                "products": products,
            },
        )
        print(f"saved {leaf['id']} rows={len(rows)} total={len(products)}", flush=True)


if __name__ == "__main__":
    main()
