#!/usr/bin/env python3
"""Scrape Arc'teryx GB outdoor accessories + packs + climbing-gear via Bloomreach.

Writes:
  src/data/ax/ax-gear-raw.json
"""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src/data/ax/ax-gear-raw.json"
FEED = "https://jh5e3sxgk0.execute-api.us-west-2.amazonaws.com/product-feed/products"


def bloomreach_category(category_id: str, rows: int = 200) -> list[dict]:
    params = {
        "account_id": "7358",
        "domain_key": "arcteryx",
        "request_type": "search",
        "search_type": "category",
        "q": category_id,
        "rows": str(rows),
        "start": "0",
        "view_id": "gb",
        "url": f"https://arcteryx.com/gb/en/c/{category_id}",
        "ref_url": f"https://arcteryx.com/gb/en/c/{category_id}",
        "_br_uid_2": "uid=1234567890123:v=11.5:ts=1700000000000:hc=1",
        "request_id": str(int(time.time() * 1000)),
        "fl": "pid,title,description,slug,price_gb,discount_price_gb,colour_images_map_gb,hover_image,thumb_image,analytics_name,gender,is_new",
    }
    url = "https://core.dxpapi.com/api/v1/core/?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["response"]["docs"]


def feed_by_id(gender: str) -> dict[str, dict]:
    qs = urllib.parse.urlencode(
        {
            "market": "outdoor",
            "language": "en",
            "country": "gb",
            "gender": gender,
            "category": "",
            "subCategory": "",
            "env": "prod",
        }
    )
    req = urllib.request.Request(
        f"{FEED}?{qs}",
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        items = json.loads(r.read())
    return {p["id"]: p for p in items}


def parse_br_colours(doc: dict) -> list[dict]:
    colours: list[dict] = []
    for row in doc.get("colour_images_map_gb") or []:
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


def gender_norm(raw: str | None) -> str:
    g = (raw or "").lower().strip()
    if g in ("men", "mens", "male"):
        return "mens"
    if g in ("women", "womens", "female"):
        return "womens"
    return "unisex"


def is_harness(name: str | None) -> bool:
    return "harness" in (name or "").lower()


def collections_for(kind: str, gender: str) -> list[str]:
    if kind == "accessories":
        if gender == "mens":
            return ["ax-acc-mens"]
        if gender == "womens":
            return ["ax-acc-womens"]
        return ["ax-acc-womens", "ax-acc-mens"]
    if kind == "climbing":
        if gender == "mens":
            return ["ax-climbing-mens"]
        if gender == "womens":
            return ["ax-climbing-womens"]
        return ["ax-climbing-womens", "ax-climbing-mens"]
    # packs (+ non-harness climbing gear like chalk bags) → bags
    if gender == "mens":
        return ["ax-bags-mens"]
    if gender == "womens":
        return ["ax-bags-womens"]
    return ["ax-bags-womens", "ax-bags-mens"]


def main() -> None:
    feed_map: dict[str, dict] = {}
    for g in ("mens", "womens"):
        feed_map.update(feed_by_id(g))
        time.sleep(0.2)

    # accessories → accessories; packs → bags; climbing harness → climbing gear
    # (chalk bags etc. stay under bags)
    sources = [
        ("accessories", "accessories"),
        ("packs", "bags"),
        ("climbing-gear", "climbing"),
    ]
    products: list[dict] = []
    seen: set[str] = set()

    for br_cat, default_kind in sources:
        docs = bloomreach_category(br_cat)
        print(f"{br_cat}: {len(docs)} docs")
        for d in docs:
            pid = d.get("pid")
            if not pid or pid in seen:
                continue
            seen.add(pid)
            feed_item = feed_map.get(pid) or {}
            colours = parse_br_colours(d)
            if not colours:
                main = feed_item.get("mainImage") or {}
                colours = [
                    {
                        "color": main.get("colourLabel") or "Default",
                        "profile": main.get("url") or d.get("thumb_image") or "",
                        "thumb": d.get("thumb_image") or "",
                        "hover": d.get("hover_image") or main.get("url") or "",
                        "selected": True,
                    }
                ]
            gender = gender_norm(d.get("gender") or feed_item.get("gender"))
            sale = d.get("discount_price_gb") or d.get("price_gb")
            list_p = d.get("price_gb") or sale
            if feed_item:
                sale = (
                    feed_item.get("discountPrice")
                    or feed_item.get("minDiscountPrice")
                    or feed_item.get("price")
                    or sale
                )
                list_p = feed_item.get("price") or feed_item.get("minPrice") or list_p
            slug = d.get("slug") or feed_item.get("slug") or ""
            name = d.get("title") or feed_item.get("name") or pid
            kind = default_kind
            if br_cat == "climbing-gear" and not is_harness(str(name)):
                # chalk bags / buckets remain in bags category
                kind = "bags"
            products.append(
                {
                    "id": pid,
                    "name": name,
                    "slug": slug,
                    "url": f"https://arcteryx.com/gb/en/shop/{slug}" if slug else "",
                    "kind": kind,
                    "sourceCategory": br_cat,
                    "gender": gender,
                    "collections": collections_for(kind, gender),
                    "gbpPrice": float(sale) if sale is not None else None,
                    "gbpListPrice": float(list_p) if list_p is not None else None,
                    "isNew": bool(d.get("is_new") or feed_item.get("isNew")),
                    "shortDescription": d.get("description")
                    or feed_item.get("description")
                    or "",
                    "colours": colours,
                }
            )
        time.sleep(0.15)

    payload = {
        "scrapedAt": datetime.now(timezone.utc).isoformat(),
        "source": [
            "https://arcteryx.com/gb/en/c/accessories",
            "https://arcteryx.com/gb/en/c/packs",
            "https://arcteryx.com/gb/en/c/climbing-gear",
        ],
        "count": len(products),
        "products": products,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    by_kind: dict[str, int] = {}
    for p in products:
        by_kind[p["kind"]] = by_kind.get(p["kind"], 0) + 1
    print(f"Wrote {len(products)} → {OUT} ({by_kind})")


if __name__ == "__main__":
    main()
