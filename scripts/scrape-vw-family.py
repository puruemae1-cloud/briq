#!/usr/bin/env python3
"""Generic Vivienne Westwood GB family scraper.

Example:
  python3 scripts/scrape-vw-family.py --family vw-women-bags --limit 2
  python3 scripts/scrape-vw-family.py --family vw-women-bags --leaf vw-women-bags-all --limit 3
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from vw_common import load_json, save_json, scrape_leaf_rows
from vw_config import RAW_DIR, VW_FAMILY_SCRAPERS, merge_product_rows

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", required=True, choices=sorted(VW_FAMILY_SCRAPERS))
    ap.add_argument("--leaf", default="all", help="leaf id or all")
    ap.add_argument("--limit", type=int, default=0, help="limit PDPs per leaf")
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()

    cfg = VW_FAMILY_SCRAPERS[args.family]
    leaves = cfg["leaves"] if args.leaf == "all" else [x for x in cfg["leaves"] if x["id"] == args.leaf]
    if not leaves:
        raise SystemExit(f"unknown leaf: {args.leaf}")

    out_raw = RAW_DIR / cfg["out"]
    existing = load_json(out_raw, {"products": []})
    products = existing.get("products") or []

    skip_ids = {str(p.get("id") or p.get("sku") or "") for p in products}
    for leaf in leaves:
        rows = scrape_leaf_rows(leaf, headed=args.headed, limit=args.limit, skip_ids=skip_ids)
        products = merge_product_rows(products, rows)
        skip_ids |= {str(r.get("id") or r.get("sku") or "") for r in rows}
        save_json(
            out_raw,
            {
                "scrapedAt": datetime.now(timezone.utc).isoformat(),
                "brand": "Vivienne Westwood",
                "hub": cfg["hub"],
                "family": args.family,
                "leaves": cfg["leaves"],
                "products": products,
            },
        )
        print(f"saved {leaf['id']} rows={len(rows)} total={len(products)}", flush=True)


if __name__ == "__main__":
    main()
