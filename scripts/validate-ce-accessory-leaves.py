#!/usr/bin/env python3
"""Fail weekly CE sync when shop-nav accessory leaves stay empty despite catalog stock.

Validates that critical Celine accessory leaf IDs have products after build-ce-catalog.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "src" / "data" / "ce" / "ce-catalog.json"

# Leaves that must be non-empty when the parent hub has products.
REQUIRED_LEAVES: dict[str, list[str]] = {
    "ce-women-belts": ["ce-women-belts"],
    "ce-women-silk-squares-accessories": [
        "ce-women-silk-squares-accessories",
        "ce-women-silk-scarves",
    ],
    "ce-women-scarves": ["ce-women-scarves"],
    "ce-women-hats": ["ce-women-hats"],
    "ce-women-hair-accessories": ["ce-women-hair-accessories", "ce-women-hair"],
    "ce-women-earrings": ["ce-women-earrings"],
    "ce-women-necklaces": ["ce-women-necklaces"],
    "ce-women-bracelets": ["ce-women-bracelets"],
    "ce-women-rings": ["ce-women-rings"],
    "ce-women-wallets": ["ce-women-wallets"],
    "ce-women-coin-card-holders": [
        "ce-women-coin-card-holders",
        "ce-women-card-holders",
    ],
    "ce-women-pouches-tech-accessories": [
        "ce-women-pouches-tech-accessories",
        "ce-women-pouches",
    ],
    "ce-women-wallets-on-chain": ["ce-women-wallets-on-chain", "ce-women-woc"],
    "ce-men-belts": ["ce-men-belts"],
    "ce-men-silks-scarves": ["ce-men-silks-scarves", "ce-men-scarves"],
    "ce-men-hats-soft-accessories": ["ce-men-hats-soft-accessories", "ce-men-hats"],
}


def _matches(product: dict, ids: list[str]) -> bool:
    sub = product.get("subcategory") or ""
    cols = set(product.get("ceCollections") or [])
    return sub in ids or any(i in cols for i in ids)


def main() -> int:
    if not CATALOG.exists():
        print(f"MISSING {CATALOG}", file=sys.stderr)
        return 1
    products = json.loads(CATALOG.read_text())
    if not isinstance(products, list):
        products = products.get("products") or []

    failures: list[str] = []
    for nav_id, match_ids in REQUIRED_LEAVES.items():
        n = sum(1 for p in products if _matches(p, match_ids))
        status = "OK" if n > 0 else "EMPTY"
        print(f"{status:5} {nav_id}: {n}")
        if n == 0:
            failures.append(nav_id)

    if failures:
        print(
            "CE accessory leaf validation failed (empty): " + ", ".join(failures),
            file=sys.stderr,
        )
        return 1
    print("OK CE accessory leaf validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
