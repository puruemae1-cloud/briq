#!/usr/bin/env python3
"""Curated Korean copy for Prada women's shoes (offline, no translate API).

Used by build-pr-catalog to seed the translate cache so PDPs stay natural Korean
even when Google/MyMemory rate-limit.
"""
from __future__ import annotations

# Exact product titles from Prada GB hub (officialNameEn)
TITLE_KO: dict[str, str] = {
    "Antiqued leather ballerinas": "앤틱 가죽 발레리나",
    "Antiqued leather lace-up shoes": "앤틱 가죽 레이스업 슈즈",
    "Antiqued leather pumps": "앤틱 가죽 펌프스",
    "Ayers leather pointy toe pumps": "에이어스 가죽 포인티 토 펌프스",
    "Brushed leather Monolith Mary Janes": "브러시드 가죽 모놀리스 메리제인",
    "Brushed leather Monolith loafers": "브러시드 가죽 모놀리스 로퍼",
    "Brushed leather ballerina slingbacks": "브러시드 가죽 발레리나 슬링백",
    "Brushed leather ballerinas": "브러시드 가죽 발레리나",
    "Brushed leather loafers": "브러시드 가죽 로퍼",
    "Brushed leather mules": "브러시드 가죽 뮬",
    "Brushed leather pumps": "브러시드 가죽 펌프스",
    "Brushed leather slingback pumps": "브러시드 가죽 슬링백 펌프스",
    "Chevron slingback pumps": "쉐브론 슬링백 펌프스",
    "Chocolate antiqued leather loafers": "초콜릿 앤틱 가죽 로퍼",
    "Chocolate brushed leather loafers": "초콜릿 브러시드 가죽 로퍼",
    "Chocolate printed leather loafers": "초콜릿 프린트 가죽 로퍼",
    "Chocolate suede loafers": "초콜릿 스웨이드 로퍼",
    "Collapse Re-Nylon and suede sneakers": "Collapse Re-Nylon & 스웨이드 스니커즈",
    "Collapse crochet laced sneakers": "Collapse 크로셰 레이스 스니커즈",
    "Court Re-Nylon sneakers": "Court Re-Nylon 스니커즈",
    "Court leather sneakers": "Court 가죽 스니커즈",
    "Crochet ballerinas": "크로셰 발레리나",
    "Crochet platform sandals": "크로셰 플랫폼 샌들",
    "Crochet pumps": "크로셰 펌프스",
    "Crochet sandals": "크로셰 샌들",
    "Crochet slides": "크로셰 슬라이드",
    "Downtown Bold Re-Nylon and suede sneakers": "Downtown Bold Re-Nylon & 스웨이드 스니커즈",
    "Downtown Bold nappa leather and suede sneakers": "Downtown Bold 나파 가죽 & 스웨이드 스니커즈",
    "Embroidered satin slingback pumps": "자수 새틴 슬링백 펌프스",
    "Fabric ballerinas": "패브릭 발레리나",
    "Fabric pumps": "패브릭 펌프스",
    "Fabric slingback pumps": "패브릭 슬링백 펌프스",
    "Feather-embellished satin pumps": "페더 장식 새틴 펌프스",
    "Flat mordoré nappa leather sandals": "플랫 모르도레 나파 가죽 샌들",
    "Leather and canvas boots": "가죽 & 캔버스 부츠",
    "Leather ballerinas": "가죽 발레리나",
    "Leather booties": "가죽 부티",
    "Leather boots": "가죽 부츠",
    "Leather lace-up booties": "가죽 레이스업 부티",
    "Leather lace-up shoes": "가죽 레이스업 슈즈",
    "Leather laced booties": "가죽 레이스 부티",
    "Leather loafers": "가죽 로퍼",
    "Leather mules": "가죽 뮬",
    "Leather pumps": "가죽 펌프스",
    "Leather sandals": "가죽 샌들",
    "Leather slingback pumps": "가죽 슬링백 펌프스",
    "Leather slippers": "가죽 슬리퍼",
    "Low heel mesh fabric ballerinas": "로우힐 메쉬 패브릭 발레리나",
    "Matelassé nappa leather flatform slides": "마틀라세 나파 가죽 플랫폼 슬라이드",
    "Mesh fabric and suede sneakers": "메쉬 패브릭 & 스웨이드 스니커즈",
    "Mesh fabric ballerinas": "메쉬 패브릭 발레리나",
    "Mesh fabric slingback pumps": "메쉬 패브릭 슬링백 펌프스",
    "Metallic leather high-heeled sandals": "메탈릭 가죽 하이힐 샌들",
    "Metallic leather sandals": "메탈릭 가죽 샌들",
    "Monolith brushed leather lace-up shoes": "모놀리스 브러시드 가죽 레이스업 슈즈",
    "Monolith studded leather booties": "모놀리스 스터드 가죽 부티",
    "Mordoré nappa leather sandals": "모르도레 나파 가죽 샌들",
    "Naplak patent leather ballerinas": "나플락 페이턴트 가죽 발레리나",
    "Nappa leather ballerinas": "나파 가죽 발레리나",
    "Nappa leather platform sandals": "나파 가죽 플랫폼 샌들",
    "Nappa leather sneakers": "나파 가죽 스니커즈",
    "Nubuck flatform mules": "누벅 플랫폼 뮬",
    "Nubuck mules": "누벅 뮬",
    "Nubuck slides": "누벅 슬라이드",
    "Open side patent leather pumps": "오픈 사이드 페이턴트 가죽 펌프스",
    "Open-side leather pumps": "오픈 사이드 가죽 펌프스",
    "Padded nappa leather sandals": "패디드 나파 가죽 샌들",
    "Padded suede sandals": "패디드 스웨이드 샌들",
    "Patent leather sandals": "페이턴트 가죽 샌들",
    "Patent leather thong sandals": "페이턴트 가죽 통 샌들",
    "Printed leather slingback pumps": "프린트 가죽 슬링백 펌프스",
    "Python-print Ayers leather platform sandals": "파이톤 프린트 에이어스 가죽 플랫폼 샌들",
    "Rubber Monolith sandals": "러버 모놀리스 샌들",
    "Rubber platform sandals": "러버 플랫폼 샌들",
    "Rubber slides": "러버 슬라이드",
    "Rubber thong sandals": "러버 통 샌들",
    "Saffiano patent leather slingback pumps": "사피아노 페이턴트 가죽 슬링백 펌프스",
    "Satin pumps": "새틴 펌프스",
    "Shearling lined suede booties": "시어링 안감 스웨이드 부티",
    "Shearling-lined suede booties": "시어링 안감 스웨이드 부티",
    "Shuffle antiqued leather loafers": "Shuffle 앤틱 가죽 로퍼",
    "Shuffle nubuck leather loafers": "Shuffle 누벅 가죽 로퍼",
    "Speedrock mesh fabric sneakers": "Speedrock 메쉬 패브릭 스니커즈",
    "Speedrock technical mesh and leather sneakers": "Speedrock 테크니컬 메쉬 & 가죽 스니커즈",
    "Stretch nappa leather booties": "스트레치 나파 가죽 부티",
    "Stretch nappa leather boots": "스트레치 나파 가죽 부츠",
    "Suede and shearling loafers": "스웨이드 & 시어링 로퍼",
    "Suede and shearling mules": "스웨이드 & 시어링 뮬",
    "Suede ballerinas": "스웨이드 발레리나",
    "Suede leather slingback pumps": "스웨이드 가죽 슬링백 펌프스",
    "Suede loafers": "스웨이드 로퍼",
    "Suede mules": "스웨이드 뮬",
    "Suede platform sandals": "스웨이드 플랫폼 샌들",
    "Suede pointy toe pumps": "스웨이드 포인티 토 펌프스",
    "Suede pumps": "스웨이드 펌프스",
    "Suede sandals": "스웨이드 샌들",
    "Suede slingback pumps": "스웨이드 슬링백 펌프스",
    "Suede slippers": "스웨이드 슬리퍼",
    "Suede sneakers": "스웨이드 스니커즈",
    "Toblach nappa leather booties": "Toblach 나파 가죽 부티",
    "Toblach nappa leather boots": "Toblach 나파 가죽 부츠",
    "Vintage-effect leather boots": "빈티지 이펙트 가죽 부츠",
}

