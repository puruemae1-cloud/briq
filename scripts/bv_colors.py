"""Bottega Veneta colour names → Korean retail spelling, plus same-name disambiguation.

Machine translation renders BV's poetic colour names literally ("Blush" → 붉어지다,
"Mineral" → 무기염류, "Cardinal" → 추기경). Korean luxury retail transliterates
them instead, so product titles use this glossary token by token ("A/B" → "가/나").
"""
from __future__ import annotations

import re
from collections import defaultdict

BV_COLOR_KO: dict[str, str] = {
    "abyss": "어비스",
    "air": "에어",
    "alabaster": "알라바스터",
    "algae": "알가",
    "alpi green": "알피 그린",
    "always now": "올웨이즈 나우",
    "amber": "앰버",
    "ambra": "암브라",
    "anthracite": "앤트러사이트",
    "anthracite melange": "앤트러사이트 멜란지",
    "ardoise": "아르두아즈",
    "ardoise melange": "아르두아즈 멜란지",
    "aubergine": "오베르진",
    "avocado": "아보카도",
    "azurite": "아주라이트",
    "ballerina": "발레리나",
    "balliamo": "발리아모",
    "bare morning": "베어 모닝",
    "bark green": "바크 그린",
    "barolo": "바롤로",
    "barolo multi": "바롤로 멀티",
    "basalt": "바솔트",
    "basil": "바질",
    "beige": "베이지",
    "beige melange": "베이지 멜란지",
    "bianco": "비앙코",
    "billiard": "빌리어드",
    "bitter chocolate": "비터 초콜릿",
    "black": "블랙",
    "black grass": "블랙 그래스",
    "blood stone": "블러드 스톤",
    "blu venezia": "블루 베네치아",
    "blue": "블루",
    "blue bell": "블루벨",
    "blue gravel": "블루 그래블",
    "blue ink": "블루 잉크",
    "blue royal": "블루 로열",
    "blue shirt": "블루 셔츠",
    "blue shirt melange": "블루 셔츠 멜란지",
    "blue venezia": "블루 베네치아",
    "blush": "블러시",
    "bone": "본",
    "bordeaux": "보르도",
    "bronze": "브론즈",
    "brow": "브라우",
    "brown": "브라운",
    "bubble": "버블",
    "buff": "버프",
    "burgundy": "버건디",
    "burned orange": "번트 오렌지",
    "burnt umber": "번트 엄버",
    "butter": "버터",
    "butter yellow": "버터 옐로우",
    "buttercup": "버터컵",
    "buttermilk": "버터밀크",
    "caiman": "카이만",
    "camel": "카멜",
    "camel melange": "카멜 멜란지",
    "camelia": "카멜리아",
    "cameo": "카메오",
    "camo": "카모",
    "camomile": "카모마일",
    "camomille": "카모마일",
    "cane sugar": "케인 슈거",
    "caramel": "카라멜",
    "cardinal": "카디널",
    "carrubo": "카루보",
    "carrubo mel": "카루보 멜란지",
    "cedar": "시더",
    "chalk": "초크",
    "champ": "샴페인",
    "charcoal": "차콜",
    "charcoal melange": "차콜 멜란지",
    "cherry": "체리",
    "cherry tomato": "체리 토마토",
    "chestnut melange": "체스트넛 멜란지",
    "chili": "칠리",
    "chocolate": "초콜릿",
    "cinnabar": "시나바",
    "cioccolato": "초콜라토",
    "citrine": "시트린",
    "cloud": "클라우드",
    "cloudy indigo": "클라우디 인디고",
    "clove": "클로브",
    "cookie blue": "쿠키 블루",
    "crave": "크레이브",
    "crepuscolo": "크레푸스콜로",
    "crocodile": "크로커다일",
    "cruise": "크루즈",
    "cypress": "사이프러스",
    "dark antracite": "다크 앤트러사이트",
    "dark apple candy": "다크 애플 캔디",
    "dark barolo": "다크 바롤로",
    "dark bison": "다크 바이슨",
    "dark blue": "다크 블루",
    "dark caramel": "다크 카라멜",
    "dark caramel 20": "다크 카라멜",
    "dark carrubo": "다크 카루보",
    "dark forest": "다크 포레스트",
    "dark green": "다크 그린",
    "dark grey": "다크 그레이",
    "dark grey melange": "다크 그레이 멜란지",
    "dark indigo": "다크 인디고",
    "dark juniper": "다크 주니퍼",
    "dark jute melange": "다크 주트 멜란지",
    "dark leather": "다크 레더",
    "dark moss": "다크 모스",
    "dark navy": "다크 네이비",
    "dark olive": "다크 올리브",
    "dark praline": "다크 프랄린",
    "dark red": "다크 레드",
    "dark slate melange": "다크 슬레이트 멜란지",
    "dark taupe": "다크 토프",
    "deep blue": "딥 블루",
    "deep caramel": "딥 카라멜",
    "deep mahogany": "딥 마호가니",
    "deep moss": "딥 모스",
    "deep red": "딥 레드",
    "denim": "데님",
    "desert": "데저트",
    "desert taupe": "데저트 토프",
    "dim grey": "딤 그레이",
    "doll": "돌",
    "double black": "더블 블랙",
    "double espresso": "더블 에스프레소",
    "dove": "도브",
    "ebony": "에보니",
    "eclipse": "이클립스",
    "ecru": "에크루",
    "emerald": "에메랄드",
    "emerald green": "에메랄드 그린",
    "espresso": "에스프레소",
    "flash green": "플래시 그린",
    "flash red": "플래시 레드",
    "flower": "플라워",
    "fond": "퐁",
    "fondant": "퐁당",
    "fountain": "파운틴",
    "frassino": "프라시노",
    "garnet": "가넷",
    "glacial": "글레이셜",
    "glacier": "글레이셔",
    "gloss": "글로스",
    "glossy wood": "글로시 우드",
    "gold": "골드",
    "gold caramel": "골드 카라멜",
    "graphite": "그라파이트",
    "grass": "그래스",
    "grass green": "그래스 그린",
    "gravel": "그래블",
    "green": "그린",
    "green marble alpi": "그린 마블 알피",
    "green oasis": "그린 오아시스",
    "green tweed": "그린 트위드",
    "greige": "그레이지",
    "grey": "그레이",
    "grey clay": "그레이 클레이",
    "grey dim": "그레이 딤",
    "grey melange": "그레이 멜란지",
    "grey putty": "그레이 퍼티",
    "grey seal": "그레이 실",
    "harbor grey": "하버 그레이",
    "havana": "하바나",
    "hemp": "헴프",
    "hibiscus": "히비스커스",
    "himalaya": "히말라야",
    "ice": "아이스",
    "iceberg": "아이스버그",
    "indigo": "인디고",
    "intense carrubo": "인텐스 카루보",
    "ivory": "아이보리",
    "jalapeno": "할라피뇨",
    "jam": "잼",
    "jungle": "정글",
    "jute": "주트",
    "kale": "케일",
    "kiwi": "키위",
    "lake": "레이크",
    "lapis": "라피스",
    "lava": "라바",
    "lava mel": "라바 멜란지",
    "lava red": "라바 레드",
    "liana": "리아나",
    "light bleach": "라이트 블리치",
    "light blue": "라이트 블루",
    "light blue gravel": "라이트 블루 그래블",
    "light dandelion": "라이트 댄디라이언",
    "light grey": "라이트 그레이",
    "light grey melange": "라이트 그레이 멜란지",
    "light wenge mel": "라이트 웬지 멜란지",
    "light wood": "라이트 우드",
    "lighthouse": "라이트하우스",
    "lilac": "라일락",
    "limestone": "라임스톤",
    "limone": "리모네",
    "linen melange": "리넨 멜란지",
    "macadamia": "마카다미아",
    "madder brown": "매더 브라운",
    "malachite": "말라카이트",
    "matcha": "말차",
    "matte black": "매트 블랙",
    "medallion": "메달리온",
    "medium grey": "미디엄 그레이",
    "medium grey melange": "미디엄 그레이 멜란지",
    "merlot": "메를로",
    "metallic mist": "메탈릭 미스트",
    "mid blue": "미드 블루",
    "mid grey": "미드 그레이",
    "midnight": "미드나잇",
    "midnight blue": "미드나잇 블루",
    "mineral": "미네랄",
    "mirth washed": "머스 워시드",
    "mist": "미스트",
    "mojave beige": "모하비 베이지",
    "moment after": "모먼트 애프터",
    "montebello": "몬테벨로",
    "mud": "머드",
    "multi": "멀티",
    "muse brass": "뮤즈 브라스",
    "mustard": "머스터드",
    "nail polish": "네일 폴리시",
    "natural": "내추럴",
    "natural pink": "내추럴 핑크",
    "navy": "네이비",
    "navy 302": "네이비",
    "navy melange": "네이비 멜란지",
    "neptune": "넵튠",
    "nero": "네로",
    "nero opaco": "네로 오파코",
    "new amber": "뉴 앰버",
    "night": "나이트",
    "night residue": "나이트 레지듀",
    "night sounds": "나이트 사운즈",
    "nightfall": "나이트폴",
    "nocciola": "노촐라",
    "noce": "노체",
    "nocturnal": "녹터널",
    "oat cocoa": "오트 코코아",
    "obsidian grey": "옵시디언 그레이",
    "ocean": "오션",
    "old wood": "올드 우드",
    "olive": "올리브",
    "olive oil": "올리브 오일",
    "optic white": "옵틱 화이트",
    "optic white rubber": "옵틱 화이트 러버",
    "optical": "옵티컬",
    "orange": "오렌지",
    "oxblood melange": "옥스블러드 멜란지",
    "oxford blue": "옥스퍼드 블루",
    "pale blue": "페일 블루",
    "pale brown": "페일 브라운",
    "pale herb": "페일 허브",
    "pale meringue": "페일 머랭",
    "pale oak": "페일 오크",
    "pale pink": "페일 핑크",
    "papermoon": "페이퍼문",
    "parakeet": "패러킷",
    "parch": "파치먼트",
    "parchment": "파치먼트",
    "peach": "피치",
    "pearl grey": "펄 그레이",
    "pearl grey melange": "펄 그레이 멜란지",
    "pecan": "피칸",
    "petroleum": "페트롤리엄",
    "pickle": "피클",
    "pine forest": "파인 포레스트",
    "pine green": "파인 그린",
    "pinecone": "파인콘",
    "pink": "핑크",
    "pink shell": "핑크 셸",
    "platinum": "플래티넘",
    "polar": "폴라",
    "pollen": "폴렌",
    "pop red": "팝 레드",
    "popcorn": "팝콘",
    "powder pink": "파우더 핑크",
    "prairie": "프레리",
    "prosecco": "프로세코",
    "pudding": "푸딩",
    "pumice": "퍼미스",
    "python": "파이톤",
    "racing green": "레이싱 그린",
    "raintree": "레인트리",
    "red": "레드",
    "red jasper": "레드 재스퍼",
    "red marble": "레드 마블",
    "red stone": "레드 스톤",
    "redstone": "레드스톤",
    "ribbon": "리본",
    "rice": "라이스",
    "ricordami": "리코르다미",
    "ristretto": "리스트레토",
    "riverbed melange": "리버베드 멜란지",
    "roccia": "로치아",
    "rock crystal quartz": "록 크리스털 쿼츠",
    "rock melange": "록 멜란지",
    "rosewood": "로즈우드",
    "royal blue": "로열 블루",
    "rubber": "러버",
    "rust": "러스트",
    "ruthenium": "루테늄",
    "sahara": "사하라",
    "sahara mel": "사하라 멜란지",
    "sandshell melange": "샌드셸 멜란지",
    "sapele": "사펠레",
    "scarlet": "스칼렛",
    "sea salt": "씨 솔트",
    "seasalt": "씨 솔트",
    "seaweed": "씨위드",
    "sepia brown": "세피아 브라운",
    "sesame": "세서미",
    "shadow": "섀도",
    "shamrock": "샴록",
    "sherbert": "셔벗",
    "shore": "쇼어",
    "shrub": "슈럽",
    "sienna brown": "시에나 브라운",
    "silica grey": "실리카 그레이",
    "silt": "실트",
    "silver": "실버",
    "slate melange": "슬레이트 멜란지",
    "slow rise": "슬로 라이즈",
    "smoke": "스모크",
    "solstice": "솔스티스",
    "sour": "사워",
    "space": "스페이스",
    "squill": "스퀼",
    "star anise": "스타 아니스",
    "steel": "스틸",
    "sterling": "스털링",
    "sterling mel": "스털링 멜란지",
    "sterling melange": "스털링 멜란지",
    "stone": "스톤",
    "stone brown": "스톤 브라운",
    "stone melange": "스톤 멜란지",
    "straw": "스트로",
    "string": "스트링",
    "stucco": "스투코",
    "stucco melange": "스투코 멜란지",
    "sulfur": "설퍼",
    "sunflower": "선플라워",
    "syrup": "시럽",
    "taffy": "태피",
    "tannin": "타닌",
    "tapioca": "타피오카",
    "tarragon": "타라곤",
    "taxi": "택시",
    "teak": "티크",
    "teal": "틸",
    "terra pink": "테라 핑크",
    "thistle": "시슬",
    "thunder": "썬더",
    "tobacco": "토바코",
    "toffee": "토피",
    "transparent": "트랜스페어런트",
    "travertine": "트래버틴",
    "trench": "트렌치",
    "tufo": "투포",
    "turquoise": "터쿼이즈",
    "tuscany brown": "투스카니 브라운",
    "utility blue": "유틸리티 블루",
    "vanilla": "바닐라",
    "velvet steps": "벨벳 스텝스",
    "vernis": "베르니",
    "violet": "바이올렛",
    "wader green": "웨이더 그린",
    "washed black": "워시드 블랙",
    "wenge": "웬지",
    "wheatfield": "휘트필드",
    "white": "화이트",
    "white grey": "화이트 그레이",
    "wine": "와인",
    "wood": "우드",
    "yellow": "옐로우",
    "yellow gold": "옐로우 골드",
    "zesty": "제스티",
}


