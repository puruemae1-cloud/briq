#!/usr/bin/env python3
"""Build Bottega Veneta catalogue from scraped raw JSON.

Pricing: KRW = round_만원(GBP × 2100 × 1.05 × 1.15) — same as Gucci.
"""
from __future__ import annotations

import socket
socket.setdefaulttimeout(10)

import re
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
from ko_qa import ensure_official_english_name, is_good_korean, translate_en_to_ko  # noqa: E402


def _t(text: str, cache: dict[str, str]) -> str:
    import os
    offline = os.environ.get("BV_OFFLINE_KO", "").strip() in {"1", "true", "yes"}
    raw = (text or "").strip()
    if not raw:
        return ""
    # Normalize common SFCC prefixes so glossary / cache hits are more reliable.
    cleaned = re.sub(
        r"^(?:•\s*)?(?:Material|Colour|Color|Hardware|Lining)\s*:\s*",
        "",
        raw,
        flags=re.I,
    ).strip()
    prefix = ""
    low = raw.lower()
    if "material:" in low:
        prefix = "소재: "
    elif re.search(r"colou?r:", low):
        prefix = "색상: "
    elif "hardware:" in low:
        prefix = "하드웨어: "
    elif "lining:" in low:
        prefix = "안감: "
    body = translate_en_to_ko(cleaned or raw, cache, offline=offline)
    if not body:
        return ""
    if prefix and not body.startswith(("소재", "색상", "하드웨어", "안감", "재질")):
        return prefix + body
    return body


def category_for_hub(hub_id: str) -> str:
    return HUBS_BY_ID[hub_id]["category"]


def _clean_bullet(text: str) -> str:
    t = re.sub(r"^[•\-\*·]\s*", "", (text or "").strip())
    return t.strip()


def _pick_ko(prev: str | None, new: str | None) -> str:
    """Prefer good Korean; fall back to whichever side has Hangul."""
    a = str(prev or "").strip()
    b = str(new or "").strip()
    if is_good_korean(b) and (not a or not is_good_korean(a) or len(b) >= len(a) * 0.6):
        return b
    if is_good_korean(a):
        return a
    return b or a


def build_story(
    *,
    intro_ko: str,
    features_ko: list[str],
    size_model_ko: str,
    material_ko: str,
    care_ko: str,
    color_ko: str,
    name_ko: str,
    images: list[str],
) -> list[dict]:
    """Multi-block editorial story so BV PDPs feel as rich as Prada/VW."""
    stories: list[dict] = []
    img0 = images[0] if images else ""

    intro = (intro_ko or "").strip() or name_ko
    stories.append({"titleKo": "제품 소개", "bodyKo": intro, "image": img0})

    skip = {x for x in (material_ko, color_ko) if x}
    detail_bits = [f for f in features_ko if f and f not in skip]
    if not detail_bits and features_ko:
        detail_bits = list(features_ko)
    if detail_bits:
        body = "\n".join(f"• {b}" for b in detail_bits[:12])
        stories.append(
            {
                "titleKo": "디테일 & 특징",
                "bodyKo": body,
                "image": images[1] if len(images) > 1 else img0,
                "reverse": True,
            }
        )

    mat_care_parts: list[str] = []
    if material_ko:
        mk = material_ko if material_ko.startswith(("소재", "재질")) else f"소재: {material_ko}"
        mat_care_parts.append(mk)
    if color_ko:
        ck = color_ko if ("색" in color_ko or "컬러" in color_ko) else f"색상: {color_ko}"
        mat_care_parts.append(ck)
    if care_ko:
        mat_care_parts.append(care_ko)
    if mat_care_parts:
        stories.append(
            {
                "titleKo": "소재 & 케어",
                "bodyKo": "\n".join(f"• {p}" for p in mat_care_parts),
                "image": images[2] if len(images) > 2 else img0,
            }
        )

    if size_model_ko:
        stories.append(
            {
                "titleKo": "사이즈 & 모델",
                "bodyKo": size_model_ko,
                "image": images[3] if len(images) > 3 else img0,
                "reverse": True,
            }
        )

    # Remaining official packshots as wide gallery — fills the PDP visually.
    used = {s.get("image") for s in stories if s.get("image")}
    gallery_idx = 0
    for img in images:
        if img in used:
            continue
        if len(stories) >= 10:
            break
        gallery_idx += 1
        stories.append(
            {
                "titleKo": "갤러리",
                "bodyKo": "보테가 베네타 공식 이미지로 실루엣과 디테일을 확인할 수 있습니다.",
                "image": img,
                "layout": "wide",
                "reverse": gallery_idx % 2 == 0,
            }
        )
    return stories


