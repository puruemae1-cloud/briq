"""Bottega Veneta line names stay in English inside Korean titles (조디 → Jodie).

Machine translation either transliterates line names (조디, 안디아모) or translates them
literally (Sardine → 정어리, Parachute → 낙하산, Drop Ring → 반지 떨어뜨리기). Size words
follow Korean retail spelling (작은 → 스몰, 큰 → 라지). A rule only fires when the official
English name contains that word, so unrelated Korean words are never touched.
"""
from __future__ import annotations

import re

# (word in the official English name, Korean renderings in nameKo, replacement)
MODEL_RULES: list[tuple[str, str, str]] = [
    (r"andiamo", r"안디아모", "Andiamo"),
    (r"jodie", r"조디", "Jodie"),
    (r"cabat", r"카바트|카밧", "Cabat"),
    (r"a mano", r"아 마노", "A Mano"),
    (r"mare", r"메어|마레", "Mare"),
    (r"sardine", r"정어리", "Sardine"),
    (r"diago", r"디아고|다이아고", "Diago"),
    (r"astaire", r"아스테어", "Astaire"),
    (r"orbit", r"오비트|오르빗", "Orbit"),
    (r"flash", r"플래시", "Flash"),
    (r"cassette", r"카세트", "Cassette"),
    (r"piccolo", r"피콜로", "Piccolo"),
    (r"prisma", r"프리즘|프리즈마", "Prisma"),
    (r"veneta", r"베네타", "Veneta"),
    (r"veneto", r"베네토", "Veneto"),
    (r"campana", r"카파나|캄파나|종", "Campana"),
    (r"riva", r"리바", "Riva"),
    (r"barbara", r"바바라", "Barbara"),
    (r"silenzio", r"실렌지오", "Silenzio"),
    (r"palazzo", r"팔라초|팔라조", "Palazzo"),
    (r"sunday", r"일요일", "Sunday"),
    (r"parachute", r"낙하산|패러슈트", "Parachute"),
    (r"cherry", r"체리", "Cherry"),
    (r"rosa", r"로사", "Rosa"),
    (r"fin", r"핀|지느러미", "Fin"),
    (r"claw", r"발톱|클로", "Claw"),
    (r"pinacoteca", r"피나코테카", "Pinacoteca"),
    (r"serena", r"세레나", "Serena"),
    (r"charlotte", r"샬롯", "Charlotte"),
    (r"onda", r"온다", "Onda"),
    (r"solo", r"솔로", "Solo"),
    (r"madison", r"매디슨", "Madison"),
    (r"lauren", r"로렌", "Lauren"),
    (r"blink", r"블링크", "Blink"),
    (r"odys?s?ey|odissey", r"오디세이", "Odyssey"),
    (r"shot", r"샷", "Shot"),
    (r"haddock", r"해덕|해독", "Haddock"),
    (r"sampieri", r"삼피에리", "Sampieri"),
    (r"elio", r"엘리오", "Elio"),
    (r"loop", r"루프", "Loop"),
    (r"sophia", r"소피아", "Sophia"),
    (r"livia", r"리비아", "Livia"),
    (r"traveler", r"여행자용|여행자", "Traveler"),
    (r"nodo", r"노도", "Nodo"),
    (r"notte", r"노테", "Notte"),
    (r"sawyer", r"소여", "Sawyer"),
    (r"dawson", r"도슨", "Dawson"),
    (r"tosca", r"토스카", "Tosca"),
    (r"giorno", r"일|조르노", "Giorno"),
    (r"parco", r"파르코", "Parco"),
    (r"angolo", r"앙골로", "Angolo"),
    (r"ugo", r"우고", "Ugo"),
    (r"pier", r"피어", "Pier"),
    (r"corso", r"코르소", "Corso"),
    (r"allegra", r"알레그라", "Allegra"),
    (r"sabato", r"사바토", "Sabato"),
    (r"veneziana", r"베네치아|베네치아나", "Veneziana"),
    (r"fantasmina", r"판타스미나", "Fantasmina"),
    (r"notturno", r"녹턴|노투르노", "Notturno"),
    (r"concert", r"콘서트", "Concert"),
    (r"voyager", r"보야저|보이저", "Voyager"),
    (r"corriere", r"코리에레", "Corriere"),
    (r"romeo", r"로미오", "Romeo"),
    (r"glaston", r"글래스턴", "Glaston"),
    (r"gino", r"지노", "Gino"),
    (r"rocco", r"로코", "Rocco"),
    (r"tarik", r"타릭", "Tarik"),
    (r"bacio", r"바치오", "Bacio"),
    (r"ovetto", r"오베토", "Ovetto"),
    (r"vesta", r"베스타", "Vesta"),
    (r"sumo", r"스모", "Sumo"),
    (r"soffietto", r"소피에토", "Soffietto"),
    (r"orto", r"오르토", "Orto"),
    (r"vaulta", r"볼타", "Vaulta"),
    (r"tide", r"타이드", "Tide"),
    (r"rob", r"롭", "Rob"),
    (r"lug", r"러그", "Lug"),
    (r"klog", r"클로그", "Klog"),
    (r"spicchio", r"스피키오|조각", "Spicchio"),
    (r"rosita", r"로시타", "Rosita"),
    (r"salsa", r"살사", "Salsa"),
    (r"wallace", r"월리스", "Wallace"),
    (r"twillie", r"트윌리", "Twillie"),
    (r"scudo", r"스쿠도", "Scudo"),
    (r"mezzanotte", r"메짜노테|메차노테", "Mezzanotte"),
    (r"scaletta", r"스칼레타", "Scaletta"),
    (r"grace", r"그레이스", "Grace"),
    (r"rana", r"라나", "Rana"),
    (r"getaway weekender", r"주말 여행용 가방|주말 여행", "Getaway 위켄더"),
    (r"getaway", r"게터웨이|도주용", "Getaway"),
    (r"bang bang", r"방 방|뱅 뱅", "Bang Bang"),
    (r"dizzy", r"어지러운|디지", "Dizzy"),
    (r"candy", r"캔디", "Candy"),
    (r"forte", r"포르테", "Forte"),
    (r"dash", r"대시", "Dash"),
    (r"knot", r"매듭|노트", "Knot"),
    (r"drop", r"드롭|물방울|방울", "Drop"),
    (r"1998", r"1998년", "1998"),
]

