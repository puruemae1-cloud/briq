#!/usr/bin/env python3
"""Build Belstaff catalogue JSON from scraped raw (PS pricing + KO copy)."""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "src/data/bs/bs-catalog-raw.json"
OUT_JSON = ROOT / "src/data/bs/bs-catalog.json"
OUT_TS = ROOT / "src/data/bs/bs-catalog.ts"
CACHE_PATH = ROOT / "src/data/bs/bs-translate-cache.json"


def gbp_to_krw(gbp: float | None) -> int:
    """Same tiered formula as Paul Smith."""
    if gbp is None:
        return 0
    g = float(gbp)
    if g <= 110:
        base = g * 2100 * 1.06 + 20_000
    else:
        base = g * 2100 * 1.10 * 1.05 + 20_000
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


def title_case_name(title: str) -> str:
    s = (title or "").strip()
    if not s:
        return s
    # Keep short ALLCAPS brands tokens readable
    if s.isupper() and len(s) > 3:
        return " ".join(
            w.capitalize() if w.lower() not in {"uk", "us", "eu"} else w.upper()
            for w in s.split()
        )
    return s


def accent_for(color: str) -> str:
    h = hashlib.md5((color or "x").encode()).hexdigest()
    r = 40 + int(h[0:2], 16) % 80
    g = 40 + int(h[2:4], 16) % 80
    b = 40 + int(h[4:6], 16) % 80
    return f"#{r:02x}{g:02x}{b:02x}"


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:70] or "item"


def color_key(color: str) -> str:
    return slugify(color) or "default"


SHOE_TYPES = {
    "BOOTS - M",
    "TRAINERS - M",
    "SHOES - M",
    "FOOTWEAR - M",
}
ACC_TYPES_PREFIX = (
    "HATS",
    "WALLET",
    "BAGS",
    "HOME ACCESSORIES",
    "MISC",
    "GIFT",
)
OUTER_TYPES = {"JACKETS - M", "COATS - M", "GILETS - M"}


def is_shoe(channels: set[str], ptype: str) -> bool:
    if "footwear" in channels:
        return True
    return ptype in SHOE_TYPES or ptype.startswith("BOOTS") or ptype.startswith("TRAINERS")


def is_accessory(channels: set[str], ptype: str, title: str) -> bool:
    if "footwear" in channels:
        return False
    if "accessories" in channels and "clothing" not in channels and "outerwear" not in channels:
        return True
    if any(ptype.startswith(p) for p in ACC_TYPES_PREFIX):
        return True
    low = (title or "").lower()
    if any(k in low for k in ("wallet", "belt", "cap", "beanie", "scarf", "glove", "bag")):
        if "jacket" not in low and "shirt" not in low:
            return True
    return False


def classify(row: dict) -> tuple[str, str, list[str]]:
    """category, subcategory, bsCollections."""
    channels = set(row.get("channels") or [])
    ptype = row.get("product_type") or ""
    title = row.get("title") or ""

    # Shoes (incl. new-arrivals footwear) → 슈즈 → 벨스타프 → 남성용
    if is_shoe(channels, ptype):
        return "shoes", "bs-shoes-men", ["belstaff-shoes", "bs-shoes-men"]

    # Accessories → 악세서리 → 벨스타프 → 남성용
    if is_accessory(channels, ptype, title):
        return "accessories", "bs-acc-men", ["belstaff-accessories", "bs-acc-men"]

    cols = ["belstaff", "bs-men"]
    if "new" in channels:
        cols.append("bs-men-new")
    if "outerwear" in channels or ptype in OUTER_TYPES:
        cols.append("bs-men-outerwear")
    if "clothing" in channels or ptype not in OUTER_TYPES:
        cols.append("bs-men-clothing")
    if ptype in OUTER_TYPES and "bs-men-outerwear" not in cols:
        cols.append("bs-men-outerwear")
    if "bs-men-outerwear" not in cols and "bs-men-clothing" not in cols:
        cols.append("bs-men-clothing")

    if "bs-men-outerwear" in cols and "clothing" not in channels and ptype in OUTER_TYPES:
        leaf = "bs-men-outerwear"
    elif "bs-men-outerwear" in cols and "outerwear" in channels:
        leaf = "bs-men-outerwear"
    elif "bs-men-clothing" in cols:
        leaf = "bs-men-clothing"
    else:
        leaf = "bs-men-new"

    seen: set[str] = set()
    cols = [c for c in cols if not (c in seen or seen.add(c))]
    return "luxury", leaf, cols

def shoe_fallback_chart() -> dict:
    return {
        "id": "bs-shoes-mens-uk",
        "titleKo": "벨스타프 남성 슈즈 사이즈 차트 (UK)",
        "noteKo": "Belstaff 표기 사이즈는 UK 기준입니다. 발 길이를 재어 가장 가까운 수치를 선택하세요.",
        "headers": ["UK", "EU", "US", "KR(mm)"],
        "rows": [
            ["6", "40", "7", "250"],
            ["6.5", "40.5", "7.5", "253"],
            ["7", "41", "8", "255"],
            ["7.5", "41.5", "8.5", "258"],
            ["8", "42", "9", "260"],
            ["8.5", "42.5", "9.5", "265"],
            ["9", "43", "10", "270"],
            ["9.5", "43.5", "10.5", "273"],
            ["10", "44", "11", "275"],
            ["10.5", "44.5", "11.5", "278"],
            ["11", "45", "12", "280"],
            ["12", "46", "13", "290"],
            ["13", "47", "14", "295"],
        ],
    }


