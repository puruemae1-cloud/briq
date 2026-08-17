#!/usr/bin/env python3
"""Build bb-catalog.ts from bb-catalog-raw.json (Burberry Women)."""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bb_women_config import primary_category_for_collections  # noqa: E402
from catalog_image_guard import existing_images, image_on_disk  # noqa: E402

RAW_PATH = ROOT / "src/data/bb/bb-catalog-raw.json"
OUT_PATH = ROOT / "src/data/bb/bb-catalog.ts"
OUT_JSON = ROOT / "src/data/bb/bb-catalog.json"
BAK_PATH = ROOT / "src/data/bb/bb-catalog.ts.bak"
TRANSLATE_CACHE = ROOT / "src/data/bb/bb-translate-cache.json"


def _extract_registered_from_ts(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in re.finditer(
        r'\n  \{\n    id: "(bb-[^"]+)"[\s\S]*?\n    registeredAt: "([^"]+)"',
        text,
    ):
        out[m.group(1)] = m.group(2)
    return out


def load_existing_registered() -> dict[str, str]:
    """Keep stable Briq registration times across rebuilds.

    Only match style-level product ids (2-space indent), never variant ids —
    variants sit after `registeredAt` and would otherwise steal the next
    product's timestamp.

    If the live catalogue looks mass-restamped (most styles share one calendar
    day) and `.bak` has an older distribution, prefer bak timestamps so weekly
    sync / translate rebuilds cannot flood homepage "최신등록순" with Burberry.
    """
    from collections import Counter

    from_ts: dict[str, str] = {}
    from_json: dict[str, str] = {}
    from_bak: dict[str, str] = {}

    if OUT_PATH.exists():
        from_ts = _extract_registered_from_ts(OUT_PATH.read_text())
    if OUT_JSON.exists():
        try:
            for p in json.loads(OUT_JSON.read_text()):
                pid = p.get("id")
                reg = p.get("registeredAt")
                if pid and reg:
                    from_json[str(pid)] = str(reg)
        except Exception:
            pass
    if BAK_PATH.exists():
        from_bak = _extract_registered_from_ts(BAK_PATH.read_text())

    live = from_ts or from_json
    if live and from_bak:
        days = Counter(v[:10] for v in live.values())
        top_day, top_n = days.most_common(1)[0]
        if top_n / max(len(live), 1) >= 0.75:
            bak_day = Counter(v[:10] for v in from_bak.values()).most_common(1)[0][0]
            if bak_day < top_day:
                print(
                    f"WARN: mass re-stamp detected ({top_n}/{len(live)} on {top_day}); "
                    f"restoring registeredAt from bak ({bak_day})",
                    flush=True,
                )
                merged = dict(from_bak)
                for pid, reg in live.items():
                    if pid not in merged:
                        merged[pid] = reg  # truly new styles keep live stamp
                return merged

    out = dict(from_ts)
    for pid, reg in from_json.items():
        out.setdefault(pid, reg)
    for pid, reg in from_bak.items():
        out.setdefault(pid, reg)
    return out


def catalog_max_registered(*paths: Path) -> datetime | None:
    times: list[datetime] = []
    for path in paths:
        if not path.exists():
            continue
        # Style-level dates only (same indent as product registeredAt).
        for m in re.finditer(r'\n    registeredAt: "([^"]+)"', path.read_text()):
            try:
                ts = datetime.fromisoformat(m.group(1).replace("Z", "+00:00"))
            except ValueError:
                continue
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            times.append(ts)
    return max(times) if times else None


def briq_registered_at(
    pid: str,
    existing: dict[str, str],
    batch_start: datetime,
    index: int,
) -> str:
    """Existing styles keep their first Briq registration time.

    Brand-new style ids always get timestamps after every known catalogue
    max so homepage / shop `sort=new` rails surface them immediately.
    """
    if pid in existing:
        return existing[pid]
    ts = batch_start + timedelta(seconds=index)
    return ts.strftime("%Y-%m-%dT%H:%M:%S.000Z")


ACCENTS = [
    "#1A2E28",
    "#2C241C",
    "#1A2428",
    "#3A2F28",
    "#24302A",
    "#4A3A32",
    "#2A4038",
    "#1E3A4A",
]

_KO: dict[str, str] = {}
if TRANSLATE_CACHE.exists():
    _KO = json.loads(TRANSLATE_CACHE.read_text())


def t(text: str | None) -> str:
    """Lookup Korean translation with Burberry→버버리 polish."""
    if not text:
        return ""
    s = str(text).strip()
    ko = _KO.get(s, s)
    ko = ko.replace("Burberry", "버버리").replace("버 버리", "버버리")
    return ko


TRENCH_COLLECTION_IDS = frozenset(
    {
        "bb-women-trench-coats",
        "bb-men-trench-coats",
    }
)


def is_trench_product(cols: list[str] | None) -> bool:
    if not cols:
        return False
    return any(c in TRENCH_COLLECTION_IDS for c in cols)


def gbp_to_krw(gbp: float, cols: list[str] | None = None) -> int:
    """Burberry pricing.
    ≤£110: GBP × 2100 × 1.06 + ₩20,000
    >£110: GBP × 2100 × 1.18 × 1.05 + ₩20,000
    Trench coats (>£110): use 1.10 instead of 1.18.
    Round to 천원.
    """
    if gbp is None:
        return 0
    g = float(gbp)
    if g <= 110:
        base = g * 2100 * 1.06 + 20_000
    else:
        markup = 1.10 if is_trench_product(cols) else 1.18
        base = g * 2100 * markup * 1.05 + 20_000
    return int(round(base / 1_000) * 1_000)


KIDS_PRICE_SURCHARGE_KRW = 100_000

# Adult Burberry shoe size charts (mirrors src/data/bb/bb-shoe-size-charts.ts).
BB_MEN_SHOE_SIZE_CHART = {
    "id": "bb-men-shoes",
    "titleKo": "남성 슈즈 사이즈 차트",
    "noteKo": "아래 사이즈표를 참고해 가장 잘 맞는 사이즈를 찾아보세요. Briq 표기 사이즈는 이탈리아(IT) 기준입니다.",
    "headers": ["UK", "IT", "USA", "JP", "KR"],
    "rows": [
        ["5", "39", "6", "25cm", "250mm"],
        ["5.5", "39.5", "6.5", "25.5cm", "255mm"],
        ["6", "40", "7", "26cm", "260mm"],
        ["6.5", "40.5", "7.5", "26.2cm", "262mm"],
        ["7", "41", "8", "26.5cm", "265mm"],
        ["7.5", "41.5", "8.5", "26.7cm", "267mm"],
        ["8", "42", "9", "27cm", "270mm"],
        ["8.5", "42.5", "9.5", "27.5cm", "275mm"],
        ["9", "43", "10", "28cm", "280mm"],
        ["9.5", "43.5", "10.5", "28.2cm", "282mm"],
        ["10", "44", "11", "28.5cm", "285mm"],
        ["10.5", "44.5", "11.5", "28.7cm", "287mm"],
        ["11", "45", "12", "29cm", "290mm"],
        ["11.5", "45.5", "12.5", "29.5cm", "295mm"],
        ["12", "46", "13", "30cm", "300mm"],
    ],
}

BB_WOMEN_SHOE_SIZE_CHART = {
    "id": "bb-women-shoes",
    "titleKo": "여성 슈즈 사이즈 차트",
    "noteKo": "아래 치수를 확인해 사이즈를 선택하세요. Briq 표기 사이즈는 이탈리아(IT) 기준입니다.",
    "headers": ["UK", "IT", "USA", "JP", "KR"],
    "rows": [
        ["2", "35", "5", "22.5cm", "225mm"],
        ["2.5", "35.5", "5.5", "22.8cm", "228mm"],
        ["3", "36", "6", "23cm", "230mm"],
        ["3.5", "36.5", "6.5", "23.5cm", "235mm"],
        ["4", "37", "7", "24cm", "240mm"],
        ["4.5", "37.5", "7.5", "24.2cm", "242mm"],
        ["5", "38", "8", "24.5cm", "245mm"],
        ["5.5", "38.5", "8.5", "24.8cm", "248mm"],
        ["6", "39", "9", "25cm", "250mm"],
        ["6.5", "39.5", "9.5", "25.5cm", "255mm"],
        ["7", "40", "10", "26cm", "260mm"],
        ["7.5", "40.5", "10.5", "26.2cm", "262mm"],
        ["8", "41", "11", "26.5cm", "265mm"],
        ["8.5", "41.5", "11.5", "26.7cm", "267mm"],
        ["9", "42", "12", "27cm", "270mm"],
    ],
}

# Burberry apparel body charts (UK / IT) — coats, trench, jackets, ready-to-wear
BB_WOMEN_APPAREL_UK_CHART = {
    "id": "bb-women-apparel-uk",
    "titleKo": "버버리 여성 의류 사이즈 차트 (UK)",
    "noteKo": "신체 치수(cm) 기준입니다. 트렌치·코트·재킷 등 UK 숫자 사이즈에 해당합니다. 두 사이즈 사이라면 여유 핏은 큰 사이즈를 선택하세요.",
    "headers": ["UK", "가슴", "허리", "엉덩이"],
    "rows": [
        ["02", "78", "59", "85"],
        ["04", "80", "61", "87"],
        ["06", "83", "64", "90"],
        ["08", "86", "67", "93"],
        ["10", "89", "70", "96"],
        ["12", "94", "75", "101"],
        ["14", "99", "80", "106"],
        ["16", "104", "85", "111"],
        ["18", "111", "93", "118"],
        ["20", "116", "98", "123"],
    ],
}

BB_WOMEN_APPAREL_ALPHA_CHART = {
    "id": "bb-women-apparel-alpha",
    "titleKo": "버버리 여성 의류 사이즈 차트 (알파)",
    "noteKo": "신체 치수(cm) 기준입니다. XXS–XXXL 알파 사이즈 상품에 해당합니다.",
    "headers": ["사이즈", "가슴", "허리", "엉덩이"],
    "rows": [
        ["XXS", "78", "59", "85"],
        ["XS", "81", "62", "88"],
        ["S", "86", "67", "93"],
        ["M", "91", "72", "98"],
        ["L", "97", "78", "104"],
        ["XL", "104", "85", "111"],
        ["XXL", "111", "93", "118"],
        ["XXXL", "118", "100", "125"],
    ],
}

BB_MEN_APPAREL_IT_CHART = {
    "id": "bb-men-apparel-it",
    "titleKo": "버버리 남성 의류 사이즈 차트 (IT)",
    "noteKo": "신체 치수(cm) 기준입니다. 트렌치·코트·재킷 등 IT 숫자 사이즈에 해당합니다.",
    "headers": ["IT", "가슴", "허리"],
    "rows": [
        ["44", "88", "76"],
        ["46", "92", "80"],
        ["48", "96", "84"],
        ["50", "100", "88"],
        ["52", "104", "92"],
        ["54", "108", "96"],
        ["56", "112", "100"],
        ["58", "116", "104"],
        ["60", "120", "108"],
    ],
}

BB_MEN_APPAREL_ALPHA_CHART = {
    "id": "bb-men-apparel-alpha",
    "titleKo": "버버리 남성 의류 사이즈 차트 (알파)",
    "noteKo": "신체 치수(cm) 기준입니다. XS–XXXL 알파 사이즈 상품에 해당합니다.",
    "headers": ["사이즈", "가슴", "허리"],
    "rows": [
        ["XS", "88", "76"],
        ["S", "94", "82"],
        ["M", "100", "88"],
        ["L", "106", "94"],
        ["XL", "114", "102"],
        ["XXL", "122", "110"],
        ["XXXL", "130", "118"],
    ],
}

BB_KIDS_APPAREL_CHART = {
    "id": "bb-kids-apparel",
    "titleKo": "버버리 키즈 의류 사이즈 차트",
    "noteKo": "연령·키(cm) 참고 가이드입니다. 상품별 표기 사이즈를 우선하세요.",
    "headers": ["사이즈", "연령", "키(cm)", "가슴"],
    "rows": [
        ["3Y", "3세", "98", "55"],
        ["4Y", "4세", "104", "57"],
        ["6Y", "6세", "116", "61"],
        ["8Y", "8세", "128", "66"],
        ["10Y", "10세", "140", "71"],
        ["12Y", "12세", "152", "76"],
        ["14Y", "14세", "164", "81"],
    ],
}


def is_kids_product(cols: list[str]) -> bool:
    return any(str(c).startswith("bb-kids-") for c in cols)


def apply_kids_surcharge(price: int | None, cols: list[str]) -> int | None:
    if not price:
        return price
    if is_kids_product(cols):
        return int(price) + KIDS_PRICE_SURCHARGE_KRW
    return price


def _is_men_cols(cols: list[str]) -> bool:
    return any(
        str(c).startswith("bb-men")
        or str(c) in {"bb-gifts-him", "bb-scarves-men"}
        for c in cols
    )


def _is_women_cols(cols: list[str]) -> bool:
    return any(
        str(c).startswith("bb-women")
        or str(c) in {"bb-gifts-her", "bb-scarves-women"}
        for c in cols
    )


def size_chart_for_collections(cols: list[str], size_labels: list[str] | None = None) -> dict | None:
    """Pick shoe or apparel size chart for Burberry collections."""
    labels = [str(s).upper() for s in (size_labels or [])]
    numeric_uk = any(re.fullmatch(r"0?\d{1,2}", s) for s in labels)
    numeric_it = any(re.fullmatch(r"4\d|5\d|6\d", s) for s in labels)
    alpha = any(
        s in {"XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL", "3XL", "4XL"}
        for s in labels
    )

    shoe = shoe_size_chart_for_collections(cols)
    if shoe:
        return shoe

    if is_kids_product(cols) or any(str(c).startswith("bb-kids") for c in cols):
        return BB_KIDS_APPAREL_CHART

    # Apparel / trench / coats / ready-to-wear
    apparelish = any(
        any(
            k in str(c)
            for k in (
                "trench",
                "coat",
                "jacket",
                "clothes",
                "dress",
                "knit",
                "trouser",
                "skirt",
                "top",
                "shirt",
                "polo",
                "hoodie",
                "sweat",
                "latest",
                "classics",
                "summer",
                "poncho",
                "cape",
                "outerwear",
                "ready-to-wear",
                "bb-girl",
                "bb-boy",
                "tailoring",
                "quilt",
                "down",
                "parka",
            )
        )
        for c in cols
    ) or bool(labels)

    if not apparelish and not labels:
        return None

    if _is_men_cols(cols) and not _is_women_cols(cols):
        if numeric_it or (not alpha and numeric_uk is False and any("trench" in str(c) or "coat" in str(c) for c in cols)):
            # Men trench/coats are typically IT 44–60
            if numeric_it or any("trench" in str(c) or "coat" in str(c) for c in cols):
                return BB_MEN_APPAREL_IT_CHART
        if alpha or not numeric_it:
            return BB_MEN_APPAREL_ALPHA_CHART
        return BB_MEN_APPAREL_IT_CHART

    # Default women / unisex gifts-her style
    if numeric_uk or any("trench" in str(c) for c in cols):
        return BB_WOMEN_APPAREL_UK_CHART
    if alpha:
        return BB_WOMEN_APPAREL_ALPHA_CHART
    return BB_WOMEN_APPAREL_UK_CHART if _is_women_cols(cols) else BB_MEN_APPAREL_IT_CHART


def shoe_size_chart_for_collections(cols: list[str]) -> dict | None:
    if any(
        c == "bb-men-shoes"
        or str(c).startswith("bb-men-sneakers")
        or str(c).startswith("bb-men-sandals")
        or str(c).startswith("bb-men-boots")
        or str(c).startswith("bb-men-loafers")
        for c in cols
    ):
        return BB_MEN_SHOE_SIZE_CHART
    if any(
        c == "bb-women-shoes"
        or str(c).startswith("bb-women-sneakers")
        or str(c).startswith("bb-women-sandals")
        or str(c).startswith("bb-women-boots")
        or str(c).startswith("bb-women-loafers")
        or str(c).startswith("bb-women-pumps")
        for c in cols
    ):
        return BB_WOMEN_SHOE_SIZE_CHART
    return None


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:80] or "item"


