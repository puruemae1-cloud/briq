#!/usr/bin/env python3
"""Refresh Celine raw availability from official GB SFCC Product-Variation.

Uses Sites-CELINE_GB-Site — works when HTML PDP is WAF-blocked.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from celine_common import apply_sfcc_availability, load_json, save_json  # noqa: E402
from celine_config import celine_raw_paths  # noqa: E402


def main() -> int:
    changed = 0
    checked = 0
    for path in celine_raw_paths():
        payload = load_json(path, {"products": []})
        products = payload.get("products") or []
        local = 0
        for row in products:
            if not isinstance(row, dict) or row.get("membershipOnly"):
                continue
            before = row.get("availability"), row.get("availabilityConfidence")
            updated = apply_sfcc_availability(row)
            checked += 1
            if (updated.get("availability"), updated.get("availabilityConfidence")) != before:
                local += 1
                changed += 1
            row.clear()
            row.update(updated)
            time.sleep(0.08)
        if local:
            payload["products"] = products
            save_json(path, payload)
        print(f"{path.name}: updated {local}/{len(products)}", flush=True)
    print(f"SFCC stock refresh checked={checked} changed={changed}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
