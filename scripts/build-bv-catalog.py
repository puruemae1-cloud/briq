#!/usr/bin/env python3
"""Build Bottega Veneta catalogue from scraped raw JSON.

Pricing: KRW = round_만원(GBP × 2100 × 1.05 × 1.15) — same as Gucci.
"""
from __future__ import annotations

import socket
socket.setdefaulttimeout(10)

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from bv_common import html_to_text, load_json, save_json, slugify, sort_sizes  # noqa: E402
from bv_config import (  # noqa: E402
    HUB_ORDER,
    HUBS_BY_ID,
    OUT_JSON,
    OUT_TS,
    RAW_DIR,
    TRANSLATE_CACHE,
)
from di_common import gbp_to_krw  # noqa: E402
from ko_qa import ensure_official_english_name, translate_en_to_ko  # noqa: E402


def _t(text: str, cache: dict[str, str]) -> str:
    import os
    offline = os.environ.get("BV_OFFLINE_KO", "").strip() in {"1", "true", "yes"}
    return translate_en_to_ko(text, cache, offline=offline) if text else ""


def category_for_hub(hub_id: str) -> str:
    return HUBS_BY_ID[hub_id]["category"]


def build_description_ko(raw: dict, cache: dict[str, str]) -> tuple[str, list[str], list[dict]]:
    parts: list[str] = []
    features: list[str] = []
    stories: list[dict] = []

    compact = str(raw.get("compactedLongDesc") or "").strip()
    if compact:
        parts.append(_t(compact, cache))
        stories.append({"titleKo": "제품 소개", "bodyKo": _t(compact, cache), "image": ""})

    for b in raw.get("longDescription") or []:
        ko = _t(str(b), cache)
        if ko:
            features.append(ko)
            parts.append(ko)

    for b in raw.get("shortDescription") or []:
        ko = _t(str(b), cache)
        if ko and ko not in features:
            features.append(ko)

    size_model = str(raw.get("sizeModel") or "").strip()
    if size_model:
        ko = _t(size_model, cache)
        parts.append(ko)
        stories.append({"titleKo": "사이즈 & 모델", "bodyKo": ko, "image": ""})

    material = str(raw.get("composition") or raw.get("material") or "").strip()
    if material:
        ko = _t(material, cache)
        parts.append(ko)
        features.append(ko)

    care = str(raw.get("productCare") or "").strip()
    if care:
        # Keep care concise
        care_short = care.split("\n\n")[0][:600]
        ko = _t(care_short, cache)
        stories.append({"titleKo": "케어 가이드", "bodyKo": ko, "image": ""})

    desc = "\n".join(p for p in parts if p).strip()
    return desc, features[:12], stories