def clean_name(name: str) -> str:
    return (name or "").replace("\u200b", "").strip()


def style_key(product: dict) -> str:
    swatches = product.get("swatches") or []
    ids = sorted({str(s.get("id")) for s in swatches if s.get("id")})
    if len(ids) >= 2:
        return "swatch:" + "-".join(ids)
    # fallback: name without trailing colour hints
    return "name:" + slugify(clean_name(product.get("title") or product.get("id") or ""))


# Exact EN titles / colourway ids removed from Briq (manual merchandising).
EXCLUDED_TITLES = {
    "Wide Check Wool Silk Scarf",
}
EXCLUDED_COLOURWAY_IDS = {
    "80787791",
    "80787821",
    "81101611",
    "81101621",
    "81106531",
    "81124591",
    "81124611",
    "81124621",
    "81124631",
    "81134271",
    "81225811",
    "81225831",
    "81232511",
}
EXCLUDED_STYLE_ID_PREFIXES = (
    "bb-wide-check-wool-silk-scarf",
)


def is_excluded_product(product: dict) -> bool:
    title = clean_name(product.get("title") or "")
    pid = str(product.get("id") or "")
    if title in EXCLUDED_TITLES:
        return True
    if pid in EXCLUDED_COLOURWAY_IDS:
        return True
    return False