def build_description_ko(
    raw: dict, cache: dict[str, str], images: list[str]
) -> tuple[str, list[str], list[dict], dict]:
    parts: list[str] = []
    features: list[str] = []

    compact = str(raw.get("compactedLongDesc") or "").strip()
    # Translate paragraph-by-paragraph so glossary hits (artisans line, etc.) apply.
    intro_bits: list[str] = []
    if compact:
        for para in re.split(r"\n+", compact):
            para = para.strip()
            if not para:
                continue
            ko = _t(para, cache)
            if ko:
                intro_bits.append(ko)
    intro_ko = "\n".join(intro_bits).strip()
    if intro_ko:
        parts.append(intro_ko)

    for b in raw.get("longDescription") or []:
        ko = _t(_clean_bullet(str(b)), cache)
        if ko and ko not in features:
            features.append(ko)
            parts.append(ko)

    for b in raw.get("shortDescription") or []:
        ko = _t(_clean_bullet(str(b)), cache)
        if ko and ko not in features:
            features.append(ko)

    size_model = str(raw.get("sizeModel") or "").strip()
    size_model_ko = _t(size_model, cache) if size_model else ""
    if size_model_ko:
        parts.append(size_model_ko)

    material = str(raw.get("composition") or raw.get("material") or "").strip()
    material_ko = _t(_clean_bullet(material), cache) if material else ""
    if material_ko and material_ko not in features:
        features.append(material_ko)
        parts.append(material_ko)

    care = str(raw.get("productCare") or "").strip()
    care_ko = ""
    if care:
        care_short = care.split("\n\n")[0][:600]
        care_ko = _t(care_short, cache)

    color = str(raw.get("color") or "").strip()
    color_ko = _t(color, cache) if color else ""

    name_ko = _t(str(raw.get("name") or ""), cache) or str(raw.get("name") or "")
    stories = build_story(
        intro_ko=intro_ko,
        features_ko=features,
        size_model_ko=size_model_ko,
        material_ko=material_ko,
        care_ko=care_ko,
        color_ko=color_ko,
        name_ko=name_ko,
        images=images,
    )

    desc = "\n".join(p for p in parts if p).strip()
    extras = {
        "materialKo": material_ko,
        "colorKo": color_ko,
        "careKo": care_ko,
        "sizeModelKo": size_model_ko,
    }
    return desc, features[:14], stories, extras


def _merge_images(existing: dict, incoming: dict) -> None:
    """Keep the longer official gallery when the same SKU appears in multiple hubs."""
    old_imgs = list(existing.get("images") or [])
    new_imgs = list(incoming.get("images") or [])
    if len(new_imgs) <= len(old_imgs):
        return
    existing["images"] = new_imgs
    existing["image"] = new_imgs[0]
    existing["hoverImage"] = new_imgs[1] if len(new_imgs) > 1 else new_imgs[0]
    for v in existing.get("variants") or []:
        v["images"] = new_imgs
        v["image"] = new_imgs[0]
    # Rebuild gallery blocks against the fuller image set.
    intro = ""
    for sec in existing.get("storySections") or []:
        if sec.get("titleKo") == "제품 소개":
            intro = str(sec.get("bodyKo") or "")
            break
    if not intro:
        intro = str(existing.get("descriptionKo") or existing.get("nameKo") or "")
    material = ""
    color = ""
    for spec in existing.get("techSpecs") or []:
        if spec.get("labelKo") == "소재":
            material = str(spec.get("valueKo") or "")
        elif spec.get("labelKo") == "색상":
            color = str(spec.get("valueKo") or "")
    size_model = ""
    care = ""
    for sec in existing.get("storySections") or []:
        title = str(sec.get("titleKo") or "")
        if title == "사이즈 & 모델":
            size_model = str(sec.get("bodyKo") or "")
        elif title in {"소재 & 케어", "케어 가이드"} and not care:
            # keep full block only if we cannot split; build_story will re-compose
            pass
    existing["storySections"] = build_story(
        intro_ko=intro,
        features_ko=list(existing.get("featuresKo") or []),
        size_model_ko=size_model,
        material_ko=material,
        care_ko=care,
        color_ko=color,
        name_ko=str(existing.get("nameKo") or ""),
        images=new_imgs,
    )