def build_variants(raw: dict, images: list[str], cache: dict[str, str]) -> list[dict]:
    smc = str(raw.get("id") or raw.get("sku") or "")
    color = str(raw.get("color") or "").strip() or "기본"
    color_ko = _t(color, cache) if color != "기본" else "기본"
    color_key = slugify(color)
    base_gbp = float(raw.get("gbpPrice") or 0)
    sizes = sort_sizes(list(raw.get("sizes") or []))
    cols = list(raw.get("collections") or [])
    source = raw.get("link") or raw.get("url") or ""

    usable = [
        s
        for s in sizes
        if str(s.get("value") or "").upper() not in {"", "TU"}
    ]
    multi = any(
        str(s.get("value") or "").upper() not in {"OS", "U", "ONE SIZE", "ONESIZE"}
        for s in usable
    )

    variants: list[dict] = []
    if multi and usable:
        for s in usable:
            val = str(s.get("value") or "")
            disp = str(s.get("displayValue") or val)
            if val.upper() in {"U", "OS"} and disp.upper() in {"U", "OS"}:
                disp = "One Size"
            sgbp = float(s.get("gbpPrice") or base_gbp or 0)
            if sgbp <= 0:
                continue
            sprice = gbp_to_krw(sgbp)
            list_gbp = s.get("listGbpPrice")
            compare = gbp_to_krw(float(list_gbp)) if list_gbp else None
            variants.append(
                {
                    "id": f"bv-{slugify(smc)}-{slugify(val)}",
                    "name": disp,
                    "nameKo": disp,
                    "size": disp,
                    "sku": str(s.get("id") or smc),
                    "gbpPrice": sgbp,
                    "price": sprice,
                    "compareAtPrice": compare if compare and compare > sprice else None,
                    "image": images[0] if images else "",
                    "images": images,
                    "sourceUrl": source,
                    "inStock": bool(s.get("inStock", True)),
                    "colorKey": color_key,
                    "colorNameKo": color_ko,
                    "bvCollections": cols,
                }
            )
    else:
        if base_gbp <= 0:
            return []
        variants.append(
            {
                "id": f"bv-{slugify(smc)}",
                "name": color_ko,
                "nameKo": color_ko,
                "size": "One Size",
                "sku": smc,
                "gbpPrice": base_gbp,
                "price": gbp_to_krw(base_gbp),
                "image": images[0] if images else "",
                "images": images,
                "sourceUrl": source,
                "inStock": bool(raw.get("inStock", True)),
                "colorKey": color_key,
                "colorNameKo": color_ko,
                "bvCollections": cols,
            }
        )
    return variants


def translate_size_chart(guide: dict | None, cache: dict[str, str]) -> dict | None:
    if not isinstance(guide, dict):
        return None
    headers = list(guide.get("headers") or [])
    rows = list(guide.get("rows") or [])
    if len(headers) < 2 or len(rows) < 1:
        return None
    title = str(guide.get("titleKo") or "사이즈 가이드")
    note = str(guide.get("noteKo") or "")
    # title/note may still be English from scrape
    title_ko = _t(title, cache) if title else "사이즈 가이드"
    note_ko = _t(note, cache) if note else "보테가 베네타 공홈 사이즈 가이드 기준입니다."
    headers_ko = []
    for h in headers:
        if h in {"BV", "UK", "US", "KR", "EU", "IT", "FR"}:
            headers_ko.append(h)
        else:
            headers_ko.append(_t(h, cache) or h)
    return {
        "id": str(guide.get("id") or "bv-size"),
        "titleKo": title_ko,
        "noteKo": note_ko,
        "headers": headers_ko,
        "rows": rows,
    }


def build_product(raw: dict, hub_id: str, cache: dict[str, str], now: str) -> dict | None:
    smc = str(raw.get("id") or raw.get("sku") or "")
    if not smc or raw.get("pdpError"):
        return None
    images = list(raw.get("localImages") or [])
    if not images:
        return None
    variants = build_variants(raw, images, cache)
    if not variants:
        return None

    name = str(raw.get("name") or smc)
    name_ko = _t(name, cache)
    desc_ko, features_ko, stories = build_description_ko(raw, cache)
    if not desc_ko:
        desc_ko = name_ko

    # Attach first images to story sections
    for i, sec in enumerate(stories):
        if not sec.get("image") and images:
            sec["image"] = images[min(i, len(images) - 1)]

    chart = translate_size_chart(raw.get("sizeGuide"), cache)
    cols = list(raw.get("collections") or [])
    cat = category_for_hub(hub_id)
    # Prefer last leaf id as subcategory
    sub = cols[-1] if cols else hub_id

    prod = {
        "id": f"bv-{slugify(smc)}",
        "brand": "보테가 베네타",
        "name": name,
        "nameKo": name_ko,
        "category": cat,
        "subcategory": sub,
        "bvCollections": cols,
        "tags": ["보테가 베네타", "Bottega Veneta", "BV"],
        "descriptionKo": desc_ko,
        "image": images[0],
        "images": images,
        "hoverImage": images[1] if len(images) > 1 else images[0],
        "price": min(v["price"] for v in variants),
        "gbpPrice": min(float(v["gbpPrice"]) for v in variants),
        "inStock": any(v.get("inStock") for v in variants),
        "sourceUrl": raw.get("link") or raw.get("url") or "",
        "featuresKo": features_ko,
        "storySections": stories,
        "techSpecs": [
            *([{"labelKo": "소재", "valueKo": _t(str(raw.get("composition") or raw.get("material") or ""), cache)}]
              if (raw.get("composition") or raw.get("material")) else []),
            {"labelKo": "제품 코드", "valueKo": smc},
        ],
        "sizeChart": chart,
        "variants": variants,
        "accentColor": "#111111",
        "registeredAt": now,
        "updatedAt": now,
        "badge": "New",
        "newBadgeAt": now,
        "editTier": "new",
        "_hub": hub_id,
    }
    ensure_official_english_name(prod, name)
    return prod