def color_ko_from_en(en: str) -> str | None:
    """Glossary Korean for an official BV colour ("Black/muse brass" → "블랙/뮤즈 브라스").

    Returns None when any token is unknown so callers keep their translated value.
    """
    parts = [t.strip() for t in re.split(r"\s*/\s*", (en or "").strip()) if t.strip()]
    if not parts:
        return None
    out: list[str] = []
    for part in parts:
        ko = BV_COLOR_KO.get(re.sub(r"\s+", " ", part.lower()))
        if not ko:
            return None
        if ko not in out:
            out.append(ko)
    return "/".join(out)


def unknown_color_tokens(en: str) -> list[str]:
    parts = [t.strip() for t in re.split(r"\s*/\s*", (en or "").strip()) if t.strip()]
    return [p for p in parts if re.sub(r"\s+", " ", p.lower()) not in BV_COLOR_KO]


def product_color_ko(p: dict) -> str:
    for spec in p.get("techSpecs") or []:
        if spec.get("labelKo") == "색상" and str(spec.get("valueKo") or "").strip():
            return str(spec["valueKo"]).strip()
    for v in p.get("variants") or []:
        c = str(v.get("colorNameKo") or "").strip()
        if c and c != "기본":
            return c
    return ""


def apply_color_ko(p: dict, new_ko: str) -> bool:
    """Swap the product's Korean colour everywhere it is shown (specs, swatches, bullets)."""
    old = product_color_ko(p)
    if not new_ko or old == new_ko:
        return False
    for spec in p.get("techSpecs") or []:
        if spec.get("labelKo") == "색상":
            spec["valueKo"] = new_ko
    for v in p.get("variants") or []:
        if old and v.get("colorNameKo") == old:
            v["colorNameKo"] = new_ko
            if v.get("nameKo") == old:
                v["nameKo"] = new_ko
            if v.get("name") == old:
                v["name"] = new_ko
    if old:
        pat = re.compile(r"(색상\s*:\s*)" + re.escape(old) + r"(?=\s*$|\n)", re.M)
        p["featuresKo"] = [pat.sub(lambda m: m.group(1) + new_ko, str(f)) for f in p.get("featuresKo") or []]
        if isinstance(p.get("descriptionKo"), str):
            p["descriptionKo"] = pat.sub(lambda m: m.group(1) + new_ko, p["descriptionKo"])
        for sec in p.get("storySections") or []:
            if isinstance(sec.get("bodyKo"), str):
                sec["bodyKo"] = pat.sub(lambda m: m.group(1) + new_ko, sec["bodyKo"])
    return True


