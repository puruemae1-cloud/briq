#!/usr/bin/env python3
"""Refresh Prada RTW sizeChart entries to include Short (…S) size guidance.

Uses pr_size_charts enrichment (official 5 cm shorter length note + Short tab).
Safe to run after scrape/build and from weekly sync.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from pr_size_charts import (  # noqa: E402
    size_chart_for_mens_rtw_variants,
    size_chart_for_variants,
)

CATALOG = ROOT / "src/data/pr/pr-catalog.json"


def _is_mens_rtw(product: dict) -> bool:
    chart_id = str((product.get("sizeChart") or {}).get("id") or "")
    if chart_id.startswith("pr-men"):
        return True
    if chart_id.startswith("pr-women"):
        return False
    sub = str(product.get("subcategory") or "")
    tags = [str(t).lower() for t in (product.get("tags") or [])]
    if "pr-men" in sub or any("men" in t and "women" not in t for t in tags):
        return True
    return False


def patch_product(product: dict) -> bool:
    variants = product.get("variants") or []
    if not variants:
        return False
    old = product.get("sizeChart")
    if not isinstance(old, dict):
        return False
    chart_id = str(old.get("id") or "")
    if chart_id not in {
        "pr-women-rtw-numeric",
        "pr-men-rtw-numeric",
        "pr-men-denim-waist",
    }:
        # Letter-only / shoes charts — no Short (…S) IT columns
        return False

    if _is_mens_rtw(product):
        new = size_chart_for_mens_rtw_variants(variants)
    else:
        new = size_chart_for_variants(variants)
    if not new:
        return False
    if new == old:
        return False
    product["sizeChart"] = new
    return True


def main() -> None:
    products = json.loads(CATALOG.read_text())
    updated = 0
    with_short_tab = 0
    for p in products:
        if not isinstance(p, dict):
            continue
        if patch_product(p):
            updated += 1
        tabs = (p.get("sizeChart") or {}).get("tabs") or []
        if any(t.get("id") == "short" for t in tabs):
            with_short_tab += 1
    CATALOG.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n")
    print(f"updated sizeChart on {updated} products; short tabs={with_short_tab}")


if __name__ == "__main__":
    main()
