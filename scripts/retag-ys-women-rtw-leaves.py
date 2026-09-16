#!/usr/bin/env python3
"""Retag existing YS women RTW raw products with official subcategory leaf collections.

Does not re-fetch PDPs — only PLP membership from each configured leaf.
"""
from __future__ import annotations

from pathlib import Path

from ysl_common import iter_plp_products, load_json, save_json
from ysl_config import RAW_DIR, YS_WOMEN_RTW_LEAVES

OUT = RAW_DIR / "ys-women-rtw-catalog-raw.json"


def main() -> int:
    data = load_json(OUT, {"products": []})
    products = data.get("products") or []
    by_id = {str(p.get("id") or ""): p for p in products if p.get("id")}
    print(f"raw products={len(by_id)}", flush=True)

    for leaf in YS_WOMEN_RTW_LEAVES:
        lid = leaf["id"]
        cols = list(leaf.get("collections") or [])
        rows = iter_plp_products(leaf["slug"], require_full=True)
        ids = {str(p.get("id") or "") for p in rows if p.get("id")}
        hit = 0
        missing = 0
        for pid in ids:
            row = by_id.get(pid)
            if not row:
                missing += 1
                # Minimal stub so leaf filter still works after rebuild once PDP scraped.
                by_id[pid] = {
                    "id": pid,
                    "sku": pid,
                    "name": pid,
                    "collections": list(cols),
                    "leafId": lid,
                    "needsPdp": True,
                }
                continue
            merged_cols = list(
                dict.fromkeys([*(row.get("collections") or []), *cols, lid])
            )
            row["collections"] = merged_cols
            # Keep a leafId for size-chart hint when product is exclusive to this leaf.
            if not row.get("leafId") or row.get("leafId") == "ys-women-rtw-all":
                if lid != "ys-women-rtw-all":
                    row["leafId"] = lid
            hit += 1
        print(
            f"  {lid}: plp={len(ids)} tagged={hit} missing_stubs={missing}",
            flush=True,
        )

    out_products = list(by_id.values())
    # Ensure every product still has ys-women-rtw-all if it was in view-all scrape
    for p in out_products:
        cols = list(p.get("collections") or [])
        if "ys-women" in cols and "ys-women-rtw-all" not in cols:
            # Only add all if it was previously catalogued under women RTW hub
            if any(c.startswith("ys-women") for c in cols):
                pass
        p["collections"] = list(dict.fromkeys(cols))

    save_json(
        OUT,
        {
            **{k: v for k, v in data.items() if k != "products"},
            "products": out_products,
            "family": "ys-women-rtw",
            "leaves": [l["id"] for l in YS_WOMEN_RTW_LEAVES],
        },
    )
    print(f"saved {OUT} products={len(out_products)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
