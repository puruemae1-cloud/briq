#!/usr/bin/env python3
"""Write curated Korean copy for Prada women's accessories (non-SLG)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "src/data/pr/pr-womens-accessories-catalog-raw.json"
SLG_PATH = ROOT / "src/data/pr/pr-slg-ko-copy.json"
OUT_PATH = ROOT / "src/data/pr/pr-accessories-ko-copy.json"
DESC_DATA = Path(__file__).with_name("_accessories_desc_ko.py")

MATERIALS: dict[str, str] = {
    "Acetate": "아세테이트",
    "Cashmere": "캐시미어",
    "Fabric": "패브릭",
    "Fabric/Leather": "패브릭/가죽",
    "Leather": "가죽",
    "Metal": "메탈",
    "Other Materials": "기타 소재",
    "Wool": "울",
    "Woven Materials": "우븐 소재",
}

DETAIL_EXACT: dict[str, str] = {
    '"Heritage" print': '"Heritage" 프린트',
    '"Tulip" print': '"Tulip" 프린트',
    "-Frame compatible with graduated lenses": "도수 렌즈 호환 프레임",
    "-Frame not compatible with graduated lenses": "도수 렌즈 비호환 프레임",
    "100% UVA / UVB protection": "100% UVA/UVB 차단",
    "100% UVA / UVB protection--Standard Fit": "100% UVA/UVB 차단 · 스탠다드 핏",
    "100% alpaca wool": "100% 알파카 울",
    "100% cashmere": "100% 캐시미어",
    "100% virgin wool": "100% 버진 울",
    "50% silk 45% cashmere 3%polyester 2% polyamide": "실크 50% · 캐시미어 45% · 폴리에스터 3% · 폴리아미드 2%",
    "51% silk 49% cashmere": "실크 51% · 캐시미어 49%",
    "56% silk 25% viscose 11% polyamide 8% wool": "실크 56% · 비스코스 25% · 폴리아미드 11% · 울 8%",
    "60% silk 40% wool": "실크 60% · 울 40%",
    "70% virgin wool 30% cashmere": "버진 울 70% · 캐시미어 30%",
    "78% silk 22% wool": "실크 78% · 울 22%",
    "90% wool 10% cashmere": "울 90% · 캐시미어 10%",
    "Adjustable leather handle": "길이 조절 가죽 핸들",
    "Adjustable nose pads suitable for any fit": "모든 핏에 적합한 조절식 노즈 패드",
    "Adjustable, detachable leather shoulder strap": "조절·탈부착 가죽 숄더 스트랩",
    "Alternative fit": "얼터너티브 핏",
    "Article comes with dedicated packaging": "전용 패키지 동봉",
    "Back button closure": "백 버튼 클로저",
    "Barrette closure": "바레트 클로저",
    "Bloom Dots print": "Bloom Dots 프린트",
    "Blue Light lenses without prescription have a special filter to reduce exposure to the blue light of digital devices and sunlight": "무도수 블루라이트 렌즈는 디지털 기기와 햇빛의 블루라이트 노출을 줄이는 특수 필터가 적용되어 있습니다",
    "Blue Light lenses without prescription have a special filter to reduce exposure to the blue light of digital devices and sunlight. Blue light is considered harmful up to 455 nm with maximum toxicity between 415-455 nm": "무도수 블루라이트 렌즈는 디지털 기기와 햇빛의 블루라이트 노출을 줄이는 특수 필터가 적용되어 있습니다. 블루라이트는 455nm까지 유해하며, 415–455nm 구간에서 독성이 가장 높습니다",
    "Braided": "브레이디드",
    "Button detail": "버튼 디테일",
    "Cable knit": "케이블 니트",
    "Cable-knit motif": "케이블 니트 모티프",
    "Card slot on the front": "앞면 카드 슬롯",
    "Cashmere and shearling lining": "캐시미어 & 시어링 안감",
    "Check Flower print": "Check Flower 프린트",
    "Check Paisley print": "Check Paisley 프린트",
    "Clip back": "백 클립",
    "Clip closure": "클립 클로저",
    "Clip fastening": "클립 잠금",
    "Clip on the back": "백 클립",
    "Comes with a Re-Nylon pouch": "Re-Nylon 파우치 동봉",
    "Compatible with the Prada Linea Rossa by Oakley snow helmet": "Prada Linea Rossa by Oakley 스노 헬멧 호환",
    "Cord ties with leather details": "가죽 디테일 코드 타이",
    "Cotton lining": "코튼 안감",
    "Cropped fit": "크롭 핏",
    "Crystal Lenses": "크리스탈 렌즈",
    "Crystal lenses": "크리스탈 렌즈",
    "Denim triangle logo": "데님 트라이앵글 로고",
    "Detachable leather wristlet": "탈부착 가죽 리스트렛",
    "Detachable, adjustable leather shoulder strap": "탈부착·조절 가죽 숄더 스트랩",
    "Detachable, adjustable nylon shoulder strap.": "탈부착·길이 조절 나일론 숄더 스트랩",
    "Detachable, adjustable nylon tape shoulder strap": "탈부착·길이 조절 나일론 테이프 숄더 스트랩",
    "Do not bleach": "표백 금지",
    "Do not dry clean": "드라이클리닝 금지",
    "Do not iron": "다림질 금지",
    "Do not natural dry": "자연 건조 금지",
    "Do not tumble dry": "건조기 사용 금지",
    "Do not wash": "세탁 금지",
    "Double Match print: Madras and Tie-Dye": "Double Match 프린트: Madras & Tie-Dye",
    "Double Match print: Mermaids and Polka-dot print": "Double Match 프린트: Mermaids & Polka-dot",
    "Double Match print: Mermaids and Polka-dots": "Double Match 프린트: Mermaids & Polka-dots",
    "Double weave fabric": "더블 위브 패브릭",
    "Drawstring closure": "드로우스트링 클로저",
    "Drawstring closure with leather laces": "가죽 레이스 드로우스트링 클로저",
    "Duchess interior with patch pocket": "듀chesse 내부 · 패치 포켓",
    "Elasticized strap color: Matte Black": "탄성 스트랩 컬러: 매트 블랙",
    "Elasticized strap color: Matte Gray": "탄성 스트랩 컬러: 매트 그레이",
    "Embroidered lettering logo": "자수 레터링 로고",
    "Embroidered logo": "자수 로고",
    "Enameled logo": "에나멜 로고",
    "Enameled metal lettering logo": "에나멜 메탈 레터링 로고",
    "Enameled metal logo buckle": "에나멜 메탈 로고 버클",
    "Enameled metal triangle logo": "에나멜 메탈 트라이앵글 로고",
    "Enameled metal triangle logo charm": "에나멜 메탈 트라이앵글 로고 참",
    "Enameled metal triangle logo on the tote": "토트 에나멜 메탈 트라이앵글 로고",
    "Enameled triangle logo": "에나멜 트라이앵글 로고",
    "Enameled-metal triangle logo": "에나멜 메탈 트라이앵글 로고",
    "Engraved logo": "각인 로고",
    "Fantasy print": "Fantasy 프린트",
    "Fisherman's rib knit": "피셔맨 리브 니트",
    "Fleece lining": "플리스 안감",
    "Flowers print": "Flowers 프린트",
    "For pierced ears": "피어싱용",
    "For pierced ears--Metal triangle logo": "피어싱용 · 메탈 트라이앵글 로고",
    "Frame compatible with graduated lenses": "도수 렌즈 호환 프레임",
    "Frame not compatible with graduated lenses": "도수 렌즈 비호환 프레임",
    "Fringe on all four sides": "사면 프린지",
    "Fringe on four sides": "사면 프린지",
    "Fringe on two sides": "양면 프린지",
    "Full Fitting": "풀 핏",
    "Garden Dots print": "Garden Dots 프린트",
    "Garden print": "Garden 프린트",
    "Garment-dyed treatment": "가먼트 다이 가공",
    "Gradient Lips print": "Gradient Lips 프린트",
    "Hair pin": "헤어 핀",
    "Hot-stamped logo": "핫스탬프 로고",
    "Hot-stamped logo on the pendant": "펜던트 핫스탬프 로고",
    "Hypoallergenic and nickel free materials": "저자극·니켈 프리 소재",
    "Hypoallergenic and nickel-free materials": "저자극·니켈 프리 소재",
    "Inside pocket with two card slots": "내부 포켓 · 카드 슬롯 2개",
    "Interchangeable lenses with Prizm™ technology that increases visual contrast and Single Layer anti-fog treatment": "Prizm™ 기술 교환 렌즈 · 시각 대비 향상 · Single Layer 김서림 방지 코팅",
    "Interlocking clasp": "인터로킹 클라스프",
    "Iron at maximum sole-plate temperature of 120 °c": "다리미 최고 온도 120°C",
    "Jacquard knit": "자카드 니트",
    "Jacquard logo": "자카드 로고",
    "Keychain with removable split ring": "탈부착 스플릿 링 키체인",
    "Knit triangle logo": "니트 트라이앵글 로고",
    "Laser-cut logo on the buckle": "버클 레이저컷 로고",
    "Lasered logo on the buckle": "버클 레이저 로고",
    "Leather": "가죽",
    "Leather Handle Loop with Snap": "스냅 가죽 핸들 루프",
    "Leather drawstring closure": "가죽 드로우스트링 클로저",
    "Leather handle": "가죽 핸들",
    "Leather lace closure": "가죽 레이스 클로저",
    "Leather logo label": "가죽 로고 라벨",
    "Leather strap": "가죽 스트랩",
    "Leather strap and metal key ring": "가죽 스트랩 & 메탈 키링",
    "Leather strap and metal ring": "가죽 스트랩 & 메탈 링",
    "Leather triangle logo": "가죽 트라이앵글 로고",
    "Leather wristlet": "가죽 리스트렛",
    "Line drip drying in the shade": "그늘에 뉘어 건조",
    "Lined garment": "라이닝 처리",
    "Linen blend interior": "린넨 블렌드 내부",
    "Lips print": "Lips 프린트",
    "Lobster claw clasp": "랍스터 클라 클라스프",
    "Logo label": "로고 라벨",
    "Loden fabric triangle logo": "로덴 패브릭 트라이앵글 로고",
    "Logo engraved on medallion": "메달리온 각인 로고",
    "Logo engraved on the buckle": "버클 각인 로고",
    "Logo loop with enameled metal triangle charm": "에나멜 메탈 트라이앵글 참 로고 루프",
    "Logo on medal": "메달 로고",
    "Logo-engraved charm": "로고 각인 참",
    "Logo-engraved medal": "로고 각인 메달",
    "Logo-engraved metal belt tip": "로고 각인 메탈 벨트 팁",
    "Logo-print Re-Nylon interior with zipper pocket": "로고 프린트 Re-Nylon 내부 · 지퍼 포켓",
    "Logo-print Re-Nylon lining": "로고 프린트 Re-Nylon 안감",
    "Logo-print Re-Nylon lining with zipper pocket": "로고 프린트 Re-Nylon 안감 · 지퍼 포켓",
    "Logo-print nylon lining": "로고 프린트 나일론 안감",
    "Logo-print nylon lining with patch pocket": "로고 프린트 나일론 안감 · 패치 포켓",
    "Magnetic clasp": "마그네틱 클라스프",
    "Maximum washing temperature 30 °c, mild process": "최대 세탁 온도 30°C · 약하게",
    "Metal buckle": "메탈 버클",
    "Metal buckle closure": "메탈 버클 클로저",
    "Metal buckle with enameled metal triangle logo": "에나멜 메탈 트라이앵글 로고 메탈 버클",
    "Metal buckles": "메탈 버클",
    "Metal clip on the back": "백 메탈 클립",
    "Metal lettering logo": "메탈 레터링 로고",
    "Metal logo": "메탈 로고",
    "Metal screw clasp on the back": "백 메탈 스크류 클라스프",
    "Metal triangle logo": "메탈 트라이앵글 로고",
    "Nappa leather": "나파 가죽",
    "Nappa leather and nylon lining": "나파 가죽 & 나일론 안감",
    "Nappa leather interior with card slots": "나파 가죽 내부 · 카드 슬롯",
    "Nappa leather interior with patch pocket": "나파 가죽 내부 · 패치 포켓",
    "Natural pearls": "내추럴 진주",
    "Non-prescription Blue Light lenses have a special filter to reduce exposure to the blue light of digital devices and sunlight.": "무도수 블루라이트 렌즈는 디지털 기기와 햇빛의 블루라이트 노출을 줄이는 특수 필터가 적용되어 있습니다.",
    "Other available colors": "다른 컬러 구성 가능",
    "Other colors available": "다른 컬러 구성 가능",
    "Painted metal lettering logo": "페인트 메탈 레터링 로고",
    "Plexiglas pin": "플렉시글라스 핀",
    "Polarized Crystal Lenses": "편광 크리스탈 렌즈",
    "Prada logo": "Prada 로고",
    "Prada logo triangle": "Prada 로고 트라이앵글",
    "Print logo": "프린트 로고",
    "Printed lettering logo": "프린트 레터링 로고",
    "Printed logo": "프린트 로고",
    "Prints: Degradé and Cars": "프린트: Degradé & Cars",
    "Prints: Degradé and Lipstick": "프린트: Degradé & Lipstick",
    "Prints: Degradé and Mouths": "프린트: Degradé & Mouths",
    "Prints: Octagon and Tulip": "프린트: Octagon & Tulip",
    "Professional fur clean only": "전문 모피 클리닝만 가능",
    "Professional leather clean only": "전문 가죽 클리닝만 가능",
    "Professionally dryclean: no trichloroethylene, reduce moisture, short cycle, no steam and low heat": "전문 드라이클리닝: 트리클로로에틸렌 금지 · 습기 최소화 · 단시간 · 스팀·고온 금지",
    "Push-button clasp": "푸시 버튼 클라스프",
    "Raffia-effect yarn": "라피아 이펙트 얀",
    "Re-Nylon interior with patch pocket": "Re-Nylon 내부 · 패치 포켓",
    "Re-Nylon lining": "Re-Nylon 안감",
    "Re-Nylon lining with zipper pocket": "Re-Nylon 안감 · 지퍼 포켓",
    "Re-Nylon logo lining with zipper pocket": "Re-Nylon 로고 안감 · 지퍼 포켓",
    "Re-press by hand": "손으로 재다림질",
    "Removable chain shoulder strap": "탈부착 체인 숄더 스트랩",
    "Removable leather wristlet": "탈부착 가죽 리스트렛",
    "Removable tote": "탈부착 토트",
    "Saffiano leather": "사피아노 가죽",
    "Saffiano leather and metal": "사피아노 가죽 & 메탈",
    "Saffiano leather handle": "사피아노 가죽 핸들",
    "Saffiano leather handle, drop 20 cm": "사피아노 가죽 핸들 · 드롭 20cm",
    "Saffiano leather strap, drop 20 cm": "사피아노 가죽 스트랩 · 드롭 20cm",
    "Satin handle": "새틴 핸들",
    "Satin interior with zipper pocket": "새틴 내부 · 지퍼 포켓",
    "Set of two elastic bands": "엘라스틱 밴드 2개 세트",
    "Set of two hair clips": "헤어 클립 2개 세트",
    "Side-release buckle on the cuff": "커프 사이드 릴리스 버클",
    "Silk lining": "실크 안감",
    "Size M": "사이즈 M",
    "Slit at wrist": "손목 슬릿",
    "Snap hook closure": "스냅 훅 클로저",
    "Snap-hook and breeze ring": "스냅 훅 & 브리즈 링",
    "Soft three-layer foam interior with moisture-wicking polar fleece lining": "3층 소프트 폼 내부 · 흡습 폴라 플리스 안감",
    "Standard Fit": "스탠다드 핏",
    "Standard fit": "스탠다드 핏",
    "Steam iron, medium": "스팀 다림질 · 중간",
    "Steel hook and split ring": "스틸 훅 & 스플릿 링",
    "Switchlock technology with 6 magnets around the frame for quick lens changes based on weather conditions": "Switchlock 기술 · 프레임 주위 6개 마그넷 · 날씨에 따른 빠른 렌즈 교환",
    "Symbole jacquard motif": "Symbole 자카드 모티프",
    "Symbole print": "Symbole 프린트",
    "Triangle logo": "트라이앵글 로고",
    "Triangle print": "Triangle 프린트",
    "Triangular metal buckle--Lettering logo": "트라이앵글 메탈 버클 · 레터링 로고",
    "Tumble drying possible low temperature; exhaust temperature max. 60 °c": "저온 건조기 사용 가능 · 배기 온도 최대 60°C",
    "Turn-lock clasp": "턴 락 클라스프",
    "Two-tone double face": "투톤 더블 페이스",
    "Two-tone double face fabric": "투톤 더블 페이스 패브릭",
    "Use press-cloth": "다리미布 사용",
    "Visible engraved logo": "비저블 각인 로고",
    "With crystals": "크리스탈 장식",
    "With internal pocket": "내부 포켓",
    "With mini pouch": "미니 파우치 포함",
    "With removable leather pendant": "탈부착 가죽 펜던트",
    "With removable leather strap": "탈부착 가죽 스트랩",
    "With snap hook": "스냅 훅",
    "With snap hook and ring": "스냅 훅 & 링",
    "With snap hook and split ring": "스냅 훅 & 스플릿 링",
    "With snap-hook and ring": "스냅 훅 & 링",
    "With snap-hook and split ring": "스냅 훅 & 스플릿 링",
    "With synthetic crystals": "합성 크리스탈",
    "Zip closure": "지퍼 클로저",
    "Zipper closure": "지퍼 클로저",
    "Zipper pocket on the back": "뒷면 지퍼 포켓",
}

FRAME_PREFIXES: list[tuple[str, str]] = [
    ("Acetate frame front - Color: ", "아세테이트 프레임 프론트 · 컬러: "),
    ("Acetate frame front in ", "아세테이트 프레임 프론트 · "),
    ("Acetate frame front - ", "아세테이트 프레임 프론트 · "),
    ("Metal frame front - Color: ", "메탈 프레임 프론트 · 컬러: "),
    ("Recycled acetate frame front - Color: ", "리사이클 아세테이트 프레임 프론트 · 컬러: "),
    ("Recycled bio-acetate frame front - Color: ", "리사이클 바이오 아세테이트 프레임 프론트 · 컬러: "),
]


def _collect_unique() -> tuple[set[str], set[str], set[str]]:
    raw = json.loads(RAW_PATH.read_text())
    descs: set[str] = set()
    details: set[str] = set()
    materials: set[str] = set()
    for product in raw["products"]:
        d = (product.get("description") or "").strip()
        if d:
            descs.add(d)
        for item in product.get("details") or []:
            s = (item or "").strip()
            if s:
                details.add(s)
        m = (product.get("material") or "").strip()
        if m:
            materials.add(m)
        for item in product.get("materialsCare") or []:
            s = (item or "").strip()
            if s:
                materials.add(s)
    return descs, details, materials


def _load_slg_reuse() -> dict[str, str]:
    if not SLG_PATH.exists():
        return {}
    slg = json.loads(SLG_PATH.read_text())
    reuse: dict[str, str] = {}
    for section in ("descriptions", "details", "materials"):
        reuse.update(slg.get(section) or {})
    return reuse


def _load_descriptions() -> dict[str, str]:
    if not DESC_DATA.exists():
        raise FileNotFoundError(f"Missing {DESC_DATA.name}")
    ns: dict[str, object] = {}
    exec(DESC_DATA.read_text(encoding="utf-8"), ns)  # noqa: S102
    descriptions = ns.get("DESCRIPTIONS")
    if not isinstance(descriptions, dict):
        raise ValueError(f"{DESC_DATA.name} must define DESCRIPTIONS dict")
    return dict(descriptions)


def translate_detail(text: str, slg_reuse: dict[str, str]) -> str:
    if text in slg_reuse:
        return slg_reuse[text]
    if text in DETAIL_EXACT:
        return DETAIL_EXACT[text]
    for prefix, ko_prefix in FRAME_PREFIXES:
        if text.startswith(prefix):
            return ko_prefix + text[len(prefix) :].replace("&amp;", "&")
    m = re.match(r"Lens-nose-temple measurements?: (.+)$", text)
    if m:
        return f"렌즈-브릿지-템플 길이: {m.group(1)}"
    m = re.match(r"Lens-nose-temple measurement : (.+)$", text)
    if m:
        return f"렌즈-브릿지-템플 길이: {m.group(1)}"
    raise KeyError(f"Missing detail translation: {text!r}")


def build_copy() -> dict[str, dict[str, str]]:
    desc_needed, detail_needed, material_needed = _collect_unique()
    slg_reuse = _load_slg_reuse()
    descriptions = dict(_load_descriptions())
    details = {s: translate_detail(s, slg_reuse) for s in sorted(detail_needed)}
    materials = dict(MATERIALS)

    for section, needed, mapping in (
        ("descriptions", desc_needed, descriptions),
        ("details", detail_needed, details),
        ("materials", material_needed, materials),
    ):
        missing = sorted(needed - set(mapping))
        if missing:
            raise SystemExit(
                f"Missing {section} translations ({len(missing)}):\n" + "\n".join(missing[:5])
            )
        for en, ko in slg_reuse.items():
            if en in needed and en not in mapping:
                mapping[en] = ko

    return {"descriptions": descriptions, "details": details, "materials": materials}


def main() -> None:
    payload = build_copy()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(
        f"Wrote {OUT_PATH} "
        f"({len(payload['descriptions'])} desc, "
        f"{len(payload['details'])} details, "
        f"{len(payload['materials'])} materials)"
    )


if __name__ == "__main__":
    main()