def apparel_fallback_chart() -> dict:
    return {
        "id": "bs-men-apparel-alpha",
        "titleKo": "벨스타프 남성 의류 사이즈 차트",
        "noteKo": "일반 알파 사이즈 참고표입니다. 제품별 실측이 있으면 실측을 우선하세요.",
        "headers": ["사이즈", "가슴(cm)", "허리(cm)"],
        "rows": [
            ["XS", "90", "78.5"],
            ["S", "94–98", "82.5–86.5"],
            ["M", "98–102", "86.5–90.5"],
            ["L", "102–106", "90.5–94.5"],
            ["XL", "106–110", "94.5–98.5"],
            ["XXL", "110–114", "98.5–102.5"],
            ["3XL", "114–118", "102.5–106.5"],
        ],
    }


def to_size_chart(raw_chart: dict | None, *, shoes: bool, title_ko: str) -> dict:
    if raw_chart and raw_chart.get("rows") and raw_chart.get("headers"):
        headers = list(raw_chart["headers"])
        rows = list(raw_chart["rows"])
        keys = set(raw_chart.get("measureKeys") or [])
        joined = " ".join(headers)
        has_foot = ("Foot Length" in keys) or ("발 길이" in joined)
        has_chest = ("Chest" in keys) or ("가슴" in joined)
        # Reject mismatched charts (e.g. trainer PDP returning apparel grid).
        if shoes and not has_foot:
            return shoe_fallback_chart()
        if not shoes and has_foot and not has_chest:
            return apparel_fallback_chart()
        # Drop empty trailing measure columns mismatch
        width = len(headers)
        rows = [r[:width] + ["—"] * max(0, width - len(r)) for r in rows]
        return {
            "id": f"bs-measure-{slugify(title_ko)[:40]}",
            "titleKo": f"{title_ko} 사이즈 차트 (cm)",
            "noteKo": "Belstaff 공식 바디/제품 측정값(cm)입니다. 브랜드·시즌에 따라 핏이 다를 수 있으니 참고용으로 확인해 주세요.",
            "headers": headers,
            "rows": rows,
        }
    if shoes:
        return shoe_fallback_chart()
    return apparel_fallback_chart()