def _base_name(p: dict, color: str) -> str:
    nk = str(p.get("nameKo") or "").strip()
    base = str(p.get("nameKoBase") or "").strip()
    if base and (nk == base or nk.startswith(base + " ")):
        return base
    # nameKo was rewritten elsewhere (build / KO repair) — drop any colour tail we added.
    if color and nk.endswith(" " + color):
        return nk[: -len(color) - 1].strip()
    return nk


def disambiguate_names_by_color(products: list[dict]) -> int:
    """Append the Korean colour when several products share one nameKo but differ in colour.

    Idempotent: the uncoloured title is kept in ``nameKoBase`` so re-runs never stack suffixes.
    """
    groups: dict[str, list[tuple[dict, str]]] = defaultdict(list)
    for p in products:
        color = product_color_ko(p)
        groups[_base_name(p, color)].append((p, color))
    changed = 0
    for base, rows in groups.items():
        colors = {c for _, c in rows if c}
        suffix = len(rows) > 1 and len(colors) > 1
        for p, color in rows:
            want = f"{base} {color}" if suffix and color else base
            if p.get("nameKo") != want:
                p["nameKo"] = want
                changed += 1
            if want != base:
                p["nameKoBase"] = base
            else:
                p.pop("nameKoBase", None)
    return changed


