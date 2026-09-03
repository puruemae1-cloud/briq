#!/usr/bin/env python3
"""Rebuild cw-catalog.ts from raw (+ optional enriched) with KO names, rounded prices, variants, stories."""
from __future__ import annotations

import json, re, html as H
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = json.loads((ROOT / "src/data/cw/cw-catalog-raw.json").read_text())
RAW_BY_SKU = {p["sku"]: p for p in RAW["products"] if p.get("sku")}
ENR_PATH = ROOT / "src/data/cw/cw-pdp-enriched.json"
ENR = json.loads(ENR_PATH.read_text())["products"] if ENR_PATH.exists() else {}
ED_PATH = ROOT / "src/data/cw/cw-editorial.json"
ED_MODELS = json.loads(ED_PATH.read_text()).get("models") if ED_PATH.exists() else {}


def model_key_from_url(url: str) -> str | None:
    if not url:
        return None
    path = re.sub(r"[?#].*$", "", url)
    parts = [p for p in path.strip("/").split("/") if p]
    if len(parts) >= 2 and parts[-1].endswith(".html"):
        return parts[-2]
    if parts:
        return parts[-1].replace(".html", "")
    return None

PHRASES = [
    (r"Black Shadow", "블랙 섀도우"),
    (r"Sapphire Edge", "사파이어 엣지"),
    (r"Super Compressor", "슈퍼 컴프레서"),
    (r"Pic'?n'?Mix", "픽앤믹스"),
    (r"Bel Canto", "벨 칸토"),
    (r"Jump Hour", "점프아워"),
    (r"Cranwell", "크랜웰"),
    (r"Dune Aeolian", "듄 에올리안"),
    (r"Full Lume", "풀 룸"),
    (r"Nearly New", "니얼리 뉴"),
    (r"Fine Italian", "파인 이탈리안"),
    (r"Light Blue", "라이트 블루"),
]
WORDS = [
    ("Trident", "트라이던트"),
    ("Bronze", "브론즈"),
    ("Sealander", "실랜더"),
    ("Twelve", "트웰브"),
    ("Moonphase", "문페이즈"),
    ("Aquitaine", "아키텐"),
    ("Sandhurst", "샌드허스트"),
    ("Atoll", "아톨"),
    ("Lumière", "뤼미에르"),
    ("Lumiere", "뤼미에르"),
    ("Reef", "리프"),
    ("Pro", "프로"),
    ("Automatic", "오토매틱"),
    ("Chronograph", "크로노그래프"),
    ("Classic", "클래식"),
    ("Extreme", "익스트림"),
    ("Series", "시리즈"),
    ("Titanium", "티타늄"),
    ("Ceramic", "세라믹"),
    ("Skeleton", "스켈레톤"),
    ("Limited", "리미티드"),
    ("Edition", "에디션"),
    ("Steel", "스틸"),
    ("Bracelet", "브레이슬릿"),
    ("Leather", "가죽"),
    ("Rubber", "러버"),
    ("Strap", "스트랩"),
    ("Hybrid", "하이브리드"),
    ("Aquaflex", "아쿠아플렉스"),
    ("Consort", "콘소트"),
    ("Bader", "베이더"),
    ("Vintage", "빈티지"),
    ("Oak", "오크"),
    ("Camel", "카멜"),
    ("Tobacco", "토바코"),
    ("Brown", "브라운"),
    ("Sand", "샌드"),
    ("Dawn", "던"),
    ("Dusk", "더스크"),
    ("Noon", "눈"),
    ("Black", "블랙"),
    ("White", "화이트"),
    ("Blue", "블루"),
    ("Green", "그린"),
    ("Orange", "오렌지"),
    ("Silver", "실버"),
    ("Gold", "골드"),
    ("Grey", "그레이"),
    ("Gray", "그레이"),
    ("Red", "레드"),
    ("Sky", "스카이"),
    ("Tide", "타이드"),
    ("Mulberry", "멀베리"),
    ("Pistachio", "피스타치오"),
    ("Alabaster", "알라바스터"),
    ("Light", "라이트"),
]

SPEC_LABELS = {
    "Watch Model": "모델",
    "Size": "사이즈",
    "Dial Colour": "다이얼 컬러",
    "Case Material": "케이스 소재",
    "Case Colour": "케이스 컬러",
    "Bezel Colour": "베젤 컬러",
    "Height": "두께",
    "Lug-to-Lug": "러그 투 러그",
    "Case Weight": "케이스 무게",
    "Weight inc. Strap": "스트랩 포함 무게",
    "Water Resistance": "방수",
    "Movement": "무브먼트",
    "Power Reserve": "파워리저브",
    "No of Jewels": "주얼 수",
    "Complication Type": "컴플리케이션",
    "Vibrations": "진동수",
    "Timing Tolerance": "일오차",
    "Lume": "루메",
    "Strap SKU": "스트랩 SKU",
    "Strap Material": "스트랩 소재",
    "Strap Colour": "스트랩 컬러",
    "Colour": "컬러",
    "Range": "라인",
}


def to_ko(s: str) -> str:
    if not s:
        return ""
    for a, b in PHRASES:
        s = re.sub(a, b, s, flags=re.I)
    for a, b in WORDS:
        s = re.sub(rf"\b{re.escape(a)}\b", b, s)
    s = re.sub(r"\bThe\b", "", s)
    return re.sub(r"\s{2,}", " ", s).strip(" ·")


