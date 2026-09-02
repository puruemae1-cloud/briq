#!/usr/bin/env python3
"""Fix hybrid EN/KO in Dior catalog — translate failing featuresKo & rebuild story sections.

  python3 scripts/fix-di-ko-hybrid.py
  python3 scripts/fix-di-ko-hybrid.py --scope acc-shoes
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from di_slg_ko import FEATURE_KO, MATERIAL_KO, MADEIN_KO  # noqa: E402
from ko_qa import (  # noqa: E402
    check_brand,
    find_hybrid_fields,
    is_good_korean,
    load_products,
    translate_en_to_ko,
)

CAT = ROOT / "src/data/di/di-catalog.json"
CACHE_PATH = ROOT / "src/data/di/di-translate-cache.json"
CHECKPOINT = 40

ACC_COLS = {
    "di-men-accessories", "di-men-acc-all", "di-men-sunglasses", "di-men-belts",
    "di-men-ties-pocket-squares", "di-men-scarves", "di-men-hats-gloves", "di-men-socks",
    "di-men-fashion-jewelry", "di-men-silver-jewelry", "di-men-key-rings",
    "di-men-charm-jewelry", "di-men-lifestyle", "di-men-acc-tech", "di-men-pet-accessories",
    "di-men-slg", "di-men-slg-all", "di-men-card-holders", "di-men-compact-wallets",
    "di-men-long-wallets", "di-men-pouches", "di-men-tech-accessories",
}
SHOE_COLS = {
    "dior-shoes", "di-men-shoes", "di-men-shoes-all", "di-men-sneakers",
    "di-men-sandals-mules", "di-men-loafers", "di-men-lace-ups", "di-men-boots",
}


def load_cache() -> dict[str, str]:
    if CACHE_PATH.is_file():
        return json.loads(CACHE_PATH.read_text())
    return {}


def save_cache(cache: dict[str, str]) -> None:
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n")


def in_scope(p: dict, scope: str) -> bool:
    cols = set(p.get("diCollections") or [])
    sub = str(p.get("subcategory") or "")
    if scope == "all":
        return True
    sc = ACC_COLS | SHOE_COLS
    return bool(cols.intersection(sc) or sub in sc)


def tr_line(line: str, cache: dict[str, str]) -> str:
    s = re.sub(r"\s+", " ", (line or "").strip())
    if not s or is_good_korean(s):
        return s
    if s in FEATURE_KO:
        return FEATURE_KO[s]
    ko = translate_en_to_ko(s, cache)
    if ko and is_good_korean(ko):
        return ko
    return s


def load_acc_enrich():
    spec = importlib.util.spec_from_file_location(
        "enrich_di_men_accessories_pdp",
        ROOT / "scripts/enrich-di-men-accessories-pdp.py",
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


_acc = load_acc_enrich()


def rebuild_stories(p: dict) -> None:
    images = list(p.get("images") or [])
    desc = (p.get("descriptionKo") or "").strip()
    feats = list(p.get("featuresKo") or [])
    tech = p.get("techSpecs") or []
    mat = ""
    madein = ""
    dims = ""
    for row in tech:
        if not isinstance(row, dict):
            continue
        label = str(row.get("labelKo") or "")
        val = str(row.get("valueKo") or "")
        if label == "소재":
            mat = val
        elif label == "제조국":
            madein = f"제조국: {val}" if val else ""
        elif label == "크기":
            dims = val
    cols = set(p.get("diCollections") or [])
    if cols.intersection(SHOE_COLS):
        from enrich_di_men_rtw_pdp import story_sections_for_rtw  # noqa: WPS433

        p["storySections"] = story_sections_for_rtw(
            desc, images, features_ko=feats, material_ko=mat, madein=madein,
        )
    else:
        p["storySections"] = _acc.story_sections_for_slg(
            desc, images, features_ko=feats, material_ko=mat, madein=madein, dims_ko=dims,
        )


def polish_tech(p: dict) -> bool:
    changed = False
    for row in p.get("techSpecs") or []:
        if not isinstance(row, dict):
            continue
        val = str(row.get("valueKo") or "").strip()
        if val in MATERIAL_KO:
            row["valueKo"] = MATERIAL_KO[val]
            changed = True
        elif val in MADEIN_KO:
            row["valueKo"] = MADEIN_KO[val]
            changed = True
    return changed


def apply_glossary(p: dict) -> bool:
    changed = False
    feats = p.get("featuresKo") or []
    new_feats = []
    for feat in feats:
        if isinstance(feat, str) and feat in FEATURE_KO:
            new_feats.append(FEATURE_KO[feat])
            changed = True
        else:
            new_feats.append(feat)
    if changed:
        p["featuresKo"] = new_feats
    return changed


def fix_product(p: dict, bad_fields: set[str], cache: dict[str, str]) -> int:
    fixed = 0
    gloss_changed = apply_glossary(p)
    tech_changed = polish_tech(p)
    if gloss_changed or tech_changed:
        fixed += 1
    if any(f == "descriptionKo" for f in bad_fields):
        old = (p.get("descriptionKo") or "").strip()
        new = tr_line(old, cache)
        if new != old:
            p["descriptionKo"] = new
            fixed += 1

    feats = list(p.get("featuresKo") or [])
    new_feats: list[str] = []
    feat_changed = False
    for feat in feats:
        if not isinstance(feat, str):
            new_feats.append(str(feat))
            continue
        if "featuresKo" in bad_fields and not is_good_korean(feat):
            ko = tr_line(feat, cache)
            new_feats.append(ko)
            if ko != feat:
                feat_changed = True
                fixed += 1
        else:
            new_feats.append(feat)
    if feat_changed:
        p["featuresKo"] = new_feats

    sections = list(p.get("storySections") or [])
    sec_changed = False
    for i, sec in enumerate(sections):
        if not isinstance(sec, dict):
            continue
        key = f"story[{i}].bodyKo"
        if key not in bad_fields:
            continue
        old = str(sec.get("bodyKo") or "").strip()
        if not old:
            continue
        # Detail sections built from features — rebuild wholesale below.
        if sec.get("titleKo") in ("디테일 & 특징", "소재 & 스펙", "디테일"):
            sec_changed = True
            continue
        new = tr_line(old, cache)
        if new != old:
            sec["bodyKo"] = new
            sec_changed = True
            fixed += 1
    if feat_changed or sec_changed or gloss_changed or tech_changed or any(
        f.startswith("story[") for f in bad_fields
    ):
        rebuild_stories(p)
        fixed += 1
    return fixed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", choices=("all", "acc-shoes"), default="all")
    args = ap.parse_args()

    products = load_products(CAT)
    by_id = {str(p.get("id")): p for p in products if p.get("id")}
    bad = check_brand("di")
    cache = load_cache()

    by_pid: dict[str, set[str]] = {}
    for _brand, pid, field, _ratio, _snippet in bad:
        p = by_id.get(pid)
        if not p or not in_scope(p, args.scope):
            continue
        by_pid.setdefault(pid, set()).add(field)

    # Also polish acc/shoes products for glossary + tech even if not in bad list.
    if args.scope == "acc-shoes":
        for p in products:
            if in_scope(p, args.scope):
                by_pid.setdefault(str(p.get("id")), set())

    print(f"fix targets: {len(by_pid)} products (scope={args.scope})", flush=True)
    total_fixed = 0
    for i, (pid, fields) in enumerate(sorted(by_pid.items()), 1):
        n = fix_product(by_id[pid], fields, cache)
        total_fixed += n
        if i % CHECKPOINT == 0:
            CAT.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n")
            save_cache(cache)
            print(f"  checkpoint {i}/{len(by_pid)} fixed_ops={total_fixed}", flush=True)
        time.sleep(0.05)

    CAT.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n")
    save_cache(cache)

    remaining = check_brand("di")
    if args.scope == "acc-shoes":
        remaining = [
            b for b in remaining if in_scope(by_id.get(b[1], {}), "acc-shoes")
        ]
    print(f"DONE fixed_ops={total_fixed} remaining_bad={len(remaining)}", flush=True)
    for row in remaining[:15]:
        print(f"  {row[1]} {row[2]} en_ratio={row[3]:.2f} {row[4][:80]}", flush=True)
    return 0 if not remaining else 1


if __name__ == "__main__":
    raise SystemExit(main())