COLOR_KO: dict[str, str] = {
    "Anthracite Gray": "앤트래사이트 그레이",
    "Beige": "베이지",
    "Black": "블랙",
    "Black/Tan": "블랙/탄",
    "Burgundy": "버건디",
    "Camel Brown": "카멜 브라운",
    "Chalk White": "초크 화이트",
    "Cocoa Brown": "코코아 브라운",
    "Coffee": "커피",
    "Cognac": "코냑",
    "Cord": "코드",
    "Crystal": "크리스탈",
    "Dark Brown": "다크 브라운",
    "Desert Beige": "데저트 베이지",
    "Dove Gray": "도브 그레이",
    "Ecru": "에크루",
    "Fern Green": "펀 그린",
    "Forest Green": "포레스트 그린",
    "Granite Gray": "그래니트 그레이",
    "Honey": "허니",
    "Ivory": "아이보리",
    "Natural": "내추럴",
    "Navy": "네이비",
    "Orchid Pink": "오키드 핑크",
    "Pearl Gray": "펄 그레이",
    "Peony Pink": "피오니 핑크",
    "Pineapple": "파인애플",
    "Platinum": "플래티넘",
    "Quartz": "쿼츠",
    "Red": "레드",
    "Rock Gray": "록 그레이",
    "Rosebud Pink": "로즈버드 핑크",
    "Sand Beige": "샌드 베이지",
    "Silver": "실버",
    "Teak": "티크",
    "Travertine Stone": "트래버틴 스톤",
    "Violet": "바이올렛",
    "White": "화이트",
    "White/Black": "화이트/블랙",
    "White/Blue": "화이트/블루",
}

