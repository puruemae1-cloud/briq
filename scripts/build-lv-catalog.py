#!/usr/bin/env python3
"""Build Briq Louis Vuitton Home (furniture & lighting) catalog from scrape raw.

  python3 scripts/build-lv-catalog.py
  python3 scripts/check-catalog-korean.py --brand lv --fail
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from ko_qa import gtx_translate, is_good_korean  # noqa: E402
from lv_common import gbp_to_krw, slugify  # noqa: E402
from lv_home_ko import apply_phrases  # noqa: E402

RAW = ROOT / "src/data/lv/lv-furniture-catalog-raw.json"
CACHE = ROOT / "src/data/lv/lv-translate-cache.json"
OUT_JSON = ROOT / "src/data/lv/lv-catalog.json"
OUT_TS = ROOT / "src/data/lv/lv-catalog.ts"

ACCENTS = ["#1A2420", "#2C241C", "#243028", "#1E3A32", "#3A2F28", "#2A4038"]


def load_cache() -> dict[str, str]:
    if CACHE.is_file():
        return json.loads(CACHE.read_text())
    return {}


def save_cache(cache: dict[str, str]) -> None:
    CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False) + "\n")


def t(text: str | None, cache: dict[str, str]) -> str:
    if not text:
        return ""
    s = re.sub(r"<[^>]+>", " ", str(text))
    s = re.sub(r"\s+", " ", s).strip()
    if not s:
        return ""
    if s in cache:
        return cache[s]
    polished = apply_phrases(s)
    if is_good_korean(polished):
        cache[s] = polished
        return polished
    try:
        ko = gtx_translate(s, target="ko")
        ko = apply_phrases(ko)
        cache[s] = ko
        time.sleep(0.35)
        return ko
    except Exception:
        cache[s] = polished
        return polished


def js_str(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def build_product(row: dict, cache: dict[str, str], idx: int) -> dict:
    details = row.get("details") or {}
    paras = details.get("paragraphs") or []
    bullets = details.get("bullets") or []
    specs = details.get("specs") or []

    title_en = (row.get("title") or row.get("id") or "").strip()
    title_ko = t(title_en, cache)
    desc_parts = [t(p, cache) for p in paras if p.strip()]
    bullet_ko = [t(b, cache) for b in bullets if b.strip()]
    if bullet_ko:
        desc_parts.extend(f"• {b}" for b in bullet_ko)
    for spec in specs:
        label = t(spec.get("label"), cache)
        val = t(spec.get("value"), cache)
        if label and val:
            desc_parts.append(f"{label}: {val}")

    desc_ko = "\n\n".join(desc_parts).strip()
    images = row.get("images") or []
    image = images[0] if images else "/products/lv-pdp/placeholder.jpg"
    sku = str(row.get("id") or slugify(title_en))
    pid = f"lv-{slugify(sku)}"
    gbp = row.get("gbpPrice")
    try:
        gbp_f = float(gbp) if gbp is not None else 0.0
    except (TypeError, ValueError):
        gbp_f = 0.0
    price = gbp_to_krw(gbp_f) if gbp_f else 0

    leaf = row.get("leafId") or "lv-furniture-lighting-all"
    cols = row.get("collections") or [
        "louis-vuitton",
        "louis-vuitton-accessories",
        "lv-home-lifestyle",
        "lv-furniture-lighting",
        leaf,
    ]

    story_sections = []
    for i, img in enumerate(images[1:6], start=1):
        story_sections.append(
            {
                "titleKo": "디테일",
                "bodyKo": desc_ko if i == 1 else "",
                "image": img,
                "layout": "wide" if i == 1 else "default",
            }
        )

    tech_specs = []
    for spec in specs:
        tech_specs.append(
            {
                "labelKo": t(spec.get("label"), cache),
                "valueKo": t(spec.get("value"), cache),
            }
        )

    return {
        "id": pid,
        "name": title_en,
        "nameKo": title_ko,
        "brand": "Louis Vuitton",
        "price": price,
        "gbpPrice": gbp_f,
        "category": "accessories",
        "subcategory": leaf,
        "lvCollections": cols,
        "tags": ["louis-vuitton", "lv-home", leaf],
        "descriptionKo": desc_ko,
        "image": image,
        "images": images,
        "accent": ACCENTS[idx % len(ACCENTS)],
        "sourceUrl": row.get("url"),
        "sku": sku,
        "storySections": story_sections,
        "techSpecs": tech_specs,
        "registeredAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "variants": [
            {
                "id": f"{pid}-os",
                "name": "One Size",
                "nameKo": "원 사이즈",
                "sku": sku,
                "gbpPrice": gbp_f,
                "price": price,
                "image": image,
                "images": images,
                "sourceUrl": row.get("url"),
                "inStock": True,
                "size": "One Size",
                "lvCollections": cols,
            }
        ],
    }


def main() -> int:
    if not RAW.is_file():
        print(f"Missing {RAW} — run scrape-lv-furniture-lighting.py first", flush=True)
        return 1
    raw = json.loads(RAW.read_text())
    products_in = raw.get("products") or []
    cache = load_cache()
    products = [build_product(row, cache, i) for i, row in enumerate(products_in)]
    save_cache(cache)
    OUT_JSON.write_text(json.dumps(products, indent=2, ensure_ascii=False) + "\n")
    OUT_TS.write_text(
        "import type { Product } from \"@/data/product-types\";\n"
        "import catalog from \"@/data/lv/lv-catalog.json\";\n\n"
        "export const lvCatalogProducts = catalog as Product[];\n"
    )
    print(f"Built {len(products)} LV products → {OUT_JSON.relative_to(ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
