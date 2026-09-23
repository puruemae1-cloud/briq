#!/usr/bin/env python3
"""Rebuild Dior clothing size options from Algolia when catalog is stuck on OS.

Compares RTW / homewear / swim products that only expose OS against dior.com
merch index variants, then rewrites selectable sizes + size charts.

  python3 scripts/patch-di-rtw-sizes-from-algolia.py
  python3 scripts/patch-di-rtw-sizes-from-algolia.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from di_common import algolia_merch_hits_by_codes, algolia_variant_gbp, gbp_to_krw, slugify  # noqa: E402
from di_size_charts import size_chart_for_di_mens_rtw, size_chart_for_di_womens_rtw  # noqa: E402

CAT = ROOT / "src/data/di/di-catalog.json"


def di_variant_sort_key(size: str | None) -> tuple:
    s = str(size or "").strip()
    m = re.search(r"(\d+(?:\.\d+)?)", s)
    if m:
        return (0, float(m.group(1)), s)
    order = ["XXXS", "XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL", "4XL"]
    su = s.upper()
    if su in order:
        return (1, order.index(su), s)
    return (2, s)


def list_price_from_variants(variants: list[dict], fallback: int = 0) -> int:
    prices = [
        int(v["price"])
        for v in variants
        if isinstance(v.get("price"), (int, float)) and v.get("price") > 0
    ]
    return min(prices) if prices else fallback

WOMEN_LEAVES = {
    "di-womens",
    "di-women-rtw-all",
    "di-women-tshirts",
    "di-women-shirts",
    "di-women-sweaters-cardigans",
    "di-women-dresses",
    "di-women-skirts",
    "di-women-trousers-shorts",
    "di-women-denim",
    "di-women-swimsuits",
    "di-women-homewear-lingerie",
    "di-women-coats",
    "di-women-jackets",
}

MEN_LEAVES = {
    "di-mens",
    "di-men-rtw-all",
    "di-men-tshirts-polos",
    "di-men-shirts",
    "di-men-knitwear-sweatshirts",
    "di-men-trousers-shorts",
    "di-men-denim",
    "di-men-beachwear",
    "di-men-outerwear",
    "di-men-tailored-jackets",
    "di-men-leather",
    "di-men-suits-tuxedos",
}

OS_SIZES = {"OS", "ONE SIZE", "TU", "U", "ONESIZE", "ONE-SIZE"}


def is_clothing(product: dict) -> bool:
    leaf = str(product.get("subcategory") or "")
    cols = set(product.get("diCollections") or [])
    return leaf in WOMEN_LEAVES or leaf in MEN_LEAVES or bool(cols & WOMEN_LEAVES) or bool(
        cols & MEN_LEAVES
    )


def is_women(product: dict) -> bool:
    leaf = str(product.get("subcategory") or "")
    cols = set(product.get("diCollections") or [])
    return leaf in WOMEN_LEAVES or bool(cols & WOMEN_LEAVES)


def is_os_only(product: dict) -> bool:
    sizes = [str(v.get("size") or "").strip().upper() for v in (product.get("variants") or [])]
    sizes = [s for s in sizes if s]
    return (not sizes) or (len(sizes) == 1 and sizes[0] in OS_SIZES)


def extract_sizes(hit: dict) -> list[dict]:
    raw = hit.get("variants") if isinstance(hit.get("variants"), list) else []
    out: list[dict] = []
    seen: set[str] = set()
    for vv in raw:
        if not isinstance(vv, dict):
            continue
        sz = str(vv.get("sizeFormatted") or vv.get("size") or "").strip()
        if not sz or sz.upper() in OS_SIZES or sz.startswith("{"):
            continue
        # Normalize T44 → prefer sizeFormatted already; strip leading T if numeric
        if sz.upper().startswith("T") and sz[1:].isdigit():
            sz = sz[1:]
        key = sz.upper()
        if key in seen:
            continue
        seen.add(key)
        out.append(vv if vv.get("sizeFormatted") else {**vv, "sizeFormatted": sz})
    return out


def rebuild_variants(product: dict, hit: dict, size_rows: list[dict]) -> list[dict]:
    pid = product["id"]
    images = product.get("images") or []
    image = images[0] if images else product.get("image") or ""
    gbp_f = float(product.get("gbpPrice") or 0)
    price = int(product.get("price") or 0)
    source_url = product.get("sourceUrl") or ""
    prev = product.get("variants") or []
    color_key = prev[0].get("colorKey") if prev else "default"
    color_ko = (prev[0].get("colorNameKo") if prev else None) or "기본"
    collections = product.get("diCollections") or []

    variants: list[dict] = []
    for vv in size_rows:
        sz = str(vv.get("sizeFormatted") or vv.get("size") or "").strip()
        if sz.upper().startswith("T") and sz[1:].isdigit():
            sz = sz[1:]
        v_gbp = algolia_variant_gbp(
            vv.get("price") if isinstance(vv.get("price"), dict) else None, gbp_f
        )
        variants.append(
            {
                "id": f"{pid}-sz-{slugify(sz, max_len=24)}",
                "name": sz,
                "nameKo": sz,
                "sku": str(vv.get("sku") or product.get("sku") or pid),
                "gbpPrice": v_gbp,
                "price": gbp_to_krw(v_gbp) if v_gbp else price,
                "image": image,
                "images": images,
                "sourceUrl": source_url,
                "inStock": True,
                "colorKey": color_key,
                "colorNameKo": color_ko,
                "size": sz,
                "diCollections": collections,
            }
        )
    return sorted(variants, key=lambda v: di_variant_sort_key(v.get("size")))


def fetch_sibling_hit(style_prefix: str) -> dict | None:
    """When a colorway is gone from Algolia, reuse sizes from another color of same style."""
    import urllib.parse
    import urllib.request

    from di_common import ALGOLIA_MERCH_API_KEY, ALGOLIA_MERCH_APP_ID, ALGOLIA_MERCH_INDEX

    if not style_prefix or len(style_prefix) < 6:
        return None
    params = urllib.parse.urlencode(
        {
            "query": style_prefix,
            "hitsPerPage": 10,
            "attributesToRetrieve": "*",
        }
    )
    body = json.dumps(
        {"requests": [{"indexName": ALGOLIA_MERCH_INDEX, "params": params}]}
    ).encode()
    url = f"https://{ALGOLIA_MERCH_APP_ID}-dsn.algolia.net/1/indexes/*/queries"
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Algolia-Application-Id": ALGOLIA_MERCH_APP_ID,
            "X-Algolia-API-Key": ALGOLIA_MERCH_API_KEY,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            hits = (json.loads(resp.read()).get("results") or [{}])[0].get("hits") or []
    except Exception:
        return None
    scored = []
    for h in hits:
        oid = str(h.get("objectID") or "")
        if style_prefix.replace("_", "") not in oid.replace("_", ""):
            continue
        rows = extract_sizes(h)
        if rows:
            scored.append((len(rows), h))
    if not scored:
        return None
    scored.sort(key=lambda x: -x[0])
    return scored[0][1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", default="", help="Comma-separated SKUs")
    args = ap.parse_args()

    products = json.loads(CAT.read_text())
    targets = [p for p in products if is_clothing(p) and is_os_only(p)]
    if args.only:
        want = {x.strip() for x in args.only.split(",") if x.strip()}
        targets = [p for p in targets if p.get("sku") in want]

    codes = [p["sku"] for p in targets if p.get("sku")]
    hits: dict[str, dict] = {}
    for i in range(0, len(codes), 15):
        hits.update(algolia_merch_hits_by_codes(codes[i : i + 15]))
        print(f"  algolia {min(i + 15, len(codes))}/{len(codes)}", flush=True)

    fixed = 0
    kept_os = 0
    missing = 0
    sibling = 0
    samples: list[str] = []

    by_id = {p["id"]: p for p in products}
    for p in targets:
        sku = p.get("sku") or ""
        hit = hits.get(sku) or {}
        size_rows = extract_sizes(hit) if hit else []
        if not size_rows:
            # style code before color: 341V33A6759_X0861 → 341V33A6759
            style = sku.split("_")[0] if "_" in sku else sku[:12]
            sib = fetch_sibling_hit(style)
            if sib:
                size_rows = extract_sizes(sib)
                if size_rows:
                    hit = sib
                    sibling += 1
        if not hit and not size_rows:
            missing += 1
            continue
        if len(size_rows) < 1:
            kept_os += 1
            continue
        variants = rebuild_variants(p, hit, size_rows)
        if len(variants) < 1:
            kept_os += 1
            continue
        leaf = str(p.get("subcategory") or "")
        title_en = p.get("name") or ""
        if is_women(p):
            chart = size_chart_for_di_womens_rtw(variants, leaf_id=leaf, title_en=title_en)
        else:
            chart = size_chart_for_di_mens_rtw(variants, leaf_id=leaf, title_en=title_en)
        p["variants"] = variants
        p["price"] = list_price_from_variants(variants, int(p.get("price") or 0))
        if chart:
            p["sizeChart"] = chart
        by_id[p["id"]] = p
        fixed += 1
        if len(samples) < 8:
            samples.append(
                f"{sku} → {[v.get('size') for v in variants[:8]]}"
                + ("…" if len(variants) > 8 else "")
            )

    print(
        f"DONE targets={len(targets)} fixed={fixed} kept_os={kept_os} "
        f"missing={missing} sibling={sibling}",
        flush=True,
    )
    for s in samples:
        print(" ", s, flush=True)

    if args.dry_run:
        print("dry-run: catalog not written", flush=True)
        return

    out = [by_id[p["id"]] for p in products]
    CAT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {CAT}", flush=True)


if __name__ == "__main__":
    main()
