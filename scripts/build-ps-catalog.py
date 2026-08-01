#!/usr/bin/env python3
"""Build Paul Smith mens catalogue TypeScript from scraped raw JSON."""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "src/data/ps/ps-catalog-raw.json"
OUT_PATH = ROOT / "src/data/ps/ps-catalog.ts"
CACHE_PATH = ROOT / "src/data/ps/ps-translate-cache.json"

# Burberry-like formula, but 1.18 → 1.10 for >£110
def gbp_to_krw(gbp: float | None) -> int:
    if gbp is None:
        return 0
    g = float(gbp)
    if g <= 110:
        base = g * 2100 * 1.06 + 20_000
    else:
        base = g * 2100 * 1.10 * 1.05 + 20_000
    return int(round(base / 1_000) * 1_000)


CLOTHING_TYPE_MAP = {
    "All in One": ("ps-men-all-in-one", "올인원"),
    "Coats": ("ps-men-coats", "코트"),
    "Dressing Gown": ("ps-men-dressing-gown", "드레싱 가운"),
    "Jackets": ("ps-men-jackets", "재킷"),
    "Jeans": ("ps-men-jeans", "진"),
    "Knitwear": ("ps-men-knitwear", "니트웨어"),
    "Loungewear": ("ps-men-loungewear", "라운지웨어"),
    "Polo Shirt": ("ps-men-polos", "폴로 셔츠"),
    "Pyjamas": ("ps-men-pyjamas", "파자마"),
    "Shirts": ("ps-men-shirts", "셔츠"),
    "Shorts": ("ps-men-shorts", "쇼츠"),
    "Suits": ("ps-men-suits", "수트"),
    "Sweat Pants": ("ps-men-sweat-pants", "스웻팬츠"),
    "Sweatshirts": ("ps-men-sweatshirts", "스웻셔츠"),
    "Swimwear": ("ps-men-swimwear", "스윔웨어"),
    "T-Shirts": ("ps-men-tshirts", "티셔츠"),
    "Trousers": ("ps-men-trousers", "트라우저"),
    "Underwear": ("ps-men-underwear", "언더웨어"),
    "Waistcoats": ("ps-men-waistcoats", "웨이스트코트"),
}

SHOE_STYLE_MAP = {
    "Boots": ("ps-shoes-boots", "부츠"),
    "Brogues": ("ps-shoes-brogues", "브로그"),
    "Derby Shoes": ("ps-shoes-derby", "더비 슈즈"),
    "Espadrilles": ("ps-shoes-espadrilles", "에스파드리유"),
    "Loafers": ("ps-shoes-loafers", "로퍼"),
    "Oxford Shoes": ("ps-shoes-oxford", "옥스포드"),
    "Sandals": ("ps-shoes-sandals", "샌들"),
    "Shoe Care": ("ps-shoes-care", "슈케어"),
    "Slides": ("ps-shoes-slides", "슬라이드"),
    "Trainers": ("ps-shoes-trainers", "스니커즈"),
}

# When Elevate `style` is missing, map product_type → shoe leaf
SHOE_PTYPE_MAP = {
    "Sneaker": ("ps-shoes-trainers", "스니커즈"),
    "Boots": ("ps-shoes-boots", "부츠"),
    "Loafer": ("ps-shoes-loafers", "로퍼"),
    "Slip On": ("ps-shoes-loafers", "로퍼"),
    "Sandal": ("ps-shoes-sandals", "샌들"),
    "Espadrille": ("ps-shoes-espadrilles", "에스파드리유"),
    "Shoe": ("ps-shoes-other", "기타 슈즈"),
}

ACC_TYPE_MAP = {
    "Bags": ("ps-acc-bags", "백"),
    "Belts": ("ps-acc-belts", "벨트"),
    "Boots": ("ps-acc-boots", "부츠"),
    "Ceramics": ("ps-acc-ceramics", "세라믹"),
    "Giftset": ("ps-acc-giftset", "기프트 세트"),
    "Gloves": ("ps-acc-gloves", "글러브"),
    "Hats": ("ps-acc-hats", "모자"),
    "Jewellery": ("ps-acc-jewellery", "주얼리"),
    "Keyrings": ("ps-acc-keyrings", "키링"),
    "Knitwear": ("ps-acc-knitwear", "니트웨어"),
    "Novelty Items": ("ps-acc-novelty", "노블티"),
    "Pocket Squares": ("ps-acc-pocket-squares", "포켓 스퀘어"),
    "Pyjamas": ("ps-acc-pyjamas", "파자마"),
    "Scarves": ("ps-acc-scarves", "스카프"),
    "Small Leather Goods": ("ps-acc-slg", "가죽 소품"),
    "Socks": ("ps-acc-socks", "삭스"),
    "Stationery": ("ps-acc-stationery", "스테이셔너리"),
    "Swimwear": ("ps-acc-swimwear", "스윔웨어"),
    "Ties": ("ps-acc-ties", "타이"),
    "Towels": ("ps-acc-towels", "타월"),
    "Umbrellas": ("ps-acc-umbrellas", "우산"),
    "Underwear": ("ps-acc-underwear", "언더웨어"),
}