MATERIAL_KO: dict[str, str] = {
    "Leather": "가죽",
    "Fabric": "패브릭",
    "Fabric/Leather": "패브릭/가죽",
    "Other Materials": "기타 소재",
    "Viscose": "비스코스",
}

# Exact detail lines (optional overrides; pattern engine covers the rest)
DETAIL_KO: dict[str, str] = {
    "Structure": "구조",
    "Composition": "소재 구성",
    "-Leather lining": "가죽 안감",
}

# Ordered phrase replacements for details / descriptions (longer first).
PHRASE_KO: list[tuple[str, str]] = [
    ("These shoes have undergone an artisan treatment, giving the leather a deliberate vintage look.",
     "장인 가공으로 가죽에 의도적인 빈티지 룩을 부여했습니다."),
    ("enameled metal triangle logo", "에나멜 메탈 트라이앵글 로고"),
    ("Enameled metal triangle logo", "에나멜 메탈 트라이앵글 로고"),
    ("Rubber sole with embossed logo", "러버 솔, 엠보스 로고"),
    ("with embossed logo", ", 엠보스 로고"),
    ("embossed logo", "엠보스 로고"),
    ("suede band", "스웨이드 밴드"),
    ("leather band", "가죽 밴드"),
    ("Leather band", "가죽 밴드"),
    ("logo-engraved metal buckle", "로고 각인 메탈 버클"),
    ("logo-engraved buckle", "로고 각인 버클"),
    ("leather strap", "가죽 스트랩"),
    ("Leather strap", "가죽 스트랩"),
    ("ankle strap", "앵클 스트랩"),
    ("instep strap", "인스텝 스트랩"),
    ("strap and", "스트랩 및"),
    ("straps and", "스트랩 및"),
    ("metal buckle", "메탈 버클"),
    ("metal buckles", "메탈 버클"),
    ("metal studs", "메탈 스터드"),
    ("covered buckle", "커버 버클"),
    ("hook-and-loop strap closure", "벨크로 스트랩 클로저"),
    ("metal lettering logo", "메탈 레터링 로고"),
    (" with ", " · "),
    (" and ", " 및 "),
    ("hot-stamped logo", "핫스탬프 로고"),
    ("Hot-stamped logo", "핫스탬프 로고"),
    ("screen-printed logo", "스크린 프린트 로고"),
    ("Screen-printed logo", "스크린 프린트 로고"),
    ("Screen-printed Prada Milano logo", "스크린 프린트 Prada Milano 로고"),
    ("Screen-printed Prada logo", "스크린 프린트 프라다 로고"),
    ("Screen-printed Prada triangle logo", "스크린 프린트 프라다 트라이앵글 로고"),
    ("Screen-printed leather triangle logo", "스크린 프린트 가죽 트라이앵글 로고"),
    ("Screen-printed leather logo", "스크린 프린트 가죽 로고"),
    ("Screen-printed lettering logo", "스크린 프린트 레터링 로고"),
    ("Screen-printed triangle logo", "스크린 프린트 트라이앵글 로고"),
    ("Screen-printed logo on the upper", "갑피 스크린 프린트 로고"),
    ("Removable leather-covered insole", "탈착식 가죽 커버 인솔"),
    ("Removable fabric-covered insole", "탈착식 패브릭 커버 인솔"),
    ("Removable shearling-covered insole", "탈착식 시어링 커버 인솔"),
    ("Removable leather insole", "탈착식 가죽 인솔"),
    ("Leather-covered platform and heel", "가죽 커버 플랫폼·힐"),
    ("Suede-covered platform and heel", "스웨이드 커버 플랫폼·힐"),
    ("Leather-covered wedge heel", "가죽 커버 웨지 힐"),
    ("Leather-covered heel", "가죽 커버 힐"),
    ("Fabric-covered heel", "패브릭 커버 힐"),
    ("Satin-covered heel", "새틴 커버 힐"),
    ("Suede-covered heel", "스웨이드 커버 힐"),
    ("Metallic leather heel", "메탈릭 가죽 힐"),
    ("Varnished heel", "광택 힐"),
    ("Monoblock rubber sole", "모노블록 러버 솔"),
    ("monoblock rubber sole", "모노블록 러버 솔"),
    ("rubber monobloc sole", "모노블록 러버 솔"),
    ("Leather and rubber sole", "가죽·러버 솔"),
    ("Leather and monoblock rubber sole", "가죽·모노블록 러버 솔"),
    ("Leather and rubber monoblock sole", "가죽·모노블록 러버 솔"),
    ("Monoblock rubber and leather sole", "모노블록 러버·가죽 솔"),
    ("Rubber flatform sole", "러버 플랫폼 솔"),
    ("Rubber sole", "러버 솔"),
    ("Leather sole", "가죽 솔"),
    ("EVA sole", "EVA 솔"),
    ("TPU sole", "TPU 솔"),
    ("shearling lining", "시어링 안감"),
    ("Shearling lining", "시어링 안감"),
    ("leather lining", "가죽 안감"),
    ("Leather lining", "가죽 안감"),
    ("fabric lining", "패브릭 안감"),
    ("Fabric lining", "패브릭 안감"),
    ("Perforated leather lining", "펀칭 가죽 안감"),
    ("Side zipper closure", "사이드 지퍼 클로저"),
    ("Closure with flat laces", "플랫 레이스 클로저"),
    ("Closure with laces", "레이스 클로저"),
    ("Closure with multicolored polyester laces", "멀티컬러 폴리에스터 레이스 클로저"),
    ("Laces and strap closure", "레이스·스트랩 클로저"),
    ("Laces closure", "레이스 클로저"),
    ("Flat lace closure", "플랫 레이스 클로저"),
    ("Flat laces closure", "플랫 레이스 클로저"),
    ("Elasticized laces", "신축 레이스"),
    ("Two-tone polyester laces", "투톤 폴리에스터 레이스"),
    ("Polyester laces", "폴리에스터 레이스"),
    ("Flat cotton laces", "플랫 코튼 레이스"),
    ("Cotton laces", "코튼 레이스"),
    ("Flat laces", "플랫 레이스"),
    ("Leather-covered insole", "가죽 커버 인솔"),
    ("Leather insole", "가죽 인솔"),
    ("Shearling insole", "시어링 인솔"),
    ("Leather welt with stitching", "스티치 가죽 웰트"),
    ("Leather welt", "가죽 웰트"),
    ("Rubber welt with notched detail", "노치 디테일 러버 웰트"),
    ("Notched-effect stamped rubber welt", "노치 이펙트 스탬프 러버 웰트"),
    ("Notched-effect rubber welt", "노치 이펙트 러버 웰트"),
    ("Lug tread", "러그 트레드"),
    ("Lug sole", "러그 솔"),
    ("Geometric tread", "기하학 트레드"),
    ("Patterned rubber tread", "패턴 러버 트레드"),
    ("Patterned tread", "패턴 트레드"),
    ("Notched tread", "노치 트레드"),
    ("Tread with a geometric pattern", "기하학 패턴 트레드"),
    ("Tread with geometric pattern", "기하학 패턴 트레드"),
    ("Tread with geometric lines", "기하학 라인 트레드"),
    ("Treat with geometric lines", "기하학 라인 트레드"),
    ("Tread with wave pattern", "웨이브 패턴 트레드"),
    ("Metal lettering logo", "메탈 레터링 로고"),
    ("Embroidered logo", "자수 로고"),
    ("Fabric logo label", "패브릭 로고 라벨"),
    ("Prada Milano logo embossed on the tongue", "텅에 엠보스 Prada Milano 로고"),
    ("Prada rubber triangle logo in relief", "릴리프 프라다 러버 트라이앵글 로고"),
    ("Hot-stamped logo on the tongue", "텅 핫스탬프 로고"),
    ("Rubber appliqués on the upper", "갑피 러버 아플리케"),
    ("Floral appliqué", "플로럴 아플리케"),
    ("Leather band", "가죽 밴드"),
    ("brushed leather", "브러시드 가죽"),
    ("Brushed leather", "브러시드 가죽"),
    ("antiqued leather", "앤틱 가죽"),
    ("Antiqued leather", "앤틱 가죽"),
    ("nappa leather", "나파 가죽"),
    ("Nappa leather", "나파 가죽"),
    ("patent leather", "페이턴트 가죽"),
    ("Patent leather", "페이턴트 가죽"),
    ("mesh fabric", "메쉬 패브릭"),
    ("Mesh fabric", "메쉬 패브릭"),
    ("ballerinas", "발레리나"),
    ("Ballerinas", "발레리나"),
    ("slingback pumps", "슬링백 펌프스"),
    ("Slingback pumps", "슬링백 펌프스"),
    ("loafers", "로퍼"),
    ("Loafers", "로퍼"),
    ("sneakers", "스니커즈"),
    ("Sneakers", "스니커즈"),
    ("sandals", "샌들"),
    ("Sandals", "샌들"),
    ("mules", "뮬"),
    ("Mules", "뮬"),
    ("booties", "부티"),
    ("Booties", "부티"),
    ("boots", "부츠"),
    ("Boots", "부츠"),
    ("pumps", "펌프스"),
    ("Pumps", "펌프스"),
    ("slippers", "슬리퍼"),
    ("slides", "슬라이드"),
    ("leather", "가죽"),
    ("Leather", "가죽"),
    ("suede", "스웨이드"),
    ("Suede", "스웨이드"),
    ("fabric", "패브릭"),
    ("Fabric", "패브릭"),
    ("shearling", "시어링"),
    ("Shearling", "시어링"),
    ("rubber", "러버"),
    ("Rubber", "러버"),
    ("satin", "새틴"),
    ("Satin", "새틴"),
    ("crochet", "크로셰"),
    ("Crochet", "크로셰"),
    ("nubuck", "누벅"),
    ("Nubuck", "누벅"),
    ("Prada", "프라다"),
    ("Upper with", "갑피:"),
    ("Crisscross upper with", "크로스 갑피:"),
    ("Heel height", "힐 높이"),
    ("heel height", "힐 높이"),
    ("Sole height", "솔 높이"),
    ("Boot leg height", "부츠 길이"),
    ("Boot leg", "부츠 길이"),
]


