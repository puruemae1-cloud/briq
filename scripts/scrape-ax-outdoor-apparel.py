#!/usr/bin/env python3
"""Scrape Arc'teryx GB outdoor women's/men's apparel (excl. footwear/packs/harness).

Writes:
  src/data/ax/ax-apparel-raw.json
  src/data/ax/ax-apparel-urls.json  (for PDP enrichment)
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src/data/ax/ax-apparel-raw.json"
URLS = ROOT / "src/data/ax/ax-apparel-urls.json"
FEED = "https://jh5e3sxgk0.execute-api.us-west-2.amazonaws.com/product-feed/products"
EXISTING_SHOES = ROOT / "src/data/ax/ax-catalog.ts"
OUTLET_CAT = ROOT / "src/data/ax/ax-outlet-catalog.ts"


def feed(gender: str, category: str = "") -> list[dict]:
    qs = urllib.parse.urlencode(
        {
            "market": "outdoor",
            "language": "en",
            "country": "gb",
            "gender": gender,
            "category": category,
            "subCategory": "",
            "env": "prod",
        }
    )
    req = urllib.request.Request(
        f"{FEED}?{qs}",
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())


def bloomreach_pid(pid: str) -> dict | None:
    params = {
        "account_id": "7358",
        "domain_key": "arcteryx",
        "request_type": "search",
        "search_type": "keyword",
        "q": pid,
        "rows": "5",
        "start": "0",
        "view_id": "gb",
        "url": "https://arcteryx.com/gb/en",
        "ref_url": "https://arcteryx.com/gb/en",
        "_br_uid_2": "uid=1234567890123:v=11.5:ts=1700000000000:hc=1",
        "request_id": str(int(time.time() * 1000)),
        "fl": "pid,title,description,slug,price_gb,discount_price_gb,colour_images_map_gb,hover_image,thumb_image,analytics_name,gender,is_new",
    }
    url = "https://core.dxpapi.com/api/v1/core/?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            docs = json.loads(r.read())["response"]["docs"]
    except Exception:
        return None
    return next((d for d in docs if d.get("pid") == pid), docs[0] if docs else None)


def parse_br_colours(br: dict | None) -> list[dict]:
    colours: list[dict] = []
    for row in (br or {}).get("colour_images_map_gb") or []:
        parts = str(row).split(":::")
        if len(parts) < 4:
            continue
        color = parts[1]
        profile = parts[3] if parts[3] not in ("", "null", "undefined") else ""
        thumb = (
            parts[4]
            if len(parts) > 4 and parts[4] not in ("", "null", "undefined")
            else ""
        )
        hover = (
            parts[6]
            if len(parts) > 6 and parts[6] not in ("", "null", "undefined")
            else ""
        )
        if not profile and not thumb:
            continue
        colours.append(
            {
                "color": color,
                "profile": profile,
                "thumb": thumb,
                "hover": hover,
                "selected": parts[2] == "true",
            }
        )
    return colours


def parse_feed_colours(item: dict) -> list[dict]:
    colours: list[dict] = []
    for opt in (item.get("colourOptions") or {}).get("options") or []:
        img = opt.get("image") or {}
        th = opt.get("thumbnail") or {}
        color = (
            img.get("colourLabel")
            or th.get("label")
            or opt.get("primaryColour")
            or ""
        )
        # strip product name from thumbnail labels like "Atom SV Hoody W Vitality"
        if color and " " in color and not img.get("colourLabel"):
            # keep as-is; build script will slugify
            pass
        colours.append(
            {
                "color": img.get("colourLabel") or opt.get("primaryColour") or color,
                "profile": img.get("url") or "",
                "thumb": th.get("url") or "",
                "hover": "",
                "selected": False,
            }
        )
    # dedupe by color
    seen: set[str] = set()
    out: list[dict] = []
    for c in colours:
        key = (c.get("color") or "").lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def existing_shoe_skus() -> set[str]:
    skus: set[str] = set()
    if EXISTING_SHOES.exists():
        skus |= set(re.findall(r'sku: "(X\d+)"', EXISTING_SHOES.read_text()))
    if OUTLET_CAT.exists():
        text = OUTLET_CAT.read_text()
        for m in re.finditer(
            r'id: "axo-[^"]+"([\s\S]*?)(?=\n  \{\n    id: |\n\];)', text
        ):
            block = m.group(0)
            if 'category: "shoes"' in block[:800]:
                sm = re.search(r'sku: "(X\d+)"', block)
                if sm:
                    skus.add(sm.group(1))
    raw_shoes = ROOT / "src/data/ax/ax-catalog-raw.json"
    if raw_shoes.exists():
        for p in json.loads(raw_shoes.read_text()).get("products") or []:
            if p.get("id"):
                skus.add(p["id"])
    return skus


def main() -> None:
    shoe_skus = existing_shoe_skus()
    products: list[dict] = []
    new_fw = 0
    skipped_fw = 0

    for gender in ("womens", "mens"):
        all_items = feed(gender, "")
        fw_items = feed(gender, "footwear")
        pack_ids = {p["id"] for p in feed(gender, "packs")}
        fw_ids = {p["id"] for p in fw_items}

        for p in fw_items:
            if p["id"] in shoe_skus:
                skipped_fw += 1
                continue
            # would add new footwear — currently expected 0
            new_fw += 1
            # skip adding here; user asked only non-dupes and none remain
            shoe_skus.add(p["id"])

        for p in all_items:
            pid = p["id"]
            if pid in fw_ids or pid in pack_ids:
                continue
            name = p.get("name") or p.get("marketingName") or ""
            if "Harness" in name:
                continue

            # Feed colourOptions are usually complete; Bloomreach fills gaps.
            colours = parse_feed_colours(p)
            if len(colours) < 2:
                br = bloomreach_pid(pid)
                br_cols = parse_br_colours(br)
                if len(br_cols) > len(colours):
                    colours = br_cols
                time.sleep(0.08)
            if not colours:
                main = p.get("mainImage") or {}
                colours = [
                    {
                        "color": main.get("colourLabel") or "Default",
                        "profile": main.get("url") or "",
                        "thumb": "",
                        "hover": main.get("url") or "",
                        "selected": True,
                    }
                ]

            sale = p.get("discountPrice") or p.get("minDiscountPrice") or p.get("price")
            list_p = p.get("price") or p.get("minPrice") or sale
            slug = p.get("slug") or ""
            url = f"https://arcteryx.com/gb/en/shop/{slug}" if slug else ""

            products.append(
                {
                    "id": pid,
                    "name": name,
                    "slug": slug,
                    "url": url,
                    "gender": gender,
                    "kind": "clothing",
                    "collections": [
                        "ax-womens" if gender == "womens" else "ax-mens"
                    ],
                    "gbpPrice": sale,
                    "gbpListPrice": list_p,
                    "shortDescription": p.get("shortDescription") or "",
                    "isNew": bool(p.get("isNew")),
                    "colours": colours,
                    "mainImage": (p.get("mainImage") or {}).get("url") or "",
                }
            )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "scrapedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "products": products,
        "meta": {
            "skippedFootwearDupes": skipped_fw,
            "newFootwearWouldAdd": new_fw,
        },
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    URLS.write_text(
        json.dumps(
            {
                "products": [
                    {"index": i, "id": p["id"], "url": p["url"], "name": p["name"]}
                    for i, p in enumerate(products)
                ]
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
    print(
        f"Wrote {len(products)} apparel → {OUT} "
        f"(skipped fw dupes={skipped_fw}, new fw={new_fw})"
    )


if __name__ == "__main__":
    main()
