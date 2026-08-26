#!/usr/bin/env python3
"""Build pr-fine-jewelry-ko-copy.json with fluent KO and en_ratio <= 0.30."""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "src/data/pr/pr-fine-jewelry-catalog-raw.json"
OUT = ROOT / "src/data/pr/pr-fine-jewelry-ko-copy.json"
MAX_EN_RATIO = 0.30

# ── helpers ──────────────────────────────────────────────────────────────────

def en_ratio(s: str) -> float:
    if not s:
        return 0.0
    lat = len(re.findall(r"[A-Za-z]", s))
    return lat / max(len(s.replace(" ", "")), 1)


def gtx(text: str) -> str:
    q = urllib.parse.quote(text[:4500])
    url = (
        "https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl=en&tl=ko&dt=t&q={q}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "briq-pr-fj-ko-build"})
    with urllib.request.urlopen(req, timeout=90) as r:
        data = json.load(r)
    return "".join(p[0] for p in data[0] if p[0]).strip()


def postprocess_ko(text: str) -> str:
    """Normalize brand/collection terms after machine translation."""
    repl = [
        (r"프라다\s*컷", "프라다 컷"),
        (r"Prada Cut", "프라다 컷"),
        (r"Prada", "프라다"),
        (r"Eternal Gold", "이터널 골드"),
        (r"Couleur Vivante", "쿨레르 비반트"),
        (r"Mario Prada", "마리오 프라다"),
        (r"Aura Blockchain", "아우라 블록체인"),
        (r"laboratory[- ]grown", "랩 그로운"),
        (r"lab[- ]created", "랩 그로운"),
        (r"lab[- ]made", "랩 메이드"),
        (r"yellow gold", "옐로우 골드"),
        (r"white gold", "화이트 골드"),
        (r"rose gold", "로즈 골드"),
        (r"pink gold", "핑크 골드"),
        (r"mother-of-pearl", "마더 오브 펄"),
        (r"mother of pearl", "마더 오브 펄"),
        (r"pavé", "파베"),
        (r"pave", "파베"),
        (r"18\s*karat", "18K"),
        (r"18\s*kt", "18K"),
        (r"\(18K\)", "(18K)"),
    ]
    out = text
    for pat, ko in repl:
        out = re.sub(pat, ko, out, flags=re.I)
    out = re.sub(r"\s+", " ", out).strip()
    return out


# ── title translation ────────────────────────────────────────────────────────

COLLECTION_KO = {
    "Eternal Gold": "이터널 골드",
    "Couleur Vivante": "쿨레르 비반트",
    "Small Eternal Gold": "스몰 이터널 골드",
}

PRODUCT_PHRASES = [
    ("Eternal mini triangle pendant necklace", "이터널 미니 트라이앵글 펜던트 네크리스"),
    ("micro triangle pendant necklace", "마이크로 트라이앵글 펜던트 네크리스"),
    ("mini triangle pendant necklace", "미니 트라이앵글 펜던트 네크리스"),
    ("large pendant necklace", "라지 펜던트 네크리스"),
    ("small pendant necklace", "스몰 펜던트 네크리스"),
    ("pendant necklace", "펜던트 네크리스"),
    ("chain necklace", "체인 네크리스"),
    ("multi-coil snake bracelet", "멀티 코일 스네이크 팔찌"),
    ("multi-coil bracelet", "멀티 코일 팔찌"),
    ("bangle bracelet", "뱅글 팔찌"),
    ("cuff bracelet", "커프 팔찌"),
    ("snake bracelet", "스네이크 팔찌"),
    ("pendant earrings", "펜던트 이어링"),
    ("medium drop earrings", "미디엄 드롭 이어링"),
    ("small drop earrings", "스몰 드롭 이어링"),
    ("stud earrings", "스터드 이어링"),
    ("single pendant earring", "싱글 펜던트 이어링"),
    ("single earring", "싱글 이어링"),
    ("medium earrings", "미디엄 이어링"),
    ("solitaire ring", "솔리테어 링"),
    ("contrarié ring", "콘트라리에 링"),
    ("snake mini ring", "스네이크 미니 링"),
    ("snake ring", "스네이크 링"),
    ("chain ring", "체인 링"),
    ("nano triangle mono earring", "나노 트라이앵글 모노 이어링"),
    ("small triangle brooch", "스몰 트라이앵글 브로치"),
    ("triangle brooch", "트라이앵글 브로치"),
    ("Bow bangle bracelet", "보우 뱅글 팔찌"),
    ("Bow pendant necklace", "보우 펜던트 네크리스"),
    ("Bow bracelet", "보우 팔찌"),
    ("Bow earrings", "보우 이어링"),
    ("Bow headband", "보우 헤드밴드"),
    ("Bow ring", "보우 링"),
    ("Bow brooch", "보우 브로치"),
    ("Nano Heart single earring", "나노 하트 싱글 이어링"),
    ("Nano Heart necklace", "나노 하트 네크리스"),
    ("choker with large pendant", "라지 펜던트 초커"),
    ("choker with medium pendant", "미디엄 펜던트 초커"),
    ("necklace in rose gold with mini triangle pendant", "미니 트라이앵글 펜던트 로즈 골드 네크리스"),
    ("necklace in rose gold with nano triangle pendant", "나노 트라이앵글 펜던트 로즈 골드 네크리스"),
    ("Pop Charms necklace with pendants", "팝 참 펜던트 네크리스"),
    ("Pop Charms necklace with pendant", "팝 참 펜던트 네크리스"),
    ("Pop Charms pendants", "팝 참 펜던트"),
    ("Pop Charms", "팝 참"),
    ("brooch", "브로치"),
    ("bracelet", "팔찌"),
    ("necklace", "네크리스"),
    ("earrings", "이어링"),
    ("choker", "초커"),
    ("ring", "링"),
    ("pendants", "펜던트"),
]

METAL_KO = {
    "yellow gold": "옐로우 골드",
    "white gold": "화이트 골드",
    "rose gold": "로즈 골드",
    "Yellow gold": "옐로우 골드",
}

STONE_KO = {
    "laboratory-grown diamonds": "랩 그로운 다이아몬드",
    "laboratory-grown diamond": "랩 그로운 다이아몬드",
    "laboratory grown diamonds": "랩 그로운 다이아몬드",
    "laboratory grown diamond": "랩 그로운 다이아몬드",
    "pavé diamonds": "파베 다이아몬드",
    "pavé diamond": "파베 다이아몬드",
    "mother-of-pearl": "마더 오브 펄",
    "morganites": "모가나이트",
    "morganite": "모가나이트",
    "aquamarines": "아쿠아마린",
    "aquamarine": "아쿠아마린",
    "citrines": "시트린",
    "citrine": "시트린",
    "peridots": "페리도트",
    "peridot": "페리도트",
    "amethysts": "자수정",
    "amethyst": "자수정",
    "diamonds": "다이아몬드",
    "diamond": "다이아몬드",
}


def translate_stones(s: str) -> str:
    out = s
    for en, ko in sorted(STONE_KO.items(), key=lambda x: -len(x[0])):
        out = re.sub(rf"\b{re.escape(en)}\b", ko, out, flags=re.I)
    out = re.sub(r"\band\b", "·", out, flags=re.I)
    out = re.sub(r"\bwith\b", "", out, flags=re.I)
    out = re.sub(r"\s+", " ", out).strip(" ·")
    return out


def title_ko(en: str) -> str:
    s = en.strip()
    for col_en, col_ko in sorted(COLLECTION_KO.items(), key=lambda x: -len(x[0])):
        if s.startswith(col_en):
            s = col_ko + " " + s[len(col_en) :].strip()
            break
    extra = [
        ("necklace in rose gold with mini triangle pendant", "미니 트라이앵글 펜던트 로즈 골드 네크리스"),
        ("necklace in rose gold with nano triangle pendant", "나노 트라이앵글 펜던트 로즈 골드 네크리스"),
        ("Nano Heart single earring", "나노 하트 싱글 이어링"),
        ("Nano Heart necklace", "나노 하트 네크리스"),
        ("choker with large pendant", "라지 펜던트 초커"),
        ("choker with medium pendant", "미디엄 펜던트 초커"),
        ("mini triangle pendant", "미니 트라이앵글 펜던트"),
        ("nano triangle pendant", "나노 트라이앵글 펜던트"),
        ("large pendant", "라지 펜던트"),
        ("medium pendant", "미디엄 펜던트"),
        ("Nano Heart", "나노 하트"),
    ]
    for a, b in extra:
        s = re.sub(re.escape(a), b, s, flags=re.I)
    for prod_en, prod_ko in PRODUCT_PHRASES:
        s = re.sub(rf"\b{re.escape(prod_en)}\b", prod_ko, s, flags=re.I)
    for m_en, m_ko in METAL_KO.items():
        s = re.sub(rf"\b{re.escape(m_en)}\b", m_ko, s, flags=re.I)
    for st_en, st_ko in sorted(STONE_KO.items(), key=lambda x: -len(x[0])):
        s = re.sub(rf"\b{re.escape(st_en)}\b", st_ko, s, flags=re.I)
    for a, b in [("Eternal mini", "미니"), ("Bow", "보우")]:
        s = re.sub(re.escape(a), b, s, flags=re.I)
    s = re.sub(r"\s*-\s*", " · ", s)
    s = re.sub(r"\bin\b", "", s, flags=re.I)
    s = re.sub(r"\bwith\b", "", s, flags=re.I)
    s = re.sub(r"\band\b", "·", s, flags=re.I)
    s = re.sub(r"\s+", " ", s).strip(" ·")
    return s


# ── detail translation ───────────────────────────────────────────────────────

DETAIL_RULES: dict[str, str] = {
    "Adjustable length": "길이 조절 가능",
    "Adjustable size": "사이즈 조절 가능",
    "Available in different sizes": "다양한 사이즈 제공",
    "Box clasp with button": "박스 클래스프(버튼)",
    "Box clasp with push button": "박스 클래스프(푸시 버튼)",
    "Box clasp with push-button": "박스 클래스프(푸시 버튼)",
    "Clasp closure": "클래스프 여밈",
    "Consult the Size Guide to find your size": "사이즈는 사이즈 가이드를 참고해 주세요.",
    "Consult the Size Guide to find your size materials": "사이즈는 사이즈 가이드를 참고해 주세요.",
    "See the Size Guide to find your size": "사이즈는 사이즈 가이드를 참고해 주세요.",
    "Double button clasp": "더블 버튼 클래스프",
    "Double push-button clasp": "더블 푸시 버튼 클래스프",
    "For pierced ears": "피어싱 전용",
    "Heart pendant with logo": "로고 하트 펜던트",
    "Hidden clasp": "히든 클래스프",
    "Hinged clasp": "힌지 클래스프",
    "Hinged closure": "힌지 클로저",
    "Laboratory Grown Diamonds": "랩 그로운 다이아몬드",
    "Laser-cut logo on clasp": "클래스프 레이저 컷 로고",
    "Laser-cut logo on the back": "뒷면 레이저 컷 로고",
    "Laser-cut logo on the clasp": "클래스프 레이저 컷 로고",
    "Laser-cut logo on the inside": "내부 레이저 컷 로고",
    "Laser-cut logo on the side": "측면 레이저 컷 로고",
    "Laser-engraved logo": "레이저 각인 로고",
    "Laser-engraved logo on medal": "메달 레이저 각인 로고",
    "Laser-engraved logo on the back": "뒷면 레이저 각인 로고",
    "Laser-engraved logo on the side": "측면 레이저 각인 로고",
    "Lobster claw clasp": "랍스터 클로 클래스프",
    "Lobster claw clasp with logo-engraved medal": "로고 각인 메달 랍스터 클로 클래스프",
    "Logo lasered on the back": "뒷면 레이저 각인 로고",
    "Logo lasered on the side": "측면 레이저 각인 로고",
    "Logo on charm": "참 로고",
    "Logo on medallion": "메달리온 로고",
    "Logo-engraved medal": "로고 각인 메달",
    "Made in Italy": "이탈리아 제조",
    "Pin closure on the back": "뒷면 핀 클로저",
    "Prada Cut amethyst": "프라다 컷 자수정",
    "Prada Cut aquamarine": "프라다 컷 아쿠아마린",
    "Prada Cut aquamarines": "프라다 컷 아쿠아마린",
    "Prada Cut morganite": "프라다 컷 모가나이트",
    "Prada Cut peridot": "프라다 컷 페리도트",
    "Prada Cut peridots": "프라다 컷 페리도트",
    "Prada Cut stones": "프라다 컷 스톤",
    "Push-button box clasp": "푸시 버튼 박스 클래스프",
    "Push-button clasp": "푸시 버튼 클래스프",
    "Suiffé amethysts": "스위페 컷 자수정",
    "Suiffé aquamarines": "스위페 컷 아쿠아마린",
    "Suiffé citrines": "스위페 컷 시트린",
    "Suiffé peridots": "스위페 컷 페리도트",
    "Triangle logo": "트라이앵글 로고",
    "Velvet ribbon with gold triangle tips": "골드 트라이앵글 팁 벨벳 리본",
    "Velvet ribbon with gold-tipped ends": "골드 팁 벨벳 리본",
    "Visible lasered logo": "레이저 각인 로고",
    "Visible logo": "로고 디테일",
    "Visible logo on the chain links": "체인 링크 로고",
    "Visible logo on the links": "링크 로고",
    "Visible logo on the triangle": "트라이앵글 로고",
    "Visible triangle logo": "트라이앵글 로고",
    "Each step of Prada's responsible gold and diamond production chain is verified and traceable thanks to Aura Blockchain technology": "프라다의 책임 있는 골드·다이아몬드 생산 공정의 모든 단계는 아우라 블록체인 기술로 검증·추적됩니다.",
    "Each step of Prada's responsible gold and diamond production chain is verified and traceable thanks to Aura Blockchain technology.": "프라다의 책임 있는 골드·다이아몬드 생산 공정의 모든 단계는 아우라 블록체인 기술로 검증·추적됩니다.",
    "Each step of Prada's responsible gold and diamond production is verified and traceable thanks to Aura Blockchain technology.": "프라다의 책임 있는 골드·다이아몬드 생산의 모든 단계는 아우라 블록체인 기술로 검증·추적됩니다.",
    "Each step of the production chain responsible for gold and diamonds of Prada is verified and traceable thanks to the Aura Blockchain technology": "프라다 골드·다이아몬드 생산 공정의 모든 단계는 아우라 블록체인 기술로 검증·추적됩니다.",
    "The number and total carat weight of diamonds vary depending on the size": "다이아몬드 개수와 총 캐럿은 사이즈에 따라 달라질 수 있습니다.",
    "The number and total carat weight of the diamonds varies depending on the size": "다이아몬드 개수와 총 캐럿은 사이즈에 따라 달라질 수 있습니다.",
    "The number and total carat weight of the diamonds vary depending on the cut": "다이아몬드 개수와 총 캐럿은 컷에 따라 달라질 수 있습니다.",
    "The number and total carat weight of the diamonds vary depending on the size": "다이아몬드 개수와 총 캐럿은 사이즈에 따라 달라질 수 있습니다.",
    "Semi-precious stones: Mother of pearl - Weight: 1.01 ct": "준보석: 마더 오브 펄 · 중량: 1.01 ct",
}


def translate_material_line(s: str) -> str:
    out = s
    repl = [
        (r"750 Yellow Gold", "750 옐로우 골드"),
        (r"750 White Gold", "750 화이트 골드"),
        (r"750 Rose Gold", "750 로즈 골드"),
        (r"750 Pink Gold", "750 핑크 골드"),
        (r"\(18\s*kt\)", "(18K)"),
        (r"\(18kt\)", "(18K)"),
        (r"Prada Cut Laboratory[- ]Grown Diamond", "프라다 컷 랩 그로운 다이아몬드"),
        (r"Prada Cut Laboratory[- ]Grown Diamonds", "프라다 컷 랩 그로운 다이아몬드"),
        (r"Laboratory[- ]Grown Diamonds", "랩 그로운 다이아몬드"),
        (r"Laboratory Grown Diamonds", "랩 그로운 다이아몬드"),
        (r"Prada Cut Laboratory-Grown Diamond", "프라다 컷 랩 그로운 다이아몬드"),
        (r"Prada Cut Laboratory-Grown Diamonds", "프라다 컷 랩 그로운 다이아몬드"),
        (r"mother-of-pearl", "마더 오브 펄"),
        (r"\bwith diamonds\b", "다이아몬드"),
        (r"\bwith\b", "·"),
        (r"\band\b", "·"),
        (r"morganites", "모가나이트"),
        (r"aquamarines", "아쿠아마린"),
        (r"peridots", "페리도트"),
        (r"amethysts", "자수정"),
        (r"citrines", "시트린"),
        (r"morganite", "모가나이트"),
        (r"aquamarine", "아쿠아마린"),
        (r"peridot", "페리도트"),
        (r"amethyst", "자수정"),
        (r"citrine", "시트린"),
        (r"diamonds gold", "다이아몬드"),
        (r"Total carats:", "총 캐럿:"),
        (r"Total Carats:", "총 캐럿:"),
        (r"circa", "약"),
    ]
    for pat, ko in repl:
        out = re.sub(pat, ko, out, flags=re.I)
    out = re.sub(r"\s+", " ", out).strip()
    return out


def translate_diamond_spec(s: str) -> str:
    out = s.lstrip("-").strip()
    repl = [
        (r"Diamonds?:", "다이아몬드:"),
        (r"Total carats:", "총 캐럿:"),
        (r"Cut:", "컷:"),
        (r"Color:", "컬러:"),
        (r"Clarity:", "투명도:"),
        (r"\bRound\b", "라운드"),
        (r"\bbrilliant\b", "브릴리언트"),
        (r"\bdiamonds?\b", "다이아"),
    ]
    for pat, ko in repl:
        out = re.sub(pat, ko, out, flags=re.I)
    return out.strip()


def translate_dimension(s: str) -> str:
    out = s
    repl = [
        (r"Heart pendant, height", "하트 펜던트 높이"),
        (r"Triangle pendant, length", "트라이앵글 펜던트 길이"),
        (r"Triangle pendant, width", "트라이앵글 펜던트 너비"),
        (r"Triangle pendant:", "트라이앵글 펜던트:"),
        (r"Length", "길이"),
        (r"adjustable to", "조절"),
        (r"and", "·"),
        (r"inches", "인치"),
        (r"height", "높이"),
        (r"width", "너비"),
    ]
    for pat, ko in repl:
        out = re.sub(pat, ko, out, flags=re.I)
    return out.strip()


def detail_ko(en: str) -> str:
    s = en.strip()
    if s in DETAIL_RULES:
        return DETAIL_RULES[s]
    if re.match(r"^Gold\s*750$", s, re.I):
        return "750 골드"
    if s in {"Gold 750", "Gold750"}:
        return "750 골드"
    if s.startswith("-Diamond") or s.startswith("Diamond"):
        return translate_diamond_spec(s)
    if re.match(r"750 ", s):
        return translate_material_line(s)
    if re.match(r"Total [Cc]arats:", s):
        return translate_material_line(s)
    if "cm (" in s or "pendant" in s.lower() and "cm" in s:
        return translate_dimension(s)
    return translate_material_line(s)


# ── color translation ────────────────────────────────────────────────────────

COLOR_PARTS = {
    "Gold": "골드",
    "Rose Gold": "로즈 골드",
    "White Gold": "화이트 골드",
    "White": "화이트",
    "Mop": "마더 오브 펄",
    "Amethyst": "자수정",
    "Aquamarine": "아쿠아마린",
    "Peridot": "페리도트",
    "Morganite": "모가나이트",
    "Citrine": "시트린",
    "Pink": "핑크",
}


def color_ko(en: str) -> str:
    s = en.strip()
    mapping = {
        "Gold/White": "골드/화이트",
        "Gold": "골드",
        "Rose Gold/White": "로즈 골드/화이트",
        "White Gold/ White": "화이트 골드/화이트",
        "White Gold": "화이트 골드",
        "Rose Gold": "로즈 골드",
        "Gold/Aquamarine/Peridot": "골드/아쿠아마린/페리도트",
        "Gold/Peridot/Amethyst": "골드/페리도트/자수정",
        "Gold/Morganite/Aquamarine": "골드/모가나이트/아쿠아마린",
        "Gold/Morganite/Citrine": "골드/모가나이트/시트린",
        "Gold Pink/Mop/White": "골드/핑크/마더 오브 펄/화이트",
        "Gold/Morganite": "골드/모가나이트",
        "Gold/Amethyst": "골드/자수정",
        "Gold/Aquamarine": "골드/아쿠아마린",
        "Gold/Peridot": "골드/페리도트",
        "Gold/Aquamarine/White/Peridot": "골드/아쿠아마린/화이트/페리도트",
        "Gold/Peridot/White/Amethyst": "골드/페리도트/화이트/자수정",
        "Gold/Aquamarine/White/Morganite": "골드/아쿠아마린/화이트/모가나이트",
    }
    return mapping.get(s, s)


# ── description templates ─────────────────────────────────────────────────────

CV = "프라다 파인 주얼리 쿨레르 비반트 컬렉션"
EG = "이터널 골드"
TRI_OPEN = (
    "끊임없이 진화하는 상징, 트라이앵글은 프라다의 이분법적이고 언컨벤셔널한 정신을 담아내며 "
    "언제나 새롭고 놀라운 해석을 가능하게 합니다."
)
CV_COLOR = (
    "탁월한 색채 가치로 선정된 컬러 젬이 주인공인 "
    f"{CV}."
)
CV_EXPLORE = (
    f"{CV}은 절대적인 컬러, 조각적인 라인, 대비를 탐구합니다."
)
CV_DICHO = (
    f"이분법, 하모니, 대비 — {CV}은 새로운 컬러 언어를 탐구합니다."
)
EG_REDEFINE = (
    f"{EG} 주얼리는 과학, 기술 혁신, 장인 전통이 어우러진 유니크한 창작으로 "
    "파인 주얼리의 규칙을 재정의합니다."
)
SNAKE_OPEN = (
    "프라다는 상반된 아이디어를 결합하며, 과거와 현재, 새로움과 앤티크 사이에서 "
    "미적 표현의 접점을 찾고 패러독스의 개념을 가지고 놀습니다."
)
BOW_OPEN = "주얼리 아키타입의 재발견은 보우의 모던한 해석으로 이어집니다."


def desc_ko(en: str) -> str:
    s = en.strip()
    # Exact overrides loaded from companion module if present
    try:
        from pr_fine_jewelry_ko_descriptions import DESCRIPTIONS_KO  # noqa: WPS433

        if s in DESCRIPTIONS_KO:
            return DESCRIPTIONS_KO[s]
    except ImportError:
        pass

    if s.startswith("A continuously evolving symbol"):
        if "necklace made of recycled white gold" in s:
            return (
                f"{TRI_OPEN} 1913년 마리오 프라다가 처음 선보인 아이코닉한 기하학적 형태가 "
                "리사이클드 화이트 골드 네크리스의 구조적 요소가 됩니다. 강인하면서도 컨텨포러리한 "
                "라인의 체인 네크리스는 새로운 패턴의 파베 다이아몬드로 장식되어, 반짝이는 빛의 "
                "독특한 효과를 연출합니다."
            )
        if "bracelet made of recycled yellow gold with an original cut" in s:
            return (
                f"{TRI_OPEN} 1913년 마리오 프라다가 선보인 아이코닉한 기하학적 형태가 "
                "오리지널 컷의 리사이클드 옐로우 골드 팔찌를 구성합니다. 클래식 커프 팔찌를 "
                "세련되고 컨템포러리한 라인으로 재해석하여 조각적인 디자인으로 탈바꿈했습니다."
            )
        if "single earring made of recycled white gold" in s:
            return (
                f"{TRI_OPEN} 1913년 마리오 프라다가 처음 선보인 아이코닉 트라이앵글이 "
                "리사이클드 화이트 골드 싱글 이어링의 실루엣에 담겼습니다. 컨템포러리한 라인의 "
                "주얼은 혁신적인 기법의 파베 다이아몬드로 장식되어 반짝이는 빛의 독특한 효과를 선사합니다."
            )
        if "single earring made of recycled yellow gold" in s:
            return (
                f"{TRI_OPEN} 1913년 마리오 프라다가 처음 선보인 아이코닉 트라이앵글이 "
                "리사이클드 옐로우 골드 싱글 이어링의 실루엣에 담겼습니다. 컨템포러리한 라인의 "
                "주얼은 혁신적인 기법의 파베 다이아몬드로 장식되어 반짝이는 빛의 독특한 효과를 선사합니다."
            )
        if "embossed pattern" in s and "yellow gold" in s:
            return (
                f"{TRI_OPEN} 아이코닉한 기하학적 형태가 엠보싱 패턴으로 변모하여 "
                "리사이클드 옐로우 골드 뱅글 팔찌를 특징짓습니다. 스파클링 파베 다이아몬드와 "
                "히든 클래스프로 완성된 독창적이고 세련된 주얼입니다."
            )

    if s.startswith("A pavé of diamonds covers"):
        return (
            "다이아몬드 파베가 아이코닉 트라이앵글의 표면을 덮으며, 우아함과 모던함, 혁신, "
            "그리고 프라다 특유의 장인 정신을 표현합니다. 브랜드 탄생 이래 이어져 온 로고를 "
            "슬릭한 라인과 세련된 캐릭터로 다시 제안하는 파인 주얼리 컬렉션입니다."
        )

    if s.startswith("A pavé of diamonds embellishes"):
        base = (
            "1913년 마리오 프라다의 스티머 트렁크 홀마크로 처음 등장한 아이코닉 트라이앵글의 "
            "표면을 다이아몬드 파베가 장식하고 빛을 더합니다. 병치된 다이아몬드가 "
            "리사이클드 옐로우 골드 뱅글 팔찌 위에서 오리지널한 빛의 연출을 만들어냅니다."
        )
        if "hidden hinge clasp" in s:
            return base + " 히든 힌지 클래스프로 기능적이면서도 세련된 착용감을 완성합니다."
        return base + " 팁에 세팅된 다이아몬드가 주얼 디자인을 한층 돋보이게 합니다."

    if "A sophisticated design distinguishes this ring in recycled yellow gold" in s:
        return (
            "세련된 디자인이 주얼리 컬렉션의 리사이클드 옐로우 골드 링을 돋보이게 합니다. "
            "모던하고 혁신적인 톤은 과거와 현재를 우아한 디테일로 잇는 프라다의 듀얼 소울을 강조합니다."
        )
    if "rose gold ring from the fine jewelry" in s:
        return (
            "세련된 디자인이 파인 주얼리 컬렉션의 로즈 골드 링을 특징짓습니다. "
            "프레셔스 다이아몬드가 트라이앵글의 세 모서리를 밝혀 예상치 못한 빛의 연출을 만들어냅니다."
        )
    if "yellow gold ring from the fine jewelry" in s:
        return (
            "세련된 디자인이 파인 주얼리 컬렉션의 옐로우 골드 링을 특징짓습니다. "
            "프레셔스 다이아몬드가 트라이앵글의 세 모서리를 밝혀 예상치 못한 빛의 연출을 만들어냅니다."
        )

    if s.startswith("A subtle play of contrasts"):
        return (
            "섬세한 대비와 상징적 레퍼런스가 리사이클드 옐로우 골드 이어링의 디자인을 이룹니다. "
            "혁신과 장인적 탁월함의 대화가 체인의 재해석을 이끌어내며, 프라다 아이덴티티의 "
            "내재된 이분법을 표현합니다."
        )

    if s.startswith("An unexpected aesthetic combination") or s.startswith("An unexpected aesthetic mix"):
        if "ring made of recycled yellow gold" in s and "triangle logo" in s:
            return (
                "팝 아트의 표현력과 인더스트리얼 형태가 섞여 사랑의 보편적 상징을 새롭게 해석합니다. "
                "리사이클드 옐로우 골드 하트 링은 트라이앵글 로고로 완성되어 "
                "프라다의 듀얼리스트 정신을 강조합니다."
            )
        if "oversized pendant" in s:
            return (
                "팝 아트의 표현력과 인더스트리얼 형태가 섞여 사랑의 보편적 상징을 새롭게 해석합니다. "
                "오버사이즈 리사이클드 옐로우 골드 하트 펜던트는 벨벳 리본과 함께하며, "
                "하트 상단의 둥근 형태와 하단의 트라이앵글 라인이 예상치 못한 믹스를 연출합니다."
            )
        if "these earrings" in s:
            return (
                "팝 아트의 표현력과 인더스트리얼 형태가 섞여 사랑의 보편적 상징을 새롭게 해석합니다. "
                "리사이클드 옐로우 골드 하트 이어링은 트라이앵글 로고로 완성되어 "
                "프라다의 듀얼리스틱 정신을 드러냅니다."
            )
        if "embellished with sparkling diamonds" in s:
            return (
                "팝 아트의 표현력과 인더스트리얼 셰이프가 결합해 사랑의 보편적 상징을 새롭게 해석합니다. "
                "리사이클드 옐로우 골드 하트 링은 스파클링 다이아몬드로 장식되었습니다."
            )

    if s.startswith("Artisan tradition and technological innovation"):
        if "ring made of recycled white gold" in s:
            return (
                "장인 전통과 기술 혁신이 만나 클래식 주얼리 코드를 재정의합니다. "
                "랩에서 제작된 프라다 컷 다이아몬드는 아이코닉 트라이앵글에서 영감을 받은 "
                "오리지널 컷을 지녔습니다. 리사이클드 화이트 골드 링에 스파클링 다이아몬드가 "
                "컨템포러리한 라인을 한층 돋보이게 합니다."
            )
        return (
            "장인 전통과 기술 혁신이 만나 클래식 주얼리 코드를 재정의합니다. "
            "랩에서 제작된 프라다 컷 다이아몬드는 아이코닉 트라이앵글에서 영감을 받은 "
            "오리지널 컷을 지녔습니다. 리사이클드 옐로우 골드 싱글 펜던트 이어링에 "
            "스파클링 다이아몬드가 컨템포러리한 라인을 한층 돋보이게 합니다."
        )

    if s.startswith("Chosen for their exceptional chromatic value"):
        if "rose gold bracelet" in s and "citrine" in s:
            return (
                f"{CV_COLOR} 조각적인 라인, 하모니, 대비의 연구가 "
                "로즈 골드 팔찌 디자인에 영감을 줍니다. 시트린의 웜한 브릴리언스와 "
                "핑크 모가나이트의 우아함이 프라다 컷으로 강조됩니다."
            )
        if "white gold bracelet" in s and "amethyst" in s:
            return (
                f"{CV_COLOR} 조각적인 라인, 하모니, 대비의 연구가 "
                "화이트 골드 팔찌 디자인에 영감을 줍니다. 자수정의 인텐시티와 "
                "골드 그린 페리도트의 비브란트한 빛이 프라다 컷으로 강조됩니다."
            )
        if "rose gold earrings with morganite" in s:
            return (
                f"{CV_COLOR} 조각적인 라인과 절대적인 컬러가 "
                "로즈 골드 모가나이트 이어링 디자인에 수렴합니다. "
                "프라다 컷이 스톤의 섬세하고 내추럴한 브릴리언스를 타임리스한 뷰티로 끌어올립니다."
            )
        if "white gold earrings with amethyst" in s:
            return (
                f"{CV_COLOR} 조각적인 라인과 절대적인 컬러가 "
                "화이트 골드 자수정 이어링 디자인에 수렴합니다. "
                "프라다 컷이 스톤의 내추럴한 브릴리언스와 인텐스한 색감을 타임리스한 뷰티로 끌어올립니다."
            )
        if "white gold earrings with aquamarine" in s:
            return (
                f"{CV_COLOR} 조각적인 라인과 절대적인 컬러가 "
                "화이트 골드 아쿠아마린 이어링 디자인에 수렴합니다. "
                "프라다 컷이 스톤의 크리스탈린 브릴리언스를 타임리스한 뷰티로 끌어올립니다."
            )
        if "white gold earrings with peridot" in s:
            return (
                f"{CV_COLOR} 조각적인 라인과 절대적인 컬러가 "
                "화이트 골드 페리도트 이어링 디자인에 수렴합니다. "
                "프라다 컷이 스톤의 그린 골드 색감과 내추럴한 브릴리언스를 타임리스한 뷰티로 끌어올립니다."
            )

    if "Dichotomies, harmonies" in s:
        tail = "독보적인 프라다 컷과 독점 타원 컷이 스톤의 자연스러운 빛을 강조합니다."
        if "aquamarine meets the green-gold shade of peridot" in s and "diamonds" not in s:
            return f"{CV_DICHO} 아쿠아마린과 골드 그린 페리도트가 만나는 펜던트 이어링 디자인에 반영됩니다. {tail}"
        if "pink morganite meets the radiant delicacy of aquamarine" in s and "diamonds" not in s:
            return f"{CV_DICHO} 핑크 모가나이트와 아쿠아마린의 라디언트한 섬세함이 만나는 펜던트 이어링에 반영됩니다. {tail}"
        if "delicate pink morganite meets the warm brilliance of citrine" in s:
            return f"{CV_DICHO} 섬세한 핑크 모가나이트와 시트린의 웜한 브릴리언스가 만나는 펜던트 이어링에 반영됩니다. {tail}"
        if "green-gold peridot meets the intensity of amethyst" in s and "diamonds" not in s:
            return f"{CV_DICHO} 골드 그린 페리도트와 자수정의 인텐시티가 만나는 펜던트 이어링에 반영됩니다. {tail}"
        if "aquamarine meets the green-gold shade of peridot and the timeless elegance of diamonds" in s:
            return f"{CV_DICHO} 아쿠아마린, 페리도트, 다이아몬드가 어우러진 펜던트 이어링에 반영됩니다. {tail}"
        if "green-gold peridot meets the intensity of amethyst and the timeless elegance of diamonds" in s:
            return f"{CV_DICHO} 페리도트, 자수정, 다이아몬드가 어우러진 펜던트 이어링에 반영됩니다. {tail}"
        if "pink morganite meets the radiant delicacy of aquamarine and the timeless elegance of diamonds" in s:
            return f"{CV_DICHO} 모가나이트, 아쿠아마린, 다이아몬드가 어우러진 펜던트 이어링에 반영됩니다. {tail}"

    if s.startswith("Eternal Gold jewels redefine"):
        if "necklace made of recycled yellow gold" in s and "chain design" in s:
            return (
                f"{EG_REDEFINE} 랩에서 제작된 프라다 컷 다이아몬드가 "
                "리사이클드 옐로우 골드 네크리스의 우아하고 컨템포러리한 실루엣에 "
                "스파클을 더합니다. 체인 디자인은 아이코닉 트라이앵글에서 영감을 받은 "
                "유니크한 컷의 다이아몬드로 장식되었습니다."
            )
        if "bangle bracelet made of recycled white gold" in s:
            return (
                f"{EG} 주얼리는 기술 혁신과 장인 전통을 블렌드하는 언컨벤셔널한 접근으로 "
                "주얼리의 규칙을 재정의합니다. 프라다 컷 다이아몬드가 리사이클드 화이트 골드 "
                "뱅글 팔찌의 실루엣을 밝혀 줍니다. 스네이크 모티프가 프라다 창작의 듀얼리즘을 "
                "표현하며, 랩 메이드 다이아몬드가 주얼을 장식합니다."
            )
        if "bangle bracelet made of recycled yellow gold" in s:
            return (
                f"{EG} 주얼리는 기술 혁신과 장인 전통을 블렌드하는 언컨벤셔널한 접근으로 "
                "주얼리의 규칙을 재정의합니다. 프라다 컷 다이아몬드가 리사이클드 옐로우 골드 "
                "뱅글 팔찌의 실루엣을 밝혀 줍니다. 스네이크 모티프가 프라다 창작의 듀얼리즘을 "
                "표현하며, 랩 메이드 다이아몬드가 주얼을 장식합니다."
            )
        if "ring made of recycled white gold" in s:
            return (
                f"{EG} 주얼리는 기술 혁신과 장인 전통을 블렌드하는 언컨벤셔널한 접근으로 "
                "주얼리의 규칙을 재정의합니다. 프라다 컷 다이아몬드가 리사이클드 화이트 골드 "
                "링의 실루엣을 밝혀 줍니다. 스네이크 모티프가 강인하고 컨템포러리한 스타일로 "
                "재해석되었습니다."
            )

    if s.startswith("Inspired by the ancient talisman"):
        return (
            "고대부터 주얼리 세계에 존재해 온 탈리스만에서 영감을 받은 "
            "리사이클드 로즈 골드 네크리스는 아이코닉한 기하학적 형태와 "
            "프레셔스 소재를 결합합니다. 무지갯빛 마더 오브 펄과 "
            "루미너스 다이아몬드 파베가 우아한 디자인을 완성합니다. "
            "내부 슬라이딩 메커니즘으로 다양하게 착용할 수 있으며, "
            "퍼스널 메시지 각인도 가능합니다."
        )

    if s.startswith("Modern and bold, Eternal Gold"):
        return (
            f"모던하고 볼드한 {EG} 주얼리는 탁월함과 진보의 상징이 됩니다. "
            "과학과 장인 정신을 블렌드한 기법으로 랩에서 제작된 프라다 컷 다이아몬드가 "
            "로맨틱한 매력이 가득한 리사이클드 옐로우 골드 이어링 디자인에 "
            "스파클을 더합니다."
        )

    if s.startswith("Part of Prada's DNA"):
        return (
            "2000년대 초부터 프라다의 DNA에 담긴 체인 이미지가 새로운 형태와 의미를 갖습니다. "
            "파인 주얼리 컬렉션을 위해 볼드하고 세련된 디자인으로 재탄생한 체인은 "
            "힘과 우아함을 동시에 표현합니다. 리사이클드 옐로우 골드 팔찌의 각 링크는 "
            "브랜드의 상징적인 트라이앵글 셰이프에서 영감을 받았습니다."
        )

    if s.startswith("Prada combines antithetical ideas"):
        if "ring in recycled rose gold is decorated with the logo" in s:
            return (
                f"{SNAKE_OPEN} 주얼리에서 가장 오래된 신화적 상징인 스네이크가 "
                "브랜드의 듀얼리즘 컨셉을 표현합니다. 리사이클드 로즈 골드 링은 "
                "로고로 장식되어 브랜드의 스피릿을 강화합니다."
            )
        if "ring in recycled white gold is decorated with the logo" in s:
            return (
                f"{SNAKE_OPEN} 주얼리에서 가장 오래된 신화적 상징인 스네이크가 "
                "브랜드의 듀얼리즘 컨셉을 표현합니다. 리사이클드 화이트 골드 링은 "
                "로고로 장식되어 브랜드의 스피릿을 강화합니다."
            )
        if "rigid bracelet made of recycled white gold" in s:
            return (
                f"{SNAKE_OPEN} 스네이크가 리사이클드 화이트 골드 "
                "리지드 팔찌로 재해석되었습니다. 곡선적이고 우아한 디자인에 "
                "스파클링 파베 다이아몬드가 더해졌습니다."
            )
        if "rigid bracelet made of recycled yellow gold" in s:
            return (
                f"{SNAKE_OPEN} 스네이크가 리사이클드 옐로우 골드 "
                "리지드 팔찌로 재해석되었습니다. 아이코닉 트라이앵글의 "
                "기하학적 형태를 닮은 볼드한 라인과 스파클링 다이아몬드가 "
                "실루엣을 강조합니다."
            )
        if "ring made of recycled white gold that blends creativity" in s:
            return (
                f"{SNAKE_OPEN} 스네이크가 리사이클드 화이트 골드 링으로 "
                "재해석되었습니다. 파베 다이아몬드가 비추는 우아하고 "
                "곡선적인 디자인이 특징입니다."
            )
        if "ring made of recycled yellow gold, designed with bold lines" in s:
            return (
                f"{SNAKE_OPEN} 스네이크가 리사이클드 옐로우 골드 링으로 "
                "재해석되었습니다. 다이아몬드가 비추는 우아한 실루엣과 "
                "측면 각인 로고가 특징입니다."
            )
        if "ring made of recycled yellow gold, designed with strong lines" in s:
            return (
                f"{SNAKE_OPEN} 스네이크가 리사이클드 옐로우 골드 링으로 "
                "재해석되었습니다. 아이코닉 트라이앵글을 닮은 강인한 라인과 "
                "다이아몬드, 측면 각인 로고가 특징입니다."
            )
        if "triangle logo on the head of the snake" in s:
            return (
                f"{SNAKE_OPEN} 스네이크가 브랜드의 듀얼리즘 컨셉을 표현합니다. "
                "리사이클드 옐로우 골드 링의 스네이크 헤드에 트라이앵글 로고가 "
                "장식되어 브랜드의 스피릿을 강조합니다."
            )

    if s.startswith("Prada reinterprets the classic shapes"):
        return (
            "프라다는 타임리스한 언어를 바탕으로 클래식 주얼리의 형태와 "
            "테마를 컨템포러리한 시각으로 재해석합니다. 마리오 프라다가 "
            "디자인한 트렁크에 처음 등장한 프라다 트라이앵글은 "
            "18K 리사이클드 옐로우 골드 링 위에서 브릴리언트 컷 "
            "다이아몬드 파베로 빛납니다."
        )

    if s.startswith("Prada's identifying element"):
        return (
            "프라다의 아이덴티티 요소인 트라이앵글이 파인 주얼리 컬렉션의 "
            "주인공이 됩니다. 1913년 마리오 프라다의 스티머 트렁크 "
            "시그니처로 탄생한 형태가 슬릭한 기하학적 펜던트에 "
            "랩 그로운 다이아몬드와 함께 재탄생했습니다."
        )

    if s.startswith("Pure lines, sleek and elegant"):
        if "pendant necklace in rose gold" in s and "micro" not in s:
            return (
                "퓨어하고 슬릭하며 우아한 라인이 로즈 골드 "
                "펜던트 네크리스를 정의합니다. 이터널하고 유니버설한 "
                "상징을 컨템포러리 디자인으로 재해석하며, 프라다의 "
                "혁신적 스피릿과 장인 전통을 담았습니다."
            )
        if "pendant necklace in white gold" in s:
            return (
                "퓨어하고 슬릭하며 우아한 라인이 화이트 골드 "
                "펜던트 네크리스를 정의합니다. 섬세한 마이크로 사이즈의 "
                "하트에 아이코닉 트라이앵글에서 영감을 받은 "
                "프라다 컷 랩 그로운 다이아몬드가 스파클합니다."
            )
        if "single heart-shaped earring in rose gold" in s:
            return (
                "퓨어하고 슬릭하며 우아한 라인이 로즈 골드 "
                "하트 실루엣 싱글 이어링을 정의합니다. 이터널하고 "
                "유니버설한 상징을 컨템포러리하고 세련된 디자인으로 "
                "재해석했습니다."
            )
        if "single heart-shaped earring in white gold" in s:
            return (
                "퓨어하고 슬릭하며 우아한 라인이 화이트 골드 "
                "하트 실루엣 싱글 이어링을 정의합니다. 섬세한 "
                "마이크로 사이즈에 프라다 컷 랩 그로운 다이아몬드가 "
                "스파클합니다."
            )

    if s.startswith("Sophisticated craftsmanship"):
        return (
            "세련된 장인 정신과 리서치가 프라다 이터널 골드 컬렉션을 "
            "탄생시켰습니다. 스파클링하고 아이코닉한 디테일이 담긴 "
            "프레셔스 피스의 컬렉션입니다."
        )

    if "The Eternal Gold Collection establishes" in s or "The Eternal Gold collection establishes" in s:
        base = (
            "이터널 골드 컬렉션은 원형적 형태와 이터널 심볼 사이의 "
            "대화를 열어갑니다. 프라다 트라이앵글의 아이코닉한 기하학적 "
            "형태가 링의 포컬 요소가 됩니다."
        )
        if "white gold, framed by a diamond pavé" in s:
            return base + " 다이아몬드 파베가 프레임을 이루며, 혁신과 장인적 탁월함의 조화를 표현합니다."
        if "white gold ring with diamond pavé" in s:
            return base + " 다이아몬드 파베와 함께 혁신과 장인적 탁월함의 조화를 표현합니다."
        if "recycled yellow gold illuminated with diamond pavé" in s:
            return base + " 다이아몬드 파베가 리사이클드 옐로우 골드 링을 밝혀 줍니다."
        if "recycled yellow gold. Bold" in s:
            return base + " 볼드하고 입체적인 라인이 컨템포러리하고 독보적인 주얼을 완성합니다."

    if s.startswith("The Prada Fine Jewelry Couleur Vivante collection explores"):
        solitaire = (
            f"{CV_EXPLORE} 탁월한 색채 가치로 선정된 스톤이 "
            "프라다 컷 솔리테어 링 디자인에 결합되었습니다. "
            "유니크하고 혁신적인 셰이프가 스톤의 내추럴 뷰티를 "
            "끌어올립니다."
        )
        if "aquamarine and peridot" in s:
            return solitaire.replace("스톤이", "아쿠아마린과 페리도트가")
        if "morganite and aquamarine" in s:
            return solitaire.replace("스톤이", "모가나이트와 아쿠아마린이")
        if "morganite and citrines" in s:
            return solitaire.replace("스톤이", "모가나이트와 시트린이")
        if "peridot and amethyst" in s:
            return solitaire.replace("스톤이", "페리도트와 자수정이")
        if "aquamarine meet the brilliance of pink morganite" in s:
            return (
                f"{CV_EXPLORE} 화이트 골드 팔찌에 아쿠아마린과 "
                "핑크 모가나이트가 프라다 컷과 함께 세팅되었습니다."
            )
        if "gold-green peridot meets the crystalline brilliance of aquamarine" in s:
            return (
                f"{CV_EXPLORE} 화이트 골드 팔찌에 골드 그린 페리도트와 "
                "아쿠아마린이 프라다 컷과 함께 세팅되었습니다."
            )
        if "suiffé-cut peridots" in s:
            return (
                f"{CV_EXPLORE} 화이트 골드에 스위페 컷 페리도트가 "
                "섬세하게 세팅된 네크리스입니다. "
                "프라다 컷 아쿠아마린이 주얼을 완성합니다."
            )
        if "suiffé-cut aquamarines" in s:
            return (
                f"{CV_EXPLORE} 크리스탈린 브릴리언스의 스위페 컷 "
                "아쿠아마린이 화이트 골드 네크리스에 세팅되었습니다. "
                "핑크 모가나이트가 주얼을 완성합니다."
            )

    if s.startswith("The Prada triangle becomes the precious pattern"):
        return (
            "프라다 트라이앵글이 리사이클드 옐로우 골드 팔찌의 "
            "프레셔스 패턴이 됩니다. 모더니스트 디자인과 "
            "우아한 디테일이 어우러진 주얼입니다."
        )

    if s.startswith("The evocative power of symbols inspires"):
        if "Robot pendant" in s:
            return (
                f"상징이 전하는 힘에 영감을 받은 {EG} 네크리스는 "
                "영감을 줍니다. 로봇 펜던트가 슬림한 체인 디자인을 "
                "생동감 있게 연출하며, 옐로우 골드와 다이아몬드로 "
                "프레셔스하게 재해석되었습니다."
            )
        if "Spring/Summer 2011" in s and "necklace exploring iconic shapes" in s:
            return (
                f"상징이 전하는 힘에 영감을 받은 {EG} 네크리스는 "
                "2011 S/S 컬렉션의 팝 심볼과 트라이앵글 로고가 "
                "옐로우 골드 주얼리에 언컨벤셔널하고 다이내믹한 우아함을 더합니다."
            )
        if "pendant exploring iconic and timeless shapes" in s and "Spring/Summer 2011" in s:
            return (
                f"상징이 전하는 힘에 영감을 받은 {EG} 펜던트는 "
                "2011 S/S 팝 모티프와 트라이앵글 로고를 담은 "
                "두 개의 옐로우 골드 참이 퍼스널 스토리를 "
                "전하는 크리에이티브한 조합을 제안합니다."
            )
        if "pendant necklace exploring iconic shapes" in s and "rose" in s:
            return (
                f"상징이 전하는 힘에 영감을 받은 {EG} 펜던트 네크리스는 "
                "영감을 줍니다. 장미와 트라이앵글 로고가 "
                "옐로우 골드 주얼리에 언컨벤셔널하고 다이내믹한 "
                "우아함을 더합니다."
            )
        if "rose, an eternal emblem" in s:
            return (
                f"상징이 전하는 힘에 영감을 받은 {EG} 펜던트는 "
                "장미와 트라이앵글의 두 펜던트가 퍼스널 스토리를 "
                "전하는 크리에이티브한 조합을 제안합니다."
            )
        if "distinctive, unconventional emblems" in s:
            return (
                f"상징이 전하는 힘에 영감을 받은 {EG} 펜던트는 "
                "두 옐로우 골드 펜던트가 프라다 코드를 반영하며 "
                "퍼스널 스토리를 전하는 조합을 제안합니다."
            )
        if "emblem of freedom and dynamism" in s:
            return (
                f"상징이 전하는 힘에 영감을 받은 {EG} 펜던트는 "
                "자유와 다이내믹의 상징과 트라이앵글 로고가 "
                "퍼스널 스토리를 전하는 조합을 제안합니다."
            )
        if "robot with sparkling diamonds" in s:
            return (
                f"상징이 전하는 힘에 영감을 받은 {EG} 펜던트는 "
                "스파클링 다이아몬드 로봇과 트라이앵글이 "
                "퍼스널 스토리를 전하는 조합을 제안합니다."
            )

    if s.startswith("The heart, one of the universal symbols"):
        if "Each link in the chain" in s:
            return (
                "사랑의 보편적 상징인 하트가 프라다 파인 주얼리 "
                "컬렉션의 주인공이 됩니다. 팝에서 영감을 받은 볼드한 "
                "라인이 로고의 기하학적 요소와 우아하게 대비됩니다. "
                "각 체인 링크는 트라이앵글에서 영감을 받아 "
                "리파인드하고 아이코닉한 실루엣을 완성합니다."
            )
        return (
            "사랑의 보편적 상징인 하트가 프라다 파인 주얼리 "
            "컬렉션의 주인공이 됩니다. 팝에서 영감을 받은 볼드한 "
            "라인이 프라다 로고의 기하학적 요소와 우아하게 대비됩니다. "
            "리사이클드 옐로우 골드 네크리스는 브랜드의 타임리스 "
            "전통과 독창성을 담은 프레셔스 주얼입니다."
        )

    if s.startswith("The rediscovery of jewelry archetypes continues"):
        if "laboratory-grown diamond is an expression of refined, modern femininity" in s:
            return (
                f"{BOW_OPEN} 프라다의 유니크한 코드로 변모한 "
                "리사이클드 옐로우 골드 링은 랩 그로운 다이아몬드로 "
                "장식되어 세련되고 모던한 페미니니티를 표현합니다."
            )
        if "protagonist of the design of this elegant recycled yellow gold bracelet" in s:
            return (
                f"{BOW_OPEN} 보우가 리사이클드 옐로우 골드 "
                "팔찌 디자인의 주인공이 됩니다. 심플한 형태와 "
                "클린한 라인이 컨템포러리 페미니니티를 표현합니다."
            )
        if "exclusive headband" in s:
            return (
                f"{BOW_OPEN} 보우가 리사이클드 옐로우 골드 "
                "헤드밴드를 장식합니다. 심플한 형태와 클린한 "
                "라인이 컨템포러리 페미니니티를 표현합니다."
            )
        if "embellishes this necklace made of recycled yellow gold" in s:
            return (
                f"{BOW_OPEN} 보우가 리사이클드 옐로우 골드 "
                "네크리스를 장식합니다. 심플한 형태와 클린한 "
                "라인이 컨템포러리 페미니니티를 표현합니다."
            )
        if "embellished with laboratory-grown diamonds" in s:
            return (
                f"{BOW_OPEN} 프라다의 유니크한 코드로 변모한 "
                "리사이클드 옐로우 골드 이어링은 랩 그로운 "
                "다이아몬드로 장식되었습니다."
            )
        if "expression of refined, contemporary femininity" in s and "earrings" in s:
            return (
                f"{BOW_OPEN} 프라다의 유니크한 코드로 변모한 "
                "리사이클드 옐로우 골드 이어링은 세련되고 "
                "컨템포러리한 페미니니티를 표현합니다."
            )
        if "bangle bracelet made of recycled yellow gold" in s:
            return (
                f"{BOW_OPEN} 리사이클드 옐로우 골드 뱅글 팔찌는 "
                "퓨어하고 심플한 라인으로 세련되고 "
                "컨템포러리한 페미니니티를 표현합니다."
            )
        if "articulated gold bracelet" in s:
            return (
                f"{BOW_OPEN} 가장 심플한 형태로 제시된 보우가 "
                "리사이클드 옐로우 골드 관절 팔찌를 빛내 줍니다. "
                "랩 그로운 다이아몬드가 클린하고 우아한 "
                "디자인을 더욱 돋보이게 합니다."
            )

    if s.startswith("The rediscovery of jewelry archetypes continues,"):
        if "yellow gold ring" in s:
            return (
                f"{BOW_OPEN} 프라다의 유니크한 코드로 재해석된 "
                "보우가 옐로우 골드 링을 정의합니다. "
                "세련되고 모던한 페미니니티를 표현합니다."
            )
        if "brooch" in s:
            return (
                f"{BOW_OPEN} 프라다의 유니크한 코드로 재해석된 "
                "보우가 리사이클드 옐로우 골드 브로치를 "
                "정의합니다. 세련되고 모던한 페미니니티를 표현합니다."
            )

    if s.startswith("The snake, one of the oldest mythological symbols"):
        return (
            "주얼리에서 가장 오래된 신화적 상징인 스네이크가 "
            "브랜드의 듀얼리즘 컨셉을 표현합니다. "
            f"{SNAKE_OPEN} 리사이클드 옐로우 골드 링의 "
            "스네이크 헤드에 트라이앵글 로고가 장식되어 "
            "브랜드의 스피릿을 강조합니다."
        )

    if s.startswith("The triangle, Prada's identifying element"):
        base = (
            "프라다의 아이덴티티 요소인 트라이앵글이 "
            "파인 주얼리 컬렉션의 주인공이 됩니다. "
            "1913년 마리오 프라다의 트래블 트렁크 로고로 "
            "탄생한 형태가 파베 다이아몬드와 함께 "
        )
        if "micro size" in s and "recycled yellow gold" in s:
            return base + "마이크로 사이즈 펜던트에 재탄생했습니다. 리사이클드 옐로우 골드 네크리스가 브랜드의 타임리스 전통을 담습니다."
        if "micro size" in s and "recycled white gold" in s:
            return base + "마이크로 사이즈 펜던트에 재탄생했습니다. 리사이클드 화이트 골드 네크리스가 브랜드의 타임리스 전통을 담습니다."
        if "mini size" in s and "recycled yellow gold" in s:
            return base + "미니 사이즈 펜던트에 재탄생했습니다. 리사이클드 옐로우 골드 네크리스가 브랜드의 타임리스 전통을 담습니다."
        if "mini size" in s and "recycled white gold" in s:
            return base + "미니 사이즈 펜던트에 재탄생했습니다. 리사이클드 화이트 골드 네크리스가 브랜드의 타임리스 전통을 담습니다."

    if s.startswith("The triangle, Prada's signature element"):
        if "oversized pendant made of recycled yellow gold" in s and "accompanied" in s:
            return (
                "프라다의 시그니처 요소인 트라이앵글이 "
                "파인 주얼리 컬렉션의 주인공이 됩니다. "
                "볼드하고 스무스한 오버사이즈 펜던트가 "
                "벨벳 리본과 함께 브랜드의 타임리스 "
                "전통을 담습니다."
            )
        if "oversized pendant in recycled yellow gold with a bold, smooth line" in s:
            return (
                "프라다의 시그니처 요소인 트라이앵글이 "
                "파인 주얼리 컬렉션의 주인공이 됩니다. "
                "볼드하고 스무스한 오버사이즈 펜던트가 "
                "벨벳 리본과 함께 브랜드의 타임리스 "
                "전통을 담습니다."
            )
        if "reimagined as an earring in rose gold" in s:
            return (
                "프라다의 시그니처 요소인 트라이앵글이 "
                "로즈 골드 이어링으로 재탄생했습니다. "
                "브랜드의 타임리스 헤리티지와 독창성을 "
                "담은 세련된 주얼입니다."
            )
        if "mini version on the pendant of this rose gold necklace" in s:
            return (
                "프라다의 시그니처 요소인 트라이앵글이 "
                "로즈 골드 네크리스 펜던트의 미니 버전으로 "
                "재탄생했습니다. 브랜드의 타임리스 "
                "헤리티지를 담은 세련된 주얼입니다."
            )
        if "small version on the pendant of this rose gold necklace" in s:
            return (
                "프라다의 시그니처 요소인 트라이앵글이 "
                "로즈 골드 네크리스 펜던트의 스몰 버전으로 "
                "재탄생했습니다. 브랜드의 타임리스 "
                "헤리티지를 담은 세련된 주얼입니다."
            )
        if "reimagined in a bold, smooth form on these earrings" in s:
            return (
                "프라다의 시그니처 요소인 트라이앵글이 "
                "리사이클드 옐로우 골드 이어링에 "
                "볼드하고 스무스한 형태로 재탄생했습니다."
            )
        if "oversized pendant of this necklace" in s and "Each link" in s:
            return (
                "프라다의 시그니처 요소인 트라이앵글이 "
                "리사이클드 옐로우 골드 네크리스의 "
                "오버사이즈 펜던트에 재탄생했습니다. "
                "각 체인 링크는 스무스한 면과 포인티한 "
                "면으로 트라이앵글의 절대적 형태를 "
                "표현합니다."
            )
        if "bold, sophisticated shape on these earrings" in s:
            return (
                "프라다의 시그니처 요소인 트라이앵글이 "
                "리사이클드 옐로우 골드 이어링에 "
                "볼드하고 세련된 형태로 재탄생했습니다."
            )

    if s.startswith("The triangle, a continuously evolving symbol"):
        return (
            f"{TRI_OPEN} 엠보싱 패턴으로 변모한 아이코닉 "
            "기하학적 형태가 리사이클드 화이트 골드 팔찌를 "
            "애니메이트합니다. 오리지널 패턴의 파베 "
            "다이아몬드와 히든 클래스프로 완성된 "
            "독창적이고 세련된 주얼입니다."
        )

    if s.startswith("The triangle, first introduced by Mario Prada"):
        return (
            f"{TRI_OPEN} 1913년 마리오 프라다가 선보인 "
            "아이코닉 기하학적 실루엣이 리사이클드 "
            "화이트 골드 브로치 디자인에 담겼습니다. "
            "오리지널 패턴의 파베 다이아몬드가 "
            "반짝이는 빛의 독특한 효과를 연출합니다."
        )

    if s.startswith("The triangle, the emblematic geometric shape"):
        return (
            "프라다 DNA의 상징적 기하학적 형태인 "
            "트라이앵글이 리사이클드 로즈 골드 "
            "브로치로 재탄생했습니다. 세련된 "
            "모더니스트 디자인이 특징입니다."
        )

    if s.startswith("These sparkling, precious earrings"):
        return (
            "리사이클드 골드와 다이아몬드로 제작된 "
            "스파클링하고 프레셔스한 이어링은 "
            "새로운 우아함의 정의를 상징합니다."
        )

    if s.startswith("This bold, precious necklace"):
        return (
            "볼드하고 프레셔스한 네크리스가 "
            "강렬한 임팩트를 만듭니다. 리사이클드 "
            "옐로우 골드 소재에 서로 다른 크기의 "
            "요소가 곡선적인 실루엣을 형성합니다. "
            "각 링크는 스무스한 면과 트라이앵글 "
            "형태의 포인티한 면으로 프라다의 "
            "듀얼 아이덴티티를 연상시킵니다."
        )

    if s.startswith("This bracelet has a strong"):
        return (
            "강인하고 볼드하며 프레셔스한 "
            "캐릭터의 팔찌입니다. 리사이클드 "
            "옐로우 골드로 제작되었으며, "
            "기하학적 요소로 구성됩니다. "
            "프라다 트라이앵글은 새롭고 "
            "컨템포러리한 주얼리의 상징이 됩니다."
        )

    if s.startswith("This bracelet made of recycled rose gold is a contemporary"):
        return (
            "리사이클드 로즈 골드 팔찌는 클래식 "
            "타원 뱅글의 컨템포러리 재해석입니다. "
            "엠보싱 모티프가 1913년 마리오 프라다의 "
            "홀마크로 등장한 트라이앵글을 "
            "연상시킵니다. 히든 힌지 클래스프가 "
            "프라다의 언컨벤셔널한 소울을 강조합니다."
        )

    if s.startswith("This bracelet with an elegant design made of recycled rose gold"):
        return (
            "세련된 디자인의 리사이클드 로즈 골드 "
            "팔찌는 프라다의 듀얼 소울을 담습니다. "
            "프레셔스 다이아몬드와 아이코닉 "
            "트라이앵글이 빛의 연출을 만들어냅니다. "
            "단독 또는 레이어링 착용이 가능한 "
            "우아하고 구조적인 디자인입니다."
        )

    if s.startswith("This elegant bracelet made of recycled yellow gold"):
        return (
            "우아한 리사이클드 옐로우 골드 "
            "팔찌는 프라다의 듀얼 소울을 "
            "담습니다. 프레셔스 다이아몬드와 "
            "아이코닉 트라이앵글이 빛의 "
            "연출을 만들어냅니다."
        )

    if s.startswith("This necklace has a strong"):
        return (
            "강인하고 볼드하며 프레셔스한 "
            "네크리스입니다. 리사이클드 "
            "옐로우 골드에 서로 다른 크기의 "
            "요소가 곡선적인 실루엣을 "
            "형성합니다."
        )

    if s.startswith("This recycled gold bracelet is a contemporary"):
        return (
            "리사이클드 골드 팔찌는 클래식 "
            "타원 뱅글의 컨템포러리 재해석입니다. "
            "1913년 마리오 프라다의 홀마크로 "
            "등장한 트라이앵글을 연상시키는 "
            "엠보싱 모티프가 특징입니다."
        )

    if s.startswith("This signet ring"):
        return (
            "리사이클드 옐로우 골드 시그넷 링은 "
            "프라다의 아이코닉 트라이앵글 "
            "형태를 재해석합니다. 우아함, "
            "모던함, 혁신, 장인 정신을 "
            "표현하는 파인 주얼리 컬렉션의 "
            "슬릭한 라인과 세련된 캐릭터를 "
            "담았습니다."
        )

    if s.startswith("This sparkling, precious earring"):
        return (
            "스파클링하고 프레셔스한 이 "
            "이어링은 프라다의 세련되고 "
            "소피스티케이티드한 에센스를 "
            "담습니다. 리사이클드 골드와 "
            "랩 그로운 다이아몬드로 제작된 "
            "트라이앵글 셰이프의 "
            "익스클루시브 피스입니다."
        )

    raise KeyError(f"No desc template: {s[:80]}")


# ── main ─────────────────────────────────────────────────────────────────────

def collect_strings(raw: dict) -> tuple[set[str], set[str], set[str], set[str], set[str]]:
    titles, descs, details, materials, colors = set(), set(), set(), set(), set()
    for p in raw.get("products") or []:
        t = (p.get("officialNameEn") or p.get("title") or "").strip()
        if t:
            titles.add(t)
        d = (p.get("description") or "").strip()
        if d:
            descs.add(d)
        for line in p.get("details") or []:
            line = str(line).strip()
            if line:
                details.add(line)
        for line in p.get("materialsCare") or []:
            line = str(line).strip()
            if line:
                materials.add(line)
        mat = (p.get("material") or "").strip()
        if mat:
            materials.add(mat)
        col = (p.get("color") or "").strip()
        if col:
            colors.add(col)
    return titles, descs, details, materials, colors


def validate(payload: dict) -> list[tuple[str, str, str, float]]:
    bad = []
    for sec in ("titles", "descriptions", "details", "materials", "colors"):
        for k, v in (payload.get(sec) or {}).items():
            r = en_ratio(str(v))
            if r > MAX_EN_RATIO:
                bad.append((sec, k, str(v), r))
    return bad


def main() -> None:
    raw = json.loads(RAW.read_text())
    titles_s, descs_s, details_s, materials_s, colors_s = collect_strings(raw)

    print(f"Source: {len(titles_s)} titles, {len(descs_s)} descs, {len(details_s)} details, {len(colors_s)} colors", flush=True)

    payload = {
        "titles": {t: title_ko(t) for t in sorted(titles_s)},
        "descriptions": {d: desc_ko(d) for d in sorted(descs_s)},
        "details": {d: detail_ko(d) for d in sorted(details_s)},
        "materials": {m: detail_ko(m) for m in sorted(materials_s)},
        "colors": {c: color_ko(c) for c in sorted(colors_s)},
    }

    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")

    bad = validate(payload)
    print(f"\nWrote {OUT}", flush=True)
    print(f"Counts: titles={len(payload['titles'])}, descriptions={len(payload['descriptions'])}, "
          f"details={len(payload['details'])}, materials={len(payload['materials'])}, colors={len(payload['colors'])}", flush=True)
    print(f"Bad entries (en_ratio > {MAX_EN_RATIO}): {len(bad)}", flush=True)
    for sec, k, v, r in bad[:20]:
        print(f"  [{sec}] ratio={r:.2f}: {v[:90]}", flush=True)

    if bad:
        sys.exit(1)


if __name__ == "__main__":
    main()
