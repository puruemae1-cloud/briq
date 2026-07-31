#!/usr/bin/env python3
"""Build ax-apparel-catalog.ts from outdoor apparel raw + PDP + translations."""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "src/data/ax/ax-apparel-raw.json"
PDP_PATH = ROOT / "src/data/ax/ax-apparel-pdp-cache.json"
TRANSLATE_CACHE = ROOT / "src/data/ax/ax-translate-cache.json"
OUT_PATH = ROOT / "src/data/ax/ax-apparel-catalog.ts"
IMG_ROOT = ROOT / "public/products/axa-pdp"

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
    if not text:
        return ""
    s = str(text).strip()
    return _KO.get(s, s)


def parse_gbp(val) -> float:
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace("£", "").replace(",", "").replace("GBP", "").strip()
    try:
        return float(s)
    except ValueError:
        m = re.search(r"(\d+(?:\.\d+)?)", s)
        return float(m.group(1)) if m else 0.0


def gbp_to_krw(gbp: float | None) -> int:
    if gbp is None:
        return 0
    base = float(gbp) * 2100 * 1.18 + 20_000
    return int(round(base / 1_000) * 1_000)


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:80] or "item"


def ts_escape(s: str) -> str:
    return (
        s.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "")
    )


def js_str(s: str) -> str:
    return '"' + ts_escape(s) + '"'


def js_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)


def list_gallery(pid: str, cslug: str) -> list[str]:
    d = IMG_ROOT / pid / cslug
    if not d.exists():
        return []
    nums = sorted(
        [p for p in d.glob("[0-9]*.jpg")],
        key=lambda p: int(p.stem) if p.stem.isdigit() else 999,
    )
    out = [
        f"/products/axa-pdp/{pid}/{cslug}/{p.name}"
        for p in nums
        if p.stat().st_size > 800
    ]
    if not out:
        thumb = d / "thumb.jpg"
        if thumb.exists() and thumb.stat().st_size > 800:
            out = [f"/products/axa-pdp/{pid}/{cslug}/thumb.jpg"]
    return out


def size_chart(gender: str) -> dict:
    return {
        "id": "ax-apparel",
        "titleKo": (
            "아크테릭스 여성 의류 사이즈 가이드"
            if gender == "womens"
            else "아크테릭스 남성 의류 사이즈 가이드"
        ),
        "noteKo": "상품에 표기된 사이즈를 선택하세요. R은 Regular 기장입니다.",
        "headers": ["Size", "설명"],
        "rows": [
            ["XXS", "Extra Extra Small"],
            ["XS", "Extra Small"],
            ["S / SR", "Small / Small Regular"],
            ["M / MR", "Medium / Medium Regular"],
            ["L / LR", "Large / Large Regular"],
            ["XL / XLR", "Extra Large / XL Regular"],
            ["XXL / 2XR", "2X Large"],
        ],
    }


def default_sizes(name: str, gender: str) -> list[str]:
    n = (name or "").lower()
    if any(k in n for k in ("pant", "short", "tight", "legging", "capri", "skirt")):
        if gender == "womens":
            return ["00", "0", "2", "4", "6", "8", "10", "12", "14"]
        return ["28", "30", "32", "34", "36", "38"]
    return ["XXS", "XS", "S", "M", "L", "XL", "XXL"]


def build_story(pdp: dict, images: list[str]) -> list[dict]:
    sections: list[dict] = []
    for i, sec in enumerate(pdp.get("sections") or []):
        heading = t(sec.get("heading") or "")
        body = t(sec.get("body") or "")
        if not heading and not body:
            continue
        item: dict = {"titleKo": heading or "상세", "bodyKo": body}
        if images:
            item["image"] = images[i % len(images)]
        if i % 2 == 1:
            item["reverse"] = True
        sections.append(item)
    for feat in pdp.get("features") or []:
        title = t(feat.get("title") or "")
        body = t(feat.get("body") or "")
        if not body:
            continue
        item = {"titleKo": title or "특징", "bodyKo": body}
        if images:
            item["image"] = images[len(sections) % len(images)]
        if len(sections) % 2 == 1:
            item["reverse"] = True
        sections.append(item)
    return sections[:8]