def build() -> None:
    raw = json.loads(RAW_PATH.read_text())
    products_in = raw.get("products") or []
    now = datetime.now(timezone.utc)
    out: list[dict] = []

    for idx, row in enumerate(products_in):
        handle = row.get("handle") or ""
        if not handle:
            continue
        title = title_case_name(row.get("title") or handle)
        color = row.get("colorName") or "Default"
        body = html_to_text(row.get("body_html") or "")
        cat, leaf, cols = classify(row)
        shoes = cat == "shoes"

        # Images
        n_img = min(8, len(row.get("images") or []))
        local_imgs = [f"/products/bs-pdp/{handle}/{i}.jpg" for i in range(1, n_img + 1)]
        if not local_imgs:
            continue

        variants_out = []
        gbp_prices = []
        for v in row.get("variants") or []:
            gbp = float(v.get("price") or 0)
            if gbp <= 0:
                continue
            gbp_list = v.get("compare_at_price")
            try:
                gbp_list_f = float(gbp_list) if gbp_list else None
            except Exception:
                gbp_list_f = None
            if gbp_list_f is not None and gbp_list_f <= gbp + 0.01:
                gbp_list_f = None
            krw = gbp_to_krw(gbp)
            krw_list = gbp_to_krw(gbp_list_f) if gbp_list_f else None
            size = v.get("option1") or ""
            # Belstaff: option1=size, option2=colour
            ckey = color_key(color)
            vid = f"bs-{handle}-{slugify(size) or 'os'}"
            variants_out.append(
                {
                    "id": vid,
                    "name": f"{title} — {size}" if size else title,
                    "nameKo": f"{t(title)} — {size}" if size else t(title),
                    "sku": v.get("sku") or "",
                    "gbpPrice": gbp,
                    "price": krw,
                    **({"compareAtPrice": krw_list} if krw_list and krw_list > krw else {}),
                    "image": local_imgs[0],
                    "images": local_imgs,
                    "hoverImage": local_imgs[1] if len(local_imgs) > 1 else local_imgs[0],
                    "sourceUrl": f"https://belstaff.com/products/{handle}",
                    "inStock": bool(v.get("available")),
                    "colorKey": ckey,
                    "colorNameKo": t(color) if en_ratio(color) > 0.3 else color,
                    "size": size,
                    "bsCollections": cols,
                }
            )
            if v.get("available"):
                gbp_prices.append(gbp)
            else:
                gbp_prices.append(gbp)

        if not variants_out:
            continue

        sell_gbps = [float(v.get("price") or 0) for v in row.get("variants") or [] if v.get("available")]
        if not sell_gbps:
            sell_gbps = [float(v.get("price") or 0) for v in row.get("variants") or [] if v.get("price")]
        gbp_sell = min(sell_gbps) if sell_gbps else 0
        if gbp_sell <= 0:
            continue

        list_gbps = []
        for v in row.get("variants") or []:
            c = v.get("compare_at_price")
            try:
                cf = float(c) if c else None
            except Exception:
                cf = None
            if cf and cf > float(v.get("price") or 0) + 0.01:
                list_gbps.append(cf)
        gbp_list = min(list_gbps) if list_gbps else None

        price = gbp_to_krw(gbp_sell)
        compare = gbp_to_krw(gbp_list) if gbp_list else None

        name_ko = t(title)
        desc_ko = t(body) if body else ""
        # Official PDP Details accordion (preferred) → featuresKo
        features = []
        for line in row.get("details") or []:
            line = re.sub(r"\s+", " ", str(line)).strip()
            if line:
                features.append(t(line))
        if not features:
            for line in (body or "").split("\n"):
                line = line.strip(" •-\t")
                if 12 <= len(line) <= 120:
                    features.append(t(line))
                if len(features) >= 6:
                    break

        specs = []
        for line in row.get("fit") or []:
            line = re.sub(r"\s+", " ", str(line)).strip()
            if line:
                specs.append({"labelKo": "핏", "valueKo": t(line)})
        for line in (row.get("care") or [])[:6]:
            line = re.sub(r"\s+", " ", str(line)).strip()
            if line:
                specs.append({"labelKo": "케어", "valueKo": t(line)})

        chart = to_size_chart(
            row.get("sizeChart"), shoes=shoes, title_ko=name_ko or "벨스타프"
        )

        # registration time: newer first, slightly offset by index
        pub = row.get("published_at") or row.get("created_at")
        try:
            reg = datetime.fromisoformat(pub.replace("Z", "+00:00")) if pub else now
        except Exception:
            reg = now - timedelta(minutes=idx)
        # bump scrape order so new arrivals rank well among same publish day
        if "new" in set(row.get("channels") or []):
            reg = max(reg, now - timedelta(hours=6) - timedelta(seconds=idx))

        badge = None
        if "new" in set(row.get("channels") or []):
            badge = "New"
        if compare and compare > price:
            badge = "Sale"

        in_stock = any(v["inStock"] for v in variants_out)
        product = {
            "id": f"bs-{handle}",
            "name": title,
            "nameKo": name_ko,
            "brand": "벨스타프",
            "price": price,
            **({"compareAtPrice": compare} if compare and compare > price else {}),
            "category": cat,
            "subcategory": leaf,
            "bsCollections": cols,
            "tags": ["belstaff", "벨스타프", *cols],
            "descriptionKo": desc_ko,
            "image": local_imgs[0],
            "images": local_imgs,
            "hoverImage": local_imgs[1] if len(local_imgs) > 1 else local_imgs[0],
            "accent": accent_for(color),
            **({"badge": badge} if badge else {}),
            "gbpPrice": gbp_sell,
            **({"gbpListPrice": gbp_list} if gbp_list else {}),
            "sku": next((v.get("sku") for v in row.get("variants") or [] if v.get("sku")), ""),
            "sourceUrl": f"https://belstaff.com/products/{handle}",
            "inStock": in_stock,
            "variants": variants_out,
            "sizeChart": chart,
            "registeredAt": reg.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "featuresKo": features or None,
            "techSpecs": specs or None,
            "storySections": [
                {
                    "titleKo": name_ko,
                    "bodyKo": desc_ko,
                    "image": local_imgs[0],
                    "imageAlt": name_ko,
                }
            ]
            if desc_ko
            else None,
        }
        # drop None features
        if not product.get("featuresKo"):
            product.pop("featuresKo", None)
        if not product.get("techSpecs"):
            product.pop("techSpecs", None)
        if not product.get("storySections"):
            product.pop("storySections", None)

        out.append(product)
        if (idx + 1) % 40 == 0:
            print(f"  built {idx+1}/{len(products_in)}", flush=True)
            CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2) + "\n")

    # sort: newest registered first
    out.sort(key=lambda p: p.get("registeredAt") or "", reverse=True)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_TS.write_text(
        'import type { Product } from "@/data/products";\n'
        'import data from "./bs-catalog.json";\n\n'
        "/** Auto-generated — thin wrapper over JSON catalogue. */\n"
        "export const bsCatalogProducts = data as unknown as Product[];\n",
        encoding="utf-8",
    )
    CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2) + "\n")

    from collections import Counter

    c = Counter(p["subcategory"] for p in out)
    print(f"Wrote {len(out)} products → {OUT_JSON.relative_to(ROOT)}")
    for k, v in c.most_common():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    build()