def is_excluded_style(product: dict) -> bool:
    pid = str(product.get("id") or "")
    name = clean_name(product.get("name") or "")
    name_ko = clean_name(product.get("nameKo") or "")
    if name in EXCLUDED_TITLES or name_ko == "Wide 체크 울 실크 스카프":
        return True
    return any(pid == p or pid.startswith(p + "-") for p in EXCLUDED_STYLE_ID_PREFIXES)


def ts_str(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)


def emit_product(p: dict) -> str:
    """Serialize one Product object as TS literal."""
    lines = ["  {"]
    for key, val in p.items():
        if val is None:
            continue
        if key in ("ggCollections", "bbCollections", "cwCollections") and isinstance(val, list):
            lines.append(
                f"    {key}: {json.dumps(val)} as Product[\"{key}\"],"
            )
        elif key == "variants" and isinstance(val, list):
            lines.append("    variants: [")
            for v in val:
                lines.append("      {")
                for vk, vv in v.items():
                    if vv is None:
                        continue
                    if vk == "bbCollections" and isinstance(vv, list):
                        lines.append(
                            f"        bbCollections: {json.dumps(vv)} as Product[\"bbCollections\"],"
                        )
                    elif isinstance(vv, str):
                        lines.append(f"        {vk}: {json.dumps(vv, ensure_ascii=False)},")
                    elif isinstance(vv, bool):
                        lines.append(f"        {vk}: {'true' if vv else 'false'},")
                    elif isinstance(vv, float):
                        lines.append(f"        {vk}: {vv},")
                    elif isinstance(vv, int):
                        lines.append(f"        {vk}: {vv},")
                    elif isinstance(vv, list):
                        lines.append(f"        {vk}: {json.dumps(vv, ensure_ascii=False)},")
                    else:
                        lines.append(f"        {vk}: {json.dumps(vv, ensure_ascii=False)},")
                lines.append("      },")
            lines.append("    ],")
        elif key == "storySections" and isinstance(val, list):
            lines.append(f"    storySections: {json.dumps(val, ensure_ascii=False)},")
        elif key == "featuresKo" and isinstance(val, list):
            lines.append(f"    featuresKo: {json.dumps(val, ensure_ascii=False)},")
        elif key == "techSpecs" and isinstance(val, list):
            lines.append(f"    techSpecs: {json.dumps(val, ensure_ascii=False)},")
        elif key == "tags" and isinstance(val, list):
            lines.append(f"    tags: {json.dumps(val, ensure_ascii=False)},")
        elif key == "images" and isinstance(val, list):
            lines.append(f"    images: {json.dumps(val, ensure_ascii=False)},")
        elif isinstance(val, str):
            lines.append(f"    {key}: {json.dumps(val, ensure_ascii=False)},")
        elif isinstance(val, bool):
            lines.append(f"    {key}: {'true' if val else 'false'},")
        elif isinstance(val, float):
            lines.append(f"    {key}: {val},")
        elif isinstance(val, int):
            lines.append(f"    {key}: {val},")
        else:
            lines.append(f"    {key}: {json.dumps(val, ensure_ascii=False)},")
    lines.append("  }")
    return "\n".join(lines)


