#!/usr/bin/env python3
"""Rebuild cw-catalog.ts from raw (+ optional enriched) with KO names, rounded prices, variants, stories."""
from __future__ import annotations

import json, re, html as H
from pathlib import Path

ROOT = Path("/Users/jeonghyunlee/Documents/briq")
RAW = json.loads((ROOT / "src/data/cw/cw-catalog-raw.json").read_text())
ENR_PATH = ROOT / "src/data/cw/cw-pdp-enriched.json"
ENR = json.loads(ENR_PATH.read_text())["products"] if ENR_PATH.exists() else {}

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


def local_gallery(sku: str) -> list[str]:
    folder = ROOT / "public/products/cw-pdp" / slugify(sku)
    if not folder.exists():
        return []
    files = sorted(folder.glob("*.jpg"), key=lambda p: int(re.sub(r"\D", "", p.stem) or "0"))
    return [f"/products/cw-pdp/{slugify(sku)}/{f.name}" for f in files]


def resolve_variant_sku(v: dict, members: list, colour: str | None, primary_sku: str) -> str:
    sku = (v.get("sku") or "").strip()
    label = (v.get("labelEn") or "").strip().lower()
    if is_full_sku(sku):
        return sku
    # Match raw catalogue members by strap keyword in subtitle/url
    for m in members:
        msku = m.get("sku") or ""
        if not is_full_sku(msku):
            continue
        hay = f"{m.get('subtitle') or ''} {m.get('url') or ''} {msku}".lower()
        tokens = [t for t in re.split(r"[^a-z0-9]+", label) if len(t) > 2]
        if tokens and all(t in hay or t[:4] in hay for t in tokens[:2]):
            return msku
    # Same dial prefix as primary + strap code from label heuristics
    if is_full_sku(primary_sku):
        prefix = "-".join(primary_sku.split("-")[:-1])
        # Prefer member with same dial prefix
        same = [m["sku"] for m in members if (m.get("sku") or "").startswith(prefix + "-")]
        for msku in same:
            hay = msku.lower()
            if "bracelet" in label and msku.upper().endswith(("B0", "B1", "B0R")):
                return msku
        # Last resort: keep primary when this is the selected strap image set
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


def translate_en(text: str) -> str:
    """Google Translate (gtx) with CW term post-pass."""
    text = (text or "").strip()
    if not text:
        return ""
    if text in _TX_CACHE:
        return _TX_CACHE[text]
    # Protect model codes
    protected = {}
    def hold(m):
        k = f"⟦{len(protected)}⟧"
        protected[k] = m.group(0)
        return k
    held = re.sub(r"\b(?:C\d{2}|C\d|N\d{2}|Mk\.?\s*[IVX]+|GMT|COSC|Ti)\b", hold, text)
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
    # Prefer our lexicon for brand terms that gtx literalizes
    out = out.replace("팔찌", "브레이슬릿").replace("검은 그림자", "블랙 섀도우")
    out = out.replace("사파이어 가장자리", "사파이어 엣지").replace("청동", "브론즈")
    out = out.replace("삼지창", "트라이던트").replace("물개", "실랜더")
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

# Group by name + size + colour when enriched; else keep flat SKUs
products_out = []
grouped = {}

for raw in RAW["products"]:
    sku = raw["sku"]
    en = ENR.get(sku) or ENR.get(raw.get("sku")) or {}
    if en.get("error"):
        en = {}

    name_en = en.get("nameEn") or raw.get("name") or sku
    size = en.get("size")
    colour = en.get("colour")
    # parse from subtitle if needed
    sub = clean_sub(raw.get("subtitle") or "")
    if not size or not colour:
        parts = [p.strip() for p in sub.split("·")]
        for p in parts:
            if re.match(r"\d+mm$", p.replace(" ", "")):
                size = size or p.strip()
            elif p and not any(x in p.lower() for x in ["automatic", "bracelet", "rubber", "leather", "gmt"]):
                if not colour and "mm" not in p:
                    colour = p

    group_key = f"{name_en}|{size or ''}|{colour or ''}"
    grouped.setdefault(group_key, {"raw_members": [], "en": en, "name_en": name_en, "size": size, "colour": colour})
    grouped[group_key]["raw_members"].append(raw)
    # prefer enriched member
    if en and not en.get("error"):
        grouped[group_key]["en"] = en

