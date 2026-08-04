#!/usr/bin/env python3
"""Build Gucci handbags catalogue from scraped raw.

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
RAW_PATH = ROOT / "src/data/gc/gc-catalog-raw.json"
OUT_JSON = ROOT / "src/data/gc/gc-catalog.json"
OUT_TS = ROOT / "src/data/gc/gc-catalog.ts"
CACHE_PATH = ROOT / "src/data/gc/gc-translate-cache.json"

LEAF_COLLECTIONS = [
    "gc-women-shoulder-bags",
    "gc-women-mini-bags",
    "gc-women-crossbody-bags",
    "gc-women-tote-bags",
    "gc-women-top-handle-bags",
    "gc-women-backpacks-beltbags",
    "gc-women-clutches-evening",
    "gc-women-personalised",
]


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
    """Convert '[구찌 소프트빗] 맥시 숄더백' → '구찌 소프트빗 맥시 숄더백'."""
    s = (name or "").strip()
    m = re.match(r"^\[([^\]]+)\]\s*(.*)$", s)
    if m:
        inner, rest = m.group(1).strip(), m.group(2).strip()
        return f"{inner} {rest}".strip() if rest else inner
    return s


def strip_gucci_warranty(text: str) -> str:
    """Drop KR Gucci A/S warranty + clientservice.kr copy from product text.

    Official KR PDP injects clauses like:
      품질보증기준: A/S 보증기간 2년(...)
      AS 유선접수: 클라이언트서비스 02-3452-1921 / clientservice.kr@gucci.com
    They may sit together or be split by other detail bullets — remove each clause.
    """
    if not text:
        return ""
    s = text.replace("\xa0", " ").replace("\u202f", " ")
    s = re.sub(r"[ \t]+", " ", s)

    # Warranty standards clause (ends at next middle-dot bullet or EOL)
    s = re.sub(
        r"품질보증기준\s*:[^·\n]*",
        "",
        s,
        flags=re.I,
    )
    # Phone / email AS intake clause
    s = re.sub(
        r"AS\s*유선접수\s*:[^·\n]*clientservice\.kr@gucci\.com",
        "",
        s,
        flags=re.I,
    )
    s = re.sub(r"clientservice\.kr@gucci\.com", "", s, flags=re.I)
    # Orphan AS phone line without email
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
        # Skip season codes like PF25 alone
        if re.fullmatch(r"[A-Z]{1,3}\d{2}", line):
            continue
        # Drop KR Gucci warranty / client-service footers
        if is_gucci_warranty_line(line):
            cleaned = strip_gucci_warranty(line)
            if cleaned:
                out.append(cleaned)
            continue
        # Drop long medical warning footers
        if "전자의료" in line or "electromedical" in line.lower() or "WARNING:" in line:
            # keep the closure part before warning if present
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


def build_product(row: dict, prev: dict | None, now_iso: str) -> dict | None:
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
        if c in LEAF_COLLECTIONS or c == "gc-handbags"
    ]
    # Always include parent handbag hub when in any leaf
    if any(c in LEAF_COLLECTIONS for c in cols) and "gc-handbags" not in cols:
        cols.append("gc-handbags")
    cols = sorted(set(cols))
    if not cols:
        cols = ["gc-handbags"]

    leaf = next((c for c in LEAF_COLLECTIONS if c in cols), "gc-handbags")

    ko = row.get("translationKo") or {}
    en = row.get("translationEn") or {}

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
        # Fallback to remote URLs (dev only) — still set path pattern
        remotes = row.get("images") or ([] if not row.get("image") else [row["image"]])
        images = remotes[:1]

    image = images[0]
    # Official Gucci PLP hover is the on-model / lookbook frame (type 100),
    # not PDP gallery[1] (usually a side packshot _002).
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
            {
                "titleKo": name_ko,
                "bodyKo": editorial_ko,
                "image": image,
            }
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

    color_key = slugify(color_en or color_ko or "default")
    pid = f"gc-{slugify(title_en)}-{slugify(code)[-12:]}"
    # Stable id from product code
    pid = f"gc-{code.lower()}"

    registered = (prev or {}).get("registeredAt") or now_iso

    variant = {
        "id": f"{pid}-u",
        "name": f"{title_en} — {color_en or 'One Size'}".strip(" —"),
        "nameKo": f"{name_ko} — {color_ko or '원 사이즈'}".strip(" —"),
        "sku": code,
        "gbpPrice": float(gbp),
        "price": price,
        "image": image,
        "images": images,
        "hoverImage": hover,
        "sourceUrl": row.get("url") or "",
        "inStock": bool(row.get("inStock", True)),
        "colorKey": color_key,
        "colorNameKo": color_ko or color_en or "기본",
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
        "name": title_en,
        "nameKo": name_ko,
        "brand": "구찌",
        "price": price,
        "category": "bags",
        "subcategory": leaf,
        "gcCollections": cols,
        "tags": tags,
        "descriptionKo": description_ko,
        "image": image,
        "images": images,
        "hoverImage": hover,
        "accent": accent_for(code),
        "badge": badge,
        "gbpPrice": float(gbp),
        "sku": code,
        "sourceUrl": row.get("url") or "",
        "inStock": bool(row.get("inStock", True)),
        "variants": [variant],
        "storySections": story,
        "registeredAt": registered,
        "editTier": "new" if badge == "New" else "signature",
    }


def main() -> None:
    if not RAW_PATH.exists():
        raise SystemExit(f"Missing {RAW_PATH} — run scrape-gc-handbags.py first")

    raw = json.loads(RAW_PATH.read_text())
    rows = raw.get("products") or []

    prev_by_sku: dict[str, dict] = {}
    if OUT_JSON.exists():
        for p in json.loads(OUT_JSON.read_text()):
            if p.get("sku"):
                prev_by_sku[str(p["sku"])] = p

    now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    products: list[dict] = []
    for i, row in enumerate(rows, start=1):
        sku = str(row.get("productCode") or row.get("id") or "")
        prod = build_product(row, prev_by_sku.get(sku), now_iso)
        if prod:
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
        "/** Auto-generated — Gucci women's handbags. */\n"
        "export const gcCatalogProducts = data as unknown as Product[];\n"
    )
    CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2))
    print(f"Wrote {len(products)} products → {OUT_JSON}", flush=True)
    for leaf in LEAF_COLLECTIONS:
        n = sum(1 for p in products if leaf in (p.get("gcCollections") or []))
        print(f"  {leaf}: {n}", flush=True)


if __name__ == "__main__":
    main()
