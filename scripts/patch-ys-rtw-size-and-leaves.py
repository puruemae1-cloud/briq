#!/usr/bin/env python3
"""Fast patch: YS RTW size fields/charts + women subcategory collections."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ys_size_charts import parse_ys_size_token, size_chart_for_rtw  # noqa: E402
from ysl_common import load_json, save_json  # noqa: E402

CATALOG = ROOT / "src/data/ys/ys-catalog.json"
RAW_WOMEN = ROOT / "src/data/ys/ys-women-rtw-catalog-raw.json"
RAW_MEN = ROOT / "src/data/ys/ys-men-rtw-catalog-raw.json"


def _sizes_from_variants(variants: list[dict]) -> list[dict]:
    out = []
    for v in variants or []:
        label = str(v.get("size") or v.get("nameKo") or v.get("name") or "")
        if not label:
            continue
        ysl, gb = parse_ys_size_token(label)
        out.append(
            {
                "value": ysl or label,
                "displayValue": f"YSL {ysl} / GB {gb}" if ysl and gb else label,
            }
        )
    return out


def _sizes_from_raw(raw: dict | None) -> list[dict]:
    if not raw:
        return []
    return list(raw.get("sizes") or [])


def patch_product(p: dict, raw: dict | None) -> bool:
    changed = False
    if p.get("category") != "luxury":
        # Still merge collections for women RTW hubs if present.
        pass
    else:
        variants = p.get("variants") or []
        for v in variants:
            if v.get("size"):
                continue
            label = str(v.get("nameKo") or v.get("name") or "")
            if label:
                v["size"] = label
                changed = True

        sizes = _sizes_from_raw(raw) or _sizes_from_variants(variants)
        mens = any(
            c in {"ys-men", "ys-men-rtw-all"} or str(c).startswith("ys-men-")
            for c in (p.get("ysCollections") or [])
        ) or str(p.get("subcategory") or "").startswith("ys-men")
        leaf_hint = ""
        if raw and raw.get("leafId"):
            leaf_hint = str(raw["leafId"])
        else:
            for c in reversed(p.get("ysCollections") or []):
                cs = str(c)
                if cs.startswith("ys-") and cs not in {
                    "ys-men",
                    "ys-women",
                    "saint-laurent",
                }:
                    leaf_hint = cs
                    break
        chart = size_chart_for_rtw(sizes, mens=mens, leaf_hint=leaf_hint)
        if chart and chart != p.get("sizeChart"):
            p["sizeChart"] = chart
            changed = True

    if raw:
        cols = list(
            dict.fromkeys(
                [*(p.get("ysCollections") or []), *(raw.get("collections") or [])]
            )
        )
        if cols != (p.get("ysCollections") or []):
            p["ysCollections"] = cols
            p["subcategory"] = cols[-1] if cols else p.get("subcategory")
            for v in p.get("variants") or []:
                v["ysCollections"] = cols
            changed = True
    return changed


def main() -> int:
    catalog = load_json(CATALOG, [])
    women_raw = {
        str(p["id"]): p
        for p in (load_json(RAW_WOMEN, {}).get("products") or [])
        if p.get("id")
    }
    men_raw = {
        str(p["id"]): p
        for p in (load_json(RAW_MEN, {}).get("products") or [])
        if p.get("id")
    }

    changed_n = 0
    luxury_n = 0
    with_size = 0
    with_chart = 0
    for p in catalog:
        pid = str(p.get("id") or "").removeprefix("ys-").upper()
        # raw ids are mixed case
        raw = women_raw.get(pid) or women_raw.get(pid.lower())
        if not raw:
            # try exact keys
            for k, v in women_raw.items():
                if k.upper() == pid:
                    raw = v
                    break
        if not raw:
            for k, v in men_raw.items():
                if k.upper() == pid:
                    raw = v
                    break
        if p.get("category") == "luxury":
            luxury_n += 1
        if patch_product(p, raw):
            changed_n += 1
        if p.get("category") == "luxury":
            if any(v.get("size") for v in (p.get("variants") or [])):
                with_size += 1
            if p.get("sizeChart"):
                with_chart += 1

    save_json(CATALOG, catalog)
    # verify sample
    sample = next(x for x in catalog if x.get("id") == "ys-631980y7b734141")
    print(
        json.dumps(
            {
                "changed": changed_n,
                "luxury": luxury_n,
                "with_size": with_size,
                "with_chart": with_chart,
                "sample_size": sample["variants"][0].get("size"),
                "sample_chart_title": (sample.get("sizeChart") or {}).get("titleKo"),
                "sample_headers": (sample.get("sizeChart") or {}).get("headers"),
                "sample_cols": sample.get("ysCollections"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
