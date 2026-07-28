#!/usr/bin/env python3
"""Weekly Galvin Green stock/price sync for Briq gg catalog.

Re-fetches men-new / women-new products.json, updates matching variants by SKU,
adds new handles, rebuilds gg-catalog.ts.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "src/data/gg/gg-catalog-raw.json"

_spec = importlib.util.spec_from_file_location(
    "scrape_gg", ROOT / "scripts/scrape-gg-new-arrivals.py"
)
_scrape = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_scrape)

COLLECTIONS = _scrape.COLLECTIONS
assign_colors = _scrape.assign_colors
download_images = _scrape.download_images
normalize_product = _scrape.normalize_product
paginate_collection = _scrape.paginate_collection


def sync() -> None:
    if not RAW_PATH.exists():
        print("No raw catalog — running full scrape…")
        subprocess.check_call(
            [sys.executable, str(ROOT / "scripts/scrape-gg-new-arrivals.py")],
            cwd=str(ROOT),
        )
        return

    raw = json.loads(RAW_PATH.read_text())
    products: list[dict] = raw.get("products") or []
    by_handle = {p["handle"]: p for p in products if p.get("handle")}

    updated_stock = 0
    updated_price = 0
    added_handles = 0
    new_products: list[dict] = []
    collections_meta: dict[str, list[str]] = dict(raw.get("collections") or {})

    for shopify_handle, briq_coll in COLLECTIONS:
        print(f"Sync {shopify_handle}…")
        remote = paginate_collection(shopify_handle)
        handles: list[str] = []
        for r in remote:
            handles.append(r.get("handle") or "")
            norm = normalize_product(r, briq_coll)
            h = norm["handle"]
            if h not in by_handle:
                new_products.append(norm)
                by_handle[h] = norm
                products.append(norm)
                added_handles += 1
                print(f"  + new handle {h}")
                continue

            existing = by_handle[h]
            existing["title"] = norm["title"]
            existing["body_html"] = norm["body_html"]
            existing["tags"] = norm["tags"]
            existing["images"] = norm["images"] or existing.get("images")
            existing["styleName"] = norm["styleName"]
            existing["collection"] = briq_coll
            existing["published_at"] = norm.get("published_at") or existing.get("published_at")

            remote_by_sku = {v["sku"]: v for v in norm["variants"] if v.get("sku")}
            existing_skus = {v.get("sku") for v in existing.get("variants") or []}

            for v in existing.get("variants") or []:
                sku = v.get("sku")
                if not sku or sku not in remote_by_sku:
                    if v.get("available"):
                        v["available"] = False
                        updated_stock += 1
                    continue
                rv = remote_by_sku[sku]
                if bool(v.get("available")) != bool(rv.get("available")):
                    v["available"] = bool(rv.get("available"))
                    updated_stock += 1
                if v.get("price") != rv.get("price"):
                    v["price"] = rv.get("price")
                    updated_price += 1
                if v.get("compare_at_price") != rv.get("compare_at_price"):
                    v["compare_at_price"] = rv.get("compare_at_price")
                    updated_price += 1

            for sku, rv in remote_by_sku.items():
                if sku not in existing_skus:
                    existing.setdefault("variants", []).append(rv)
                    updated_stock += 1
                    print(f"  + new sku {sku} on {h}")

        collections_meta[shopify_handle] = [h for h in handles if h]
        time.sleep(0.15)

    assign_colors(products)

    if new_products:
        print(f"Downloading images for {len(new_products)} new colorways…")
        download_images(new_products)

    raw["scrapedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    raw["collections"] = collections_meta
    raw["products"] = products
    RAW_PATH.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("Rebuilding gg-catalog.ts …")
    subprocess.check_call([sys.executable, str(ROOT / "scripts/build-gg-catalog.py")], cwd=str(ROOT))

    men = len(collections_meta.get("men-new") or [])
    women = len(collections_meta.get("women-new") or [])
    print("=== GG weekly sync summary ===")
    print(f"  men-new handles:   {men}")
    print(f"  women-new handles: {women}")
    print(f"  total colorways:   {len(products)}")
    print(f"  stock updates:     {updated_stock}")
    print(f"  price updates:     {updated_price}")
    print(f"  new handles:       {added_handles}")


if __name__ == "__main__":
    sync()
