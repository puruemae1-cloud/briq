#!/usr/bin/env python3
"""Fail when AllSaints PDP copy is still English."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from ko_qa import en_ratio, is_good_korean  # noqa: E402

CATALOG = ROOT / "src/data/al/al-catalog.json"
MAX_EN_RATIO = 0.40


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fail", action="store_true")
    ap.add_argument("--max-bad", type=int, default=0)
    ap.add_argument("--category", default="all")
    args = ap.parse_args()
    products = json.loads(CATALOG.read_text(encoding="utf-8")) if CATALOG.exists() else []
    if args.category != "all":
        cats = {c.strip() for c in args.category.split(",") if c.strip()}
        products = [p for p in products if p.get("category") in cats]
    bad: list[tuple[str, str, float]] = []
    for p in products:
        pid = str(p.get("id") or "")
        fields = [("descriptionKo", p.get("descriptionKo"))]
        for i, sec in enumerate(p.get("storySections") or []):
            if str(sec.get("titleKo") or "") == "스타일링":
                continue
            fields.append((f"story[{i}].bodyKo", sec.get("bodyKo")))
        for i, feat in enumerate(p.get("featuresKo") or []):
            fields.append((f"featuresKo[{i}]", feat))
        for i, spec in enumerate(p.get("techSpecs") or []):
            if (spec or {}).get("labelKo") == "제품 코드":
                continue
            fields.append((f"techSpecs[{i}].valueKo", (spec or {}).get("valueKo")))
        for field, val in fields:
            s = str(val or "").strip()
            if not s:
                continue
            if is_good_korean(s, max_ratio=MAX_EN_RATIO):
                continue
            bad.append((pid, field, en_ratio(s)))
    print(f"AL Korean QA — products={len(products)} bad_fields={len(bad)}", flush=True)
    for pid, field, ratio in bad[:25]:
        print(f"  {pid} {field} en_ratio={ratio:.2f}", flush=True)
    if args.fail and len(bad) > args.max_bad:
        print(f"FAIL AL Korean bad_fields={len(bad)} > max={args.max_bad}", flush=True)
        return 1
    print(f"OK AL Korean — badFields={len(bad)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
