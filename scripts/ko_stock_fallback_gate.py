#!/usr/bin/env python3
"""Korean QA gate that never blocks stock/size updates.

Drop-in replacement for ``check-catalog-korean.py --brand X --fail`` inside
weekly pipelines. When the rebuilt catalogue carries English copy (usually
machine translation rate limited mid-run):

  1. merge onto the committed catalogue with the stock-only fallback
     (existing rows keep committed Korean copy but take new stock, sizes and
     prices; brand-new untranslated rows are held back for the next sync)
  2. fail only if problems remain that the committed catalogue did not have

Usage: python3 scripts/ko_stock_fallback_gate.py --brand di
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ko_qa import CATALOG_PATHS, MAX_KO_EN_RATIO, find_hybrid_fields, load_products  # noqa: E402
from stock_only_fallback import apply_fallback, committed_catalog  # noqa: E402


def bad_fields(products: list[dict], max_ratio: float) -> set[tuple[str, str]]:
    return {(pid, field) for pid, field, _r, _s in find_hybrid_fields(products, max_ratio=max_ratio)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand", required=True)
    ap.add_argument("--max-ratio", type=float, default=MAX_KO_EN_RATIO)
    args = ap.parse_args()

    failed = False
    for path in CATALOG_PATHS[args.brand]:
        if path.suffix != ".json" or not path.is_file():
            continue
        current = load_products(path)
        bad = bad_fields(current, args.max_ratio)
        if not bad:
            print(f"{args.brand}: Korean QA ok ({path.name})", flush=True)
            continue
        print(
            f"{args.brand}: {len(bad)} untranslated field(s) in {path.name} — "
            "applying stock-only fallback",
            flush=True,
        )
        apply_fallback(path, lambda p: not find_hybrid_fields([p], max_ratio=args.max_ratio))
        rel = str(path.relative_to(ROOT))
        try:
            baseline = bad_fields(committed_catalog(rel), args.max_ratio)
        except Exception:  # noqa: BLE001 — first commit of this catalogue
            baseline = set()
        extra = bad_fields(json.loads(path.read_text()), args.max_ratio) - baseline
        if extra:
            failed = True
            print(f"Korean QA regressions after fallback ({len(extra)}):", flush=True)
            for pid, field in sorted(extra)[:30]:
                print(f"  {pid} {field}", flush=True)
        else:
            print(f"{args.brand}: remaining issues already in the committed catalogue", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
