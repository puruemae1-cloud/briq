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


def tr(
    text: str | None,
    cache: dict[str, str],
    *,
    allow_remote: bool = True,
    prose: bool = False,
) -> str:
    """Translate copy. Titles may use TITLE_MAP; PDP prose must never (avoids EN/KO hybrids)."""
    s = clean_html_text(text or "")
    if not s:
        return ""
    if s in cache and is_good_korean(cache[s]):
        return cache[s]
    if has_hangul(s) and is_good_korean(s):
        cache[s] = s
        return s
    fast = os.environ.get("BRIQ_FAST_BUILD") == "1"
    if prose:
        # Full-sentence PDP copy — never glossary-swap (creates "Featu링" / "워치 is" hybrids).
        if fast or not allow_remote:
            # Keep EN rather than caching a hybrid; weekly sync without FAST will translate.
            return s
        try:
            out = gtx_translate(s)
            time.sleep(0.05)
        except Exception:
            out = s
        if out and is_good_korean(out):
            cache[s] = out
            return out
        return out or s
    dicted = clean_title_ko(s)
    if fast or not allow_remote:
        cache[s] = dicted or s
        return cache[s]
    try:
        out = gtx_translate(s)
        time.sleep(0.05)
        out = clean_title_ko(out or dicted or s)
    except Exception:
        out = dicted or s
    if out and is_good_korean(out):
        cache[s] = out
    elif out:
        # Title-style leftovers (e.g. "Little Seymour 워치") are acceptable for nameKo.
        cache[s] = out
    return out or s


def clean_title_ko(text: str) -> str:
    out = text.strip()
    for en, ko in sorted(TITLE_MAP.items(), key=lambda kv: -len(kv[0])):
        out = re.sub(rf"\b{re.escape(en)}\b", ko, out, flags=re.I)
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
            # Keep description/care/composition as whole bodies so EN→KO prose
            # stays coherent (sentence-splitting produced untranslated hybrids).
            if label.lower() in {"description", "care instructions", "composition"}:
                return [body]
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
    # One colourway per SKU — shared colorKey so PDP size chips aren't
    # mis-rendered as duplicate colour image swatches.
    color = row.get("color") if isinstance(row.get("color"), dict) else {}
    color_label = str((color or {}).get("label") or (color or {}).get("label_int") or "").strip()
    color_key = product_id
    color_name_ko = color_label if color_label else "기본"
    size_stock = row.get("sizeStock") if isinstance(row.get("sizeStock"), dict) else {}
    out = []
    for size in sizes:
        stock = size_stock.get(size)
        if stock is None:
            stock = size_stock.get(size.upper())
        in_stock = bool(row.get("availability", True)) if stock is None else bool(stock)
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
                "inStock": in_stock,
                "colorKey": color_key,
                "colorNameKo": color_name_ko,
                "size": size,
                "vwCollections": row.get("collections") or [],
            }
        )
    return out


def leaf_to_category(leaf: str) -> str:
    """Map VW leaf id → Briq shop category.

    Bag style leaves use names like crossbody/totes/clutches (no 'bags' substring),
    so a naive `'bags' in leaf` check mis-filed them as accessories and hid them
    from /shop?category=bags&sub=vivienne-westwood-bags.
    """
    l = (leaf or "").lower()
    if any(
        m in l
        for m in (
            "bags",
            "handbag",
            "crossbody",
            "clutch",
            "tote",
            "backpack",
            "satchel",
            "shoulder",
        )
    ):
        return "bags"
    if "shoes" in l or "boot" in l or "flat" in l or "pump" in l or "sandal" in l or "trainer" in l or "platform" in l:
        return "shoes"
    if "watch" in l:
        return "watches"
    if any(
        x in l
        for x in (
            "rtw",
            "clothing",
            "coats",
            "jackets",
            "dresses",
            "knitwear",
            "shirts",
            "trousers",
            "skirts",
            "corset",
            "sweat",
        )
    ):
        return "luxury"
    return "accessories"