def clean_sub(s: str) -> str:
    if not s:
        return ""
    s = H.unescape(s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"main-attributes[^ ]*", " ", s)
    toks = re.findall(r"\d+mm|[A-Za-z][A-Za-z0-9][A-Za-z0-9 /&'\-\.]{0,40}", s)
    out, seen = [], set()
    for t in toks:
        t = t.strip(" .")
        k = t.lower()
        if len(t) < 2 or k in seen or "attribute" in k:
            continue
        seen.add(k)
        out.append(t)
    return " · ".join(out[:5])


def round_krw(gbp: float) -> int:
    return int(round((gbp * 2100 * 1.05 + 200_000) / 10_000) * 10_000)


def slugify(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()


def is_full_sku(sku: str) -> bool:
    return bool(sku) and sku.count("-") >= 2 and len(sku) > 10


def case_size_from_sku(sku: str) -> str | None:
    """Extract case diameter from CW SKU middle token (e.g. 36ADA4 → 36mm)."""
    parts = (sku or "").split("-")
    if len(parts) < 2:
        return None
    m = re.match(r"^(\d{2,3})[A-Z0-9]+$", parts[1], re.I)
    return f"{m.group(1)}mm" if m else None


def dial_family_key(sku: str, line: str) -> str:
    """
    Group strap sisters across case sizes.
    4-part: C63-36ADA4-S00B0-B0 + C63-39ADA4-S00B0-RK → new|C63|ADA4|S00B0
    3-part: C60-41A3H31S0BB0-B0 + C60-44A3H31S0BB0-RK → new|C60|A3H31S0BB0
    (leading case-diameter digits stripped from the model token).
    """
    parts = (sku or "").split("-")
    if len(parts) < 2:
        return f"{line}|{sku}"
    model = parts[1]
    m = re.match(r"^(\d{2,3})([A-Z0-9]+)$", model, re.I)
    model_code = m.group(2).upper() if m else model.upper()
    prefix = parts[0].upper()
    if len(parts) >= 4:
        dial = parts[2].upper()
        return f"{line}|{prefix}|{model_code}|{dial}"
    # 3-part SKUs embed dial in the middle token; last token is strap only.
    return f"{line}|{prefix}|{model_code}"


def cw_model_group_key(url: str) -> str | None:
    """
    For CW model landing pages (e.g. /trident-biscay-gmt/C642.html), use
    the parent slug + short model code so 39/42 + strap SKUs are grouped.
    """
    if not url:
        return None
    path = re.sub(r"[?#].*$", "", url).strip("/")
    parts = [p for p in path.split("/") if p]
    if len(parts) < 2:
        return None
    tail = parts[-1].replace(".html", "")
    parent = parts[-2].lower()
    # Model pages look like C640/C641/C642; SKU pages look like full C60-... codes.
    if re.fullmatch(r"[A-Z]\d{3,5}", tail, re.I):
        return f"{parent}|{tail.upper()}"
    return None


def strap_color_key(sku: str) -> str:
    """Stable option key across case sizes (dial + strap tokens when present)."""
    parts = (sku or "").split("-")
    if len(parts) >= 4:
        return slugify(f"{parts[2]}-{parts[-1]}")
    return slugify(parts[-1] if parts else sku)


STRAP_SUFFIX_LABELS = {
    "B0": "Bader Bracelet",
    "B0R": "Bader Bracelet",
    "B1": "Consort Bracelet",
    "B1R": "Consort Bracelet",
    "HB": "Blue Hybrid Rubber",
    "HV": "Khaki Hybrid Rubber",
    "HK": "Black Hybrid Rubber",
    "VT1": "Tan Vintage Oak Leather",
    "RB": "Blue Rubber Strap",
    "RW": "White Rubber Strap",
    "RK": "Black Rubber Strap",
    "RO": "Orange Rubber Strap",
    "RG": "Green Rubber Strap",
    "RY": "Yellow Rubber Strap",
    "RLB": "Light Blue Rubber Strap",
    "RV": "Green Rubber Strap",
}

DIAL_CODE_LABELS = {
    "S0BW0": "Sand/Blue",
    "S0RK0": "Black/Red",
    "S0KK0": "Black",
    "S0KW0": "Black/White",
    "B0KK0": "Bronze/Black",
    "B0VV0": "Bronze/Green",
}


def strap_label_from_sku(sku: str, enrich: dict | None = None) -> str:
    en = enrich or {}
    if en.get("strap") and isinstance(en.get("strap"), str):
        return en["strap"].strip()
    suf = (sku or "").split("-")[-1].upper()
    if suf in STRAP_SUFFIX_LABELS:
        return STRAP_SUFFIX_LABELS[suf]
    if suf.startswith("B"):
        return "Steel Bracelet"
    if suf.startswith("R"):
        return "Rubber Strap"
    if suf.startswith("M") or suf.startswith("VT"):
        return "Leather Strap"
    return sku


def option_label_from_sku(sku: str, enrich: dict | None = None, *, multi_dial: bool) -> str:
    """Human label for the colour/strap chip (include dial when the model has multiple)."""
    en = enrich or {}
    strap = strap_label_from_sku(sku, en)
    parts = (sku or "").split("-")
    dial_code = parts[2].upper() if len(parts) >= 4 else ""
    dial = (en.get("colour") or "").strip() or DIAL_CODE_LABELS.get(dial_code, "")
    if multi_dial and dial:
        return f"{dial} · {strap}"
    return strap


def normalize_case_size(size: str | None, sku: str = "") -> str | None:
    if size:
        m = re.search(r"(\d{2,3})\s*mm", str(size), re.I)
        if m:
            return f"{m.group(1)}mm"
    return case_size_from_sku(sku)


def local_gallery(sku: str) -> list[str]:
    folder = ROOT / "public/products/cw-pdp" / slugify(sku)
    if not folder.exists():
        return []
    files = sorted(folder.glob("*.jpg"), key=lambda p: int(re.sub(r"\D", "", p.stem) or "0"))
    out = []
    for f in files:
        if f.stat().st_size < 2500:
            continue
        out.append(f"/products/cw-pdp/{slugify(sku)}/{f.name}")
    return out


def existing_images(paths: list[str] | None) -> list[str]:
    out = []
    for p in paths or []:
        if not p:
            continue
        fp = ROOT / "public" / p.lstrip("/")
        if fp.exists() and fp.stat().st_size >= 2500:
            out.append(p)
    return out


def gbp_for_sku(sku: str, fallback: float | None = None) -> float | None:
    raw = RAW_BY_SKU.get(sku)
    if raw and raw.get("gbpPrice") is not None:
        return float(raw["gbpPrice"])
    return fallback


def is_nearly_new(text: str | None) -> bool:
    return "nearly new" in (text or "").lower()


def display_name_en(sku: str, en: dict, raw: dict) -> str:
    """Prefer live catalogue name; ignore enrich contamination from Nearly New PDPs."""
    raw_name = (raw.get("name") or "").strip()
    en_name = (en.get("nameEn") or "").strip()
    if sku.upper().startswith("N") or is_nearly_new(raw_name):
        return en_name or raw_name or sku
    if is_nearly_new(en_name):
        return raw_name or re.sub(r"\s*-\s*Nearly New.*$", "", en_name, flags=re.I).strip() or sku
    return en_name or raw_name or sku


def enrich_score(en: dict) -> int:
    if not en or en.get("error"):
        return -100
    score = 0
    if en.get("strapVariants"):
        score += 8
    if en.get("technicalsEn"):
        score += 5
    if en.get("featuresEn"):
        score += 3
    if en.get("colour"):
        score += 2
    if en.get("shortDescriptionEn"):
        score += 2
    if en.get("images"):
        score += 1
    if is_nearly_new(en.get("nameEn")):
        score -= 20
    if "/sale/" in (en.get("sourceUrl") or "") or "nearly-new" in (en.get("sourceUrl") or ""):
        score -= 15
    return score


def best_enrich(members: list[dict]) -> dict:
    best: dict = {}
    best_s = -10_000
    for m in members:
        en = ENR.get(m.get("sku") or "") or {}
        s = enrich_score(en)
        if s > best_s:
            best_s = s
            best = en
    return best if best_s > -100 else {}


def best_source_url(members: list[dict], en: dict) -> str:
    for m in members:
        u = m.get("url") or ""
        if u and "/sale/" not in u and "nearly-new" not in u.lower():
            return u
    for m in members:
        if m.get("url"):
            return m["url"]
    return en.get("sourceUrl") or ""


def pick_editorial(members: list[dict], en: dict) -> list[dict]:
    editorial = (en.get("editorial") or {}).get("sections") or []
    if editorial:
        return editorial
    urls = [best_source_url(members, en)] + [m.get("url") or "" for m in members]
    for u in urls:
        mkey = model_key_from_url(u)
        if mkey and ED_MODELS.get(mkey) and ED_MODELS[mkey].get("sections"):
            return ED_MODELS[mkey].get("sections") or []
    # Fall back: strip ---nearly-new from key
    for u in urls:
        mkey = model_key_from_url(u)
        if not mkey:
            continue
        base = re.sub(r"---nearly-new$", "", mkey)
        if base != mkey and ED_MODELS.get(base) and ED_MODELS[base].get("sections"):
            return ED_MODELS[base].get("sections") or []
    return []


def resolve_variant_sku(v: dict, members: list, colour: str | None, primary_sku: str) -> str:
    sku = (v.get("sku") or "").strip()
    label = (v.get("labelEn") or "").strip().lower()
    if is_full_sku(sku):
        return sku
    # Match raw catalogue members by strap keyword in subtitle/url
    best = None
    tokens = [t for t in re.split(r"[^a-z0-9]+", label) if len(t) > 2]
    for m in members:
        msku = m.get("sku") or ""
        if not is_full_sku(msku):
            continue
        hay = f"{m.get('subtitle') or ''} {m.get('url') or ''} {msku}".lower()
        score = sum(1 for t in tokens if t in hay)
        if "bracelet" in label and msku.upper().endswith(("B1", "B1R", "B0", "B0R")):
            score += 3
            # Prefer B1 over B0 when both exist
            if msku.upper().endswith(("B1", "B1R")):
                score += 2
        if score > 0 and (best is None or score > best[0]):
            best = (score, msku)
    if best:
        return best[1]
    if is_full_sku(primary_sku):
        if v.get("images") and slugify(primary_sku) in (v.get("image") or ""):
            return primary_sku
    return sku


def build_tech_specs(en: dict) -> list[dict]:
    specs = []
    for row in en.get("technicalsEn") or []:
        label_en = row.get("labelEn") or ""
        value_en = str(row.get("valueEn") or "")
        if label_en in ("Strap SKU",):
            continue
        label_ko = SPEC_LABELS.get(label_en) or translate_en(label_en)
        value_ko = to_ko(value_en) if re.search(r"[A-Za-z]{3,}", value_en) else value_en
        # Prefer translate for longer values
        if len(value_en) > 18 and re.search(r"[A-Za-z]", value_en):
            value_ko = translate_en(value_en)
        specs.append({"labelKo": label_ko, "valueKo": value_ko})
    return specs


_TX_CACHE_PATH = ROOT / "src/data/cw/cw-translate-cache.json"
_TX_CACHE = json.loads(_TX_CACHE_PATH.read_text()) if _TX_CACHE_PATH.exists() else {}


def polish_ko(out: str) -> str:
    out = out.replace("팔찌", "브레이슬릿").replace("검은 그림자", "블랙 섀도우")
    out = out.replace("사파이어 가장자리", "사파이어 엣지").replace("청동", "브론즈")
    out = out.replace("삼지창", "트라이던트").replace("물개", "실랜더")
    out = out.replace("크리스토퍼 워드", "크리스토퍼와드")
    out = out.replace("로꼬", "Loco").replace("로코", "Loco")
    out = out.replace("크리스토퍼와드(Christopher Ward)", "크리스토퍼와드")
    out = out.replace("Christopher Ward", "크리스토퍼와드")
    return out


def translate_en(text: str) -> str:
    """Google Translate (gtx) with CW term post-pass."""
    text = (text or "").strip()
    if not text:
        return ""
    if text in _TX_CACHE:
        return polish_ko(_TX_CACHE[text])
    # Protect model codes
    protected = {}
    def hold(m):
        k = f"⟦{len(protected)}⟧"
        protected[k] = m.group(0)
        return k
    held = re.sub(r"\b(?:C\d{2}|C\d|N\d{2}|Mk\.?\s*[IVX]+|GMT|COSC|Ti|Loco)\b", hold, text)
    try:
        import urllib.request, urllib.parse, json as _json
        q = urllib.parse.quote(held[:4500])
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ko&dt=t&q={q}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=25) as r:
            data = _json.loads(r.read().decode())
        out = "".join(part[0] for part in data[0] if part and part[0])
    except Exception:
        out = to_ko(text)
    for k, v in protected.items():
        out = out.replace(k, v)
    out = polish_ko(out)
    _TX_CACHE[text] = out
    if len(_TX_CACHE) % 25 == 0:
        _TX_CACHE_PATH.write_text(json.dumps(_TX_CACHE, ensure_ascii=False, indent=2))
    return out


