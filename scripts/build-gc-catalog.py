#!/usr/bin/env python3
"""Build Gucci catalogue from scraped raw (handbags + women's RTW).

Pricing: KRW = round_천원(GBP × 2100 × 1.05 × 1.15)
Prefer official Korean copy from Gucci catalog API; fall back to gtx translate.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

from plp_hover import pick_hover_local

ROOT = Path(__file__).resolve().parents[1]
HANDBAG_RAW = ROOT / "src/data/gc/gc-catalog-raw.json"
RTW_RAW = ROOT / "src/data/gc/gc-rtw-catalog-raw.json"
OUT_JSON = ROOT / "src/data/gc/gc-catalog.json"
OUT_TS = ROOT / "src/data/gc/gc-catalog.ts"
CACHE_PATH = ROOT / "src/data/gc/gc-translate-cache.json"

# Back-compat alias
RAW_PATH = HANDBAG_RAW

HANDBAG_LEAF_COLLECTIONS = [
    "gc-women-shoulder-bags",
    "gc-women-mini-bags",
    "gc-women-crossbody-bags",
    "gc-women-tote-bags",
    "gc-women-top-handle-bags",
    "gc-women-backpacks-beltbags",
    "gc-women-clutches-evening",
    "gc-women-personalised",
]

RTW_LEAF_COLLECTIONS = [
    "gc-women-knitwear",
    "gc-women-tops-shirts",
    "gc-women-tshirts-sweatshirts",
    "gc-women-dresses",
    "gc-women-pants-shorts",
    "gc-women-denim",
    "gc-women-skirts",
    "gc-women-swimwear",
    "gc-women-coats-jackets",
    "gc-women-outerwear",
    "gc-women-leather",
    "gc-women-activewear",
    "gc-women-cocktail-evening",
]

# Keep old name for any external imports
LEAF_COLLECTIONS = HANDBAG_LEAF_COLLECTIONS

# Official Gucci women RTW Italian size guide (approx body measurements).
GC_WOMEN_RTW_SIZE_CHART = {
    "id": "gc-women-rtw-it",
    "titleKo": "구찌 여성 의류 사이즈 차트",
    "noteKo": (
        "구찌 여성 레디투웨어는 이탈리아(IT) 사이즈를 기준으로 표기합니다. "
        "브랜드·시즌·실루엣에 따라 핏이 다를 수 있으니 참고용으로 확인해 주세요."
    ),
    "headers": ["IT", "KR", "UK", "US", "FR", "가슴 (cm)", "허리 (cm)", "엉덩이 (cm)"],
    "rows": [
        ["34", "44", "4", "00", "32", "80", "58", "86"],
        ["36", "44", "6", "0", "34", "84", "62", "90"],
        ["38", "55", "8", "2", "36", "88", "66", "94"],
        ["40", "55", "10", "4", "38", "92", "70", "98"],
        ["42", "66", "12", "6", "40", "96", "74", "102"],
        ["44", "66", "14", "8", "42", "100", "78", "106"],
        ["46", "77", "16", "10", "44", "104", "82", "110"],
        ["48", "77", "18", "12", "46", "108", "86", "114"],
    ],
}


def gbp_to_krw(gbp: float | None) -> int:
    if gbp is None:
        return 0
    base = float(gbp) * 2100 * 1.05 * 1.15
    return int(round(base / 1_000) * 1_000)


_KO: dict[str, str] = {}
if CACHE_PATH.exists():
    _KO = json.loads(CACHE_PATH.read_text())


def en_ratio(s: str) -> float:
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return 0.0
    latin = sum(1 for c in letters if ("A" <= c <= "Z") or ("a" <= c <= "z"))
    return latin / len(letters)


def gtx(text: str) -> str:
    q = urllib.parse.quote(text[:4500])
    url = (
        "https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl=en&tl=ko&dt=t&q={q}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=35) as r:
        data = json.loads(r.read().decode())
    return "".join(part[0] for part in data[0] if part and part[0])


def t(text: str | None) -> str:
    s = re.sub(r"\s+", " ", (text or "").strip())
    if not s:
        return ""
    if s in _KO and en_ratio(_KO[s]) < 0.55:
        return _KO[s]
    if en_ratio(s) < 0.35 or len(s) < 4:
        return s
    try:
        ko = gtx(s).strip()
        if ko:
            _KO[s] = ko
            return ko
    except Exception:
        pass
    return s


def html_to_text(html: str) -> str:
    s = unescape(html or "")
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"</p>", "\n", s, flags=re.I)
    s = re.sub(r"<li>", "• ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n\n", s)
    return s.strip()


def accent_for(key: str) -> str:
    h = hashlib.md5((key or "x").encode()).hexdigest()
    r = 40 + int(h[0:2], 16) % 80
    g = 40 + int(h[2:4], 16) % 80
    b = 40 + int(h[4:6], 16) % 80
    return f"#{r:02x}{g:02x}{b:02x}"


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:70] or "item"


def clean_name_ko(name: str) -> str:
    s = (name or "").strip()
    m = re.match(r"^\[([^\]]+)\]\s*(.*)$", s)
    if m:
        inner, rest = m.group(1).strip(), m.group(2).strip()
        return f"{inner} {rest}".strip() if rest else inner
    return s


def strip_gucci_warranty(text: str) -> str:
    if not text:
        return ""
    s = text.replace("\xa0", " ").replace("\u202f", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"품질보증기준\s*:[^·\n]*", "", s, flags=re.I)
    s = re.sub(
        r"AS\s*유선접수\s*:[^·\n]*clientservice\.kr@gucci\.com",
        "",
        s,
        flags=re.I,
    )
    s = re.sub(r"clientservice\.kr@gucci\.com", "", s, flags=re.I)
    s = re.sub(
        r"AS\s*유선접수\s*:[^·\n]*02-3452-1921[^·\n]*",
        "",
        s,
        flags=re.I,
    )
    s = re.sub(r"(?:\s*[·•]\s*){2,}", " · ", s)
    s = re.sub(r"^\s*[·•]\s*", "", s)
    s = re.sub(r"\s*[·•]\s*$", "", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r"[ \t]+\n", "\n", s)
    return s.strip(" \t·•\n")


def is_gucci_warranty_line(line: str) -> bool:
    s = (line or "").replace("\xa0", " ")
    if "품질보증기준" in s:
        return True
    if "clientservice.kr@gucci.com" in s.lower():
        return True
    if re.search(r"AS\s*유선접수", s, flags=re.I):
        return True
    return False


def detail_lines(parts: list | None) -> list[str]:
    out: list[str] = []
    for p in parts or []:
        line = html_to_text(str(p))
        if not line:
            continue
        if re.fullmatch(r"[A-Z]{1,3}\d{2}", line):
            continue
        if is_gucci_warranty_line(line):
            cleaned = strip_gucci_warranty(line)
            if cleaned:
                out.append(cleaned)
            continue
        if "전자의료" in line or "electromedical" in line.lower() or "WARNING:" in line:
            before = re.split(r"WARNING:|경고:", line, maxsplit=1)[0].strip()
            if before:
                out.append(before)
            continue
        out.append(line)
    return out


def care_lines(care: str | None) -> list[str]:
    if not care:
        return []
    return [html_to_text(x) for x in care.split("|") if html_to_text(x)]


def format_size_label(size: str) -> str:
    s = (size or "").strip()
    if not s:
        return "One Size"
    if s.isdigit():
        return f"IT {s}"
    return s.upper() if len(s) <= 4 else s


def size_slug(size: str) -> str:
    return slugify(format_size_label(size))


def common_copy(row: dict) -> dict:
    ko = row.get("translationKo") or {}
    en = row.get("translationEn") or {}
    code = row.get("productCode") or row.get("id") or ""

    title_en = (row.get("title") or en.get("name") or code).strip()
    name_ko = clean_name_ko(ko.get("name") or "") or t(title_en)

    color_en = (row.get("variant") or en.get("variationDescription") or "").strip()
    color_ko = (ko.get("variationDescription") or "").strip() or (
        t(color_en) if color_en else ""
    )
    colors = ko.get("colors") or en.get("colors") or []
    if not color_ko and colors:
        color_ko = colors[0].get("name") or ""

    editorial_ko = strip_gucci_warranty(
        html_to_text(ko.get("editorialDescription") or "")
    )
    editorial_en = html_to_text(en.get("editorialDescription") or "")
    if not editorial_ko and editorial_en:
        editorial_ko = strip_gucci_warranty(t(editorial_en))

    details_ko = [
        strip_gucci_warranty(x) for x in detail_lines(ko.get("detailParts"))
    ]
    details_ko = [x for x in details_ko if x]
    if not details_ko:
        details_ko = [
            strip_gucci_warranty(t(x))
            for x in detail_lines(en.get("detailParts"))
        ]
        details_ko = [x for x in details_ko if x]

    care_ko = care_lines(ko.get("materialCare"))
    if not care_ko:
        care_ko = [t(x) for x in care_lines(en.get("materialCare"))]

    materials_ko = ko.get("materials") or []
    if not materials_ko and en.get("materials"):
        materials_ko = [t(x) for x in en["materials"]]

    images = list(row.get("localImages") or [])
    if not images and row.get("localImage"):
        images = [row["localImage"]]
    if not images:
        remotes = row.get("images") or (
            [] if not row.get("image") else [row["image"]]
        )
        images = remotes[:1]

    image = images[0] if images else ""
    hover = (
        row.get("localHover")
        or pick_hover_local(
            images,
            remote_images=row.get("images") or [],
            explicit=None,
        )
        or image
    )

    description_bits = [editorial_ko] if editorial_ko else []
    if details_ko:
        description_bits.append(" · ".join(details_ko[:8]))
    description_ko = strip_gucci_warranty(
        "\n\n".join(x for x in description_bits if x).strip()
    )

    story: list[dict] = []
    if editorial_ko:
        story.append(
            {"titleKo": name_ko, "bodyKo": editorial_ko, "image": image}
        )
    if details_ko:
        story.append(
            {
                "titleKo": "디테일",
                "bodyKo": strip_gucci_warranty(" · ".join(details_ko)),
                "image": images[1] if len(images) > 1 else image,
                "reverse": True,
            }
        )
    if materials_ko:
        story.append(
            {
                "titleKo": "소재",
                "bodyKo": " · ".join(materials_ko),
                "image": images[2] if len(images) > 2 else image,
            }
        )
    if care_ko:
        story.append(
            {
                "titleKo": "케어",
                "bodyKo": " · ".join(care_ko),
                "image": images[3] if len(images) > 3 else image,
                "reverse": True,
            }
        )
    for i, img in enumerate(images[1:], start=1):
        if len(story) >= 8:
            break
        story.append(
            {
                "titleKo": "갤러리",
                "bodyKo": f"{name_ko}의 디테일.",
                "image": img,
                "layout": "wide",
                "reverse": i % 2 == 0,
            }
        )

    return {
        "code": code,
        "title_en": title_en,
        "name_ko": name_ko,
        "color_en": color_en,
        "color_ko": color_ko,
        "color_key": slugify(color_en or color_ko or "default"),
        "images": images,
        "image": image,
        "hover": hover,
        "description_ko": description_ko,
        "story": story,
    }


def build_handbag_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    code = row.get("productCode") or row.get("id")
    if not code:
        return None
    gbp = row.get("gbpPrice")
    if gbp is None:
        return None
    price = gbp_to_krw(float(gbp))
    if price <= 0:
        return None

    cols = [
        c
        for c in (row.get("collections") or [])
        if c in HANDBAG_LEAF_COLLECTIONS or c == "gc-handbags"
    ]
    if any(c in HANDBAG_LEAF_COLLECTIONS for c in cols) and "gc-handbags" not in cols:
        cols.append("gc-handbags")
    cols = sorted(set(cols))
    if not cols:
        cols = ["gc-handbags"]

    leaf = next((c for c in HANDBAG_LEAF_COLLECTIONS if c in cols), "gc-handbags")
    copy = common_copy(row)
    pid = f"gc-{str(code).lower()}"
    registered = (prev or {}).get("registeredAt") or now_iso

    variant = {
        "id": f"{pid}-u",
        "name": f"{copy['title_en']} — {copy['color_en'] or 'One Size'}".strip(" —"),
        "nameKo": f"{copy['name_ko']} — {copy['color_ko'] or '원 사이즈'}".strip(" —"),
        "sku": code,
        "gbpPrice": float(gbp),
        "price": price,
        "image": copy["image"],
        "images": copy["images"],
        "hoverImage": copy["hover"],
        "sourceUrl": row.get("url") or "",
        "inStock": bool(row.get("inStock", True)),
        "colorKey": copy["color_key"],
        "colorNameKo": copy["color_ko"] or copy["color_en"] or "기본",
        "size": "One Size",
        "gcCollections": cols,
    }

    tags = ["gucci", "구찌", "handbag", "핸드백", *cols]
    badge = None
    label = (row.get("label") or "").lower()
    if "new" in label:
        badge = "New"

    return {
        "id": pid,
        "name": copy["title_en"],
        "nameKo": copy["name_ko"],
        "brand": "구찌",
        "price": price,
        "category": "bags",
        "subcategory": leaf,
        "gcCollections": cols,
        "tags": tags,
        "descriptionKo": copy["description_ko"],
        "image": copy["image"],
        "images": copy["images"],
        "hoverImage": copy["hover"],
        "accent": accent_for(code),
        "badge": badge,
        "gbpPrice": float(gbp),
        "sku": code,
        "sourceUrl": row.get("url") or "",
        "inStock": bool(row.get("inStock", True)),
        "variants": [variant],
        "storySections": copy["story"],
        "registeredAt": registered,
        "editTier": "new" if badge == "New" else "signature",
    }


def build_rtw_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    code = row.get("productCode") or row.get("id")
    if not code:
        return None
    gbp = row.get("gbpPrice")
    if gbp is None:
        return None
    price = gbp_to_krw(float(gbp))
    if price <= 0:
        return None

    cols = [
        c
        for c in (row.get("collections") or [])
        if c in {*RTW_LEAF_COLLECTIONS, "gc-women-rtw", "gc-women", "gucci"}
    ]
    cols = sorted(set([*cols, "gc-women-rtw", "gc-women", "gucci"]))

    leaf = next((c for c in RTW_LEAF_COLLECTIONS if c in cols), "gc-women-rtw")
    copy = common_copy(row)
    pid = f"gc-{str(code).lower()}"
    registered = (prev or {}).get("registeredAt") or now_iso
    in_stock = bool(row.get("inStock", True))

    size_rows = row.get("sizes") or []
    variants: list[dict] = []
    if size_rows:
        for sz in size_rows:
            size_raw = str(sz.get("size") or "").strip()
            if not size_raw:
                continue
            label = format_size_label(size_raw)
            slug = size_slug(size_raw)
            sku = str(sz.get("sku") or f"{code}-{slug}")
            variants.append(
                {
                    "id": f"{pid}-{slug}",
                    "name": f"{copy['title_en']} — {label}",
                    "nameKo": f"{copy['name_ko']} — {label}",
                    "sku": sku,
                    "gbpPrice": float(gbp),
                    "price": price,
                    "image": copy["image"],
                    "images": copy["images"],
                    "hoverImage": copy["hover"],
                    "sourceUrl": row.get("url") or "",
                    "inStock": in_stock,
                    "colorKey": copy["color_key"],
                    "colorNameKo": copy["color_ko"] or copy["color_en"] or "기본",
                    "size": label,
                    "gcCollections": cols,
                }
            )
    if not variants:
        variants = [
            {
                "id": f"{pid}-os",
                "name": f"{copy['title_en']} — One Size",
                "nameKo": f"{copy['name_ko']} — 원 사이즈",
                "sku": code,
                "gbpPrice": float(gbp),
                "price": price,
                "image": copy["image"],
                "images": copy["images"],
                "hoverImage": copy["hover"],
                "sourceUrl": row.get("url") or "",
                "inStock": in_stock,
                "colorKey": copy["color_key"],
                "colorNameKo": copy["color_ko"] or copy["color_en"] or "기본",
                "size": "One Size",
                "gcCollections": cols,
            }
        ]

    tags = ["gucci", "구찌", "rtw", "의류", "여성", "ready-to-wear", *cols]
    badge = None
    label = (row.get("label") or "").lower()
    if "new" in label:
        badge = "New"

    return {
        "id": pid,
        "name": copy["title_en"],
        "nameKo": copy["name_ko"],
        "brand": "구찌",
        "price": price,
        "category": "luxury",
        "subcategory": leaf,
        "gcCollections": cols,
        "tags": tags,
        "descriptionKo": copy["description_ko"],
        "image": copy["image"],
        "images": copy["images"],
        "hoverImage": copy["hover"],
        "accent": accent_for(code),
        "badge": badge,
        "gbpPrice": float(gbp),
        "sku": code,
        "sourceUrl": row.get("url") or "",
        "inStock": in_stock,
        "variants": variants,
        "sizeChart": GC_WOMEN_RTW_SIZE_CHART,
        "storySections": copy["story"],
        "registeredAt": registered,
        "editTier": "new" if badge == "New" else "signature",
    }


def build_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    kind = (row.get("kind") or "").lower()
    cols = row.get("collections") or []
    if kind == "rtw" or any(
        c in RTW_LEAF_COLLECTIONS or c in {"gc-women-rtw", "gc-women"} for c in cols
    ):
        return build_rtw_product(row, prev, now_iso)
    return build_handbag_product(row, prev, now_iso)


def load_rows() -> list[dict]:
    rows: list[dict] = []
    if HANDBAG_RAW.exists():
        data = json.loads(HANDBAG_RAW.read_text())
        for row in data.get("products") or []:
            row = dict(row)
            row.setdefault("kind", "handbag")
            rows.append(row)
    if RTW_RAW.exists():
        data = json.loads(RTW_RAW.read_text())
        for row in data.get("products") or []:
            row = dict(row)
            row["kind"] = "rtw"
            rows.append(row)
    return rows


def main() -> None:
    rows = load_rows()
    if not rows:
        raise SystemExit(
            "Missing Gucci raw catalogues — run scrape-gc-handbags.py "
            "and/or scrape-gc-womens-rtw.py first"
        )

    prev_by_sku: dict[str, dict] = {}
    if OUT_JSON.exists():
        for p in json.loads(OUT_JSON.read_text()):
            if p.get("sku"):
                prev_by_sku[str(p["sku"])] = p

    now_iso = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    products: list[dict] = []
    seen_ids: set[str] = set()
    for i, row in enumerate(rows, start=1):
        sku = str(row.get("productCode") or row.get("id") or "")
        prod = build_product(row, prev_by_sku.get(sku), now_iso)
        if not prod:
            continue
        if prod["id"] in seen_ids:
            if row.get("kind") == "rtw":
                products = [p for p in products if p["id"] != prod["id"]]
                products.append(prod)
            continue
        seen_ids.add(prod["id"])
        products.append(prod)
        if i % 50 == 0:
            CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2))
            print(f"built {i}/{len(rows)}", flush=True)
            time.sleep(0.05)

    products.sort(key=lambda p: p["id"])
    OUT_JSON.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n")
    OUT_TS.write_text(
        'import type { Product } from "@/data/products";\n'
        'import data from "./gc-catalog.json";\n\n'
        "/** Auto-generated — Gucci handbags + women's ready-to-wear. */\n"
        "export const gcCatalogProducts = data as unknown as Product[];\n"
    )
    CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2))
    print(f"Wrote {len(products)} products → {OUT_JSON}", flush=True)
    bags_n = sum(1 for p in products if p.get("category") == "bags")
    rtw_n = sum(1 for p in products if p.get("category") == "luxury")
    print(f"  handbags: {bags_n}  rtw: {rtw_n}", flush=True)
    for leaf in RTW_LEAF_COLLECTIONS:
        n = sum(1 for p in products if leaf in (p.get("gcCollections") or []))
        print(f"  {leaf}: {n}", flush=True)


if __name__ == "__main__":
    main()
