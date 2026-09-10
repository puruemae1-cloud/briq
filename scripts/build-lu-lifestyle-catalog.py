#!/usr/bin/env python3
"""Build lu-lifestyle-catalog.ts — London Undercover lifestyle (Everyday/Grooming/Home/Stationery/Bags)."""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "src/data/lu/lu-lifestyle-pdp-raw.json"
CACHE_PATH = ROOT / "src/data/lu/lu-translate-cache.json"
OUT_PATH = ROOT / "src/data/lu/lu-lifestyle-catalog.ts"
IMG_ROOT = ROOT / "public/products/lu-pdp"

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
if CACHE_PATH.exists():
    _KO = json.loads(CACHE_PATH.read_text())

_KO_NORM: dict[str, str] = {
    re.sub(r"\s+", " ", k).strip(): v for k, v in _KO.items()
}


def gbp_to_krw(gbp: float | None) -> int:
    """GBP × 2100 × 1.06 + ₩50,000 — round to 천원."""
    if gbp is None:
        return 0
    base = float(gbp) * 2100 * 1.06 + 50_000
    return int(round(base / 1_000) * 1_000)


def t(text: str | None) -> str:
    if not text:
        return ""
    s = str(text).strip()
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    if s in _KO:
        return _KO[s]
    return _KO_NORM.get(s, s)


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:80] or "item"


def js_str(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def js_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)


def parse_gbp(val) -> float:
    if val is None or val == "":
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).replace("£", "").replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        m = re.search(r"(\d+(?:\.\d+)?)", s)
        return float(m.group(1)) if m else 0.0


class ListHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.paras: list[str] = []
        self.bullets: list[str] = []
        self._buf: list[str] = []
        self._in_li = False
        self._in_p = False

    def handle_starttag(self, tag, attrs):
        if tag == "li":
            self._in_li = True
            self._buf = []
        elif tag == "p":
            self._in_p = True
            self._buf = []
        elif tag in ("br", "hr") and (self._in_li or self._in_p):
            self._buf.append(" ")

    def handle_endtag(self, tag):
        if tag == "li" and self._in_li:
            text = re.sub(r"\s+", " ", "".join(self._buf)).strip()
            if text:
                self.bullets.append(text)
            self._in_li = False
        elif tag == "p" and self._in_p:
            text = re.sub(r"\s+", " ", "".join(self._buf)).strip()
            if text:
                # Prefer sentence-like chunks when a <p> packs title + body via <br>
                chunks = [c.strip() for c in re.split(r"(?<=[.!?])\s+(?=[A-Z])", text) if c.strip()]
                if len(chunks) >= 2 and len(chunks[0]) < 80:
                    self.paras.extend(chunks)
                else:
                    self.paras.append(text)
            self._in_p = False

    def handle_data(self, data):
        if self._in_li or self._in_p:
            self._buf.append(data)


def parse_body(html: str) -> tuple[list[str], list[str]]:
    p = ListHTMLParser()
    try:
        p.feed(html or "")
    except Exception:
        pass
    return p.paras, p.bullets


def local_images(handle: str) -> list[str]:
    d = IMG_ROOT / handle
    if not d.exists():
        return []
    files = sorted(
        [p for p in d.glob("[0-9]*.jpg")],
        key=lambda p: int(p.stem) if p.stem.isdigit() else 999,
    )
    return [f"/products/lu-pdp/{handle}/{p.name}" for p in files if p.stat().st_size > 800]


def clean_title(title: str) -> str:
    return re.sub(r"^London Undercover\s+", "", title or "", flags=re.I).strip()