def _pick_ko_field(prev_val, new_val):
    """Prefer natural Korean over longer leftover English (weekly re-scrape safety)."""
    prev_s = str(prev_val or "").strip()
    new_s = str(new_val or "").strip()
    prev_ok = bool(prev_s) and is_good_korean(prev_s)
    new_ok = bool(new_s) and is_good_korean(new_s)
    if new_ok and not prev_ok:
        return new_val
    if prev_ok and not new_ok:
        return prev_val
    if new_ok and prev_ok:
        # Both OK — keep the richer copy.
        return new_val if len(new_s) >= len(prev_s) else prev_val
    # Neither is good Korean — take the rebuild result so retries can overwrite EN.
    return new_val if new_s else prev_val


def _merge_vw_product(prev: dict | None, new: dict) -> dict:
    """Keep the richer row; union collections; never downgrade bags → accessories."""
    if not prev:
        return new
    out = dict(new)
    cols = list(dict.fromkeys([*(prev.get("vwCollections") or []), *(new.get("vwCollections") or [])]))
    out["vwCollections"] = cols
    # Prefer bags category if either side is bags (leaf mis-order safety).
    if prev.get("category") == "bags" or new.get("category") == "bags":
        out["category"] = "bags"
    # Prefer the bags-*all / more specific bag leaf as subcategory when available.
    prev_sub = str(prev.get("subcategory") or "")
    new_sub = str(new.get("subcategory") or "")
    if prev_sub.endswith("bags-all") and not new_sub.endswith("bags-all"):
        out["subcategory"] = prev_sub
    # Keep the longer image gallery when replacing a thinner row.
    if len(prev.get("images") or []) > len(new.get("images") or []):
        out["images"] = prev["images"]
        out["image"] = prev.get("image") or out.get("image")
    # Korean PDP copy: never keep longer English over a good translation.
    # Weekly scrape often rebuilds EN prose (gtx flakes / BRIQ_FAST_BUILD); keep
    # prior KO for description, story, features, and techSpecs together.
    picked = _pick_ko_field(prev.get("descriptionKo"), new.get("descriptionKo"))
    out["descriptionKo"] = picked
    if picked == prev.get("descriptionKo") and not is_good_korean(str(new.get("descriptionKo") or "")):
        out["storySections"] = prev.get("storySections") or out.get("storySections")
        out["featuresKo"] = prev.get("featuresKo") or out.get("featuresKo")
        out["techSpecs"] = prev.get("techSpecs") or out.get("techSpecs")
        # Prefer KO title when rebuild left English product names.
        out["nameKo"] = _pick_ko_field(prev.get("nameKo"), new.get("nameKo"))
    elif is_good_korean(str(new.get("descriptionKo") or "")):
        out["storySections"] = new.get("storySections") or out.get("storySections")
        out["featuresKo"] = new.get("featuresKo") or out.get("featuresKo")
        out["techSpecs"] = new.get("techSpecs") or out.get("techSpecs")
    else:
        # Neither side has good descriptionKo — still prefer any good KO fragments.
        out["featuresKo"] = _pick_ko_list(prev.get("featuresKo"), new.get("featuresKo"))
        out["techSpecs"] = _pick_ko_tech_specs(prev.get("techSpecs"), new.get("techSpecs"))
        out["nameKo"] = _pick_ko_field(prev.get("nameKo"), new.get("nameKo"))
    # Prefer richer size variants (never keep OS-only when multi-size exists).
    prev_vars = prev.get("variants") or []
    new_vars = out.get("variants") or []
    def _size_richness(vs: list) -> int:
        sizes = {str(v.get("size") or v.get("name") or "") for v in vs}
        sizes.discard("")
        if sizes <= {"OS", "원 사이즈"}:
            return 0
        return len(sizes)
    if _size_richness(prev_vars) > _size_richness(new_vars):
        out["variants"] = prev_vars
    if prev.get("sizeChart") and not out.get("sizeChart"):
        out["sizeChart"] = prev["sizeChart"]
    return out


