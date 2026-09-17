#!/usr/bin/env python3
"""Build Briq AllSaints catalog from scraped raw JSON."""
from __future__ import annotations

import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from curl_cffi import requests as crequests  # noqa: E402

from al_common import load_json, save_json, slugify, clean_html_text  # noqa: E402
from al_config import RAW_DIR, AL_FAMILY_ORDER, AL_FAMILY_SCRAPERS  # noqa: E402
from di_common import gbp_to_krw  # noqa: E402
from ko_qa import en_ratio, is_good_korean  # noqa: E402

OUT_JSON = ROOT / "src/data/al/al-catalog.json"
OUT_TS = ROOT / "src/data/al/al-catalog.ts"
CACHE = ROOT / "src/data/al/al-translate-cache.json"

_BING = {"ig": "", "token": "", "key": "", "fetched_at": 0.0}
_HTTP = crequests.Session()

TITLE_MAP = {
    "allsaints": "올세인츠",
    "all saints": "올세인츠",
    "leather": "레더",
    "jacket": "재킷",
    "hoodie": "후디",
    "sweatshirt": "스웨트셔츠",
    "t-shirt": "티셔츠",
    "shirt": "셔츠",
    "jeans": "진",
    "trousers": "트라우저",
    "boots": "부츠",
    "trainers": "스니커즈",
    "sneakers": "스니커즈",
    "belt": "벨트",
    "wallet": "지갑",
    "scarf": "스카프",
    "sunglasses": "선글라스",
}


def family_category(family: str) -> str:
    return AL_FAMILY_SCRAPERS[family]["category"]


def _bing_token() -> tuple[str, str, str]:
    now = time.time()
    if _BING["token"] and now - float(_BING["fetched_at"] or 0) < 500:
        return _BING["ig"], _BING["token"], _BING["key"]
    r = _HTTP.get("https://www.bing.com/translator", impersonate="chrome131", timeout=40)
    ig = re.search(r'IG:"([^"]+)"', r.text)
    tok = re.search(r'params_AbusePreventionHelper\s*=\s*\[(\d+),"([^"]+)",(\d+)\]', r.text)
    if not (ig and tok):
        raise RuntimeError("bing token failed")
    _BING["ig"] = ig.group(1)
    _BING["key"] = tok.group(1)
    _BING["token"] = tok.group(2)
    _BING["fetched_at"] = now
    return _BING["ig"], _BING["token"], _BING["key"]


def translate(text: str, cache: dict[str, str]) -> str:
    s = (text or "").strip()
    if not s:
        return ""
    if is_good_korean(s, max_ratio=0.35) and en_ratio(s) < 0.35:
        return s
    if s in cache and is_good_korean(cache[s], max_ratio=0.4):
        return cache[s]
    # Fast build: skip live Bing — retranslate-al-ko fills KO after.
    if os.environ.get("BRIQ_FAST_BUILD") == "1":
        return s
    low = s.lower()
    for en, ko in TITLE_MAP.items():
        if low == en:
            cache[s] = ko
            return ko
    try:
        ig, token, key = _bing_token()
        r = _HTTP.post(
            "https://www.bing.com/ttranslatev3",
            params={"isVertical": "1", "IG": ig, "IID": "translator.5024"},
            data={
                "fromLang": "en",
                "to": "ko",
                "text": s[:4500],
                "token": token,
                "key": key,
            },
            impersonate="chrome131",
            timeout=40,
        )
        data = r.json()
        out = (
            ((data[0] or {}).get("translations") or [{}])[0].get("text")
            if isinstance(data, list)
            else ""
        )
        out = (out or "").strip()
        if out and is_good_korean(out, max_ratio=0.45):
            cache[s] = out
            return out
    except Exception:
        pass
    return cache.get(s) or s


def color_ko(name: str, cache: dict[str, str]) -> str:
    n = (name or "").strip()
    if not n:
        return "기본"
    return translate(n, cache)


