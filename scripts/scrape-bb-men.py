#!/usr/bin/env python3
"""Scrape Burberry Men PLPs + PDPs and merge into bb-catalog-raw.json."""
from __future__ import annotations

import importlib.util
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bb_men_config import MEN_COLLECTIONS  # noqa: E402
from bb_women_config import BASE  # noqa: E402

RAW_PATH = ROOT / "src/data/bb/bb-catalog-raw.json"
PDP_CACHE = ROOT / "src/data/bb/bb-pdp-cache.json"
IMG_ROOT = ROOT / "public/products/bb-pdp"
MAX_WORKERS = 8

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
    # Keep non-men collections from existing women scrape
    for pid, prod in old_products.items():
        cols = [c for c in (prod.get("collections") or []) if not str(c).startswith("bb-men-")]
        if cols:
            membership[pid] = set(cols)

    plp_meta: dict[str, dict] = dict(existing.get("collections") or {})
    # Drop previous men collection meta; will refresh
    plp_meta = {k: v for k, v in plp_meta.items() if not str(k).startswith("bb-men-")}

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

    for coll_id, label, path, top, _parent in MEN_COLLECTIONS:
        items = scrape_collection(coll_id, path)
        plp_meta[coll_id] = {
            "label": label,
            "path": path,
            "category": top,
            "count": len(items),
        }
        for it in items:
            pid = it["id"]
            membership.setdefault(pid, set()).add(coll_id)
            prev = cards.get(pid) or {}
            if not prev.get("gbpPrice") and it.get("gbpPrice"):
                cards[pid] = it
            elif it.get("title") and len(it["title"]) > len(prev.get("title") or ""):
                cards[pid] = {**prev, **it}
            else:
                cards.setdefault(pid, it)

    # Only enrich colourways that have at least one men collection (new or updated)
    men_ids = sorted(
        pid
        for pid, cols in membership.items()
        if any(str(c).startswith("bb-men-") for c in cols)
    )
    print(f"Men-linked colourways to enrich: {len(men_ids)}", flush=True)

    def job(pid: str) -> tuple[str, dict | None, str | None]:
        card = cards.get(pid) or {}
        path = card.get("url") or f"-p{pid}"
        if path.startswith("http"):
            path = path.replace(BASE, "")
        if not path.startswith("/"):
            path = "/" + path
        try:
            # Force refresh sizes for men pass when missing local images
            if pid in cache and not cache[pid].get("localImages"):
                del cache[pid]
            pdp = enrich_one(pid, path, cache)
            return pid, pdp, None
        except Exception as e:  # noqa: BLE001
            return pid, None, str(e)

    errors = []
    done = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(job, pid): pid for pid in men_ids}
        for fut in as_completed(futs):
            pid, pdp, err = fut.result()
            done += 1
            if done % 25 == 0 or done == len(men_ids):
                PDP_CACHE.write_text(json.dumps(cache, ensure_ascii=False))
                print(f"  Men PDP {done}/{len(men_ids)}", flush=True)
            if err:
                errors.append({"id": pid, "error": err})

    # Sibling swatches for men products
    extra_ids: list[str] = []
    for pid in list(men_ids):
        pdp = cache.get(pid) or {}
        for sw in pdp.get("swatches") or []:
            sid = str(sw.get("id"))
            if sid and sid not in membership:
                membership[sid] = set(membership.get(pid) or [])
                cards.setdefault(
                    sid,
                    {
                        "id": sid,
                        "title": sw.get("name") or "",
                        "url": sw.get("url") or f"-p{sid}",
                        "color": sw.get("label") or "",
                        "image": sw.get("image") or "",
                    },
                )
                extra_ids.append(sid)
    extra_ids = sorted(set(extra_ids))
    if extra_ids:
        print(f"Men sibling colourways: {len(extra_ids)}", flush=True)
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futs = {ex.submit(job, pid): pid for pid in extra_ids}
            for i, fut in enumerate(as_completed(futs), start=1):
                pid, pdp, err = fut.result()
                if i % 25 == 0 or i == len(extra_ids):
                    PDP_CACHE.write_text(json.dumps(cache, ensure_ascii=False))
                    print(f"  sibling PDP {i}/{len(extra_ids)}", flush=True)
                if err:
                    errors.append({"id": pid, "error": err})

    products = []
    for pid, cols in sorted(membership.items()):
        card = cards.get(pid) or {}
        pdp = cache.get(pid) or old_products.get(pid) or {}
        # Prefer cache PDP fields; fall back to previous raw product
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
        f"Wrote {RAW_PATH} products={len(products)} men_errors={len(errors)}",
        flush=True,
    )


if __name__ == "__main__":
    main()
