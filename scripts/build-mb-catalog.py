#!/usr/bin/env python3
"""Build Briq Mulberry catalog from scraped raw leaf files."""
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
from mulberry_common import RAW_DIR, load_json, save_json, slugify  # noqa: E402

OUT_JSON = ROOT / "src/data/mb/mb-catalog.json"
OUT_TS = ROOT / "src/data/mb/mb-catalog.ts"
CACHE = ROOT / "src/data/mb/mb-translate-cache.json"

TITLE_MAP = {
    "mulberry": "멀버리",
    "clutch": "클러치",
    "shoulder bag": "숄더백",
    "crossbody": "크로스바디",
    "tote": "토트",
    "bucket": "버킷",
    "backpack": "백팩",
    "satchel": "사첼",
    "messenger": "메신저",
    "briefcase": "브리프케이스",
    "holdall": "홀드올",
    "wallet": "월렛",
    "purse": "퍼스",
    "card holder": "카드홀더",
    "keyring": "키링",
    "sunglasses": "선글라스",
    "leather": "레더",
    "nappa": "나파",
    "suede": "스웨이드",
    "classic grain": "클래식 그레인",
    "heavy grain": "헤비 그레인",
    "small classic grain": "스몰 클래식 그레인",
    "high shine": "하이 샤인",
    "scotchgrain": "스카치그레인",
    "shiny buffalo": "샤이니 버팔로",
    "mini": "미니",
    "small": "스몰",
    "micro": "마이크로",
    "large": "라지",
    "medium": "미디엄",
    "top handle": "탑 핸들",
    "camera bag": "카메라 백",
    "darley": "달리",
    "lily": "릴리",
    "bayswater": "베이즈워터",
    "alexa": "알렉사",
    "amberley": "앰벌리",
    "roxanne": "록산느",
    "iris": "아이리스",
    "hackney": "해크니",
    "islington": "이즐링턴",
    "antony": "안토니",
    "stevie": "스티비",
    "cosmetic pouch": "코스메틱 파우치",
    "pouch": "파우치",
}


def clean_title_ko(text: str) -> str:
    out = (text or "").strip()
    for en, ko in sorted(TITLE_MAP.items(), key=lambda kv: -len(kv[0])):
        out = re.sub(rf"(?<![A-Za-z0-9]){re.escape(en)}(?![A-Za-z0-9])", ko, out, flags=re.I)
    out = re.sub(r"\s{2,}", " ", out).strip(" ;,-")
    return out


def tr(text: str, cache: dict[str, str], *, allow_remote: bool = True, prose: bool = False) -> str:
    s = (text or "").strip()
    if not s:
        return ""
    if s in cache and (is_good_korean(cache[s]) or prose):
        return cache[s]
    if has_hangul(s) and is_good_korean(s):
        cache[s] = s
        return s
    fast = os.environ.get("BRIQ_FAST_BUILD") == "1"
    if prose:
        # Full-sentence copy — never run fashion TITLE_MAP (creates EN/KO hybrids).
        if fast or not allow_remote:
            cache[s] = s
            return s
        try:
            out = gtx_translate(s)
            time.sleep(0.05)
        except Exception:
            out = s
        cache[s] = out or s
        return cache[s]
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
    if out:
        cache[s] = out
    return out


def style_key(title: str, colour: str) -> str:
    t = (title or "").strip()
    c = (colour or "").strip()
    if c and t.lower().endswith(c.lower()):
        t = t[: -len(c)].strip(" -|")
    # Strip colour-like trailing fragments from og title (usually style only)
    return slugify(t or title, max_len=48)


def build_size_chart(row: dict) -> dict | None:
    raw = row.get("sizeChart") or {}
    headers = raw.get("headers") or []
    rows = raw.get("rows") or []
    if not headers or not rows:
        return None
    return {
        "id": "mb-size",
        "titleKo": "사이즈 가이드",
        "noteKo": "멀버리 공식 사이즈 가이드를 기준으로 합니다.",
        "headers": headers,
        "rows": rows,
    }