def apply_phrases(text: str) -> str:
    import re

    out = text
    for en, ko in sorted(PHRASE_KO, key=lambda kv: -len(kv[0])):
        out = re.sub(re.escape(en), ko, out, flags=re.I)
    # Leftover connective English after partial replacements
    out = re.sub(r"\band\b", "및", out, flags=re.I)
    out = re.sub(r"\bwith\b", "·", out, flags=re.I)
    out = re.sub(r"\bband\b", "밴드", out, flags=re.I)
    out = re.sub(r"\bstrap\b", "스트랩", out, flags=re.I)
    out = re.sub(r"\bbuckle\b", "버클", out, flags=re.I)
    out = re.sub(r"\bheel\b", "힐", out, flags=re.I)
    out = re.sub(r"\blayer\b", "레이어", out, flags=re.I)
    out = re.sub(r"\btip\b", "팁", out, flags=re.I)
    out = re.sub(r"\bheight\b", "높이", out, flags=re.I)
    out = re.sub(r"\bmetal\b", "메탈", out, flags=re.I)
    out = re.sub(r"\binserts\b", "인서트", out, flags=re.I)
    out = re.sub(r"\beyelets\b", "아일렛", out, flags=re.I)
    out = re.sub(r"\beyelet\b", "아일렛", out, flags=re.I)
    out = re.sub(r"\benameled\b", "에나멜", out, flags=re.I)
    out = re.sub(r"\btriangle\b", "트라이앵글", out, flags=re.I)
    out = re.sub(r"\bantiqued\b", "앤틱", out, flags=re.I)
    out = re.sub(r"\bfinish\b", "마감", out, flags=re.I)
    out = re.sub(r"\bhooks\b", "훅", out, flags=re.I)
    out = re.sub(r"\bperforations\b", "펀칭", out, flags=re.I)
    out = re.sub(r"\bfeathers\b", "페더", out, flags=re.I)
    out = re.sub(r"\bembroidery\b", "자수", out, flags=re.I)
    out = re.sub(r"\bbow\b", "보우", out, flags=re.I)
    out = re.sub(r"\bcrisscross\b", "크로스", out, flags=re.I)
    out = re.sub(r"\bcords\b", "코드", out, flags=re.I)
    out = re.sub(r"\bfront\b", "앞면", out, flags=re.I)
    out = re.sub(r"\bpiping\b", "파이핑", out, flags=re.I)
    out = re.sub(r"\bapron\b", "에이프런", out, flags=re.I)
    out = re.sub(r"\braffia\b", "라피아", out, flags=re.I)
    out = re.sub(r"\bwoven\b", "우븐", out, flags=re.I)
    out = re.sub(r"\bdetails\b", "디테일", out, flags=re.I)
    out = re.sub(r"\bexpanded\b", "발포", out, flags=re.I)
    out = re.sub(r"\blogo-print\b", "로고 프린트", out, flags=re.I)
    out = re.sub(r"\blace\b", "레이스", out, flags=re.I)
    out = re.sub(r"\bon the\b", "", out, flags=re.I)
    out = re.sub(r"\bthe\b", "", out, flags=re.I)
    out = re.sub(r"\blogo\b", "로고", out, flags=re.I)
    out = re.sub(r"\bwedge\b", "웨지", out, flags=re.I)
    out = re.sub(r"\bplatform\b", "플랫폼", out, flags=re.I)
    out = re.sub(r"\bsole\b", "솔", out, flags=re.I)
    out = re.sub(r"\bcork-covered\b", "코르크 커버", out, flags=re.I)
    out = re.sub(r"\s{2,}", " ", out)
    out = re.sub(r"\s+([,·.])", r"\1", out)
    out = re.sub(r"·\s*·", "·", out)
    return out.strip()