def size_chart_from_raw(raw: dict, *, category: str, mens: bool) -> dict | None:
    guide = raw.get("sizeGuide")
    if not isinstance(guide, dict):
        return None
    headers = guide.get("headers") or []
    rows = guide.get("rows") or []
    if len(headers) < 2 or len(rows) < 1:
        return None
    kind = "슈즈" if category == "shoes" else "의류"
    gender = "남성" if mens else "여성"
    note = clean_html_text(raw.get("modelCopy") or "")
    note_ko = note
    return {
        "id": str(raw.get("sizeChartId") or f"al-{category}"),
        "titleKo": f"올세인츠 {gender} {kind} 사이즈 가이드",
        "noteKo": note_ko
        or "공홈 사이즈 가이드 기준입니다. 스타일·소재에 따라 핏이 달라질 수 있습니다.",
        "headers": headers,
        "rows": rows,
    }


def build_story(
    desc_ko: str,
    bullets_ko: list[str],
    care_ko: list[str],
    tips_ko: str,
    images: list[str],
) -> list[dict]:
    sections = []
    if desc_ko:
        sections.append({"titleKo": "제품 소개", "bodyKo": desc_ko, "image": images[0] if images else ""})
    if bullets_ko:
        sections.append(
            {
                "titleKo": "디테일 & 특징",
                "bodyKo": "\n".join(f"· {b}" for b in bullets_ko[:12]),
                "image": images[1] if len(images) > 1 else (images[0] if images else ""),
            }
        )
    if care_ko:
        sections.append(
            {
                "titleKo": "케어 가이드",
                "bodyKo": "\n".join(care_ko[:8]),
                "image": images[2] if len(images) > 2 else "",
            }
        )
    if tips_ko:
        sections.append({"titleKo": "스타일링 팁", "bodyKo": tips_ko, "image": ""})
    return sections


def build_product(raw: dict, family: str, cache: dict[str, str]) -> dict | None:
    pid = str(raw.get("id") or "")
    if not pid:
        return None
    images = list(raw.get("localImages") or [])
    if not images:
        return None
    sizes = raw.get("sizes") or []
    # Prefer size-level GBP when present.
    gbps = [float(s["gbpPrice"]) for s in sizes if s.get("gbpPrice")]
    gbp = float(raw.get("gbpPrice") or (min(gbps) if gbps else 0) or 0)
    if gbp <= 0:
        return None
    price = gbp_to_krw(gbp)
    name = str(raw.get("name") or pid)
    name_ko = translate(name, cache)
    bullets_en = list(raw.get("shortDescription") or [])
    care_en = list(raw.get("longDescription") or [])
    desc_en = str(raw.get("description") or "")
    if not desc_en and bullets_en:
        desc_en = bullets_en[0]
        bullets_en = bullets_en[1:]
    desc_ko = translate(desc_en, cache) if desc_en else name_ko
    bullets_ko = [translate(b, cache) for b in bullets_en if b][:10]
    care_ko = [translate(c, cache) for c in care_en if c][:8]
    tips_ko = translate(str(raw.get("stylistsTips") or ""), cache)
    color_name = color_ko(str(raw.get("color") or ""), cache)
    color_key = slugify(str(raw.get("color") or "default"))

    cat = family_category(family)
    mens = "men" in family
    variants = []
    usable = [s for s in sizes if str(s.get("value") or "").upper() not in {"", "U", "TU"}]
    if usable and any(str(s.get("value") or "").upper() not in {"OS", "U", "TU"} for s in usable):
        for s in usable:
            val = str(s.get("value") or "")
            disp = str(s.get("displayValue") or val)
            sgbp = float(s.get("gbpPrice") or gbp)
            sprice = gbp_to_krw(sgbp)
            list_gbp = s.get("listGbpPrice")
            compare = gbp_to_krw(float(list_gbp)) if list_gbp else None
            variants.append(
                {
                    "id": f"al-{slugify(pid)}-{slugify(val)}",
                    "name": disp,
                    "nameKo": disp,
                    "size": disp,
                    "sku": str(s.get("id") or pid),
                    "gbpPrice": sgbp,
                    "price": sprice,
                    "compareAtPrice": compare if compare and compare > sprice else None,
                    "image": images[0],
                    "images": images,
                    "sourceUrl": raw.get("link") or raw.get("url") or "",
                    "inStock": bool(s.get("inStock", True)),
                    "colorKey": color_key,
                    "colorNameKo": color_name,
                    "alCollections": list(raw.get("collections") or []),
                }
            )
    else:
        variants.append(
            {
                "id": f"al-{slugify(pid)}",
                "name": color_name,
                "nameKo": color_name,
                "sku": pid,
                "gbpPrice": gbp,
                "price": price,
                "image": images[0],
                "images": images,
                "sourceUrl": raw.get("link") or raw.get("url") or "",
                "inStock": bool(raw.get("inStock", True)),
                "colorKey": color_key,
                "colorNameKo": color_name,
                "alCollections": list(raw.get("collections") or []),
            }
        )

    chart = size_chart_from_raw(raw, category=cat, mens=mens)
    # Translate chart note if English
    if chart and chart.get("noteKo") and not is_good_korean(chart["noteKo"], max_ratio=0.4):
        chart["noteKo"] = translate(chart["noteKo"], cache)

    features = [x for x in [*bullets_ko[:6], *care_ko[:2]] if x]
    tech = []
    if care_ko:
        tech.append({"labelKo": "소재 / 케어", "valueKo": " · ".join(care_ko[:4])})
    if raw.get("originCountry"):
        tech.append({"labelKo": "제조국", "valueKo": translate(str(raw["originCountry"]), cache)})
    tech.append({"labelKo": "제품 코드", "valueKo": pid})

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return {
        "id": f"al-{slugify(pid)}",
        "brand": "올세인츠",
        "name": name,
        "nameKo": name_ko,
        "category": cat,
        "subcategory": (raw.get("collections") or [None])[-1],
        "alCollections": list(raw.get("collections") or []),
        "tags": ["올세인츠", "AllSaints", "All Saints"],
        "descriptionKo": desc_ko or name_ko,
        "image": images[0],
        "images": images,
        "hoverImage": images[1] if len(images) > 1 else images[0],
        "price": min(v["price"] for v in variants),
        "gbpPrice": min(float(v["gbpPrice"]) for v in variants),
        "inStock": any(v.get("inStock") for v in variants),
        "sourceUrl": raw.get("link") or raw.get("url") or "",
        "featuresKo": features,
        "storySections": build_story(desc_ko or name_ko, bullets_ko, care_ko, tips_ko, images),
        "techSpecs": tech,
        "sizeChart": chart,
        "variants": variants,
        "accentColor": "#111111",
        "registeredAt": now,
        "updatedAt": now,
    }


