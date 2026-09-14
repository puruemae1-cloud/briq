#!/usr/bin/env python3
"""Audit Briq shop / category hrefs and guard against uncapped PLP regressions.

Checks:
  1. Every /shop href in categories.ts, home-banners.ts, site.ts parses cleanly
     (category ∈ known set; sub, if any, exists as a nav node id).
  2. Top-level category + homepage CTA hrefs are present.
  3. Shop page still paginates via getShopProductList + sliceShopPage + API
     (prevents weekly sync / refactors from shipping full catalogues to the client).

Usage:
  python3 scripts/check-nav-shop-links.py
  python3 scripts/check-nav-shop-links.py --fail
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
KNOWN_CATEGORIES = {
    "luxury",
    "watches",
    "bags",
    "shoes",
    "accessories",
    "sports",
}

HREF_RE = re.compile(r'href:\s*"(/shop[^"]*)"')
SHOP_HREF_RE = re.compile(r'shopHref:\s*"(/shop[^"]*)"')
ID_RE = re.compile(r'\bid:\s*"([a-z0-9-]+)"')


def extract_nav_ids(text: str) -> set[str]:
    return set(ID_RE.findall(text))


def parse_shop_href(href: str) -> tuple[str | None, str | None, str]:
    parsed = urlparse(href)
    if parsed.path != "/shop":
        return None, None, f"path is {parsed.path!r}, expected /shop"
    qs = parse_qs(parsed.query)
    category = (qs.get("category") or [None])[0]
    sub = (qs.get("sub") or [None])[0]
    if category is not None and category not in KNOWN_CATEGORIES:
        return category, sub, f"unknown category {category!r}"
    return category, sub, ""


def collect_hrefs() -> list[tuple[str, str]]:
    files = [
        ROOT / "src/data/categories.ts",
        ROOT / "src/data/home-banners.ts",
        ROOT / "src/lib/site.ts",
        ROOT / "src/components/SiteHeader.tsx",
        ROOT / "src/app/page.tsx",
    ]
    out: list[tuple[str, str]] = []
    for path in files:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for m in HREF_RE.finditer(text):
            out.append((str(path.relative_to(ROOT)), m.group(1)))
        for m in SHOP_HREF_RE.finditer(text):
            out.append((str(path.relative_to(ROOT)), m.group(1)))
        # Template literals / buildShopHref string fragments are skipped —
        # those are constructed at runtime from nav ids.
    return out


def check_pagination_guard() -> list[str]:
    errors: list[str] = []
    shop_page = (ROOT / "src/app/shop/page.tsx").read_text(encoding="utf-8")
    grid = (ROOT / "src/components/ShopProductGrid.tsx").read_text(encoding="utf-8")
    api = ROOT / "src/app/api/products/shop/route.ts"

    for needle in ("getShopProductList", "sliceShopPage", "toCardProduct", "SHOP_PAGE_SIZE"):
        if needle not in shop_page:
            errors.append(f"shop/page.tsx missing pagination piece: {needle}")
    if "products={list}" in shop_page or "products={ list }" in shop_page:
        errors.append(
            "shop/page.tsx appears to pass the full product list to a client grid"
        )
    if "/api/products/shop" not in grid:
        errors.append("ShopProductGrid must fetch more pages from /api/products/shop")
    if not api.is_file():
        errors.append("missing src/app/api/products/shop/route.ts")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fail", action="store_true", help="exit 1 on any error")
    args = ap.parse_args()

    categories_text = (ROOT / "src/data/categories.ts").read_text(encoding="utf-8")
    nav_ids = extract_nav_ids(categories_text)
    # Top-level category ids are also valid "sub" absences; brand hubs must be in nav.
    nav_ids |= KNOWN_CATEGORIES

    errors: list[str] = []
    warnings: list[str] = []
    hrefs = collect_hrefs()
    seen: set[str] = set()

    for source, href in hrefs:
        if href in seen:
            continue
        seen.add(href)
        category, sub, err = parse_shop_href(href)
        if err:
            errors.append(f"{source}: {href} — {err}")
            continue
        if sub and sub not in nav_ids:
            errors.append(
                f"{source}: {href} — sub={sub!r} not found as a nav id in categories.ts"
            )

    # Required surfaces
    required = [
        "/shop?category=luxury",
        "/shop?category=luxury&sort=new",
        "/shop?category=watches",
        "/shop?category=bags",
        "/shop?category=shoes",
        "/shop?category=accessories",
        "/shop?category=sports",
        "/shop?sort=new",
    ]
    flat = {h for _, h in hrefs}
    for need in required:
        # allow either exact or with extra params already covered by luxury&sort=new
        if need not in flat and not any(h.startswith(need) for h in flat):
            # soft: luxury without sort is ok if luxury&sort=new exists
            if need == "/shop?category=luxury" and any(
                h.startswith("/shop?category=luxury") for h in flat
            ):
                continue
            warnings.append(f"missing expected shop surface href: {need}")

    errors.extend(check_pagination_guard())

    print(f"checked {len(seen)} unique /shop hrefs from source files")
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")

    if errors:
        print(f"FAIL — {len(errors)} error(s)")
        return 1 if args.fail else 0
    print("OK — nav shop links + PLP pagination guard")
    return 0


if __name__ == "__main__":
    sys.exit(main())
