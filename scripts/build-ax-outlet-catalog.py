#!/usr/bin/env python3
"""Build ax-outlet-catalog.ts from outlet raw + PDP + translations."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from ax_size_charts import chart_for  # noqa: E402
from ax_size_order import sort_ax_sizes  # noqa: E402

RAW_PATH = ROOT / "src/data/ax/ax-outlet-raw.json"
PDP_PATH = ROOT / "src/data/ax/ax-outlet-pdp-cache.json"
TRANSLATE_CACHE = ROOT / "src/data/ax/ax-translate-cache.json"
OUT_PATH = ROOT / "src/data/ax/ax-outlet-catalog.ts"
IMG_ROOT = ROOT / "public/products/axo-pdp"
EXISTING_AX = ROOT / "src/data/ax/ax-catalog.ts"

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
        [
            p
            for p in d.iterdir()
            if p.is_file() and re.fullmatch(r"\d+\.jpg", p.name, flags=re.I)
        ],
        key=lambda p: int(p.stem),
    )
    out = []
    seen: set[str] = set()
    for p in nums:
        if p.stat().st_size <= 800:
            continue
        digest = hashlib.md5(p.read_bytes()).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        out.append(f"/products/axo-pdp/{pid}/{cslug}/{p.name}")
    if not out:
        thumb = d / "thumb.jpg"
        if thumb.exists() and thumb.stat().st_size > 800:
            out = [f"/products/axo-pdp/{pid}/{cslug}/thumb.jpg"]
    return out


def list_hover(pid: str, cslug: str, gallery: list[str]) -> str:
    """Official Arc'teryx PLP hover asset when present, else gallery[1]."""
    hover = IMG_ROOT / pid / cslug / "hover.jpg"
    if hover.exists() and hover.stat().st_size > 2000:
        return f"/products/axo-pdp/{pid}/{cslug}/hover.jpg"
    if len(gallery) > 1:
        return gallery[1]
    return gallery[0] if gallery else ""


def size_chart_for(
    kind: str,
    genders: list[str],
    *,
    name: str = "",
    sizes: list[str] | None = None,
) -> dict | None:
    note = (
        "발 길이를 재어 가장 가깝거나 같거나 큰 수치를 고르세요. "
        "Briq 표기 사이즈는 Arc'teryx UK 기준입니다."
    )
    if kind == "footwear":
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
        ]
        is_women = "womens" in genders and "mens" not in genders
        return {
            "id": "ax-shoes-womens" if is_women else "ax-shoes-mens",
            "titleKo": (
                "아크테릭스 여성 슈즈 사이즈 차트 (UK)"
                if is_women
                else "아크테릭스 남성 슈즈 사이즈 차트 (UK)"
            ),
            "noteKo": note,
            "headers": headers,
            "rows": rows,
        }
    if kind == "clothing":
        # Official Arc'teryx CM body-measurement charts (jacket vs pant, alpha vs numeric)
        n = (name or "").lower()
        if "womens" in genders and "mens" not in genders:
            gender = "womens"
        elif "mens" in genders and "womens" not in genders:
            gender = "mens"
        elif "women" in n:
            gender = "womens"
        else:
            gender = "mens"
        return chart_for(name, gender, sizes or [])
    return None


def collections_for(kind: str, genders: list[str]) -> tuple[str, list[str], str]:
    """Return (briq_category, axCollections, primary_subcategory)."""
    if kind == "footwear":
        cols = []
        if "womens" in genders:
            cols.append("ax-shoes-womens")
        if "mens" in genders:
            cols.append("ax-shoes-mens")
        if not cols:
            cols = ["ax-shoes-mens"]
        return "shoes", cols, cols[0]
    if kind == "accessories":
        cols = []
        if "womens" in genders:
            cols.append("ax-acc-womens")
        if "mens" in genders:
            cols.append("ax-acc-mens")
        if not cols:
            cols = ["ax-acc-mens", "ax-acc-womens"]
        return "accessories", cols, cols[0]
    # clothing → luxury outlet
    cols = []
    if "womens" in genders:
        cols.append("ax-outlet-womens")
    if "mens" in genders:
        cols.append("ax-outlet-mens")
    if not cols:
        cols = ["ax-outlet-mens"]
    return "luxury", cols, cols[0]