def build_story(desc_ko: str, details_ko: str, dims: list[str], images: list[str]) -> list[dict]:
    sections = []
    if desc_ko:
        sections.append(
            {
                "titleKo": "제품 소개",
                "bodyKo": desc_ko,
                "image": images[0] if images else "",
            }
        )
    if details_ko:
        sections.append(
            {
                "titleKo": "디테일 & 특징",
                "bodyKo": details_ko,
                "image": images[1] if len(images) > 1 else (images[0] if images else ""),
            }
        )
    if dims:
        sections.append(
            {
                "titleKo": "사이즈 & 디멘션",
                "bodyKo": " · ".join(dims[:12]),
                "image": images[2] if len(images) > 2 else "",
            }
        )
    if not sections and images:
        sections.append({"titleKo": "제품 소개", "bodyKo": "멀버리 공식 제품입니다.", "image": images[0]})
    return sections


def load_all_rows() -> list[dict]:
    rows: list[dict] = []
    if not RAW_DIR.is_dir():
        return rows
    for path in sorted(RAW_DIR.glob("*-catalog-raw.json")):
        payload = load_json(path, {"products": []})
        for p in payload.get("products") or []:
            p = dict(p)
            p["_rawFile"] = path.name
            rows.append(p)
    return rows


def group_rows(rows: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for row in rows:
        key = style_key(row.get("title") or "", row.get("colour") or "")
        groups.setdefault(key, []).append(row)
    return groups


def build_product(style: str, colourways: list[dict], cache: dict[str, str], idx: int) -> dict:
    lead = colourways[0]
    title_en = (lead.get("title") or style).strip()
    # Prefer shorter style name without colour
    for row in colourways:
        t = (row.get("title") or "").strip()
        c = (row.get("colour") or "").strip()
        if c and t.lower().endswith(c.lower()):
            title_en = t[: -len(c)].strip(" -|") or title_en
            break
        if t and len(t) < len(title_en):
            title_en = t

    title_ko = tr(title_en, cache, allow_remote=True)
    if not is_good_korean(title_ko):
        title_ko = clean_title_ko(title_en) or title_ko

    category = lead.get("category") or "bags"
    collections: list[str] = []
    for row in colourways:
        for c in row.get("collections") or []:
            if c not in collections:
                collections.append(c)

    variants = []
    for row in colourways:
        colour = (row.get("colour") or "기본").strip() or "기본"
        colour_ko = tr(colour, cache, allow_remote=False) or clean_title_ko(colour) or colour
        gbp = float(row.get("gbpPrice") or 0)
        price = gbp_to_krw(gbp)
        images = row.get("localImages") or []
        if not images:
            # keep remote as last resort — prefer local CDN paths
            rem = row.get("images") or []
            images = rem[:1]
        image = images[0] if images else "/products/mb-pdp/placeholder.jpg"
        sizes = [str(x).strip() for x in (row.get("sizes") or []) if str(x).strip()]
        # Bags/SLG rarely expose true size grids on Mulberry; ignore nav noise.
        real_sizes = []
        for s in sizes:
            su = s.upper()
            if su in {"OS", "ONESIZE", "ONE SIZE", "XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL"}:
                real_sizes.append("OS" if "ONE" in su or su == "OS" else su)
            elif re.fullmatch(r"\d{2}(?:\.\d)?", s):
                real_sizes.append(s)
        if not real_sizes:
            real_sizes = ["OS"]
        sizes = list(dict.fromkeys(real_sizes))
        color_key = slugify(colour, max_len=40)
        vid_base = f"mb-{slugify(row.get('id') or row.get('sku') or colour, max_len=48)}"
        for size in sizes:
            variants.append(
                {
                    "id": f"{vid_base}-sz-{slugify(size, max_len=16)}",
                    "name": f"{colour} / {size}",
                    "nameKo": f"{colour_ko}" if size == "OS" else f"{colour_ko} / {size}",
                    "sku": row.get("sku") or vid_base,
                    "gbpPrice": gbp,
                    "price": price,
                    "image": image,
                    "images": images,
                    "sourceUrl": row.get("url") or "",
                    "inStock": bool(row.get("availability", True)),
                    "colorKey": color_key,
                    "colorNameKo": colour_ko,
                    "size": size,
                    "mbCollections": list(row.get("collections") or collections),
                }
            )

    # Lead media from cheapest in-stock colourway
    priced = sorted(variants, key=lambda v: (not v["inStock"], v["price"] or 0))
    lead_v = priced[0] if priced else None
    images = (lead_v or {}).get("images") or []
    image = (lead_v or {}).get("image") or "/products/mb-pdp/placeholder.jpg"
    gbp = float((lead_v or {}).get("gbpPrice") or 0)
    price = int((lead_v or {}).get("price") or gbp_to_krw(gbp))

    desc_en = (lead.get("description") or "").strip()
    details_en = (lead.get("details") or "").strip()
    # Prefer longer description across colourways
    for row in colourways:
        if len((row.get("description") or "")) > len(desc_en):
            desc_en = row["description"]
        if len((row.get("details") or "")) > len(details_en):
            details_en = row["details"]

    desc_ko = tr(desc_en[:1200], cache, allow_remote=True, prose=True) if desc_en else ""
    details_ko = tr(details_en[:1200], cache, allow_remote=True, prose=True) if details_en else ""
    dims = []
    for row in colourways:
        for d in row.get("dims") or []:
            if d not in dims:
                dims.append(d)
    dims_ko = [tr(d, cache, allow_remote=False, prose=True) or d for d in dims[:12]]

    features = []
    if details_ko:
        features = [x.strip() for x in re.split(r"[·\n\|]", details_ko) if x.strip()][:10]
    if dims_ko:
        features.extend(dims_ko[:4])

    size_chart = None
    for row in colourways:
        size_chart = build_size_chart(row)
        if size_chart:
            break

    pid = f"mb-{style}"
    tech = []
    if dims_ko:
        tech.append({"labelKo": "디멘션", "valueKo": " · ".join(dims_ko[:6])})
    if colourways:
        tech.append({"labelKo": "컬러웨이", "valueKo": f"{len(colourways)}가지"})

    return {
        "id": pid,
        "name": title_en,
        "nameKo": title_ko,
        "brand": "Mulberry",
        "category": category,
        "subcategory": (collections[2] if len(collections) > 2 else (collections[-1] if collections else "mulberry-bags")),
        "mbCollections": collections,
        "tags": ["mulberry", "멀버리", category],
        "descriptionKo": desc_ko or details_ko or title_ko,
        "image": image,
        "images": images or [image],
        "accent": ["#1A1A1A", "#2c241e", "#3a322c", "#241f1c"][idx % 4],
        "gbpPrice": gbp,
        "sku": lead.get("sku") or pid,
        "sourceUrl": lead.get("url") or "",
        "variants": variants,
        "storySections": build_story(desc_ko, details_ko, dims_ko, images or [image]),
        "techSpecs": tech,
        "featuresKo": features,
        "sizeChart": size_chart,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    cache = load_json(CACHE, {})
    rows = load_all_rows()
    if not rows:
        print("no raw rows — writing empty catalog", flush=True)
        products: list[dict] = []
    else:
        groups = group_rows(rows)
        products = []
        for idx, (style, colourways) in enumerate(sorted(groups.items(), key=lambda x: x[0])):
            products.append(build_product(style, colourways, cache, idx))
            if (idx + 1) % 10 == 0:
                save_json(CACHE, cache)
                print(f"built {idx+1}/{len(groups)}", flush=True)

    save_json(CACHE, cache)
    save_json(OUT_JSON, products)
    OUT_TS.write_text(
        "/* Auto-generated by scripts/build-mb-catalog.py — do not edit */\n"
        'import type { Product } from "@/data/product-types";\n'
        'import data from "./mb-catalog.json";\n'
        "\n"
        "/** Mulberry catalog (JSON import keeps the TS module small for Vercel builds). */\n"
        "export const mbCatalogProducts = data as unknown as Product[];\n"
    )
    print(f"wrote {len(products)} products -> {OUT_JSON}", flush=True)


if __name__ == "__main__":
    main()
