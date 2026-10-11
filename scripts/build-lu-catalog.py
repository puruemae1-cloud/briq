#!/usr/bin/env python3
"""Build lu-catalog.ts — London Undercover umbrellas (Auto Compact / Telescopic / Full Length)."""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "src/data/lu/lu-pdp-raw.json"
CACHE_PATH = ROOT / "src/data/lu/lu-translate-cache.json"
OUT_PATH = ROOT / "src/data/lu/lu-catalog.ts"
IMG_ROOT = ROOT / "public/products/lu-pdp"

# GBP × 2100 × 1.06 + ₩50,000 → round to 천원
def gbp_to_krw(gbp: float | None) -> int:
    if gbp is None:
        return 0
    base = float(gbp) * 2100 * 1.06 + 50_000
    return int(round(base / 1_000) * 1_000)


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

# (handle suffix, style EN name, style KO name, category leaf id)
STYLE_DEFS = [
    ("auto-compact-umbrella", "Auto-Compact Umbrella", "오토컴팩트 우산", "lu-auto-compact"),
    ("whangee-telescopic-umbrella", "Whangee Telescopic Umbrella", "Whangee 텔레스코픽 우산", "lu-telescopic"),
    ("maple-telescopic-umbrella", "Maple Telescopic Umbrella", "Maple 텔레스코픽 우산", "lu-telescopic"),
    ("double-cg-umbrella", "Double CG Umbrella", "Double CG 장우산", "lu-full-length"),
    ("multi-cg-umbrella", "Multi CG Umbrella", "Multi CG 장우산", "lu-full-length"),
    ("e1-city-gent-umbrella", "E1 City Gent Umbrella", "E1 City Gent 장우산", "lu-full-length"),
    ("w1-city-gent-umbrella", "W1 City Gent Umbrella", "W1 City Gent 장우산", "lu-full-length"),
    ("city-lux-umbrella", "City Lux Umbrella", "City Lux 장우산", "lu-full-length"),
    ("city-gent-umbrella", "City Gent Umbrella", "City Gent 장우산", "lu-full-length"),
    ("oak-solid-stick-umbrella", "Oak Solid Stick Umbrella", "Oak Solid Stick 장우산", "lu-full-length"),
    ("classic-umbrella", "Classic Umbrella", "Classic 장우산", "lu-full-length"),
]

COLOR_KO = {
    "Black": "블랙",
    "Navy": "네이비",
    "Yellow": "옐로우",
    "Orange": "오렌지",
    "Red": "레드",
    "Brown": "브라운",
    "Tan": "탄",
    "Khaki": "카키",
    "Olive Green": "올리브 그린",
    "Light Olive Green": "라이트 올리브 그린",
    "Dark Grey": "다크 그레이",
    "Dark Gray": "다크 그레이",
    "Olive Drab": "올리브 드랩",
}


_KO: dict[str, str] = {}
if CACHE_PATH.exists():
    _KO = json.loads(CACHE_PATH.read_text())

_KO_NORM: dict[str, str] = {
    re.sub(r"\s+", " ", k).strip(): v for k, v in _KO.items()
}


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
    return s[:70] or "item"


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


def color_ko(name: str) -> str:
    raw = (name or "").strip()
    if not raw:
        return raw
    if raw in COLOR_KO:
        return COLOR_KO[raw]
    cached = t(raw)
    if cached and cached != raw and any("\uac00" <= c <= "\ud7a3" for c in cached):
        return cached
    return raw


def match_style(handle: str):
    for suf, en, ko, leaf in STYLE_DEFS:
        if handle.endswith(suf):
            return en, ko, leaf
    return None


def local_images(handle: str) -> list[str]:
    d = IMG_ROOT / handle
    if not d.exists():
        return []
    files = sorted(
        [p for p in d.glob("[0-9]*.jpg")],
        key=lambda p: int(p.stem) if p.stem.isdigit() else 999,
    )
    return [f"/products/lu-pdp/{handle}/{p.name}" for p in files if p.stat().st_size > 800]


