#!/usr/bin/env python3
"""Scrape Bottega Veneta UK hub → raw catalog JSON.

  BV_LIMIT=3 python3 scripts/scrape-bv-hub.py --hub men-travel
  python3 scripts/scrape-bv-hub.py --all
  BV_REFRESH_STOCK=1 python3 scripts/scrape-bv-hub.py --hub men-bags
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from bv_common import (  # noqa: E402
    MAX_WORKERS,
    fetch_product,
    iter_plp,
    load_json,
    product_row_from_pdp,
    save_json,
)
from bv_config import HUB_ORDER, HUBS_BY_ID, PDP_CACHE, RAW_DIR, merge_product_rows  # noqa: E402

_CACHE_LOCK = Lock()


def _limit() -> int:
    try:
        return int(os.environ.get("BV_LIMIT") or "0")
    except ValueError:
        return 0


def _refresh_stock() -> bool:
    return os.environ.get("BV_REFRESH_STOCK", "").strip() in {"1", "true", "yes"}


def _save_cache(cache: dict) -> None:
    """Snapshot under lock so json.dumps never races worker inserts."""
    with _CACHE_LOCK:
        snap = dict(cache)
    save_json(PDP_CACHE, snap)


def _scrape_one(
    pid: str,
    plp_url: str,
    leaf: dict,
    cache: dict,
    *,
    refresh: bool,
) -> dict:
    with _CACHE_LOCK:
        hit = (
            (not refresh)
            and pid in cache
            and cache[pid].get("localImages")
            and not cache[pid].get("pdpError")
        )
        cached = dict(cache[pid]) if hit else None
    if cached is not None:
        cached["collections"] = list(leaf.get("collections") or [])
        cached["leafId"] = leaf.get("id")
        cached["cgid"] = leaf.get("cgid")
        return cached
    try:
        data = fetch_product(pid)
        prod = data.get("product") or {}
        row = product_row_from_pdp(
            pid,
            prod,
            leaf=leaf,
            plp_url=plp_url,
            refresh_sizes=True,
        )
        with _CACHE_LOCK:
            cache[pid] = row
        return row
    except Exception as e:
        row = {
            "id": pid,
            "sku": pid,
            "collections": list(leaf.get("collections") or []),
            "leafId": leaf.get("id"),
            "cgid": leaf.get("cgid"),
            "url": plp_url,
            "pdpError": f"{type(e).__name__}: {e}",
        }
        print(f"    WARN pdp {pid}: {e}", flush=True)
        return row


def scrape_hub(hub_id: str, *, limit: int = 0) -> int:
    hub = HUBS_BY_ID[hub_id]
    leaves = list(hub["leaves"])
    # Also tag hub parent membership via hub cgid scrape when hub has many leaves
    # (travel already includes hub as its only leaf).
    out_path = RAW_DIR / hub["out"]
    existing = load_json(out_path, {"products": []})
    products = existing.get("products") or []
    cache = load_json(PDP_CACHE, {})
    if not isinstance(cache, dict):
        cache = {}
    refresh = _refresh_stock()
    limit = limit or _limit()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"== BV hub {hub_id} leaves={len(leaves)} limit={limit or '∞'} refresh={refresh} ==", flush=True)

    for leaf in leaves:
        leaf = dict(leaf)
        leaf["_hubCategory"] = hub["category"]
        print(f"-- leaf {leaf['id']} cgid={leaf['cgid']} --", flush=True)
        tiles = iter_plp(leaf["cgid"])
        official = tiles[0]["officialCount"] if tiles else None
        print(f"  plp official={official} scraped={len(tiles)}", flush=True)

        if limit:
            tiles = tiles[:limit]

        rows: list[dict] = []
        # Membership-only hubs still fetch PDP for new gift SKUs; existing get tagged.
        skip_full = bool(hub.get("membershipOnly")) and not refresh
        known_ids = {str(p.get("id")) for p in products}

        def work(tile: dict) -> dict:
            pid = tile["pid"]
            if skip_full and pid in known_ids:
                return {
                    "id": pid,
                    "sku": pid,
                    "collections": list(leaf.get("collections") or []),
                    "leafId": leaf["id"],
                    "cgid": leaf["cgid"],
                }
            return _scrape_one(pid, tile.get("url") or "", leaf, cache, refresh=refresh)

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futs = [ex.submit(work, t) for t in tiles]
            for i, fut in enumerate(as_completed(futs), start=1):
                rows.append(fut.result())
                if i % 20 == 0 or i == len(futs):
                    print(f"    {i}/{len(futs)}", flush=True)
                    _save_cache(cache)

        products = merge_product_rows(products, rows)
        print(
            f"  leaf done official={official} scraped_tiles={len(tiles)} "
            f"hub_products={len(products)}",
            flush=True,
        )
        save_json(
            out_path,
            {
                "hub": hub_id,
                "category": hub["category"],
                "scrapedAt": datetime.now(timezone.utc).isoformat(),
                "leaves": [l["id"] for l in hub["leaves"]],
                "leafCounts": {
                    **(existing.get("leafCounts") or {}),
                    leaf["id"]: {"official": official, "scraped": len(tiles)},
                },
                "products": products,
            },
        )
        existing = load_json(out_path, {"products": products})
        time.sleep(0.2)

    _save_cache(cache)
    print(f"OK {hub_id} products={len(products)} → {out_path}", flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hub", default="", help="Hub id (e.g. men-travel)")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    if args.all:
        hubs = HUB_ORDER
    elif args.hub:
        if args.hub not in HUBS_BY_ID:
            raise SystemExit(f"unknown hub: {args.hub}; choose from {HUB_ORDER}")
        hubs = [args.hub]
    else:
        raise SystemExit("pass --hub <id> or --all")

    rc = 0
    for hid in hubs:
        try:
            scrape_hub(hid, limit=args.limit)
        except Exception as e:
            print(f"ERROR hub {hid}: {e}", flush=True)
            rc = 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