def detail_to_ko(text: str) -> str:
    import re

    s = (text or "").strip()
    if not s:
        return ""
    if s in DETAIL_KO:
        return DETAIL_KO[s]
    # Numeric heel / sole patterns
    m = re.match(
        r"^(Leather-covered heel(?:, height)?,?)\s*(\d+)\s*mm\.?$", s, re.I
    )
    if m:
        return f"가죽 커버 힐 {m.group(2)}mm"
    m = re.match(
        r"^(Suede-covered heel(?:, height)?,?)\s*(\d+)\s*mm\.?$", s, re.I
    )
    if m:
        return f"스웨이드 커버 힐 {m.group(2)}mm"
    m = re.match(
        r"^(Fabric-covered heel(?:, height)?,?)\s*(\d+)\s*mm\.?$", s, re.I
    )
    if m:
        return f"패브릭 커버 힐 {m.group(2)}mm"
    m = re.match(
        r"^(Satin-covered heel(?:, height)?:?)\s*(\d+)\s*mm\.?$", s, re.I
    )
    if m:
        return f"새틴 커버 힐 {m.group(2)}mm"
    m = re.match(r"^(Varnished heel(?:, height)?:?)\s*(\d+)\s*mm\.?$", s, re.I)
    if m:
        return f"광택 힐 {m.group(2)}mm"
    m = re.match(r"^Heel height:?\s*(\d+)\s*mm\.?$", s, re.I)
    if m:
        return f"힐 높이 {m.group(1)}mm"
    m = re.match(r"^Rubber sole(?:, height)?,?\s*(\d+)\s*mm\.?$", s, re.I)
    if m:
        return f"러버 솔 {m.group(1)}mm"
    m = re.match(r"^Boot leg(?: height)?:?\s*(\d+)\s*cm\.?$", s, re.I)
    if m:
        return f"부츠 길이 {m.group(1)}cm"
    m = re.match(
        r"^Monoblock rubber sole(?:,\s*(\d+)\s*mm)?(?:, with hot-stamped logo)?$",
        s,
        re.I,
    )
    if m:
        mm = m.group(1) or ""
        base = "모노블록 러버 솔" + (f" {mm}mm" if mm else "")
        if "hot-stamped" in s.lower():
            base += ", 핫스탬프 로고"
        return base
    return apply_phrases(s)


