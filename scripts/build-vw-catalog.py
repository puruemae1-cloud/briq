#!/usr/bin/env python3
"""Build Briq Vivienne Westwood catalog from scraped raw files."""
from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from di_common import gbp_to_krw  # noqa: E402
from ko_qa import gtx_translate, has_hangul, is_good_korean  # noqa: E402
from vw_common import clean_html_text, load_json, save_json, slugify  # noqa: E402
from vw_config import vw_raw_paths  # noqa: E402

OUT_JSON = ROOT / "src/data/vw/vw-catalog.json"
OUT_TS = ROOT / "src/data/vw/vw-catalog.ts"
CACHE = ROOT / "src/data/vw/vw-translate-cache.json"

ACCENTS = ["#1A1A1A", "#291f1d", "#302722", "#382e29", "#1f2529", "#2A2028"]
TITLE_MAP = {
    "vivienne westwood": "비비안 웨스트우드",
    "orb": "오브",
    "shoulder bag": "숄더백",
    "handbag": "핸드백",
    "crossbody": "크로스바디",
    "tote": "토트",
    "jacket": "재킷",
    "coat": "코트",
    "dress": "드레스",
    "skirt": "스커트",
    "shirt": "셔츠",
    "trousers": "트라우저",
    "pants": "팬츠",
    "knitwear": "니트웨어",
    "sweater": "스웨터",
    "cardigan": "가디건",
    "shoes": "슈즈",
    "boots": "부츠",
    "sneakers": "스니커즈",
    "earrings": "이어링",
    "necklace": "네클리스",
    "bracelet": "브레이슬릿",
    "ring": "링",
    "watch": "워치",
    "leather": "레더",
    "suede": "스웨이드",
    "wool": "울",
    "cotton": "코튼",
}


def translate_cache() -> dict[str, str]:
    return load_json(CACHE, {})


def tr(text: str | None, cache: dict[str, str], *, allow_remote: bool = True) -> str:
    s = clean_html_text(text or "")
    if not s:
        return ""
    if s in cache and is_good_korean(cache[s]):
        return cache[s]
    if has_hangul(s):
        cache[s] = s
        return s
    fast = os.environ.get("BRIQ_FAST_BUILD") == "1"
    if fast or not allow_remote or len(s) > 120:
        out = clean_title_ko(s) or s
        cache[s] = out
        return out
    try:
        out = gtx_translate(s)
        time.sleep(0.02)
    except Exception:
        out = s
    out = clean_title_ko(out or s)
    if out:
        cache[s] = out
    return out


def clean_title_ko(text: str) -> str:
    out = text.strip()
    for en, ko in TITLE_MAP.items():
        out = re.sub(re.escape(en), ko, out, flags=re.I)
    out = re.sub(r"\bIN\b", "", out, flags=re.I)
    out = re.sub(r"\bTHE\b", "", out, flags=re.I)
    out = re.sub(r"\s{2,}", " ", out).strip(" ;,-")
    return out


def tag_bundle(row: dict) -> list[str]:
    leaf = str(row.get("leafId") or "")
    tags = ["vivienne-westwood", "비비안 웨스트우드"]
    if "-men-" in leaf or leaf == "vw-men":
        tags += ["men", "남성"]
    if "-women-" in leaf or leaf == "vw-women":
        tags += ["women", "여성"]
    if any(x in leaf for x in ["rtw", "clothing", "coats", "jackets", "dresses", "knitwear", "shirts", "trousers", "skirts"]):
        tags += ["rtw", "ready-to-wear"]
    elif "bags" in leaf:
        tags += ["bags", "가방"]
    elif "shoes" in leaf:
        tags += ["shoes", "슈즈"]
    elif "watches" in leaf:
        tags += ["watches", "워치"]
    elif "jewellery" in leaf:
        tags += ["jewellery", "주얼리"]
    else:
        tags += ["accessories", "악세서리"]
    return list(dict.fromkeys(tags))


def extract_detail_lines(row: dict, label: str) -> list[str]:
    details = row.get("details") or []
    for item in details:
        if (item.get("label") or "").strip().lower() == label.lower():
            body = clean_html_text(item.get("body") or "")
            if not body or body.lower() == label.lower():
                continue
            lines = [clean_html_text(x) for x in re.split(r"\n|\.(?=\s+[A-Z])", body)]
            lines = [x.strip() for x in lines if x.strip()]
            if lines:
                return lines
            return [body]
    return []


def size_sort_key(size: str) -> tuple:
    s = str(size or "").strip()
    order = ["XXXS", "XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL", "OS"]
    if s.upper() in order:
        return (0, order.index(s.upper()), s)
    m = re.search(r"(\d+(?:\.\d+)?)", s)
    if m:
        return (1, float(m.group(1)), s)
    return (2, s)


def build_variants(product_id: str, row: dict, price: int) -> list[dict]:
    sizes = sorted({str(x).strip() for x in (row.get("sizes") or []) if str(x).strip()}, key=size_sort_key)
    images = row.get("images") or []
    image = images[0] if images else "/products/vw-pdp/placeholder.jpg"
    if not sizes:
        sizes = ["OS"]
    out = []
    for size in sizes:
        out.append(
            {
                "id": f"{product_id}-sz-{slugify(size, max_len=24)}",
                "name": size,
                "nameKo": "원 사이즈" if size == "OS" else size,
                "sku": row.get("sku") or product_id,
                "gbpPrice": float(row.get("gbpPrice") or 0),
                "price": price,
                "image": image,
                "images": images,
                "sourceUrl": row.get("url") or "",
                "inStock": bool(row.get("availability", True)),
                "size": size,
                "vwCollections": row.get("collections") or [],
            }
        )
    return out


