#!/usr/bin/env python3
"""Make every Bottega Veneta Korean title unique.

Same name, other colour → colour suffix (조디 → 조디 블랙). Same name and colour →
the real difference from the official copy (아스테어 로퍼 블랙 (여성 · 오픈백)).
Runs after the KO repair pass in the weekly sync, which can rewrite nameKo.

  python3 scripts/fix-bv-name-colors.py          # fix bv-catalog.json in place
  python3 scripts/fix-bv-name-colors.py --check  # exit 1 if any title is still shared
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from bv_colors import duplicate_name_groups, normalize_bv_names  # noqa: E402
from bv_common import load_json, save_json  # noqa: E402
from bv_config import OUT_JSON  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only; fail on leftovers")
    args = ap.parse_args()

    products = load_json(OUT_JSON, [])
    if not isinstance(products, list) or not products:
        print(f"no products in {OUT_JSON}", flush=True)
        return 1
    if not args.check:
        stats = normalize_bv_names(products)
        save_json(OUT_JSON, products)
        print(
            f"bv names: recolored={stats['recolored']} renamed={stats['renamed']} "
            f"unknown_colors={len(stats['unknown'])} {stats['unknown'][:20]}",
            flush=True,
        )
    left = duplicate_name_groups(products)
    print(f"bv shared titles left: {len(left)}", flush=True)
    for name, n in left[:20]:
        print(f"  {name} ×{n}", flush=True)
    return 1 if left and args.check else 0


if __name__ == "__main__":
    raise SystemExit(main())
