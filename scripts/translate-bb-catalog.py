#!/usr/bin/env python3
"""Offline EN→KO for Burberry Women using fashion phrase dictionaries."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "src/data/bb/bb-catalog-raw.json"
CACHE_PATH = ROOT / "src/data/bb/bb-translate-cache.json"

# Longest-first.
PHRASES = [
    ("Fits true to size, take your normal size.", "정사이즈입니다. 평소 사이즈를 선택하세요."),
    ("Specialist dry clean", "전문 드라이클리닝"),
    ("Do not tumble dry", "텀블 건조 금지"),
    ("Do not bleach", "표백 금지"),
    ("Do not wash", "세탁 불가"),
    ("Do not iron", "다림질 금지"),
    ("Dry clean", "드라이클리닝"),
    ("Made in the United Kingdom", "영국 제작"),
    ("Made in England", "영국 제작"),
    ("Made in Italy", "이탈리아 제작"),
    ("Made in France", "프랑스 제작"),
    ("Made in Spain", "스페인 제작"),
    ("Made in Portugal", "포르투갈 제작"),
    ("Made in Madagascar", "마다가스카르 제작"),
    ("Product Details", "제품 상세"),
    ("Size & Fit", "사이즈 & 핏"),
    ("Fabric & Care", "소재 & 케어"),
    ("comes with a dust bag", "더스트백 포함"),
    ("Comes with a dust bag", "더스트백 포함"),
    ("Equestrian Knight Design", "에퀘스트리언 나이트 디자인"),
    ("Prince of Wales check", "프린스 오브 웨일스 체크"),
    ("Prince of Wales", "프린스 오브 웨일스"),
    ("Burberry Check", "버버리 체크"),
    ("Tropical Gabardine", "트로피컬 개버딘"),
    ("fit-and-flare", "핏앤플레어"),
    ("Fit-and-flare", "핏앤플레어"),
    ("twist-lock belt", "트위스트락 벨트"),
    ("side slip pockets", "사이드 슬립 포켓"),
    ("hook and zip closure", "훅 앤 지퍼 잠금"),
    ("Back hook and zip closure", "뒷면 훅 앤 지퍼 잠금"),
    ("Slim fit:", "슬림 핏:"),
    ("Regular fit:", "레귤러 핏:"),
    ("Relaxed fit:", "릴랙스드 핏:"),
    ("this style is cut to a fitted silhouette.", "핏한 실루엣으로 재단되었습니다."),
    ("Model’s height:", "모델 키:"),
    ("Model's height:", "모델 키:"),
    ("Model wears size", "모델 착용 사이즈"),
    ("Length:", "기장:"),
    ("Heel height:", "굽 높이:"),
    ("crafted in Italy", "이탈리아에서 제작"),
    ("woven in Italy", "이탈리아에서 제직"),
    ("handcrafted in", "핸드크래프트"),
    ("Debuted on the Burberry", "버버리"),
    ("runway", "런웨이"),
    ("Trench Coat", "트렌치 코트"),
    ("Puffer Jacket", "패딩 재킷"),
    ("Quilted Jacket", "퀼팅 재킷"),
    ("Bomber Jacket", "봄버 재킷"),
    ("Shirt Dress", "셔츠 드레스"),
    ("Polo Shirt", "폴로 셔츠"),
    ("T-shirt Dress", "티셔츠 드레스"),
    ("T-shirt", "티셔츠"),
    ("Sweatshirt", "스웨트셔츠"),
    ("Cardigan", "카디건"),
    ("Hoodie", "후디"),
    ("Blouse", "블라우스"),
    ("Blazer", "블레이저"),
    ("Jacket", "재킷"),
    ("Coat", "코트"),
    ("Cape", "케이프"),
    ("Poncho", "판초"),
    ("Dress", "드레스"),
    ("Skirt", "스커트"),
    ("Trousers", "팬츠"),
    ("Shorts", "쇼츠"),
    ("Jeans", "진"),
    ("Scarf", "스카프"),
    ("Sunglasses", "선글라스"),
    ("Backpack", "백팩"),
    ("Shoulder Bag", "숄더백"),
    ("Crossbody Bag", "크로스바디 백"),
    ("Crossbody", "크로스바디"),
    ("Tote Bag", "토트백"),
    ("Top Handle", "탑 핸들"),
    ("Mini Bag", "미니백"),
    ("Card Case", "카드 케이스"),
    ("Wallet", "지갑"),
    ("Sneakers", "스니커즈"),
    ("Sandals", "샌들"),
    ("Ballerinas", "발레리나"),
    ("Loafers", "로퍼"),
    ("Boots", "부츠"),
    ("Pumps", "펌프스"),
    ("Belt", "벨트"),
    ("Pouch", "파우치"),
    ("Bikini", "비키니"),
    ("Swimwear", "스윔웨어"),
    ("Cashmere", "캐시미어"),
    ("Gabardine", "개버딘"),
    ("Cotton", "코튼"),
    ("Wool", "울"),
    ("Silk", "실크"),
    ("Leather", "레더",),
    ("Denim", "데님"),
    ("Linen", "린넨"),
    ("Nylon", "나일론"),
    ("Check", "체크"),
    ("Quilted", "퀼팅"),
    ("Belted", "벨트"),
    ("Oversized", "오버사이즈"),
    ("Cropped", "크롭"),
    ("Sleeveless", "슬리브리스"),
    ("Long-sleeved", "롱슬리브"),
    ("Short-sleeved", "숏슬리브"),
    ("Embroidered", "자수"),
    ("Reversible", "리버시블"),
    ("Vintage", "빈티지"),
    ("Archive", "아카이브"),
    ("Tailored", "테일러드"),
    ("Structured", "스트럭처드"),
    ("Lightweight", "경량"),
    ("Stretch", "스트레치"),
    ("Grainy", "그레인한"),
    ("Softly", "부드럽게"),
    ("A pair of", ""),
    ("A pair", ""),
    ("Imported", "수입"),
    ("One size", "프리사이즈"),
    ("Burberry", "버버리"),
    ("Details", "디테일"),
]

COLORS = {
    "Black": "블랙",
    "White": "화이트",
    "Ivory": "아이보리",
    "Cream": "크림",
    "Beige": "베이지",
    "Sand": "샌드",
    "Sand beige": "샌드 베이지",
    "Brown": "브라운",
    "Navy": "네이비",
    "Navy blue": "네이비 블루",
    "Blue": "블루",
    "Red": "레드",
    "Pink": "핑크",
    "Green": "그린",
    "Olive": "올리브",
    "Grey": "그레이",
    "Gray": "그레이",
    "Silver": "실버",
    "Gold": "골드",
    "Yellow": "옐로우",
    "Orange": "오렌지",
    "Purple": "퍼플",
    "Camel": "카멜",
    "Tan": "탠",
    "Khaki": "카키",
    "Charcoal": "차콜",
    "Archive beige": "아카이브 베이지",
    "Honey": "허니",
    "Stone": "스톤",
    "Ice white": "아이스 화이트",
    "Fawn brown": "폰 브라운",
    "Mallow pink": "멜로우 핑크",
    "Saltmarsh beige": "솔트마쉬 베이지",
    "Honey beige": "허니 베이지",
    "Pale blue": "페일 블루",
    "Dark green": "다크 그린",
    "Bright red": "브라이트 레드",
}

MAT = {
    "wool": "울",
    "cotton": "코튼",
    "silk": "실크",
    "cashmere": "캐시미어",
    "linen": "린넨",
    "leather": "레더",
    "lambskin": "램스킨",
    "calf leather": "카프 레더",
    "calfskin": "카프스킨",
    "goat suede": "고트 스웨이드",
    "polyester": "폴리에스터",
    "polyamide": "폴리아미드",
    "nylon": "나일론",
    "elastane": "엘라스테인",
    "cupro": "큐프로",
    "viscose": "비스코스",
    "polyurethane": "폴리우레탄",
    "raffia": "라피아",
    "mother-of-pearl": "자개",
    "sheep leather": "시프 레더",
    "trim": "트림",
    "lining": "안감",
    "upper": "갑피",
    "sole": "밑창",
    "heel": "힐",
    "outer": "겉감",
}


def polish(text: str) -> str:
    out = text
    for a, b in [
        ("버 버리", "버버리"),
        ("가바딘", "개버딘"),
        ("원 사이즈", "프리사이즈"),
        ("  ", " "),
    ]:
        out = out.replace(a, b)
    return out.strip()


def naturalize(text: str) -> str:
    """Second pass: turn mixed EN glue into more natural Korean."""
    s = text
    glue = [
        ("woven in Italy with the ", "이탈리아에서 "),
        ("woven in Italy with a ", "이탈리아에서 "),
        ("woven in Italy with ", "이탈리아에서 "),
        ("crafted in Italy from ", "이탈리아에서 "),
        ("crafted in Italy from a ", "이탈리아에서 "),
        ("handcrafted in Madagascar", "마다가스카르에서 핸드크래프트"),
        ("printed with the ", ""),
        ("printed with a ", ""),
        ("lined in a ", "안감은 "),
        ("lined in ", "안감은 "),
        ("woven with a tonal ", ""),
        ("woven with a ", ""),
        ("woven with the ", ""),
        ("woven with ", ""),
        ("Cut to a ", ""),
        ("cut to a ", ""),
        ("cut to an ", ""),
        ("the sleeveless style is cinched at the waist with a ", "슬리브리스 스타일은 허리에 "),
        ("cinched at the waist with a ", "허리에 "),
        ("cinched at the waist with ", "허리에 "),
        (" – a nod to our timeless ", " – 타임리스한 "),
        (" a nod to our timeless ", " 타임리스한 "),
        ("silhouette, the ", "실루엣이며, "),
        ("silhouette.", "실루엣입니다."),
        (" in wool ", " 울 "),
        (" in a wool ", " 울 "),
        (" in cotton ", " 코튼 "),
        (" in silk ", " 실크 "),
        (" in leather ", " 레더 "),
        (" in stretch ", " 스트레치 "),
        (" in a ", " "),
        (" in an ", " "),
        (" from stretch ", " 스트레치 "),
        (" from grainy ", " 그레인한 "),
        (" from ", " "),
        (" with a ", " "),
        (" with the ", " "),
        (" with ", " "),
        (" and ", " 및 "),
        (" the ", " "),
        (" The ", " "),
        (" this style ", " 이 스타일 "),
        (" this jacket ", " 이 재킷 "),
        (" this dress ", " 이 드레스 "),
        (" features ", "에는 "),
        (" featuring ", ""),
        (" set on a ", " "),
        (" made from ", ""),
        (" Made from ", ""),
        (" to a fitted silhouette", " 핏한 실루엣으로"),
        (" Fits true to size, take your normal size.", " 정사이즈입니다. 평소 사이즈를 선택하세요."),
        (" Model wears size ", " 모델 착용 사이즈 "),
        (" Model’s height: ", " 모델 키: "),
        (" Model's height: ", " 모델 키: "),
        ("Length: ", "기장: "),
        ("Heel height: ", "굽 높이: "),
        ("blend ", "블렌드 "),
        ("tonal ", ""),
        ("softly structured ", "부드럽게 스트럭처드한 "),
        ("mid-length ", "미디 기장 "),
        ("half-canvas construction", "하프 캔버스 구조"),
        ("slim fit", "슬림 핏"),
        ("A-line shape", "A라인 실루엣"),
        ("Cotswolds tote", "코츠월즈 토트"),
        ("our heritage styles", "헤리티지 스타일"),
        ("Inspired by ", ""),
        ("Debuted on the 버버리 Summer ", "버버리 썸머 "),
        ("Debuted on the 버버리 ", "버버리 "),
        (" runway,", " 런웨이에서 선보인,"),
        (" runway.", " 런웨이에서 선보였습니다."),
    ]
    for a, b in glue:
        s = s.replace(a, b)
    s = re.sub(r"\s{2,}", " ", s).strip()
    s = s.replace(" .", ".").replace(" ,", ",")
    # Prefer Korean sentence ending for description-like text
    hangul = sum(1 for c in s if "\uac00" <= c <= "\ud7a3")
    if hangul >= 8 and s.endswith(".") and not s.endswith(("니다.", "세요.", "습니다.", "요.")):
        s = s[:-1] + "입니다."
    return polish(s)


def translate_material(text: str) -> str:
    s = text

    def repl(m: re.Match) -> str:
        pct, fiber = m.group(1), m.group(2).strip().lower()
        return f"{MAT.get(fiber, fiber)} {pct}%"

    for en, ko in sorted(MAT.items(), key=lambda x: -len(x[0])):
        s = re.sub(rf"(?i)\b{re.escape(en)}\b", ko, s)
    s = re.sub(
        r"(?i)(\d+)\s*%\s*([a-z][a-z\s\-]*?[a-z])(?=\s*(?:,|/|#|$))",
        repl,
        s,
    )
    return polish(s.replace(" #", " · ").replace("#", " · "))


def translate_text(text: str) -> str:
    if not text:
        return ""
    s = text.strip()
    if re.match(r"(?i)^item\s+\d+", s):
        return re.sub(r"(?i)^item\s+", "품번 ", s)
    if re.fullmatch(r"\d+\s*ml", s, re.I):
        return s.lower().replace(" ", "")
    if s in COLORS:
        return COLORS[s]
    for en, ko in sorted(COLORS.items(), key=lambda x: -len(x[0])):
        if s.lower() == en.lower():
            return ko

    # material-ish
    if re.search(r"\d+\s*%", s) or any(
        w in s.lower() for w in ("lining", "upper", "trim", "sole", "heel", "outer")
    ):
        return translate_material(s)

    out = s
    for en, ko in PHRASES:
        out = re.sub(rf"(?<![A-Za-z]){re.escape(en)}(?![A-Za-z])", ko, out, flags=re.I)

    out = re.sub(r"^A\s+", "", out)
    out = re.sub(r"^An\s+", "", out)
    out = naturalize(out)
    return polish(out)


def main() -> None:
    raw = json.loads(RAW_PATH.read_text())
    prev = {}
    if CACHE_PATH.exists():
        prev = json.loads(CACHE_PATH.read_text())

    cache: dict[str, str] = {}
    # keep previous good Korean translations (contain hangul and differ from source)
    for k, v in prev.items():
        if v and v != k and any("\uac00" <= c <= "\ud7a3" for c in v):
            cache[k] = polish(v.replace("Burberry", "버버리"))

    strings: set[str] = set()
    for p in raw.get("products") or []:
        for key in ("title", "color", "description", "measurements", "materialComposition"):
            val = p.get(key)
            if not val:
                continue
            if key == "description":
                for part in str(val).split("##"):
                    if part.strip():
                        strings.add(part.strip())
            else:
                strings.add(str(val).strip())
        for acc in p.get("accordion") or []:
            if acc.get("label"):
                strings.add(acc["label"].strip())
            for text in acc.get("texts") or []:
                for piece in str(text).split("#"):
                    if piece.strip():
                        strings.add(piece.strip())

    for s in sorted(strings):
        # Always regenerate from dictionaries so naturalize improvements apply.
        # Keep prior MT only when it is already mostly Korean.
        prev_v = cache.get(s)
        if prev_v and sum(1 for c in prev_v if "\uac00" <= c <= "\ud7a3") > len(prev_v) * 0.35:
            cache[s] = naturalize(prev_v)
        else:
            cache[s] = translate_text(s)

    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2))
    # quality peek
    sample_keys = [k for k in cache if "Belted Check Wool Dress" in k or k.startswith("A tailored")]
    print(f"Wrote {CACHE_PATH} entries={len(cache)}")
    for k in sample_keys[:3]:
        print(" ·", k[:70], "=>", cache[k][:110])


if __name__ == "__main__":
    main()
