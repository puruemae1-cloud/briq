#!/usr/bin/env python3
"""Re-scrape CW category PLPs (incl. Show more / UpdateGrid pagination) and sync raw catalog."""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/jeonghyunlee/Documents/briq")
RAW_PATH = ROOT / "src/data/cw/cw-catalog-raw.json"
UA = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept-Language": "en-GB,en;q=0.9",
}
BASE = "https://www.christopherward.com/on/demandware.store/Sites-cwgross-Site/en_GB/Search-UpdateGrid"
QV = "https://www.christopherward.com/on/demandware.store/Sites-cwgross-Site/en_GB/Product-ShowQuickView"

# (briq_id, cgid, optional query extras for filters)
CATEGORIES = [
    ("cw-new-releases", "new-watches", None),
    ("cw-bestsellers", "most-popular-watches", None),
    ("cw-hidden-gems", "hidden-gems", None),
    # Sale "All watches" refinement — excludes straps/bracelets
    ("cw-clearance", "sale", "prefn1=ID&prefv1=All%20watches"),
    ("cw-atelier", "atelier-watches", None),
    ("cw-dive", "dive-watches", None),
    ("cw-integrated-sports", "integrated-sports-watches", None),
    ("cw-adventure-field", "adventure-field-watches", None),
    ("cw-military", "military-watches", None),
    ("cw-bel-canto", "Bel-Canto-Watches", None),
    ("cw-sealander", "sealander", None),
    ("cw-twelve", "the-twelve-watches", None),
    ("cw-trident", "trident-watches", None),
    ("cw-moonphase", "moonphase-watches", None),
]


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            **UA,
            "Accept": "application/json,text/javascript,*/*",
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def is_watch_sku(pid: str) -> bool:
    """C*/N* watch refs — exclude strap-like N20-STL / bare accessory SKUs."""
    if not re.match(r"^[CN]\d", pid):
        return False
    # Nearly-new bracelet / strap refs look like N20-STL-… / N22-TIT-…
    if re.match(r"^N\d{2}-(STL|TIT|RUB|HYB|MAS|TIDE)-", pid, re.I):
        return False
    return True


def scrape_category(cgid: str, extra: str | None, sz: int = 36) -> list[str]:
    all_pids: list[str] = []
    start = 0
    while True:
        q = f"cgid={urllib.parse.quote(cgid)}&srule=most-popular&start={start}&sz={sz}"
        if extra:
            q = f"{q}&{extra}"
        html = fetch(f"{BASE}?{q}")
        pids = list(dict.fromkeys(re.findall(r'data-pid="([^"]+)"', html)))
        if not pids:
            break
        all_pids.extend(pids)
        if len(pids) < sz:
            break
        start += sz
        time.sleep(0.12)
    seen: set[str] = set()
    out: list[str] = []
    for p in all_pids:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def parse_price(product: dict) -> tuple[float | None, float | None]:
    price = product.get("price") or {}
    sales = price.get("sales") or {}
    lst = price.get("list") or {}
    sale_v = sales.get("value")
    list_v = lst.get("value")
    gbp = float(sale_v) if sale_v is not None else (float(list_v) if list_v is not None else None)
    list_gbp = float(list_v) if list_v is not None else None
    if list_gbp is not None and gbp is not None and list_gbp <= gbp:
        list_gbp = None
    return gbp, list_gbp


def ensure_product(raw: dict, sku: str, collection: str) -> dict:
    by = {p["sku"]: p for p in raw["products"]}
    if sku in by:
        p = by[sku]
        cols = list(p.get("collections") or [])
        if collection not in cols:
            cols.append(collection)
        p["collections"] = cols
        if not p.get("primaryCollection"):
            p["primaryCollection"] = collection
        return p

    # Fetch PDP quick view for new SKU
    print(f"  + fetch new SKU {sku}")
    try:
        data = fetch_json(f"{QV}?pid={urllib.parse.quote(sku)}")
        prod = data.get("product") or {}
    except Exception as e:
        print(f"    ERR {e}")
        prod = {}
    gbp, list_gbp = parse_price(prod)
    name = (prod.get("productName") or sku).strip()
    images = prod.get("images") or {}
    large = (images.get("large") or images.get("hi-res") or images.get("medium") or [])
    img = ""
    if large and isinstance(large, list) and large[0].get("url"):
        img = large[0]["url"]
    url = ""
    sel = prod.get("selectedProductUrl") or prod.get("productUrl") or ""
    if sel:
        url = urllib.parse.urljoin("https://www.christopherward.com", sel.split("?")[0])
    p = {
        "sku": sku,
        "name": name,
        "subtitle": "",
        "url": url,
        "image": img,
        "badge": "Nearly New" if "nearly new" in name.lower() or sku.upper().startswith("N") else None,
        "gbpPrice": gbp,
        "gbpListPrice": list_gbp,
        "collections": [collection],
        "primaryCollection": collection,
    }
    raw["products"].append(p)
    time.sleep(0.15)
    return p


