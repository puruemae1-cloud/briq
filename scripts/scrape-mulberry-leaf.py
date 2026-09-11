#!/usr/bin/env python3
"""Scrape one Mulberry leaf PLP + PDPs into src/data/mb/*-raw.json."""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from mulberry_common import (  # noqa: E402
    RAW_DIR,
    download_images,
    load_json,
    save_json,
    scrape_pdp,
    scrape_plp,
    slugify,
)
from mulberry_config import leaf_by_id  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--leaf", required=True, help="Leaf id e.g. mb-women-clutches")
    ap.add_argument("--limit", type=int, default=0, help="Max PLP cards (0=all)")
    ap.add_argument("--skip-images", action="store_true")
    ap.add_argument("--skip-existing", action="store_true", help="Skip URLs already in raw")
    args = ap.parse_args()

    leaf = leaf_by_id(args.leaf)
    if not leaf:
        raise SystemExit(f"unknown leaf {args.leaf}")

    out_path = RAW_DIR / f"{args.leaf}-catalog-raw.json"
    payload = load_json(out_path, {"leafId": args.leaf, "products": []})
    existing = {p.get("url"): p for p in (payload.get("products") or []) if p.get("url")}

    print(f"== PLP {leaf['url']}", flush=True)
    cards = scrape_plp(leaf["url"])
    if args.limit:
        cards = cards[: args.limit]
    print(f"PLP cards={len(cards)}", flush=True)

    products = list(payload.get("products") or [])
    by_url = {p.get("url"): i for i, p in enumerate(products) if p.get("url")}

    for i, card in enumerate(cards, start=1):
        url = card["url"]
        print(f"[{i}/{len(cards)}] {card.get('title')} {url}", flush=True)
        if args.skip_existing and url in existing:
            print("  skip existing", flush=True)
            continue
        try:
            pdp = scrape_pdp(url)
        except Exception as e:
            print(f"  FAIL pdp: {e}", flush=True)
            continue
        if not pdp.get("title"):
            pdp["title"] = card.get("title") or ""
        if not pdp.get("gbpPrice"):
            pdp["gbpPrice"] = card.get("gbpPrice") or 0
        if not pdp.get("images") and card.get("plpImage"):
            pdp["images"] = [card["plpImage"]]

        slug = slugify(
            (pdp.get("sku") or "") or Path(url.rstrip("/")).name,
            max_len=64,
        )
        pdp["id"] = slug
        pdp["leafId"] = args.leaf
        pdp["collections"] = list(leaf.get("collections") or [])
        pdp["category"] = leaf.get("category") or "bags"

        if not args.skip_images and pdp.get("images"):
            local = download_images(slug, pdp["images"])
            if local:
                pdp["localImages"] = local

        if url in by_url:
            products[by_url[url]] = pdp
        else:
            by_url[url] = len(products)
            products.append(pdp)
        payload["products"] = products
        payload["leafId"] = args.leaf
        payload["url"] = leaf["url"]
        save_json(out_path, payload)
        time.sleep(0.4)

    print(f"wrote {len(products)} -> {out_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
