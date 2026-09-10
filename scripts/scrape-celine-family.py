#!/usr/bin/env python3
"""Generic Celine GB family scraper (men/women RTW, bags, …).

Example:
  python3 scripts/scrape-celine-family.py --family ce-women-rtw --limit 2
  python3 scripts/scrape-celine-family.py --family ce-women-bags --leaf ce-women-bags-all --limit 3
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from celine_common import load_json, save_json, scrape_leaf_rows
from celine_config import CE_FAMILY_SCRAPERS, RAW_DIR, merge_product_rows

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", required=True, choices=sorted(CE_FAMILY_SCRAPERS))
    ap.add_argument("--leaf", default="all", help="leaf id or all")
    ap.add_argument("--limit", type=int, default=0, help="limit PDPs per leaf")
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()

    cfg = CE_FAMILY_SCRAPERS[args.family]
    leaves = cfg["leaves"] if args.leaf == "all" else [x for x in cfg["leaves"] if x["id"] == args.leaf]
    if not leaves:
        raise SystemExit(f"unknown leaf: {args.leaf}")

    from celine_common import is_blocked_pdp_title

    out_raw = RAW_DIR / cfg["out"]
    existing = load_json(out_raw, {"products": []})
    products = existing.get("products") or []

    # Skip healthy IDs, but ALWAYS retry Access Denied / blocked poison rows.
    skip_ids = {
        str(p.get("id") or p.get("sku") or "")
        for p in products
        if str(p.get("id") or p.get("sku") or "")
        and not is_blocked_pdp_title(p.get("title"))
        and not p.get("scrapeBlocked")
    }
    for leaf in leaves:
        rows = scrape_leaf_rows(leaf, headed=args.headed, limit=args.limit, skip_ids=skip_ids)
        products = merge_product_rows(products, rows)
        skip_ids |= {str(r.get("id") or r.get("sku") or "") for r in rows}
        save_json(
            out_raw,
            {
                "scrapedAt": datetime.now(timezone.utc).isoformat(),
                "brand": "Celine",
                "hub": cfg["hub"],
                "family": args.family,
                "leaves": cfg["leaves"],
                "products": products,
            },
        )
        print(f"saved {leaf['id']} rows={len(rows)} total={len(products)}", flush=True)


if __name__ == "__main__":
    main()