MEASURE_Y_KO = {
    "Chest circumference": "가슴 둘레",
    "Sleeve length": "소매 길이",
    "Centre-Back length": "뒷중심 길이",
    "Center-Back length": "뒷중심 길이",
    "Waist circumference": "허리 둘레",
    "Hip circumference": "엉덩이 둘레",
    "Inside leg": "인심",
    "Inseam": "인심",
    "Thigh circumference": "허벅지 둘레",
    "Foot length": "발 길이",
    "Shoe size": "슈즈 사이즈",
}


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
    if en_ratio(s) < 0.35 or len(s) < 8:
        return s
    try:
        ko = gtx(s).strip()
        if ko:
            _KO[s] = ko
            return ko
    except Exception:
        pass
    return s


def js_str(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:70] or "item"


def price_pair(entity: dict, plp: dict) -> tuple[float, float]:
    sell = entity.get("priceAsNumber")
    listed = entity.get("priceBeforeDiscountAsNumber")
    if sell is None:
        sp = plp.get("sellingPrice") or {}
        sell = sp.get("min") if isinstance(sp, dict) else sell
    if listed is None:
        lp = plp.get("listPrice") or {}
        listed = lp.get("min") if isinstance(lp, dict) else listed
    try:
        sell_f = float(sell or 0)
    except Exception:
        sell_f = 0.0
    try:
        list_f = float(listed or sell_f or 0)
    except Exception:
        list_f = sell_f
    if list_f < sell_f:
        list_f = sell_f
    return sell_f, list_f


