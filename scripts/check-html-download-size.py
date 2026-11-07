#!/usr/bin/env python3
"""Fail when key HTML pages exceed Naver-friendly uncompressed sizes.

Naver Search Advisor "웹 페이지 다운로드 크기" tracks decoded HTML bytes.
Keep /, /shop, and hubs under the budgets below (4MB is the hard error
threshold; we fail earlier so crawl budget stays useful).

Also verifies card APIs ship slim DTOs (no PDP variant skus/tags).
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request

SITE = os.environ.get("SITE", "https://www.briq.kr").rstrip("/")
UA = "Mozilla/5.0 (compatible; briq-html-size-guard/1.0; +https://www.briq.kr)"

# Uncompressed HTML budgets (bytes). Tuned for slim card DTOs + shop page-1 SSR.
BUDGETS = {
    "/": 520_000,
    "/shop": 320_000,
    "/brands": 200_000,
}

EXPECTED_DTO = 3


def fetch(path: str) -> bytes:
    req = urllib.request.Request(
        f"{SITE}{path}",
        headers={"User-Agent": UA, "Accept-Encoding": "identity"},
    )
    with urllib.request.urlopen(req, timeout=90) as res:
        return res.read()


def fetch_json(path: str) -> dict:
    return json.loads(fetch(path))


def check_card_dto(path: str, payload: dict, errors: list[str]) -> None:
    dto = payload.get("dto")
    if dto != EXPECTED_DTO:
        errors.append(f"{path}: dto={dto!r} expected {EXPECTED_DTO} (slim deploy missing?)")
        return

    products: list[dict] = []
    if isinstance(payload.get("products"), list):
        products.extend(payload["products"])
    rails = payload.get("rails") or {}
    if isinstance(rails, dict):
        for items in rails.values():
            if isinstance(items, list):
                products.extend(items)
    for key in ("signature", "newItems", "flannels"):
        items = payload.get(key)
        if isinstance(items, list):
            products.extend(items)

    for product in products[:40]:
        if not isinstance(product, dict):
            continue
        if product.get("tags") is not None:
            errors.append(f"{path}: card product still has tags ({product.get('id')})")
            return
        if product.get("descriptionKo") or product.get("description"):
            errors.append(
                f"{path}: card product still has description ({product.get('id')})"
            )
            return
        for variant in product.get("variants") or []:
            if not isinstance(variant, dict):
                continue
            if variant.get("sku") or variant.get("gbpPrice") or variant.get("sourceUrl"):
                errors.append(
                    f"{path}: fat variant fields on {product.get('id')} "
                    f"(sku/gbpPrice/sourceUrl must be omitted)"
                )
                return
            images = variant.get("images")
            if isinstance(images, list) and len(images) > 0:
                errors.append(
                    f"{path}: variant images[] on {product.get('id')} "
                    "(omit per-variant galleries from cards)"
                )
                return
            if len(product.get("variants") or []) > 6:
                errors.append(
                    f"{path}: {product.get('id')} has "
                    f"{len(product['variants'])} variants (cap 6 for cards)"
                )
                return


def main() -> int:
    errors: list[str] = []

    try:
        shop = fetch_json("/api/products/shop?category=all&limit=8")
        check_card_dto("/api/products/shop", shop, errors)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"/api/products/shop: fetch failed ({exc})")

    try:
        home = fetch_json("/api/home-data?v=guard")
        check_card_dto("/api/home-data", home, errors)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"/api/home-data: fetch failed ({exc})")

    for path, budget in BUDGETS.items():
        try:
            body = fetch(path)
        except Exception as exc:  # noqa: BLE001 — surface any fetch failure
            errors.append(f"{path}: fetch failed ({exc})")
            continue
        size = len(body)
        kb = size / 1024
        budget_kb = budget / 1024
        status = "ok" if size <= budget else "OVER"
        print(f"{status}: {path} {size:,} bytes ({kb:.1f} KB) budget={budget_kb:.0f} KB")
        if size > budget:
            errors.append(
                f"{path}: {size:,} bytes exceeds {budget:,} "
                "(slim card DTOs / cap variants / avoid SSR page-2 shop grids)"
            )

    if errors:
        print("html download size check failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print("ok: key HTML pages within Naver download-size budgets + slim card DTOs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
