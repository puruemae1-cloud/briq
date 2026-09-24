#!/usr/bin/env python3
"""Extract bags-only catalogue slices from full brand JSON.

Bags PLPs must not parse 20–60MB full brand catalogues (RTW + shoes +
accessories). Re-run after weekly brand syncs that rewrite *-catalog.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src" / "data"

SOURCES: dict[str, list[Path]] = {
    "bb": [DATA / "bb/bb-catalog.json"],
    "ax": [
        DATA / "ax/ax-catalog.json",
        DATA / "ax/ax-apparel-catalog.json",
        DATA / "ax/ax-outlet-catalog.json",
        DATA / "ax/ax-gear-catalog.json",
    ],
    "bs": [DATA / "bs/bs-catalog.json"],
    "gc": [DATA / "gc/gc-catalog.json"],
    "bv": [DATA / "bv/bv-catalog.json"],
    "ch": [DATA / "ch/ch-catalog.json"],
    "ce": [DATA / "ce/ce-catalog.json"],
    "vw": [DATA / "vw/vw-catalog.json"],
    "pr": [DATA / "pr/pr-catalog.json"],
    "di": [DATA / "di/di-catalog.json"],
    "mb": [DATA / "mb/mb-catalog.json"],
    "ys": [DATA / "ys/ys-catalog.json"],
}

EXPORT_NAME = {
    "bb": "bbBagsCatalogProducts",
    "ax": "axBagsCatalogProducts",
    "bs": "bsBagsCatalogProducts",
    "gc": "gcBagsCatalogProducts",
    "bv": "bvBagsCatalogProducts",
    "ch": "chBagsCatalogProducts",
    "ce": "ceBagsCatalogProducts",
    "vw": "vwBagsCatalogProducts",
    "pr": "prBagsCatalogProducts",
    "di": "diBagsCatalogProducts",
    "mb": "mbBagsCatalogProducts",
    "ys": "ysBagsCatalogProducts",
}


def load_products(paths: list[Path]) -> list[dict]:
    out: list[dict] = []
    for p in paths:
        if not p.exists():
            print(f"WARN missing {p}", file=sys.stderr)
            continue
        data = json.loads(p.read_text())
        if isinstance(data, list):
            out.extend(data)
    return out


def main() -> None:
    total_n = 0
    total_bytes = 0
    for key, paths in SOURCES.items():
        products = load_products(paths)
        bags = [p for p in products if p.get("category") == "bags"]
        seen: set[str] = set()
        uniq: list[dict] = []
        for p in bags:
            pid = p.get("id")
            if not isinstance(pid, str) or pid in seen:
                continue
            seen.add(pid)
            uniq.append(p)
        out_json = DATA / key / f"{key}-bags-catalog.json"
        out_ts = DATA / key / f"{key}-bags-catalog.ts"
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(
            json.dumps(uniq, ensure_ascii=False, separators=(",", ":")) + "\n"
        )
        export = EXPORT_NAME[key]
        out_ts.write_text(
            'import type { Product } from "@/data/product-types";\n'
            f'import data from "./{key}-bags-catalog.json";\n\n'
            f"/** Bags-only slice — bags PLPs must not parse the full {key} catalogue. */\n"
            f"export const {export} = data as unknown as Product[];\n"
        )
        total_n += len(uniq)
        total_bytes += out_json.stat().st_size
        print(f"{key}: {len(uniq)} bags → {out_json.stat().st_size / 1e6:.2f}MB")
    print(f"TOTAL {total_n} products {total_bytes / 1e6:.1f}MB")


if __name__ == "__main__":
    main()