def cm_only(cell: str) -> str:
    s = (cell or "").strip()
    m = re.match(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*cm", s, re.I)
    if m:
        return m.group(1)
    # "98cm/38.6\""
    m = re.match(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*cm\s*/", s, re.I)
    if m:
        return m.group(1)
    return s


def chart_from_measurement(chart: dict, title: str) -> dict | None:
    if not chart or not chart.get("x") or not chart.get("y"):
        return None
    xs = [str(x) for x in chart.get("x") or []]
    ys = [str(y) for y in chart.get("y") or []]
    grid: dict[tuple[int, int], str] = {}
    for cell in chart.get("contents") or []:
        try:
            grid[(int(cell["x"]), int(cell["y"]))] = cm_only(str(cell.get("content") or ""))
        except Exception:
            continue
    headers = ["사이즈", *[MEASURE_Y_KO.get(y, t(y) or y) for y in ys]]
    rows = []
    for xi, size in enumerate(xs):
        row = [size]
        for yi, _y in enumerate(ys):
            row.append(grid.get((xi, yi), "—"))
        rows.append(row)
    if not rows:
        return None
    return {
        "id": f"ps-measure-{slugify(title)[:40]}",
        "titleKo": f"{title} 사이즈 차트 (cm)",
        "noteKo": "제품 실측값(cm)입니다. 브랜드·시즌에 따라 핏이 다를 수 있으니 참고용으로 확인해 주세요.",
        "headers": headers,
        "rows": rows,
    }


def shoe_size_chart() -> dict:
    # Paul Smith UK mens shoes — common UK→KR mapping (approx)
    return {
        "id": "ps-shoes-mens-uk",
        "titleKo": "폴 스미스 남성 슈즈 사이즈 차트 (UK)",
        "noteKo": "Paul Smith 표기 사이즈는 UK 기준입니다. 발 길이를 재어 가장 가까운 수치를 선택하세요.",
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
        ],
    }


def belt_size_chart() -> dict:
    return {
        "id": "ps-acc-belts-waist",
        "titleKo": "폴 스미스 남성 벨트 사이즈 차트 (인치)",
        "noteKo": "표기 사이즈는 허리 인치(UK) 기준입니다. 평소 바지 허리 사이즈에 맞춰 선택하세요.",
        "headers": ["벨트", "허리(inch)", "허리(cm)"],
        "rows": [
            ["28", "28", "71"],
            ["30", "30", "76"],
            ["32", "32", "81"],
            ["34", "34", "86"],
            ["36", "36", "91"],
            ["38", "38", "97"],
            ["40", "40", "102"],
            ["42", "42", "107"],
            ["44", "44", "112"],
        ],
    }


def sock_size_chart() -> dict:
    return {
        "id": "ps-acc-socks-uk",
        "titleKo": "폴 스미스 남성 삭스 사이즈 차트",
        "noteKo": "UK 슈즈 사이즈 기준 범위입니다. 두 사이즈 사이라면 큰 쪽을 선택하세요.",
        "headers": ["표기", "UK", "EU", "KR(mm)"],
        "rows": [
            ["3/5", "3–5", "36–38", "220–240"],
            ["6/8", "6–8", "39–42", "245–260"],
            ["9/12", "9–12", "43–46", "270–290"],
            ["S/M", "6–8", "39–42", "245–260"],
            ["L/XL", "9–12", "43–46", "270–290"],
            ["One Size", "6–11", "39–45", "245–280"],
        ],
    }


def hat_size_chart() -> dict:
    return {
        "id": "ps-acc-hats-alpha",
        "titleKo": "폴 스미스 남성 모자 사이즈 차트",
        "noteKo": "머리 둘레(cm) 기준 참고표입니다. 브랜드·모델에 따라 핏이 다를 수 있습니다.",
        "headers": ["사이즈", "머리 둘레(cm)"],
        "rows": [
            ["S", "55–56"],
            ["M", "57–58"],
            ["L", "59–60"],
            ["One Size", "56–59"],
        ],
    }


def glove_size_chart() -> dict:
    return {
        "id": "ps-acc-gloves-alpha",
        "titleKo": "폴 스미스 남성 글러브 사이즈 차트",
        "noteKo": "손 둘레(cm) 기준 참고표입니다. 장갑은 소재에 따라 늘어남이 다를 수 있습니다.",
        "headers": ["사이즈", "손 둘레(cm)"],
        "rows": [
            ["S", "19–20"],
            ["M", "21–22"],
            ["L", "23–24"],
            ["One Size", "20–23"],
        ],
    }


def apparel_alpha_chart(title: str) -> dict:
    return {
        "id": "ps-men-apparel-alpha",
        "titleKo": f"{title} 사이즈 차트 (알파)",
        "noteKo": "일반 알파 사이즈 참고표입니다. 제품별 실측이 있으면 실측을 우선하세요.",
        "headers": ["사이즈", "가슴(cm)", "허리(cm)"],
        "rows": [
            ["XS", "88", "76"],
            ["S", "94", "82"],
            ["M", "100", "88"],
            ["L", "106", "94"],
            ["XL", "114", "102"],
            ["XXL", "122", "110"],
        ],
    }


def infer_acc_type(ptype: str | None, title: str) -> tuple[str, str]:
    if ptype and str(ptype) in ACC_TYPE_MAP:
        return ACC_TYPE_MAP[str(ptype)]
    name = (title or "").lower()
    if "glove" in name:
        return ACC_TYPE_MAP["Gloves"]
    if "gift" in name or "three pack" in name or "two pack" in name:
        return ACC_TYPE_MAP["Giftset"]
    if "sock" in name:
        return ACC_TYPE_MAP["Socks"]
    if "belt" in name:
        return ACC_TYPE_MAP["Belts"]
    if "umbrella" in name:
        return ACC_TYPE_MAP["Umbrellas"]
    if "bauble" in name or "ornament" in name:
        return ACC_TYPE_MAP["Novelty Items"]
    if "hand care" in name or "botanist" in name:
        return ACC_TYPE_MAP["Novelty Items"]
    return ("ps-acc-other", "기타 악세서리")


def fallback_size_chart(cat: str, leaf_id: str, name_ko: str) -> dict | None:
    if cat == "shoes" or leaf_id.startswith("ps-shoes-") or leaf_id == "ps-acc-boots":
        return shoe_size_chart()
    if leaf_id == "ps-acc-belts":
        return belt_size_chart()
    if leaf_id == "ps-acc-socks":
        return sock_size_chart()
    if leaf_id == "ps-acc-hats":
        return hat_size_chart()
    if leaf_id == "ps-acc-gloves":
        return glove_size_chart()
    if leaf_id in {
        "ps-acc-underwear",
        "ps-acc-swimwear",
        "ps-acc-pyjamas",
        "ps-men-underwear",
        "ps-men-swimwear",
        "ps-men-loungewear",
        "ps-men-pyjamas",
    }:
        return apparel_alpha_chart(name_ko or "폴 스미스")
    return None


def classify(row: dict) -> tuple[str, str, list[str], str]:
    """Return category, subcategory, psCollections, leaf label."""
    channels = set(row.get("channels") or [])
    entity = row.get("entity") or {}
    plp = row.get("plp") or {}
    title = entity.get("name") or plp.get("title") or ""
    ptype = (
        entity.get("product_type")
        or plp.get("product_type")
        or (entity.get("categoryName") or [None])[-1]
    )
    style = entity.get("style") or plp.get("style")

    cols: list[str] = []
    # Primary channel priority: shoes > accessories > clothing/tailoring
    if "shoes" in channels:
        cat = "shoes"
        if style and str(style) in SHOE_STYLE_MAP:
            leaf_id, leaf_ko = SHOE_STYLE_MAP[str(style)]
        elif ptype and str(ptype) in SHOE_PTYPE_MAP:
            leaf_id, leaf_ko = SHOE_PTYPE_MAP[str(ptype)]
        else:
            leaf_id, leaf_ko = ("ps-shoes-other", "기타 슈즈")
        cols = ["paul-smith-shoes", "ps-shoes-men", leaf_id]
        return cat, leaf_id, cols, leaf_ko

    if "accessories" in channels and "clothing" not in channels and "tailoring" not in channels:
        cat = "accessories"
        leaf_id, leaf_ko = infer_acc_type(str(ptype) if ptype else None, title)
        # Acc "Boots" with UK shoe sizes → treat as shoes leaf under accessories nav still
        cols = ["paul-smith-accessories", "ps-acc-men", leaf_id]
        return cat, leaf_id, cols, leaf_ko

    # clothing / tailoring → luxury
    cat = "luxury"
    cols = ["paul-smith", "ps-men"]
    if "tailoring" in channels:
        cols.append("ps-men-tailoring")
    leaf_id, leaf_ko = CLOTHING_TYPE_MAP.get(str(ptype or ""), ("ps-men-other", "기타 의류"))
    if leaf_id not in cols:
        cols.append(leaf_id)
    # If only tailoring and no clothing type match, use tailoring leaf
    if "tailoring" in channels and "clothing" not in channels and str(ptype or "") not in CLOTHING_TYPE_MAP:
        return cat, "ps-men-tailoring", ["paul-smith", "ps-men", "ps-men-tailoring"], "테일러링"
    return cat, leaf_id, cols, leaf_ko


def variant_in_stock(v: dict) -> bool:
    if "inStock" in v:
        return bool(v.get("inStock"))
    stock = str(v.get("stock") or v.get("stock_status") or "").lower()
    if stock in ("yes", "true", "in_stock", "instock"):
        return True
    if stock in ("no", "false", "out_of_stock", "outofstock"):
        return False
    qty = v.get("quantity") or v.get("stockNumber")
    try:
        return int(qty) > 0
    except Exception:
        return False


def build_variants(row: dict, price: int, compare: int | None, cols: list[str]) -> list[dict]:
    entity = row.get("entity") or {}
    plp = row.get("plp") or {}
    images = row.get("images") or []
    color = entity.get("variantName") or entity.get("detailed_colour_label") or entity.get("colour_group") or "Default"
    color_ko = t(color) if color and color != "Default" else color
    color_key = slugify(color)
    handle = row.get("handle") or row.get("key")
    gbp_sell, gbp_list = price_pair(entity, plp)

    items = entity.get("items") or []
    conf = row.get("configurableOptions") or []
    plp_vars = plp.get("variants") or []

    source = items or conf or plp_vars
    out = []
    for i, raw in enumerate(source):
        if items:
            size = str(raw.get("name") or "")
            vid = str(raw.get("item") or f"{row.get('key')}-{i}")
            sku = str(raw.get("sku") or vid)
            in_stock = variant_in_stock(raw)
            # per-size prices rarely differ; use product price
            v_gbp = gbp_sell
            v_list = gbp_list
        elif conf:
            size = str(raw.get("label") or "")
            vid = str(raw.get("value") or f"{row.get('key')}-{i}")
            sku = str(raw.get("sku") or vid)
            in_stock = variant_in_stock(raw)
            v_gbp, v_list = gbp_sell, gbp_list
        else:
            size = str(raw.get("label") or "")
            vid = str(raw.get("key") or f"{row.get('key')}-{i}")
            sku = vid
            in_stock = variant_in_stock(raw)
            try:
                v_gbp = float(raw.get("sellingPrice") or gbp_sell)
            except Exception:
                v_gbp = gbp_sell
            try:
                v_list = float(raw.get("listPrice") or v_gbp)
            except Exception:
                v_list = v_gbp

        v_price = gbp_to_krw(v_gbp)
        v_compare = gbp_to_krw(v_list) if v_list > v_gbp + 0.01 else None
        out.append(
            {
                "id": f"ps-{slugify(vid)}",
                "name": f"{color} / {size}" if size else color,
                "nameKo": f"{color_ko} / {size}" if size else color_ko,
                "sku": sku,
                "size": size or None,
                "gbpPrice": v_gbp,
                "price": v_price,
                **({"compareAtPrice": v_compare} if v_compare else {}),
                "image": images[0] if images else "/products/ps-pdp/placeholder.jpg",
                "images": images,
                "hoverImage": images[1] if len(images) > 1 else (images[0] if images else None),
                "sourceUrl": row.get("sourceUrl"),
                "inStock": in_stock,
                "colorKey": color_key,
                "colorNameKo": color_ko,
                "psCollections": cols,
            }
        )
    if not out:
        out.append(
            {
                "id": f"ps-{handle}",
                "name": color,
                "nameKo": color_ko,
                "sku": entity.get("sku") or handle,
                "gbpPrice": gbp_sell,
                "price": price,
                **({"compareAtPrice": compare} if compare else {}),
                "image": images[0] if images else "/products/ps-pdp/placeholder.jpg",
                "images": images,
                "hoverImage": images[1] if len(images) > 1 else (images[0] if images else None),
                "sourceUrl": row.get("sourceUrl"),
                "inStock": not bool(row.get("isOutOfStock")),
                "colorKey": color_key,
                "colorNameKo": color_ko,
                "psCollections": cols,
            }
        )
    return out


def story_sections(name_ko: str, body_ko: str, images: list[str], details: list[str]) -> list[dict]:
    sections = []
    if body_ko:
        item = {"titleKo": name_ko, "bodyKo": body_ko}
        if images:
            item["image"] = images[0]
        sections.append(item)
    for i, d in enumerate(details[:4]):
        item = {"titleKo": "디테일", "bodyKo": d}
        if images:
            item["image"] = images[(i + 1) % len(images)]
            if i % 2 == 0:
                item["reverse"] = True
        sections.append(item)
    for img in images[2:6]:
        sections.append(
            {
                "titleKo": "갤러리",
                "bodyKo": f"{name_ko}의 디테일.",
                "image": img,
                "layout": "wide",
            }
        )
    return sections[:10]


def main() -> None:
    if not RAW_PATH.exists():
        raise SystemExit(f"Missing {RAW_PATH} — run scrape-ps-mens.py first")
    raw = json.loads(RAW_PATH.read_text())
    print(f"raw products={len(raw)}")

    batch_start = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)
    blocks: list[str] = []
    accents = ["#1a1a1a", "#2c2c2c", "#3d3d3d", "#111111"]
    count = 0

    items = sorted(raw.values(), key=lambda r: (r.get("plp") or {}).get("title") or "")
    for idx, row in enumerate(items):
        entity = row.get("entity") or {}
        plp = row.get("plp") or {}
        title = entity.get("name") or plp.get("title") or row.get("handle") or row.get("key")
        handle = row.get("handle") or slugify(title)
        images = [u for u in (row.get("images") or []) if u]
        if not images:
            continue

        cat, sub, cols, _leaf_ko = classify(row)
        gbp_sell, gbp_list = price_pair(entity, plp)
        if gbp_sell <= 0:
            continue
        price = gbp_to_krw(gbp_sell)
        compare = gbp_to_krw(gbp_list) if gbp_list > gbp_sell + 0.01 else None

        name_ko = t(title)
        short = entity.get("short_description_text") or entity.get("product_description_text") or ""
        long = entity.get("product_description_text") or short
        desc_ko = t(short or long)
        details = []
        for key in (
            "fit_information_text",
            "material_information_text",
            "care_info_text",
            "size_information_text",
        ):
            val = entity.get(key)
            if val:
                details.append(t(str(val)))

        variants = build_variants(row, price, compare, cols)
        any_stock = any(v.get("inStock") for v in variants)
        # product price = cheapest in-stock else cheapest
        priced = [v for v in variants if v.get("inStock")] or variants
        price = min(v["price"] for v in priced)
        compare_candidates = [v.get("compareAtPrice") for v in priced if v.get("compareAtPrice")]
        compare = min(compare_candidates) if compare_candidates else None
        if compare and compare <= price:
            compare = None

        chart = chart_from_measurement(row.get("measurementChart") or {}, name_ko)
        if not chart:
            chart = fallback_size_chart(cat, sub, name_ko)
        elif cat == "shoes" and not any(
            "발" in h or "foot" in h.lower() or "shoe" in h.lower()
            for h in (chart.get("headers") or [])
        ):
            # Prefer dedicated UK shoe chart when measurement chart is apparel-like
            chart = shoe_size_chart()

        badge = None
        if compare and compare > price:
            badge = "Sale"
        elif entity.get("newProduct"):
            badge = "New"

        registered = (batch_start + timedelta(seconds=idx)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        story = story_sections(name_ko, desc_ko, images, details)
        features = [d for d in details if d][:8]
        tech = [{"labelKo": "특징", "valueKo": f} for f in features[:6]]

        pid = f"ps-{handle}"
        lines = [
            "  {",
            f"    id: {js_str(pid)},",
            f"    name: {js_str(title)},",
            f"    nameKo: {js_str(name_ko)},",
            f'    brand: "폴 스미스",',
            f"    price: {price},",
        ]
        if compare:
            lines.append(f"    compareAtPrice: {compare},")
        lines += [
            f"    category: {js_str(cat)},",
            f"    subcategory: {js_str(sub)},",
            f"    psCollections: {json.dumps(cols, ensure_ascii=False)} as Product[\"psCollections\"],",
            f"    tags: {json.dumps(['paul smith', '폴 스미스', *cols[:6]], ensure_ascii=False)},",
            f"    descriptionKo: {js_str(desc_ko[:1200] if desc_ko else name_ko)},",
            f"    image: {js_str(images[0])},",
            f"    images: {json.dumps(images, ensure_ascii=False)},",
            f"    hoverImage: {js_str(images[1] if len(images) > 1 else images[0])},",
            f"    accent: {js_str(accents[idx % len(accents)])},",
        ]
        if badge:
            lines.append(f"    badge: {js_str(badge)},")
        lines += [
            f"    gbpPrice: {gbp_sell},",
        ]
        if gbp_list > gbp_sell:
            lines.append(f"    gbpListPrice: {gbp_list},")
        lines += [
            f"    sku: {js_str(str(entity.get('sku') or handle))},",
            f"    sourceUrl: {js_str(row.get('sourceUrl') or '')},",
            f"    inStock: {str(any_stock).lower()},",
            f"    registeredAt: {js_str(registered)},",
        ]
        if chart:
            lines.append(f"    sizeChart: {json.dumps(chart, ensure_ascii=False)},")
        if story:
            lines.append(f"    storySections: {json.dumps(story, ensure_ascii=False)},")
        if features:
            lines.append(f"    featuresKo: {json.dumps(features, ensure_ascii=False)},")
        if tech:
            lines.append(f"    techSpecs: {json.dumps(tech, ensure_ascii=False)},")
        # variants
        lines.append("    variants: [")
        for v in variants:
            lines.append("      {")
            for k, val in v.items():
                if val is None:
                    continue
                if k == "psCollections":
                    lines.append(f"        psCollections: {json.dumps(val, ensure_ascii=False)} as ProductVariant[\"psCollections\"],")
                elif isinstance(val, bool):
                    lines.append(f"        {k}: {str(val).lower()},")
                elif isinstance(val, (int, float)):
                    lines.append(f"        {k}: {val},")
                elif isinstance(val, list):
                    lines.append(f"        {k}: {json.dumps(val, ensure_ascii=False)},")
                else:
                    lines.append(f"        {k}: {js_str(str(val))},")
            lines.append("      },")
        lines.append("    ],")
        lines.append("  },")
        blocks.append("\n".join(lines))
        count += 1
        if count % 40 == 0:
            CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2) + "\n")
            print(f"built {count}", flush=True)

    CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2) + "\n")
    out = "\n".join(
        [
            'import type { Product, ProductVariant } from "@/data/products";',
            "",
            "/** Auto-generated Paul Smith mens catalogue — do not edit by hand. */",
            "export const psCatalogProducts: Product[] = [",
            *blocks,
            "];",
            "",
        ]
    )
    OUT_PATH.write_text(out)
    print(f"Wrote {count} products → {OUT_PATH}")


if __name__ == "__main__":
    main()
