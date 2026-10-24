#!/usr/bin/env python3
"""Build bb-catalog.ts from bb-catalog-raw.json (Burberry Women)."""
from __future__ import annotations

from briq_pricing import apply_site_price  # noqa: E402

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
    return apply_site_price(int(round(base / 1_000) * 1_000))
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

# Official Burberry body charts (uk.burberry.com size-guide, centimetres).
# Coats, dresses, jackets and tops share one women's UK table that starts at 0.
# Do not replace these with the older 02–20 table.
BB_WOMEN_APPAREL_UK_CHART = {
    "id": "bb-women-apparel-uk",
    "titleKo": "버버리 여성 의류 사이즈 차트 (UK)",
    "noteKo": "영국 공식 사이즈 가이드의 신체 치수(cm)입니다. UK 0부터 18까지입니다. 두 사이즈 사이라면 여유 핏은 큰 사이즈를 선택하세요.",
    "headers": ["UK", "가슴", "허리", "엉덩이"],
    "rows": [
        ["0", "72", "55", "80"],
        ["02", "74", "57", "82"],
        ["04", "76", "59", "84"],
        ["06", "80", "63", "88"],
        ["08", "84", "67", "92"],
        ["10", "88", "71", "96"],
        ["12", "92", "75", "100"],
        ["14", "97", "80", "105"],
        ["16", "102", "85", "110"],
        ["18", "107", "90", "115"],
    ],
}

BB_WOMEN_APPAREL_ALPHA_CHART = {
    "id": "bb-women-apparel-alpha",
    "titleKo": "버버리 여성 의류 사이즈 차트 (알파)",
    "noteKo": "영국 공식 사이즈 가이드의 신체 치수(cm)입니다. XXXS–XXXL 알파 사이즈에 해당합니다.",
    "headers": ["사이즈", "가슴", "허리", "엉덩이"],
    "rows": [
        ["XXXS", "66", "49", "74"],
        ["XXS", "72", "55", "80"],
        ["XS", "78", "61", "86"],
        ["S", "84", "67", "92"],
        ["M", "90", "73", "98"],
        ["L", "96", "79", "104"],
        ["XL", "102", "85", "110"],
        ["XXL", "108", "91", "116"],
        ["XXXL", "114", "97", "122"],
    ],
}

BB_MEN_APPAREL_IT_CHART = {
    "id": "bb-men-apparel-it",
    "titleKo": "버버리 남성 의류 사이즈 차트 (IT)",
    "noteKo": "영국 공식 사이즈 가이드의 신체 치수(cm)입니다. 재킷·코트 IT 42–60에 해당합니다.",
    "headers": ["IT", "가슴", "허리", "엉덩이"],
    "rows": [
        ["42", "86", "71", "85"],
        ["44", "90", "75", "89"],
        ["46", "94", "79", "93"],
        ["48", "98", "83", "97"],
        ["50", "102", "87", "101"],
        ["52", "106", "91", "105"],
        ["54", "110", "95", "109"],
        ["56", "114", "99", "113"],
        ["58", "118", "103", "117"],
        ["60", "122", "107", "121"],
    ],
}

BB_MEN_APPAREL_ALPHA_CHART = {
    "id": "bb-men-apparel-alpha",
    "titleKo": "버버리 남성 의류 사이즈 차트 (알파)",
    "noteKo": "영국 공식 사이즈 가이드의 신체 치수(cm)입니다. XXXS–XXXL 알파 사이즈에 해당합니다.",
    "headers": ["사이즈", "가슴", "허리", "엉덩이"],
    "rows": [
        ["XXXS", "74", "59", "73"],
        ["XXS", "80", "65", "79"],
        ["XS", "86", "71", "85"],
        ["S", "92", "77", "91"],
        ["M", "98", "83", "97"],
        ["L", "104", "89", "103"],
        ["XL", "110", "95", "109"],
        ["XXL", "116", "101", "115"],
        ["XXXL", "122", "107", "121"],
    ],
}

BB_KIDS_APPAREL_CHART = {
    "id": "bb-kids-apparel",
    "titleKo": "버버리 키즈 의류 사이즈 차트",
    "noteKo": "영국 공식 키즈 의류 가이드의 키·가슴·허리(cm)입니다. 개월 사이즈는 공식 가이드에 치수가 없습니다.",
    "headers": ["사이즈", "키", "가슴", "허리"],
    "rows": [
        ["3Y", "98", "54.5", "52.5"],
        ["4Y", "104", "56", "54.5"],
        ["5Y", "110", "58", "55"],
        ["6Y", "116", "60.5", "56"],
        ["7Y", "122", "63", "57"],
        ["8Y", "128", "64", "59"],
        ["10Y", "140", "71", "63.5"],
        ["12Y", "152", "78", "68"],
        ["14Y", "164", "86", "73"],
        ["S", "86 - 92", "51 - 52", "49.75 - 50.5"],
        ["M", "98 - 116", "54.5 - 60.5", "52.5 - 59"],
        ["L", "128 - 164", "64 - 86", "59 - 73"],
    ],
}

