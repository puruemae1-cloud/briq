#!/usr/bin/env python3
"""Fail when Bottega Veneta nameKo is still English."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "src/data/bv/bv-catalog.json"


def has_hangul(s: str) -> bool:
    return any("\uac00" <= c <= "\ud7a3" for c in (s or ""))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fail", action="store_true")
    ap.add_argument("--max-bad", type=int, default=0)
    args = ap.parse_args()
    products = json.loads(CATALOG.read_text(encoding="utf-8"))
    bad = []
    for p in products:
        nk = str(p.get("nameKo") or "").strip()
        if not nk:
            continue
        if has_hangul(nk):
            continue
        if re.search(r"[A-Za-z]{3,}", nk):
            bad.append((p.get("id"), nk))
    print(f"bv nameKo english_rows={len(bad)} / {len(products)}", flush=True)
    for pid, nk in bad[:20]:
        print(f"  {pid}: {nk}", flush=True)
    if args.fail and len(bad) > args.max_bad:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