def translate_story(name_en: str, short_en: str, features: list[str], images: list[str]) -> list[dict]:
    """Natural Korean PDP story blocks."""
    name_ko = to_ko(name_en)
    body_ko = translate_en(short_en) if short_en else f"{name_ko} — 크리스토퍼와드의 시그니처 타임피스."

    sections = [
        {
            "titleKo": name_ko,
            "bodyKo": body_ko,
            "image": images[0] if images else None,
        }
    ]

    feat_titles = [
        ("무브먼트", ["movement", "jewel", "power reserve", "automatic", "sellita", "eta", "calibre", "hour"]),
        ("다이얼", ["dial", "lume", "index", "hand"]),
        ("케이스", ["case", "titanium", "steel", "ceramic", "water", "atm", "bezel"]),
        ("스트랩", ["strap", "bracelet", "rubber", "leather", "bader", "consort"]),
    ]
    used = set()
    for title, keys in feat_titles:
        matched = [f for f in features if any(k in f.lower() for k in keys) and f not in used]
        if not matched:
            continue
        for f in matched:
            used.add(f)
        img = None
        if title == "무브먼트" and len(images) > 1:
            img = images[1]
        elif title == "다이얼" and len(images) > 2:
            img = images[2]
        elif title == "케이스" and len(images) > 3:
            img = images[3]
        elif title == "스트랩" and len(images) > 4:
            img = images[4]
        body = translate_en(". ".join(matched[:6]))
        sections.append({"titleKo": title, "bodyKo": body, "image": img, "reverse": title in ("다이얼", "스트랩")})

    if len(sections) == 1 and len(images) > 1:
        sections.append(
            {
                "titleKo": "디테일 갤러리",
                "bodyKo": f"{name_ko}의 다이얼·케이스·스트랩 디테일을 가까이에서 확인해 보세요.",
                "image": images[min(2, len(images) - 1)],
                "reverse": True,
            }
        )
    return [s for s in sections if s.get("bodyKo")]