def shoe_text_ko(text: str | None) -> str | None:
    """Return curated Korean if we have an exact/offline mapping; else None."""
    s = (text or "").strip()
    if not s:
        return ""
    if s in TITLE_KO:
        return TITLE_KO[s]
    if s in COLOR_KO:
        return COLOR_KO[s]
    if s in MATERIAL_KO:
        return MATERIAL_KO[s]
    if s in DETAIL_KO:
        return DETAIL_KO[s]
    # Detail-like short lines
    if len(s) < 120 and (
        s.lower().startswith("upper ")
        or "heel" in s.lower()
        or "sole" in s.lower()
        or "lining" in s.lower()
        or "laces" in s.lower()
        or "logo" in s.lower()
        or s.lower().startswith("boot leg")
    ):
        return detail_to_ko(s)
    return None


def seed_shoe_cache(cache: dict[str, str]) -> int:
    """Merge curated shoe strings into the translate cache. Returns #keys written."""
    import json
    from pathlib import Path

    n = 0
    for mapping in (TITLE_KO, COLOR_KO, MATERIAL_KO, DETAIL_KO):
        for en, ko in mapping.items():
            cache[en] = ko
            n += 1
    desc_path = Path(__file__).resolve().parents[1] / "src/data/pr/pr-shoe-desc-ko.json"
    if desc_path.is_file():
        for en, ko in json.loads(desc_path.read_text()).items():
            cache[en] = ko
            n += 1
    return n
