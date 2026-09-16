#!/usr/bin/env python3
"""Fail when Vivienne Westwood PDP copy is still English.

Weekly sync must not ship EN leftovers in descriptionKo / story / features.
Covers accessories, bags, luxury (RTW), shoes, and watches.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ko_qa import en_ratio, is_good_korean  # noqa: E402

CATALOG = ROOT / "src/data/vw/vw-catalog.json"
MAX_EN_RATIO = 0.40
MAX_BAD = 0
VW_SHOP_CATEGORIES = ("accessories", "bags", "luxury", "shoes", "watches")


def parse_categories(raw: str) -> list[str]:
    s = (raw or "").strip().lower()
    if not s or s == "all":
        return list(VW_SHOP_CATEGORIES)
    cats = [c.strip() for c in s.split(",") if c.strip()]
    unknown = [c for c in cats if c not in VW_SHOP_CATEGORIES]
    if unknown:
        raise SystemExit(
            f"unknown category {unknown!r}; expected one of {list(VW_SHOP_CATEGORIES)} or all"
        )
    return cats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--category",
        default="all",
        help="One category, comma-separated list, or 'all' (default)",
    )
    ap.add_argument("--fail", action="store_true")
    ap.add_argument("--max-bad", type=int, default=MAX_BAD)
    args = ap.parse_args()

    categories = set(parse_categories(args.category))
    products = json.loads(CATALOG.read_text(encoding="utf-8"))
    scoped = [p for p in products if p.get("category") in categories]
    bad: list[tuple[str, str, float]] = []
    for p in scoped:
        pid = str(p.get("id") or "")
        fields = [("descriptionKo", p.get("descriptionKo"))]
        for i, sec in enumerate(p.get("storySections") or []):
            title = str(sec.get("titleKo") or "")
            if title == "스타일링":
                continue  # curated Korean blurb
            fields.append((f"story[{i}].bodyKo", sec.get("bodyKo")))
        for i, feat in enumerate(p.get("featuresKo") or []):
            fields.append((f"featuresKo[{i}]", feat))
        for i, spec in enumerate(p.get("techSpecs") or []):
            fields.append((f"techSpecs[{i}].valueKo", (spec or {}).get("valueKo")))
        for field, val in fields:
            s = str(val or "").strip()
            if not s:
                continue
            if is_good_korean(s, max_ratio=MAX_EN_RATIO):
                continue
            bad.append((pid, field, en_ratio(s)))

    print(
        f"VW Korean QA — categories={','.join(sorted(categories))} "
        f"products={len(scoped)} bad_fields={len(bad)}",
        flush=True,
    )
    for pid, field, ratio in bad[:25]:
        print(f"  {pid} {field} en_ratio={ratio:.2f}", flush=True)
    if len(bad) > 25:
        print(f"  … +{len(bad) - 25} more", flush=True)

    bad_desc_pids = {pid for pid, field, _ in bad if field == "descriptionKo"}
    if len(bad_desc_pids) > args.max_bad:
        print(
            f"ERROR: {len(bad_desc_pids)} products still have English descriptionKo "
            f"(max {args.max_bad}). Run: python3 scripts/retranslate-vw-ko.py --category all",
            flush=True,
        )
        if args.fail:
            return 1
        return 0

    print(
        f"OK VW Korean — badDesc={len(bad_desc_pids)} badFields={len(bad)}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