# Size words and literal / half-translated product words — every category.
WORD_RULES: list[tuple[str, str, str]] = [
    (r"small", r"작은|소형|작은 크기", "스몰"),
    (r"large", r"큰|대형|큰 크기", "라지"),
    (r"medium", r"중간 크기|중간", "미디엄"),
    (r"baby", r"아기", "베이비"),
    (r"maxi", r"막시", "맥시"),
    (r"aviator", r"비행사|파일럿|아비에이터", "에비에이터"),
    (r"cat eye", r"고양이 눈", "캣아이"),
    (r"butterfly", r"나비", "버터플라이"),
    (r"thong", r"통", "쏭"),
    (r"sandal", r"산달", "샌들"),
    (r"mule", r"뮬레", "뮬"),
    (r"soft", r"부드러운", "소프트"),
    (r"east-west", r"동서", "이스트웨스트"),
    (r"dustbag", r"먼지주머니", "더스트백"),
    (r"bi-fold", r"Bi-Fold", "바이폴드"),
    (r"with coin purse", r"지갑 With 코인 퍼스", "코인 퍼스 지갑"),
    (r"flap", r"Flap", "플랩"),
    (r"long", r"Long", "롱"),
    (r"key", r"Key", "키"),
    (r"faded", r"Faded", "페이디드"),
    (r"cloudy", r"Cloudy", "클라우디"),
]

# Clothing names use these words as fabric/style terms (Palazzo Jeans, Parachute Shirt).
SKIP_MODEL_CATEGORIES = {"luxury"}

_COMPILED = [
    (re.compile(rf"\b(?:{en})\b", re.I), re.compile(rf"(?<!\S)(?:{ko})(?!\S)"), out)
    for en, ko, out in MODEL_RULES
]
_WORDS = [
    (re.compile(rf"\b(?:{en})\b", re.I), re.compile(rf"(?<!\S)(?:{ko})(?!\S)"), out)
    for en, ko, out in WORD_RULES
]
_DROP_TAIL = re.compile(r"^(.+?) 떨어뜨리기$")
MODEL_WORDS = {out for _, _, out in MODEL_RULES if re.fullmatch(r"[A-Za-z0-9 ]+", out)}


def anglicize_models(name_ko: str, name_en: str, category: str = "") -> str:
    """Korean title with BV line names in English and retail size words."""
    out = (name_ko or "").strip()
    en = name_en or ""
    if not out:
        return out
    if category not in SKIP_MODEL_CATEGORIES:
        if re.search(r"\bdrop\b", en, re.I):
            m = _DROP_TAIL.match(out)
            if m:
                out = f"Drop {m.group(1)}"
        for en_re, ko_re, repl in _COMPILED:
            if en_re.search(en):
                out = ko_re.sub(repl, out)
    for en_re, ko_re, repl in _WORDS:
        if en_re.search(en):
            out = ko_re.sub(repl, out)
    return re.sub(r"\s{2,}", " ", out).strip()


def is_model_english(name_ko: str) -> bool:
    """True when the only Latin words in a title are BV line names / codes (not untranslated copy)."""
    rest = name_ko or ""
    for word in sorted(MODEL_WORDS, key=len, reverse=True):
        rest = re.sub(rf"\b{re.escape(word)}\b", " ", rest)
    rest = re.sub(r"\bBV\d{3,5}[A-Z]{0,3}\b|\b[0-9A-Z]{10,}\b", " ", rest)
    return not re.search(r"[A-Za-z]{3,}", rest)
