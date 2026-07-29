#!/usr/bin/env python3
"""Build bb-catalog.ts from bb-catalog-raw.json (Burberry Women)."""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bb_women_config import primary_category_for_collections  # noqa: E402

RAW_PATH = ROOT / "src/data/bb/bb-catalog-raw.json"
OUT_PATH = ROOT / "src/data/bb/bb-catalog.ts"
TRANSLATE_CACHE = ROOT / "src/data/bb/bb-translate-cache.json"

ACCENTS = [
    "#1A2E28",
    "#2C241C",
    "#1A2428",
    "#3A2F28",
    "#24302A",
    "#4A3A32",
    "#2A4038",
    "#1E3A4A",
]

_KO: dict[str, str] = {}
if TRANSLATE_CACHE.exists():
    _KO = json.loads(TRANSLATE_CACHE.read_text())


def t(text: str | None) -> str:
    """Lookup Korean translation with Burberry→버버리 polish."""
    if not text:
        return ""
    s = str(text).strip()
    ko = _KO.get(s, s)
    ko = ko.replace("Burberry", "버버리").replace("버 버리", "버버리")
    return ko


def gbp_to_krw(gbp: float) -> int:
    """Burberry Women pricing.
    ≤£110: GBP × 2100 × 1.06 + ₩20,000
    >£110: GBP × 2100 × 1.18 × 1.05 + ₩20,000
    Round to 천원.
    """
    if gbp is None:
        return 0
    g = float(gbp)
    if g <= 110:
        base = g * 2100 * 1.06 + 20_000
    else:
        base = g * 2100 * 1.18 * 1.05 + 20_000
    return int(round(base / 1_000) * 1_000)


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:80] or "item"


def clean_name(name: str) -> str:
    return (name or "").replace("\u200b", "").strip()


def style_key(product: dict) -> str:
    swatches = product.get("swatches") or []
    ids = sorted({str(s.get("id")) for s in swatches if s.get("id")})
    if len(ids) >= 2:
        return "swatch:" + "-".join(ids)
    # fallback: name without trailing colour hints
    return "name:" + slugify(clean_name(product.get("title") or product.get("id") or ""))


def ts_str(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)


def emit_product(p: dict) -> str:
    """Serialize one Product object as TS literal."""
    lines = ["  {"]
    for key, val in p.items():
        if val is None:
            continue
        if key in ("ggCollections", "bbCollections", "cwCollections") and isinstance(val, list):
            lines.append(
                f"    {key}: {json.dumps(val)} as Product[\"{key}\"],"
            )
        elif key == "variants" and isinstance(val, list):
            lines.append("    variants: [")
            for v in val:
                lines.append("      {")
                for vk, vv in v.items():
                    if vv is None:
                        continue
                    if vk == "bbCollections" and isinstance(vv, list):
                        lines.append(
                            f"        bbCollections: {json.dumps(vv)} as Product[\"bbCollections\"],"
                        )
                    elif isinstance(vv, str):
                        lines.append(f"        {vk}: {json.dumps(vv, ensure_ascii=False)},")
                    elif isinstance(vv, bool):
                        lines.append(f"        {vk}: {'true' if vv else 'false'},")
                    elif isinstance(vv, float):
                        lines.append(f"        {vk}: {vv},")
                    elif isinstance(vv, int):
                        lines.append(f"        {vk}: {vv},")
                    elif isinstance(vv, list):
                        lines.append(f"        {vk}: {json.dumps(vv, ensure_ascii=False)},")
                    else:
                        lines.append(f"        {vk}: {json.dumps(vv, ensure_ascii=False)},")
                lines.append("      },")
            lines.append("    ],")
        elif key == "storySections" and isinstance(val, list):
            lines.append(f"    storySections: {json.dumps(val, ensure_ascii=False)},")
        elif key == "featuresKo" and isinstance(val, list):
            lines.append(f"    featuresKo: {json.dumps(val, ensure_ascii=False)},")
        elif key == "techSpecs" and isinstance(val, list):
            lines.append(f"    techSpecs: {json.dumps(val, ensure_ascii=False)},")
        elif key == "tags" and isinstance(val, list):
            lines.append(f"    tags: {json.dumps(val, ensure_ascii=False)},")
        elif key == "images" and isinstance(val, list):
            lines.append(f"    images: {json.dumps(val, ensure_ascii=False)},")
        elif isinstance(val, str):
            lines.append(f"    {key}: {json.dumps(val, ensure_ascii=False)},")
        elif isinstance(val, bool):
            lines.append(f"    {key}: {'true' if val else 'false'},")
        elif isinstance(val, float):
            lines.append(f"    {key}: {val},")
        elif isinstance(val, int):
            lines.append(f"    {key}: {val},")
        else:
            lines.append(f"    {key}: {json.dumps(val, ensure_ascii=False)},")
    lines.append("  }")
    return "\n".join(lines)


