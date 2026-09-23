#!/usr/bin/env python3
"""Rebuild Dior size options from Algolia (full size run + OOS chips).

- Expand every RTW / homewear / swim / shoes / belts SKU to the full official size list
- Keep OOS sizes visible with inStock=false (PDP shows 품절)
- Belts: label numeric sizes as '{n} cm' + attach cm↔inch size chart
- True one-size (TU/U/OS) stays OS

  python3 scripts/patch-di-rtw-sizes-from-algolia.py
  python3 scripts/patch-di-rtw-sizes-from-algolia.py --dry-run
  python3 scripts/patch-di-rtw-sizes-from-algolia.py --only 693M206A7011_C585
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from di_common import algolia_merch_hits_by_codes, algolia_variant_gbp, gbp_to_krw, slugify  # noqa: E402
from di_size_charts import (  # noqa: E402
    format_di_belt_size,
    is_di_belt_leaf,
    size_chart_for_di_belts,
    size_chart_for_di_mens_rtw,
    size_chart_for_di_mens_shoes,
    size_chart_for_di_womens_rtw,
    size_chart_for_di_womens_shoes,
)

CAT = ROOT / "src/data/di/di-catalog.json"

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

WOMEN_SHOE_LEAVES = {
    "di-women-shoes",
    "di-women-shoes-all",
    "di-women-sneakers",
    "di-women-pumps",
    "di-women-ballerinas",
    "di-women-loafers-flats",
    "di-women-boots",
    "di-women-sandals",
}

MEN_SHOE_LEAVES = {
    "di-men-shoes",
    "di-men-shoes-all",
    "di-men-sneakers",
    "di-men-loafers",
    "di-men-lace-ups",
    "di-men-boots",
    "di-men-sandals-mules",
}

OS_SIZES = {"OS", "ONE SIZE", "TU", "U", "ONESIZE", "ONE-SIZE"}
BELT_LEAVES = {"di-women-belts", "di-men-belts"}
SIZED_LEAVES = WOMEN_LEAVES | MEN_LEAVES | WOMEN_SHOE_LEAVES | MEN_SHOE_LEAVES | BELT_LEAVES


def size_key(size: object) -> str:
    """Compare sizes ignoring 'cm' suffix so '70' and '70 cm' match."""
    s = str(size or "").strip().upper()
    return re.sub(r"\s*CM$", "", s).strip()


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
    # Prefer in-stock prices; fall back to any variant price.
    stocked = [
        int(v["price"])
        for v in variants
        if v.get("inStock") is not False
        and isinstance(v.get("price"), (int, float))
        and v.get("price") > 0
    ]
    if stocked:
        return min(stocked)
    prices = [
        int(v["price"])
        for v in variants
        if isinstance(v.get("price"), (int, float)) and v.get("price") > 0
    ]
    return min(prices) if prices else fallback


def is_clothing(product: dict) -> bool:
    """RTW + shoes + belts — full size runs + OOS chips from Algolia."""
    leaf = str(product.get("subcategory") or "")
    cols = set(product.get("diCollections") or [])
    return leaf in SIZED_LEAVES or bool(cols & SIZED_LEAVES)


def is_belt(product: dict) -> bool:
    leaf = str(product.get("subcategory") or "")
    cols = list(product.get("diCollections") or [])
    return is_di_belt_leaf(leaf, cols)


def is_women(product: dict) -> bool:
    leaf = str(product.get("subcategory") or "")
    cols = set(product.get("diCollections") or [])
    return leaf in WOMEN_LEAVES or leaf in WOMEN_SHOE_LEAVES or bool(
        cols & (WOMEN_LEAVES | WOMEN_SHOE_LEAVES)
    )


def is_shoe(product: dict) -> bool:
    leaf = str(product.get("subcategory") or "")
    cols = set(product.get("diCollections") or [])
    return leaf in WOMEN_SHOE_LEAVES or leaf in MEN_SHOE_LEAVES or bool(
        cols & (WOMEN_SHOE_LEAVES | MEN_SHOE_LEAVES)
    )


def normalize_size(raw: object, *, belt: bool = False) -> str:
    sz = str(raw or "").strip()
    if not sz or sz.startswith("{"):
        return ""
    if sz.upper().startswith("T") and sz[1:].isdigit():
        sz = sz[1:]
    if belt:
        return format_di_belt_size(sz)
    return sz


def extract_size_rows(hit: dict, *, belt: bool = False) -> list[dict]:
    """All sellable size rows from Algolia (including OOS).

    Prefer variantsWithStocks (full run + stock). Never trust `variants` alone as
    the size list when variantsWithStocks exists but is empty — and when only
    `variants` is present, keep it (may be in-stock-only on older index payloads).
    """
    raw = hit.get("variantsWithStocks")
    if not isinstance(raw, list) or not raw:
        raw = hit.get("variants") if isinstance(hit.get("variants"), list) else []
    out: list[dict] = []
    seen: set[str] = set()
    for vv in raw:
        if not isinstance(vv, dict):
            continue
        sz = normalize_size(vv.get("sizeFormatted") or vv.get("size"), belt=belt)
        if not sz or size_key(sz) in OS_SIZES:
            continue
        key = size_key(sz)
        if key in seen:
            continue
        seen.add(key)
        row = dict(vv)
        row["sizeFormatted"] = sz
        out.append(row)
    return out


def would_shrink(product: dict, new_vars: list[dict], *, stock_known: bool) -> bool:
    """Block replacing a full size run with an in-stock-only Algolia `variants` slice."""
    old = [
        size_key(v.get("size"))
        for v in (product.get("variants") or [])
        if str(v.get("size") or "").strip() and size_key(v.get("size")) not in OS_SIZES
    ]
    new = [
        size_key(v.get("size"))
        for v in new_vars
        if str(v.get("size") or "").strip()
    ]
    if len(old) >= 2 and len(new) < len(old) and not stock_known:
        return True
    return False


def size_in_stock(vv: dict, *, stock_known: bool) -> bool:
    """Map Algolia stock → Briq inStock. If no stock payload, keep purchasable."""
    if not stock_known:
        return True
    stock = vv.get("stock") if isinstance(vv.get("stock"), dict) else None
    if stock is not None:
        if "hasStock" in stock:
            return bool(stock.get("hasStock"))
        units = stock.get("stockUnits")
        if isinstance(units, (int, float)):
            return units > 0
        total = str(stock.get("total") or "").lower()
        if total in ("none", "out", "outofstock", "0"):
            return False
        if total in ("low", "medium", "high", "normal"):
            return True
    status = str(vv.get("status") or vv.get("stockLevel") or "").lower()
    if status in ("outofstock", "out_of_stock", "unavailable", "soldout"):
        return False
    return True


def rebuild_variants(
    product: dict, size_rows: list[dict], *, stock_known: bool, belt: bool = False
) -> list[dict]:
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
        sz = normalize_size(vv.get("sizeFormatted") or vv.get("size"), belt=belt)
        if not sz:
            continue
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
                "inStock": size_in_stock(vv, stock_known=stock_known),
                "colorKey": color_key,
                "colorNameKo": color_ko,
                "size": sz,
                "diCollections": collections,
            }
        )
    return sorted(variants, key=lambda v: di_variant_sort_key(v.get("size")))


def fetch_sibling_hit(style_prefix: str) -> dict | None:
    """When a colorway is gone from Algolia, reuse size list from another color of same style."""
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
        rows = extract_size_rows(h)
        if rows:
            scored.append((len(rows), h))
    if not scored:
        return None
    scored.sort(key=lambda x: -x[0])
    return scored[0][1]


def variants_need_update(product: dict, new_vars: list[dict]) -> bool:
    old = product.get("variants") or []
    if len(old) != len(new_vars):
        return True
    old_map = {
        size_key(v.get("size")): bool(v.get("inStock") is not False) for v in old
    }
    new_map = {
        size_key(v.get("size")): bool(v.get("inStock") is not False) for v in new_vars
    }
    # Also refresh when bare numbers need cm labels (belts).
    old_labels = {str(v.get("size") or "").strip() for v in old}
    new_labels = {str(v.get("size") or "").strip() for v in new_vars}
    if old_labels != new_labels:
        return True
    return old_map != new_map


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", default="", help="Comma-separated SKUs")
    ap.add_argument(
        "--os-only",
        action="store_true",
        help="Only rewrite products that are stuck on a single OS variant",
    )
    args = ap.parse_args()

    products = json.loads(CAT.read_text())
    targets = [p for p in products if is_clothing(p)]
    if args.os_only:
        targets = [
            p
            for p in targets
            if (lambda sizes: (not sizes) or (len(sizes) == 1 and sizes[0] in OS_SIZES))(
                [str(v.get("size") or "").strip().upper() for v in (p.get("variants") or []) if v.get("size")]
            )
        ]
    if args.only:
        want = {x.strip() for x in args.only.split(",") if x.strip()}
        targets = [p for p in targets if p.get("sku") in want]

    codes = [p["sku"] for p in targets if p.get("sku")]
    hits: dict[str, dict] = {}
    for i in range(0, len(codes), 15):
        hits.update(algolia_merch_hits_by_codes(codes[i : i + 15]))
        if i and i % 150 == 0:
            print(f"  algolia {min(i + 15, len(codes))}/{len(codes)}", flush=True)
        time.sleep(0.05)
    print(f"  algolia done {len(hits)}/{len(codes)}", flush=True)

    fixed = 0
    unchanged = 0
    kept_os = 0
    missing = 0
    sibling = 0
    oos_marked = 0
    samples: list[str] = []

    by_id = {p["id"]: p for p in products}
    for p in targets:
        sku = p.get("sku") or ""
        hit = hits.get(sku) or {}
        used_sibling = False
        belt = is_belt(p)
        size_rows = extract_size_rows(hit, belt=belt) if hit else []
        stock_known = bool(hit.get("variantsWithStocks"))
        if not size_rows:
            style = sku.split("_")[0] if "_" in sku else sku[:12]
            sib = fetch_sibling_hit(style)
            if sib:
                size_rows = extract_size_rows(sib, belt=belt)
                if size_rows:
                    hit = sib
                    used_sibling = True
                    sibling += 1
                    # Sibling stock is for another colorway — show sizes, keep buyable
                    stock_known = False

        if not size_rows:
            # Genuine one-size on Algolia (TU/U) or missing hit
            if hit and not extract_size_rows(hit, belt=belt):
                kept_os += 1
            else:
                missing += 1
            continue

        variants = rebuild_variants(p, size_rows, stock_known=stock_known, belt=belt)
        if len(variants) < 1:
            kept_os += 1
            continue
        if would_shrink(p, variants, stock_known=stock_known):
            # Keep existing full run; only refresh stock flags when we can map sizes.
            unchanged += 1
            continue
        chart_needed = False
        if belt:
            chart = size_chart_for_di_belts(variants)
            chart_needed = bool(chart) and (p.get("sizeChart") or {}).get("id") != "di-belts"
        elif is_shoe(p):
            chart = (
                size_chart_for_di_womens_shoes()
                if is_women(p)
                else size_chart_for_di_mens_shoes()
            )
        elif is_women(p):
            leaf = str(p.get("subcategory") or "")
            chart = size_chart_for_di_womens_rtw(
                variants, leaf_id=leaf, title_en=p.get("name") or ""
            )
        else:
            leaf = str(p.get("subcategory") or "")
            chart = size_chart_for_di_mens_rtw(
                variants, leaf_id=leaf, title_en=p.get("name") or ""
            )
        if not variants_need_update(p, variants) and not chart_needed:
            unchanged += 1
            continue

        p["variants"] = variants
        p["price"] = list_price_from_variants(variants, int(p.get("price") or 0))
        # Product-level availability: any size in stock
        p["inStock"] = any(v.get("inStock") is not False for v in variants)
        if chart:
            p["sizeChart"] = chart
        elif belt and (p.get("sizeChart") or {}).get("id") == "di-belts":
            p.pop("sizeChart", None)
        by_id[p["id"]] = p
        fixed += 1
        n_oos = sum(1 for v in variants if v.get("inStock") is False)
        oos_marked += n_oos
        if len(samples) < 10:
            tag = "sib" if used_sibling else ("belt" if belt else "ok")
            samples.append(
                f"{sku} [{tag}] "
                + ", ".join(
                    f"{v.get('size')}{'✗' if v.get('inStock') is False else '✓'}"
                    for v in variants[:8]
                )
                + ("…" if len(variants) > 8 else "")
            )

    print(
        f"DONE targets={len(targets)} fixed={fixed} unchanged={unchanged} "
        f"kept_os={kept_os} missing={missing} sibling={sibling} oos_chips={oos_marked}",
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
