#!/usr/bin/env python3
"""Fix all Dior catalog prices — Gucci GBP formula, ignore KRW Algolia pollution.

  python3 scripts/fix-di-catalog-prices.py
  python3 scripts/fix-di-catalog-prices.py --check
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from di_common import di_price_anomalies, normalize_di_product_prices  # noqa: E402

CAT = ROOT / "src/data/di/di-catalog.json"


def load_raw_gbp_map() -> dict[str, float]:
    out: dict[str, float] = {}
    for fp in glob.glob(str(ROOT / "src/data/di/*-catalog-raw.json")):
        data = json.loads(Path(fp).read_text())
        for p in data.get("products") or []:
            pid = str(p.get("id") or "").strip()
            gbp = p.get("gbpPrice")
            if pid and gbp is not None:
                try:
                    out[pid] = float(gbp)
                except (TypeError, ValueError):
                    pass
    return out


def sku_keys(product: dict) -> list[str]:
    keys: list[str] = []
    for k in (product.get("sku"), product.get("id")):
        s = str(k or "").strip()
        if not s:
            continue
        keys.append(s)
        if s.startswith("di-"):
            keys.append(s[3:])
    return list(dict.fromkeys(keys))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="Report anomalies only")
    args = ap.parse_args()

    products = json.loads(CAT.read_text())
    raw_gbp = load_raw_gbp_map()

    if args.check:
        bad = di_price_anomalies(products)
        print(f"anomalies={len(bad)}", flush=True)
        for pid, gbp, pr, exp, vgbp in bad[:30]:
            print(f"  {pid} gbp={gbp} krw={pr} expected={exp} var_gbp={vgbp}", flush=True)
        return 1 if bad else 0

    fixed = 0
    for p in products:
        rg = None
        for key in sku_keys(p):
            if key in raw_gbp:
                rg = raw_gbp[key]
                break
        if normalize_di_product_prices(p, rg):
            fixed += 1

    CAT.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n")
    bad = di_price_anomalies(products)
    print(f"DONE fixed={fixed} remaining_anomalies={len(bad)}", flush=True)
    for pid, gbp, pr, exp, vgbp in bad[:10]:
        print(f"  still bad: {pid} gbp={gbp} krw={pr} expected={exp}", flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