def build_story(
    paras: list[str],
    bullets: list[str],
    images: list[str],
    style_ko: str,
) -> tuple[str, list[str], list[dict]]:
    """Return descriptionKo, featuresKo, storySections."""
    para_ko = [t(p) for p in paras if p]
    bullets_ko = [t(b) for b in bullets if b]
    desc = para_ko[0] if para_ko else f"{style_ko} — 런던언더커버의 영국 우산."
    features = bullets_ko[:12]

    sections: list[dict] = []
    # Lead story
    if para_ko:
        item: dict = {"titleKo": style_ko, "bodyKo": para_ko[0]}
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
        # Split bullets into 2 feature blocks mixed with images
        mid = max(1, len(bullets_ko) // 2)
        chunks = [bullets_ko[:mid], bullets_ko[mid:]]
        for j, chunk in enumerate(chunks):
            if not chunk:
                continue
            body = " · ".join(chunk)
            item = {
                "titleKo": "스펙" if j == 0 else "구성",
                "bodyKo": body,
            }
            if images:
                item["image"] = images[(len(sections)) % len(images)]
                if len(sections) % 2 == 1:
                    item["reverse"] = True
            sections.append(item)

    # Extra gallery images as caption/wide story beats
    used = {s.get("image") for s in sections if s.get("image")}
    for img in images:
        if img in used:
            continue
        item = {
            "titleKo": "갤러리",
            "bodyKo": f"{style_ko}의 디테일과 실루엣.",
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
    groups: dict[str, list[dict]] = {}
    meta: dict[str, tuple[str, str, str]] = {}

    for pid, p in raw.items():
        handle = p.get("handle") or ""
        matched = match_style(handle)
        if not matched:
            print("skip ungrouped", handle)
            continue
        en, ko, leaf = matched
        groups.setdefault(en, []).append(p)
        meta[en] = (en, ko, leaf)

    batch_start = datetime.now(timezone.utc).replace(microsecond=0)
    blocks: list[str] = []

    for idx, (style_en, items) in enumerate(sorted(groups.items(), key=lambda x: x[0])):
        style_en, style_ko, leaf = meta[style_en]
        # sort colourways by title
        items = sorted(items, key=lambda p: (p.get("title") or ""))
        parent_cols = ["umbrellas", "london-undercover", leaf]

        variants_out: list[dict] = []
        all_images: list[str] = []
        lead_image = ""
        lead_hover = ""
        min_price = None
        min_compare = None
        min_gbp = None
        min_gbp_list = None
        any_stock = False
        best_tags: list[str] = []
        best_body = ""
        source_url = ""

        for p in items:
            handle = p["handle"]
            v0 = (p.get("variants") or [{}])[0]
            color = (v0.get("option1") or v0.get("title") or "Default").strip()
            cslug = slugify(color)
            gbp = parse_gbp(v0.get("price"))
            gbp_list = parse_gbp(v0.get("compare_at_price")) if v0.get("compare_at_price") else 0.0
            if gbp_list <= gbp:
                gbp_list = 0.0
            price = gbp_to_krw(gbp)
            compare = gbp_to_krw(gbp_list) if gbp_list > gbp else None
            if compare and compare <= price:
                compare = None

            imgs = local_images(handle)
            if not imgs:
                # fallback CDN
                for i, im in enumerate(p.get("images") or [], 1):
                    src = im.get("src")
                    if src:
                        imgs.append(src)
            if not imgs:
                continue

            in_stock = bool(v0.get("available", p.get("collectionAvailable", True)))
            any_stock = any_stock or in_stock
            if not lead_image:
                lead_image = imgs[0]
                lead_hover = imgs[1] if len(imgs) > 1 else imgs[0]
                best_tags = [
                    x.strip()
                    for x in (
                        p.get("tags").split(",")
                        if isinstance(p.get("tags"), str)
                        else (p.get("tags") or [])
                    )
                    if str(x).strip()
                ]
                best_body = p.get("body_html") or ""
                source_url = f"https://londonundercover.co.uk/products/{handle}"

            for g in imgs:
                if g not in all_images:
                    all_images.append(g)

            if min_price is None or price < min_price:
                min_price = price
                min_gbp = gbp
                min_compare = compare
                min_gbp_list = gbp_list or None

            cko = color_ko(color)
            variants_out.append(
                {
                    "id": f"lu-{handle}",
                    "name": f"{color}",
                    "nameKo": cko,
                    "sku": str(v0.get("sku") or handle),
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
                    "luCollections": parent_cols,
                }
            )

        if not variants_out or not lead_image:
            print("skip empty", style_en)
            continue

        paras, bullets = parse_body(best_body)
        desc, features, story = build_story(paras, bullets, all_images or [lead_image], style_ko)

        badge = None
        if any("Best Selling" == t for t in best_tags):
            badge = "Best"
        if min_compare and min_compare > (min_price or 0):
            badge = "Sale"

        registered = (batch_start + timedelta(seconds=idx)).strftime(
            "%Y-%m-%dT%H:%M:%S.000Z"
        )
        style_id = f"lu-{slugify(style_en)}"
        accent = ACCENTS[idx % len(ACCENTS)]

        tech = []
        if bullets:
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
            f"    name: {js_str(style_en)},",
            f"    nameKo: {js_str(style_ko)},",
            '    brand: "런던언더커버",',
            f"    price: {min_price},",
        ]
        if min_compare:
            block.append(f"    compareAtPrice: {min_compare},")
        block += [
            '    category: "accessories",',
            f"    subcategory: {js_str(leaf)},",
            f'    luCollections: {js_json(parent_cols)} as Product["luCollections"],',
            f"    tags: {js_json(['london undercover', '런던언더커버', 'umbrella', '우산', leaf, *best_tags[:8]])},",
            f"    descriptionKo: {js_str(desc)},",
            f"    image: {js_str(lead_image)},",
            f"    images: {js_json(all_images[:24] or [lead_image])},",
            f"    hoverImage: {js_str(lead_hover)},",
            f"    accent: {js_str(accent)},",
        ]
        if badge:
            block.append(f"    badge: {js_str(badge)},")
        block += [
            f"    gbpPrice: {min_gbp},",
        ]
        if min_gbp_list:
            block.append(f"    gbpListPrice: {min_gbp_list},")
        block += [
            f"    sku: {js_str(variants_out[0]['sku'])},",
            f"    sourceUrl: {js_str(source_url)},",
            f"    registeredAt: {js_str(registered)},",
            '    editTier: "signature",',
            f"    storySections: {js_json(story)},",
            f"    featuresKo: {js_json(features)},",
        ]
        if tech:
            block.append(f"    techSpecs: {js_json(tech)},")
        block.append("    variants: [")
        for v in variants_out:
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
        "/** Auto-generated London Undercover umbrella catalogue — do not edit by hand. */\n"
        'import type { Product } from "@/data/products";\n\n'
        "export const luCatalogProducts = [\n"
        + ",\n".join(blocks)
        + "\n] as unknown as Product[];\n"
    )
    OUT_PATH.write_text(out)
    print(f"Wrote {len(blocks)} styles → {OUT_PATH}")


if __name__ == "__main__":
    main()
