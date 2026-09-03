#!/usr/bin/env python3
"""Enrich Dior women's SLG catalog: rich PDP copy, featuresKo, techSpecs.

One Size only — no size charts. Checkpoints every 25 SKUs.

  python3 scripts/enrich-di-women-slg-pdp.py
  python3 scripts/enrich-di-women-slg-pdp.py --only 2ESCH135FGP_H140
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

from di_common import algolia_merch_hits_by_codes  # noqa: E402
from di_slg_ko import FEATURE_KO, MATERIAL_KO  # noqa: E402
from ko_qa import en_ratio, gtx_translate, is_good_korean  # noqa: E402

CAT = ROOT / "src/data/di/di-catalog.json"
PDP_CACHE = ROOT / "src/data/di/di-women-slg-pdp-cache.json"
RAW = ROOT / "src/data/di/di-women-slg-catalog-raw.json"
CHECKPOINT_EVERY = 25

SLG_LEAVES = {
    "di-women-slg",
    "di-women-slg-all",
    "di-women-card-holders",
    "di-women-wallets",
    "di-women-pouches",
    "di-women-slg-tech",
}

_DIM_RE = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(?:x|\×)\s*(\d+(?:[.,]\d+)?)"
    r"(?:\s*(?:x|\×)\s*(\d+(?:[.,]\d+)?))?\s*cm",
    re.I,
)


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


def tr_slg(line: str, cache: dict[str, str], *, live: bool = False) -> str:
    s = line.strip()
    if not s:
        return ""
    if s in FEATURE_KO:
        return FEATURE_KO[s]
    ko = tr(s, cache, live=live)
    if ko and (is_good_korean(ko) and en_ratio(ko) <= 0.3):
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


def polish_features(features: list[str], cache: dict[str, str]) -> list[str]:
    out: list[str] = []
    for line in features:
        if en_ratio(line) > 0.3 or not is_good_korean(line):
            ko = tr_slg(line, cache, live=True)
            out.append(ko if ko else line)
        else:
            out.append(line)
    return out


def is_slg(product: dict) -> bool:
    cols = set(product.get("diCollections") or [])
    leaf = product.get("subcategory") or ""
    return bool(cols.intersection(SLG_LEAVES) or leaf in SLG_LEAVES)


def extract_dimensions(chars: list[str]) -> str:
    for line in chars:
        m = _DIM_RE.search(line.replace(",", "."))
        if m:
            parts = [m.group(1), m.group(2)]
            if m.group(3):
                parts.append(m.group(3))
            return " × ".join(p.replace(".", ".") for p in parts) + " cm"
        if "dimension" in line.lower() or "size" in line.lower():
            ko = tr(line, {}, live=False)
            if ko and is_good_korean(ko):
                return ko
    return ""


def story_sections_for_slg(
    description_ko: str,
    images: list[str],
    *,
    features_ko: list[str] | None = None,
    material_ko: str = "",
    madein: str = "",
    dims_ko: str = "",
) -> list[dict]:
    if not images:
        return [{"titleKo": "제품 소개", "bodyKo": description_ko, "image": ""}]
    detail_body = (
        " · ".join((features_ko or [])[:8])
        if features_ko
        else (
            "Dior 공식 제품 컷으로 확인하는 실루엣·소재·"
            "시그니처 장식 디테일입니다."
        )
    )
    spec_parts: list[str] = []
    if material_ko:
        spec_parts.append(f"주요 소재: {material_ko}")
    if dims_ko:
        spec_parts.append(f"크기: {dims_ko}")
    if madein:
        spec_parts.append(madein)
    spec_body = ". ".join(spec_parts) if spec_parts else detail_body

    sections: list[dict] = [
        {"titleKo": "제품 소개", "bodyKo": description_ko, "image": images[0]},
    ]
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
                "titleKo": "소재 & 스펙",
                "bodyKo": spec_body,
                "image": images[min(4, len(images) - 1)],
            }
        )
    if len(images) > 6:
        sections.append(
            {
                "titleKo": "스타일링",
                "bodyKo": (
                    "데일리부터 트래블까지 다양한 룩에 어울리는 "
                    "디올 여성 스몰 레더 굿즈 실루엣입니다."
                ),
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
    sku = product.get("sku") or ""
    title_en = (pdp.get("title") or product.get("name") or "").strip()
    subtitle_en = (raw_row.get("subtitle") or hit.get("subtitle") or "").strip()
    desc_en = clean_desc = (pdp.get("description") or "").strip()
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
    features_ko: list[str] = []
    for line in chars_en:
        ko = tr_slg(line, cache, live=live_translate)
        if ko:
            features_ko.append(ko)
    features_ko = polish_features(features_ko, cache)
    if features_ko:
        product["featuresKo"] = features_ko

    mat_en = material_label(pdp.get("material") or hit.get("material"))
    mat_ko = ""
    if mat_en:
        mat_ko = MATERIAL_KO.get(mat_en) or MATERIAL_KO.get(mat_en.lower()) or ""
        if not mat_ko:
            # title-case lookup
            for k, v in MATERIAL_KO.items():
                if k.lower() == mat_en.lower():
                    mat_ko = v
                    break
        if not mat_ko:
            mat_ko = tr(mat_en, cache, live=live_translate) if mat_en else ""
        if mat_ko and (en_ratio(mat_ko) > 0.3 or not is_good_korean(mat_ko)):
            # last resort curated / leave empty rather than EN in story
            mat_ko = MATERIAL_KO.get(mat_en, mat_ko if is_good_korean(mat_ko) else mat_en)
    origin = madein_ko(pdp.get("madein") or hit.get("madein"))
    dims_ko = extract_dimensions(chars_en)

    tech: list[dict] = []
    if mat_ko and en_ratio(mat_ko) <= 0.3:
        tech.append({"labelKo": "소재", "valueKo": mat_ko})
    elif mat_en:
        # still store curated if possible
        fallback = MATERIAL_KO.get(mat_en) or next(
            (v for k, v in MATERIAL_KO.items() if k.lower() == mat_en.lower()),
            "",
        )
        if fallback:
            tech.append({"labelKo": "소재", "valueKo": fallback})
            mat_ko = fallback
    if dims_ko:
        tech.append({"labelKo": "크기", "valueKo": dims_ko})
    if origin:
        tech.append({"labelKo": "제조국", "valueKo": origin})
    if tech:
        product["techSpecs"] = tech

    product["storySections"] = story_sections_for_slg(
        description_ko,
        images,
        features_ko=features_ko,
        material_ko=mat_ko if mat_ko and en_ratio(mat_ko) <= 0.3 else "",
        madein=f"제조국: {origin}" if origin else "",
        dims_ko=dims_ko,
    )
    return product


def write_catalog(products: list[dict]) -> None:
    CAT.write_text(json.dumps(products, indent=2, ensure_ascii=False) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="Comma-separated SKUs")
    ap.add_argument("--translate", action="store_true")
    ap.add_argument("--skip-warm", action="store_true")
    args = ap.parse_args()

    if not CAT.is_file():
        print("ERROR: di-catalog.json missing", flush=True)
        return 1

    products = json.loads(CAT.read_text())
    pdp_cache = json.loads(PDP_CACHE.read_text()) if PDP_CACHE.is_file() else {}
    raw_by = {}
    if RAW.is_file():
        raw_by = {
            p["id"]: p for p in json.loads(RAW.read_text()).get("products") or []
        }

    slg = [p for p in products if is_slg(p)]
    if args.only:
        want = {x.strip() for x in args.only.split(",") if x.strip()}
        slg = [p for p in slg if p.get("sku") in want]

    if not slg:
        print("No SLG products in catalog — run scrape + merge first.", flush=True)
        return 0

    codes = [p["sku"] for p in slg if p.get("sku")]
    hits: dict[str, dict] = {}
    for i in range(0, len(codes), 15):
        hits.update(algolia_merch_hits_by_codes(codes[i : i + 15]))

    cache = load_translate_cache()
    live = bool(args.translate)
    if not args.skip_warm:
        n = warm_feature_cache(pdp_cache, hits, codes, cache)
        print(f"  warmed {n} characteristic lines", flush=True)

    stats = {"with_features": 0, "with_tech": 0, "sections_gt1": 0}

    for i, p in enumerate(slg, 1):
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
            print(f"  checkpoint {i}/{len(slg)}", flush=True)
            write_catalog(products)
            save_translate_cache(cache)

    write_catalog(products)
    save_translate_cache(cache)
    print(
        f"DONE slg={len(slg)} features={stats['with_features']} "
        f"tech={stats['with_tech']} rich_sections={stats['sections_gt1']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
