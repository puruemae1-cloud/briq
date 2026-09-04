#!/usr/bin/env python3
"""Build Belstaff catalogue JSON from scraped raw (PS pricing + KO copy)."""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from ko_qa import en_ratio, translate_en_to_ko  # noqa: E402

# Keep module-level aliases used elsewhere in this file.

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog_image_guard import existing_images  # noqa: E402
RAW_PATH = ROOT / "src/data/bs/bs-catalog-raw.json"
OUT_JSON = ROOT / "src/data/bs/bs-catalog.json"
OUT_TS = ROOT / "src/data/bs/bs-catalog.ts"
CACHE_PATH = ROOT / "src/data/bs/bs-translate-cache.json"
DETAILS_HANDLE = ROOT / "src/data/bs/bs-details-cache.json"


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


def t(text: str | None) -> str:
    return translate_en_to_ko(text, _KO)


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


def load_details_cache() -> dict[str, dict]:
    if not DETAILS_HANDLE.exists():
        return {}
    try:
        data = json.loads(DETAILS_HANDLE.read_text())
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def merge_pdp_details(row: dict, cache: dict[str, dict]) -> dict:
    """Attach official accordion details/fit/care onto a raw product row."""
    handle = str(row.get("handle") or "")
    cached = cache.get(handle) if handle else None
    if not isinstance(cached, dict):
        cached = {}
    out = dict(row)
    for key in ("details", "fit", "care"):
        cur = out.get(key)
        if isinstance(cur, list) and cur:
            continue
        val = cached.get(key)
        if isinstance(val, list) and val:
            out[key] = val
    return out


def build_story_sections(
    *,
    name_ko: str,
    desc_ko: str,
    features: list[str],
    fit_lines: list[str],
    local_imgs: list[str],
) -> list[dict] | None:
    """Richer PDP story: intro + detail bullets + remaining gallery frames."""
    if not desc_ko and not features and not local_imgs:
        return None
    sections: list[dict] = []
    body_parts: list[str] = []
    if desc_ko:
        body_parts.append(desc_ko)
    if features:
        body_parts.append("\n".join(f"• {line}" for line in features))
    if fit_lines:
        body_parts.append("\n".join(f"• {line}" for line in fit_lines))
    intro_body = "\n\n".join(body_parts).strip()
    if intro_body or local_imgs:
        sections.append(
            {
                "titleKo": name_ko,
                "bodyKo": intro_body or name_ko,
                "image": local_imgs[0] if local_imgs else None,
                "imageAlt": name_ko,
            }
        )
    captions = [
        "제품 디테일",
        "측면 디테일",
        "후면 디테일",
        "디테일 클로즈업",
        "추가 컷",
        "착용 컷",
        "구성 디테일",
    ]
    for i, img in enumerate(local_imgs[1:7], start=0):
        # First gallery caption carries the full details list; later frames
        # keep a single highlight so every official photo has Korean copy.
        if i == 0 and features:
            body = "\n".join(f"• {line}" for line in features)
            if fit_lines:
                body = body + "\n" + "\n".join(f"• {line}" for line in fit_lines)
        else:
            feat = features[i] if i < len(features) else ""
            body = feat or "벨스타프 공식 제품 컷입니다."
        sections.append(
            {
                "titleKo": captions[i] if i < len(captions) else f"갤러리 {i + 2}",
                "bodyKo": body,
                "image": img,
                "imageAlt": f"{name_ko} {i + 2}",
                "layout": "caption",
                "reverse": bool(i % 2),
            }
        )
    for s in sections:
        if not s.get("image"):
            s.pop("image", None)
            s.pop("imageAlt", None)
    return sections or None


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