BB_MEN_JEANS_CHART = {
    "id": "bb-men-jeans",
    "titleKo": "버버리 남성 진 사이즈 차트",
    "noteKo": "영국 공식 진 가이드의 허리·엉덩이(cm)입니다. 사이즈 숫자는 허리 표기입니다.",
    "headers": ["사이즈", "허리", "엉덩이"],
    "rows": [
        ["28", "71", "85"],
        ["29", "73.5", "87.5"],
        ["30", "76", "90"],
        ["31", "78.5", "92.5"],
        ["32", "81", "95"],
        ["33", "83.5", "97.5"],
        ["34", "86", "100"],
        ["35", "88.5", "102.5"],
        ["36", "91", "105"],
        ["38", "96", "110"],
        ["40", "101", "115"],
        ["42", "106", "120"],
    ],
}

BB_MEN_BELT_CHART = {
    "id": "bb-men-belts",
    "titleKo": "버버리 남성 벨트 사이즈 차트",
    "noteKo": "영국 공식 벨트 가이드의 길이(cm)입니다.",
    "headers": ["사이즈", "길이"],
    "rows": [
        ["75", "75cm"],
        ["80", "80cm"],
        ["85", "85cm"],
        ["90", "90cm"],
        ["95", "95cm"],
        ["100", "100cm"],
        ["105", "105cm"],
        ["115", "115cm"],
        ["120", "120cm"],
    ],
}

_UK_APPAREL = {"0", "00", "02", "04", "06", "08", "10", "12", "14", "16", "18", "20"}
_IT_APPAREL = {"42", "44", "46", "48", "50", "52", "54", "56", "58", "60"}
_ALPHA = {"XXXS", "XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL", "XXXXL", "3XL", "4XL"}
_BELT = {"65", "70", "75", "80", "85", "90", "95", "100", "105", "110", "115", "120"}


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


def _bb_size_sort_key(size: str) -> tuple:
    """Match src/lib/ax-size-order.ts — XXXS first, then XXS…XL."""
    letter = {
        "XXXS": 0,
        "XXS": 1,
        "XS": 2,
        "S": 3,
        "M": 4,
        "L": 5,
        "XL": 6,
        "XXL": 7,
        "2XL": 7,
        "XXXL": 8,
        "3XL": 8,
        "4XL": 9,
        "5XL": 10,
        "OS": 11,
        "ONE SIZE": 11,
        "프리사이즈": 11,
    }
    s = (size or "").strip()
    u = s.upper()
    if u in letter:
        return (0, letter[u], s)
    try:
        return (1, float(s.replace(",", ".")), s)
    except ValueError:
        return (2, 0.0, s.lower())


def one_size_chart(measurements: str | None) -> dict | None:
    """One-size styles (capes, ponchos …) get the official flat measurements
    instead of a body-size chart that has no matching size chip."""
    m = re.match(
        r"\s*([\d.]+)\s*x\s*([\d.]+)\s*cm\s*/\s*([\d.]+)\.?\s*x\s*([\d.]+)\s*in",
        str(measurements or ""),
        re.I,
    )
    if not m:
        return None
    w_cm, h_cm, w_in, h_in = (g.rstrip(".") for g in m.groups())
    return {
        "id": "bb-one-size-measurements",
        "titleKo": "버버리 원사이즈 제품 실측",
        "noteKo": "공식 제품 실측(가로 × 세로) 기준입니다. 원사이즈 단일 옵션으로 판매됩니다.",
        "headers": ["사이즈", "가로 × 세로 (cm)", "가로 × 세로 (inch)"],
        "rows": [["프리사이즈", f"{w_cm} × {h_cm}", f"{w_in} × {h_in}"]],
    }


def _chart_labels(size_labels: list[str] | None) -> list[str]:
    return [
        str(s).strip()
        for s in (size_labels or [])
        if str(s).strip() and str(s).strip() != "프리사이즈"
    ]


