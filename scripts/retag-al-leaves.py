#!/usr/bin/env python3
"""Retag AllSaints raw products with subcategory leaf collections (no PDP)."""
from __future__ import annotations

import argparse

from al_common import fetch_plp_pids, load_json, save_json
from al_config import RAW_DIR, AL_FAMILY_SCRAPERS


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", required=True, choices=sorted(AL_FAMILY_SCRAPERS))
    args = ap.parse_args()
    cfg = AL_FAMILY_SCRAPERS[args.family]
    out = RAW_DIR / cfg["out"]
    data = load_json(out, {"products": []})
    products = data.get("products") or []
    by_id = {str(p.get("id") or ""): p for p in products if p.get("id")}
    print(f"raw products={len(by_id)}", flush=True)
    for leaf in cfg["leaves"]:
        ids = set(fetch_plp_pids(leaf["cgid"]))
        cols = list(leaf.get("collections") or [])
        hit = 0
        for pid in ids:
            row = by_id.get(pid)
            if not row:
                continue
            row["collections"] = list(dict.fromkeys([*(row.get("collections") or []), *cols]))
            hit += 1
        print(f"  {leaf['id']}: plp={len(ids)} tagged={hit}", flush=True)
    save_json(
        out,
        {
            **{k: v for k, v in data.items() if k != "products"},
            "products": list(by_id.values()),
        },
    )
    print(f"saved {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
