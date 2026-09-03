#!/usr/bin/env python3
"""Reclassify Dior Accessorize Your Bag SKUs into official category.lvl2 leaves.

Bags → Dior → 여성용 → 악세서리 Your Bag → (백 주얼리 / 토트용 / …)

Uses Algolia merch category.lvl2 for each SKU already under di-accessorize-bag
(or on the official accessorize PLP), then writes di-catalog.json.

  python3 scripts/reclassify-di-accessorize-bag.py
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from di_common import (  # noqa: E402
    ACCESSORIZE_BAG_LEAVES,
    ACCESSORIZE_BAG_LVL2_TO_ID,
    ALGOLIA_MERCH_API_KEY,
    ALGOLIA_MERCH_APP_ID,
    ALGOLIA_MERCH_INDEX,
    PARENT_COLS_ACCESSORIZE_BAG,
    extract_next_data,
    BASE,
    LANG,
    UA,
)

CAT = ROOT / "src/data/di/di-catalog.json"
LEAVES_OUT = ROOT / "src/data/di/di-accessorize-bag-leaves.json"
RAW_OUT = ROOT / "src/data/di/di-accessorize-bag-catalog-raw.json"


def log(msg: str) -> None:
    print(msg, flush=True)


def fetch_hits_by_object_ids(oids: list[str]) -> list[dict]:
    out: list[dict] = []
    for i in range(0, len(oids), 40):
        chunk = oids[i : i + 40]
        filt = " OR ".join(f'objectID:"{o}"' for o in chunk)
        params = urllib.parse.urlencode(
            {
                "query": "",
                "hitsPerPage": 40,
                "filters": filt,
                "attributesToRetrieve": "*",
            }
        )
        body = json.dumps(
            {"requests": [{"indexName": ALGOLIA_MERCH_INDEX, "params": params}]}
        ).encode()
        req = urllib.request.Request(
            f"https://{ALGOLIA_MERCH_APP_ID}-dsn.algolia.net/1/indexes/*/queries",
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-Algolia-Application-Id": ALGOLIA_MERCH_APP_ID,
                "X-Algolia-API-Key": ALGOLIA_MERCH_API_KEY,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            hits = json.loads(r.read())["results"][0].get("hits") or []
        out.extend(hits)
    return out


def lvl2_of(hit: dict) -> str:
    cat = hit.get("category") or {}
    v = cat.get("lvl2") if isinstance(cat, dict) else None
    if isinstance(v, list):
        v = v[0] if v else None
    if not v:
        v = hit.get("category.lvl2") or hit.get("category_lvl2")
        if isinstance(v, list):
            v = v[0] if v else None
    return (str(v) if v else "").strip()


def sku_key(sku: str) -> str:
    return (sku or "").replace("_", "").upper()


def main() -> int:
    LEAVES_OUT.write_text(
        json.dumps(ACCESSORIZE_BAG_LEAVES, ensure_ascii=False, indent=2) + "\n"
    )

    # Prefer live PLP object IDs; fall back to catalog accessorize membership
    oids: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        import time

        url = f"{BASE}/{LANG}/fashion/womens-fashion/bags/accessorize-your-bag"
        with sync_playwright() as p:
            browser = p.webkit.launch(headless=True)
            page = browser.new_context(
                user_agent=UA, locale="en-GB", viewport={"width": 1440, "height": 900}
            ).new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=120000)
            time.sleep(1.5)
            for sel in (
                "#onetrust-accept-btn-handler",
                'button:has-text("Accept All")',
            ):
                try:
                    page.locator(sel).first.click(timeout=2000)
                    break
                except Exception:
                    pass
            time.sleep(1)
            for _ in range(5):
                page.mouse.wheel(0, 2800)
                time.sleep(0.25)
            pp = (
                ((extract_next_data(page.content()) or {}).get("props") or {}).get(
                    "pageProps"
                )
                or {}
            )
            results = (
                ((pp.get("partialFiltersState") or {}).get("result") or {}).get(
                    "results"
                )
                or []
            )
            oids = [
                x["objectID"]
                for x in results
                if isinstance(x, dict) and x.get("objectID")
            ]
            # follow pagination if any
            pag = pp.get("pagination") or {}
            next_url = pag.get("next")
            pages = 0
            while next_url and pages < 6:
                pages += 1
                page.goto(next_url, wait_until="domcontentloaded", timeout=120000)
                time.sleep(1.2)
                for _ in range(4):
                    page.mouse.wheel(0, 2600)
                    time.sleep(0.2)
                pp2 = (
                    ((extract_next_data(page.content()) or {}).get("props") or {}).get(
                        "pageProps"
                    )
                    or {}
                )
                results2 = (
                    ((pp2.get("partialFiltersState") or {}).get("result") or {}).get(
                        "results"
                    )
                    or []
                )
                for x in results2:
                    if isinstance(x, dict) and x.get("objectID"):
                        oids.append(x["objectID"])
                next_url = ((pp2.get("pagination") or {}).get("next"))
            browser.close()
        oids = list(dict.fromkeys(oids))
        log(f"plp objectIDs={len(oids)}")
    except Exception as e:
        log(f"WARN plp fetch failed: {e}")

    products = json.loads(CAT.read_text())
    by_sku = {
        sku_key(p.get("sku") or ""): p
        for p in products
        if p.get("sku")
    }

    # Also include existing catalog accessorize members
    existing = [
        p
        for p in products
        if p.get("subcategory") == "di-accessorize-bag"
        or "di-accessorize-bag" in (p.get("diCollections") or [])
        or str(p.get("subcategory") or "").startswith("di-acc-bag-")
    ]
    log(f"catalog accessorize-ish={len(existing)}")

    hits = fetch_hits_by_object_ids(oids) if oids else []
    # Map sku -> lvl2 from PLP hits
    sku_to_lvl2: dict[str, str] = {}
    sku_to_hit: dict[str, dict] = {}
    for h in hits:
        sku = str(h.get("sku") or h.get("productId") or "").upper()
        if not sku:
            # objectID prd-CODE
            oid = str(h.get("objectID") or "")
            if oid.startswith("prd-"):
                sku = oid[4:]
        key = sku_key(sku)
        lv = lvl2_of(h)
        if key and lv:
            sku_to_lvl2[key] = lv
            sku_to_hit[key] = h

    # For existing without hit, try merch by sku
    missing = []
    for p in existing:
        key = sku_key(p.get("sku") or "")
        if key and key not in sku_to_lvl2:
            missing.append(key)
    if missing:
        log(f"fetch missing merch={len(missing)}")
        # build fake objectIDs from sku
        more_oids = []
        for p in existing:
            key = sku_key(p.get("sku") or "")
            if key in missing:
                # try common objectID forms
                more_oids.append("prd-" + key)
        more = fetch_hits_by_object_ids(list(dict.fromkeys(more_oids)))
        for h in more:
            sku = str(h.get("sku") or "").upper()
            key = sku_key(sku)
            lv = lvl2_of(h)
            if key and lv:
                sku_to_lvl2[key] = lv
                sku_to_hit[key] = h

    counts: Counter[str] = Counter()
    unmapped: list[str] = []
    touched = 0
    raw_rows: list[dict] = []

    targets = {id(p) for p in existing}
    # Also add any PLP hit present in catalog
    for key, h in sku_to_hit.items():
        p = by_sku.get(key)
        if p:
            targets.add(id(p))

    for p in products:
        if id(p) not in targets:
            continue
        key = sku_key(p.get("sku") or "")
        lv = sku_to_lvl2.get(key, "")
        leaf = ACCESSORIZE_BAG_LVL2_TO_ID.get(lv)
        if not leaf:
            # fuzzy: strip trailing spaces already; try casefold
            for k, lid in ACCESSORIZE_BAG_LVL2_TO_ID.items():
                if k.casefold() == lv.casefold():
                    leaf = lid
                    break
        if not leaf:
            unmapped.append(f"{key}:{lv or '?'}")
            leaf = "di-accessorize-bag"
            counts["di-accessorize-bag"] += 1
        else:
            counts[leaf] += 1

        cols = list(dict.fromkeys([*(p.get("diCollections") or []), *PARENT_COLS_ACCESSORIZE_BAG, leaf]))
        p["category"] = "bags"
        p["subcategory"] = leaf
        p["diCollections"] = cols
        # keep tags sensible
        tags = set(p.get("tags") or [])
        tags.update({"dior", "디올", "bags", "handbags", "가방", "핸드백", "여성", "accessorize"})
        p["tags"] = sorted(tags)
        touched += 1
        raw_rows.append(
            {
                "sku": p.get("sku"),
                "id": p.get("id"),
                "lvl2": lv,
                "leaf": leaf,
                "name": p.get("name"),
                "nameKo": p.get("nameKo"),
                "images": p.get("images") or [],
            }
        )

    CAT.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n")
    RAW_OUT.write_text(
        json.dumps(
            {"products": raw_rows, "counts": dict(counts), "leaves": ACCESSORIZE_BAG_LEAVES},
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    log(f"touched={touched}")
    for lid, n in sorted(counts.items(), key=lambda x: -x[1]):
        log(f"  {lid}: {n}")
    if unmapped:
        log(f"unmapped={len(unmapped)} sample={unmapped[:8]}")
    return 0 if touched else 1


if __name__ == "__main__":
    raise SystemExit(main())
