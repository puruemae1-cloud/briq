#!/usr/bin/env python3
"""One-shot repair: fix Celine raw availability poisoned by AVAILABLE NOW-only checks.

Safe to re-run. Writes healed availability back into ce-*-catalog-raw.json so
weekly merges stop carrying mass false sold-outs.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from celine_common import load_json, save_json  # noqa: E402
from celine_config import celine_raw_paths  # noqa: E402


def heal_availability(row: dict) -> bool:
    """Return True when the row was changed."""
    if row.get("membershipOnly"):
        return False
    before = row.get("availability"), row.get("availabilityConfidence")
    conf = str(row.get("availabilityConfidence") or "")
    title = str(row.get("title") or "")
    images = [x for x in (row.get("images") or []) if x and "placeholder" not in str(x)]
    blob = " ".join(
        [
            title,
            str(row.get("url") or ""),
            " ".join(
                str(d.get("body") or "")
                for d in (row.get("details") or [])
                if isinstance(d, dict)
            ),
        ]
    )
    if re.search(r"\bsold[\s-]?out\b|\bout of stock\b|\bnotify me\b", blob, re.I):
        row["availability"] = False
        row["availabilityConfidence"] = "sold_out"
    elif row.get("scrapeBlocked"):
        row["availability"] = None
        row["availabilityConfidence"] = "blocked"
    elif row.get("availability") is False and conf not in {
        "sold_out",
        "schema_oos",
        "sfcc_oos",
    }:
        if images and (row.get("details") or row.get("sizes")):
            row["availability"] = True
            row["availabilityConfidence"] = "healed_full_pdp"
        elif images:
            row["availability"] = True
            row["availabilityConfidence"] = "healed_listed"
        else:
            row["availability"] = None
            row["availabilityConfidence"] = "unknown"
    after = row.get("availability"), row.get("availabilityConfidence")
    return after != before


def main() -> None:
    changed_rows = 0
    for path in celine_raw_paths():
        payload = load_json(path, {"products": []})
        products = payload.get("products") or []
        n = 0
        for row in products:
            if isinstance(row, dict) and heal_availability(row):
                n += 1
        if n:
            payload["products"] = products
            save_json(path, payload)
            print(f"{path.name}: healed {n}/{len(products)}", flush=True)
            changed_rows += n
        else:
            print(f"{path.name}: no changes", flush=True)
    print(f"TOTAL healed rows {changed_rows}", flush=True)


if __name__ == "__main__":
    main()
