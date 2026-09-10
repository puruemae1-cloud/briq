#!/usr/bin/env python3
"""Build Briq Celine catalog from scraped raw files.

Currently supports the first Celine pipeline: men's ready-to-wear.
"""
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

from celine_config import celine_raw_paths  # noqa: E402
from celine_common import clean_html_text, load_json, save_json, slugify  # noqa: E402
from di_common import gbp_to_krw  # noqa: E402
from ko_qa import gtx_translate, has_hangul, is_good_korean  # noqa: E402

OUT_JSON = ROOT / "src/data/ce/ce-catalog.json"
OUT_TS = ROOT / "src/data/ce/ce-catalog.ts"
CACHE = ROOT / "src/data/ce/ce-translate-cache.json"

ACCENTS = ["#1A1A1A", "#291f1d", "#302722", "#382e29", "#1f2529"]
TITLE_MAP = {
    "celine": "셀린느",
    "shirts": "셔츠",
    "shirt": "셔츠",
    "t-shirt": "티셔츠",
    "t-shirts": "티셔츠",
    "tops": "탑",
    "classic": "클래식",
    "loose": "루즈",
    "oversized": "오버사이즈",
    "overshirt": "오버셔츠",
    "cotton poplin": "코튼 포플린",
    "cotton denim": "코튼 데님",
    "wool": "울",
    "corduroy": "코듀로이",
    "light cotton gabardine": "라이트 코튼 개버딘",
    "pants": "팬츠",
    "shorts": "쇼츠",
    "jacket": "재킷",
    "coat": "코트",
    "leather": "레더",
    "sweatshirt": "스웨트셔츠",
    "knitwear": "니트웨어",
    "jewellery": "주얼리",
    "sunglasses": "선글라스",
    "wallets": "월렛",
    "wallet": "월렛",
    "bags": "가방",
    "bag": "백",
}
LINE_MAP = {
    "100% cotton": "100% 면",
    "100% wool": "100% 울",
    "triomphe embroidery": "트리옹프 자수",
    "classic fit": "클래식 핏",
    "regular fit": "레귤러 핏",
    "loose fit": "루즈 핏",
    "oversized fit": "오버사이즈 핏",
    "shirt collar with collar stays": "카라 스테이가 포함된 셔츠 칼라",
    "buttoned cuffs": "버튼 커프스",
    "7 celine paris-engraved mother-of-pearl buttons": "CELINE PARIS 각인 자개 버튼 7개",
    "1 celine paris-engraved mother-of-pearl button on the cuffs": "커프스 CELINE PARIS 각인 자개 버튼 1개",
    "the classic celine shape fits true to size. we suggest taking your usual size.": "셀린느의 클래식 실루엣 기준 정사이즈로 제안됩니다. 평소 선택하시는 사이즈를 권장합니다.",
    "the item can be washed on a delicate cycle at a maximum temperature of 30°c / 85°f.": "최대 30°C의 섬세 코스로 세탁해 주세요.",
    "only use bleach-free laundry products.": "표백 성분이 없는 세제를 사용해 주세요.",
    "do not tumble dry.": "건조기 사용은 권장되지 않습니다.",
    "maximum ironing temperature: 150°c / 302°f": "다림질 최대 온도는 150°C입니다.",
    "the item can be delicately dry cleaned with hydrocarbons": "하이드로카본 계열로 약하게 드라이클리닝할 수 있습니다.",
    "we suggest taking your usual size.": "평소 선택하시는 사이즈를 권장합니다.",
    "fits true to size.": "정사이즈로 제안됩니다.",
    "classic celine shape fits true to size.": "셀린느의 클래식 실루엣 기준 정사이즈로 제안됩니다.",
    "the classic celine shape fits true to size.": "셀린느의 클래식 실루엣 기준 정사이즈로 제안됩니다.",
}


def translate_cache() -> dict[str, str]:
    return load_json(CACHE, {})


def tr(text: str | None, cache: dict[str, str], *, allow_remote: bool = True) -> str:
    s = clean_html_text(text or "")
    if not s:
        return ""
    low = s.lower()
    if low in LINE_MAP:
        cache[s] = LINE_MAP[low]
        return cache[s]
    if "fits true to size" in low and "usual size" in low:
        cache[s] = "셀린느의 클래식 실루엣 기준 정사이즈로 제안됩니다. 평소 선택하시는 사이즈를 권장합니다."
        return cache[s]
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
    tags = ["celine", "셀린느"]
    if "-men-" in leaf or leaf == "ce-men":
        tags += ["men", "남성"]
    if "-women-" in leaf or leaf == "ce-women":
        tags += ["women", "여성"]
    if any(x in leaf for x in ["shirts", "tshirts", "sweatshirts", "knitwear", "denim", "pants", "tailoring", "coats", "jackets", "leather", "rtw"]):
        tags += ["rtw", "ready-to-wear"]
    elif "bags" in leaf or leaf.endswith("-bag"):
        tags += ["bags", "가방"]
    elif "shoes" in leaf or any(x in leaf for x in ["boots", "sneakers", "loafers", "sandals", "pumps"]):
        tags += ["shoes", "슈즈"]
    else:
        tags += ["accessories", "악세서리"]
    return list(dict.fromkeys(tags))