def default_sizes(kind: str, genders: list[str]) -> list[str]:
    if kind == "footwear":
        return ["7", "7.5", "8", "8.5", "9", "9.5", "10", "10.5", "11"]
    if kind == "accessories":
        return ["OS"]
    return ["S", "M", "L", "XL"]


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
    for j, feat in enumerate(pdp.get("features") or []):
        title = t(feat.get("title") or "")
        body = t(feat.get("body") or "")
        if not body:
            continue
        item = {"titleKo": title or "특징", "bodyKo": body}
        if images:
            item["image"] = images[(len(sections)) % len(images)]
        if len(sections) % 2 == 1:
            item["reverse"] = True
        sections.append(item)
    return sections[:8]


def main() -> None:
    raw = json.loads(RAW_PATH.read_text())
    pdp_all = json.loads(PDP_PATH.read_text())
    products_out: list[str] = []
    batch_start = datetime.now(timezone.utc).replace(microsecond=0)

    # Skip outdoor footwear SKUs already in ax-catalog to avoid duplicate cards
    existing_skus: set[str] = set()
    if EXISTING_AX.exists():
        for m in re.finditer(r'sku: "(X\d+)"', EXISTING_AX.read_text()):
            existing_skus.add(m.group(1))

    skipped_fw = 0
    for idx, p in enumerate(raw["products"]):
        pid = p["id"]
        kind = p["kind"]
        if kind == "footwear" and pid in existing_skus:
            # Still include outlet version with distinct id — user wants outlet stock.
            # Use axo- prefix always for outlet catalogue.
            pass

        pdp = pdp_all.get(pid) or {}
        genders = list(p.get("genders") or [p.get("gender") or "mens"])
        category, cols, sub = collections_for(kind, genders)

        sale_gbp = parse_gbp(
            pdp.get("gbpPrice")
            if pdp.get("gbpPrice") not in (None, "")
            else p.get("gbpPrice") or p.get("gbpListPrice") or 0
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
            sizes = default_sizes(kind, genders)
        sizes = sort_ax_sizes(sizes)

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
                # try any folder under pid
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
                lead_hover = list_hover(pid, cslug, gallery)
            for g in gallery:
                if g not in all_images:
                    all_images.append(g)

            color_ko = colour_name_ko(cname)
            for size in sizes:
                vid = f"axo-{pid.lower()}-{cslug}-{size.replace('.', '_').replace('/', '-')}"
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
                    f"        hoverImage: {js_str(list_hover(pid, cslug, gallery))},",
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
        style_id = f"axo-{pid.lower()}"
        chart = size_chart_for(kind, genders, name=name, sizes=sizes)
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
            f"    category: {js_str(category)},",
            f"    subcategory: {js_str(sub)},",
            f'    axCollections: {js_json(cols)} as Product["axCollections"],',
            f"    tags: {js_json(['arcteryx', '아크테릭스', 'outlet', '아울렛', kind, *cols, *genders])},",
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
        ]
        if chart:
            block.append(f"    sizeChart: {js_json(chart)},")
        block += [
            "    variants: [",
            *variants_blocks,
            "    ],",
            "  },",
        ]
        products_out.append("\n".join(block))

    header = """/** Auto-generated Arc'teryx Outlet catalogue — do not edit by hand. */
import type { Product } from "@/data/products";

export const axOutletCatalogProducts = [
"""
    OUT_PATH.write_text(header + "\n".join(products_out) + "\n] as unknown as Product[];\n")
    print(f"Wrote {len(products_out)} products → {OUT_PATH} (skipped fw dup note={skipped_fw})")


if __name__ == "__main__":
    main()
