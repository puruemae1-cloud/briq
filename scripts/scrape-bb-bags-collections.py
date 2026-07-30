#!/usr/bin/env python3
"""Scrape Burberry Bags Collections PLPs and merge bb-bags-collections-* into bb-catalog-raw.json."""
from __future__ import annotations

import importlib.util
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bb_bags_collections_config import BAGS_COLLECTIONS  # noqa: E402
from bb_women_config import BASE  # noqa: E402

# Keep in sync with build-bb-catalog.EXCLUDED_TITLES
EXCLUDED_TITLES = {"Wide Check Wool Silk Scarf"}
EXCLUDED_COLOURWAY_IDS = {
    "80787791",
    "80787821",
    "81101611",
    "81101621",
    "81106531",
    "81124591",
    "81124611",
    "81124621",
    "81124631",
    "81134271",
    "81225811",
    "81225831",
    "81232511",
}

RAW_PATH = ROOT / "src/data/bb/bb-catalog-raw.json"
PDP_CACHE = ROOT / "src/data/bb/bb-pdp-cache.json"
IMG_ROOT = ROOT / "public/products/bb-pdp"
MAX_WORKERS = 8
PREFIX = "bb-bags-collections-"

_spec = importlib.util.spec_from_file_location(
    "scrape_bb_women", ROOT / "scripts/scrape-bb-women.py"
)
_scrape = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_scrape)

scrape_collection = _scrape.scrape_collection
enrich_one = _scrape.enrich_one


def main() -> None:
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    IMG_ROOT.mkdir(parents=True, exist_ok=True)

    existing = {}
    if RAW_PATH.exists():
        existing = json.loads(RAW_PATH.read_text())
    old_products = {
        str(p["id"]): p for p in (existing.get("products") or []) if p.get("id")
    }

    cache: dict = {}
    if PDP_CACHE.exists():
        cache = json.loads(PDP_CACHE.read_text())

    membership: dict[str, set[str]] = {}
    for pid, prod in old_products.items():
        cols = [
            c for c in (prod.get("collections") or []) if not str(c).startswith(PREFIX)
        ]
        if cols:
            membership[pid] = set(cols)

    plp_meta: dict[str, dict] = {
        k: v
        for k, v in (existing.get("collections") or {}).items()
        if not str(k).startswith(PREFIX)
    }

    cards: dict[str, dict] = {}
    for pid, prod in old_products.items():
        cards[pid] = {
            "id": pid,
            "title": prod.get("title") or "",
            "url": (prod.get("url") or "").replace(BASE, "") or "",
            "color": prod.get("color") or "",
            "gbpPrice": prod.get("gbpPrice"),
            "gbpListPrice": prod.get("gbpListPrice"),
            "image": prod.get("image") or "",
            "label": prod.get("label"),
        }

    for coll_id, label, path, top, _parent in BAGS_COLLECTIONS:
        items = scrape_collection(coll_id, path)
        plp_meta[coll_id] = {
            "label": label,
            "path": path,
            "category": top,
            "count": len(items),
        }
        for it in items:
            pid = it["id"]
            title = (it.get("title") or "").replace("\u200b", "").strip()
            if pid in EXCLUDED_COLOURWAY_IDS or title in EXCLUDED_TITLES:
                continue
            membership.setdefault(pid, set()).add(coll_id)
            prev = cards.get(pid) or {}
            if not prev.get("gbpPrice") and it.get("gbpPrice"):
                cards[pid] = it
            elif it.get("title") and len(it["title"]) > len(prev.get("title") or ""):
                cards[pid] = {**prev, **it}
            else:
                cards.setdefault(pid, it)

    scarf_ids = sorted(
        pid
        for pid, cols in membership.items()
        if any(str(c).startswith(PREFIX) for c in cols)
    )
    need = [
        pid
        for pid in scarf_ids
        if pid not in cache or not (cache.get(pid) or {}).get("localImages")
    ]
    print(
        f"Bags-collections-linked colourways: {len(scarf_ids)} (enrich {len(need)})",
        flush=True,
    )

    def job(pid: str) -> tuple[str, dict | None, str | None]:
        card = cards.get(pid) or {}
        path = card.get("url") or f"-p{pid}"
        if path.startswith("http"):
            path = path.replace(BASE, "")
        if not path.startswith("/"):
            path = "/" + path
        try:
            if pid in cache and not cache[pid].get("localImages"):
                del cache[pid]
            pdp = enrich_one(pid, path, cache)
            return pid, pdp, None
        except Exception as e:  # noqa: BLE001
            return pid, None, str(e)

    errors = []
    if need:
        done = 0
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futs = {ex.submit(job, pid): pid for pid in need}
            for fut in as_completed(futs):
                pid, pdp, err = fut.result()
                done += 1
                if done % 25 == 0 or done == len(need):
                    PDP_CACHE.write_text(json.dumps(cache, ensure_ascii=False))
                    print(f"  Bags-collections PDP {done}/{len(need)}", flush=True)
                if err:
                    errors.append({"id": pid, "error": err})

    products = []
    for pid, cols in sorted(membership.items()):
        if pid in EXCLUDED_COLOURWAY_IDS:
            continue
        card = cards.get(pid) or {}
        title = (
            (cache.get(pid) or {}).get("name")
            or card.get("title")
            or (old_products.get(pid) or {}).get("title")
            or ""
        )
        if str(title).replace("\u200b", "").strip() in EXCLUDED_TITLES:
            continue
        pdp = cache.get(pid) or old_products.get(pid) or {}
        prev = old_products.get(pid) or {}
        local_imgs = pdp.get("localImages") or prev.get("images") or []
        products.append(
            {
                "id": pid,
                "title": pdp.get("name") or card.get("title") or prev.get("title") or "",
                "url": pdp.get("sourceUrl")
                or prev.get("url")
                or (f"{BASE}{card['url']}" if card.get("url") else ""),
                "color": pdp.get("color") or card.get("color") or prev.get("color") or "",
                "gbpPrice": pdp.get("gbpPrice")
                or card.get("gbpPrice")
                or prev.get("gbpPrice"),
                "gbpListPrice": pdp.get("gbpListPrice")
                or card.get("gbpListPrice")
                or prev.get("gbpListPrice"),
                "image": (local_imgs[0] if local_imgs else None)
                or card.get("image")
                or prev.get("image")
                or "",
                "images": local_imgs or prev.get("images") or [],
                "remoteImages": pdp.get("images") or prev.get("remoteImages") or [],
                "sizes": pdp.get("sizes") or prev.get("sizes") or [],
                "swatches": pdp.get("swatches") or prev.get("swatches") or [],
                "description": pdp.get("description") or prev.get("description") or "",
                "accordion": pdp.get("accordion") or prev.get("accordion") or [],
                "measurements": pdp.get("measurements") or prev.get("measurements"),
                "materialComposition": pdp.get("materialComposition")
                or prev.get("materialComposition"),
                "collections": sorted(cols),
                "label": card.get("label") or prev.get("label"),
            }
        )

    payload = {
        "scrapedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": BASE,
        "collectionCounts": {
            k: (v.get("count") if isinstance(v, dict) else v)
            for k, v in plp_meta.items()
            if isinstance(v, dict) and "count" in v
        },
        "collections": plp_meta,
        "productCount": len(products),
        "errors": errors,
        "products": products,
    }
    RAW_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    PDP_CACHE.write_text(json.dumps(cache, ensure_ascii=False))
    print(
        f"Wrote {RAW_PATH} products={len(products)} bags_collections_errors={len(errors)}",
        flush=True,
    )


if __name__ == "__main__":
    main()