def _pick_ko_list(prev_val, new_val):
    prev_list = [str(x).strip() for x in (prev_val or []) if str(x).strip()]
    new_list = [str(x).strip() for x in (new_val or []) if str(x).strip()]
    prev_ok = bool(prev_list) and all(is_good_korean(x) for x in prev_list)
    new_ok = bool(new_list) and all(is_good_korean(x) for x in new_list)
    if new_ok and not prev_ok:
        return new_val
    if prev_ok and not new_ok:
        return prev_val
    return new_val if new_list else prev_val


def _pick_ko_tech_specs(prev_val, new_val):
    def values(specs) -> list[str]:
        out = []
        for spec in specs or []:
            if isinstance(spec, dict):
                v = str(spec.get("valueKo") or "").strip()
                if v:
                    out.append(v)
        return out

    prev_vals = values(prev_val)
    new_vals = values(new_val)
    prev_ok = bool(prev_vals) and all(is_good_korean(x) for x in prev_vals)
    new_ok = bool(new_vals) and all(is_good_korean(x) for x in new_vals)
    if new_ok and not prev_ok:
        return new_val
    if prev_ok and not new_ok:
        return prev_val
    return new_val if new_vals else prev_val


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
    features_ko = [
        y
        for x in (description_en + composition_en)[:10]
        if (y := tr(x, cache, allow_remote=True, prose=True))
    ]
    care_ko = [y for x in care_en[:6] if (y := tr(x, cache, allow_remote=True, prose=True))]
    desc_parts = []
    if features_ko:
        desc_parts.append(" / ".join(features_ko[:3]))
    description_ko = "\n\n".join([x for x in desc_parts if x]).strip() or title_ko
    variants = build_variants(pid, row, price)

    tech_specs = []
    if composition_en:
        tech_specs.append(
            {"labelKo": "소재", "valueKo": tr(composition_en[0], cache, allow_remote=True, prose=True)}
        )
    elif description_en:
        tech_specs.append(
            {"labelKo": "디테일", "valueKo": tr(description_en[0], cache, allow_remote=True, prose=True)}
        )
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
        "sizeChart": row.get("sizeChart") if isinstance(row.get("sizeChart"), dict) else None,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    cache = translate_cache()
    # Drop hybrid glossary leftovers so prose can be re-translated cleanly.
    purged = 0
    for k, v in list(cache.items()):
        if not isinstance(v, str):
            continue
        if len(v) >= 40 and not is_good_korean(v):
            del cache[k]
            purged += 1
    if purged:
        print(f"purged {purged} hybrid cache entries", flush=True)

    by_id: dict[str, dict] = {}
    rows: list[dict] = []
    raw_paths = vw_raw_paths()
    leaf_filter = (os.environ.get("VW_LEAF_FILTER") or "").strip()
    if not raw_paths:
        raise SystemExit("no vw-*-catalog-raw.json files found")
    for path in raw_paths:
        if leaf_filter and leaf_filter not in path.name:
            continue
        payload = load_json(path, {"products": []})
        rows.extend(payload.get("products") or [])
    if leaf_filter and not rows:
        raise SystemExit(f"no rows for VW_LEAF_FILTER={leaf_filter!r}")

    # When filtering a leaf, merge into existing catalog so other families stay intact.
    if leaf_filter and OUT_JSON.is_file():
        for p in load_json(OUT_JSON, []):
            if isinstance(p, dict) and p.get("id"):
                by_id[p["id"]] = p

    for idx, row in enumerate(rows):
        if not row.get("id"):
            continue
        p = build_product(row, cache, idx)
        by_id[p["id"]] = _merge_vw_product(by_id.get(p["id"]), p)
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
