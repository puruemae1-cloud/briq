#!/usr/bin/env python3
"""Build ax-catalog.ts from Arc'teryx footwear raw + PDP + translations."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from ax_size_order import sort_ax_sizes  # noqa: E402

RAW_PATH = ROOT / "src/data/ax/ax-catalog-raw.json"
PDP_PATH = ROOT / "src/data/ax/ax-pdp-cache.json"
TRANSLATE_CACHE = ROOT / "src/data/ax/ax-translate-cache.json"
OUT_PATH = ROOT / "src/data/ax/ax-catalog.ts"
IMG_ROOT = ROOT / "public/products/ax-pdp"

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


def colour_name_ko(cname: str) -> str:
    """Arc'teryx colourways stay English; only basic colours may use KO."""
    basic = {
        "Black": "블랙",
        "White": "화이트",
        "Navy": "네이비",
        "Grey": "그레이",
        "Gray": "그레이",
        "Red": "레드",
        "Blue": "블루",
        "Green": "그린",
        "Brown": "브라운",
        "Beige": "베이지",
        "Orange": "오렌지",
        "Yellow": "옐로우",
        "Purple": "퍼플",
        "Pink": "핑크",
    }
    raw = (cname or "").strip()
    if not raw:
        return raw
    if "/" in raw:
        parts = re.split(r"\s*/\s*", raw)
        return " / ".join(colour_name_ko(p) for p in parts if p)
    if raw in basic:
        return basic[raw]
    cached = _KO.get(raw)
    if cached and cached == raw:
        return raw
    if cached and raw in basic:
        return cached
    return raw


def gbp_to_krw(gbp: float | None) -> int:
    """Arc'teryx: GBP × 2100 × 1.18 + ₩20,000 — round to 천원."""
    if gbp is None:
        return 0
    base = float(gbp) * 2100 * 1.18 + 20_000
    return int(round(base / 1_000) * 1_000)


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:80] or "item"


def color_slug(name: str) -> str:
    return slugify(name) or "default"


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
        [
            p
            for p in d.iterdir()
            if p.is_file() and re.fullmatch(r"\d+\.jpg", p.name, flags=re.I)
        ],
        key=lambda p: int(p.stem),
    )
    out = [f"/products/ax-pdp/{pid}/{cslug}/{p.name}" for p in nums]
    thumb = d / "thumb.jpg"
    if thumb.exists():
        tpath = f"/products/ax-pdp/{pid}/{cslug}/thumb.jpg"
        if tpath not in out:
            # Prefer numbered gallery first; thumb is PLP fallback only if empty
            if not out:
                out = [tpath]
    return out


def size_chart(gender: str) -> dict:
    note = (
        "발 길이를 재어 가장 가깝거나 같거나 큰 수치를 고르세요. "
        "Briq 표기 사이즈는 Arc'teryx UK 기준입니다. "
        "일부 모델은 크게 나오는 편이라 반 사이즈 작게 권장될 수 있으니 상품 설명을 확인하세요."
    )
    headers = ["UK", "CM", "US M", "US W", "EU", "KR"]
    rows = [
        ["3.5", "22cm", "4", "5", "36", "220mm"],
        ["4", "22.5cm", "4.5", "5.5", "36⅔", "225mm"],
        ["4.5", "23cm", "5", "6", "37⅓", "230mm"],
        ["5", "23.5cm", "5.5", "6.5", "38", "235mm"],
        ["5.5", "24cm", "6", "7", "38⅔", "240mm"],
        ["6", "24.5cm", "6.5", "7.5", "39⅓", "245mm"],
        ["6.5", "25cm", "7", "8", "40", "250mm"],
        ["7", "25.5cm", "7.5", "8.5", "40⅔", "255mm"],
        ["7.5", "26cm", "8", "9", "41⅓", "260mm"],
        ["8", "26.5cm", "8.5", "9.5", "42", "265mm"],
        ["8.5", "27cm", "9", "10", "42⅔", "270mm"],
        ["9", "27.5cm", "9.5", "10.5", "43⅓", "275mm"],
        ["9.5", "28cm", "10", "11", "44", "280mm"],
        ["10", "28.5cm", "10.5", "11.5", "44⅔", "285mm"],
        ["10.5", "29cm", "11", "12", "45⅓", "290mm"],
        ["11", "29.5cm", "11.5", "12.5", "46", "295mm"],
        ["11.5", "30cm", "12", "13", "46⅔", "300mm"],
        ["12", "30.5cm", "12.5", "13.5", "47⅓", "305mm"],
        ["12.5", "31cm", "13", "14", "48", "310mm"],
        ["13", "31.5cm", "13.5", "14.5", "48⅔", "315mm"],
        ["13.5", "32cm", "14", "15", "49⅓", "320mm"],
    ]
    if gender == "womens":
        return {
            "id": "ax-shoes-womens",
            "titleKo": "아크테릭스 여성 슈즈 사이즈 차트 (UK)",
            "noteKo": note,
            "headers": headers,
            "rows": rows,
        }
    return {
        "id": "ax-shoes-mens",
        "titleKo": "아크테릭스 남성 슈즈 사이즈 차트 (UK)",
        "noteKo": note,
        "headers": headers,
        "rows": rows,
    }