for i, (gkey, g) in enumerate(sorted(grouped.items(), key=lambda x: x[0])):
    en = g["en"] or {}
    name_en = g["name_en"]
    members = g["raw_members"]
    # primary enriched or first member — prefer full SKU
    primary_sku = en.get("sku") or members[0]["sku"]
    if not is_full_sku(primary_sku):
        primary_sku = next((m["sku"] for m in members if is_full_sku(m.get("sku") or "")), members[0]["sku"])
    # If enrich collapsed to master, keep a full member SKU as primary
    if en.get("seedSku") and is_full_sku(en["seedSku"]):
        primary_sku = en["seedSku"]
    elif not is_full_sku(str(en.get("sku") or "")):
        for m in members:
            if is_full_sku(m.get("sku") or ""):
                primary_sku = m["sku"]
                break
    gbp = en.get("gbpPrice") if en.get("gbpPrice") is not None else members[0].get("gbpPrice")
    if gbp is None:
        continue
    list_gbp = en.get("gbpListPrice") or members[0].get("gbpListPrice")

    # variants from strapVariants if present, else from group members with different straps
    variants = []
    strap_vars = [v for v in (en.get("strapVariants") or []) if v.get("sku") and v.get("price") is not None]
    if not strap_vars:
        strap_vars = [v for v in (en.get("strapVariants") or []) if v.get("labelEn")]
    if strap_vars:
        seen_vids = set()
        for v in strap_vars:
            vsku = resolve_variant_sku(v, members, g.get("colour"), primary_sku)
            if not vsku:
                continue
            vid = slugify(vsku)
            if vid in seen_vids:
                continue
            seen_vids.add(vid)
            vimgs = v.get("images") or local_gallery(vsku)
            if not vimgs:
                # Prefer PLP hero for this SKU
                plp = f"/products/cw/{slugify(vsku)}.jpg"
                if (ROOT / "public" / plp.lstrip("/")).exists():
                    vimgs = [plp]
                else:
                    vimgs = local_gallery(primary_sku)[:1] or [en.get("image")]
            vimgs = [x for x in vimgs if x]
            variants.append(
                {
                    "id": vid,
                    "name": v.get("labelEn") or vsku,
                    "nameKo": to_ko(v.get("labelEn") or vsku),
                    "sku": vsku,
                    "gbpPrice": v.get("gbpPrice") or gbp,
                    "price": v.get("price") or round_krw(v.get("gbpPrice") or gbp),
                    "image": vimgs[0],
                    "images": vimgs,
                    "sourceUrl": v.get("sourceUrl") or members[0].get("url") or "",
                    "inStock": v.get("inStock", True),
                }
            )
    elif len(members) > 1:
        # fallback: each raw member as strap-ish variant using subtitle last token
        for m in members:
            sub = clean_sub(m.get("subtitle") or "")
            label = sub.split("·")[-1].strip() if sub else m["sku"]
            mgbp = m.get("gbpPrice") or gbp
            msku = m["sku"]
            vimgs = local_gallery(msku) or [f"/products/cw/{slugify(msku)}.jpg"]
            variants.append(
                {
                    "id": slugify(msku),
                    "name": label,
                    "nameKo": to_ko(label),
                    "sku": msku,
                    "gbpPrice": mgbp,
                    "price": round_krw(mgbp),
                    "image": vimgs[0],
                    "images": vimgs,
                    "sourceUrl": m.get("url") or "",
                    "inStock": True,
                }
            )

    images = en.get("images") or local_gallery(primary_sku)
    if not images:
        images = [f"/products/cw/{slugify(primary_sku)}.jpg"]
    # Prefer longest gallery among variants matching primary
    for v in variants:
        if v["sku"] == primary_sku and len(v.get("images") or []) > len(images):
            images = v["images"]
            break

    sub_bits = []
    if g.get("size"):
        sub_bits.append(g["size"])
    if g.get("colour"):
        sub_bits.append(g["colour"])
    sub_en = " · ".join(sub_bits)
    name_ko = to_ko(name_en) + (f" · {to_ko(sub_en)}" if sub_en else "")

    cols = en.get("collections") or members[0].get("collections") or []
    primary = en.get("primaryCollection") or members[0].get("primaryCollection") or (cols[0] if cols else "cw-atelier")

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
    if en.get("shortDescriptionEn"):
        desc = translate_en(en["shortDescriptionEn"])[:320]

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
            "accent": accents[i % len(accents)],
            "badge": badge,
            "sku": primary_sku,
            "sourceUrl": en.get("sourceUrl") or members[0].get("url"),
            "inStock": en.get("inStock", True),
            "registeredAt": None,  # set below
            "editTier": "signature",
            "variants": variants if len(variants) > 1 else [],
            "braceletResize": bool(en.get("braceletResize")),
            "braceletResizeFeeKrw": en.get("braceletResizeFeeKrw") or 20000,
            "storySections": story,
            "techSpecs": tech_specs,
            "featuresKo": features_ko,
            "memberSkus": [m["sku"] for m in members],
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
print("wrote", out, "products", len(products_out), "withVariants", sum(1 for p in products_out if p.get("variants")), "enriched", sum(1 for p in products_out if p.get("storySections") and p["storySections"][0].get("bodyKo")))
