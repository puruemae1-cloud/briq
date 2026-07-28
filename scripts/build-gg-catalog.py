#!/usr/bin/env python3
"""Build gg-catalog.ts from gg-catalog-raw.json (Galvin Green new arrivals)."""
from __future__ import annotations

import html as H
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "src/data/gg/gg-catalog-raw.json"
OUT_PATH = ROOT / "src/data/gg/gg-catalog.ts"
IMG_ROOT = ROOT / "public/products/gg-pdp"

ACCENTS = [
    "#1A2E28",
    "#1F4D3A",
    "#24302A",
    "#2A4038",
    "#2F5A3E",
    "#1E3A4A",
    "#243447",
    "#2C2A28",
    "#3A2F28",
    "#1A2428",
]

# Longest phrases first for translation.
PHRASE_MAP = [
    ("Crystal Blue", "크리스탈 블루"),
    ("Royal Blue", "로열 블루"),
    ("Moonlight Blue", "문라이트 블루"),
    ("Forged Iron", "포지드 아이언"),
    ("Mid layer", "미드레이어"),
    ("Mid-layer", "미드레이어"),
    ("Water repellent", "발수"),
    ("Water-repellent", "발수"),
    ("Waterproof", "방수"),
    ("Windproof", "방풍"),
    ("Breathable", "통기성"),
    ("Insulating", "보온"),
    ("Full Zip", "풀집"),
    ("Half Zip", "하프집"),
    ("Golf Jacket", "골프 재킷"),
    ("Golf Vest", "골프 베스트"),
    ("Golf Shirt", "골프 셔츠"),
    ("Golf Trousers", "골프 팬츠"),
    ("Golf Shorts", "골프 쇼츠"),
    ("Golf Skirt", "골프 스커트"),
    ("Golf Cap", "골프 캡"),
    ("Golf Hat", "골프 햇"),
    ("Golf Polo", "골프 폴로"),
    ("Trousers", "팬츠"),
    ("Jacket", "재킷"),
    ("Vest", "베스트"),
    ("Shirt", "셔츠"),
    ("Shorts", "쇼츠"),
    ("Skirt", "스커트"),
    ("Cap", "캡"),
    ("Hat", "햇"),
    ("Polo", "폴로"),
    ("Hoodie", "후디"),
    ("Sweater", "스웨터"),
    ("Pullover", "풀오버"),
    ("Pants", "팬츠"),
    ("Dress", "드레스"),
    ("Gloves", "글러브"),
    ("Belt", "벨트"),
    ("Socks", "삭스"),
    ("Stretch", "스트레치"),
    ("Lightweight", "경량"),
    ("Performance", "퍼포먼스"),
    ("Technical", "테크니컬"),
    ("Layer", "레이어"),
    ("Sleeve", "슬리브"),
    ("Long", "롱"),
    ("Short", "숏"),
    ("Men", "남성"),
    ("Women", "여성"),
    ("Ladies", "여성"),
]

COLOR_MAP = {
    "Crystal Blue": "크리스탈 블루",
    "Royal Blue": "로열 블루",
    "Moonlight Blue": "문라이트 블루",
    "Delphinium Blue": "델피늄 블루",
    "Storm Blue": "스톰 블루",
    "Forged Iron": "포지드 아이언",
    "Pink Fuchsia": "핑크 퓨시아",
    "Black": "블랙",
    "Navy": "네이비",
    "Orange": "오렌지",
    "White": "화이트",
    "Sand": "샌드",
    "Beige": "베이지",
    "Grey": "그레이",
    "Gray": "그레이",
    "Blue": "블루",
    "Pink": "핑크",
    "Fuchsia": "퓨시아",
    "Red": "레드",
    "Yellow": "옐로우",
    "Green": "그린",
    "Olive": "올리브",
    "Brown": "브라운",
    "Ivory": "아이보리",
    "Cream": "크림",
    "Silver": "실버",
    "Gold": "골드",
    "Purple": "퍼플",
    "Teal": "틸",
    "Coral": "코랄",
    "Charcoal": "차콜",
    "Stone": "스톤",
    "Khaki": "카키",
    "Lime": "라임",
    "Turquoise": "터쿼이즈",
}

COLOR_TAGS = sorted(COLOR_MAP.keys(), key=len, reverse=True)

