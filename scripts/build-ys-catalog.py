#!/usr/bin/env python3
"""Build Briq Saint Laurent catalog from scraped raw JSON."""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from curl_cffi import requests as crequests  # noqa: E402

from di_common import gbp_to_krw  # noqa: E402
from ko_qa import en_ratio, is_good_korean  # noqa: E402
from ysl_common import load_json, save_json, slugify  # noqa: E402
from ysl_config import RAW_DIR, YS_FAMILY_ORDER, YS_FAMILY_SCRAPERS  # noqa: E402
from ys_size_charts import parse_ys_size_token, size_chart_for_rtw  # noqa: E402

OUT_JSON = ROOT / "src/data/ys/ys-catalog.json"
OUT_TS = ROOT / "src/data/ys/ys-catalog.ts"
CACHE = ROOT / "src/data/ys/ys-translate-cache.json"

_BING = {"ig": "", "token": "", "key": "", "fetched_at": 0.0}
_HTTP = crequests.Session()

TITLE_MAP = {
    "saint laurent": "생로랑",
    "ysl": "YSL",
    "cassandre": "카산드라",
    "le 5 a 7": "르 5 a 7",
    "niki": "니키",
    "loulou": "룰루",
    "sunset": "선셋",
    "jamie": "제이미",
    "kate": "케이트",
    "tote bag": "토트백",
    "tote": "토트",
    "backpack": "백팩",
    "messenger": "메신저",
    "briefcase": "브리프케이스",
    "wallet": "월렛",
    "card case": "카드 케이스",
    "credit card": "신용카드",
    "belt": "벨트",
    "sneakers": "스니커즈",
    "boots": "부츠",
    "loafers": "로퍼",
    "sandals": "샌들",
    "leather": "레더",
    "patent leather": "페이턴트 레더",
    "grained leather": "그레인 레더",
    "calfskin": "카프스킨",
    "cotton": "코튼",
    "wool": "울",
    "silk": "실크",
    "black": "블랙",
    "white": "화이트",
    "ivory": "아이보리",
    "beige": "베이지",
    "brown": "브라운",
    "navy": "네이비",
    "red": "레드",
    "gold": "골드",
    "silver": "실버",
}


def _refresh_bing() -> None:
    r = _HTTP.get(
        "https://www.bing.com/translator",
        impersonate="chrome131",
        timeout=12,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    html = r.text
    ig = re.search(r'IG:"([^"]+)"', html)
    tok = re.search(
        r'params_AbusePreventionHelper\s*=\s*\[(\d+),"([^"]+)",(\d+)\]', html
    )
    if not ig or not tok:
        raise RuntimeError("bing-token-missing")
    _BING["ig"] = ig.group(1)
    _BING["key"] = tok.group(1)
    _BING["token"] = tok.group(2)
    _BING["fetched_at"] = time.time()


def _bing(text: str) -> str:
    if time.time() - float(_BING["fetched_at"] or 0) > 200 or not _BING["token"]:
        _refresh_bing()
    r = _HTTP.post(
        f"https://www.bing.com/ttranslatev3?isVertical=1&&IG={_BING['ig']}&IID=translator.5023",
        data={
            "fromLang": "en",
            "to": "ko",
            "text": text[:900],
            "token": _BING["token"],
            "key": _BING["key"],
        },
        impersonate="chrome131",
        timeout=12,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.bing.com/translator",
        },
    )
    if r.status_code == 401:
        _BING["fetched_at"] = 0
        raise RuntimeError("bing-401")
    r.raise_for_status()
    data = r.json()
    return data[0]["translations"][0]["text"]


