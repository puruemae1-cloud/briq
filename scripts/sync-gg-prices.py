#!/usr/bin/env python3
"""Refresh Galvin Green price / compare_at / stock from live product.js for every colourway."""
from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "src/data/gg/gg-catalog-raw.json"

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def fetch_js(handle: str) -> dict | None:
    url = f"https://www.galvingreen.com/en-gb/products/{handle}.js"
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except Exception as e:
            wait = 1.5 * (attempt + 1)
            print(f"  warn {handle}: {e} — retry {wait:.1f}s")
            time.sleep(wait)
    return None


def sync() -> None:
    raw = json.loads(RAW_PATH.read_text())
    products = raw.get("products") or []
    updated = 0
    sale_colors = 0
    failed = 0

    for i, p in enumerate(products, 1):
        handle = p.get("handle")
        if not handle:
            continue
        js = fetch_js(handle)
        time.sleep(0.12)
        if not js:
            failed += 1
            continue

        by_sku = {}
        for v in js.get("variants") or []:
            sku = v.get("sku") or ""
            price = v.get("price")
            # cents → pounds string
            if isinstance(price, (int, float)) and price > 999:
                price_str = f"{price / 100:.2f}"
            else:
                price_str = str(price) if price is not None else "0"
            cap = v.get("compare_at_price")
            if isinstance(cap, (int, float)) and cap and cap > 999:
                cap_str = f"{cap / 100:.2f}"
            elif cap:
                cap_str = str(cap)
            else:
                cap_str = None
            by_sku[sku] = {
                "price": price_str,
                "compare_at_price": cap_str,
                "available": bool(v.get("available")),
                "size": v.get("option1") or v.get("title") or "",
            }

        changed = False
        has_sale = False
        for v in p.get("variants") or []:
            sku = v.get("sku") or ""
            remote = by_sku.get(sku)
            if not remote:
                # match by size
                size = str(v.get("size") or "")
                remote = next(
                    (r for r in by_sku.values() if r["size"] == size),
                    None,
                )
            if not remote:
                continue
            if v.get("price") != remote["price"]:
                v["price"] = remote["price"]
                changed = True
            if v.get("compare_at_price") != remote["compare_at_price"]:
                v["compare_at_price"] = remote["compare_at_price"]
                changed = True
            if bool(v.get("available")) != remote["available"]:
                v["available"] = remote["available"]
                changed = True
            if remote["compare_at_price"]:
                try:
                    if float(remote["compare_at_price"]) > float(remote["price"]):
                        has_sale = True
                except (TypeError, ValueError):
                    pass

        if changed:
            updated += 1
        if has_sale:
            sale_colors += 1
        if i % 25 == 0 or i == len(products):
            print(f"… {i}/{len(products)} updated={updated} sale_colorways={sale_colors}")

    RAW_PATH.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Raw updated. colourways_changed={updated} sale_colorways={sale_colors} failed={failed}")
    print("Rebuilding gg-catalog.ts …")
    subprocess.check_call(
        [sys.executable, str(ROOT / "scripts/build-gg-catalog.py")],
        cwd=str(ROOT),
    )


if __name__ == "__main__":
    sync()