MEN_CORE = {
    "new",
    "outerwear",
    "clothing",
    "footwear",
    "accessories",
    "men-icons",
    "men-motorcycle",
    "mens-sale",
}
WOMEN_CORE = {
    "women-new",
    "women-outerwear",
    "women-clothing",
    "women-footwear",
    "women-accessories",
    "women-icons",
    "women-motorcycle",
    "womens-sale",
}
LUXURY_FORCE = {
    "men-icons",
    "women-icons",
    "men-motorcycle",
    "women-motorcycle",
    "mens-sale",
    "womens-sale",
}
OUTER_M = {"JACKETS - M", "COATS - M", "GILETS - M"}
OUTER_W = {"JACKETS - W", "COATS - W", "GILETS - W"}


def is_women(row: dict) -> bool:
    channels = set(row.get("channels") or [])
    ptype = row.get("product_type") or ""
    if channels & {
        "women-new",
        "women-outerwear",
        "women-clothing",
        "women-footwear",
        "women-accessories",
        "women-icons",
        "women-motorcycle",
        "womens-sale",
    }:
        return True
    if any(str(c).startswith("women-") for c in channels):
        return True
    if ptype.endswith("- W"):
        return True
    tags = {str(t).lower() for t in (row.get("tags") or [])}
    if ("women" in tags or "womenswear" in tags) and not ptype.endswith("- M"):
        if not (channels & MEN_CORE):
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


def is_bag(ptype: str, title: str = "") -> bool:
    """True Belstaff bags (not wash bags / wallets)."""
    if (ptype or "").startswith("BAGS"):
        return True
    low = (title or "").lower()
    if "wash bag" in low:
        return False
    return False


def is_accessory(channels: set[str], ptype: str, title: str) -> bool:
    if "footwear" in channels or "women-footwear" in channels:
        return False
    if is_bag(ptype, title):
        return False
    if (
        ("accessories" in channels or "women-accessories" in channels)
        and "clothing" not in channels
        and "women-clothing" not in channels
        and "outerwear" not in channels
        and "women-outerwear" not in channels
    ):
        # Accessories channel alone isn't enough if it's actually a bag type
        if is_bag(ptype, title):
            return False
        # Don't treat pure bag titles in accessories channel as soft accessories
        # when product_type is BAGS (handled above). Other channel-only accessories OK.
        return True
    if any(ptype.startswith(p) for p in ACC_TYPES_PREFIX):
        return True
    low = (title or "").lower()
    if any(k in low for k in ("wallet", "belt", "cap", "beanie", "scarf", "glove")):
        if "jacket" not in low and "shirt" not in low:
            return True
    return False


def _dedupe(cols: list[str]) -> list[str]:
    seen: set[str] = set()
    return [c for c in cols if not (c in seen or seen.add(c))]


MEN_CHANNELS = {
    "new",
    "outerwear",
    "clothing",
    "footwear",
    "accessories",
    "men-icons",
    "men-motorcycle",
    "mens-sale",
}