def leaf_to_category(leaf: str) -> str:
    if "bags" in leaf:
        return "bags"
    if "shoes" in leaf:
        return "shoes"
    if "watches" in leaf:
        return "watches"
    if any(x in leaf for x in ["rtw", "clothing", "coats", "jackets", "dresses", "knitwear", "shirts", "trousers", "skirts"]):
        return "luxury"
    return "accessories"


def build_story(description_ko: str, images: list[str], features_ko: list[str]) -> list[dict]:
    sections = [{"titleKo": "제품 소개", "bodyKo": description_ko, "image": images[0] if images else ""}]
    if len(images) > 1 and features_ko:
        sections.append(
            {
                "titleKo": "디테일 & 특징",
                "bodyKo": " · ".join(features_ko[:8]),
                "image": images[min(1, len(images) - 1)],
            }
        )
    if len(images) > 2:
        sections.append(
            {
                "titleKo": "스타일링",
                "bodyKo": "비비안 웨스트우드 공식 이미지로 실루엣과 디테일을 확인할 수 있습니다.",
                "image": images[min(2, len(images) - 1)],
            }
        )
    return sections


def build_product(row: dict, cache: dict[str, str], idx: int) -> dict:
    sku = str(row.get("sku") or row.get("id") or "").strip()
    pid = f"vw-{slugify(sku.replace('.', '-'))}"
    title_en = (row.get("title") or sku).strip()
    title_ko = tr(title_en, cache, allow_remote=True) or clean_title_ko(title_en) or title_en
    gbp = float(row.get("gbpPrice") or 0)
    price = gbp_to_krw(gbp)
    images = row.get("images") or []
    image = images[0] if images else "/products/vw-pdp/placeholder.jpg"
    description_en = extract_detail_lines(row, "Description")
    composition_en = extract_detail_lines(row, "Composition")
    care_en = extract_detail_lines(row, "Care Instructions")
    features_ko = [y for x in (description_en + composition_en)[:10] if (y := tr(x, cache, allow_remote=False))]
    care_ko = [y for x in care_en[:6] if (y := tr(x, cache, allow_remote=False))]
    desc_parts = []
    if features_ko:
        desc_parts.append(" / ".join(features_ko[:3]))
    description_ko = "\n\n".join([x for x in desc_parts if x]).strip() or title_ko
    variants = build_variants(pid, row, price)

    tech_specs = []
    if composition_en:
        tech_specs.append({"labelKo": "소재", "valueKo": tr(composition_en[0], cache)})
    elif description_en:
        tech_specs.append({"labelKo": "디테일", "valueKo": tr(description_en[0], cache)})
    if row.get("categoryLabel"):
        category_ko = clean_title_ko(str(row["categoryLabel"]).replace("/", " / ").title())
        tech_specs.append({"labelKo": "카테고리", "valueKo": category_ko})

    features = []
    for block in (features_ko, care_ko):
        for line in block:
            if line and line not in features:
                features.append(line)

    return {
        "id": pid,
        "name": title_en,
        "nameKo": title_ko,
        "brand": "Vivienne Westwood",
        "category": leaf_to_category(row.get("leafId") or ""),
        "subcategory": row.get("leafId") or "vw-women-bags-all",
        "vwCollections": list(dict.fromkeys(row.get("collections") or [])),
        "tags": tag_bundle(row),
        "descriptionKo": description_ko,
        "image": image,
        "images": images,
        "accent": ACCENTS[idx % len(ACCENTS)],
        "gbpPrice": gbp,
        "sku": sku,
        "sourceUrl": row.get("url") or "",
        "inStock": bool(row.get("availability", True)),
        "variants": variants,
        "storySections": build_story(description_ko, images, features),
        "techSpecs": tech_specs,
        "featuresKo": features,
        "sizeChart": None,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    cache = translate_cache()
    by_id: dict[str, dict] = {}
    rows: list[dict] = []
    raw_paths = vw_raw_paths()
    if not raw_paths:
        raise SystemExit("no vw-*-catalog-raw.json files found")
    for path in raw_paths:
        payload = load_json(path, {"products": []})
        rows.extend(payload.get("products") or [])
    for idx, row in enumerate(rows):
        if not row.get("id"):
            continue
        p = build_product(row, cache, idx)
        by_id[p["id"]] = p
        if (idx + 1) % 10 == 0:
            save_json(CACHE, cache)
            print(f"built {idx+1}/{len(rows)}", flush=True)

    products = list(by_id.values())
    save_json(CACHE, cache)
    save_json(OUT_JSON, products)
    OUT_TS.parent.mkdir(parents=True, exist_ok=True)
    # Thin TS wrapper only — embedding the full catalog in .ts OOMs Vercel builds.
    OUT_TS.write_text(
        "/* Auto-generated by scripts/build-vw-catalog.py — do not edit */\n"
        'import type { Product } from "@/data/product-types";\n'
        'import data from "./vw-catalog.json";\n'
        "\n"
        "/** Vivienne Westwood catalog (JSON import keeps the TS module small for Vercel builds). */\n"
        "export const vwCatalogProducts = data as unknown as Product[];\n"
    )
    print(f"wrote {len(products)} products -> {OUT_JSON} + {OUT_TS}", flush=True)


if __name__ == "__main__":
    main()
