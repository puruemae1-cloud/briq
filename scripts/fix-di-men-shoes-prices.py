#!/usr/bin/env python3
"""Fix Dior men's shoes pricing — Gucci formula from scraped GBP, not KRW Algolia amounts.

  python3 scripts/fix-di-men-shoes-prices.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from di_common import gbp_to_krw  # noqa: E402

CAT = ROOT / "src/data/di/di-catalog.json"
RAW = ROOT / "src/data/di/di-men-shoes-catalog-raw.json"

SHOE_COLS = {
    "dior-shoes",
    "di-men-shoes",
    "di-men-shoes-all",
    "di-men-sneakers",
    "di-men-sandals-mules",
    "di-men-loafers",
    "di-men-lace-ups",
    "di-men-boots",
}


def is_shoe(p: dict) -> bool:
    cols = set(p.get("diCollections") or [])
    sub = str(p.get("subcategory") or "")
    return bool(cols.intersection(SHOE_COLS) or sub in SHOE_COLS)


def main() -> None:
    products = json.loads(CAT.read_text())
    raw_by = {}
    if RAW.is_file():
        raw_by = {
            p["id"]: float(p["gbpPrice"])
            for p in json.loads(RAW.read_text()).get("products") or []
            if p.get("id") and p.get("gbpPrice") is not None
        }

    fixed = 0
    for p in products:
        if not is_shoe(p):
            continue
        sku = str(p.get("sku") or p.get("id") or "").replace("di-", "")
        gbp = float(p.get("gbpPrice") or 0)
        if sku in raw_by and raw_by[sku] > 0:
            gbp = raw_by[sku]
        elif gbp >= 5000:
            # Was polluted with KRW stored as GBP — recover from raw or skip.
            gbp = raw_by.get(sku) or 0
        if gbp <= 0 or gbp >= 5000:
            continue
        krw = gbp_to_krw(gbp)
        p["gbpPrice"] = gbp
        p["price"] = krw
        for v in p.get("variants") or []:
            v["gbpPrice"] = gbp
            v["price"] = krw
        fixed += 1

    CAT.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n")
    print(f"DONE fixed={fixed} shoes", flush=True)


if __name__ == "__main__":
    main()