def _gtx_once(text: str) -> str:
    r = _HTTP.get(
        "https://translate.googleapis.com/translate_a/single",
        params={"client": "gtx", "sl": "en", "tl": "ko", "dt": "t", "q": text[:4500]},
        impersonate="chrome131",
        timeout=10,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    r.raise_for_status()
    data = r.json()
    return "".join(part[0] for part in data[0] if part and part[0])


def mt_translate(text: str) -> str:
    last: Exception | None = None
    for fn in (_bing, _gtx_once):
        for attempt in range(2):
            try:
                out = fn(text)
                if out and en_ratio(out) < 0.55:
                    time.sleep(0.15)
                    return out
            except Exception as e:
                last = e
                if fn is _bing:
                    _BING["fetched_at"] = 0
                time.sleep(0.5 * (attempt + 1))
    if last:
        raise last
    return ""


def translate(text: str, cache: dict[str, str]) -> str:
    s = re.sub(r"\s+", " ", (text or "").strip())
    if not s:
        return ""
    if s in cache and is_good_korean(cache[s], max_ratio=0.50):
        return cache[s]
    if is_good_korean(s, max_ratio=0.35):
        cache[s] = s
        return s
    low = s.lower()
    out = s
    for en, ko in sorted(TITLE_MAP.items(), key=lambda kv: -len(kv[0])):
        if en in low:
            out = re.sub(re.escape(en), ko, out, flags=re.I)
    if out != s and is_good_korean(out, max_ratio=0.55):
        cache[s] = out
        return out
    try:
        ko = mt_translate(s)
    except Exception:
        ko = out if out != s else s
    if ko and is_good_korean(ko, max_ratio=0.55):
        cache[s] = ko
        return ko
    cache[s] = out if out != s else s
    return cache[s]


def color_ko(name: str | None, cache: dict[str, str]) -> str:
    s = (name or "").strip()
    if not s:
        return "원 사이즈"
    return translate(s.title() if s.isupper() else s, cache)





def parse_size_display(display: str) -> tuple[str, str]:
    """'YSL F34 / GB 6' or 'YSL 41 / GB 16' -> (ysl, gb)."""
    return parse_ys_size_token(display)


def build_shoes_size_chart(sizes: list[dict], *, mens: bool) -> dict | None:
    rows = []
    for s in sizes or []:
        ysl, gb = parse_size_display(str(s.get("displayValue") or s.get("value") or ""))
        if not ysl:
            continue
        rows.append([ysl, gb or "—", "—"])
    if len(rows) < 2:
        return None
    # dedupe
    seen = set()
    uniq = []
    for r in rows:
        if r[0] in seen:
            continue
        seen.add(r[0])
        uniq.append(r)
    return {
        "id": "ys-shoes-men" if mens else "ys-shoes-women",
        "titleKo": "생로랑 슈즈 사이즈 가이드",
        "noteKo": "공홈 표기(YSL / GB) 기준입니다. 발볼·디자인에 따라 핏이 달라질 수 있습니다.",
        "headers": ["YSL (EU)", "GB", "참고"],
        "rows": uniq,
    }


def build_rtw_size_chart(
    sizes: list[dict],
    *,
    mens: bool,
    leaf_hint: str = "",
) -> dict | None:
    return size_chart_for_rtw(sizes, mens=mens, leaf_hint=leaf_hint)


def build_story(desc_ko: str, bullets_ko: list[str], care_ko: str, images: list[str]) -> list[dict]:
    sections = []
    if desc_ko:
        sections.append(
            {
                "titleKo": "제품 소개",
                "bodyKo": desc_ko,
                "image": images[0] if images else "",
            }
        )
    if bullets_ko:
        sections.append(
            {
                "titleKo": "디테일 & 특징",
                "bodyKo": " · ".join(bullets_ko[:10]),
                "image": images[1] if len(images) > 1 else (images[0] if images else ""),
            }
        )
    if care_ko:
        sections.append(
            {
                "titleKo": "케어 가이드",
                "bodyKo": care_ko,
                "image": images[2] if len(images) > 2 else (images[0] if images else ""),
            }
        )
    return sections


def family_category(family: str) -> str:
    return YS_FAMILY_SCRAPERS[family]["category"]


def build_product(raw: dict, family: str, cache: dict[str, str]) -> dict | None:
    pid = str(raw.get("id") or "")
    if not pid:
        return None
    images = list(raw.get("localImages") or [])
    if not images:
        return None
    gbp = float(raw.get("gbpPrice") or 0)
    if gbp <= 0:
        return None
    price = gbp_to_krw(gbp)
    name = str(raw.get("name") or pid)
    name_ko = translate(name, cache)
    desc = str(raw.get("description") or "")
    desc_ko = translate(desc, cache) if desc else ""
    bullets = []
    for b in raw.get("shortDescription") or []:
        t = re.sub(r"<[^>]+>", "", str(b)).strip()
        # Skip marketing tracking links / empty.
        if not t or t.startswith("http") or "marketing?cid=" in t:
            continue
        # Keep dimensions / material bullets richer via MT; cap length.
        if len(t) > 220:
            t = t[:220].rsplit(" ", 1)[0]
        bullets.append(translate(t, cache))
    # Long official care blocks are repetitive — use a natural Korean care note.
    if raw.get("productCare"):
        care_ko = (
            "물·오일·향수·화장품 등 액체성 물질과의 접촉을 피하고, "
            "거친 표면과의 마찰을 줄여 주세요. 보관 시 직사광선과 고온·다습한 환경을 피하고, "
            "전용 더스트백에 넣어 형태를 유지해 주세요."
        )
    else:
        care_ko = ""
    comps = str(raw.get("compositions") or "")
    comps_ko = translate(comps, cache) if comps else ""
    color_name = color_ko(str(raw.get("color") or ""), cache)
    color_key = slugify(str(raw.get("colorCode") or raw.get("color") or "default"))

    sizes = raw.get("sizes") or []
    # Stable small→large for letter + F/GB numeric labels (matches PDP chip order).
    _letter = {"XXXS": 0, "XXS": 1, "XS": 2, "S": 3, "M": 4, "L": 5, "XL": 6, "XXL": 7, "XXXL": 8}

    def _size_key(s: dict) -> tuple:
        disp = str(s.get("displayValue") or s.get("value") or "")
        m = re.search(r"\b(XXXS|XXS|XS|S|M|L|XL|XXL|XXXL)\b", disp, re.I)
        if m:
            return (0, _letter.get(m.group(1).upper(), 99), disp)
        fm = re.search(r"\bF(\d{2})\b", disp, re.I)
        if fm:
            return (1, int(fm.group(1)), disp)
        return (2, 0, disp)

    sizes = sorted(list(sizes), key=_size_key)
    usable_sizes = [
        s
        for s in sizes
        if str(s.get("value") or "").upper() not in {"", "U", "TU", "OS"}
        or (s.get("displayValue") and "U" not in str(s.get("displayValue")))
    ]
    # unique-size accessories often only have U
    variants = []
    if usable_sizes and any(str(s.get("value") or "").upper() not in {"U", "TU", "OS"} for s in sizes):
        for s in sizes:
            val = str(s.get("value") or "").replace("_", ".")
            disp = str(s.get("displayValue") or val)
            if val.upper() in {"U", "TU", "OS"} and len(sizes) == 1:
                label = "OS"
                size_label = "OS"
            else:
                # Chip label: primary size only (XS, F36, 48) — drop " / GB …".
                primary = re.sub(r"^YSL\s+", "", disp, flags=re.I).strip() or val
                if " /" in primary:
                    primary = primary.split(" /", 1)[0].strip()
                label = primary or val
                size_label = label
            vid = f"ys-{pid}-{slugify(val)}"
            variants.append(
                {
                    "id": vid,
                    "name": label,
                    "nameKo": label,
                    "size": size_label,
                    "sku": str(s.get("id") or pid),
                    "gbpPrice": gbp,
                    "price": price,
                    "image": images[0],
                    "images": images,
                    "sourceUrl": raw.get("url") or "",
                    "inStock": bool(s.get("inStock", True)),
                    "colorKey": color_key,
                    "colorNameKo": color_name,
                    "ysCollections": list(raw.get("collections") or []),
                }
            )
    else:
        variants.append(
            {
                "id": f"ys-{pid}",
                "name": color_name,
                "nameKo": color_name,
                "sku": pid,
                "gbpPrice": gbp,
                "price": price,
                "image": images[0],
                "images": images,
                "sourceUrl": raw.get("url") or "",
                "inStock": bool(raw.get("inStock", True)),
                "colorKey": color_key,
                "colorNameKo": color_name,
                "ysCollections": list(raw.get("collections") or []),
            }
        )

    cat = family_category(family)
    mens = "men" in family
    leaf_hint = str(raw.get("leafId") or "")
    cols = [str(c) for c in (raw.get("collections") or [])]
    if not leaf_hint:
        for c in reversed(cols):
            if c.startswith("ys-") and c not in {"ys-men", "ys-women", "saint-laurent"}:
                leaf_hint = c
                break
    size_chart = None
    if cat == "shoes":
        size_chart = build_shoes_size_chart(sizes, mens=mens)
    elif cat == "luxury":
        size_chart = build_rtw_size_chart(sizes, mens=mens, leaf_hint=leaf_hint)

    features = [x for x in [comps_ko, *(bullets[:6])] if x]
    tech = []
    if comps_ko:
        tech.append({"labelKo": "소재", "valueKo": comps_ko})
    if raw.get("madeIn"):
        tech.append({"labelKo": "제조국", "valueKo": translate(str(raw["madeIn"]).title(), cache)})
    tech.append({"labelKo": "제품 코드", "valueKo": pid})

    return {
        "id": f"ys-{pid.lower()}",
        "brand": "생로랑",
        "name": name,
        "nameKo": name_ko,
        "category": cat,
        "subcategory": (raw.get("collections") or [None])[-1],
        "ysCollections": list(raw.get("collections") or []),
        "tags": ["생로랑", "Saint Laurent", "YSL", "입생로랑"],
        "descriptionKo": desc_ko or name_ko,
        "image": images[0],
        "images": images,
        "hoverImage": images[1] if len(images) > 1 else images[0],
        "price": price,
        "gbpPrice": gbp,
        "inStock": any(v.get("inStock") for v in variants),
        "sourceUrl": raw.get("url") or "",
        "featuresKo": features,
        "storySections": build_story(desc_ko or name_ko, bullets, care_ko, images),
        "techSpecs": tech,
        "sizeChart": size_chart,
        "variants": variants,
        "accentColor": "#111111",
    }


def main() -> int:
    cache = load_json(CACHE, {})
    products: list[dict] = []
    seen: set[str] = set()
    for family in YS_FAMILY_ORDER:
        cfg = YS_FAMILY_SCRAPERS[family]
        raw_path = RAW_DIR / cfg["out"]
        data = load_json(raw_path, {})
        rows = data.get("products") or []
        print(f"build {family}: raw={len(rows)}", flush=True)
        for i, row in enumerate(rows, start=1):
            p = build_product(row, family, cache)
            if not p:
                continue
            if p["id"] in seen:
                # merge collections
                for existing in products:
                    if existing["id"] == p["id"]:
                        cols = list(
                            dict.fromkeys(
                                [*(existing.get("ysCollections") or []), *(p.get("ysCollections") or [])]
                            )
                        )
                        existing["ysCollections"] = cols
                        for v in existing.get("variants") or []:
                            v["ysCollections"] = cols
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
        "/* Auto-generated by scripts/build-ys-catalog.py — do not edit */\n"
        'import type { Product } from "@/data/product-types";\n'
        'import data from "./ys-catalog.json";\n\n'
        "/** Saint Laurent catalog (JSON import keeps the TS module small for Vercel builds). */\n"
        "export const ysCatalogProducts = data as unknown as Product[];\n",
        encoding="utf-8",
    )
    save_json(CACHE, cache)
    print(f"OK ys catalog products={len(products)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
