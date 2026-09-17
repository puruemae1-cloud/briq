#!/usr/bin/env python3
"""Retag existing YS men RTW raw products with official subcategory leaf collections.

Does not re-fetch PDPs — only PLP membership from each configured leaf.
Also stamps ys-men-rtw-all onto every SKU in the union so Briq '전체' matches 남성용.
"""
from __future__ import annotations

from ysl_common import iter_plp_products, load_json, save_json
from ysl_config import RAW_DIR, YS_MEN, YS_MEN_RTW_LEAVES

OUT = RAW_DIR / "ys-men-rtw-catalog-raw.json"
ALL_ID = "ys-men-rtw-all"


def main() -> int:
    data = load_json(OUT, {"products": []})
    products = data.get("products") or []
    by_id = {str(p.get("id") or ""): p for p in products if p.get("id")}
    print(f"raw products={len(by_id)}", flush=True)

    for leaf in YS_MEN_RTW_LEAVES:
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
                by_id[pid] = {
                    "id": pid,
                    "sku": pid,
                    "name": pid,
                    "collections": list(dict.fromkeys([*cols, ALL_ID])),
                    "leafId": lid,
                    "needsPdp": True,
                }
                continue
            merged_cols = list(
                dict.fromkeys([*(row.get("collections") or []), *cols, lid, ALL_ID, *YS_MEN])
            )
            row["collections"] = merged_cols
            if not row.get("leafId") or row.get("leafId") == ALL_ID:
                if lid != ALL_ID:
                    row["leafId"] = lid
            hit += 1
        print(
            f"  {lid}: plp={len(ids)} tagged={hit} missing_stubs={missing}",
            flush=True,
        )

    out_products = list(by_id.values())
    for p in out_products:
        cols = list(p.get("collections") or [])
        if any(str(c).startswith("ys-men") for c in cols):
            cols = list(dict.fromkeys([*cols, *YS_MEN, ALL_ID]))
        p["collections"] = cols

    save_json(
        OUT,
        {
            **{k: v for k, v in data.items() if k != "products"},
            "products": out_products,
            "family": "ys-men-rtw",
            "leaves": [l["id"] for l in YS_MEN_RTW_LEAVES],
        },
    )
    print(f"saved {OUT} products={len(out_products)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