def main() -> None:
    raw = json.loads(RAW_PATH.read_text())
    pdp_all = json.loads(PDP_PATH.read_text()) if PDP_PATH.exists() else {}
    products_out: list[str] = []
    batch_start = datetime.now(timezone.utc).replace(microsecond=0)

    for idx, p in enumerate(raw["products"]):
        pid = p["id"]
        gender = p.get("gender") or "mens"
        cols = list(p.get("collections") or ["ax-mens"])
        sub = cols[0]
        pdp = pdp_all.get(pid) or {}

        sale_gbp = parse_gbp(
            pdp.get("gbpPrice")
            if pdp.get("gbpPrice") not in (None, "")
            else p.get("gbpPrice") or 0
        )
        list_gbp = parse_gbp(
            pdp.get("gbpListPrice")
            if pdp.get("gbpListPrice") not in (None, "")
            else p.get("gbpListPrice") or sale_gbp
        )
        if list_gbp < sale_gbp:
            list_gbp = sale_gbp
        if sale_gbp <= 0 and list_gbp > 0:
            sale_gbp = list_gbp
        price = gbp_to_krw(sale_gbp)
        compare = gbp_to_krw(list_gbp) if list_gbp > sale_gbp + 0.01 else None

        name = p.get("name") or pdp.get("title") or pid
        name_ko = t(name) or name
        tagline = pdp.get("tagline") or p.get("shortDescription") or ""
        desc_ko = t(tagline) or tagline

        sizes = [str(s) for s in (pdp.get("sizes") or pdp.get("sizesUk") or [])]
        if not sizes:
            sizes = default_sizes(name, gender)

        colour_names = []
        for c in pdp.get("colours") or []:
            if isinstance(c, str) and c.strip():
                colour_names.append(c.strip())
        raw_colours = p.get("colours") or []
        raw_by = {c["color"]: c for c in raw_colours if c.get("color")}
        raw_by_l = {c["color"].lower(): c for c in raw_colours if c.get("color")}
        if not colour_names:
            colour_names = [c["color"] for c in raw_colours if c.get("color")]

        variants_blocks: list[str] = []
        all_images: list[str] = []
        lead_image = ""
        lead_hover = ""

        for cname in colour_names:
            meta = raw_by.get(cname) or raw_by_l.get(cname.lower())
            if not meta:
                for k, v in raw_by.items():
                    if cname.lower() in k.lower() or k.lower() in cname.lower():
                        meta = v
                        break
            cslug = slugify(cname if not meta else meta["color"])
            gallery = list_gallery(pid, cslug)
            if not gallery and meta:
                gallery = list_gallery(pid, slugify(meta["color"]))
                cslug = slugify(meta["color"])
            if not gallery:
                pdir = IMG_ROOT / pid
                if pdir.exists():
                    for subdir in sorted(pdir.iterdir()):
                        if subdir.is_dir():
                            gallery = list_gallery(pid, subdir.name)
                            if gallery:
                                cslug = subdir.name
                                break
            if not gallery:
                continue
            if not lead_image:
                lead_image = gallery[0]
                lead_hover = gallery[1] if len(gallery) > 1 else gallery[0]
            for g in gallery:
                if g not in all_images:
                    all_images.append(g)

            color_ko = t(cname) or cname
            for size in sizes:
                vid = f"axa-{pid.lower()}-{cslug}-{size.replace('.', '_').replace('/', '-')}"
                v_lines = [
                    "      {",
                    f"        id: {js_str(vid)},",
                    f"        name: {js_str(f'{cname} / {size}')},",
                    f"        nameKo: {js_str(f'{color_ko} / {size}')},",
                    f"        sku: {js_str(f'{pid}-{cslug}-{size}')},",
                    f"        gbpPrice: {sale_gbp},",
                    f"        price: {price},",
                ]
                if compare:
                    v_lines.append(f"        compareAtPrice: {compare},")
                v_lines += [
                    f"        image: {js_str(gallery[0])},",
                    f"        images: {js_json(gallery)},",
                    f"        hoverImage: {js_str(gallery[1] if len(gallery) > 1 else gallery[0])},",
                    f"        sourceUrl: {js_str(p.get('url') or '')},",
                    "        inStock: true,",
                    f"        colorKey: {js_str(cslug)},",
                    f"        colorNameKo: {js_str(color_ko)},",
                    f"        size: {js_str(size)},",
                    f'        axCollections: {js_json(cols)} as Product["axCollections"],',
                    "      },",
                ]
                variants_blocks.append("\n".join(v_lines))

        if not lead_image or not variants_blocks:
            print(f"skip no images/variants: {pid} {name}")
            continue

        story = build_story(pdp, all_images or [lead_image])
        features_ko = []
        for feat in pdp.get("features") or []:
            title = t(feat.get("title") or "")
            body = t(feat.get("body") or "")
            if title and body:
                features_ko.append(f"{title}: {body}")
            elif body:
                features_ko.append(body)

        registered = (batch_start + timedelta(seconds=idx)).strftime(
            "%Y-%m-%dT%H:%M:%S.000Z"
        )
        accent = ACCENTS[idx % len(ACCENTS)]
        style_id = f"axa-{pid.lower()}"
        chart = size_chart(gender)
        badge = "Sale" if compare else ("New" if p.get("isNew") else None)

        block = [
            "  {",
            f"    id: {js_str(style_id)},",
            f"    name: {js_str(name)},",
            f"    nameKo: {js_str(name_ko)},",
            '    brand: "아크테릭스",',
            f"    price: {price},",
        ]
        if compare:
            block.append(f"    compareAtPrice: {compare},")
        block += [
            '    category: "luxury",',
            f"    subcategory: {js_str(sub)},",
            f'    axCollections: {js_json(cols)} as Product["axCollections"],',
            f"    tags: {js_json(['arcteryx', '아크테릭스', 'clothing', *cols, gender])},",
            f"    descriptionKo: {js_str(desc_ko)},",
            f"    image: {js_str(lead_image)},",
            f"    images: {js_json(all_images[:24] or [lead_image])},",
            f"    hoverImage: {js_str(lead_hover)},",
            f"    accent: {js_str(accent)},",
        ]
        if badge:
            block.append(f"    badge: {js_str(badge)},")
        block += [
            f"    gbpPrice: {sale_gbp},",
        ]
        if compare:
            block.append(f"    gbpListPrice: {list_gbp},")
        block += [
            f"    sku: {js_str(pid)},",
            f"    sourceUrl: {js_str(p.get('url') or '')},",
            f"    registeredAt: {js_str(registered)},",
            f'    editTier: {js_str("new" if badge == "New" else "bestseller")},',
            f"    storySections: {js_json(story)},",
            f"    featuresKo: {js_json(features_ko)},",
            "    techSpecs: [],",
            f"    sizeChart: {js_json(chart)},",
            "    variants: [",
            *variants_blocks,
            "    ],",
            "  },",
        ]
        products_out.append("\n".join(block))

    header = """/** Auto-generated Arc'teryx outdoor apparel catalogue — do not edit by hand. */
import type { Product } from "@/data/products";

export const axApparelCatalogProducts: Product[] = [
"""
    OUT_PATH.write_text(header + "\n".join(products_out) + "\n];\n")
    print(f"Wrote {len(products_out)} products → {OUT_PATH}")


if __name__ == "__main__":
    main()
