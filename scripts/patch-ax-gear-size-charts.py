#!/usr/bin/env python3
"""Attach official Arc'teryx gear size charts onto ax-gear-catalog.{ts,json}.

Safe to re-run. Prefer this over a full rebuild when PDP images are incomplete.

  python3 scripts/patch-ax-gear-size-charts.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ax_gear_size_charts import chart_for_gear_product  # noqa: E402

JSON_PATH = ROOT / "src/data/ax/ax-gear-catalog.json"
TS_PATH = ROOT / "src/data/ax/ax-gear-catalog.ts"
RAW_PATH = ROOT / "src/data/ax/ax-gear-raw.json"
PDP_PATH = ROOT / "src/data/ax/ax-gear-pdp-cache.json"


def sku_of(product: dict) -> str:
    return str(product.get("sku") or "").upper()


def patch_json() -> int:
    products = json.loads(JSON_PATH.read_text())
    raw_by = {
        str(p["id"]).upper(): p
        for p in (json.loads(RAW_PATH.read_text()).get("products") or [])
        if p.get("id")
    }
    pdp_by = json.loads(PDP_PATH.read_text()) if PDP_PATH.exists() else {}
    updated = 0
    for p in products:
        sku = sku_of(p)
        raw = raw_by.get(sku) or {}
        pdp = pdp_by.get(sku) or pdp_by.get(p.get("sku") or "") or {}
        sizes = sorted(
            {
                str(v.get("size"))
                for v in (p.get("variants") or [])
                if v.get("size")
            }
        )
        chart = chart_for_gear_product(
            name=p.get("name") or raw.get("name") or "",
            gender=raw.get("gender") or "",
            sizes=sizes,
            sizing_url=((pdp.get("sizingChart") or {}).get("url")),
        )
        if not chart:
            if p.get("sizeChart"):
                p.pop("sizeChart", None)
                updated += 1
            continue
        if p.get("sizeChart") != chart:
            p["sizeChart"] = chart
            updated += 1
    JSON_PATH.write_text(json.dumps(products, indent=2, ensure_ascii=False) + "\n")
    return updated


def patch_ts() -> int:
    text = TS_PATH.read_text()
    raw_by = {
        str(p["id"]).upper(): p
        for p in (json.loads(RAW_PATH.read_text()).get("products") or [])
        if p.get("id")
    }
    pdp_by = json.loads(PDP_PATH.read_text()) if PDP_PATH.exists() else {}
    products = json.loads(JSON_PATH.read_text())
    by_id = {p["id"]: p for p in products}

    parts = re.split(r'(?=  \{\n    id: ")', text)
    out: list[str] = []
    updated = 0
    for part in parts:
        m = re.match(r'  \{\n    id: "([^"]+)"', part)
        if not m:
            out.append(part)
            continue
        pid = m.group(1)
        prod = by_id.get(pid)
        if not prod:
            out.append(part)
            continue
        sku = sku_of(prod)
        raw = raw_by.get(sku) or {}
        pdp = pdp_by.get(sku) or {}
        sizes = sorted(
            {
                str(v.get("size"))
                for v in (prod.get("variants") or [])
                if v.get("size")
            }
        )
        chart = chart_for_gear_product(
            name=prod.get("name") or "",
            gender=raw.get("gender") or "",
            sizes=sizes,
            sizing_url=((pdp.get("sizingChart") or {}).get("url")),
        )
        # Drop existing sizeChart line(s)
        new_part = re.sub(r"\n    sizeChart: \{.*?\},", "", part, count=1, flags=re.S)
        if chart:
            chart_js = "    sizeChart: " + json.dumps(chart, ensure_ascii=False) + ","
            # Insert before gbpPrice (always present)
            if "    gbpPrice:" in new_part:
                new_part = new_part.replace(
                    "    gbpPrice:",
                    chart_js + "\n    gbpPrice:",
                    1,
                )
            else:
                new_part = new_part.replace(
                    "    variants:",
                    chart_js + "\n    variants:",
                    1,
                )
            updated += 1
        elif "sizeChart:" in part:
            updated += 1
        out.append(new_part)
    TS_PATH.write_text("".join(out))
    return updated


def main() -> None:
    n_json = patch_json()
    n_ts = patch_ts()
    # verify target harness
    products = json.loads(JSON_PATH.read_text())
    sample = next(p for p in products if p["id"] == "axg-x000009656")
    print(
        f"patched json≈{n_json} ts≈{n_ts}; "
        f"Skaha Men's chart={ (sample.get('sizeChart') or {}).get('id') }"
    )
    with_chart = sum(1 for p in products if p.get("sizeChart"))
    print(f"gear products with sizeChart: {with_chart}/{len(products)}")


if __name__ == "__main__":
    main()