accents = ["#1A2A38", "#24302A", "#1A2428", "#2C241C", "#243447", "#3A2F28", "#1F4D3A", "#314036"]

products_out = []
grouped = {}

for raw in RAW["products"]:
    sku = raw["sku"]
    en = ENR.get(sku) or {}
    if en.get("error"):
        en = {}
    name_en = display_name_en(sku, en, raw)
    size = normalize_case_size(en.get("size") if not is_nearly_new(en.get("nameEn")) else None, sku)
    colour = en.get("colour") if not is_nearly_new(en.get("nameEn")) else None
    sub = clean_sub(raw.get("subtitle") or "")
    if not size or not colour:
        parts = [p.strip() for p in sub.split("·")]
        for part in parts:
            if re.match(r"\d+mm$", part.replace(" ", ""), re.I):
                size = size or normalize_case_size(part.strip(), sku)
            elif part and not any(
                x in part.lower()
                for x in ["automatic", "bracelet", "rubber", "leather", "gmt", "steel"]
            ):
                if not colour and "mm" not in part:
                    colour = part
    size = normalize_case_size(size, sku)
    # Group strap sisters across case diameters (official WSize axis).
    line = "nn" if (sku.upper().startswith("N") or is_nearly_new(raw.get("name"))) else "new"
    model_key = cw_model_group_key(raw.get("url") or "")
    group_key = f"{line}|model|{model_key}" if model_key else dial_family_key(sku, line)
    grouped.setdefault(
        group_key,
        {
            "raw_members": [],
            "en": {},
            "name_en": name_en,
            "sizes": set(),
            "colour": colour,
        },
    )
    grouped[group_key]["raw_members"].append(raw)
    if name_en and not is_nearly_new(name_en):
        grouped[group_key]["name_en"] = name_en
    elif not grouped[group_key].get("name_en"):
        grouped[group_key]["name_en"] = name_en
    if size:
        grouped[group_key]["sizes"].add(size)
    if colour:
        grouped[group_key]["colour"] = colour

