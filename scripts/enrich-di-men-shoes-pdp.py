#!/usr/bin/env python3
"""Enrich Dior men's shoes: Algolia size variants, official shoe size chart, rich KO PDP.

  python3 scripts/enrich-di-men-shoes-pdp.py
  python3 scripts/enrich-di-men-shoes-pdp.py --only 3SN279AFQ_H632
  python3 scripts/enrich-di-men-shoes-pdp.py --translate
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from di_common import MEN_SHOES_LEAVES, algolia_merch_hits_by_codes, gbp_to_krw  # noqa: E402
from di_size_charts import size_chart_for_di_mens_shoes  # noqa: E402
from ko_qa import is_good_korean  # noqa: E402

CAT = ROOT / "src/data/di/di-catalog.json"
PDP_CACHE = ROOT / "src/data/di/di-men-shoes-pdp-cache.json"
RAW = ROOT / "src/data/di/di-men-shoes-catalog-raw.json"
CHECKPOINT_EVERY = 25

SHOE_LEAVES = {
    "dior-shoes",
    "di-men-shoes",
    *[L["id"] for L in MEN_SHOES_LEAVES],
}


def _load_rtw():
    spec = importlib.util.spec_from_file_location(
        "enrich_di_men_rtw_pdp",
        ROOT / "scripts/enrich-di-men-rtw-pdp.py",
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


_rtw = _load_rtw()


def is_shoe_product(p: dict) -> bool:
    cols = set(p.get("diCollections") or [])
    leaf = str(p.get("subcategory") or "")
    return bool(cols.intersection(SHOE_LEAVES) or leaf in SHOE_LEAVES)


def pick_leaf(product: dict, raw_row: dict) -> str:
    cols = product.get("diCollections") or []
    for leaf_id in (L["id"] for L in MEN_SHOES_LEAVES if L["id"] != "di-men-shoes-all"):
        if leaf_id in cols:
            return leaf_id
    raw_leaf = (raw_row or {}).get("leafId") or ""
    if raw_leaf in SHOE_LEAVES and raw_leaf != "di-men-shoes-all":
        return raw_leaf
    if "di-men-shoes-all" in cols or product.get("subcategory") == "di-men-shoes-all":
        return "di-men-shoes-all"
    return str(product.get("subcategory") or "di-men-shoes-all")


def enrich_one(
    product: dict,
    *,
    pdp: dict | None,
    hit: dict | None,
    raw_row: dict | None,
    cache: dict[str, str],
    live_translate: bool,
) -> dict:
    pdp = pdp or {}
    hit = hit or {}
    raw_row = raw_row or {}
    collections = list(dict.fromkeys(product.get("diCollections") or []))
    leaf = pick_leaf(product, raw_row)
    images = list(product.get("images") or [])
    # Prefer full remote/gallery from PDP cache when local gallery is thin.
    gal = list(pdp.get("gallery") or [])
    if len(gal) > len(images):
        # keep local paths if already downloaded; else leave images as-is
        pass
    title_en = product.get("name") or pdp.get("title") or ""

    variants = _rtw.rebuild_variants(product, hit, collections=collections)
    product["variants"] = variants
    product["price"] = _rtw.list_price_from_variants(
        variants, int(product.get("price") or 0)
    )

    subtitle_en = (raw_row.get("subtitle") or "").strip()
    desc_en = (pdp.get("description") or "").strip()
    if not desc_en:
        desc_en = re.sub(
            r"\s+",
            " ",
            ((raw_row.get("details") or {}).get("paragraphs") or [""])[0],
        ).strip()

    existing_desc = (product.get("descriptionKo") or "").strip()
    if is_good_korean(existing_desc):
        description_ko = existing_desc
    else:
        parts: list[str] = []
        if subtitle_en:
            sk = _rtw.tr(subtitle_en, cache, live=live_translate)
            if sk:
                parts.append(sk)
        if desc_en:
            dk = _rtw.tr(desc_en, cache, live=live_translate)
            if dk:
                parts.append(dk)
        description_ko = "\n\n".join(parts) or existing_desc or title_en
        product["descriptionKo"] = description_ko

    chars = _rtw.parse_characteristics(
        pdp.get("characteristics") or hit.get("characteristics") or ""
    )
    features_ko: list[str] = []
    for line in chars:
        ko = _rtw.tr(line, cache, live=live_translate)
        if ko:
            features_ko.append(ko)
    if features_ko:
        product["featuresKo"] = features_ko

    mat_en = _rtw.material_label(pdp.get("material") or hit.get("material"))
    if _rtw._is_internal_code(mat_en):
        mat_en = ""
    mat_ko = _rtw.tr(mat_en, cache, live=False) if mat_en else ""
    origin = _rtw.madein_ko(pdp.get("madein") or hit.get("madein"))
    tech: list[dict] = []
    if mat_ko or mat_en:
        tech.append({"labelKo": "소재", "valueKo": mat_ko or mat_en})
    if origin:
        tech.append({"labelKo": "제조국", "valueKo": origin})
    if tech:
        product["techSpecs"] = tech

    product["storySections"] = _rtw.story_sections_for_rtw(
        description_ko,
        images,
        features_ko=features_ko,
        material_ko=mat_ko or mat_en,
        madein=f"제조국: {origin}" if origin else "",
    )

    product["sizeChart"] = size_chart_for_di_mens_shoes()
    product["subcategory"] = leaf
    if "di-men-shoes" not in collections:
        collections.append("di-men-shoes")
    if "dior-shoes" not in collections:
        collections.append("dior-shoes")
    product["diCollections"] = list(dict.fromkeys(collections))
    return product


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--translate", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    catalog = json.loads(CAT.read_text())
    products = catalog if isinstance(catalog, list) else catalog.get("products") or []
    raw = json.loads(RAW.read_text()) if RAW.is_file() else {"products": []}
    raw_by = {p["id"]: p for p in (raw.get("products") or []) if p.get("id")}
    pdp_cache = json.loads(PDP_CACHE.read_text()) if PDP_CACHE.is_file() else {}
    cache = _rtw.load_translate_cache()

    shoes = [p for p in products if is_shoe_product(p)]
    if args.only:
        only = {x.strip() for x in args.only.split(",") if x.strip()}
        shoes = [
            p
            for p in shoes
            if p.get("id") in only
            or p.get("sku") in only
            or any(only & set(str(x) for x in (p.get("diCollections") or [])))
        ]
    if args.limit:
        shoes = shoes[: args.limit]

    print(f"shoes={len(shoes)} translate={args.translate}", flush=True)
    codes = []
    for p in shoes:
        sku = str(p.get("sku") or p.get("id") or "")
        if sku:
            codes.append(sku)
    hits: dict[str, dict] = {}
    for i in range(0, len(codes), 15):
        hits.update(algolia_merch_hits_by_codes(codes[i : i + 15]))
        print(f"  algolia {min(i + 15, len(codes))}/{len(codes)}", flush=True)

    if args.translate:
        warmed = _rtw.warm_feature_cache(pdp_cache, hits, codes, cache)
        print(f"  warmed features={warmed}", flush=True)

    stats = {"variants_rebuilt": 0, "multi_size": 0, "with_features": 0, "with_chart": 0}
    for i, p in enumerate(shoes, 1):
        sku = str(p.get("sku") or p.get("id") or "")
        before = len(p.get("variants") or [])
        enrich_one(
            p,
            pdp=pdp_cache.get(sku),
            hit=hits.get(sku),
            raw_row=raw_by.get(sku) or raw_by.get(str(p.get("id") or "")),
            cache=cache,
            live_translate=args.translate,
        )
        after = len(p.get("variants") or [])
        if after != before:
            stats["variants_rebuilt"] += 1
        if after > 1:
            stats["multi_size"] += 1
        if p.get("featuresKo"):
            stats["with_features"] += 1
        if p.get("sizeChart"):
            stats["with_chart"] += 1
        if i % CHECKPOINT_EVERY == 0:
            CAT.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n")
            _rtw.save_translate_cache(cache)
            print(f"  checkpoint {i}/{len(shoes)}", flush=True)

    CAT.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n")
    _rtw.save_translate_cache(cache)
    print(
        f"DONE shoes={len(shoes)} rebuilt={stats['variants_rebuilt']} "
        f"multi={stats['multi_size']} features={stats['with_features']} "
        f"charts={stats['with_chart']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
