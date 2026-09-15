#!/usr/bin/env python3
"""Scrape Saint Laurent GB family catalogs.

Examples:
  python3 scripts/scrape-ys-family.py --family ys-men-bags --limit 3
  python3 scripts/scrape-ys-family.py --family ys-men-slg --leaf ys-men-wallets
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from ysl_common import load_json, save_json, scrape_leaf_rows
from ysl_config import RAW_DIR, YS_FAMILY_SCRAPERS, merge_product_rows

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", required=True, choices=sorted(YS_FAMILY_SCRAPERS))
    ap.add_argument("--leaf", default="all")
    ap.add_argument("--limit", type=int, default=0, help="max new PDPs this run")
    ap.add_argument("--skip-pdp", action="store_true")
    args = ap.parse_args()

    cfg = YS_FAMILY_SCRAPERS[args.family]
    leaves = cfg["leaves"] if args.leaf == "all" else [x for x in cfg["leaves"] if x["id"] == args.leaf]
    if not leaves:
        raise SystemExit(f"unknown leaf: {args.leaf}")

    out_raw = RAW_DIR / cfg["out"]
    existing = load_json(out_raw, {"products": []})
    products = existing.get("products") or []
    skip_ids = {
        str(p.get("id") or "")
        for p in products
        if p.get("id") and p.get("localImages") and not p.get("pdpError")
    }

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for leaf in leaves:
        print(f"== {args.family} / {leaf['id']} ==", flush=True)
        rows = scrape_leaf_rows(
            leaf,
            limit=args.limit,
            skip_ids=skip_ids,
            pdp=not args.skip_pdp,
        )
        products = merge_product_rows(products, rows)
        skip_ids |= {str(r.get("id") or "") for r in rows}
        save_json(
            out_raw,
            {
                "scrapedAt": datetime.now(timezone.utc).isoformat(),
                "brand": "Saint Laurent",
                "hub": cfg["hub"],
                "category": cfg["category"],
                "family": args.family,
                "leaves": cfg["leaves"],
                "products": products,
            },
        )
        print(f"saved {leaf['id']} rows={len(rows)} total={len(products)}", flush=True)
        if args.limit and len(rows) >= args.limit:
            # limit is per-run convenience — stop after first leaf hit limit
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