def raw_colors_by_id() -> dict[str, str]:
    """Official English colour per catalogue id, read from the scraped hub JSON."""
    from bv_common import load_json, slugify
    from bv_config import HUB_ORDER, HUBS_BY_ID, RAW_DIR

    out: dict[str, str] = {}
    for hub_id in HUB_ORDER:
        data = load_json(RAW_DIR / HUBS_BY_ID[hub_id]["out"], {})
        for row in (data.get("products") if isinstance(data, dict) else None) or []:
            smc = str(row.get("id") or row.get("sku") or "")
            color = str(row.get("color") or "").strip()
            if smc and color:
                out.setdefault(f"bv-{slugify(smc)}", color)
    return out


def normalize_bv_names(products: list[dict], colors_en: dict[str, str] | None = None) -> dict:
    """Glossary colours + colour-suffixed titles for same-name products. Returns stats."""
    colors_en = raw_colors_by_id() if colors_en is None else colors_en
    recolored = 0
    unknown: set[str] = set()
    for p in products:
        en = colors_en.get(str(p.get("id") or ""))
        if not en:
            continue
        ko = color_ko_from_en(en)
        if ko is None:
            unknown.update(unknown_color_tokens(en))
            continue
        if apply_color_ko(p, ko):
            recolored += 1
    renamed = disambiguate_names_by_color(products)
    return {"recolored": recolored, "renamed": renamed, "unknown": sorted(unknown)}


def duplicate_name_groups(products: list[dict]) -> list[tuple[str, int]]:
    """nameKo groups that still share a title while their colours differ (should be empty)."""
    groups: dict[str, set[str]] = defaultdict(set)
    counts: dict[str, int] = defaultdict(int)
    for p in products:
        nk = str(p.get("nameKo") or "").strip()
        color = product_color_ko(p)
        if color:
            groups[nk].add(color)
        counts[nk] += 1
    return sorted((k, counts[k]) for k, cs in groups.items() if counts[k] > 1 and len(cs) > 1)
