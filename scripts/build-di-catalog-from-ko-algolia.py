#!/usr/bin/env python3
"""Merge Dior tableware + objects raw into di-catalog using KO Algolia (+ EN fallback).

  python3 scripts/build-di-catalog-from-ko-algolia.py
  python3 scripts/check-catalog-korean.py --brand di --fail
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from di_common import (  # noqa: E402
    ALGOLIA_MERCH_API_KEY,
    ALGOLIA_MERCH_APP_ID,
    ALGOLIA_MERCH_INDEX_KO,
    dior_code_to_object_id,
    gbp_to_krw,
    slugify,
)
from ko_qa import en_ratio, is_good_korean  # noqa: E402

RAW_PATHS = [
    ROOT / "src/data/di/di-tableware-catalog-raw.json",
    ROOT / "src/data/di/di-objects-catalog-raw.json",
]
OUT_JSON = ROOT / "src/data/di/di-catalog.json"
OUT_TS = ROOT / "src/data/di/di-catalog.ts"
ACCENTS = ["#1A1A1A", "#2C2420", "#243028", "#3A2F28", "#1E2830", "#2A2028"]


def fetch_ko(codes: list[str]) -> dict[str, dict]:
    by: dict[str, dict] = {}
    oid_to = {dior_code_to_object_id(c): c for c in codes}
    oids = list(oid_to)
    url = f"https://{ALGOLIA_MERCH_APP_ID}-dsn.algolia.net/1/indexes/*/queries"
    for i in range(0, len(oids), 12):
        chunk = oids[i : i + 12]
        filt = " OR ".join(f"objectID:{oid}" for oid in chunk)
        params = urllib.parse.urlencode(
            {
                "filters": filt,
                "hitsPerPage": len(chunk) + 5,
                "attributesToRetrieve": "*",
            }
        )
        body = json.dumps(
            {"requests": [{"indexName": ALGOLIA_MERCH_INDEX_KO, "params": params}]}
        ).encode()
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-Algolia-Application-Id": ALGOLIA_MERCH_APP_ID,
                "X-Algolia-API-Key": ALGOLIA_MERCH_API_KEY,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=45) as r:
            hits = json.loads(r.read())["results"][0].get("hits") or []
        for h in hits:
            code = oid_to.get(h.get("objectID") or "")
            if code:
                by[code] = h
        print(f"  ko batch {i // 12 + 1}: {len(hits)}", flush=True)
        time.sleep(0.25)
    # one-by-one for misses
    miss = [c for c in codes if c not in by]
    for code in miss:
        oid = dior_code_to_object_id(code)
        params = urllib.parse.urlencode(
            {
                "query": code.replace("_", ""),
                "hitsPerPage": 8,
                "attributesToRetrieve": "*",
            }
        )
        body = json.dumps(
            {"requests": [{"indexName": ALGOLIA_MERCH_INDEX_KO, "params": params}]}
        ).encode()
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-Algolia-Application-Id": ALGOLIA_MERCH_APP_ID,
                "X-Algolia-API-Key": ALGOLIA_MERCH_API_KEY,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            hits = json.loads(r.read())["results"][0].get("hits") or []
        for h in hits:
            if h.get("objectID") == oid:
                by[code] = h
                break
        time.sleep(0.2)
    return by


def load_products() -> list[dict]:
    by_id: dict[str, dict] = {}
    for path in RAW_PATHS:
        if not path.is_file():
            continue
        raw = json.loads(path.read_text())
        for row in raw.get("products") or []:
            code = row.get("id")
            if not code or not row.get("images"):
                continue
            prev = by_id.get(code)
            if prev:
                cols = list(
                    dict.fromkeys(
                        (prev.get("collections") or []) + (row.get("collections") or [])
                    )
                )
                row = {**prev, **row, "collections": cols}
                if len(prev.get("images") or []) > len(row.get("images") or []):
                    row["images"] = prev["images"]
            by_id[code] = row
    return list(by_id.values())


def build_one(row: dict, h: dict, idx: int) -> dict:
    title_en = (row.get("title") or row["id"]).strip()
    title_ko = (h.get("title") or h.get("name") or "").strip() or title_en
    subtitle_ko = (h.get("subtitle") or "").strip()
    subtitle_en = (row.get("subtitle") or "").strip()
    desc_ko = re.sub(r"\s+", " ", (h.get("description") or "").strip())
    if not desc_ko or en_ratio(desc_ko) > 0.45:
        desc_ko = ((row.get("details") or {}).get("paragraphs") or [""])[0]

    parts: list[str] = []
    if subtitle_ko and is_good_korean(subtitle_ko):
        parts.append(subtitle_ko)
    elif subtitle_en and is_good_korean(subtitle_en):
        parts.append(subtitle_en)
    if desc_ko:
        parts.append(desc_ko)
    description_ko = "\n\n".join(parts)

    images = [img for img in (row.get("images") or []) if img]
    image = images[0]
    sku = str(row.get("id") or slugify(title_en))
    pid = f"di-{slugify(sku)}"
    gbp = row.get("gbpPrice")
    try:
        gbp_f = float(gbp) if gbp is not None else 0.0
    except (TypeError, ValueError):
        gbp_f = 0.0
    price = gbp_to_krw(gbp_f) if gbp_f else 0
    leaf = row.get("leafId") or "di-objects-all"
    collections = list(dict.fromkeys(row.get("collections") or []))
    if leaf not in collections:
        collections.append(leaf)
    color = row.get("color") or {}
    color_ko = None
    if isinstance(h.get("color"), dict):
        color_ko = h["color"].get("label")
    color_ko = color_ko or color.get("label") or "기본"
    tags = ["dior", "디올", "maison"]
    if "di-tableware" in collections or leaf.startswith("di-") and "tableware" in leaf:
        tags += ["tableware", "테이블웨어"]
    if "di-objects" in collections or "object" in leaf or leaf in (
        "di-books",
        "di-notebooks",
        "di-trays",
        "di-leisure",
    ):
        tags += ["objects", "오브젝트"]

    variant = {
        "id": f"{pid}-os",
        "name": "One Size",
        "nameKo": "원 사이즈",
        "sku": str(row.get("sku") or sku),
        "gbpPrice": gbp_f,
        "price": price,
        "image": image,
        "images": images,
        "sourceUrl": row.get("url") or "",
        "inStock": True,
        "colorKey": color.get("code") or "default",
        "colorNameKo": color_ko,
        "size": "OS",
        "diCollections": collections,
    }
    return {
        "id": pid,
        "name": title_en,
        "nameKo": title_ko,
        "brand": "Dior",
        "category": "accessories",
        "subcategory": leaf,
        "diCollections": collections,
        "tags": tags,
        "descriptionKo": description_ko,
        "image": image,
        "images": images,
        "accent": ACCENTS[idx % len(ACCENTS)],
        "gbpPrice": gbp_f,
        "sku": sku,
        "sourceUrl": row.get("url") or "",
        "variants": [variant],
        "storySections": [
            {
                "titleKo": "제품 소개",
                "bodyKo": description_ko or title_ko,
                "image": image,
            }
        ],
    }


def main() -> None:
    products = load_products()
    codes = [p["id"] for p in products]
    print(f"products {len(products)}", flush=True)
    ko = fetch_ko(codes)
    print(f"ko matched {len(ko)}", flush=True)
    out = [build_one(row, ko.get(row["id"]) or {}, i) for i, row in enumerate(products)]
    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    OUT_TS.write_text(
        "/* Auto-generated — do not edit */\n"
        'import type { Product } from "@/data/product-types";\n'
        f"export const diCatalogProducts = {json.dumps(out, ensure_ascii=False)} as Product[];\n"
        f"export const diCatalogGeneratedAt = {json.dumps(datetime.now(timezone.utc).isoformat())};\n"
    )
    good = sum(
        1
        for p in out
        if is_good_korean(p["descriptionKo"]) and is_good_korean(p["nameKo"])
    )
    print(f"wrote {len(out)} good≈{good}", flush=True)


if __name__ == "__main__":
    main()
