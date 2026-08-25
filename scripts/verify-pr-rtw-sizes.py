#!/usr/bin/env python3
"""Fail if Prada RTW raw/catalog mixes letter (S/M/L) and numeric size options.

  python3 scripts/verify-pr-rtw-sizes.py
  python3 scripts/verify-pr-rtw-sizes.py --raw-only
  python3 scripts/verify-pr-rtw-sizes.py --catalog-only
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from pr_sizes import MixedRtwSizesError, assert_no_mixed_rtw_sizes  # noqa: E402

RAW_MEN = ROOT / "src/data/pr/pr-mens-rtw-catalog-raw.json"
RAW_WOMEN = ROOT / "src/data/pr/pr-womens-rtw-catalog-raw.json"
CATALOG = ROOT / "src/data/pr/pr-catalog.json"

RTW_PREFIXES = ("pr-men-", "pr-women-")


def _load_products(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"Missing {path}")
    payload = json.loads(path.read_text())
    if isinstance(payload, list):
        return payload
    return payload.get("products") or []


def _catalog_rtw(products: list[dict]) -> list[dict]:
    out: list[dict] = []
    for p in products:
        if p.get("brand") != "프라다" or p.get("category") != "luxury":
            continue
        cols = p.get("prCollections") or []
        if any(str(c).startswith(RTW_PREFIXES) for c in cols):
            out.append(p)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-only", action="store_true")
    ap.add_argument("--catalog-only", action="store_true")
    args = ap.parse_args()
    check_raw = not args.catalog_only
    check_cat = not args.raw_only

    try:
        if check_raw:
            for path, label in (
                (RAW_MEN, "men's RTW raw"),
                (RAW_WOMEN, "women's RTW raw"),
            ):
                products = _load_products(path)
                assert_no_mixed_rtw_sizes(products, context=label)
                print(f"OK {label}: {len(products)} products", flush=True)
        if check_cat:
            products = _catalog_rtw(_load_products(CATALOG))
            assert_no_mixed_rtw_sizes(products, context="Prada RTW catalog")
            print(f"OK Prada RTW catalog: {len(products)} products", flush=True)
    except MixedRtwSizesError as e:
        raise SystemExit(str(e)) from e


if __name__ == "__main__":
    main()
