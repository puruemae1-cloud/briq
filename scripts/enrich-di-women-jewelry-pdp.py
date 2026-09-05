#!/usr/bin/env python3
"""Enrich Dior women's fashion jewellery catalog with Korean copy and richer PDP sections."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from di_common import WOMEN_JEWELRY_LEAVES, algolia_merch_hits_by_codes  # noqa: E402
from di_slg_ko import FEATURE_KO  # noqa: E402
from ko_qa import en_ratio, gtx_translate, is_good_korean  # noqa: E402

CAT = ROOT / "src/data/di/di-catalog.json"
PDP_CACHE = ROOT / "src/data/di/di-women-jewelry-pdp-cache.json"
RAW = ROOT / "src/data/di/di-women-jewelry-catalog-raw.json"
CHECKPOINT_EVERY = 25

ACC_LEAVES = {
    "di-women-jewelry",
    *[L["id"] for L in WOMEN_JEWELRY_LEAVES],
}

PHRASE_KO = {
    "Gold finish": "골드 피니시",
    "Silver finish": "실버 피니시",
    "Rose des Vents": "로즈 드 방",
    "Toile de Jouy Sauvage": "투알 드 주이 소바주",
    "Dior Oblique": "디올 오블리크",
    "Diortwin": "디올트윈",
    "Les Liaisons Dangereuses": "레 리에종 당제뢰즈",
}


def _load_rtw_enrich():
    spec = importlib.util.spec_from_file_location(
        "enrich_di_men_rtw_pdp",
        ROOT / "scripts/enrich-di-men-rtw-pdp.py",
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


_rtw = _load_rtw_enrich()
tr = _rtw.tr
parse_characteristics = _rtw.parse_characteristics
material_label = _rtw.material_label
madein_ko = _rtw.madein_ko
load_translate_cache = _rtw.load_translate_cache
save_translate_cache = _rtw.save_translate_cache
warm_feature_cache = _rtw.warm_feature_cache


def tr_line(line: str, cache: dict[str, str], *, live: bool = False) -> str:
    s = line.strip()
    if not s:
        return ""
    if s in FEATURE_KO:
        return FEATURE_KO[s]
    ko = tr(s, cache, live=live)
    if ko and is_good_korean(ko) and en_ratio(ko) <= 0.3:
        return ko
    if s in cache and is_good_korean(cache[s]) and en_ratio(cache[s]) <= 0.3:
        return cache[s]
    if live:
        try:
            gko = gtx_translate(s)
            if gko and is_good_korean(gko) and en_ratio(gko) <= 0.3:
                cache[s] = gko
                return gko
        except Exception:
            pass
    return ko or s


def normalize_ko_text(text: str) -> str:
    out = text or ""
    for src, dst in PHRASE_KO.items():
        out = out.replace(src, dst)
    return out


def polish_features(features: list[str], cache: dict[str, str]) -> list[str]:
    out: list[str] = []
    for line in features:
        if en_ratio(line) > 0.3 or not is_good_korean(line):
            ko = tr_line(line, cache, live=True)
            out.append(normalize_ko_text(ko if ko else line))
        else:
            out.append(normalize_ko_text(line))
    return out


def is_jewelry(product: dict) -> bool:
    cols = set(product.get("diCollections") or [])
    leaf = product.get("subcategory") or ""
    return bool(cols.intersection(ACC_LEAVES) or leaf in ACC_LEAVES)


def story_sections_for_jewelry(
    description_ko: str,
    images: list[str],
    *,
    features_ko: list[str] | None = None,
    material_ko: str = "",
    madein: str = "",
) -> list[dict]:
    if not images:
        return [{"titleKo": "제품 소개", "bodyKo": description_ko, "image": ""}]
    detail_body = (
        " · ".join((features_ko or [])[:8])
        if features_ko
        else "Dior 공식 제품 컷으로 확인하는 하우스 시그니처와 장식 디테일입니다."
    )
    spec_parts: list[str] = []
    if material_ko:
        spec_parts.append(f"주요 소재: {material_ko}")
    if madein:
        spec_parts.append(madein)
    spec_body = ". ".join(spec_parts) if spec_parts else detail_body

    sections = [{"titleKo": "제품 소개", "bodyKo": description_ko, "image": images[0]}]
    if len(images) > 2:
        sections.append(
            {
                "titleKo": "디테일 & 특징",
                "bodyKo": detail_body,
                "image": images[min(2, len(images) - 1)],
            }
        )
    if len(images) > 4:
        sections.append(
            {
                "titleKo": "소재 & 마감",
                "bodyKo": spec_body,
                "image": images[min(4, len(images) - 1)],
            }
        )
    if len(images) > 6:
        sections.append(
            {
                "titleKo": "스타일링",
                "bodyKo": "룩에 우아한 포인트를 더해주는 디올 여성 패션 주얼리입니다.",
                "image": images[min(6, len(images) - 1)],
            }
        )
    return sections


def enrich_product(
    product: dict,
    *,
    pdp: dict,
    hit: dict,
    raw_row: dict,
    cache: dict[str, str],
    live_translate: bool = False,
) -> dict:
    images = [img for img in (product.get("images") or []) if img]
    title_en = (pdp.get("title") or product.get("name") or "").strip()
    subtitle_en = (raw_row.get("subtitle") or hit.get("subtitle") or "").strip()
    desc_en = (pdp.get("description") or "").strip()
    if not desc_en:
        desc_en = ((raw_row.get("details") or {}).get("paragraphs") or [""])[0].strip()

    existing_desc = (product.get("descriptionKo") or "").strip()
    if is_good_korean(existing_desc):
        description_ko = existing_desc
    else:
        parts: list[str] = []
        if subtitle_en:
            sk = tr(subtitle_en, cache, live=live_translate)
            if sk:
                parts.append(sk)
        if desc_en:
            dk = tr(desc_en, cache, live=live_translate)
            if dk:
                parts.append(dk)
        description_ko = "\n\n".join(parts) or existing_desc or title_en
        product["descriptionKo"] = description_ko

    chars_en = parse_characteristics(
        pdp.get("characteristics") or hit.get("characteristics") or ""
    )
    features_ko = [tr_line(line, cache, live=live_translate) for line in chars_en if line]
    features_ko = polish_features(features_ko, cache)
    if features_ko:
        product["featuresKo"] = features_ko

    mat_en = material_label(pdp.get("material") or hit.get("material"))
    mat_ko = normalize_ko_text(tr(mat_en, cache, live=live_translate) if mat_en else "")
    origin = madein_ko(pdp.get("madein") or hit.get("madein"))

    tech: list[dict] = []
    if mat_ko or mat_en:
        tech.append({"labelKo": "소재", "valueKo": mat_ko or mat_en})
    if origin:
        tech.append({"labelKo": "제조국", "valueKo": origin})
    if tech:
        product["techSpecs"] = tech

    product["storySections"] = story_sections_for_jewelry(
        description_ko,
        images,
        features_ko=features_ko,
        material_ko=mat_ko or mat_en,
        madein=f"제조국: {origin}" if origin else "",
    )
    product["descriptionKo"] = normalize_ko_text(product.get("descriptionKo") or "")
    if product.get("featuresKo"):
        product["featuresKo"] = [normalize_ko_text(x) for x in product["featuresKo"]]
    if product.get("storySections"):
        for section in product["storySections"]:
            section["titleKo"] = normalize_ko_text(section.get("titleKo") or "")
            section["bodyKo"] = normalize_ko_text(section.get("bodyKo") or "")
    if product.get("techSpecs"):
        for spec in product["techSpecs"]:
            spec["labelKo"] = normalize_ko_text(spec.get("labelKo") or "")
            spec["valueKo"] = normalize_ko_text(spec.get("valueKo") or "")
    return product


def write_catalog(products: list[dict]) -> None:
    CAT.write_text(json.dumps(products, indent=2, ensure_ascii=False) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="Comma-separated SKUs")
    ap.add_argument("--translate", action="store_true")
    ap.add_argument("--skip-warm", action="store_true")
    args = ap.parse_args()

    products = json.loads(CAT.read_text())
    pdp_cache = json.loads(PDP_CACHE.read_text()) if PDP_CACHE.is_file() else {}
    raw_by = {}
    if RAW.is_file():
        raw_by = {p["id"]: p for p in json.loads(RAW.read_text()).get("products") or []}

    items = [p for p in products if is_jewelry(p)]
    if args.only:
        want = {x.strip() for x in args.only.split(",") if x.strip()}
        items = [p for p in items if p.get("sku") in want]
    if not items:
        print("No women jewelry products in catalog — run scrape + merge first.", flush=True)
        return 0

    codes = [p["sku"] for p in items if p.get("sku")]
    hits: dict[str, dict] = {}
    for i in range(0, len(codes), 15):
        hits.update(algolia_merch_hits_by_codes(codes[i : i + 15]))

    cache = load_translate_cache()
    live = bool(args.translate)
    if not args.skip_warm:
        n = warm_feature_cache(pdp_cache, hits, codes, cache)
        print(f"  warmed {n} characteristic lines", flush=True)

    stats = {"with_features": 0, "with_tech": 0, "sections_gt1": 0}
    for i, p in enumerate(items, 1):
        enrich_product(
            p,
            pdp=pdp_cache.get(p.get("sku") or "") or {},
            hit=hits.get(p.get("sku") or "") or {},
            raw_row=raw_by.get(p.get("sku") or "") or {},
            cache=cache,
            live_translate=live,
        )
        if p.get("featuresKo"):
            stats["with_features"] += 1
        if p.get("techSpecs"):
            stats["with_tech"] += 1
        if len(p.get("storySections") or []) > 1:
            stats["sections_gt1"] += 1
        if i % CHECKPOINT_EVERY == 0:
            print(f"  checkpoint {i}/{len(items)}", flush=True)
            write_catalog(products)
            save_translate_cache(cache)

    write_catalog(products)
    save_translate_cache(cache)
    print(
        f"DONE women_jewelry={len(items)} features={stats['with_features']} "
        f"tech={stats['with_tech']} rich_sections={stats['sections_gt1']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
