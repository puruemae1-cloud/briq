#!/usr/bin/env python3
"""Build Briq Dior Maison tableware catalog from scrape raw.

  python3 scripts/build-di-catalog.py
  python3 scripts/check-catalog-korean.py --brand di --fail
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from di_common import gbp_to_krw, slugify  # noqa: E402
from ko_qa import gtx_translate, is_good_korean  # noqa: E402

RAW = ROOT / "src/data/di/di-tableware-catalog-raw.json"
CACHE = ROOT / "src/data/di/di-translate-cache.json"
OUT_JSON = ROOT / "src/data/di/di-catalog.json"
OUT_TS = ROOT / "src/data/di/di-catalog.ts"

ACCENTS = ["#1A1A1A", "#2C2420", "#243028", "#3A2F28", "#1E2830", "#2A2028"]

# Light phrase polish for tableware
PHRASES = [
    (r"\bLimoges porcelain\b", "리모주 포슬린"),
    (r"\bporcelain\b", "포슬린"),
    (r"\bcrystal\b", "크리스탈"),
    (r"\bcutlery\b", "커트러리"),
    (r"\bDior Maison\b", "디올 메종"),
    (r"\bGodron\b", "고드론"),
]


def load_cache() -> dict[str, str]:
    if CACHE.is_file():
        return json.loads(CACHE.read_text())
    return {}


def save_cache(cache: dict[str, str]) -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False) + "\n")


def apply_phrases(text: str) -> str:
    out = text
    for pat, rep in PHRASES:
        out = re.sub(pat, rep, out, flags=re.I)
    return out


def t(text: str | None, cache: dict[str, str]) -> str:
    if not text:
        return ""
    s = re.sub(r"<[^>]+>", " ", str(text))
    s = re.sub(r"\s+", " ", s).strip()
    if not s:
        return ""
    if s in cache and is_good_korean(cache[s]):
        return cache[s]
    if is_good_korean(s):
        cache[s] = apply_phrases(s)
        return cache[s]
    last_err: Exception | None = None
    for attempt in range(4):
        try:
            ko = gtx_translate(s)
            ko = apply_phrases(ko)
            if is_good_korean(ko):
                cache[s] = ko
                time.sleep(0.35)
                return ko
            last_err = RuntimeError(f"still English: {ko[:60]}")
        except Exception as e:
            last_err = e
            time.sleep(1.2 * (attempt + 1))
    # Do not poison cache with English failures
    print(f"  WARN translate fail: {s[:60]}… ({last_err})")
    return apply_phrases(s)


def clean_en_desc(text: str) -> str:
    s = re.sub(r"<[^>]+>", " ", str(text or ""))
    for cut in (
        "See more Gifts",
        "We use cookies",
        "Cookie Settings",
        "Delivery estimated",
        "You may also like",
    ):
        if cut in s:
            s = s.split(cut)[0]
    return re.sub(r"\s+", " ", s).strip()


def build_product(row: dict, cache: dict[str, str], idx: int) -> dict:
    details = row.get("details") or {}
    paras = [clean_en_desc(p) for p in (details.get("paragraphs") or [])]
    paras = [p for p in paras if p and p not in ("Size & Fit", "Description")]
    bullets = [clean_en_desc(b) for b in (details.get("bullets") or [])]

    title_en = (row.get("title") or row.get("id") or "").strip()
    subtitle = clean_en_desc(row.get("subtitle") or "")
    title_ko = t(title_en, cache)
    subtitle_ko = t(subtitle, cache) if subtitle else ""

    desc_parts = [t(p, cache) for p in paras if p]
    # Subtitle as lead only when not already covered by the long description.
    if subtitle_ko and not any(subtitle_ko in p for p in desc_parts):
        desc_parts.insert(0, subtitle_ko)
    for b in bullets:
        bk = t(b, cache)
        if bk and bk not in desc_parts and bk != subtitle_ko:
            desc_parts.append(f"• {bk}")

    desc_ko = "\n\n".join(p for p in desc_parts if p).strip()
    images = [img for img in (row.get("images") or []) if img]
    image = images[0] if images else "/products/di-pdp/placeholder.jpg"
    sku = str(row.get("id") or slugify(title_en))
    pid = f"di-{slugify(sku)}"
    gbp = row.get("gbpPrice")
    try:
        gbp_f = float(gbp) if gbp is not None else 0.0
    except (TypeError, ValueError):
        gbp_f = 0.0
    price = gbp_to_krw(gbp_f) if gbp_f else 0

    leaf = row.get("leafId") or "di-plates-bowls"
    collections = list(dict.fromkeys(row.get("collections") or []))
    if leaf not in collections:
        collections.append(leaf)

    color = row.get("color") or {}
    color_label = color.get("label") or color.get("label_int") or ""
    color_ko = t(color_label, cache) if color_label else "기본"

    variant = {
        "id": f"{pid}-os",
        "name": "One Size",
        "nameKo": "원 사이즈",
        "sku": str(row.get("sku") or sku),
        "gbpPrice": gbp_f,
        "price": price,
        "image": image,
        "images": images or [image],
        "sourceUrl": row.get("url") or "",
        "inStock": True,
        "colorKey": color.get("code") or "default",
        "colorNameKo": color_ko,
        "size": "OS",
        "diCollections": collections,
    }

    return {
        "id": pid,
        "name": title_en,
        "nameKo": title_ko,
        "brand": "Dior",
        "category": "accessories",
        "subcategory": leaf,
        "diCollections": collections,
        "tags": ["dior", "디올", "tableware", "테이블웨어", "maison"],
        "descriptionKo": desc_ko,
        "image": image,
        "images": images or [image],
        "accent": ACCENTS[idx % len(ACCENTS)],
        "gbpPrice": gbp_f,
        "sku": sku,
        "sourceUrl": row.get("url") or "",
        "variants": [variant],
        "storySections": [
            {
                "titleKo": "제품 소개",
                "bodyKo": desc_ko or subtitle_ko or title_ko,
                "image": image,
            }
        ],
    }


def main() -> None:
    if not RAW.is_file():
        raise SystemExit(f"missing raw catalog: {RAW}")
    raw = json.loads(RAW.read_text())
    products_in = raw.get("products") or []
    cache = load_cache()
    out: list[dict] = []
    for i, row in enumerate(products_in):
        if not row.get("images"):
            print(f"skip no images {row.get('id')}")
            continue
        out.append(build_product(row, cache, i))
        if (i + 1) % 20 == 0:
            save_cache(cache)
            print(f"built {i+1}/{len(products_in)}")
    save_cache(cache)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    OUT_TS.write_text(
        "/* Auto-generated by scripts/build-di-catalog.py — do not edit */\n"
        'import type { Product } from "@/data/product-types";\n'
        f"export const diCatalogProducts = {json.dumps(out, ensure_ascii=False)} as Product[];\n"
        f"export const diCatalogGeneratedAt = {json.dumps(datetime.now(timezone.utc).isoformat())};\n"
    )
    print(f"wrote {len(out)} products → {OUT_JSON}")


if __name__ == "__main__":
    main()