# Extra description phrases (longest first)
DESC_PHRASES = [
    (
        "combines modern design with the reliable performance of Galvin Green’s award-winning rain gear",
        "갈빈 그린의 수상 경력 레인 기어다운 신뢰할 수 있는 퍼포먼스와 모던 디자인을 결합했습니다",
    ),
    (
        "combines modern design with the high-performance features you expect from Galvin Green’s rainwear collection",
        "갈빈 그린 레인웨어 컬렉션에서 기대하는 하이퍼포먼스 기능과 모던 디자인을 결합했습니다",
    ),
    (
        "Made from Pertex® Shield 3-layer stretch fabric, this jacket is 100% waterproof, windproof, and highly breathable, ensuring you stay dry and comfortable during wet rounds",
        "Pertex® Shield 3-레이어 스트레치 원단으로 제작되어 100% 방수·방풍·고통기성이며, 비 오는 라운드에서도 건조하고 편안하게 유지합니다",
    ),
    (
        "Made from Pertex® Shield 3-layer stretch fabric, this jacket is fully waterproof and windproof, offering excellent breathability to keep you comfortable in any weather",
        "Pertex® Shield 3-레이어 스트레치 원단으로 제작되어 완전 방수·방풍이며, 뛰어난 통기성으로 어떤 날씨에서도 편안하게 유지합니다",
    ),
    (
        "The sleek, contrasting panels offer a modern look while maintaining functional performance.",
        "슬릭한 대비 패널이 기능성을 유지하면서 모던한 룩을 완성합니다.",
    ),
    ("award-winning rain gear", "수상 경력의 레인 기어"),
    ("rainwear collection", "레인웨어 컬렉션"),
    ("modern design", "모던 디자인"),
    ("reliable performance", "신뢰할 수 있는 퍼포먼스"),
    ("functional performance", "기능적 퍼포먼스"),
    ("high-performance features", "하이퍼포먼스 기능"),
    ("high-performance", "하이퍼포먼스"),
    ("contrasting panels", "대비 패널"),
    ("modern look", "모던한 룩"),
    ("stay dry and comfortable", "건조하고 편안하게"),
    ("during wet rounds", "비 오는 라운드에서도"),
    ("in any weather", "어떤 날씨에서도"),
    ("keep you comfortable", "편안하게 유지"),
    ("offering excellent breathability", "뛰어난 통기성을 제공하며"),
    ("fully waterproof and windproof", "완전 방수·방풍"),
    ("100% waterproof, windproof, and highly breathable", "100% 방수·방풍·고통기성"),
    ("Made from", ""),
    ("this jacket is", "이 재킷은"),
    ("this vest is", "이 베스트는"),
    ("ensuring you", ""),
    ("you expect from", "에서 기대하는"),
    ("fabric,", "원단으로,"),
    ("The ", ""),
]

TECH_TAG_HINTS = (
    "PERTEX",
    "INSULA",
    "VENTIL",
    "INTERFACE",
    "GORE",
    "C-KNIT",
    "STRETCH",
    "WATERPROOF",
    "WINDPROOF",
)


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "item"


def gbp_to_krw(gbp: float) -> int:
    return int(round((gbp * 2100 * 1.05 + 200_000) / 10_000) * 10_000)


def title_case_color(slug: str) -> str:
    return " ".join(w.capitalize() for w in slug.replace("_", "-").split("-") if w)


def color_to_ko(color: str) -> str:
    if not color:
        return ""
    if color in COLOR_MAP:
        return COLOR_MAP[color]
    # Greedy longest-match over the remaining string
    tokens = color.split()
    out: list[str] = []
    i = 0
    while i < len(tokens):
        matched = False
        for n in range(min(3, len(tokens) - i), 0, -1):
            chunk = " ".join(tokens[i : i + n])
            if chunk in COLOR_MAP:
                out.append(COLOR_MAP[chunk])
                i += n
                matched = True
                break
            titled = " ".join(t.title() for t in tokens[i : i + n])
            if titled in COLOR_MAP:
                out.append(COLOR_MAP[titled])
                i += n
                matched = True
                break
        if not matched:
            out.append(COLOR_MAP.get(tokens[i].title(), tokens[i]))
            i += 1
    return " ".join(out)