def description_parts(product: dict) -> tuple[str, list[str], list[dict]]:
    desc = product.get("description") or ""
    parts = [p.strip() for p in desc.split("##") if p.strip()]
    body = t(parts[0]) if parts else ""
    features = [t(p) for p in parts[1:]] if len(parts) > 1 else []
    for acc in product.get("accordion") or []:
        label = acc.get("label") or ""
        texts = [x for x in (acc.get("texts") or []) if x]
        if label.lower() == "product details" and texts:
            if not body:
                body = t(texts[0])
            for x in texts[1:]:
                if x.lower().startswith("item "):
                    continue
                tx = t(x)
                if tx and tx not in features:
                    features.append(tx)
        elif texts:
            for x in texts:
                tx = t(x)
                if tx and tx not in features:
                    features.append(tx)
    tech = []
    if product.get("measurements"):
        tech.append({"labelKo": "사이즈 · 핏", "valueKo": t(str(product["measurements"]))})
    if product.get("materialComposition"):
        mat = t(str(product["materialComposition"]).replace(" #", " · "))
        tech.append({"labelKo": "소재", "valueKo": mat})
    return body, features[:16], tech


def main() -> None:
    raw = json.loads(RAW_PATH.read_text())
    products = [
        p for p in (raw.get("products") or []) if not is_excluded_product(p)
    ]

    groups: dict[str, list[dict]] = defaultdict(list)
    for p in products:
        groups[style_key(p)].append(p)

    briq: list[dict] = []
    existing_reg = load_existing_registered()
    peer_max = catalog_max_registered(
        OUT_PATH,
        ROOT / "src/data/cw/cw-catalog.ts",
        ROOT / "src/data/gg/gg-catalog.ts",
    )
    batch_start = datetime.now(timezone.utc)
    if peer_max and batch_start <= peer_max:
        # New BB styles must sort after every existing Briq registration
        # (BB + CW/GG) so homepage luxury / 신상품 rails stay newest-first.
        batch_start = peer_max + timedelta(seconds=1)
    new_index = 0

    for gkey, colourways in groups.items():

        colourways = sorted(colourways, key=lambda x: x.get("id") or "")
        all_cols: set[str] = set()
        for c in colourways:
            all_cols.update(c.get("collections") or [])
        cols_sorted = sorted(all_cols)

        primary = colourways[0]
        name_en = clean_name(primary.get("title") or "Burberry")
        # Prefer longest title
        for c in colourways:
            x = clean_name(c.get("title") or "")
            if len(x) > len(name_en):
                name_en = x
        name_ko = t(name_en) or name_en
        if (
            name_en in EXCLUDED_TITLES
            or name_ko == "Wide 체크 울 실크 스카프"
            or any(str(c.get("id")) in EXCLUDED_COLOURWAY_IDS for c in colourways)
        ):
            continue
        top_cat, primary_sub = primary_category_for_collections(
            cols_sorted, name_en
        )

        style_slug = slugify(name_en) or (primary.get("id") or "item")
        pid = f"bb-{style_slug}"
        # ensure unique product ids
        existing = {p["id"] for p in briq}
        base_pid = pid
        n = 2
        while pid in existing:
            pid = f"{base_pid}-{n}"
            n += 1

        flat_variants = []
        gallery_all: list[str] = []
        prices_krw = []
        body, features, tech = description_parts(primary)
        # merge accordion features from all colours lightly
        for c in colourways[1:]:
            _, feat2, tech2 = description_parts(c)
            for f in feat2:
                if f not in features:
                    features.append(f)
            if not tech:
                tech = tech2

        for c in colourways:
            color = c.get("color") or "Default"
            color_ko = t(color) or color
            color_key = slugify(color) or c.get("id")
            color_cols = sorted(set(c.get("collections") or cols_sorted))
            local_imgs = existing_images(list(c.get("images") or []))
            if not local_imgs and c.get("image") and str(c["image"]).startswith("/"):
                local_imgs = existing_images([c["image"]])
            if not local_imgs:
                continue
            for img in local_imgs:
                if img and img not in gallery_all:
                    gallery_all.append(img)
            lead_img = local_imgs[0]
            gbp = float(c.get("gbpPrice") or 0)
            gbp_list = c.get("gbpListPrice")
            price = gbp_to_krw(gbp, color_cols) if gbp else 0
            compare = (
                gbp_to_krw(float(gbp_list), color_cols)
                if gbp_list and float(gbp_list) > gbp
                else None
            )
            price = apply_kids_surcharge(price, color_cols) or 0
            compare = apply_kids_surcharge(compare, color_cols)
            if price:
                prices_krw.append(price)

            sizes = c.get("sizes") or []
            if not sizes:
                sizes = [
                    {
                        "sku": c.get("id"),
                        "label": "One size",
                        "isInStock": True,
                    }
                ]

            source = c.get("url") or ""
            for sz in sizes:
                label = str(sz.get("label") or "One size")
                label_ko = "프리사이즈" if label.lower() in ("one size", "onesize", "os") else label
                sku = str(sz.get("sku") or f"{c.get('id')}-{label}")
                in_stock = bool(sz.get("isInStock"))
                flat_variants.append(
                    {
                        "id": f"bb-{c.get('id')}-{slugify(label)}",
                        "name": f"{color} / {label}",
                        "nameKo": f"{color_ko} / {label_ko}",
                        "sku": sku,
                        "gbpPrice": gbp,
                        "price": price,
                        "compareAtPrice": compare,
                        "image": lead_img,
                        "images": local_imgs[:6] or None,
                        "hoverImage": local_imgs[1] if len(local_imgs) > 1 else None,
                        "sourceUrl": source,
                        "inStock": in_stock,
                        "colorKey": color_key,
                        "colorNameKo": color_ko,
                        "size": label_ko if label_ko == "프리사이즈" else label,
                        "bbCollections": color_cols,
                    }
                )

        in_stock_prices = [v["price"] for v in flat_variants if v.get("inStock") and v["price"]]
        price = min(in_stock_prices) if in_stock_prices else (min(prices_krw) if prices_krw else 0)
        gbp_price = None
        for v in flat_variants:
            if v.get("inStock") and v["price"] == price:
                gbp_price = v["gbpPrice"]
                break
        if gbp_price is None and flat_variants:
            gbp_price = min(v["gbpPrice"] for v in flat_variants if v.get("gbpPrice"))

        compare_at = None
        for v in flat_variants:
            if v["price"] != price:
                continue
            cap = v.get("compareAtPrice")
            if cap and cap > price:
                compare_at = cap
                break

        gallery_all = existing_images(gallery_all)
        if not gallery_all or not flat_variants:
            print(f"skip no local image: {pid}", flush=True)
            continue

        primary_image = gallery_all[0]
        badge = "New" if any(x.get("label") == "New In" for x in colourways) else None
        if "bb-women-new" in cols_sorted:
            badge = badge or "New"

        story = []
        if body:
            story.append(
                {
                    "titleKo": name_ko,
                    "bodyKo": body,
                    "image": primary_image,
                }
            )
        if features:
            story.append(
                {
                    "titleKo": "디테일",
                    "bodyKo": " · ".join(features[:8]),
                    "image": gallery_all[1] if len(gallery_all) > 1 else primary_image,
                    "reverse": True,
                }
            )

        briq.append(
            {
                "id": pid,
                "name": name_en,
                "nameKo": name_ko,
                "brand": "버버리",
                "price": price,
                "compareAtPrice": compare_at,
                "category": top_cat,
                "subcategory": primary_sub,
                "bbCollections": cols_sorted,
                "tags": ["burberry", "버버리", "bb-women", *cols_sorted],
                "descriptionKo": body[:1500] if body else None,
                "image": primary_image,
                "images": gallery_all[:12] or None,
                "hoverImage": gallery_all[1] if len(gallery_all) > 1 else None,
                "accent": ACCENTS[len(briq) % len(ACCENTS)],
                "badge": badge,
                "gbpPrice": gbp_price,
                "sku": flat_variants[0]["sku"] if flat_variants else primary.get("id"),
                "sourceUrl": primary.get("url") or flat_variants[0].get("sourceUrl"),
                "registeredAt": briq_registered_at(
                    pid, existing_reg, batch_start, new_index
                ),
                "editTier": "new" if badge == "New" else "signature",

                "storySections": story or None,
                "featuresKo": features or None,
                "techSpecs": tech or None,
                "sizeChart": size_chart_for_collections(
                    cols_sorted,
                    [
                        str(v.get("size") or "")
                        for v in flat_variants
                        if v.get("size") and v.get("size") != "프리사이즈"
                    ],
                ),
                "variants": flat_variants,
                "inStock": any(v.get("inStock") for v in flat_variants),
            }
        )
        if pid not in existing_reg:
            new_index += 1

    # Stable-ish order: luxury apparel first, then bags, shoes, accessories
    top_order = {"luxury": 0, "bags": 1, "shoes": 2, "accessories": 3}

    def sort_key(p: dict):
        return (top_order.get(p["category"], 9), p["name"].lower(), p["id"])

    briq.sort(key=sort_key)

    chunks = [emit_product(p) for p in briq]
    out = (
        "/** Auto-generated Burberry catalogue — do not edit by hand. */\n"
        'import type { Product } from "@/data/products";\n\n'
        "export const bbCatalogProducts = [\n"
        + ",\n".join(chunks)
        + "\n] as unknown as Product[];\n"
    )
    OUT_PATH.write_text(out)
    OUT_JSON.write_text(json.dumps(briq, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {OUT_PATH} styles={len(briq)} colourways={len(products)}")
    print(f"Wrote {OUT_JSON}", flush=True)


if __name__ == "__main__":
    main()