def build_story(pdp: dict, pid: str, lead_cslug: str, images: list[str]) -> list[dict]:
    sections: list[dict] = []
    for i, sec in enumerate(pdp.get("sections") or []):
        heading = t(sec.get("heading") or "")
        body = t(sec.get("body") or "")
        if not heading and not body:
            continue
        img = images[i % len(images)] if images else None
        item: dict = {"titleKo": heading or "상세", "bodyKo": body}
        if img:
            item["image"] = img
        if i % 2 == 1:
            item["reverse"] = True
        sections.append(item)
    # features as additional story blocks if no/few sections
    for j, feat in enumerate(pdp.get("features") or []):
        title = t(feat.get("title") or "")
        body = t(feat.get("body") or "")
        if not body:
            continue
        img = images[(len(sections) + j) % len(images)] if images else None
        item = {"titleKo": title or "특징", "bodyKo": body}
        if img:
            item["image"] = img
        if (len(sections) + j) % 2 == 1:
            item["reverse"] = True
        sections.append(item)
    return sections[:8]


def main() -> None:
    raw = json.loads(RAW_PATH.read_text())
    pdp_all = json.loads(PDP_PATH.read_text())
    products_out: list[str] = []
    batch_start = datetime.now(timezone.utc).replace(microsecond=0)

    for idx, p in enumerate(raw["products"]):
        pid = p["id"]
        pdp = pdp_all.get(pid) or {}
        gender = p["gender"]
        coll = p["collections"][0]
        gbp = float(pdp.get("gbpPrice") or p.get("gbpPrice") or 0)
        price = gbp_to_krw(gbp)
        name = p.get("name") or pdp.get("title") or pid
        name_ko = t(name) or name
        tagline = pdp.get("tagline") or p.get("shortDescription") or ""
        desc_ko = t(tagline) or tagline

        sizes = [str(s) for s in (pdp.get("sizesUk") or pdp.get("sizes") or [])]
        if not sizes and (pdp.get("variants") or []):
            seen = []
            for v in pdp.get("variants") or []:
                s = v.get("size")
                if s and s not in seen:
                    seen.append(str(s))
            sizes = seen
        if not sizes:
            sizes = [str(x) for x in ["7", "7.5", "8", "8.5", "9", "9.5", "10", "10.5", "11"]]
        sizes = sort_ax_sizes(sizes)

        # Prefer PDP colour list order when present, else raw colours
        colour_names = pdp.get("colours") or [c["color"] for c in p["colours"]]
        raw_by_name = {c["color"]: c for c in p["colours"]}
        # also fuzzy match ignoring case
        raw_by_lower = {c["color"].lower(): c for c in p["colours"]}

        variants_blocks: list[str] = []
        all_images: list[str] = []
        lead_image = ""
        lead_hover = ""
        lead_cslug = ""

        for ci, cname in enumerate(colour_names):
            meta = raw_by_name.get(cname) or raw_by_lower.get(cname.lower())
            if not meta:
                # try partial
                for k, v in raw_by_name.items():
                    if cname.lower() in k.lower() or k.lower() in cname.lower():
                        meta = v
                        break
            cslug = color_slug(cname)
            gallery = list_gallery(pid, cslug)
            if not gallery and meta:
                # try slug from meta color
                cslug2 = color_slug(meta["color"])
                gallery = list_gallery(pid, cslug2)
                if gallery:
                    cslug = cslug2
            if not gallery:
                continue
            if not lead_image:
                lead_image = gallery[0]
                lead_hover = gallery[1] if len(gallery) > 1 else gallery[0]
                lead_cslug = cslug
            for g in gallery:
                if g not in all_images:
                    all_images.append(g)

            color_ko = colour_name_ko(cname)
            for size in sizes:
                in_stock = True
                for v in pdp.get("variants") or []:
                    if v.get("color") == cname and str(v.get("size") or "") == size:
                        in_stock = bool(v.get("inStock"))
                        break
                else:
                    if pdp.get("variants"):
                        # colour×size not listed → treat as OOS when matrix exists
                        matched = [
                            v
                            for v in pdp.get("variants") or []
                            if v.get("color") == cname
                        ]
                        if matched:
                            in_stock = False
                vid = f"ax-{pid.lower()}-{cslug}-{size.replace('.', '_')}"
                variants_blocks.append(
                    "\n".join(
                        [
                            "      {",
                            f"        id: {js_str(vid)},",
                            f"        name: {js_str(f'{cname} / UK {size}')},",
                            f"        nameKo: {js_str(f'{color_ko} / UK {size}')},",
                            f"        sku: {js_str(f'{pid}-{cslug}-{size}')},",
                            f"        gbpPrice: {gbp},",
                            f"        price: {price},",
                            f"        image: {js_str(gallery[0])},",
                            f"        images: {js_json(gallery)},",
                            f"        hoverImage: {js_str(gallery[1] if len(gallery) > 1 else gallery[0])},",
                            f"        sourceUrl: {js_str(p.get('url') or '')},",
                            f"        inStock: {'true' if in_stock else 'false'},",
                            f"        colorKey: {js_str(cslug)},",
                            f"        colorNameKo: {js_str(color_ko)},",
                            f"        size: {js_str(size)},",
                            f'        axCollections: {js_json([coll])} as Product["axCollections"],',
                            "      },",
                        ]
                    )
                )

        if not lead_image:
            print(f"skip no images: {pid}")
            continue

        story = build_story(pdp, pid, lead_cslug, all_images or [lead_image])
        features_ko = []
        for feat in pdp.get("features") or []:
            title = t(feat.get("title") or "")
            body = t(feat.get("body") or "")
            if title and body:
                features_ko.append(f"{title}: {body}")
            elif body:
                features_ko.append(body)

        tech = []
        for spec in pdp.get("techSpecs") or []:
            lab = t(spec.get("label") or "")
            val = t(spec.get("value") or "")
            if lab or val:
                tech.append({"labelKo": lab or "스펙", "valueKo": val})

        registered = (batch_start + timedelta(seconds=idx)).strftime(
            "%Y-%m-%dT%H:%M:%S.000Z"
        )
        accent = ACCENTS[idx % len(ACCENTS)]
        style_id = f"ax-{pid.lower()}"
        chart = size_chart(gender)
        badge = "New" if p.get("isNew") else None

        block = [
            "  {",
            f"    id: {js_str(style_id)},",
            f"    name: {js_str(name)},",
            f"    nameKo: {js_str(name_ko)},",
            '    brand: "아크테릭스",',
            f"    price: {price},",
            '    category: "shoes",',
            f"    subcategory: {js_str(coll)},",
            f'    axCollections: {js_json([coll])} as Product["axCollections"],',
            f"    tags: {js_json(['arcteryx', '아크테릭스', 'shoes', coll, gender])},",
            f"    descriptionKo: {js_str(desc_ko)},",
            f"    image: {js_str(lead_image)},",
            f"    images: {js_json(all_images[:24] or [lead_image])},",
            f"    hoverImage: {js_str(lead_hover)},",
            f"    accent: {js_str(accent)},",
        ]
        if badge:
            block.append(f"    badge: {js_str(badge)},")
        block += [
            f"    gbpPrice: {gbp},",
            f"    sku: {js_str(pid)},",
            f"    sourceUrl: {js_str(p.get('url') or '')},",
            f"    registeredAt: {js_str(registered)},",
            f"    editTier: {js_str('new' if badge else 'bestseller')},",
            f"    storySections: {js_json(story)},",
            f"    featuresKo: {js_json(features_ko)},",
            f"    techSpecs: {js_json(tech)},",
            f"    sizeChart: {js_json(chart)},",
            "    variants: [",
            *variants_blocks,
            "    ],",
            "  },",
        ]
        products_out.append("\n".join(block))

    header = """/** Auto-generated Arc'teryx footwear catalogue — do not edit by hand. */
import type { Product } from "@/data/products";

export const axCatalogProducts: Product[] = [
"""
    footer = """];
"""
    OUT_PATH.write_text(header + "\n".join(products_out) + "\n" + footer)
    print(f"Wrote {len(products_out)} products → {OUT_PATH}")


if __name__ == "__main__":
    main()