def build_story(
    paras: list[str],
    bullets: list[str],
    images: list[str],
    name_ko: str,
) -> tuple[str, list[str], list[dict]]:
    para_ko = [t(p) for p in paras if p]
    bullets_ko = [t(b) for b in bullets if b]
    desc = para_ko[0] if para_ko else f"{name_ko} — 런던언더커버 라이프스타일."
    features = bullets_ko[:12]

    sections: list[dict] = []
    if para_ko:
        item: dict = {"titleKo": name_ko, "bodyKo": para_ko[0]}
        if images:
            item["image"] = images[0]
        sections.append(item)
    for i, para in enumerate(para_ko[1:4], start=1):
        item = {"titleKo": "디테일", "bodyKo": para}
        if images:
            item["image"] = images[i % len(images)]
            if i % 2 == 1:
                item["reverse"] = True
        sections.append(item)
    if bullets_ko:
        mid = max(1, len(bullets_ko) // 2)
        for j, chunk in enumerate([bullets_ko[:mid], bullets_ko[mid:]]):
            if not chunk:
                continue
            item = {
                "titleKo": "스펙" if j == 0 else "구성",
                "bodyKo": " · ".join(chunk),
            }
            if images:
                item["image"] = images[len(sections) % len(images)]
                if len(sections) % 2 == 1:
                    item["reverse"] = True
            sections.append(item)
    used = {s.get("image") for s in sections if s.get("image")}
    for img in images:
        if img in used:
            continue
        item = {
            "titleKo": "갤러리",
            "bodyKo": f"{name_ko}의 디테일.",
            "image": img,
            "layout": "wide",
        }
        if len(sections) % 2 == 1:
            item["reverse"] = True
        sections.append(item)
        if len(sections) >= 10:
            break
    return desc, features, sections[:10]


def main() -> None:
    raw = json.loads(RAW_PATH.read_text())
    batch_start = datetime.now(timezone.utc).replace(microsecond=0)
    blocks: list[str] = []
    cols_base = ["london-undercover", "lu-lifestyle"]

    items = sorted(raw.values(), key=lambda p: (p.get("title") or "").lower())
    for idx, p in enumerate(items):
        handle = p.get("handle") or f"item-{idx}"
        title = p.get("title") or handle
        name_en = clean_title(title)
        name_ko = t(name_en) or t(title) or name_en
        imgs = local_images(handle)
        if not imgs:
            for im in p.get("images") or []:
                if im.get("src"):
                    imgs.append(im["src"])
        if not imgs:
            print("skip no images", handle)
            continue

        variants_shop = p.get("variants") or [{}]
        # Lifestyle Shopify products are usually 1 colourway each; keep all variants if present
        flat_variants: list[dict] = []
        any_stock = False
        min_price = None
        min_compare = None
        min_gbp = None
        min_gbp_list = None

        for vi, v0 in enumerate(variants_shop):
            color = (v0.get("option1") or v0.get("title") or "Default").strip()
            if color.lower() in ("default title", "default"):
                color = "One Size"
            cslug = slugify(color) if color != "One Size" else "os"
            gbp = parse_gbp(v0.get("price"))
            gbp_list = parse_gbp(v0.get("compare_at_price")) if v0.get("compare_at_price") else 0.0
            if gbp_list <= gbp:
                gbp_list = 0.0
            price = gbp_to_krw(gbp)
            compare = gbp_to_krw(gbp_list) if gbp_list > gbp else None
            if compare and compare <= price:
                compare = None
            in_stock = bool(v0.get("available", p.get("collectionAvailable", True)))
            any_stock = any_stock or in_stock
            if min_price is None or price < min_price:
                min_price = price
                min_gbp = gbp
                min_compare = compare
                min_gbp_list = gbp_list or None

            color_name = color if color != "One Size" else name_en
            cko = t(color) if color != "One Size" else name_ko
            flat_variants.append(
                {
                    "id": f"lu-{handle}" + (f"-{cslug}" if len(variants_shop) > 1 else ""),
                    "name": color_name,
                    "nameKo": cko,
                    "sku": str(v0.get("sku") or f"{handle}-{vi}"),
                    "gbpPrice": gbp,
                    "price": price,
                    **({"compareAtPrice": compare} if compare else {}),
                    "image": imgs[0],
                    "images": imgs,
                    "hoverImage": imgs[1] if len(imgs) > 1 else imgs[0],
                    "sourceUrl": f"https://londonundercover.co.uk/products/{handle}",
                    "inStock": in_stock,
                    "colorKey": cslug,
                    "colorNameKo": cko,
                    "luCollections": cols_base,
                }
            )

        paras, bullets = parse_body(p.get("body_html") or "")
        desc, features, story = build_story(paras, bullets, imgs, name_ko)

        tags_raw = p.get("tags") or []
        if isinstance(tags_raw, str):
            tags_raw = [x.strip() for x in tags_raw.split(",") if x.strip()]
        life_cols = p.get("briqLifestyleCols") or []
        tags = [
            "london undercover",
            "런던언더커버",
            "lifestyle",
            "라이프스타일",
            "lu-lifestyle",
            *life_cols,
            *list(tags_raw)[:6],
        ]

        badge = None
        if any(str(x) == "Best Selling" for x in tags_raw):
            badge = "Best"
        if min_compare and min_compare > (min_price or 0):
            badge = "Sale"

        registered = (batch_start + timedelta(seconds=idx)).strftime(
            "%Y-%m-%dT%H:%M:%S.000Z"
        )
        style_id = f"lu-{handle}"
        accent = ACCENTS[idx % len(ACCENTS)]

        tech = []
        for b in bullets[:8]:
            ko = t(b)
            if ":" in ko:
                lab, val = ko.split(":", 1)
                tech.append({"labelKo": lab.strip(), "valueKo": val.strip()})
            else:
                tech.append({"labelKo": "특징", "valueKo": ko})

        block = [
            "  {",
            f"    id: {js_str(style_id)},",
            f"    name: {js_str(name_en)},",
            f"    nameKo: {js_str(name_ko)},",
            '    brand: "런던언더커버",',
            f"    price: {min_price},",
        ]
        if min_compare:
            block.append(f"    compareAtPrice: {min_compare},")
        block += [
            '    category: "accessories",',
            '    subcategory: "lu-lifestyle",',
            f'    luCollections: {js_json(cols_base)} as Product["luCollections"],',
            f"    tags: {js_json(tags)},",
            f"    descriptionKo: {js_str(desc)},",
            f"    image: {js_str(imgs[0])},",
            f"    images: {js_json(imgs[:24])},",
            f"    hoverImage: {js_str(imgs[1] if len(imgs) > 1 else imgs[0])},",
            f"    accent: {js_str(accent)},",
        ]
        if badge:
            block.append(f"    badge: {js_str(badge)},")
        block.append(f"    gbpPrice: {min_gbp},")
        if min_gbp_list:
            block.append(f"    gbpListPrice: {min_gbp_list},")
        block += [
            f"    sku: {js_str(flat_variants[0]['sku'])},",
            f'    sourceUrl: {js_str(f"https://londonundercover.co.uk/products/{handle}")},',
            f"    registeredAt: {js_str(registered)},",
            '    editTier: "signature",',
            f"    storySections: {js_json(story)},",
            f"    featuresKo: {js_json(features)},",
        ]
        if tech:
            block.append(f"    techSpecs: {js_json(tech)},")
        block.append("    variants: [")
        for v in flat_variants:
            block.append("      {")
            for k, val in v.items():
                if isinstance(val, bool):
                    block.append(f"        {k}: {'true' if val else 'false'},")
                elif isinstance(val, (int, float)):
                    block.append(f"        {k}: {val},")
                elif isinstance(val, list):
                    if k == "luCollections":
                        block.append(
                            f'        luCollections: {js_json(val)} as Product["luCollections"],'
                        )
                    else:
                        block.append(f"        {k}: {js_json(val)},")
                else:
                    block.append(f"        {k}: {js_str(str(val))},")
            block.append("      },")
        block += [
            "    ],",
            f"    inStock: {'true' if any_stock else 'false'},",
            "  }",
        ]
        blocks.append("\n".join(block))

    out = (
        "/** Auto-generated London Undercover lifestyle catalogue — do not edit by hand. */\n"
        'import type { Product } from "@/data/products";\n\n'
        "export const luLifestyleCatalogProducts = [\n"
        + ",\n".join(blocks)
        + "\n] as unknown as Product[];\n"
    )
    OUT_PATH.write_text(out)
    print(f"Wrote {len(blocks)} products → {OUT_PATH}")


if __name__ == "__main__":
    main()
