#!/usr/bin/env python3
"""Build gg-catalog.ts from gg-catalog-raw.json (Galvin Green new arrivals)."""
from __future__ import annotations

import html as H
import json
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
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


def load_cw_max_registered() -> datetime | None:
    """Newest Christopher Ward Briq registration — GG should sort after this."""
    cw_path = ROOT / "src" / "data" / "cw" / "cw-catalog.ts"
    if not cw_path.exists():
        return None
    times: list[datetime] = []
    for m in re.finditer(r'registeredAt:\s*"([^"]+)"', cw_path.read_text()):
        try:
            ts = datetime.fromisoformat(m.group(1).replace("Z", "+00:00"))
        except ValueError:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        times.append(ts)
    return max(times) if times else None


def load_existing_registered() -> dict[str, str]:
    """Keep stable Briq registration times across rebuilds.

    Ignore Shopify published_at leftovers and any stamp still older than CW.
    """
    if not OUT_PATH.exists():
        return {}
    text = OUT_PATH.read_text()
    out: dict[str, str] = {}
    cw_max = load_cw_max_registered()
    floor = cw_max + timedelta(seconds=1) if cw_max else datetime(
        2026, 7, 28, 21, 0, 0, tzinfo=timezone.utc
    )
    for m in re.finditer(
        r'id:\s*"(gg-[^"]+)"[\s\S]*?registeredAt:\s*"([^"]+)"',
        text,
    ):
        raw = m.group(2)
        try:
            ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if ts >= floor:
            out[m.group(1)] = raw
    return out


def briq_registered_at(
    pid: str,
    existing: dict[str, str],
    batch_start: datetime,
    index: int,
) -> str:
    if pid in existing:
        return existing[pid]
    # New to Briq catalogue — stamp now (not Shopify published_at)
    ts = batch_start + timedelta(seconds=index)
    return ts.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "item"


def gbp_to_krw(gbp: float) -> int:
    """Galvin Green: GBP × 2100 × 1.06 + ₩20,000 (+ ₩15,000 if ≤ £100) → round to 천원."""
    base = gbp * 2100 * 1.06 + 20_000
    if gbp <= 100:
        base += 15_000
    return int(round(base / 1_000) * 1_000)


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


_TX_CACHE_PATH = ROOT / "src/data/gg/gg-translate-cache.json"
_TX_CACHE: dict[str, str] = (
    json.loads(_TX_CACHE_PATH.read_text()) if _TX_CACHE_PATH.exists() else {}
)


def polish_gg_ko(out: str) -> str:
    """Post-pass for natural Briq / Galvin Green Korean."""
    reps = [
        ("Galvin Green", "갈빈 그린"),
        ("갈빈그린", "갈빈 그린"),
        ("퍼텍스", "PERTEX®"),
        ("Pertex", "PERTEX®"),
        ("PERTEX® 방패", "PERTEX® Shield"),
        ("PERTEX® 실드", "PERTEX® Shield"),
        ("방패 기술", "Shield 테크놀로지"),
        ("Shield 기술", "Shield 테크놀로지"),
        ("DRYVR", "DRYVR™"),
        ("정기적인", "레귤러"),
        ("정규적인", "레귤러"),
        ("보통 핏", "레귤러 핏"),
        ("아트. NO", "아티클 번호"),
        ("아트 번호", "아티클 번호"),
        ("비 속에서 놀고 있지만 긴 소매는 참을 수 없나요?", "비 오는 날 라운드를 뛰는데 긴소매는 불편하신가요?"),
        ("비 속에서 놀고 있지만", "비 오는 날 플레이하는데"),
        ("소매나 소매 부분이", "소매나 커프가"),
        ("소매나 소매 부분", "소매나 커프가"),
        ("소매나 커프이", "소매나 커프가"),
        ("소매나 커프가 스윙", "소매·커프가 스윙"),
        ("커프이", "커프가"),
        ("그리고 기술", ""),
        ("및 세부정보", ""),
        ("물을 좋아하는", "친수성"),
        ("2겹 원단", "2레이어 원단"),
        ("모델 키는", "착용 모델은"),
    ]
    for a, b in reps:
        out = out.replace(a, b)
    out = re.sub(r"PERTEX®®", "PERTEX®", out)
    out = re.sub(r"DRYVR™™", "DRYVR™", out)
    if out.strip() in {"정기적인", "정규", "보통", "Regular", "regular"}:
        out = "레귤러"
    out = re.sub(r"\s{2,}", " ", out).strip()
    return out


