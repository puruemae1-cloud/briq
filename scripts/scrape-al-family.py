#!/usr/bin/env python3
"""Scrape AllSaints GB family catalogs (union of View All + subcategory PLPs)."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from al_common import fetch_plp_pids, load_json, save_json, scrape_leaf_rows
from al_config import RAW_DIR, AL_FAMILY_SCRAPERS, merge_product_rows


def _is_view_all(leaf: dict) -> bool:
    lid = str(leaf.get("id") or "")
    return lid.endswith("-all")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", required=True, choices=sorted(AL_FAMILY_SCRAPERS))
    ap.add_argument("--leaf", default="all")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--skip-pdp", action="store_true")
    args = ap.parse_args()

    cfg = AL_FAMILY_SCRAPERS[args.family]
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

    ordered = sorted(leaves, key=lambda l: (0 if _is_view_all(l) else 1, l["id"]))
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    for leaf in ordered:
        print(f"== {args.family} / {leaf['id']} ==", flush=True)
        rows = scrape_leaf_rows(
            leaf,
            limit=args.limit,
            skip_ids=skip_ids,
            pdp=not args.skip_pdp,
        )
        products = merge_product_rows(products, rows)
        skip_ids |= {str(r.get("id") or "") for r in rows if r.get("localImages")}
        leaf_n = len(fetch_plp_pids(leaf["cgid"]))
        print(
            f"saved {leaf['id']} new={len(rows)} total={len(products)} leaf_official={leaf_n}",
            flush=True,
        )
        save_json(
            out_raw,
            {
                "family": args.family,
                "category": cfg["category"],
                "hub": cfg["hub"],
                "scrapedAt": datetime.now(timezone.utc).isoformat(),
                "leaves": [l["id"] for l in cfg["leaves"]],
                "products": products,
            },
        )

    # Union coverage check
    print(f"== {args.family} / union official count ==", flush=True)
    union: set[str] = set()
    for leaf in cfg["leaves"]:
        ids = set(fetch_plp_pids(leaf["cgid"]))
        union |= ids
        print(f"  union+ {leaf['id']}: leaf={len(ids)} running_union={len(union)}", flush=True)

    # Drop stale SKUs not on any leaf
    before = len(products)
    products = [p for p in products if str(p.get("id") or "") in union]
    dropped = before - len(products)
    if dropped:
        print(f"  dropped {dropped} stale SKUs not on any leaf PLP", flush=True)

    save_json(
        out_raw,
        {
            "family": args.family,
            "category": cfg["category"],
            "hub": cfg["hub"],
            "scrapedAt": datetime.now(timezone.utc).isoformat(),
            "leaves": [l["id"] for l in cfg["leaves"]],
            "officialUnion": len(union),
            "products": products,
        },
    )
    view_all = next((l for l in cfg["leaves"] if _is_view_all(l)), None)
    view_n = len(fetch_plp_pids(view_all["cgid"])) if view_all else 0
    print(
        f"OK {args.family} products={len(products)} view_all={view_n} union={len(union)}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
