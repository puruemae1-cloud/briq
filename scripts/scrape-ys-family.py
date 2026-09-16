#!/usr/bin/env python3
"""Scrape Saint Laurent GB family catalogs.

Inventory = union of View All + every subcategory PLP (unique SKUs).
Official target count = unique product IDs across all configured leaves.

Examples:
  python3 scripts/scrape-ys-family.py --family ys-men-bags --limit 3
  python3 scripts/scrape-ys-family.py --family ys-men-slg --leaf ys-men-wallets
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from ysl_common import fetch_plp_page, iter_plp_products, load_json, save_json, scrape_leaf_rows
from ysl_config import RAW_DIR, YS_FAMILY_SCRAPERS, merge_product_rows

ROOT = Path(__file__).resolve().parents[1]


def _is_view_all(leaf: dict) -> bool:
    lid = str(leaf.get("id") or "")
    slug = str(leaf.get("slug") or "")
    return lid.endswith("-all") or "/all-" in f"/{slug}"


def official_union_ids(leaves: list[dict]) -> set[str]:
    """Unique SKUs across every leaf PLP (View All + subcats)."""
    ids: set[str] = set()
    for leaf in leaves:
        rows = iter_plp_products(leaf["slug"], require_full=True)
        ids |= {str(p.get("id") or "") for p in rows if p.get("id")}
        print(
            f"  union+ {leaf['id']}: leaf={len(rows)} running_union={len(ids)}",
            flush=True,
        )
    return ids


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

    # View All first, then subcats — subcats may add SKUs missing from View All.
    ordered = sorted(leaves, key=lambda l: (0 if _is_view_all(l) else 1, l["id"]))

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    view_all_nb = None
    for leaf in ordered:
        print(f"== {args.family} / {leaf['id']} ==", flush=True)
        rows = scrape_leaf_rows(
            leaf,
            limit=args.limit,
            skip_ids=skip_ids,
            pdp=not args.skip_pdp,
        )
        products = merge_product_rows(products, rows)
        skip_ids |= {str(r.get("id") or "") for r in rows}
        stats = fetch_plp_page(leaf["slug"])["results"]["stats"]
        leaf_nb = int(stats.get("nbAlgoliaHits") or 0)
        if _is_view_all(leaf):
            view_all_nb = leaf_nb
        print(
            f"saved {leaf['id']} new={len(rows)} total={len(products)} leaf_official={leaf_nb}",
            flush=True,
        )
        if args.limit and len(rows) >= args.limit:
            break

    official_nb = None
    if args.leaf == "all" and not args.limit:
        print(f"== {args.family} / union official count ==", flush=True)
        auth_ids = official_union_ids(leaves)
        official_nb = len(auth_ids)
        # Keep only SKUs that still appear on at least one official leaf PLP.
        before = len(products)
        products = [p for p in products if str(p.get("id") or "") in auth_ids]
        dropped = before - len(products)
        if dropped:
            print(f"  dropped {dropped} stale SKUs not on any leaf PLP", flush=True)
        missing = auth_ids - {str(p.get("id") or "") for p in products}
        if missing:
            print(f"  WARN missing {len(missing)} official SKUs after scrape", flush=True)

    save_json(
        out_raw,
        {
            "scrapedAt": datetime.now(timezone.utc).isoformat(),
            "brand": "Saint Laurent",
            "hub": cfg["hub"],
            "category": cfg["category"],
            "family": args.family,
            "officialNbAlgoliaHits": view_all_nb,
            "officialUnionCount": official_nb,
            "leaves": cfg["leaves"],
            "products": products,
        },
    )
    print(
        f"OK {args.family} products={len(products)} "
        f"view_all={view_all_nb} union={official_nb}",
        flush=True,
    )
    if (
        official_nb is not None
        and args.leaf == "all"
        and not args.limit
        and len(products) != official_nb
    ):
        raise SystemExit(
            f"coverage mismatch {args.family}: raw={len(products)} union={official_nb}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