def classify(row: dict) -> tuple[str, str, list[str]]:
    """category, subcategory, bsCollections."""
    channels = set(row.get("channels") or [])
    ptype = row.get("product_type") or ""
    title = row.get("title") or ""
    women = is_women(row)

    icons_men = "men-icons" in channels
    icons_women = "women-icons" in channels
    moto_men = "men-motorcycle" in channels
    moto_women = "women-motorcycle" in channels
    sale_men = "mens-sale" in channels
    sale_women = "womens-sale" in channels
    force_luxury = bool(channels & LUXURY_FORCE)

    has_men_ch = bool(channels & MEN_CORE)
    has_women_ch = bool(channels & WOMEN_CORE) or any(
        str(c).startswith("women-") for c in channels
    )
    shoe_like = is_shoe(channels, ptype)
    bag_like = is_bag(ptype, title)
    acc_like = is_accessory(channels, ptype, title)

    if shoe_like and not force_luxury:
        cols = ["belstaff-shoes"]
        leaf = (
            "bs-shoes-women"
            if (women or "women-footwear" in channels)
            else "bs-shoes-men"
        )
        if "footwear" in channels or (has_men_ch and not has_women_ch and not women):
            cols.append("bs-shoes-men")
            if not women and "women-footwear" not in channels:
                leaf = "bs-shoes-men"
        if women or "women-footwear" in channels:
            if "bs-shoes-women" not in cols:
                cols.append("bs-shoes-women")
            leaf = "bs-shoes-women"
        if "bs-shoes-men" not in cols and "bs-shoes-women" not in cols:
            cols.append(leaf)
        return "shoes", leaf, _dedupe(cols)

    if bag_like and not force_luxury:
        return "bags", "belstaff-bags", ["belstaff-bags"]

    if acc_like and not force_luxury:
        cols = ["belstaff-accessories"]
        if has_men_ch or (not has_women_ch and not women):
            cols.append("bs-acc-men")
        if has_women_ch or women:
            cols.append("bs-acc-women")
        if "bs-acc-men" not in cols and "bs-acc-women" not in cols:
            cols.append("bs-acc-women" if women else "bs-acc-men")
        leaf = "bs-acc-women" if (women or has_women_ch) else "bs-acc-men"
        return "accessories", leaf, _dedupe(cols)

    women_path = bool(
        women or icons_women or moto_women or sale_women or has_women_ch
    )
    men_path = bool(channels & MEN_CHANNELS) or (
        not women_path and not ptype.endswith("- W")
    )
    if ptype.endswith("- W") and not (channels & MEN_CHANNELS):
        men_path = False
        women_path = True

    cols = ["belstaff"]
    if sale_men or sale_women:
        cols.append("bs-sale")
        if sale_men:
            cols.append("bs-sale-men")
        if sale_women:
            cols.append("bs-sale-women")

    if women_path:
        cols.append("bs-women")
        if "women-new" in channels:
            cols.append("bs-women-new")
        if "women-outerwear" in channels or ptype in OUTER_W:
            cols.append("bs-women-outerwear")
        if "women-clothing" in channels or (
            ptype.endswith("- W")
            and ptype not in OUTER_W
            and not shoe_like
            and not acc_like
        ):
            cols.append("bs-women-clothing")
        if icons_women:
            cols.append("bs-women-icons")
        if moto_women:
            cols.append("bs-women-motorcycle")
        if (
            "bs-women-outerwear" not in cols
            and "bs-women-clothing" not in cols
            and not shoe_like
            and not acc_like
            and ptype.endswith("- W")
        ):
            cols.append(
                "bs-women-outerwear" if ptype in OUTER_W else "bs-women-clothing"
            )

    if men_path:
        cols.append("bs-men")
        if "new" in channels:
            cols.append("bs-men-new")
        if "outerwear" in channels or ptype in OUTER_M:
            cols.append("bs-men-outerwear")
        if "clothing" in channels or (
            ptype.endswith("- M")
            and ptype not in OUTER_M
            and not shoe_like
            and not acc_like
        ):
            cols.append("bs-men-clothing")
        if ptype in OUTER_M and "bs-men-outerwear" not in cols:
            cols.append("bs-men-outerwear")
        if icons_men:
            cols.append("bs-men-icons")
        if moto_men:
            cols.append("bs-men-motorcycle")
        if (
            "bs-men-outerwear" not in cols
            and "bs-men-clothing" not in cols
            and not shoe_like
            and not acc_like
            and ptype.endswith("- M")
        ):
            cols.append("bs-men-clothing")

    if icons_women:
        leaf = "bs-women-icons"
    elif moto_women:
        leaf = "bs-women-motorcycle"
    elif icons_men and not women_path:
        leaf = "bs-men-icons"
    elif moto_men and not women_path:
        leaf = "bs-men-motorcycle"
    elif sale_women and not (
        {"bs-women-outerwear", "bs-women-clothing", "bs-women-new"} & set(cols)
    ):
        leaf = "bs-sale-women"
    elif sale_men and not women_path and not (
        {"bs-men-outerwear", "bs-men-clothing", "bs-men-new"} & set(cols)
    ):
        leaf = "bs-sale-men"
    elif women_path and "bs-women-outerwear" in cols and (
        "women-outerwear" in channels or ptype in OUTER_W
    ):
        leaf = "bs-women-outerwear"
    elif women_path and "bs-women-clothing" in cols:
        leaf = "bs-women-clothing"
    elif women_path and "bs-women-new" in cols:
        leaf = "bs-women-new"
    elif women_path and sale_women:
        leaf = "bs-sale-women"
    elif women_path:
        leaf = "bs-women"
    elif "bs-men-outerwear" in cols and ("outerwear" in channels or ptype in OUTER_M):
        leaf = "bs-men-outerwear"
    elif "bs-men-clothing" in cols:
        leaf = "bs-men-clothing"
    elif "bs-men-new" in cols:
        leaf = "bs-men-new"
    elif sale_men:
        leaf = "bs-sale-men"
    else:
        leaf = "bs-men"

    return "luxury", leaf, _dedupe(cols)


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
    details_cache = load_details_cache()
    now = datetime.now(timezone.utc)
    out: list[dict] = []

    # Preserve Briq registration timestamps across rebuilds so re-scrapes
    # don't reshuffle the homepage / 최신등록순 order.
    # Exception: when an existing SKU newly joins a "drop" collection
    # (Icons / Motorcycle / Sale), bump registeredAt so it surfaces on top.
    RELIST_COLLECTIONS = {
        "bs-men-icons",
        "bs-women-icons",
        "bs-men-motorcycle",
        "bs-women-motorcycle",
        "bs-sale-men",
        "bs-sale-women",
        "belstaff-bags",
    }
    prev_registered: dict[str, str] = {}
    prev_collections: dict[str, set[str]] = {}
    if OUT_JSON.exists():
        try:
            for prev in json.loads(OUT_JSON.read_text()):
                pid = prev.get("id")
                if not pid:
                    continue
                reg = prev.get("registeredAt")
                if reg:
                    prev_registered[str(pid)] = str(reg)
                prev_collections[str(pid)] = {
                    str(c) for c in (prev.get("bsCollections") or [])
                }
        except Exception:
            prev_registered = {}
            prev_collections = {}

    new_stamp_i = 0

    for idx, row_in in enumerate(products_in):
        row = merge_pdp_details(row_in, details_cache)
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
        local_imgs = existing_images(
            [f"/products/bs-pdp/{handle}/{i}.jpg" for i in range(1, n_img + 1)]
        )
        if not local_imgs:
            print(f"skip no local image: {handle}", flush=True)
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

        fit_ko = []
        for line in row.get("fit") or []:
            line = re.sub(r"\s+", " ", str(line)).strip()
            if line:
                fit_ko.append(t(line))

        specs = []
        for line in fit_ko:
            specs.append({"labelKo": "핏", "valueKo": line})
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
        # - newly joining Icons / Motorcycle / Sale also get "now"
        pid = f"bs-{handle}"
        gained_relist = bool(
            (set(cols) & RELIST_COLLECTIONS)
            - prev_collections.get(pid, set())
        )
        if pid in prev_registered and not gained_relist:
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
        story = build_story_sections(
            name_ko=name_ko,
            desc_ko=desc_ko,
            features=features,
            fit_lines=fit_ko,
            local_imgs=local_imgs,
        )
        # Above-fold copy: official intro + Details/Fit accordion (Korean).
        desc_parts: list[str] = []
        if desc_ko:
            desc_parts.append(desc_ko)
        if features:
            desc_parts.append("\n".join(f"• {line}" for line in features))
        if fit_ko:
            desc_parts.append("\n".join(f"• {line}" for line in fit_ko))
        full_desc_ko = "\n\n".join(desc_parts).strip() or desc_ko
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
            "descriptionKo": full_desc_ko,
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
            "storySections": story,
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
