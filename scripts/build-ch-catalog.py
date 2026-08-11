#!/usr/bin/env python3
"""Build Chanel RTW catalogue → src/data/ch/ch-catalog.json + ch-catalog.ts.

Pricing (same as Gucci): KRW = round_만원(GBP × 2100 × 1.05 × 1.15)
Korean copy via gtx + ch-translate-cache.json.
Size chart: French RTW FR 34–50.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "src/data/ch/ch-rtw-catalog-raw.json"
OUT_JSON = ROOT / "src/data/ch/ch-catalog.json"
OUT_TS = ROOT / "src/data/ch/ch-catalog.ts"
CACHE_PATH = ROOT / "src/data/ch/ch-translate-cache.json"

SHAPE_LEAVES = [
    "ch-women-jackets",
    "ch-women-dresses",
    "ch-women-blouses-tops",
    "ch-women-cardigans-sweaters",
    "ch-women-skirts",
    "ch-women-trousers-shorts",
    "ch-women-swimwear",
    "ch-women-outerwear",
]

PARENT_COLS = ["chanel", "ch-women", "ch-women-rtw", "ch-women-looks"]

# French women's RTW conversion (Chanel FR sizes). Body measures are approximate
# maison / industry references for shopper guidance.
CH_WOMEN_RTW_SIZE_CHART = {
    "id": "ch-women-rtw",
    "titleKo": "샤넬 여성 레디투웨어 사이즈 가이드",
    "noteKo": (
        "샤넬 레디투웨어는 프랑스(FR) 사이즈를 기준으로 합니다. Briq 사이즈 선택란의 "
        "FR 34·36 등은 제품에 표기된 사이즈와 동일합니다. 브랜드·시즌·실루엣에 따라 "
        "핏이 다를 수 있으니 참고용으로 확인해 주세요."
    ),
    "headers": [
        "FR",
        "IT",
        "UK",
        "US",
        "BUST (CM)",
        "WAIST (CM)",
        "HIP (CM)",
    ],
    "rows": [
        ["34", "38", "6", "2", "80", "62", "86"],
        ["36", "40", "8", "4", "84", "66", "90"],
        ["38", "42", "10", "6", "88", "70", "94"],
        ["40", "44", "12", "8", "92", "74", "98"],
        ["42", "46", "14", "10", "96", "78", "102"],
        ["44", "48", "16", "12", "100", "82", "106"],
        ["46", "50", "18", "14", "104", "86", "110"],
        ["48", "52", "20", "16", "108", "90", "114"],
        ["50", "54", "22", "18", "112", "94", "118"],
    ],
    "tabs": [
        {
            "id": "fr",
            "labelKo": "FR 사이즈",
            "headers": [
                "FR",
                "IT",
                "UK",
                "US",
                "BUST (CM)",
                "WAIST (CM)",
                "HIP (CM)",
            ],
            "rows": [
                ["34", "38", "6", "2", "80", "62", "86"],
                ["36", "40", "8", "4", "84", "66", "90"],
                ["38", "42", "10", "6", "88", "70", "94"],
                ["40", "44", "12", "8", "92", "74", "98"],
                ["42", "46", "14", "10", "96", "78", "102"],
                ["44", "48", "16", "12", "100", "82", "106"],
                ["46", "50", "18", "14", "104", "86", "110"],
                ["48", "52", "20", "16", "108", "90", "114"],
                ["50", "54", "22", "18", "112", "94", "118"],
            ],
        }
    ],
}


def gbp_to_krw(gbp: float | None) -> int:
    """KRW = round_만원(GBP × 2100 × 1.05 × 1.15)."""
    if gbp is None:
        return 0
    base = float(gbp) * 2100 * 1.05 * 1.15
    return int(round(base / 10_000) * 10_000)


_KO: dict[str, str] = {}
if CACHE_PATH.exists():
    try:
        _KO = json.loads(CACHE_PATH.read_text())
    except Exception:
        _KO = {}


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
    # Already mostly Korean
    if en_ratio(s) < 0.35:
        _KO[s] = s
        return s
    try:
        ko = gtx(s)
        time.sleep(0.05)
    except Exception:
        ko = s
    ko = (
        ko.replace("Chanel", "샤넬")
        .replace("CHANEL", "샤넬")
        .replace("샤 넬", "샤넬")
        .replace("Ready-to-Wear", "레디투웨어")
        .replace("Ready-To-Wear", "레디투웨어")
    )
    _KO[s] = ko
    return ko


def accent_for(key: str) -> str:
    h = hashlib.md5((key or "x").encode()).hexdigest()
    r = 40 + int(h[0:2], 16) % 80
    g = 40 + int(h[2:4], 16) % 80
    b = 40 + int(h[4:6], 16) % 80
    return f"#{r:02x}{g:02x}{b:02x}"


def reorder_locals_garment_first(row: dict) -> list[str]:
    """Put studio STOCKMAN garment shots before lifestyle model photos.

    Existing downloads keep file numbers from the old order; we only reorder
    the path list so PLP / PDP primary image is the garment packshot.
    """
    locals_ = list(row.get("localImages") or [])
    if not locals_ and row.get("localImage"):
        locals_ = [row["localImage"]]
    cdn = list(row.get("images") or [])
    metas = [m for m in (row.get("imageMeta") or []) if isinstance(m, dict)]
    if not locals_:
        return []
    if not cdn or not metas:
        return locals_

    src_to_local: dict[str, str] = {}
    for i, src in enumerate(cdn):
        if i < len(locals_) and src:
            src_to_local[str(src)] = locals_[i]

    def score(m: dict) -> tuple[int, int, int]:
        typ = str(m.get("typology") or "").upper()
        angle = str(m.get("viewAngle") or "").upper()
        preferred = (
            "PACKSHOT_STOCKMAN",
            "PACKSHOT_OTHER",
            "PACKSHOT_ALTERNATIVE",
            "PACKSHOT_DEFAULT",
            "LOOK",
            "EDITORIAL",
        )
        try:
            rank = preferred.index(typ)
        except ValueError:
            rank = 50
        angle_rank = {"FRONT": 0, "BACK": 1, "DETAIL": 2}.get(angle, 5)
        # Stable by original meta order when angle missing (FRONT is usually first STOCKMAN)
        return (rank, angle_rank, 0)

    ordered: list[str] = []
    seen_src: set[str] = set()
    for m in sorted(metas, key=score):
        src = str(m.get("source") or "")
        loc = src_to_local.get(src)
        if loc and src not in seen_src:
            seen_src.add(src)
            ordered.append(loc)
    for loc in locals_:
        if loc not in ordered:
            ordered.append(loc)
    return ordered


def format_size_label(size: str) -> str:
    s = (size or "").strip()
    if not s:
        return "One Size"
    if re.fullmatch(r"\d+(\.\d+)?", s):
        return f"FR {s}"
    return s


def size_slug(size: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (size or "").lower()).strip("-")
    return s or "os"


def load_prev() -> dict[str, dict]:
    out: dict[str, dict] = {}
    if OUT_JSON.exists():
        try:
            for p in json.loads(OUT_JSON.read_text()):
                if p.get("id"):
                    out[p["id"]] = p
        except Exception:
            pass
    return out


def build_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
    code = row.get("productCode") or row.get("sku") or row.get("id")
    if not code:
        return None
    gbp = row.get("gbpPrice")
    if gbp is None:
        return None
    price = gbp_to_krw(float(gbp))
    if price <= 0:
        return None

    leaf = row.get("leaf")
    cols = [
        c
        for c in (row.get("collections") or [])
        if c in {*SHAPE_LEAVES, *PARENT_COLS}
    ]
    cols = sorted(set([*cols, *PARENT_COLS, leaf] if leaf else [*cols, *PARENT_COLS]))
    if leaf and leaf not in SHAPE_LEAVES:
        return None
    primary = leaf if leaf in SHAPE_LEAVES else next(
        (c for c in SHAPE_LEAVES if c in cols), "ch-women-rtw"
    )

    title_en = (row.get("title") or "").strip() or str(code)
    details = row.get("details") or {}
    color_en = (details.get("color") or "").strip()
    fabrics_en = (details.get("fabrics") or "").strip()
    desc_en = (details.get("description") or "").strip()
    ref = (details.get("reference") or "").strip()

    name_ko = t(title_en)
    color_ko = t(color_en) if color_en else ""
    fabrics_ko = t(fabrics_en) if fabrics_en else ""
    desc_ko = t(desc_en) if desc_en else ""

    parts = [desc_ko]
    if color_ko:
        parts.append(f"컬러: {color_ko}")
    if fabrics_ko:
        parts.append(f"소재: {fabrics_ko}")
    if ref:
        parts.append(f"레퍼런스: {ref}")
    description_ko = "\n\n".join(p for p in parts if p)

    images = reorder_locals_garment_first(row)
    # Require at least one real local file
    images = [
        p
        for p in images
        if (ROOT / "public" / p.lstrip("/")).is_file()
        and (ROOT / "public" / p.lstrip("/")).stat().st_size > 2048
    ]
    if not images:
        print(f"skip no local image: {code}", flush=True)
        return None
    image = images[0]
    # Hover: next studio angle if available, else second image
    hover = images[1] if len(images) > 1 else None
    if hover and not (
        (ROOT / "public" / hover.lstrip("/")).is_file()
        and (ROOT / "public" / hover.lstrip("/")).stat().st_size > 2048
    ):
        hover = images[1] if len(images) > 1 else None

    pid = f"ch-{str(code).lower()}"
    registered = (prev or {}).get("registeredAt") or now_iso

    size_rows = row.get("sizes") or []
    variants: list[dict] = []
    any_in = False
    for sz in size_rows:
        size_raw = str(sz.get("orliSize") or sz.get("size") or "").strip()
        if not size_raw:
            continue
        label = format_size_label(size_raw)
        slug = size_slug(size_raw)
        sku = str(sz.get("sku") or sz.get("id") or f"{code}-{slug}")
        # Chanel.com RTW SSR almost always reports OUT_OF_STOCK (boutique /
        # not sold online). Briq fulfils as special order — keep sizes buyable.
        in_stock = True
        any_in = True
        v: dict = {
            "id": f"{pid}-{slug}",
            "name": f"{title_en} — {label}",
            "nameKo": f"{name_ko} — {label}",
            "sku": sku,
            "gbpPrice": float(gbp),
            "price": price,
            "image": image,
            "images": images,
            "sourceUrl": row.get("url") or "",
            "inStock": in_stock,
            "colorKey": color_en.lower() or "default",
            "colorNameKo": color_ko or color_en or "기본",
            "size": label,
            "chCollections": cols,
        }
        if hover:
            v["hoverImage"] = hover
        variants.append(v)

    if not variants:
        in_stock = True
        any_in = True
        variants = [
            {
                "id": f"{pid}-os",
                "name": f"{title_en} — One Size",
                "nameKo": f"{name_ko} — 원 사이즈",
                "sku": code,
                "gbpPrice": float(gbp),
                "price": price,
                "image": image,
                "images": images,
                "sourceUrl": row.get("url") or "",
                "inStock": in_stock,
                "colorKey": color_en.lower() or "default",
                "colorNameKo": color_ko or color_en or "기본",
                "size": "One Size",
                "chCollections": cols,
            }
        ]
        if hover:
            variants[0]["hoverImage"] = hover
    else:
        any_in = any(v["inStock"] for v in variants)

    tags = [
        "chanel",
        "샤넬",
        "rtw",
        "의류",
        "여성",
        "ready-to-wear",
        *cols,
    ]
    badge = "New" if row.get("new") else None

    story = []
    if desc_ko:
        story.append(
            {
                "titleKo": name_ko,
                "bodyKo": desc_ko,
                "image": image,
            }
        )

    prod: dict = {
        "id": pid,
        "name": title_en,
        "nameKo": name_ko,
        "brand": "샤넬",
        "price": price,
        "category": "luxury",
        "subcategory": primary,
        "chCollections": cols,
        "tags": tags,
        "descriptionKo": description_ko,
        "image": image,
        "images": images,
        "accent": accent_for(str(code)),
        "badge": badge,
        "gbpPrice": float(gbp),
        "sku": code,
        "sourceUrl": row.get("url") or "",
        "inStock": any_in,
        "variants": variants,
        "sizeChart": CH_WOMEN_RTW_SIZE_CHART,
        "storySections": story,
        "registeredAt": registered,
        "editTier": "new" if badge == "New" else "signature",
    }
    if hover:
        prod["hoverImage"] = hover
    return prod


def main() -> int:
    if not RAW_PATH.exists():
        raise SystemExit(f"Missing raw catalog: {RAW_PATH}")

    raw = json.loads(RAW_PATH.read_text())
    rows = raw.get("products") or []
    prev_map = load_prev()
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    products: list[dict] = []
    seen: set[str] = set()
    for i, row in enumerate(rows, start=1):
        if row.get("_skip"):
            continue
        pid_guess = f"ch-{str(row.get('sku') or row.get('id') or '').lower()}"
        prod = build_product(row, prev_map.get(pid_guess), now_iso)
        if not prod:
            continue
        if prod["id"] in seen:
            continue
        seen.add(prod["id"])
        products.append(prod)
        if i % 40 == 0:
            CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2))
            print(f"built {i}/{len(rows)}", flush=True)

    products.sort(key=lambda p: p["id"])
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n")
    OUT_TS.write_text(
        'import type { Product } from "@/data/products";\n'
        'import data from "./ch-catalog.json";\n\n'
        "/** Auto-generated — Chanel Ready-to-Wear (women). */\n"
        "export const chCatalogProducts = data as unknown as Product[];\n"
    )
    CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2) + "\n")

    leaf_n = {leaf: 0 for leaf in SHAPE_LEAVES}
    leaf_n["ch-women-looks"] = 0
    in_stock = 0
    oos = 0
    for p in products:
        if p.get("inStock"):
            in_stock += 1
        else:
            oos += 1
        for c in p.get("chCollections") or []:
            if c in leaf_n:
                leaf_n[c] += 1

    print(f"Wrote {len(products)} products → {OUT_JSON}", flush=True)
    print(f"inStock={in_stock} oos={oos}", flush=True)
    print(f"leafCounts={leaf_n}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
