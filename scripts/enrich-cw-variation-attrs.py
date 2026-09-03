#!/usr/bin/env python3
"""Fill size/colour/strap attrs on CW enriched rows missing them (for option labels)."""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = json.loads((ROOT / "src/data/cw/cw-catalog-raw.json").read_text())
ENR_PATH = ROOT / "src/data/cw/cw-pdp-enriched.json"
enr = json.loads(ENR_PATH.read_text()) if ENR_PATH.exists() else {"products": {}}
products = enr.setdefault("products", {})

UA = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "X-Requested-With": "XMLHttpRequest",
    "Accept-Language": "en-GB",
}
API = "https://www.christopherward.com/on/demandware.store/Sites-cwgross-Site/en_GB/Product-Variation"


def selected(product: dict, attr: str) -> str:
    for a in product.get("variationAttributes") or []:
        if a.get("attributeId") == attr:
            for v in a.get("values") or []:
                if v.get("selected"):
                    return str(v.get("displayValue") or v.get("value") or "").strip()
    return ""


def main() -> int:
    todo = []
    for p in RAW["products"]:
        sku = p.get("sku") or ""
        if sku.count("-") < 2:
            continue
        e = products.get(sku) or {}
        if not (e.get("size") and e.get("strap") and e.get("colour")):
            todo.append(sku)
    print(f"todo {len(todo)}", flush=True)
    for i, sku in enumerate(todo, 1):
        try:
            req = urllib.request.Request(
                f"{API}?pid={urllib.parse.quote(sku)}&quantity=1", headers=UA
            )
            with urllib.request.urlopen(req, timeout=50) as r:
                ap = json.loads(r.read().decode()).get("product") or {}
            e = products.setdefault(sku, {"sku": sku})
            if ap.get("productName"):
                e["nameEn"] = ap["productName"]
            size = selected(ap, "WSize")
            colour = selected(ap, "WDialBezelColour")
            strap = selected(ap, "WStrapColourMaterialType")
            if size:
                e["size"] = size
            if colour:
                e["colour"] = colour
            if strap:
                e["strap"] = strap
        except Exception as ex:
            print(f"ERR {sku}: {ex}", flush=True)
        if i % 25 == 0:
            ENR_PATH.write_text(json.dumps(enr, indent=2, ensure_ascii=False) + "\n")
            print(f"checkpoint {i}/{len(todo)}", flush=True)
        time.sleep(0.08)
    ENR_PATH.write_text(json.dumps(enr, indent=2, ensure_ascii=False) + "\n")
    print("done attrs", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
