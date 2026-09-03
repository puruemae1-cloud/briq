#!/usr/bin/env python3
"""Force-refresh CW PDP galleries for multi-strap families (AGM1 / C3H1)."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "cwsync", ROOT / "scripts/weekly-cw-stock-sync.py"
)
cw = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(cw)

enr = json.loads(cw.ENR_PATH.read_text()) if cw.ENR_PATH.exists() else {"products": {}}
prods = enr.setdefault("products", {})
raw = json.loads(cw.RAW_PATH.read_text())
skus = sorted(
    {
        p.get("sku") or ""
        for p in raw.get("products") or []
        if "AGM1" in (p.get("sku") or "").upper() or "C3H1" in (p.get("sku") or "").upper()
    }
    - {""}
)
print(f"redownload {len(skus)} family SKUs", flush=True)
for i, sku in enumerate(skus, 1):
    cw.sync_gallery_and_enrich(sku, prods, force=True)
    if i % 10 == 0:
        cw.ENR_PATH.write_text(json.dumps(enr, indent=2, ensure_ascii=False) + "\n")
        print(f"  {i}/{len(skus)}", flush=True)
cw.ENR_PATH.write_text(json.dumps(enr, indent=2, ensure_ascii=False) + "\n")
print("done redownload", flush=True)
raise SystemExit(0)