def translate_apparel(text: str) -> str:
    if not text:
        return ""
    protected: list[str] = []

    def _protect(m: re.Match[str]) -> str:
        protected.append(m.group(0))
        return f"__PROT{len(protected) - 1}__"

    s = re.sub(
        r"PERTEX®|PERTEX\u00ae|INSULA™|INSULA\u2122|VENTIL8™|VENTIL8\u2122|"
        r"INTERFACE-1™|INTERFACE-1\u2122|INTERFACE™|Galvin Green|C-KNIT™|GORE-TEX®|"
        r"Pertex® Shield 3-layer stretch|Pertex® Shield",
        _protect,
        text,
        flags=re.I,
    )
    for en, ko in DESC_PHRASES:
        s = re.sub(re.escape(en), ko, s, flags=re.I)
    for en, ko in PHRASE_MAP:
        s = re.sub(rf"\b{re.escape(en)}\b", ko, s, flags=re.I)
    for en in COLOR_TAGS:
        s = re.sub(rf"\b{re.escape(en)}\b", COLOR_MAP[en], s, flags=re.I)
    for i, tok in enumerate(protected):
        s = s.replace(f"__PROT{i}__", tok)
    return re.sub(r"\s{2,}", " ", s).strip()


def english_ratio(text: str) -> float:
    if not text:
        return 1.0
    letters = re.findall(r"[A-Za-z]+", text)
    hangul = re.findall(r"[가-힣]+", text)
    a, h = len(letters), len(hangul)
    if a + h == 0:
        return 0.0
    return a / (a + h)


def describe_from_tags(style: str, tags: list[str], name_ko: str) -> str:
    tset = {t.lower() for t in (tags or [])}
    joined = " ".join(tags or []).upper()
    if "PERTEX" in joined or "waterproofs" in tset or any(
        "waterproof" in t.lower() for t in tags or []
    ):
        base = (
            f"{name_ko}은 갈빈 그린의 방수·방풍 골프웨어입니다. "
            "비와 바람에도 쾌적함을 유지하도록 설계되었습니다."
        )
    elif "INTERFACE" in joined or "windproof" in tset:
        base = (
            f"{name_ko}은 방풍·발수 성능의 갈빈 그린 골프웨어입니다. "
            "바람 부는 라운드에서도 실루엣과 보온을 함께 챙깁니다."
        )
    elif "INSULA" in joined or "midlayers" in tset:
        base = (
            f"{name_ko}은 INSULA™ 보온 기술이 적용된 갈빈 그린 미드레이어입니다. "
            "단독 착용은 물론 레이어링에도 잘 어울립니다."
        )
    elif "VENTIL" in joined or "shortsleeve" in tset:
        base = (
            f"{name_ko}은 통기성 좋은 갈빈 그린 골프 셔츠입니다. "
            "라운드 중에도 쾌적한 착용감을 위해 설계되었습니다."
        )
    elif "pants" in tset or "shorts" in tset or "skirt" in tset or "skirts" in tset:
        base = (
            f"{name_ko}은 움직임이 편한 갈빈 그린 골프 보텀입니다. "
            "코스 위에서의 활동성과 단정한 핏을 함께 잡았습니다."
        )
    elif "cap" in tset or "hat" in tset or "hats" in tset:
        base = (
            f"{name_ko}은 갈빈 그린 골프 헤드웨어입니다. "
            "강한 햇살과 가벼운 비에도 실용적으로 착용할 수 있습니다."
        )
    else:
        base = (
            f"{name_ko}은 스웨덴 골프웨어 브랜드 갈빈 그린의 신상품입니다. "
            "코스 위 퍼포먼스와 세련된 실루엣을 동시에 담았습니다."
        )
    tech = [t for t in (tags or []) if any(h in t.upper() for h in TECH_TAG_HINTS)]
    tech = list(dict.fromkeys(tech))[:4]
    if tech:
        base += " 적용 테크: " + ", ".join(tech) + "."
    return base


def compose_description_ko(style: str, tags: list[str], body_html: str, name_ko: str) -> str:
    plain = strip_html(body_html or "")
    translated = translate_apparel(plain)
    if english_ratio(translated) > 0.22 or len(translated) < 40:
        return describe_from_tags(style, tags, name_ko)
    cleaned = re.sub(
        r"\b(combines|with|the|and|from|for|you|your|this|that|to|of|a|an|is|are|in|on)\b",
        " ",
        translated,
        flags=re.I,
    )
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" ,.")
    if english_ratio(cleaned) > 0.18:
        return describe_from_tags(style, tags, name_ko)
    return cleaned + ("." if cleaned and not cleaned.endswith(".") else "")


