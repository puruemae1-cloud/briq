#!/usr/bin/env python3
"""Backfill Celine accessory leaf membership on ce-catalog.json (nav ID alignment).

Safe to re-run. Used after build-ce-catalog and as a weekly sync safety net when
leaf PLP scrapes return empty / membershipOnly fails to promote.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ce_accessory_membership import enrich_row_membership  # noqa: E402

CATALOG = ROOT / "src" / "data" / "ce" / "ce-catalog.json"


def main() -> int:
    items = json.loads(CATALOG.read_text())
    if not isinstance(items, list):
        print("unexpected catalog shape", file=sys.stderr)
        return 1
    changed = 0
    for p in items:
        row = {
            "leafId": p.get("subcategory") or "",
            "title": p.get("titleEn")
            or p.get("nameEn")
            or p.get("name")
            or p.get("title")
            or "",
            "collections": list(p.get("ceCollections") or []),
        }
        enriched = enrich_row_membership(row)
        new_sub = enriched.get("leafId") or p.get("subcategory")
        new_cols = enriched.get("collections") or []
        if new_sub != p.get("subcategory") or new_cols != (p.get("ceCollections") or []):
            p["subcategory"] = new_sub
            p["ceCollections"] = new_cols
            changed += 1
    CATALOG.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n")
    print(f"patched {changed}/{len(items)} CE accessory memberships → {CATALOG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