for i, (gkey, g) in enumerate(sorted(grouped.items(), key=lambda x: x[0])):
    members = g["raw_members"]
    en = best_enrich(members) or g.get("en") or {}
    name_en = g["name_en"] or display_name_en(members[0]["sku"], en, members[0])
    case_sizes = sorted(
        g.get("sizes") or set(),
        key=lambda s: int(re.sub(r"\D", "", s) or "0"),
    )
    # Prefer primary from new-releases order, then richest gallery; fall back across sizes
    new_order = RAW["categories"].get("cw-new-releases", [])
    new_rank = {s: i for i, s in enumerate(new_order)}
    primary_sku = None
    ranked = sorted(
        [
            m["sku"]
            for m in members
            if is_full_sku(m.get("sku") or "")
            and not m["sku"].upper().startswith("N")
            and local_gallery(m["sku"])
        ],
        key=lambda s: (new_rank.get(s, 10_000), 0 if "42" in (s.split("-")[1] if "-" in s else "") else 1, s),
    )
    if ranked:
        primary_sku = ranked[0]
    if not primary_sku:
        primary_sku = next(
            (
                m["sku"]
                for m in members
                if is_full_sku(m.get("sku") or "")
                and not m["sku"].upper().startswith("N")
                and local_gallery(m["sku"])
            ),
            None,
        ) or next(
            (m["sku"] for m in members if is_full_sku(m.get("sku") or "")),
            members[0]["sku"],
        )
    primary_size = normalize_case_size(
        (ENR.get(primary_sku) or {}).get("size"), primary_sku
    )
    multi_case = len(case_sizes) > 1
    gbp = gbp_for_sku(primary_sku, members[0].get("gbpPrice"))
    if gbp is None:
        continue
    # List price only when this group is actually on sale (Nearly New / markdown)
    list_gbp = None
    if is_nearly_new(name_en) or any(is_nearly_new(m.get("name")) for m in members):
        list_gbp = en.get("gbpListPrice") or members[0].get("gbpListPrice")
    elif en.get("gbpListPrice") and members[0].get("gbpListPrice"):
        # genuine markdown on new line
        raw_list = members[0].get("gbpListPrice")
        if raw_list and float(raw_list) > float(gbp):
            list_gbp = float(raw_list)

    variants = []
    seen_vids = set()
    dial_codes = {
        (m.get("sku") or "").split("-")[2].upper()
        for m in members
        if is_full_sku(m.get("sku") or "") and (m.get("sku") or "").count("-") >= 3
    }
    multi_dial = len(dial_codes) > 1
    for m in members:
        msku = m.get("sku") or ""
        if not is_full_sku(msku):
            continue
        vid = slugify(msku)
        if vid in seen_vids:
            continue
        seen_vids.add(vid)
        men = ENR.get(msku) or {}
        label = None
        for sv in (men.get("strapVariants") or en.get("strapVariants") or []):
            if resolve_variant_sku(sv, members, g.get("colour"), primary_sku) == msku and sv.get("labelEn"):
                label = sv.get("labelEn")
                break
        if not label:
            sub = clean_sub(m.get("subtitle") or "")
            cand = sub.split("·")[-1].strip() if sub else ""
            if cand and "attribute" not in cand.lower() and len(cand) >= 3 and not cand.upper().startswith("C60-"):
                label = cand
        if not label:
            label = option_label_from_sku(msku, men, multi_dial=multi_dial)
        # Avoid dumping raw SKUs into the option picker.
        if label.upper().startswith("C60-") or label.upper().startswith("C63-") or label.upper().startswith("C12-"):
            label = option_label_from_sku(msku, men, multi_dial=multi_dial)
        vgbp = gbp_for_sku(msku, m.get("gbpPrice") or gbp)
        vimgs = local_gallery(msku)
        if not vimgs:
            for sv in (men.get("strapVariants") or en.get("strapVariants") or []):
                if resolve_variant_sku(sv, members, g.get("colour"), primary_sku) == msku:
                    vimgs = existing_images(sv.get("images"))
                    break
        if not vimgs:
            plp = f"/products/cw/{slugify(msku)}.jpg"
            if (ROOT / "public" / plp.lstrip("/")).exists():
                vimgs = [plp]
        if not vimgs:
            # Never borrow another strap/dial gallery — wrong hero + broken CDN
            # expectations when only the primary SKU was published.
            continue
        vsize = normalize_case_size(men.get("size") or (None if multi_case else primary_size), msku)
        vrow = {
            "id": vid,
            "name": label,
            "nameKo": to_ko(label),
            "sku": msku,
            "gbpPrice": float(vgbp),
            "price": round_krw(float(vgbp)),
            "image": vimgs[0],
            "images": vimgs[:10],
            "sourceUrl": m.get("url") or "",
            "inStock": bool(m.get("inStock", True)),
        }
        if multi_case and vsize:
            vrow["size"] = vsize
            vrow["colorKey"] = strap_color_key(msku)
            vrow["colorNameKo"] = to_ko(label)
        elif multi_dial:
            # Single-case but multi-dial: still expose dial×strap chips.
            vrow["colorKey"] = strap_color_key(msku)
            vrow["colorNameKo"] = to_ko(label)
        variants.append(vrow)
    if len(variants) <= 1:
        variants = []

    images = local_gallery(primary_sku) or existing_images(en.get("images"))
    if not images:
        for v in variants:
            if v["sku"] == primary_sku and v.get("images"):
                images = v["images"]
                break
    if not images and variants:
        images = variants[0]["images"]
    if not images:
        images = [f"/products/cw/{slugify(primary_sku)}.jpg"]
    # Prefer the primary variant gallery for hero/story (avoid enrich mixing dials)
    if variants:
        pref = next((v for v in variants if v["sku"] == primary_sku), variants[0])
        if pref.get("images"):
            images = pref["images"]

    sub_bits = []
    # Multi-case PDPs expose diameter as a picker — omit from the title.
    if not multi_case and primary_size:
        sub_bits.append(primary_size)
    elif not multi_case and case_sizes:
        sub_bits.append(case_sizes[0])
    # Multi-dial PDPs expose colour on chips — omit from the title so it
    # does not pin a single dial (e.g. Sand/Blue) onto a Black/Red primary.
    if g.get("colour") and not multi_dial:
        sub_bits.append(g["colour"])
    sub_en = " · ".join(sub_bits)
    name_ko = to_ko(name_en) + (f" · {to_ko(sub_en)}" if sub_en else "")

    # Category membership comes from PLP scrape (raw), not enrich — enrich often
    # mis-tags Nearly New as atelier/bel-canto and hides them from Clearance.
    cols: list[str] = []
    for m in members:
        for c in m.get("collections") or []:
            if c and c not in cols:
                cols.append(c)
    if not cols:
        cols = list(en.get("collections") or [])
    _COL_PRIORITY = [
        "cw-clearance",
        "cw-new-releases",
        "cw-bestsellers",
        "cw-hidden-gems",
        "cw-bel-canto",
        "cw-twelve",
        "cw-trident",
        "cw-sealander",
        "cw-moonphase",
        "cw-military",
        "cw-dive",
        "cw-integrated-sports",
        "cw-adventure-field",
        "cw-atelier",
    ]
    primary = next((c for c in _COL_PRIORITY if c in cols), None)
    if not primary:
        primary = (
            members[0].get("primaryCollection")
            or en.get("primaryCollection")
            or (cols[0] if cols else "cw-atelier")
        )

    price = round_krw(gbp)
    compare = round_krw(list_gbp) if list_gbp and list_gbp > gbp else None

    story_src = en.get("shortDescriptionEn") or ""
    if en.get("longDescriptionEn") and len(en["longDescriptionEn"]) > 40:
        story_src = (story_src + "\n\n" + en["longDescriptionEn"]).strip()
    story = translate_story(
        name_en,
        story_src,
        en.get("featuresEn") or [],
        images,
    )

    # Merge official CW editorial long-description (video, JJ01, captions…)
    editorial = pick_editorial(members, en)
    if editorial:
        ed_sections = []
        for es in editorial:
            title_en = (es.get("titleEn") or "").strip()
            body_en = (es.get("bodyEn") or "").strip()
            # Placeholder caption labels from old scraper — drop empty shells
            if re.match(r"^Detail\s+\d+$", body_en, re.I) and not title_en:
                continue
            title_ko = translate_en(title_en) if title_en else ""
            body_ko = translate_en(body_en) if body_en else ""
            # Keep distinctive English / brand titles
            TITLE_KO = {
                "Time to make the JJump": "Time to make the JJump",
                "Calibre JJ01": "Calibre JJ01",
                "Poetry in motion": "움직이는 시",
                "Introducing Calibre CW-003": "칼리버 CW-003 소개",
                "Architecture and artistry": "건축과 예술성",
                "Dialled up": "다이얼의 완성",
                "Your beating heart": "뛰는 심장",
                "The big finish": "피니싱의 하이라이트",
                "Case study": "케이스 스터디",
                "Charm bracelet": "매혹의 브레이슬릿",
                "Strap battle": "스트랩의 선택",
                "A revolution in motion": "움직이는 혁명",
            }
            if title_en in TITLE_KO:
                title_ko = TITLE_KO[title_en]
            elif title_en.startswith("Calibre JJ01"):
                title_ko = title_en
            elif title_en.startswith("Introducing Calibre"):
                title_ko = translate_en(title_en)
            img = es.get("image")
            if img and not existing_images([img]):
                img = None
            if not body_ko and not img and not es.get("videoUrl"):
                continue
            layout = es.get("layout") or "default"
            if layout == "wide" and (title_ko or body_ko):
                layout = "caption"
            if not title_ko and not body_ko and img:
                layout = "wide"
            ed_sections.append(
                {
                    "titleKo": title_ko,
                    "bodyKo": body_ko,
                    "image": img,
                    "videoUrl": es.get("videoUrl"),
                    "layout": layout,
                    "reverse": bool(es.get("reverse")),
                }
            )
        if ed_sections:
            # Drop consecutive duplicate bodies (keep first occurrence)
            deduped = []
            prev_body = ""
            for es in ed_sections:
                body = (es.get("bodyKo") or "").strip()
                if body and body == prev_body:
                    continue
                deduped.append(es)
                if body:
                    prev_body = body
            ed_sections = deduped
            # Keep intro story first, then editorial
            intro = story[:1] if story else []
            story = intro + ed_sections

    tech_specs = build_tech_specs(en)
    features_ko = [translate_en(f) for f in (en.get("featuresEn") or [])[:16]]

    # min price across variants for card
    if variants:
        price = min(v["price"] for v in variants)
        gbp = min(v["gbpPrice"] for v in variants)

    badge = members[0].get("badge")
    if compare and not badge:
        badge = "Sale"
    if en.get("featuresEn") and any("limited" in f.lower() for f in en["featuresEn"]):
        badge = badge or "Limited"

    desc = f"크리스토퍼와드 {name_ko}."
    if en.get("shortDescriptionEn") and not is_nearly_new(en.get("nameEn")):
        desc = translate_en(en["shortDescriptionEn"])[:320]

    source_url = best_source_url(members, en)

    products_out.append(
        {
            "id": f"cw-{slugify(primary_sku)}",
            "name": name_en,
            "nameKo": name_ko[:140],
            "brand": "Christopher Ward",
            "price": price,
            "compareAtPrice": compare,
            "gbpPrice": gbp,
            "gbpListPrice": list_gbp,
            "category": "watches",
            "subcategory": primary,
            "cwCollections": cols,
            "tags": ["christopher-ward", primary],
            "descriptionKo": desc,
            "image": images[0],
            "images": images,
            "hoverImage": images[1] if len(images) > 1 else None,
            "accent": accents[i % len(accents)],
            "badge": badge,
            "sku": primary_sku,
            "sourceUrl": source_url,
            "inStock": bool(
                en["inStock"]
                if "inStock" in en
                else members[0].get("inStock", True)
            ),
            "registeredAt": None,  # set below
            "editTier": "signature",
            "size": None if multi_case else primary_size,
            "variants": variants if len(variants) > 1 else [],
            "braceletResize": bool(en.get("braceletResize")),
            "braceletResizeFeeKrw": en.get("braceletResizeFeeKrw") or 20000,
            "storySections": story,
            "techSpecs": tech_specs,
            "featuresKo": features_ko,
            "memberSkus": [m["sku"] for m in members],
            "multiCase": multi_case,
            "caseSizes": case_sizes,
        }
    )