def refresh_price(p: dict) -> None:
    sku = p["sku"]
    if p.get("gbpPrice") is not None:
        return
    try:
        data = fetch_json(f"{QV}?pid={urllib.parse.quote(sku)}")
        gbp, list_gbp = parse_price(data.get("product") or {})
        if gbp is not None:
            p["gbpPrice"] = gbp
        if list_gbp is not None:
            p["gbpListPrice"] = list_gbp
        print(f"  price {sku} = {gbp} / list {list_gbp}")
        time.sleep(0.12)
    except Exception as e:
        print(f"  price ERR {sku}: {e}")


def rebuild_collections_from_categories(raw: dict) -> None:
    """Set each product's collections from the category membership map (source of truth)."""
    membership: dict[str, list[str]] = {}
    for cat, skus in raw["categories"].items():
        for sku in skus:
            membership.setdefault(sku, []).append(cat)

    priority = [
        "cw-clearance",
        "cw-new-releases",
        "cw-bestsellers",
        "cw-hidden-gems",
        "cw-bel-canto",
        "cw-twelve",
        "cw-trident",
        "cw-sealander",
        "cw-moonphase",
        "cw-military",
        "cw-dive",
        "cw-integrated-sports",
        "cw-adventure-field",
        "cw-atelier",
    ]

    by = {p["sku"]: p for p in raw["products"]}
    for sku, cols in membership.items():
        if sku not in by:
            continue
        uniq = list(dict.fromkeys(cols))
        by[sku]["collections"] = uniq
        prim = next((c for c in priority if c in uniq), uniq[0])
        by[sku]["primaryCollection"] = prim

    # Delisted from every tracked PLP — drop clearance so they leave Clearance filter
    for p in raw["products"]:
        if p["sku"] in membership:
            continue
        old = list(p.get("collections") or [])
        new = [c for c in old if c != "cw-clearance"]
        p["collections"] = new
        if p.get("primaryCollection") == "cw-clearance":
            p["primaryCollection"] = new[0] if new else None


def main() -> None:
    raw = json.loads(RAW_PATH.read_text())
    live: dict[str, list[str]] = {}

    print("Scraping CW category grids…")
    for briq_id, cgid, extra in CATEGORIES:
        pids = scrape_category(cgid, extra)
        watches = [p for p in pids if is_watch_sku(p)]
        live[briq_id] = watches
        print(f"  {briq_id}: live={len(pids)} watches={len(watches)}")

    # Merge: clearance replaced by live (exact sale watches); other cats add missing, keep extras
    for briq_id, watches in live.items():
        prev = list(raw["categories"].get(briq_id, []))
        if briq_id == "cw-clearance":
            merged = watches[:]  # exact live sale watches
        else:
            merged = list(dict.fromkeys(prev + watches))
        added = [s for s in watches if s not in prev]
        removed = [s for s in prev if s not in watches] if briq_id == "cw-clearance" else []
        raw["categories"][briq_id] = merged
        raw["categoryCounts"][briq_id] = len(merged)
        if added:
            print(f"  {briq_id} +{len(added)} {added[:6]}")
        if removed:
            print(f"  {briq_id} -{len(removed)} {removed[:6]}")

    # Ensure product rows exist + prices for every category member
    all_skus = sorted({s for skus in raw["categories"].values() for s in skus})
    by = {p["sku"]: p for p in raw["products"]}
    for cat, skus in raw["categories"].items():
        for sku in skus:
            if sku not in by:
                ensure_product(raw, sku, cat)
                by = {p["sku"]: p for p in raw["products"]}
            else:
                # keep membership; collections rebuilt below
                pass

    for sku in raw["categories"].get("cw-clearance", []):
        p = by.get(sku)
        if p:
            refresh_price(p)
            # force clearance badge/name hint
            if not p.get("badge") and (sku.upper().startswith("N") or "nearly new" in (p.get("name") or "").lower()):
                p["badge"] = "Nearly New"

    rebuild_collections_from_categories(raw)
    raw["scrapedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    RAW_PATH.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n")
    print("Wrote", RAW_PATH)
    print("Clearance:", raw["categories"]["cw-clearance"])
    print("Counts:", raw["categoryCounts"])


if __name__ == "__main__":
    main()