def _tabbed_chart(chart_id: str, title: str, note: str, tabs: list[dict]) -> dict:
    first = tabs[0]
    return {
        "id": chart_id,
        "titleKo": title,
        "noteKo": note,
        "headers": first["headers"],
        "rows": first["rows"],
        "tabs": tabs,
    }


def _is_waist_jeans(labels: list[str]) -> bool:
    """Waist-labelled denim (24–42), not UK 02–18 and not a dress-shirt collar."""
    if any(s in _UK_APPAREL for s in labels):
        return False
    nums = []
    for s in labels:
        if not re.fullmatch(r"\d{2}", s):
            return False
        nums.append(int(s))
    if len(nums) < 4 or min(nums) > 32 or max(nums) > 42:
        return False
    return True


def size_chart_for_collections(cols: list[str], size_labels: list[str] | None = None) -> dict | None:
    """Pick the official Burberry chart that matches the sizes actually sold."""
    labels = _chart_labels(size_labels)
    upper = [s.upper() for s in labels]
    shoe = shoe_size_chart_for_collections(cols)
    if shoe:
        return shoe

    if labels and all(s in _BELT for s in labels):
        return BB_MEN_BELT_CHART

    uk = [s for s in labels if s in _UK_APPAREL]
    it = [s for s in labels if s in _IT_APPAREL]
    alpha = [s for s in upper if s in _ALPHA]
    kids_labels = [s for s in upper if re.fullmatch(r"\d+[MY]", s)]
    men_only = _is_men_cols(cols) and not _is_women_cols(cols)
    kids_product = is_kids_product(cols)

    if _is_waist_jeans(labels) and men_only:
        return BB_MEN_JEANS_CHART

    include_kids = len(kids_labels) >= 2 and (
        kids_product or len(kids_labels) >= max(1, len(labels) / 2)
    )
    sections: list[tuple[str, str, dict]] = []
    if len(uk) >= 2:
        sections.append(("uk", "UK", BB_WOMEN_APPAREL_UK_CHART))
    if len(it) >= 2:
        sections.append(("it", "IT", BB_MEN_APPAREL_IT_CHART))
    if len(alpha) >= 2 and not include_kids:
        sections.append(
            (
                "alpha",
                "알파",
                BB_MEN_APPAREL_ALPHA_CHART if men_only else BB_WOMEN_APPAREL_ALPHA_CHART,
            )
        )
    if include_kids:
        sections.append(("kids", "키즈", BB_KIDS_APPAREL_CHART))

    if len(sections) >= 2:
        return _tabbed_chart(
            "bb-apparel-" + "-".join(key for key, _, _ in sections),
            "버버리 의류 사이즈 차트",
            "영국 공식 사이즈 가이드의 신체 치수(cm)입니다. 판매 중인 사이즈 체계를 나눠 두었습니다.",
            [
                {
                    "id": key,
                    "labelKo": label,
                    "headers": chart["headers"],
                    "rows": chart["rows"],
                }
                for key, label, chart in sections
            ],
        )
    if len(sections) == 1:
        return sections[0][2]
    if kids_product and kids_labels:
        return BB_KIDS_APPAREL_CHART
    return None


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
                        "isInStock": False,
                    }
                ]

            source = c.get("url") or ""
            color_variants = []
            for sz in sizes:
                label = str(sz.get("label") or "One size")
                label_ko = "프리사이즈" if label.lower() in ("one size", "onesize", "os") else label
                sku = str(sz.get("sku") or f"{c.get('id')}-{label}")
                in_stock = bool(sz.get("isInStock"))
                color_variants.append(
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
            # Smallest → largest (XXXS before XXS …), matching PDP chip order.
            color_variants.sort(key=lambda v: _bb_size_sort_key(str(v.get("size") or "")))
            flat_variants.extend(color_variants)

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
                "sizeChart": (
                    size_chart_for_collections(
                        cols_sorted,
                        [
                            str(v.get("size") or "")
                            for v in flat_variants
                            if v.get("size") and v.get("size") != "프리사이즈"
                        ],
                    )
                    if any(v.get("size") != "프리사이즈" for v in flat_variants)
                    else one_size_chart(primary.get("measurements"))
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
    OUT_PATH.write_text(
        "/** Auto-generated Burberry catalogue — do not edit by hand. */\n"
        'import type { Product } from "@/data/products";\n'
        'import data from "./bb-catalog.json";\n\n'
        "export const bbCatalogProducts = data as unknown as Product[];\n"
    )
    OUT_JSON.write_text(json.dumps(briq, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {OUT_PATH} styles={len(briq)} colourways={len(products)}")
    print(f"Wrote {OUT_JSON}", flush=True)


if __name__ == "__main__":
    main()
