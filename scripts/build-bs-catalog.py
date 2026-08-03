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
    "BOOTS - W",
    "TRAINERS - W",
    "SHOES - W",
    "FOOTWEAR - W",
}
ACC_TYPES_PREFIX = (
    "HATS",
    "WALLET",
    "BAGS",
    "HOME ACCESSORIES",
    "MISC",
    "GIFT",
)
OUTER_TYPES = {
    "JACKETS - M",
    "COATS - M",
    "GILETS - M",
    "JACKETS - W",
    "COATS - W",
    "GILETS - W",
}


def is_women(row: dict) -> bool:
    channels = set(row.get("channels") or [])
    ptype = row.get("product_type") or ""
    if any(str(c).startswith("women-") for c in channels):
        return True
    if ptype.endswith("- W"):
        return True
    tags = {str(t).lower() for t in (row.get("tags") or [])}
    if ("women" in tags or "womenswear" in tags) and not ptype.endswith("- M"):
        # only if no explicit men channel
        if not (channels & {"new", "outerwear", "clothing", "footwear", "accessories"}):
            return True
    return False


def is_shoe(channels: set[str], ptype: str) -> bool:
    if "footwear" in channels or "women-footwear" in channels:
        return True
    return (
        ptype in SHOE_TYPES
        or ptype.startswith("BOOTS")
        or ptype.startswith("TRAINERS")
    )


def is_accessory(channels: set[str], ptype: str, title: str) -> bool:
    if "footwear" in channels or "women-footwear" in channels:
        return False
    if (
        ("accessories" in channels or "women-accessories" in channels)
        and "clothing" not in channels
        and "women-clothing" not in channels
        and "outerwear" not in channels
        and "women-outerwear" not in channels
    ):
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
    women = is_women(row)

    # Dual-list unisex: may have both men + women accessory channels
    has_men_ch = bool(
        channels & {"new", "outerwear", "clothing", "footwear", "accessories"}
    )
    has_women_ch = any(str(c).startswith("women-") for c in channels)

    if is_shoe(channels, ptype):
        cols = ["belstaff-shoes"]
        leaf = "bs-shoes-women" if (women or "women-footwear" in channels) else "bs-shoes-men"
        # if both footwear channels somehow
        if "footwear" in channels or (has_men_ch and not has_women_ch and not women):
            cols.append("bs-shoes-men")
            if not women and "women-footwear" not in channels:
                leaf = "bs-shoes-men"
        if women or "women-footwear" in channels:
            if "bs-shoes-women" not in cols:
                cols.append("bs-shoes-women")
            leaf = "bs-shoes-women" if (women or "women-footwear" in channels) else leaf
        if "bs-shoes-men" not in cols and "bs-shoes-women" not in cols:
            cols.append(leaf)
        seen: set[str] = set()
        cols = [c for c in cols if not (c in seen or seen.add(c))]
        return "shoes", leaf, cols

    if is_accessory(channels, ptype, title):
        cols = ["belstaff-accessories"]
        if has_men_ch or (not has_women_ch and not women):
            cols.append("bs-acc-men")
        if has_women_ch or women:
            cols.append("bs-acc-women")
        if "bs-acc-men" not in cols and "bs-acc-women" not in cols:
            cols.append("bs-acc-women" if women else "bs-acc-men")
        leaf = "bs-acc-women" if (women or has_women_ch) else "bs-acc-men"
        seen = set()
        cols = [c for c in cols if not (c in seen or seen.add(c))]
        return "accessories", leaf, cols

    # Apparel / outerwear
    cols = ["belstaff"]
    if women or has_women_ch:
        cols.append("bs-women")
        if "women-new" in channels:
            cols.append("bs-women-new")
        if "women-outerwear" in channels or ptype in {
            "JACKETS - W",
            "COATS - W",
            "GILETS - W",
        }:
            cols.append("bs-women-outerwear")
        if "women-clothing" in channels or ptype not in {
            "JACKETS - W",
            "COATS - W",
            "GILETS - W",
        }:
            if "women-clothing" in channels or (
                ptype.endswith("- W")
                and ptype not in {"JACKETS - W", "COATS - W", "GILETS - W"}
            ):
                cols.append("bs-women-clothing")
        if "bs-women-outerwear" not in cols and "bs-women-clothing" not in cols:
            if ptype in {"JACKETS - W", "COATS - W", "GILETS - W"}:
                cols.append("bs-women-outerwear")
            else:
                cols.append("bs-women-clothing")
        if "bs-women-outerwear" in cols and (
            "women-outerwear" in channels
            or ptype in {"JACKETS - W", "COATS - W", "GILETS - W"}
        ):
            leaf = "bs-women-outerwear"
        elif "bs-women-clothing" in cols:
            leaf = "bs-women-clothing"
        else:
            leaf = "bs-women-new"
        # If also listed under men channels, keep men memberships too
        if has_men_ch and not ptype.endswith("- W"):
            cols.append("bs-men")
    else:
        cols.append("bs-men")
        if "new" in channels:
            cols.append("bs-men-new")
        if "outerwear" in channels or ptype in {"JACKETS - M", "COATS - M", "GILETS - M"}:
            cols.append("bs-men-outerwear")
        if "clothing" in channels or ptype not in {
            "JACKETS - M",
            "COATS - M",
            "GILETS - M",
        }:
            cols.append("bs-men-clothing")
        if ptype in {"JACKETS - M", "COATS - M", "GILETS - M"} and "bs-men-outerwear" not in cols:
            cols.append("bs-men-outerwear")
        if "bs-men-outerwear" not in cols and "bs-men-clothing" not in cols:
            cols.append("bs-men-clothing")
        if "bs-men-outerwear" in cols and (
            "outerwear" in channels or ptype in {"JACKETS - M", "COATS - M", "GILETS - M"}
        ):
            leaf = "bs-men-outerwear"
        elif "bs-men-clothing" in cols:
            leaf = "bs-men-clothing"
        else:
            leaf = "bs-men-new"

    seen = set()
    cols = [c for c in cols if not (c in seen or seen.add(c))]
    return "luxury", leaf, cols