# registeredAt: new-releases order
new_order = RAW["categories"].get("cw-new-releases", [])
new_rank = {s: i for i, s in enumerate(new_order)}
for i, p in enumerate(products_out):
    ranks = [new_rank[s] for s in p["memberSkus"] if s in new_rank]
    if ranks:
        r = min(ranks)
        p["registeredAt"] = f"2026-07-28T{20 - r // 60:02d}:{r % 60:02d}:00.000Z"
    else:
        p["registeredAt"] = f"2026-07-20T10:{i % 60:02d}:{(i * 7) % 60:02d}.000Z"

# Emit TS
lines = [
    "/** Auto-generated CW catalogue — names KO, 만원 prices, PDP stories/variants. */",
    'import type { Product } from "@/data/products";',
    'import { CW_BRACELET_RESIZE_FEE, CW_BRACELET_SIZES_CM } from "@/data/cw-twelve-picnmix";',
    "",
    "export const cwCatalogProducts: Product[] = [",
]

for p in products_out:
    lines.append("  {")
    lines.append(f'    id: {json.dumps(p["id"])},')
    lines.append(f'    name: {json.dumps(p["name"], ensure_ascii=False)},')
    lines.append(f'    nameKo: {json.dumps(p["nameKo"], ensure_ascii=False)},')
    lines.append('    brand: "Christopher Ward",')
    lines.append(f'    price: {p["price"]},')
    if p.get("compareAtPrice"):
        lines.append(f'    compareAtPrice: {p["compareAtPrice"]},')
    lines.append(f'    gbpPrice: {p["gbpPrice"]},')
    if p.get("gbpListPrice"):
        lines.append(f'    gbpListPrice: {p["gbpListPrice"]},')
    lines.append('    category: "watches",')
    lines.append(f'    subcategory: {json.dumps(p["subcategory"])},')
    lines.append(
        f'    cwCollections: {json.dumps(p["cwCollections"], ensure_ascii=False)} as Product["cwCollections"],'
    )
    lines.append(f'    tags: {json.dumps(p["tags"], ensure_ascii=False)},')
    lines.append(f'    descriptionKo: {json.dumps(p["descriptionKo"], ensure_ascii=False)},')
    lines.append(f'    image: {json.dumps(p["image"])},')
    if p.get("images"):
        lines.append(f'    images: {json.dumps(p["images"])},')
    if p.get("hoverImage"):
        lines.append(f'    hoverImage: {json.dumps(p["hoverImage"])},')
    lines.append(f'    accent: {json.dumps(p["accent"])},')
    if p.get("badge"):
        lines.append(f'    badge: {json.dumps(p["badge"])},')
    lines.append(f'    sku: {json.dumps(p["sku"])},')
    lines.append(f'    sourceUrl: {json.dumps(p.get("sourceUrl"))},')
    lines.append(f'    inStock: {str(p.get("inStock", True)).lower()},')
    lines.append(f'    registeredAt: {json.dumps(p["registeredAt"])},')
    lines.append('    editTier: "signature",')
    if p.get("variants"):
        lines.append("    variants: [")
        for v in p["variants"]:
            lines.append("      {")
            lines.append(f'        id: {json.dumps(v["id"])},')
            lines.append(f'        name: {json.dumps(v["name"], ensure_ascii=False)},')
            lines.append(f'        nameKo: {json.dumps(v["nameKo"], ensure_ascii=False)},')
            lines.append(f'        sku: {json.dumps(v["sku"])},')
            lines.append(f'        gbpPrice: {v["gbpPrice"]},')
            lines.append(f'        price: {v["price"]},')
            lines.append(f'        image: {json.dumps(v["image"])},')
            if v.get("images") and len(v["images"]) > 1:
                lines.append(f'        images: {json.dumps(v["images"])},')
            lines.append(f'        sourceUrl: {json.dumps(v["sourceUrl"])},')
            lines.append(f'        inStock: {str(v.get("inStock", True)).lower()},')
            if v.get("size"):
                lines.append(f'        size: {json.dumps(v["size"])},')
            if v.get("colorKey"):
                lines.append(f'        colorKey: {json.dumps(v["colorKey"])},')
            if v.get("colorNameKo"):
                lines.append(f'        colorNameKo: {json.dumps(v["colorNameKo"], ensure_ascii=False)},')
            lines.append("      },")
        lines.append("    ],")
    if p.get("braceletResize"):
        lines.append("    braceletResize: {")
        lines.append("      feeKrw: CW_BRACELET_RESIZE_FEE,")
        lines.append("      sizesCm: [...CW_BRACELET_SIZES_CM],")
        lines.append("    },")
    if p.get("storySections"):
        lines.append("    storySections: [")
        for s in p["storySections"]:
            lines.append("      {")
            lines.append(f'        titleKo: {json.dumps(s["titleKo"], ensure_ascii=False)},')
            lines.append(f'        bodyKo: {json.dumps(s["bodyKo"], ensure_ascii=False)},')
            if s.get("image"):
                lines.append(f'        image: {json.dumps(s["image"])},')
            if s.get("videoUrl"):
                lines.append(f'        videoUrl: {json.dumps(s["videoUrl"])},')
            if s.get("layout") and s.get("layout") != "default":
                lines.append(f'        layout: {json.dumps(s["layout"])},')
            if s.get("reverse"):
                lines.append("        reverse: true,")
            lines.append("      },")
        lines.append("    ],")
    if p.get("featuresKo"):
        lines.append(f'    featuresKo: {json.dumps(p["featuresKo"], ensure_ascii=False)},')
    if p.get("techSpecs"):
        lines.append("    techSpecs: [")
        for s in p["techSpecs"]:
            lines.append(
                "      {"
                f' labelKo: {json.dumps(s["labelKo"], ensure_ascii=False)},'
                f' valueKo: {json.dumps(s["valueKo"], ensure_ascii=False)} '
                "},"
            )
        lines.append("    ],")
    lines.append("  },")

lines.append("];")
lines.append("")

out = ROOT / "src/data/cw/cw-catalog.ts"
out.write_text("\n".join(lines))
_TX_CACHE_PATH.write_text(json.dumps(_TX_CACHE, ensure_ascii=False, indent=2))
multi_n = sum(1 for p in products_out if p.get("multiCase"))
print(
    "wrote",
    out,
    "products",
    len(products_out),
    "withVariants",
    sum(1 for p in products_out if p.get("variants")),
    "multiCaseSize",
    multi_n,
    "enriched",
    sum(1 for p in products_out if p.get("storySections") and p["storySections"][0].get("bodyKo")),
)