def description_parts(product: dict) -> tuple[str, list[str], list[dict]]:
    desc = product.get("description") or ""
    parts = [p.strip() for p in desc.split("##") if p.strip()]
    body = t(parts[0]) if parts else ""
    features = [t(p) for p in parts[1:]] if len(parts) > 1 else []
    for acc in product.get("accordion") or []:
        label = acc.get("label") or ""
        texts = [x for x in (acc.get("texts") or []) if x]
        if label.lower() == "product details" and texts:
            if not body:
                body = t(texts[0])
            for x in texts[1:]:
                if x.lower().startswith("item "):
                    continue
                tx = t(x)
                if tx and tx not in features:
                    features.append(tx)
        elif texts:
            for x in texts:
                tx = t(x)
                if tx and tx not in features:
                    features.append(tx)
    tech = []
    if product.get("measurements"):
        tech.append({"labelKo": "사이즈 · 핏", "valueKo": t(str(product["measurements"]))})
    if product.get("materialComposition"):
        mat = t(str(product["materialComposition"]).replace(" #", " · "))
        tech.append({"labelKo": "소재", "valueKo": mat})
    return body, features[:16], tech


def main() -> None:
    raw = json.loads(RAW_PATH.read_text())
    products = raw.get("products") or []

    groups: dict[str, list[dict]] = defaultdict(list)
    for p in products:
        groups[style_key(p)].append(p)

    briq: list[dict] = []
    now = datetime.now(timezone.utc)

    for gkey, colourways in groups.items():
        colourways = sorted(colourways, key=lambda x: x.get("id") or "")
        all_cols: set[str] = set()
        for c in colourways:
            all_cols.update(c.get("collections") or [])
        cols_sorted = sorted(all_cols)
        top_cat, primary_sub = primary_category_for_collections(cols_sorted)

        primary = colourways[0]
        name_en = clean_name(primary.get("title") or "Burberry")
        # Prefer longest title
        for c in colourways:
            x = clean_name(c.get("title") or "")
            if len(x) > len(name_en):
                name_en = x
        name_ko = t(name_en) or name_en

        style_slug = slugify(name_en) or (primary.get("id") or "item")
        pid = f"bb-{style_slug}"
        # ensure unique product ids
        existing = {p["id"] for p in briq}
        base_pid = pid
        n = 2
        while pid in existing:
            pid = f"{base_pid}-{n}"
            n += 1

        flat_variants = []
        gallery_all: list[str] = []
        prices_krw = []
        body, features, tech = description_parts(primary)
        # merge accordion features from all colours lightly
        for c in colourways[1:]:
            _, feat2, tech2 = description_parts(c)
            for f in feat2:
                if f not in features:
                    features.append(f)
            if not tech:
                tech = tech2

        for c in colourways:
            color = c.get("color") or "Default"
            color_ko = t(color) or color
            color_key = slugify(color) or c.get("id")
            color_cols = sorted(set(c.get("collections") or cols_sorted))
            local_imgs = list(c.get("images") or [])
            if not local_imgs and c.get("image") and str(c["image"]).startswith("/"):
                local_imgs = [c["image"]]
            for img in local_imgs:
                if img and img not in gallery_all:
                    gallery_all.append(img)
            lead_img = local_imgs[0] if local_imgs else (c.get("image") or "/products/wool-coat.svg")
            gbp = float(c.get("gbpPrice") or 0)
            gbp_list = c.get("gbpListPrice")
            price = gbp_to_krw(gbp) if gbp else 0
            compare = gbp_to_krw(float(gbp_list)) if gbp_list and float(gbp_list) > gbp else None
            if price:
                prices_krw.append(price)

            sizes = c.get("sizes") or []
            if not sizes:
                sizes = [
                    {
                        "sku": c.get("id"),
                        "label": "One size",
                        "isInStock": True,
                    }
                ]

            source = c.get("url") or ""
            for sz in sizes:
                label = str(sz.get("label") or "One size")
                label_ko = "프리사이즈" if label.lower() in ("one size", "onesize", "os") else label
                sku = str(sz.get("sku") or f"{c.get('id')}-{label}")
                in_stock = bool(sz.get("isInStock"))
                flat_variants.append(
                    {
                        "id": f"bb-{c.get('id')}-{slugify(label)}",
                        "name": f"{color} / {label}",
                        "nameKo": f"{color_ko} / {label_ko}",
                        "sku": sku,
                        "gbpPrice": gbp,
                        "price": price,
                        "compareAtPrice": compare,
                        "image": lead_img,
                        "images": local_imgs[:6] or None,
                        "sourceUrl": source,
                        "inStock": in_stock,
                        "colorKey": color_key,
                        "colorNameKo": color_ko,
                        "size": label_ko if label_ko == "프리사이즈" else label,
                        "bbCollections": color_cols,
                    }
                )

        in_stock_prices = [v["price"] for v in flat_variants if v.get("inStock") and v["price"]]
        price = min(in_stock_prices) if in_stock_prices else (min(prices_krw) if prices_krw else 0)
        gbp_price = None
        for v in flat_variants:
            if v.get("inStock") and v["price"] == price:
                gbp_price = v["gbpPrice"]
                break
        if gbp_price is None and flat_variants:
            gbp_price = min(v["gbpPrice"] for v in flat_variants if v.get("gbpPrice"))

        compare_at = None
        for v in flat_variants:
            if v["price"] != price:
                continue
            cap = v.get("compareAtPrice")
            if cap and cap > price:
                compare_at = cap
                break

        primary_image = gallery_all[0] if gallery_all else "/products/wool-coat.svg"
        badge = "New" if any(x.get("label") == "New In" for x in colourways) else None
        if "bb-women-new" in cols_sorted:
            badge = badge or "New"

        story = []
        if body:
            story.append(
                {
                    "titleKo": name_ko,
                    "bodyKo": body,
                    "image": primary_image,
                }
            )
        if features:
            story.append(
                {
                    "titleKo": "디테일",
                    "bodyKo": " · ".join(features[:8]),
                    "image": gallery_all[1] if len(gallery_all) > 1 else primary_image,
                    "reverse": True,
                }
            )

        briq.append(
            {
                "id": pid,
                "name": name_en,
                "nameKo": name_ko,
                "brand": "버버리",
                "price": price,
                "compareAtPrice": compare_at,
                "category": top_cat,
                "subcategory": primary_sub,
                "bbCollections": cols_sorted,
                "tags": ["burberry", "버버리", "bb-women", *cols_sorted],
                "descriptionKo": body[:1500] if body else None,
                "image": primary_image,
                "images": gallery_all[:12] or None,
                "accent": ACCENTS[len(briq) % len(ACCENTS)],
                "badge": badge,
                "gbpPrice": gbp_price,
                "sku": flat_variants[0]["sku"] if flat_variants else primary.get("id"),
                "sourceUrl": primary.get("url") or flat_variants[0].get("sourceUrl"),
                "registeredAt": now.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "editTier": "new" if badge == "New" else "signature",
                "storySections": story or None,
                "featuresKo": features or None,
                "techSpecs": tech or None,
                "variants": flat_variants,
                "inStock": any(v.get("inStock") for v in flat_variants),
            }
        )

    # Stable-ish order: luxury apparel first, then bags, shoes, accessories
    top_order = {"luxury": 0, "bags": 1, "shoes": 2, "accessories": 3}

    def sort_key(p: dict):
        return (top_order.get(p["category"], 9), p["name"].lower(), p["id"])

    briq.sort(key=sort_key)

    chunks = [emit_product(p) for p in briq]
    out = (
        "/** Auto-generated Burberry Women catalogue — do not edit by hand. */\n"
        'import type { Product } from "@/data/products";\n\n'
        "export const bbCatalogProducts: Product[] = [\n"
        + ",\n".join(chunks)
        + "\n];\n"
    )
    OUT_PATH.write_text(out)
    print(f"Wrote {OUT_PATH} styles={len(briq)} colourways={len(products)}")


if __name__ == "__main__":
    main()
