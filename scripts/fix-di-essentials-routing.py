#!/usr/bin/env python3
"""Apply Essentials hub routing onto di-catalog (shoes / RTW / accessories).

Re-reads di-men-essentials-catalog-raw.json and forces each SKU's category /
collections to the classified bucket so mixed RTW+accessories pollution and
bags-leaf prefer_leaf wins cannot leave Essentials items in the wrong shop tree.

  python3 scripts/fix-di-essentials-routing.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from di_common import normalize_di_product_prices  # noqa: E402
from di_size_charts import (  # noqa: E402
    size_chart_for_di_mens_rtw,
    size_chart_for_di_mens_shoes,
)

CAT = ROOT / "src/data/di/di-catalog.json"
RAW = ROOT / "src/data/di/di-men-essentials-catalog-raw.json"


def _load_merge():
    path = ROOT / "scripts" / "merge-di-catalog-ko.py"
    spec = importlib.util.spec_from_file_location("merge_di_catalog_ko", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    merge = _load_merge()
    raw = json.loads(RAW.read_text())
    by_raw = {p["id"]: p for p in (raw.get("products") or []) if p.get("id")}
    products = json.loads(CAT.read_text())
    by_sku = {p.get("sku"): p for p in products if p.get("sku")}

    fixed = 0
    buckets: Counter[str] = Counter()
    missing = 0
    for code, row in by_raw.items():
        p = by_sku.get(code)
        if not p:
            missing += 1
            continue
        leaf = str(row.get("leafId") or "")
        cols = list(dict.fromkeys(row.get("collections") or []))
        if "di-men-essentials" not in cols:
            cols.append("di-men-essentials")
        bucket = str(row.get("essentialsBucket") or "")
        # Ensure collections only reflect the routed bucket (drop pollution).
        p["diCollections"] = cols
        p["subcategory"] = leaf
        p["category"] = merge._category_for(cols, leaf, "accessories")
        p["tags"] = merge.tags_for(cols, leaf)
        if any(c in merge.RTWISH for c in cols + [leaf]):
            chart = size_chart_for_di_mens_rtw(
                p.get("variants") or [],
                leaf_id=leaf,
                title_en=str(p.get("name") or ""),
            )
            if chart:
                p["sizeChart"] = chart
            elif "sizeChart" in p and not any(c in merge.MEN_SHOESISH for c in cols + [leaf]):
                # leave existing chart if any
                pass
        elif any(c in merge.MEN_SHOESISH for c in cols + [leaf]):
            p["sizeChart"] = size_chart_for_di_mens_shoes()
        elif "sizeChart" in p and not any(
            c in merge.RTWISH or c in merge.MEN_SHOESISH for c in cols + [leaf]
        ):
            # Accessories shouldn't keep RTW/shoe charts
            p.pop("sizeChart", None)

        normalize_di_product_prices(p, float(row["gbpPrice"]) if row.get("gbpPrice") is not None else None)
        fixed += 1
        buckets[bucket or "?"] += 1

    CAT.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n")
    print(
        f"DONE fixed={fixed} missing_in_catalog={missing} buckets={dict(buckets)}",
        flush=True,
    )

    # Sanity: Cap should be accessories
    cap = by_sku.get("693C906C3777_C988")
    if cap:
        print(
            f"CAP category={cap.get('category')} sub={cap.get('subcategory')} cols={cap.get('diCollections')}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
