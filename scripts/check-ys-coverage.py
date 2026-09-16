#!/usr/bin/env python3
"""Guard Saint Laurent coverage vs official ysl.com leaf union.

Official target = unique SKUs across View All + every subcategory PLP.

Usage:
  python3 scripts/check-ys-coverage.py
  python3 scripts/check-ys-coverage.py --fail
  python3 scripts/check-ys-coverage.py --fail --family ys-men-bags
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ysl_common import iter_plp_products  # noqa: E402
from ysl_config import RAW_DIR, YS_FAMILY_SCRAPERS  # noqa: E402


def official_union_count(leaves: list[dict]) -> tuple[int, int]:
    """Return (union_count, view_all_count)."""
    ids: set[str] = set()
    view_all = 0
    for leaf in leaves:
        rows = iter_plp_products(leaf["slug"], require_full=True)
        ids |= {str(p.get("id") or "") for p in rows if p.get("id")}
        lid = str(leaf.get("id") or "")
        slug = str(leaf.get("slug") or "")
        if lid.endswith("-all") or "/all-" in f"/{slug}":
            view_all = len(rows)
    return len(ids), view_all


def raw_count(path: Path) -> int:
    if not path.is_file():
        return 0
    return len((json.loads(path.read_text(encoding="utf-8")).get("products") or []))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fail", action="store_true")
    ap.add_argument("--family", default="")
    ap.add_argument("--skip-live", action="store_true")
    args = ap.parse_args()

    families = [args.family] if args.family else list(YS_FAMILY_SCRAPERS.keys())
    bad = 0
    print(f"{'family':28} {'view_all':>8} {'union':>6} {'raw':>6} {'status'}")
    for fam in families:
        cfg = YS_FAMILY_SCRAPERS[fam]
        raw_path = RAW_DIR / cfg["out"]
        raw_n = raw_count(raw_path)
        if args.skip_live:
            meta = json.loads(raw_path.read_text(encoding="utf-8")) if raw_path.is_file() else {}
            union = int(meta.get("officialUnionCount") or meta.get("officialNbAlgoliaHits") or 0)
            view_all = int(meta.get("officialNbAlgoliaHits") or 0)
        else:
            try:
                union, view_all = official_union_count(cfg["leaves"])
            except Exception as e:
                print(f"{fam:28} {'?':>8} {'?':>6} {raw_n:6} LIVE_ERR {e}")
                bad += 1
                continue
        if raw_n == 0:
            status = "PENDING"
        elif raw_n == union:
            status = "OK"
        else:
            status = f"MISMATCH raw={raw_n} union={union}"
            bad += 1
        print(f"{fam:28} {view_all:8} {union:6} {raw_n:6} {status}")
    if args.fail and bad:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
