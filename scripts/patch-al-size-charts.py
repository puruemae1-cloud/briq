#!/usr/bin/env python3
"""Give every sized AllSaints clothing PDP the official tabbed size guide (safe to re-run).

  python3 scripts/patch-al-size-charts.py            # use cached official tables
  python3 scripts/patch-al-size-charts.py --refresh  # re-fetch official tables first
  python3 scripts/patch-al-size-charts.py --check    # exit 1 if a sized clothing PDP lacks a chart
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from al_size_charts import _has_sizes, build_chart, load_guides  # noqa: E402

CATALOG = ROOT / "src" / "data" / "al" / "al-catalog.json"
RAW = [ROOT / "src" / "data" / "al" / f"{fam}-catalog-raw.json" for fam in ("al-men-rtw", "al-women-rtw")]


def raw_chart_ids() -> dict[str, str]:
    out: dict[str, str] = {}
    for path in RAW:
        data = json.loads(path.read_text(encoding="utf-8"))
        rows = data.get("products") if isinstance(data, dict) else data
        for r in rows or []:
            rid = str(r.get("id") or r.get("sku") or "").strip()
            if rid:
                out[f"al-{rid.lower()}"] = str(r.get("sizeChartId") or "")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    guides = load_guides(refresh=args.refresh)
    chart_ids = raw_chart_ids()
    products = json.loads(CATALOG.read_text(encoding="utf-8"))
    changed = missing = 0
    for p in products:
        if p.get("category") != "luxury":
            continue
        chart = build_chart(p, chart_ids.get(p["id"], ""), guides)
        if chart is None:
            if _has_sizes(p) and not p.get("sizeChart"):
                missing += 1
            continue
        if chart != p.get("sizeChart"):
            p["sizeChart"] = chart
            changed += 1
    if changed:
        CATALOG.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"AL size charts: updated={changed} sized_without_chart={missing}", flush=True)
    return 1 if args.check and missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