def translate_en(text: str) -> str:
    """Google Translate (gtx) with GG term polish — same approach as CW catalog."""
    text = (text or "").strip()
    if not text:
        return ""
    if text in _TX_CACHE:
        return polish_gg_ko(_TX_CACHE[text])

    protected: dict[str, str] = {}

    def hold(m: re.Match[str]) -> str:
        k = f"⟦{len(protected)}⟧"
        protected[k] = m.group(0)
        return k

    held = re.sub(
        r"PERTEX®\s*Shield(?:\s*Technology)?|PERTEX\u00ae\s*Shield(?:\s*Technology)?|"
        r"PERTEX®|PERTEX\u00ae|INSULA™|INSULA\u2122|VENTIL8™|VENTIL8\u2122|"
        r"INTERFACE-1™|INTERFACE-1\u2122|INTERFACE™|DRYVR™|DRYVR\u2122|"
        r"C-KNIT™|GORE-TEX®|Galvin Green|"
        r"A\d{11,}",
        hold,
        text,
        flags=re.I,
    )
    try:
        q = __import__("urllib.parse").parse.quote(held[:4500])
        url = (
            "https://translate.googleapis.com/translate_a/single"
            f"?client=gtx&sl=en&tl=ko&dt=t&q={q}"
        )
        req = __import__("urllib.request").request.Request(
            url, headers={"User-Agent": "Mozilla/5.0"}
        )
        with __import__("urllib.request").request.urlopen(req, timeout=25) as r:
            data = json.loads(r.read().decode())
        out = "".join(part[0] for part in data[0] if part and part[0])
    except Exception:
        out = translate_apparel(text)
    for k, v in protected.items():
        out = out.replace(k, v)
    out = polish_gg_ko(out)
    _TX_CACHE[text] = out
    if len(_TX_CACHE) % 20 == 0:
        _TX_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _TX_CACHE_PATH.write_text(
            json.dumps(_TX_CACHE, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return out


def flush_tx_cache() -> None:
    _TX_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _TX_CACHE_PATH.write_text(
        json.dumps(_TX_CACHE, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


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
    if len(plain) >= 40:
        translated = translate_en(plain)
        if translated and english_ratio(translated) < 0.35:
            return translated
    return describe_from_tags(style, tags, name_ko)


# Prefer curated Korean for short feature chips (more natural than MT).
FEATURE_KO = {
    "Waterproof": "방수",
    "Windproof": "방풍",
    "Highly breathable": "높은 통기성",
    "Breathable": "통기성",
    "Lightweight": "경량",
    "Water repellent finish": "발수 마감",
    "Water-repellent finish": "발수 마감",
    "Recycled polyester": "재활용 폴리에스터",
    "Front pockets": "프론트 포켓",
    "Chest tabs for adjustable chest width": "가슴 너비 조절 탭",
    "Elastic drawstring at the hem": "밑단 신축 드로코드",
    "Repositioned side seam for optimum comfort": "착용감 최적화를 위한 사이드 심 재배치",
    "Stretch": "스트레치",
    "PFAS free water repellent": "PFAS-free 발수",
    "PFASfree water repellent": "PFAS-free 발수",
}


def build_content_from_pdp(
    pdp: dict | None,
    body_html: str,
    tags: list[str],
    name_ko: str,
    style_name: str,
) -> tuple[str, list[str], list[dict], list[dict]]:
    """Return descriptionKo, featuresKo, techSpecs, story section bodies (EN paras → KO)."""
    pdp = pdp or {}
    desc_en = (pdp.get("descriptionEn") or strip_html(body_html or "")).strip()
    feats_en = list(pdp.get("featuresEn") or [])
    fabric_en = list(pdp.get("fabricEn") or [])
    tech_en = (pdp.get("technologyEn") or "").strip()
    art_no = (pdp.get("artNo") or "").strip()
    fit_en = (pdp.get("fitEn") or "").strip()
    model_en = (pdp.get("modelInfoEn") or "").strip()

    if desc_en:
        desc_ko = translate_en(desc_en)
        if english_ratio(desc_ko) > 0.4:
            desc_ko = compose_description_ko(style_name, tags, body_html, name_ko)
    else:
        desc_ko = compose_description_ko(style_name, tags, body_html, name_ko)

    features_ko: list[str] = []
    for f in feats_en:
        key = f.strip().lstrip("-• ").strip()
        if key in FEATURE_KO:
            features_ko.append(FEATURE_KO[key])
            continue
        ko = translate_en(key)
        if ko and english_ratio(ko) < 0.5:
            features_ko.append(ko)
        elif key:
            ko2 = translate_apparel(key)
            features_ko.append(ko2 if english_ratio(ko2) < english_ratio(ko or key) else (ko or key))
    features_ko = [f for f in dict.fromkeys(features_ko) if f and f not in {"및 세부정보", "그리고 기술"}][:16]

    specs: list[dict[str, str]] = []
    if art_no:
        specs.append({"labelKo": "아티클 번호", "valueKo": art_no})
    if fit_en:
        fit_ko = "레귤러" if fit_en.strip().lower() == "regular" else translate_en(fit_en)
        if fit_ko.strip() in {"정기적인", "정규", "보통", "Regular", "regular"}:
            fit_ko = "레귤러"
        specs.append({"labelKo": "핏", "valueKo": fit_ko})
    if model_en:
        specs.append({"labelKo": "모델 정보", "valueKo": translate_en(model_en)})
    if fabric_en:
        fabric_ko = " · ".join(translate_en(x) if english_ratio(x) > 0.2 else x for x in fabric_en)
        # Keep brand tech tokens
        fabric_ko = polish_gg_ko(fabric_ko)
        specs.append({"labelKo": "소재", "valueKo": fabric_ko})
    if tech_en:
        specs.append({"labelKo": "테크놀로지", "valueKo": polish_gg_ko(tech_en)})
    if not specs:
        specs = tech_specs_from_tags(tags)
        for sp in specs:
            sp["labelKo"] = "소재 · 테크"

    # Story: split description into paragraphs
    paras_en = [p.strip() for p in re.split(r"\n+", desc_en) if len(p.strip()) >= 40]
    if not paras_en and desc_en:
        # Split long single paragraph into ~2 sentences chunks
        sentences = re.split(r"(?<=[.!?])\s+", desc_en)
        chunk: list[str] = []
        paras_en = []
        for s in sentences:
            chunk.append(s)
            if len(" ".join(chunk)) > 220:
                paras_en.append(" ".join(chunk))
                chunk = []
        if chunk:
            paras_en.append(" ".join(chunk))
    story_bodies = [translate_en(p) for p in paras_en[:4]]
    story_bodies = [b for b in story_bodies if b]

    return desc_ko, features_ko, specs, story_bodies


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


HANDLE_PRODUCT_TOKENS = {
    "waterproof",
    "windproof",
    "water",
    "repellent",
    "repellant",
    "breathable",
    "insulating",
    "thermal",
    "golf",
    "jacket",
    "vest",
    "pants",
    "trousers",
    "shorts",
    "shirt",
    "skirt",
    "hoodie",
    "sweatshirt",
    "mid",
    "layer",
    "base",
    "top",
    "bottom",
    "hat",
    "cap",
    "visor",
    "belt",
    "gloves",
    "neck",
    "warmer",
    "short",
    "sleeve",
    "sleeveless",
    "long",
    "half",
    "full",
    "zip",
    "uv",
    "protection",
    "with",
    "inner",
    "and",
    "for",
}


def clean_color_remainder(remainder: str) -> str | None:
    parts = [p for p in remainder.split("-") if p]
    color_parts = [p for p in parts if p not in HANDLE_PRODUCT_TOKENS]
    if not color_parts:
        return None
    if not any(p in COLOR_WORDS for p in color_parts):
        return None
    return "-".join(color_parts)


def color_from_handle_group(handles: list[str], handle: str, tags: list[str]) -> str:
    tagged = color_from_tags_ordered(handle, tags)
    suffix = color_from_handle_suffix(handle)

    if len(handles) <= 1:
        return suffix or tagged or "Default"

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
    cleaned = clean_color_remainder(remainder) if remainder else None
    if cleaned:
        return title_case_color(cleaned)
    return suffix or tagged or (title_case_color(remainder) if remainder else "Default")


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


# Scrape meta key → Briq collection id. Used to keep PLP membership exact
# (sibling-colour enrichment must not inflate Men/Women beyond official counts).
LEAF_META_TO_COLL = {
    "men-new": "gg-new-men",
    "women-new": "gg-new-women",
    "our-bestsellers-men": "gg-bestsellers-men",
    "our-bestsellers-women": "gg-bestsellers-women",
    "men": "gg-men",
    "women": "gg-women",
    "accessories": "gg-accessories",
    "outlet": "gg-sale",
}


def member_collections(p: dict) -> list[str]:
    cols = p.get("collections")
    if isinstance(cols, list) and cols:
        return [str(c) for c in cols]
    coll = p.get("collection")
    return [str(coll)] if coll else ["gg-new-men"]


def trusted_member_collections(
    p: dict, leaf_handles: dict[str, set[str]]
) -> list[str]:
    """Drop leaf PLP tags that were inherited onto colourways not in that scrape."""
    cols = member_collections(p)
    handle = str(p.get("handle") or "")
    out: list[str] = []
    for c in cols:
        allowed = leaf_handles.get(c)
        if allowed is not None and handle not in allowed:
            continue
        out.append(c)
    return out


def gender_of_collections(cols: list[str], tags: list[str] | None = None) -> str:
    if any(
        c in ("gg-new-women", "gg-bestsellers-women", "gg-women") or c.endswith("-women")
        for c in cols
    ):
        return "women"
    if any(
        c in ("gg-new-men", "gg-bestsellers-men", "gg-men") or c.endswith("-men")
        for c in cols
    ):
        return "men"
    if tags:
        lower = {t.lower() for t in tags}
        if "women" in lower or "women's" in lower:
            return "women"
        if "men" in lower or "men's" in lower:
            return "men"
    if "gg-accessories" in cols:
        return "accessories"
    return "men"


def primary_collection(cols: list[str]) -> str:
    """Prefer New Arrivals → Bestsellers → Men/Women → Accessories → Sale."""
    if not cols:
        return "gg-accessories"
    for c in cols:
        if c.startswith("gg-new-"):
            return c
    for c in cols:
        if "bestsellers" in c:
            return c
    for pref in ("gg-men", "gg-women", "gg-accessories", "gg-sale"):
        if pref in cols:
            return pref
    return cols[0]


ACCESSORY_TITLE_RE = re.compile(
    r"\b(belt|cap|hat|glove|gloves|umbrella|towel|visor|bag|neck warmer|wrist warmer)\b",
    re.I,
)


def is_accessory_group(members: list[dict], leaf_handles: dict[str, set[str]]) -> bool:
    """True when the style is accessory merchandise (belt/hat/etc.)."""
    for m in members:
        cols = trusted_member_collections(m, leaf_handles)
        if "gg-accessories" in cols:
            return True
        title = str(m.get("title") or "")
        if ACCESSORY_TITLE_RE.search(title):
            return True
    return False


def group_build_sort_key(
    item: tuple[tuple[str, str], list[dict]],
    leaf_handles: dict[str, set[str]],
) -> tuple[int, str]:
    """Accessories first (older registeredAt), apparel last (newer) for Men/Women PLPs."""
    (style_name, _gender), members = item
    return (0 if is_accessory_group(members, leaf_handles) else 1, style_name.lower())



def build() -> dict:
    raw = json.loads(RAW_PATH.read_text())
    products = raw.get("products") or []
    meta = raw.get("collections") or {}
    leaf_handles: dict[str, set[str]] = {}
    for meta_key, coll_id in LEAF_META_TO_COLL.items():
        handles = meta.get(meta_key)
        if isinstance(handles, list):
            leaf_handles[coll_id] = {str(h) for h in handles}
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    existing_reg = load_existing_registered()
    cw_max = load_cw_max_registered()
    batch_start = datetime.now(timezone.utc)
    if cw_max and batch_start <= cw_max:
        # New Arrivals CTA sorts by registeredAt — GG must land after CW
        batch_start = cw_max + timedelta(minutes=1)

    # Group by styleName + gender (New Arrivals + Bestsellers share one PDP)
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for p in products:
        style = (p.get("styleName") or p.get("title", "").split(" - ")[0]).strip()
        cols = trusted_member_collections(p, leaf_handles)
        # Sibling colourways with no trusted PLP tags still join the style PDP
        # via tags/gender, but do not appear on Men/Women/Sale grids alone.
        gender = gender_of_collections(
            cols or member_collections(p), p.get("tags") or []
        )
        groups[(style, gender)].append(p)

    briq_products: list[dict] = []
    used_ids: set[str] = set()

    for (style_name, gender), members in sorted(
        groups.items(), key=lambda item: group_build_sort_key(item, leaf_handles)
    ):
        handles = [m["handle"] for m in members]
        # Derive/refresh color names within group
        for m in members:
            m["colorName"] = color_from_handle_group(handles, m["handle"], m.get("tags") or [])

        all_cols = sorted(
            {c for m in members for c in trusted_member_collections(m, leaf_handles)},
            key=lambda c: (0 if c.startswith("gg-new-") else 1, c),
        )
        collection = primary_collection(all_cols)

        style_slug = slugify(style_name)
        pid = f"gg-{style_slug}"
        if pid in used_ids:
            pid = f"gg-{style_slug}-{gender}"
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
        pdp = primary.get("pdpCopy") or {}
        # Prefer any member that already has richer pdpCopy
        for m in members_sorted:
            if (m.get("pdpCopy") or {}).get("featuresEn") or (
                m.get("pdpCopy") or {}
            ).get("descriptionEn"):
                pdp = m["pdpCopy"]
                break

        desc_ko, feats, specs, story_bodies = build_content_from_pdp(
            pdp,
            primary.get("body_html") or "",
            primary.get("tags") or [],
            name_ko,
            style_name,
        )
        paras = paragraphs(body)

        flat_variants: list[dict] = []
        gallery_all: list[str] = []
        prices_krw: list[int] = []
        prices_gbp: list[float] = []
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
            color_cols = trusted_member_collections(m, leaf_handles)
            for v in m.get("variants") or []:
                size = str(v.get("size") or v.get("option1") or v.get("title") or "").strip()
                gbp = float(v.get("price") or 0)
                krw = gbp_to_krw(gbp)
                available = bool(v.get("available"))
                if available or True:  # include all; price from in-stock preferred later
                    prices_krw.append(krw)
                    prices_gbp.append(gbp)
                sku = v.get("sku") or ""
                if not first_sku and sku:
                    first_sku = sku
                vid = slugify(f"gg-{m['handle']}-{size}")
                compare_at_v = None
                cap = v.get("compare_at_price")
                if cap:
                    try:
                        cap_f = float(cap)
                        if cap_f > gbp:
                            compare_at_v = gbp_to_krw(cap_f)
                    except (TypeError, ValueError):
                        pass
                flat_variants.append(
                    {
                        "id": vid,
                        "name": f"{color} / {size}",
                        "nameKo": f"{color_ko} / {size}",
                        "sku": sku,
                        "gbpPrice": gbp,
                        "price": krw,
                        "compareAtPrice": compare_at_v,
                        "image": imgs[0] if imgs else (primary_image or "/products/run-jacket.svg"),
                        "images": imgs or None,
                        "hoverImage": imgs[1] if len(imgs) > 1 else None,
                        "sourceUrl": source,
                        "inStock": available,
                        "colorKey": color_key,
                        "colorNameKo": color_ko,
                        "size": size,
                        "ggCollections": color_cols,
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
        # Product-level sale badge only when the cheapest (display) price is itself on sale
        for v in flat_variants:
            if v["price"] != price:
                continue
            if not v.get("inStock") and in_stock_prices:
                continue
            cap = v.get("compareAtPrice")
            if cap and cap > price:
                compare_at = cap
                break

        story = []
        for i, body_ko in enumerate(story_bodies[:4] or [desc_ko]):
            story.append(
                {
                    "titleKo": name_ko if i == 0 else ("소재 · 테크" if i == 1 else "디테일"),
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

        registered = briq_registered_at(
            pid, existing_reg, batch_start, len(briq_products)
        )

        accent = ACCENTS[len(briq_products) % len(ACCENTS)]
        if not primary_image:
            primary_image = gallery_all[0] if gallery_all else "/products/run-jacket.svg"

        has_new = any(c.startswith("gg-new-") for c in all_cols)
        has_best = any("bestsellers" in c for c in all_cols)
        has_sale = "gg-sale" in all_cols
        if has_new:
            badge = "New"
            edit_tier = "new"
        elif has_best:
            badge = "Best"
            edit_tier = "bestseller"
        elif has_sale:
            badge = "Sale"
            edit_tier = "signature"
        else:
            badge = None
            edit_tier = "signature"

        product = {
            "id": pid,
            "name": name_en,
            "nameKo": name_ko,
            "brand": "Galvin Green",
            "price": price,
            "compareAtPrice": compare_at,
            "category": "sports",
            "subcategory": collection,
            "ggCollections": all_cols,
            "tags": ["galvin-green", *all_cols],
            "descriptionKo": desc_ko[:1200] if desc_ko else None,
            "image": primary_image,
            "images": gallery_all[:12] or None,
            "hoverImage": gallery_all[1] if len(gallery_all) > 1 else None,
            "accent": accent,
            "badge": badge,
            "gbpPrice": gbp_price,
            "sku": first_sku or None,
            "sourceUrl": f"https://www.galvingreen.com/en-gb/products/{primary['handle']}",
            "registeredAt": registered,
            "editTier": edit_tier,
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
        if p.get("ggCollections"):
            gg_inner = ", ".join(ts_str(c) for c in p["ggCollections"])
            lines.append(
                f"    ggCollections: [{gg_inner}] as Product[\"ggCollections\"],"
            )
        tags_inner = ", ".join(ts_str(t) for t in p["tags"])
        lines.append(f"    tags: [{tags_inner}],")
        if p.get("descriptionKo"):
            lines.append(f"    descriptionKo: {ts_str(p['descriptionKo'])},")
        lines.append(f"    image: {ts_str(p['image'])},")
        if p.get("images"):
            imgs_inner = ", ".join(ts_str(x) for x in p["images"])
            lines.append(f"    images: [{imgs_inner}],")
        if p.get("hoverImage"):
            lines.append(f"    hoverImage: {ts_str(p['hoverImage'])},")
        lines.append(f"    accent: {ts_str(p['accent'])},")
        if p.get("badge"):
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
            if v.get("compareAtPrice"):
                lines.append(f"        compareAtPrice: {v['compareAtPrice']},")
            lines.append(f"        image: {ts_str(v['image'])},")
            if v.get("images"):
                inner = ", ".join(ts_str(x) for x in v["images"])
                lines.append(f"        images: [{inner}],")
            if v.get("hoverImage"):
                lines.append(f"        hoverImage: {ts_str(v['hoverImage'])},")
            lines.append(f"        sourceUrl: {ts_str(v['sourceUrl'])},")
            lines.append(f"        inStock: {'true' if v['inStock'] else 'false'},")
            lines.append(f"        colorKey: {ts_str(v['colorKey'])},")
            lines.append(f"        colorNameKo: {ts_str(v['colorNameKo'])},")
            lines.append(f"        size: {ts_str(v['size'])},")
            if v.get("ggCollections"):
                gg_inner = ", ".join(ts_str(c) for c in v["ggCollections"])
                lines.append(
                    f"        ggCollections: [{gg_inner}] as Product[\"ggCollections\"],"
                )
            lines.append("      },")
        lines.append("    ],")
        lines.append("  },")

    lines.append("];")
    lines.append("")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")

    variant_total = sum(len(p["variants"]) for p in briq_products)
    def in_coll(p: dict, coll: str) -> bool:
        cols = p.get("collections") or [p.get("collection")]
        return coll in cols

    return {
        "grouped": len(briq_products),
        "variants": variant_total,
        "men_raw": sum(1 for p in products if in_coll(p, "gg-new-men")),
        "women_raw": sum(1 for p in products if in_coll(p, "gg-new-women")),
        "men_best": sum(1 for p in products if in_coll(p, "gg-bestsellers-men")),
        "women_best": sum(1 for p in products if in_coll(p, "gg-bestsellers-women")),
    }


if __name__ == "__main__":
    stats = build()
    flush_tx_cache()
    print(
        f"Built {OUT_PATH.relative_to(ROOT)} — "
        f"{stats['grouped']} products, {stats['variants']} variants "
        f"(raw new men/women={stats['men_raw']}/{stats['women_raw']} "
        f"best={stats['men_best']}/{stats['women_best']})"
    )