def shoe_fallback_chart(*, women: bool = False) -> dict:
    gender = "여성" if women else "남성"
    return {
        "id": "bs-shoes-womens-uk" if women else "bs-shoes-mens-uk",
        "titleKo": f"벨스타프 {gender} 슈즈 사이즈 차트 (UK)",
        "noteKo": "Belstaff 표기 사이즈는 UK 기준입니다. 발 길이를 재어 가장 가까운 수치를 선택하세요.",
        "headers": ["UK", "EU", "US", "KR(mm)"],
        "rows": [
            ["3", "36", "5", "220"],
            ["3.5", "36.5", "5.5", "225"],
            ["4", "37", "6", "230"],
            ["4.5", "37.5", "6.5", "235"],
            ["5", "38", "7", "240"],
            ["5.5", "38.5", "7.5", "245"],
            ["6", "39", "8", "250"],
            ["6.5", "40", "8.5", "253"],
            ["7", "41", "9", "255"],
            ["7.5", "41.5", "9.5", "258"],
            ["8", "42", "10", "260"],
        ]
        if women
        else [
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


def apparel_fallback_chart(*, women: bool = False) -> dict:
    gender = "여성" if women else "남성"
    return {
        "id": "bs-women-apparel-alpha" if women else "bs-men-apparel-alpha",
        "titleKo": f"벨스타프 {gender} 의류 사이즈 차트",
        "noteKo": "일반 알파 사이즈 참고표입니다. 제품별 실측이 있으면 실측을 우선하세요.",
        "headers": ["사이즈", "가슴(cm)", "허리(cm)"],
        "rows": [
            ["XS", "80–84", "62–66"],
            ["S", "84–88", "66–70"],
            ["M", "88–92", "70–74"],
            ["L", "92–96", "74–78"],
            ["XL", "96–100", "78–82"],
        ]
        if women
        else [
            ["XS", "90", "78.5"],
            ["S", "94–98", "82.5–86.5"],
            ["M", "98–102", "86.5–90.5"],
            ["L", "102–106", "90.5–94.5"],
            ["XL", "106–110", "94.5–98.5"],
            ["XXL", "110–114", "98.5–102.5"],
            ["3XL", "114–118", "102.5–106.5"],
        ],
    }


def to_size_chart(
    raw_chart: dict | None, *, shoes: bool, title_ko: str, women: bool = False
) -> dict:
    if raw_chart and raw_chart.get("rows") and raw_chart.get("headers"):
        headers = list(raw_chart["headers"])
        rows = list(raw_chart["rows"])
        keys = set(raw_chart.get("measureKeys") or [])
        joined = " ".join(headers)
        has_foot = ("Foot Length" in keys) or ("발 길이" in joined)
        has_chest = ("Chest" in keys) or ("Bust" in keys) or ("가슴" in joined)
        if shoes and not has_foot:
            return shoe_fallback_chart(women=women)
        if not shoes and has_foot and not has_chest:
            return apparel_fallback_chart(women=women)
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
        return shoe_fallback_chart(women=women)
    return apparel_fallback_chart(women=women)

def build() -> None:
    raw = json.loads(RAW_PATH.read_text())
    products_in = raw.get("products") or []
    now = datetime.now(timezone.utc)
    out: list[dict] = []

    # Preserve Briq registration timestamps across rebuilds so re-scrapes
    # don't reshuffle the homepage / 최신등록순 order.
    prev_registered: dict[str, str] = {}
    if OUT_JSON.exists():
        try:
            for prev in json.loads(OUT_JSON.read_text()):
                pid = prev.get("id")
                reg = prev.get("registeredAt")
                if pid and reg:
                    prev_registered[str(pid)] = str(reg)
        except Exception:
            prev_registered = {}

    new_stamp_i = 0

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
            row.get("sizeChart"),
            shoes=shoes,
            title_ko=name_ko or "벨스타프",
            women=is_women(row),
        )

        # Briq registration time (not Belstaff publish date):
        # - preserve existing registeredAt on rebuilds
        # - brand-new SKUs get "now" so they surface on homepage / 최신등록순
        pid = f"bs-{handle}"
        if pid in prev_registered:
            try:
                reg = datetime.fromisoformat(
                    prev_registered[pid].replace("Z", "+00:00")
                )
            except Exception:
                reg = now - timedelta(seconds=new_stamp_i)
                new_stamp_i += 1
        else:
            reg = now - timedelta(seconds=new_stamp_i)
            new_stamp_i += 1

        badge = None
        chans = set(row.get("channels") or [])
        if "new" in chans or "women-new" in chans:
            badge = "New"
        if compare and compare > price:
            badge = "Sale"

        in_stock = any(v["inStock"] for v in variants_out)
        product = {
            "id": pid,
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