def main() -> int:
    cache = load_json(CACHE, {})
    products: list[dict] = []
    seen: set[str] = set()
    for family in AL_FAMILY_ORDER:
        cfg = AL_FAMILY_SCRAPERS[family]
        raw_path = RAW_DIR / cfg["out"]
        data = load_json(raw_path, {})
        rows = data.get("products") or []
        print(f"build {family}: raw={len(rows)}", flush=True)
        for i, row in enumerate(rows, start=1):
            p = build_product(row, family, cache)
            if not p:
                continue
            if p["id"] in seen:
                for existing in products:
                    if existing["id"] == p["id"]:
                        cols = list(
                            dict.fromkeys(
                                [
                                    *(existing.get("alCollections") or []),
                                    *(p.get("alCollections") or []),
                                ]
                            )
                        )
                        existing["alCollections"] = cols
                        existing["subcategory"] = cols[-1] if cols else existing.get("subcategory")
                        for v in existing.get("variants") or []:
                            v["alCollections"] = cols
                        # Prefer chart / richer story if missing
                        if not existing.get("sizeChart") and p.get("sizeChart"):
                            existing["sizeChart"] = p["sizeChart"]
                        break
                continue
            seen.add(p["id"])
            products.append(p)
            if i % 10 == 0 or i == len(rows):
                save_json(CACHE, cache)
                print(f"  {family} {i}/{len(rows)} products={len(products)}", flush=True)
        save_json(CACHE, cache)

    save_json(OUT_JSON, products)
    OUT_TS.write_text(
        "/* Auto-generated by scripts/build-al-catalog.py — do not edit */\n"
        'import type { Product } from "@/data/product-types";\n'
        'import data from "./al-catalog.json";\n\n'
        "/** AllSaints catalog (JSON import). */\n"
        "export const alCatalogProducts = data as unknown as Product[];\n",
        encoding="utf-8",
    )
    print(f"OK wrote {OUT_JSON} products={len(products)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
