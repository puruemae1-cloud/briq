"""Tell apart Bottega Veneta products that still share a title after the colour suffix.

Same name + same colour usually means another material, men's/women's cut, hardware or
detail (open-back, slip-on, high waist…). Each group gets the fewest distinguishing
labels, taken from the official English copy: "아스테어 로퍼 블랙 (여성 · 오픈백)".
When nothing in the copy differs, the product code is the last resort.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict

# (English regex, Korean label) — first matches win within a dimension, order matters.
TEXTURE: list[tuple[str, str]] = [
    (r"\bdeer", "디어스킨"),
    (r"\bostrich", "오스트리치"),
    (r"\bcrocodile", "크로커다일"),
    (r"\bpython", "파이톤"),
    (r"\bshearling", "시어링"),
    (r"\bsuede\b", "스웨이드"),
    (r"\bgrain(?:ed|y)\b", "그레인 레더"),
    (r"\bcrinkled\b", "크링클 레더"),
    (r"\bvintage[- ]effect\b", "빈티지 이펙트"),
    (r"\bweathered\b", "웨더드 레더"),
    (r"\bsoft touch\b", "소프트 터치"),
    (r"\bmatte\b", "매트"),
    (r"\bpatent\b", "페이턴트"),
    (r"\bnappa\b", "나파 레더"),
    (r"\bsmooth\b", "스무스 레더"),
    (r"\braffia\b", "라피아"),
    (r"\bmesh\b", "메시"),
    (r"\bcanvas\b", "캔버스"),
    (r"\bnylon\b", "나일론"),
    (r"\brubber\b", "러버"),
]
PATTERN: list[tuple[str, str]] = [
    (r"\bmini intrecciato\b", "미니 인트레치아토"),
    (r"\bpadded\b", "패디드"),
    (r"\bd[ée]grad[ée]\b", "그라데이션"),
    (r"\bpinstripe", "핀스트라이프"),
    (r"\bstripe", "스트라이프"),
    (r"\bgeometric\b", "지오메트릭"),
    (r"\bface print\b", "페이스 프린트"),
    (r"\bembroider", "자수"),
    (r"\bmetallic knot\b", "메탈 노트"),
    (r"\bcoin detail", "코인 장식"),
    (r"\btassel", "태슬"),
    (r"\bface brooch\b", "페이스 브로치"),
    (r"\bmetal buckle\b", "메탈 버클"),
    (r"\bhand-enamel", "에나멜"),
    (r"\bcubic zirconia\b", "큐빅"),
    (r"\bgondola", "곤돌라"),
    (r"\bengraved\b", "인그레이빙"),
    (r"\bintrecciato (?:leather )?vamp\b|\bintrecciato detailing\b", "인트레치아토 포인트"),
    (r"\ball-over intrecciato\b|\bintrecciato craft\b", "올오버 인트레치아토"),
]
SHAPE: list[tuple[str, str]] = [
    (r"\bchain ring\b|\bchain bracelet\b", "체인"),
    (r"\bhoop", "후프"),
    (r"\bwrap-around\b", "랩어라운드"),
    (r"\btwo-part\b", "투피스"),
    (r"\belectroforming\b", "일렉트로포밍"),
    (r"\bsculptural\b", "스컬프처"),
    (r"\bstud\b", "스터드"),
    (r"\bthin\b", "슬림"),
    (r"\bstretch\b", "스트레치"),
    (r"\bthroat latch\b", "스로트 래치"),
]
CLOSURE: list[tuple[str, str]] = [
    (r"\bsliding closure\b", "슬라이딩 잠금"),
    (r"\bpush(?:[- ]button)? closure\b", "푸시 잠금"),
    (r"\bt-bar\b", "T바 잠금"),
    (r"\bhook (?:system )?closure\b|\bintegrated hook\b", "후크 잠금"),
    (r"\bspring closure\b", "스프링 잠금"),
    (r"\blobster closure\b", "랍스터 잠금"),
    (r"\bhinged closure\b", "힌지 잠금"),
    (r"\bdecorative closure\b", "장식 잠금"),
    (r"\bback zip\b", "백 지퍼"),
    (r"\bside zip\b", "사이드 지퍼"),
    (r"\bwrapped\b", "랩"),
]
STYLE: list[tuple[str, str]] = [
    (r"\bopen[- ]back\b", "오픈백"),
    (r"\bslip[- ]on\b", "슬립온"),
    (r"\bmary[- ]jane\b", "메리제인"),
    (r"\bkitten heel\b", "키튼 힐"),
    (r"\bflat\b", "플랫"),
    (r"\bslim\b", "슬림"),
    (r"\bhigh[- ]waist", "하이웨이스트"),
    (r"\blow waist\b", "로우웨이스트"),
    (r"\bmid waist\b", "미드웨이스트"),
    (r"\bwide leg\b", "와이드 레그"),
    (r"\btapered\b", "테이퍼드"),
    (r"\bstraight leg\b", "스트레이트 레그"),
    (r"\bturn(?:ed)? up\b", "턴업"),
    (r"\belasticated\b", "밴딩"),
    (r"\bbelted\b", "벨티드"),
    (r"\btrucker\b", "트러커"),
    (r"\bshort coat\b", "숏"),
    (r"\bshort sleeve", "반소매"),
    (r"\blong (?:shirt|dress)\b", "롱"),
    (r"\bmidi\b", "미디"),
    (r"\bmini skirt\b", "미니"),
    (r"\bscarf neck\b", "스카프 넥"),
    (r"\bruffle", "러플 칼라"),
    (r"\bhigh neck\b", "하이넥"),
    (r"\bdiagonal\b", "다이애거널"),
    (r"\bwater[- ]repellent\b", "발수"),
    (r"\bdetachable intrecciato leather collar\b", "탈착 칼라"),
    (r"\bintrecciato (?:leather )?collar\b", "인트레치아토 칼라"),
    (r"\bintrecciato silk lapels\b", "실크 라펠"),
    (r"\bplastron\b", "플라스트론"),
    (r"\bfront pocket\b", "프런트 포켓"),
]
FIT: list[tuple[str, str]] = [
    (r"\boversized? fit\b", "오버사이즈 핏"),
    (r"\brelaxed fit\b", "릴랙스드 핏"),
    (r"\bslim fit\b", "슬림 핏"),
    (r"\bregular fit\b", "레귤러 핏"),
]
MATERIAL: list[tuple[str, str]] = [
    (r"\bthermoplastic polyurethane\b", "TPU"),
    (r"\bostrich\b", "오스트리치"),
    (r"\bdeer", "디어스킨"),
    (r"\bcalf", "카프스킨"),
    (r"\blamb", "램스킨"),
    (r"\bcashmere\b", "캐시미어"),
    (r"\bsilk\b", "실크"),
    (r"\bwool\b", "울"),
    (r"\bcotton\b", "코튼"),
    (r"\bpoly(?:amide|ester)\b", "나일론"),
    (r"\bacetate\b", "아세테이트"),
    (r"\bsterling silver\b", "스털링 실버"),
    (r"\bbrass\b", "브라스"),
]
HARDWARE_KO = {
    "silver": "실버",
    "brass": "브라스",
    "gold": "골드",
    "brass vibrato": "브라스 비브라토",
    "muse brass": "뮤즈 브라스",
    "vintage silver": "빈티지 실버",
    "matte black": "매트 블랙",
    "black": "블랙",
}


_SPEC_LINE = re.compile(r"^[•\s]*(?:lining|hardware|colou?r|material)\s*:|\bpockets?\b", re.I)


def _text(raw: dict) -> str:
    """Official copy minus lining/hardware/pocket lines, whose words describe other parts."""
    parts: list[str] = [str(raw.get("compactedLongDesc") or "")]
    for key in ("longDescription", "shortDescription"):
        parts.extend(str(x) for x in raw.get(key) or [])
    return "\n".join(x for x in parts if not _SPEC_LINE.search(x)).lower()


def _headline(raw: dict) -> str:
    """Product one-liner + intro sentence — where BV names the main material."""
    first = (raw.get("longDescription") or [""])[0]
    return f"{raw.get('compactedLongDesc') or ''}\n{first}".lower()


def _labels(text: str, table: list[tuple[str, str]], limit: int = 2) -> str:
    out: list[str] = []
    for pat, ko in table:
        if ko not in out and re.search(pat, text):
            out.append(ko)
            if len(out) >= limit:
                break
    return " ".join(out)


def _gender(p: dict, raw: dict) -> str:
    cols = set(p.get("bvCollections") or [])
    men, women = "bv-men" in cols, "bv-women" in cols
    if men != women:
        return "남성" if men else "여성"
    g = str(raw.get("gender") or "").lower()
    return {"men": "남성", "women": "여성"}.get(g, "")


def _hardware(raw: dict) -> str:
    for b in [*(raw.get("shortDescription") or []), *(raw.get("longDescription") or [])]:
        m = re.search(r"hardware:\s*(.+?)(?:\s+finish)?\s*$", str(b).strip(), re.I)
        if m:
            ko = HARDWARE_KO.get(m.group(1).strip().lower())
            return f"{ko} 하드웨어" if ko else ""
    return ""


def _laptop(text: str) -> str:
    m = re.search(r'fits an? (\d+)["”]? laptop', text)
    return f"{m.group(1)}인치 노트북" if m else ""


def _eyewear_model(text: str, with_colour: bool = False) -> str:
    """Official frame reference printed on BV eyewear PDPs ("BV1440SA 001")."""
    m = re.search(r"\b(bv\d{4}[a-z]{0,3})(?:\s+(\d{3}))?\b", text)
    if not m:
        return ""
    model = m.group(1).upper()
    return f"{model} {m.group(2)}" if with_colour and m.group(2) else model


def _alt_fit(text: str) -> str:
    return "아시안 핏" if re.search(r"\balternative fit\b", text) else ""


def _num(s: str) -> str:
    return s.replace(",", ".")


def _flag(text: str, pattern: str, label: str) -> str:
    return label if re.search(pattern, text) else ""


def _thickness(text: str) -> str:
    m = re.search(r"thickness:\s*(?:max(?:imum)?\.?\s*)?([\d.,]+)\s*mm", text)
    return f"두께 {_num(m.group(1))}mm" if m else ""


def _size(raw: dict) -> str:
    text = "\n".join(
        [str(raw.get("sizeModel") or ""), *(str(x) for x in raw.get("longDescription") or []),
         *(str(x) for x in raw.get("shortDescription") or [])]
    )
    w = re.search(r"\bwidth:\s*([\d.,]+)\s*cm", text, re.I)
    h = re.search(r"\bheight:\s*([\d.,]+)\s*cm", text, re.I)
    if w and h:
        return f"{_num(w.group(1))}×{_num(h.group(1))}cm"
    heel = re.search(r"(?:heel|flatform):\s*([\d.,]+)\s*cm", text, re.I)
    if heel:
        return f"굽 {_num(heel.group(1))}cm"
    ext = re.search(r"(?:external (?:dimensions?|size)|chain element|knot dimensions):\s*([\d.,]+)\s*x\s*([\d.,]+)\s*(mm|cm)", text, re.I)
    if ext:
        return f"{_num(ext.group(1))}×{_num(ext.group(2))}{ext.group(3).lower()}"
    length = re.search(r"^[•\s]*length:\s*([\d.,]+)\s*(mm|cm)", text, re.I | re.M)
    if length:
        return f"길이 {_num(length.group(1))}{length.group(2).lower()}"
    width = re.search(r"(?:^|[•\s])(?<!lens )(?:drop |large drop )?width:\s*(?:max\.?\s*|from\s*)?([\d.,]+)\s*(mm|cm)", text, re.I | re.M)
    if width:
        return f"폭 {_num(width.group(1))}{width.group(2).lower()}"
    lens = re.search(r"lens width:\s*([\d.,]+)\s*mm", text, re.I)
    return f"렌즈 {_num(lens.group(1))}mm" if lens else ""


def _code(p: dict) -> str:
    return "품번 " + str(p.get("id") or "").removeprefix("bv-").upper()


def product_dims(p: dict, raw: dict) -> list[str]:
    """Candidate distinguishing labels, in the order they should be tried."""
    text = _text(raw)
    head = _headline(raw)
    comp = str(raw.get("composition") or raw.get("material") or "").lower()
    return [
        _gender(p, raw),
        _eyewear_model(text),
        _eyewear_model(text, with_colour=True),
        _alt_fit(text),
        _labels(text, STYLE),
        _labels(head, TEXTURE, limit=1),
        _hardware(raw),
        _labels(text, SHAPE, limit=1),
        _labels(text, PATTERN, limit=1),
        _labels(text, CLOSURE, limit=1),
        _labels(comp, MATERIAL, limit=3),
        _labels(text, FIT, limit=1),
        _laptop(text),
        _size(raw),
        _thickness(text),
        _flag(text, r"(?m)^[•\s]*bv embroidery\s*$", "BV 로고 자수"),
        _flag(text, r"\bback patch\b", "백 패치"),
    ]


def _collisions(keys: list[tuple]) -> int:
    return sum(n - 1 for n in Counter(keys).values() if n > 1)


def distinguish_group(members: list[dict], raw_by_id: dict[str, dict]) -> dict[str, str]:
    """Suffix label (may be "") per product id so every member reads differently."""
    dims = [product_dims(p, raw_by_id.get(str(p.get("id")), {})) for p in members]
    n_dims = len(dims[0]) if dims else 0
    chosen: list[int] = []
    keys = [tuple() for _ in members]
    while _collisions(keys) > 0:
        best, best_left = None, _collisions(keys)
        for d in range(n_dims):
            if d in chosen:
                continue
            left = _collisions([k + (dims[i][d],) for i, k in enumerate(keys)])
            if left < best_left:
                best, best_left = d, left
        if best is None:
            break
        chosen.append(best)
        keys = [k + (dims[i][best],) for i, k in enumerate(keys)]
    chosen.sort()
    counts = Counter(keys)
    out: dict[str, str] = {}
    for i, p in enumerate(members):
        labels = [dims[i][d] for d in chosen if dims[i][d]]
        if counts[keys[i]] > 1:
            labels.append(_code(p))
        out[str(p.get("id"))] = " · ".join(labels)
    return out


def distinguish_same_names(products: list[dict], raw_by_id: dict[str, dict]) -> int:
    """Append "(…)" labels to products whose nameKo is still shared. Returns renamed count."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for p in products:
        groups[str(p.get("nameKo") or "").strip()].append(p)
    renamed = 0
    for name, members in groups.items():
        if len(members) < 2 or not name:
            continue
        labels = distinguish_group(members, raw_by_id)
        for p in members:
            label = labels[str(p.get("id"))]
            if label:
                p["nameKo"] = f"{name} ({label})"
                renamed += 1
    return renamed