def extract_lines(row: dict, label: str) -> list[str]:
    details = row.get("details") or []
    for item in details:
        if (item.get("label") or "").strip().lower() == label.lower():
            html = item.get("html") or ""
            body = item.get("body") or ""
            raw = html if html else body
            lines = [
                clean_html_text(x)
                for x in re.split(r"<br\s*/?>|\n", raw, flags=re.I)
            ]
            lines = [x for x in lines if x and not x.lower().startswith("reference :")]
            if lines:
                return lines
            merged = clean_html_text(body)
            return [merged] if merged else []
    return []


def build_size_chart(row: dict) -> dict | None:
    guide = row.get("sizeGuide") or {}
    headers = guide.get("headers") or []
    rows = guide.get("rows") or []
    if not headers or not rows:
        return None
    title = headers[1] if len(headers) > 1 else "사이즈 가이드"
    title_ko = clean_title_ko(title.upper().title()) or title
    return {
        "id": f"ce-{slugify(title)}",
        "titleKo": f"셀린느 {title_ko} 사이즈 가이드",
        "noteKo": "공식 셀린느 사이즈 가이드를 기준으로 정리했습니다.",
        "headers": headers,
        "rows": rows,
    }


def size_sort_key(size: str) -> tuple:
    s = str(size or "").strip()
    order = ["XXXS", "XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL"]
    if s.upper() in order:
        return (0, order.index(s.upper()), s)
    m = re.search(r"(\d+(?:\.\d+)?)", s)
    if m:
        return (1, float(m.group(1)), s)
    return (2, s)


def build_variants(product_id: str, row: dict, price: int) -> list[dict]:
    sizes = sorted({str(x).strip() for x in (row.get("sizes") or []) if str(x).strip()}, key=size_sort_key)
    images = row.get("images") or []
    image = images[0] if images else "/products/ce-pdp/placeholder.jpg"
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
                "ceCollections": row.get("collections") or [],
            }
        )
    return out


def leaf_to_category(leaf: str) -> str:
    if "bags" in leaf:
        return "bags"
    if "shoes" in leaf or any(x in leaf for x in ["boots", "sneakers", "loafers", "sandals", "pumps"]):
        return "shoes"
    if any(x in leaf for x in ["shirts", "tshirts", "sweatshirts", "knitwear", "denim", "pants", "tailoring", "coats", "jackets", "leather", "rtw"]):
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
                "bodyKo": "셀린느 공식 이미지로 실루엣과 소재의 분위기를 확인할 수 있습니다.",
                "image": images[min(2, len(images) - 1)],
            }
        )
    return sections


def build_product(row: dict, cache: dict[str, str], idx: int) -> dict:
    sku = str(row.get("sku") or row.get("id") or "").strip()
    pid = f"ce-{slugify(sku.replace('.', '-'))}"
    title_en = (row.get("title") or sku).strip()
    title_ko = tr(title_en, cache, allow_remote=True) or clean_title_ko(title_en) or title_en
    gbp = float(row.get("gbpPrice") or 0)
    price = gbp_to_krw(gbp)
    images = row.get("images") or []
    image = images[0] if images else "/products/ce-pdp/placeholder.jpg"
    details_en = extract_lines(row, "DETAILS")
    care_en = extract_lines(row, "CARE AND MAINTENANCE")
    fit_en = extract_lines(row, "Size and fit")
    features_ko = [y for x in details_en[:10] if (y := tr(x, cache, allow_remote=False))]
    care_ko = [y for x in care_en[:6] if (y := tr(x, cache, allow_remote=False))]
    fit_ko = [y for x in fit_en[:4] if (y := tr(x, cache, allow_remote=False))]
    desc_parts = []
    if features_ko:
        desc_parts.append(" / ".join(features_ko[:3]))
    if fit_ko:
        desc_parts.append(" ".join(fit_ko[:1]))
    description_ko = "\n\n".join([x for x in desc_parts if x]).strip() or title_ko
    size_chart = build_size_chart(row)
    variants = build_variants(pid, row, price)

    tech_specs = []
    if details_en:
        tech_specs.append({"labelKo": "디테일", "valueKo": tr(details_en[0], cache)})
    if row.get("categoryLabel"):
        category_ko = clean_title_ko(str(row["categoryLabel"]).replace("/", " / ").title())
        tech_specs.append({"labelKo": "카테고리", "valueKo": category_ko})

    features = []
    for block in (features_ko, care_ko, fit_ko):
        for line in block:
            if line and line not in features:
                features.append(line)

    return {
        "id": pid,
        "name": title_en,
        "nameKo": title_ko,
        "brand": "Celine",
        "category": leaf_to_category(row.get("leafId") or ""),
        "subcategory": row.get("leafId") or "ce-men-rtw-all",
        "ceCollections": list(dict.fromkeys(row.get("collections") or [])),
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
        "sizeChart": size_chart,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    cache = translate_cache()
    by_id: dict[str, dict] = {}
    rows: list[dict] = []
    raw_paths = celine_raw_paths()
    if not raw_paths:
        raise SystemExit("no ce-*-catalog-raw.json files found")
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
        "/* Auto-generated by scripts/build-ce-catalog.py — do not edit */\n"
        'import type { Product } from "@/data/product-types";\n'
        'import data from "./ce-catalog.json";\n'
        "\n"
        "/** Celine catalog (JSON import keeps the TS module small for Vercel builds). */\n"
        "export const ceCatalogProducts = data as unknown as Product[];\n"
    )
    print(f"wrote {len(products)} products -> {OUT_JSON} + {OUT_TS}", flush=True)


if __name__ == "__main__":
    main()