def strip_html(html: str) -> str:
    if not html:
        return ""
    s = H.unescape(html)
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</p>", "\n", s)
    s = re.sub(r"(?i)</li>", "\n", s)
    s = re.sub(r"(?i)<li[^>]*>", "• ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def paragraphs(text: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"\n+", text) if p.strip()]
    out: list[str] = []
    for p in parts:
        if p.startswith("•"):
            continue
        if len(p) < 20:
            continue
        out.append(p)
    return out


def bullet_points(text: str) -> list[str]:
    bullets = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("•"):
            bullets.append(line.lstrip("• ").strip())
        elif re.match(r"^[-*]\s+", line):
            bullets.append(re.sub(r"^[-*]\s+", "", line).strip())
    return [b for b in bullets if b]


def tech_specs_from_tags(tags: list[str]) -> list[dict[str, str]]:
    specs: list[dict[str, str]] = []
    seen: set[str] = set()
    for tag in tags or []:
        upper = tag.upper()
        if any(h in upper for h in TECH_TAG_HINTS) or "layer" in tag.lower():
            key = tag.lower()
            if key in seen:
                continue
            seen.add(key)
            specs.append({"labelKo": "테크", "valueKo": tag})
    return specs[:8]


def local_images(handle: str) -> list[str]:
    folder = IMG_ROOT / handle
    if not folder.exists():
        return []
    files = sorted(
        list(folder.glob("*.jpg")) + list(folder.glob("*.webp")) + list(folder.glob("*.png")),
        key=lambda p: int(re.sub(r"\D", "", p.stem) or "0"),
    )
    out = []
    for f in files[:6]:
        if f.stat().st_size < 2000:
            continue
        out.append(f"/products/gg-pdp/{handle}/{f.name}")
    return out


def longest_common_prefix(strings: list[str]) -> str:
    if not strings:
        return ""
    prefix = strings[0]
    for s in strings[1:]:
        while not s.startswith(prefix) and prefix:
            prefix = prefix[:-1]
        if not prefix:
            break
    return prefix


COLOR_WORDS = {
    w
    for ct in COLOR_TAGS
    for w in ct.lower().replace(" ", "-").split("-")
} | {
    "crystal",
    "royal",
    "moonlight",
    "delphinium",
    "storm",
    "forged",
    "iron",
    "fuchsia",
}


def color_from_handle_suffix(handle: str) -> str | None:
    parts = handle.split("-")
    if len(parts) < 2:
        return None
    trail: list[str] = []
    for p in reversed(parts[1:]):
        if p in COLOR_WORDS:
            trail.append(p)
        else:
            break
    if not trail:
        return None
    trail.reverse()
    return title_case_color("-".join(trail))


def color_from_tags_ordered(handle: str, tags: list[str]) -> str | None:
    present = [ct for ct in COLOR_TAGS if ct in (tags or [])]
    if not present:
        return None

    def pos(ct: str) -> int:
        slug = ct.lower().replace(" ", "-")
        i = handle.find(slug)
        return i if i >= 0 else 10_000

    present.sort(key=pos)
    return " ".join(present)


def color_from_handle_group(handles: list[str], handle: str, tags: list[str]) -> str:
    if len(handles) == 1:
        return (
            color_from_handle_suffix(handle)
            or color_from_tags_ordered(handle, tags)
            or "Default"
        )
    prefix = longest_common_prefix(handles)
    while prefix and not prefix.endswith("-"):
        if all(len(h) > len(prefix) and h[len(prefix)] == "-" for h in handles):
            break
        prefix = prefix[:-1]
    if prefix.endswith("-"):
        remainder = handle[len(prefix) :]
    else:
        cut = prefix.rfind("-")
        if cut > 0:
            prefix = prefix[: cut + 1]
            remainder = handle[len(prefix) :]
        else:
            remainder = ""
    remainder = remainder.strip("-")
    if remainder:
        return title_case_color(remainder)
    return (
        color_from_handle_suffix(handle)
        or color_from_tags_ordered(handle, tags)
        or "Default"
    )


def ts_str(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def ts_optional(key: str, value, indent: int = 4) -> str:
    if value is None:
        return ""
    pad = " " * indent
    if isinstance(value, bool):
        return f"{pad}{key}: {'true' if value else 'false'},\n"
    if isinstance(value, (int, float)):
        return f"{pad}{key}: {value},\n"
    if isinstance(value, str):
        return f"{pad}{key}: {ts_str(value)},\n"
    if isinstance(value, list):
        if not value:
            return ""
        if all(isinstance(x, str) for x in value):
            inner = ", ".join(ts_str(x) for x in value)
            return f"{pad}{key}: [{inner}],\n"
        # objects
        lines = [f"{pad}{key}: ["]
        for item in value:
            if isinstance(item, dict):
                lines.append(f"{pad}  {{")
                for k, v in item.items():
                    if isinstance(v, bool):
                        lines.append(f"{pad}    {k}: {'true' if v else 'false'},")
                    elif isinstance(v, (int, float)):
                        lines.append(f"{pad}    {k}: {v},")
                    elif isinstance(v, list):
                        inner = ", ".join(ts_str(x) for x in v)
                        lines.append(f"{pad}    {k}: [{inner}],")
                    else:
                        lines.append(f"{pad}    {k}: {ts_str(str(v))},")
                lines.append(f"{pad}  }},")
            else:
                lines.append(f"{pad}  {ts_str(str(item))},")
        lines.append(f"{pad}],")
        return "\n".join(lines) + "\n"
    return ""


def build() -> dict:
    raw = json.loads(RAW_PATH.read_text())
    products = raw.get("products") or []
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    # Group by styleName (+ collection so men/women don't merge)
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for p in products:
        style = (p.get("styleName") or p.get("title", "").split(" - ")[0]).strip()
        coll = p.get("collection") or "gg-new-men"
        groups[(style, coll)].append(p)

    briq_products: list[dict] = []
    used_ids: set[str] = set()

    for (style_name, collection), members in sorted(groups.items(), key=lambda x: x[0][0].lower()):
        handles = [m["handle"] for m in members]
        # Derive/refresh color names within group
        for m in members:
            m["colorName"] = color_from_handle_group(handles, m["handle"], m.get("tags") or [])

        style_slug = slugify(style_name)
        pid = f"gg-{style_slug}"
        if pid in used_ids:
            pid = f"gg-{style_slug}-{collection.replace('gg-new-', '')}"
        used_ids.add(pid)

        # Prefer first member with images / stock
        members_sorted = sorted(
            members,
            key=lambda m: (
                0 if any(v.get("available") for v in m.get("variants") or []) else 1,
                m.get("handle", ""),
            ),
        )
        primary = members_sorted[0]
        name = style_name if " - " not in primary.get("title", "") else primary["title"].split(" - ")[0].strip()
        # Prefer full English title without color: use style + product type from first title
        # e.g. "Arlo - Waterproof Golf Jacket"
        name = primary.get("title", style_name).split(" - ")
        if len(name) >= 2:
            name_en = f"{name[0].strip()} - {' - '.join(n.strip() for n in name[1:])}"
        else:
            name_en = style_name
        # Actually style group shares same title (color not in title) — use as-is
        name_en = primary.get("title") or style_name
        name_ko = translate_apparel(name_en)
        if english_ratio(name_ko) > 0.45:
            parts = name_en.split(" - ", 1)
            if len(parts) == 2:
                name_ko = f"{parts[0]} - {translate_apparel(parts[1])}"

        body = strip_html(primary.get("body_html") or "")
        desc_ko = compose_description_ko(
            style_name,
            primary.get("tags") or [],
            primary.get("body_html") or "",
            name_ko,
        )
        paras = paragraphs(body)
        feats = [translate_apparel(b) for b in bullet_points(body)]
        feats = [f for f in feats if f and english_ratio(f) < 0.35][:8]
        specs = tech_specs_from_tags(primary.get("tags") or [])
        for sp in specs:
            sp["labelKo"] = "소재 · 테크"

        flat_variants: list[dict] = []
        gallery_all: list[str] = []
        prices_krw: list[int] = []
        prices_gbp: list[float] = []
        compare_krw: list[int] = []
        first_sku = ""
        primary_image = ""

        for m in members_sorted:
            color = m.get("colorName") or "Default"
            color_ko = color_to_ko(color)
            color_key = slugify(color)
            imgs = local_images(m["handle"])
            if not imgs:
                # fallback to scraped urls as paths won't exist — skip remote in catalog
                imgs = []
            if imgs and not primary_image:
                primary_image = imgs[0]
            for im in imgs:
                if im not in gallery_all:
                    gallery_all.append(im)

            source = f"https://www.galvingreen.com/en-gb/products/{m['handle']}"
            for v in m.get("variants") or []:
                size = str(v.get("size") or v.get("option1") or v.get("title") or "").strip()
                gbp = float(v.get("price") or 0)
                krw = gbp_to_krw(gbp)
                available = bool(v.get("available"))
                if available or True:  # include all; price from in-stock preferred later
                    prices_krw.append(krw)
                    prices_gbp.append(gbp)
                cap = v.get("compare_at_price")
                if cap:
                    try:
                        cap_f = float(cap)
                        if cap_f > gbp:
                            compare_krw.append(gbp_to_krw(cap_f))
                    except (TypeError, ValueError):
                        pass
                sku = v.get("sku") or ""
                if not first_sku and sku:
                    first_sku = sku
                vid = slugify(f"gg-{m['handle']}-{size}")
                flat_variants.append(
                    {
                        "id": vid,
                        "name": f"{color} / {size}",
                        "nameKo": f"{color_ko} / {size}",
                        "sku": sku,
                        "gbpPrice": gbp,
                        "price": krw,
                        "image": imgs[0] if imgs else (primary_image or "/products/run-jacket.svg"),
                        "images": imgs or None,
                        "sourceUrl": source,
                        "inStock": available,
                        "colorKey": color_key,
                        "colorNameKo": color_ko,
                        "size": size,
                    }
                )

        in_stock_prices = [
            v["price"] for v in flat_variants if v.get("inStock")
        ]
        price = min(in_stock_prices) if in_stock_prices else (min(prices_krw) if prices_krw else 0)
        gbp_price = None
        for v in flat_variants:
            if v.get("inStock") and v["price"] == price:
                gbp_price = v["gbpPrice"]
                break
        if gbp_price is None and flat_variants:
            gbp_price = min(v["gbpPrice"] for v in flat_variants)

        compare_at = None
        if compare_krw:
            c = min(compare_krw)
            if c > price:
                compare_at = c

        story = []
        for i, para in enumerate(paras[:4]):
            body_ko = translate_apparel(para)
            if english_ratio(body_ko) > 0.25:
                if i == 0:
                    body_ko = desc_ko
                else:
                    continue
            story.append(
                {
                    "titleKo": name_ko if i == 0 else "디테일",
                    "bodyKo": body_ko,
                    "image": gallery_all[i] if i < len(gallery_all) else (primary_image or None),
                    "reverse": i % 2 == 1,
                }
            )
        if not story:
            story.append(
                {
                    "titleKo": name_ko,
                    "bodyKo": desc_ko,
                    "image": primary_image or None,
                }
            )
        # drop None images
        for s in story:
            if not s.get("image"):
                s.pop("image", None)

        registered = primary.get("published_at") or raw.get("scrapedAt") or now_iso
        # normalize to ISO-ish
        if isinstance(registered, str) and registered.endswith("+02:00"):
            registered = registered  # keep
        elif not registered:
            registered = now_iso

        accent = ACCENTS[len(briq_products) % len(ACCENTS)]
        if not primary_image:
            primary_image = gallery_all[0] if gallery_all else "/products/run-jacket.svg"

        product = {
            "id": pid,
            "name": name_en,
            "nameKo": name_ko,
            "brand": "Galvin Green",
            "price": price,
            "compareAtPrice": compare_at,
            "category": "sports",
            "subcategory": collection,
            "tags": ["galvin-green", collection],
            "descriptionKo": desc_ko[:1200] if desc_ko else None,
            "image": primary_image,
            "images": gallery_all[:12] or None,
            "accent": accent,
            "badge": "New",
            "gbpPrice": gbp_price,
            "sku": first_sku or None,
            "sourceUrl": f"https://www.galvingreen.com/en-gb/products/{primary['handle']}",
            "registeredAt": registered,
            "editTier": "new",
            "storySections": story or None,
            "featuresKo": feats or None,
            "techSpecs": specs or None,
            "variants": flat_variants,
        }
        briq_products.append(product)

    # Emit TypeScript
    lines = [
        "/** Auto-generated Galvin Green catalogue — do not edit by hand. */",
        'import type { Product } from "@/data/products";',
        "",
        "export const ggCatalogProducts: Product[] = [",
    ]

    for p in briq_products:
        lines.append("  {")
        lines.append(f"    id: {ts_str(p['id'])},")
        lines.append(f"    name: {ts_str(p['name'])},")
        lines.append(f"    nameKo: {ts_str(p['nameKo'])},")
        lines.append(f"    brand: {ts_str(p['brand'])},")
        lines.append(f"    price: {p['price']},")
        if p.get("compareAtPrice"):
            lines.append(f"    compareAtPrice: {p['compareAtPrice']},")
        lines.append(f"    category: {ts_str(p['category'])},")
        lines.append(f"    subcategory: {ts_str(p['subcategory'])},")
        tags_inner = ", ".join(ts_str(t) for t in p["tags"])
        lines.append(f"    tags: [{tags_inner}],")
        if p.get("descriptionKo"):
            lines.append(f"    descriptionKo: {ts_str(p['descriptionKo'])},")
        lines.append(f"    image: {ts_str(p['image'])},")
        if p.get("images"):
            imgs_inner = ", ".join(ts_str(x) for x in p["images"])
            lines.append(f"    images: [{imgs_inner}],")
        lines.append(f"    accent: {ts_str(p['accent'])},")
        lines.append(f"    badge: {ts_str(p['badge'])},")
        if p.get("gbpPrice") is not None:
            lines.append(f"    gbpPrice: {p['gbpPrice']},")
        if p.get("sku"):
            lines.append(f"    sku: {ts_str(p['sku'])},")
        if p.get("sourceUrl"):
            lines.append(f"    sourceUrl: {ts_str(p['sourceUrl'])},")
        if p.get("registeredAt"):
            lines.append(f"    registeredAt: {ts_str(p['registeredAt'])},")
        lines.append(f"    editTier: {ts_str(p['editTier'])},")

        if p.get("storySections"):
            lines.append("    storySections: [")
            for s in p["storySections"]:
                lines.append("      {")
                lines.append(f"        titleKo: {ts_str(s['titleKo'])},")
                lines.append(f"        bodyKo: {ts_str(s['bodyKo'])},")
                if s.get("image"):
                    lines.append(f"        image: {ts_str(s['image'])},")
                if s.get("reverse"):
                    lines.append("        reverse: true,")
                lines.append("      },")
            lines.append("    ],")

        if p.get("featuresKo"):
            inner = ", ".join(ts_str(x) for x in p["featuresKo"])
            lines.append(f"    featuresKo: [{inner}],")

        if p.get("techSpecs"):
            lines.append("    techSpecs: [")
            for sp in p["techSpecs"]:
                lines.append(
                    f"      {{ labelKo: {ts_str(sp['labelKo'])}, valueKo: {ts_str(sp['valueKo'])} }},"
                )
            lines.append("    ],")

        lines.append("    variants: [")
        for v in p["variants"]:
            lines.append("      {")
            lines.append(f"        id: {ts_str(v['id'])},")
            lines.append(f"        name: {ts_str(v['name'])},")
            lines.append(f"        nameKo: {ts_str(v['nameKo'])},")
            lines.append(f"        sku: {ts_str(v['sku'])},")
            lines.append(f"        gbpPrice: {v['gbpPrice']},")
            lines.append(f"        price: {v['price']},")
            lines.append(f"        image: {ts_str(v['image'])},")
            if v.get("images"):
                inner = ", ".join(ts_str(x) for x in v["images"])
                lines.append(f"        images: [{inner}],")
            lines.append(f"        sourceUrl: {ts_str(v['sourceUrl'])},")
            lines.append(f"        inStock: {'true' if v['inStock'] else 'false'},")
            lines.append(f"        colorKey: {ts_str(v['colorKey'])},")
            lines.append(f"        colorNameKo: {ts_str(v['colorNameKo'])},")
            lines.append(f"        size: {ts_str(v['size'])},")
            lines.append("      },")
        lines.append("    ],")
        lines.append("  },")

    lines.append("];")
    lines.append("")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")

    variant_total = sum(len(p["variants"]) for p in briq_products)
    return {
        "grouped": len(briq_products),
        "variants": variant_total,
        "men_raw": sum(1 for p in products if p.get("collection") == "gg-new-men"),
        "women_raw": sum(1 for p in products if p.get("collection") == "gg-new-women"),
    }


if __name__ == "__main__":
    stats = build()
    print(
        f"Built {OUT_PATH.relative_to(ROOT)} — "
        f"{stats['grouped']} products, {stats['variants']} variants "
        f"(raw men={stats['men_raw']} women={stats['women_raw']})"
    )
