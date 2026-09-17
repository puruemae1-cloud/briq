#!/usr/bin/env python3
"""Fail if VW clothing still collapses to OS-only or lacks size charts."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAT = ROOT / "src/data/vw/vw-catalog.json"


def is_rtw(p: dict) -> bool:
    cols = " ".join(p.get("vwCollections") or p.get("collections") or []).lower()
    leaf = str(p.get("subcategory") or "").lower()
    blob = cols + " " + leaf
    return any(
        x in blob
        for x in (
            "rtw",
            "clothing",
            "coats",
            "jackets",
            "dresses",
            "knitwear",
            "shirts",
            "trousers",
            "skirts",
            "corset",
            "sweat",
            "t-shirt",
            "tshirt",
        )
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fail", action="store_true")
    ap.add_argument("--max-os-only", type=int, default=15)
    ap.add_argument("--min-chart-ratio", type=float, default=0.5)
    args = ap.parse_args()

    prods = json.loads(CAT.read_text())
    if isinstance(prods, dict):
        prods = prods.get("products") or []
    rtw = [p for p in prods if is_rtw(p)]
    os_only = []
    with_chart = 0
    for p in rtw:
        sizes = [(v.get("size") or v.get("name") or "") for v in (p.get("variants") or [])]
        sizes = [s for s in sizes if s]
        if sizes == ["OS"] or (len(set(sizes)) == 1 and sizes and sizes[0].upper() in {"OS", "ONE SIZE"}):
            os_only.append(p.get("id"))
        if p.get("sizeChart"):
            with_chart += 1
    ratio = (with_chart / len(rtw)) if rtw else 1.0
    print(
        f"vw_rtw={len(rtw)} os_only={len(os_only)} with_chart={with_chart} chart_ratio={ratio:.2f}"
    )
    if os_only[:8]:
        print("sample_os", os_only[:8])
    bad = len(os_only) > args.max_os_only or ratio < args.min_chart_ratio
    if bad and args.fail:
        print("ERROR VW RTW size/chart guard failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