def main() -> int:
    from briq_new_badge import apply_new_badge_ttl, stamp_new_badge, utc_now

    cache = load_json(TRANSLATE_CACHE, {})
    if not isinstance(cache, dict):
        cache = {}
    prev_rows = load_json(OUT_JSON, [])
    prev_by_id = {
        str(p.get("id")): p
        for p in (prev_rows if isinstance(prev_rows, list) else [])
        if isinstance(p, dict) and p.get("id")
    }

    products: list[dict] = []
    seen: set[str] = set()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    now_dt = utc_now()

    for hub_id in HUB_ORDER:
        hub = HUBS_BY_ID[hub_id]
        raw_path = RAW_DIR / hub["out"]
        data = load_json(raw_path, {})
        rows = data.get("products") or []
        print(f"build {hub_id}: raw={len(rows)}", flush=True)
        for i, row in enumerate(rows, start=1):
            p = build_product(row, hub_id, cache, now)
            if not p:
                continue
            if i % 10 == 0 or i == len(rows):
                print(f"  {hub_id} {i}/{len(rows)} products={len(products)}", flush=True)
                save_json(TRANSLATE_CACHE, cache)
            if p["id"] in seen:
                for existing in products:
                    if existing["id"] != p["id"]:
                        continue
                    cols = list(
                        dict.fromkeys(
                            [
                                *(existing.get("bvCollections") or []),
                                *(p.get("bvCollections") or []),
                            ]
                        )
                    )
                    existing["bvCollections"] = cols
                    existing["subcategory"] = cols[-1] if cols else existing.get("subcategory")
                    for v in existing.get("variants") or []:
                        v["bvCollections"] = cols
                    if not existing.get("sizeChart") and p.get("sizeChart"):
                        existing["sizeChart"] = p["sizeChart"]
                    break
                continue
            seen.add(p["id"])
            old = prev_by_id.get(p["id"])
            if old:
                if old.get("registeredAt"):
                    p["registeredAt"] = old["registeredAt"]
                if old.get("newBadgeAt"):
                    p["newBadgeAt"] = old["newBadgeAt"]
                if old.get("badge") and old.get("badge") != "New":
                    p["badge"] = old["badge"]
                if old.get("editTier") and old.get("editTier") != "new":
                    p["editTier"] = old["editTier"]
                apply_new_badge_ttl(p, now=now_dt, newly_synced=False)
            else:
                stamp_new_badge(p, now=now_dt, force=True)
            products.append(p)
        save_json(TRANSLATE_CACHE, cache)

    save_json(OUT_JSON, products)
    OUT_TS.write_text(
        "/* Auto-generated by scripts/build-bv-catalog.py — do not edit */\n"
        'import type { Product } from "@/data/product-types";\n'
        'import data from "./bv-catalog.json";\n\n'
        "/** Bottega Veneta catalog (JSON import). */\n"
        "export const bvCatalogProducts = data as unknown as Product[];\n",
        encoding="utf-8",
    )
    print(f"OK wrote {OUT_JSON} products={len(products)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
