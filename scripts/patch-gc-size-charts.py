#!/usr/bin/env python3
"""One-off: refresh Gucci RTW size charts in gc-catalog.json (no scrape).

Uses size_chart_for_rtw() from build-gc-catalog.py so jeans waist products
get GC_WOMEN_DENIM_SIZE_CHART and other RTW get the updated guide (JEANS
column on bottoms + denim tab). Handbags (no sizeChart) stay untouched.
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "src/data/gc/gc-catalog.json"

_spec = importlib.util.spec_from_file_location(
    "build_gc_catalog", ROOT / "scripts" / "build-gc-catalog.py"
)
_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_mod)

size_chart_for_rtw = _mod.size_chart_for_rtw


def main() -> None:
    products = json.loads(OUT_JSON.read_text())
    switched_denim: list[str] = []
    refreshed_rtw: list[str] = []
    denim_name_apparel: list[tuple[str, str, list]] = []
    handbags_untouched = 0
    other_skipped = 0

    for p in products:
        sc = p.get("sizeChart")
        if not sc:
            handbags_untouched += 1
            continue
        sc_id = sc.get("id")
        if sc_id not in {"gc-women-rtw", "gc-women-denim"}:
            other_skipped += 1
            continue

        variants = p.get("variants") or []
        new_chart = size_chart_for_rtw(variants)
        p["sizeChart"] = new_chart

        if new_chart["id"] == "gc-women-denim":
            switched_denim.append(p["id"])
        else:
            refreshed_rtw.append(p["id"])

        name = f"{p.get('name') or ''} {p.get('nameKo') or ''}"
        if re.search(r"denim|jeans|데님|\b진\b", name, re.I) and new_chart["id"] != "gc-women-denim":
            sizes = [v.get("size") for v in variants]
            denim_name_apparel.append((p["id"], p.get("name") or "", sizes))

    OUT_JSON.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n")

    target = next((p for p in products if p.get("id") == "gc-865596xddg04011"), None)
    print("=== Gucci size chart patch ===")
    print(f"products total:           {len(products)}")
    print(f"switched to denim chart:  {len(switched_denim)}")
    print(f"refreshed RTW chart:      {len(refreshed_rtw)}")
    print(f"no sizeChart (handbags+): {handbags_untouched}")
    print(f"other sizeChart skipped:  {other_skipped}")
    print()
    print("Denim chart product ids:")
    for pid in switched_denim:
        print(f"  {pid}")
    print()
    print(f"Denim-by-name but apparel IT sizes (kept RTW): {len(denim_name_apparel)}")
    for pid, name, sizes in denim_name_apparel:
        print(f"  {pid}  {name}  sizes={sizes[:8]}...")
    print()
    if target:
        sc = target["sizeChart"]
        print("VERIFY gc-865596xddg04011:")
        print(f"  chart id: {sc['id']}")
        print(f"  primary headers: {sc.get('headers')}")
        print(f"  first row: {(sc.get('rows') or [None])[0]}")
        jeans_col = (sc.get("rows") or [[None]])[0][0] if sc.get("rows") else None
        tabs = [t.get("id") for t in (sc.get("tabs") or [])]
        print(f"  tabs: {tabs}")
        print(f"  starts at JEANS: {jeans_col}")
        assert sc["id"] == "gc-women-denim", "expected denim chart"
        assert jeans_col == "20", f"expected JEANS 20 start, got {jeans_col}"
        # variant IT 23 should map — show denim row for 23
        row23 = next((r for r in sc.get("rows") or [] if r[0] == "23"), None)
        print(f"  JEANS 23 row: {row23}")
        print("  OK")
    else:
        print("WARN: gc-865596xddg04011 not found")
    print(f"\nWrote {OUT_JSON}")


if __name__ == "__main__":
    main()
