#!/usr/bin/env python3
"""Fetch Arc'teryx GB footwear product-feed + Bloomreach colour maps → ax-catalog-raw.json."""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src/data/ax/ax-catalog-raw.json"
FEED = "https://jh5e3sxgk0.execute-api.us-west-2.amazonaws.com/product-feed/products"


def feed(gender: str) -> list[dict]:
    qs = urllib.parse.urlencode(
        {
            "market": "outdoor",
            "language": "en",
            "country": "gb",
            "gender": gender,
            "category": "footwear",
            "subCategory": "",
            "env": "prod",
        }
    )
    req = urllib.request.Request(
        f"{FEED}?{qs}",
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def bloomreach(category_id: str) -> list[dict]:
    params = {
        "account_id": "7358",
        "domain_key": "arcteryx",
        "request_type": "search",
        "search_type": "category",
        "q": category_id,
        "rows": "50",
        "start": "0",
        "view_id": "gb",
        "url": "https://arcteryx.com/gb/en/c/mens/footwear",
        "ref_url": "https://arcteryx.com/gb/en/c/mens/footwear",
        "_br_uid_2": "uid=1234567890123:v=11.5:ts=1700000000000:hc=1",
        "request_id": str(int(time.time() * 1000)),
        "fl": "pid,title,description,slug,price_gb,discount_price_gb,colour_images_map_gb,hover_image,thumb_image,analytics_name,gender,is_new",
    }
    url = "https://core.dxpapi.com/api/v1/core/?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())["response"]["docs"]


def parse_colours(br_doc: dict | None, feed_item: dict) -> list[dict]:
    colours: list[dict] = []
    for row in (br_doc or {}).get("colour_images_map_gb") or []:
        parts = row.split(":::")
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
    if colours:
        return colours
    for opt in (feed_item.get("colourOptions") or {}).get("options") or []:
        img = opt.get("image") or {}
        th = opt.get("thumbnail") or {}
        colours.append(
            {
                "color": img.get("colourLabel")
                or th.get("label")
                or opt.get("primaryColour")
                or "",
                "profile": img.get("url") or "",
                "thumb": th.get("url") or "",
                "hover": (feed_item.get("mainImage") or {}).get("url") or "",
                "selected": True,
            }
        )
    return colours


def main() -> None:
    men = feed("mens")
    women = feed("womens")
    br = {d["pid"]: d for d in bloomreach("footwear-men") + bloomreach("footwear-women")}
    products = []
    for gender, items, coll in (
        ("mens", men, "ax-shoes-mens"),
        ("womens", women, "ax-shoes-womens"),
    ):
        for p in items:
            pid = p["id"]
            b = br.get(pid)
            products.append(
                {
                    "id": pid,
                    "name": p.get("name") or p.get("marketingName"),
                    "slug": p.get("slug"),
                    "url": f"https://arcteryx.com/gb/en/shop/{p.get('slug')}",
                    "gender": gender,
                    "collections": [coll],
                    "gbpPrice": p.get("price") or p.get("minPrice"),
                    "shortDescription": p.get("shortDescription")
                    or (b or {}).get("description")
                    or "",
                    "isNew": bool(
                        p.get("isNew")
                        or str((b or {}).get("is_new", "")).lower() == "true"
                    ),
                    "colours": parse_colours(b, p),
                    "mainImage": (p.get("mainImage") or {}).get("url") or "",
                }
            )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "scrapedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "products": products,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
    print(f"Wrote {len(products)} products → {OUT}")


if __name__ == "__main__":
    main()