def _apply_prev_ko(prod: dict, old: dict | None) -> None:
    """Keep previously verified Korean when rebuild left English leftovers."""
    if not old:
        # Still rebuild stories from current fields so gallery blocks stay consistent.
        old = {}

    prod["nameKo"] = _pick_ko(old.get("nameKo"), prod.get("nameKo"))
    prod["descriptionKo"] = _pick_ko(old.get("descriptionKo"), prod.get("descriptionKo"))

    old_feats = [str(x) for x in (old.get("featuresKo") or []) if str(x).strip()]
    new_feats = [str(x) for x in (prod.get("featuresKo") or []) if str(x).strip()]
    if old_feats and (not new_feats or not all(is_good_korean(x) for x in new_feats)):
        if all(is_good_korean(x) for x in old_feats):
            prod["featuresKo"] = old_feats

    # Tech specs: prefer KO values per label
    old_specs = {
        str(s.get("labelKo")): str(s.get("valueKo") or "")
        for s in (old.get("techSpecs") or [])
        if isinstance(s, dict) and s.get("labelKo")
    }
    specs = []
    for s in prod.get("techSpecs") or []:
        if not isinstance(s, dict):
            continue
        label = str(s.get("labelKo") or "")
        val = str(s.get("valueKo") or "")
        if label == "제품 코드":
            specs.append({"labelKo": label, "valueKo": val})
            continue
        specs.append({"labelKo": label, "valueKo": _pick_ko(old_specs.get(label), val)})
    if specs:
        prod["techSpecs"] = specs

    # Intro: prefer good 제품 소개 from new build, then old, then description lead.
    intro = ""
    for source in (prod, old):
        for sec in source.get("storySections") or []:
            if str(sec.get("titleKo") or "") != "제품 소개":
                continue
            body = str(sec.get("bodyKo") or "").strip()
            if is_good_korean(body):
                intro = body
                break
        if intro:
            break
    if not intro:
        desc = str(prod.get("descriptionKo") or "").strip()
        feats = {str(x).strip() for x in (prod.get("featuresKo") or [])}
        lines: list[str] = []
        for line in desc.split("\n"):
            line = line.strip()
            if not line:
                if lines:
                    break
                continue
            if line in feats and lines:
                break
            lines.append(line)
            if len(lines) >= 3:
                break
        intro = "\n".join(lines) or str(prod.get("nameKo") or "")

    material = next(
        (str(s.get("valueKo") or "") for s in (prod.get("techSpecs") or []) if s.get("labelKo") == "소재"),
        "",
    )
    color = next(
        (str(s.get("valueKo") or "") for s in (prod.get("techSpecs") or []) if s.get("labelKo") == "색상"),
        "",
    )
    size_model = ""
    care = ""
    for source in (old, prod):
        for sec in source.get("storySections") or []:
            title = str(sec.get("titleKo") or "")
            body = str(sec.get("bodyKo") or "")
            if title == "사이즈 & 모델" and is_good_korean(body) and not size_model:
                size_model = body
            elif title == "케어 가이드" and is_good_korean(body) and not care:
                care = body
    prod["storySections"] = build_story(
        intro_ko=intro,
        features_ko=list(prod.get("featuresKo") or []),
        size_model_ko=size_model,
        material_ko=material,
        care_ko=care,
        color_ko=color,
        name_ko=str(prod.get("nameKo") or ""),
        images=list(prod.get("images") or []),
    )


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
    desc_ko, features_ko, stories, extras = build_description_ko(raw, cache, images)
    if not desc_ko:
        desc_ko = name_ko

    chart = translate_size_chart(raw.get("sizeGuide"), cache)
    cols = list(raw.get("collections") or [])
    cat = category_for_hub(hub_id)
    # Prefer last leaf id as subcategory
    sub = cols[-1] if cols else hub_id

    tech: list[dict] = []
    if extras.get("materialKo"):
        tech.append({"labelKo": "소재", "valueKo": extras["materialKo"]})
    if extras.get("colorKo"):
        tech.append({"labelKo": "색상", "valueKo": extras["colorKo"]})
    tech.append({"labelKo": "제품 코드", "valueKo": smc})

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
        "techSpecs": tech,
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
                    _merge_images(existing, p)
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
            _apply_prev_ko(p, old)
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
