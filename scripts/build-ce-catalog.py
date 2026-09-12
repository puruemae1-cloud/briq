#!/usr/bin/env python3
"""Build Briq Celine catalog from scraped raw files.

Currently supports the first Celine pipeline: men's ready-to-wear.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from celine_config import celine_raw_paths  # noqa: E402
from celine_common import (  # noqa: E402
    IMG_ROOT,
    clean_html_text,
    is_blocked_pdp_title,
    load_json,
    save_json,
    slugify,
    title_from_pdp_url,
)
from di_common import gbp_to_krw  # noqa: E402
from ce_prose_ko import prose_to_ko  # noqa: E402
from ko_qa import gtx_translate, has_hangul, is_good_korean  # noqa: E402

OUT_JSON = ROOT / "src/data/ce/ce-catalog.json"
OUT_TS = ROOT / "src/data/ce/ce-catalog.ts"
CACHE = ROOT / "src/data/ce/ce-translate-cache.json"

ACCENTS = ["#1A1A1A", "#291f1d", "#302722", "#382e29", "#1f2529"]
TITLE_MAP = {
    "celine": "셀린느",
    "triomphe": "트리옹프",
    "vivienne": "비비안",
    "scarves": "스카프",
    "scarf": "스카프",
    "shawls": "숄",
    "shawl": "숄",
    "bandana": "반다나",
    "cashmere": "캐시미어",
    "skirts": "스커트",
    "skirt": "스커트",
    "dresses": "드레스",
    "dress": "드레스",
    "shirts": "셔츠",
    "shirt": "셔츠",
    "blouses": "블라우스",
    "blouse": "블라우스",
    "t-shirts": "티셔츠",
    "t-shirt": "티셔츠",
    "t shirt": "티셔츠",
    "long sleeved": "롱슬리브",
    "long sleeve": "롱슬리브",
    "short sleeved": "숏슬리브",
    "short sleeve": "숏슬리브",
    "sleeveless": "슬리브리스",
    "tops": "탑",
    "top": "탑",
    "classic": "클래식",
    "loose": "루즈",
    "oversized": "오버사이즈",
    "overshirt": "오버셔츠",
    "cotton poplin": "코튼 포플린",
    "cotton denim": "코튼 데님",
    "cotton twill": "코튼 트윌",
    "cotton jersey": "코튼 저지",
    "cotton gabardine": "코튼 개버딘",
    "light cotton gabardine": "라이트 코튼 개버딘",
    "cotton": "코튼",
    "fleece": "플리스",
    "viscose satin": "비스코스 새틴",
    "viscose": "비스코스",
    "satin": "새틴",
    "mohair wool": "모헤어 울",
    "mohair": "모헤어",
    "wool": "울",
    "silk twill": "실크 트윌",
    "silk": "실크",
    "corduroy": "코듀로이",
    "gabardine": "개버딘",
    "taurillon leather": "토리용 레더",
    "taurillon": "토리용",
    "vegetal tanning": "베지탈 태닝",
    "vegetable tanning": "베지탈 태닝",
    "laminated lambskin": "라미네이트 램스킨",
    "laminated": "라미네이트",
    "shiny lambskin": "샤이니 램스킨",
    "shiny": "샤이니",
    "smooth": "스무스",
    "natural": "내추럴",
    "printed": "프린트",
    "patchwork": "패치워크",
    "heritage": "헤리티지",
    "pants": "팬츠",
    "trousers": "팬츠",
    "shorts": "쇼츠",
    "jacket": "재킷",
    "jackets": "재킷",
    "coat": "코트",
    "coats": "코트",
    "leather": "레더",
    "shearling": "시어링",
    "lambskin": "램스킨",
    "calfskin": "카프스킨",
    "goatskin": "고트스킨",
    "suede": "스웨이드",
    "nubuck": "누벅",
    "grained": "그레인",
    "grain": "그레인",
    "vintage": "빈티지",
    "canvas": "캔버스",
    "denim": "데님",
    "sweatshirt": "스웨트셔츠",
    "knitwear": "니트웨어",
    "jewellery": "주얼리",
    "jewelry": "주얼리",
    "sunglasses": "선글라스",
    "wallets": "월렛",
    "wallet": "월렛",
    "card holder": "카드홀더",
    "bags": "가방",
    "bag": "백",
    "belt": "벨트",
    "belts": "벨트",
    "buckle": "버클",
    "reversible strap": "리버시블 스트랩",
    "reversible": "리버시블",
    "strap": "스트랩",
    "disc": "디스크",
    "helium": "헬륨",
    "boots": "부츠",
    "boot": "부츠",
    "ankle boot": "앵클 부츠",
    "sock booty": "삭 부티",
    "booty": "부티",
    "sandals": "샌들",
    "sandal": "샌들",
    "heeled sandal": "힐 샌들",
    "thong sandal": "통 샌들",
    "wedge sandal": "웨지 샌들",
    "wedge mule": "웨지 뮬",
    "wedge": "웨지",
    "mule": "뮬",
    "slide": "슬라이드",
    "sneakers": "스니커즈",
    "sneaker": "스니커즈",
    "lace up sneaker": "레이스업 스니커즈",
    "lace-up sneaker": "레이스업 스니커즈",
    "lace up": "레이스업",
    "lace-up": "레이스업",
    "pumps": "펌프스",
    "pump": "펌프스",
    "loafers": "로퍼",
    "loafer": "로퍼",
    "ballerinas": "발레리나",
    "ballerina": "발레리나",
    "heeled ballerina": "힐 발레리나",
    "soft oxford": "소프트 옥스포드",
    "oxford": "옥스포드",
    "cage heeled sandal": "케이지 힐 샌들",
    "cage": "케이지",
    "heeled": "힐",
    "heel": "힐",
    "thong": "통",
    "double strap": "더블 스트랩",
    "peplum": "페플럼",
    "racer": "레이서",
    "flared": "플레어",
    "cropped": "크롭",
    "embroidered": "자수",
    "embroidery": "자수",
    "western": "웨스턴",
    "mini": "미니",
    "medium": "미디엄",
    "large": "라지",
    "small": "스몰",
    "low": "로우",
    "high": "하이",
    "crew neck": "크루넥",
    "hoodie": "후디",
    "parka": "파카",
    "trench": "트렌치",
    "blazer": "블레이저",
    "cardigan": "가디건",
    "polo": "폴로",
    "pajama": "파자마",
    "pyjama": "파자마",
    "bikini": "비키니",
    "swimsuit": "수영복",
    "swimwear": "스윔웨어",
    "lingerie": "란제리",
    "bracelet": "브레이슬릿",
    "necklace": "네크리스",
    "earring": "이어링",
    "earrings": "이어링",
    "ring": "링",
    "brooch": "브로치",
    "scrunchy": "스크런치",
    "hat": "햇",
    "cap": "캡",
    "beanie": "비니",
    "glove": "글러브",
    "gloves": "글러브",
    "keyring": "키링",
    "charm": "참",
    "phone holder": "폰홀더",
    # Model / proper-name phonetics (fashion titles)
    "lou": "루",
    "cleo": "클레오",
    "clea": "클레아",
    "onyx": "오닉스",
    "sunny": "써니",
    "scout": "스카우트",
    "cady": "케이디",
    "bc 28": "BC 28",
    "bc 27": "BC 27",
    "bc 25": "BC 25",
    "bc 17": "BC 17",
    "bc 03": "BC 03",
    "waxed effect": "왁스드 이펙트",
    "waxed": "왁스드",
    "crocodile embossed": "크로커다일 엠보스",
    "embossed": "엠보스",
    "crocodile": "크로커다일",
    "foulard": "풀라드",
    "ribbons": "리본",
    "ribbon": "리본",
    "ties": "타이",
    "double face": "더블페이스",
    "richelieu": "리슐리외",
    "baseball": "베이스볼",
    "drill": "드릴",
    "caleche": "칼레슈",
    "nightandday": "나이트앤데이",
    "night and day": "나이트앤데이",
    "rosemary": "로즈메리",
    "patched": "패치드",
    "piano fringe": "피아노 프린지",
    "fringe": "프린지",
    "little": "리틀",
    "prize": "프라이즈",
    "sky": "스카이",
    "effect": "이펙트",
    "metal": "메탈",
    "brass": "브라스",
    "gold finish": "골드 피니시",
    "gold": "골드",
    "silver": "실버",
    "black": "블랙",
    "white": "화이트",
    "navy": "네이비",
    "beige": "베이지",
    "brown": "브라운",
    "grey": "그레이",
    "gray": "그레이",
    "red": "레드",
    "green": "그린",
    "blue": "블루",
    "pink": "핑크",
    "orange": "오렌지",
    "yellow": "옐로우",
    "khaki": "카키",
    "tan": "탠",
    "ivory": "아이보리",
    "cream": "크림",
    "bordeaux": "보르도",
    "burgundy": "버건디",
    "aviator": "에비에이터",
    "rectangle": "렉탱글",
    "cat eye": "캣아이",
    "cat-eye": "캣아이",
    "monochrome": "모노크롬",
    "logo": "로고",
    "hooded": "후드",
    "hood": "후드",
    "zipped": "지퍼",
    "zip": "지퍼",
    "buttoned": "버튼",
    "button": "버튼",
    "pocket": "포켓",
    "pockets": "포켓",
    "pleated": "플리츠",
    "straight": "스트레이트",
    "wide leg": "와이드 레그",
    "wide-leg": "와이드 레그",
    "skinny": "스키니",
    "slim": "슬림",
    "regular": "레귤러",
    "fitted": "핏티드",
    "boxy": "박시",
    "asymmetric": "비대칭",
    "wrapped": "랩",
    "wrap": "랩",
    "drawstring": "드로스트링",
    "elastic": "엘라스틱",
    "ribbed": "립",
    "quilted": "퀼팅",
    "padded": "패딩",
    "fur": "퍼",
    "jersey": "저지",
    "poplin": "포플린",
    "twill": "트윌",
    "flannel": "플란넬",
    "chiffon": "시폰",
    "organza": "오간자",
    "lace": "레이스",
    "mesh": "메쉬",
    "nylon": "나일론",
    "polyester": "폴리에스터",
    "linen": "린넨",
    "alpaca": "알파카",
    "merino": "메리노",
    "boucle": "부클레",
    "tweed": "트위드",
    "velvet": "벨벳",
    "patent": "페이턴트",
    "matte": "매트",
    "glossy": "글로시",
    "transparent": "투명",
    "opaque": "불투명",
    "with": " ",
    " and ": " ",
}
LINE_MAP = {
    "100% cotton": "100% 면",
    "100% wool": "100% 울",
    "triomphe embroidery": "트리옹프 자수",
    "celine embroidery": "셀린느 자수",
    "classic fit": "클래식 핏",
    "regular fit": "레귤러 핏",
    "loose fit": "루즈 핏",
    "oversized fit": "오버사이즈 핏",
    "mid rise": "미드 라이즈",
    "high rise": "하이 라이즈",
    "low rise": "로우 라이즈",
    "2 side pockets": "사이드 포켓 2개",
    "2 side pocket": "사이드 포켓 2개",
    "1 back pocket": "백 포켓 1개",
    "raw hems": "로우 헴",
    "raw hem": "로우 헴",
    "italy made": "이탈리아 제작",
    "made in italy": "이탈리아 제작",
    "portugal made": "포르투갈 제작",
    "made in portugal": "포르투갈 제작",
    "france made": "프랑스 제작",
    "made in france": "프랑스 제작",
    "japan made": "일본 제작",
    "made in japan": "일본 제작",
    "middle waist": "미들 웨이스트",
    "calfskin lining": "카프스킨 안감",
    "unlined": "안감 없음",
    "lining": "안감",
    "line dry.": "평평하게 건조해 주세요.",
    "line dry": "평평하게 건조해 주세요.",
    "line dry without spin.": "탈수 없이 평평하게 건조해 주세요.",
    "line dry without spin": "탈수 없이 평평하게 건조해 주세요.",
    "do not use steam.": "스팀을 사용하지 마십시오.",
    "do not use steam": "스팀을 사용하지 마십시오.",
    "elasticated waistband": "엘라스틱 웨이스트밴드",
    "elasticated waistband with adjustable drawstrings and celine engraved metal aglets": "엘라스틱 웨이스트밴드, 조절 가능한 드로스트링, 셀린느 각인 메탈 애글리트",
    "elasticated waistband adjustable drawstrings celine engraved metal aglets": "엘라스틱 웨이스트밴드, 조절 가능한 드로스트링, 셀린느 각인 메탈 애글리트",
    "elasticated waistband with adjustable drawstrings": "엘라스틱 웨이스트밴드, 조절 가능한 드로스트링",
    "elasticated waistband adjustable drawstrings": "엘라스틱 웨이스트밴드, 조절 가능한 드로스트링",
    "the loose celine shape is a large fit with dropped shoulders.": "느슨한 셀린느 실루엣은 드롭 숄더의 여유 있는 핏입니다.",
    "it is possible to take one size down from your usual size for a more fitted look.": "평소 사이즈보다 한 사이즈 아래로 선택하면 더 몸에 꼭 맞는 룩을 연출할 수 있습니다.",
    "shirt collar with collar stays": "카라 스테이가 포함된 셔츠 칼라",
    "buttoned cuffs": "버튼 커프스",
    "7 celine paris-engraved mother-of-pearl buttons": "CELINE PARIS 각인 자개 버튼 7개",
    "1 celine paris-engraved mother-of-pearl button on the cuffs": "커프스 CELINE PARIS 각인 자개 버튼 1개",
    "the classic celine shape fits true to size. we suggest taking your usual size.": "셀린느의 클래식 실루엣 기준 정사이즈로 제안됩니다. 평소 선택하시는 사이즈를 권장합니다.",
    "the item can be washed on a delicate cycle at a maximum temperature of 30°c / 85°f.": "최대 30°C의 섬세 코스로 세탁해 주세요.",
    "only use bleach-free laundry products.": "표백 성분이 없는 세제를 사용해 주세요.",
    "do not tumble dry.": "건조기 사용은 권장되지 않습니다.",
    "maximum ironing temperature: 150°c / 302°f": "다림질 최대 온도는 150°C입니다.",
    "maximum ironing temperature: 110°c / 230°f": "최대 다림질 온도: 110°C/230°F",
    "the item can be delicately dry cleaned with hydrocarbons": "하이드로카본 계열로 약하게 드라이클리닝할 수 있습니다.",
    "we suggest taking your usual size.": "평소 선택하시는 사이즈를 권장합니다.",
    "fits true to size.": "정사이즈로 제안됩니다.",
    "classic celine shape fits true to size.": "셀린느의 클래식 실루엣 기준 정사이즈로 제안됩니다.",
    "the classic celine shape fits true to size.": "셀린느의 클래식 실루엣 기준 정사이즈로 제안됩니다.",
}


def translate_cache() -> dict[str, str]:
    return load_json(CACHE, {})


def tr(
    text: str | None,
    cache: dict[str, str],
    *,
    allow_remote: bool = True,
    prose: bool = False,
) -> str:
    """Translate copy. Titles may use TITLE_MAP; PDP prose must never (avoids EN/KO hybrids)."""
    s = clean_html_text(text or "")
    if not s:
        return ""
    low = re.sub(r"\s+", " ", re.sub(r"[-–—]+", " ", s.lower())).strip()
    for key in (low, low.rstrip(" ."), low.rstrip("."), re.sub(r"[.]+$", "", low)):
        if key in LINE_MAP:
            cache[s] = LINE_MAP[key]
            return cache[s]
    # Common fit guidance patterns (keep natural KO, not glossary hybrids)
    if "loose celine shape" in low and "dropped shoulders" in low:
        cache[s] = "느슨한 셀린느 실루엣은 드롭 숄더의 여유 있는 핏입니다."
        return cache[s]
    if "one size down" in low and "fitted look" in low:
        cache[s] = "평소 사이즈보다 한 사이즈 아래로 선택하면 더 몸에 꼭 맞는 룩을 연출할 수 있습니다."
        return cache[s]
    if "fits true to size" in low and "usual size" in low:
        cache[s] = "셀린느의 클래식 실루엣 기준 정사이즈로 제안됩니다. 평소 선택하시는 사이즈를 권장합니다."
        return cache[s]
    if has_hangul(s) and is_good_korean(s):
        cache[s] = s
        return s
    # Pure codes / widths / symbols — keep as-is
    if re.fullmatch(r"[\d\s./%°CFXx×:\-()CMWcmw]+", s):
        cache[s] = s
        return s
    fast = os.environ.get("BRIQ_FAST_BUILD") == "1"
    if prose:
        # Prefer offline prose map (stable KO). Skip stale cache hybrids.
        local = prose_to_ko(s)
        want_remote = allow_remote and os.environ.get("BRIQ_CE_REMOTE") == "1" and not fast
        if local and is_good_korean(local):
            cache[s] = local
            return local
        if not want_remote:
            # Accept best local effort even if a few EN tokens remain (motif names, etc.).
            cache[s] = local or s
            return cache[s]
    if s in cache and is_good_korean(cache[s]):
        return cache[s]
    if prose:
        want_remote = allow_remote and os.environ.get("BRIQ_CE_REMOTE") == "1" and not fast
        local = prose_to_ko(s)
        if not want_remote:
            cache[s] = local or s
            return cache[s]
        try:
            out = gtx_translate(s)
            time.sleep(0.05)
        except Exception:
            out = local or s
        out = out or local or s
        if out and is_good_korean(out):
            cache[s] = out
            return out
        cache[s] = local or out
        return cache[s]
    dicted = clean_title_ko(s)
    if fast or not allow_remote:
        cache[s] = dicted or s
        return cache[s]
    try:
        out = gtx_translate(s)
        time.sleep(0.05)
        out = clean_title_ko(out or dicted or s)
    except Exception:
        out = dicted or s
    if out:
        cache[s] = out
    return out or s


def clean_title_ko(text: str) -> str:
    out = text.strip()
    # Longer phrases first; word-boundary replace to avoid partial hits.
    for en, ko in sorted(TITLE_MAP.items(), key=lambda kv: -len(kv[0])):
        en = en.strip()
        if not en:
            continue
        replacement = (ko or " ").strip() if ko.strip() else " "
        # Allow spaces inside multi-word keys; still require edges.
        pattern = re.compile(rf"(?<![A-Za-z0-9]){re.escape(en)}(?![A-Za-z0-9])", re.I)
        out = pattern.sub(replacement, out)
    # "Name IN material" → "material Name"
    m = re.match(r"^(.*?)\s+IN\s+(.+)$", out, flags=re.I)
    if m:
        left, right = m.group(1).strip(" ;,-"), m.group(2).strip(" ;,-")
        out = f"{right} {left}".strip()
    out = re.sub(r"\bIN\b", "", out, flags=re.I)
    out = re.sub(r"\bTHE\b", "", out, flags=re.I)
    out = re.sub(r"\bWITH\b", "", out, flags=re.I)
    out = re.sub(r"\bAND\b", " ", out, flags=re.I)
    out = re.sub(r"\s*[-–—]\s*", " ", out)
    out = re.sub(r"\s{2,}", " ", out).strip(" ;,-")
    return out


def tag_bundle(row: dict) -> list[str]:
    leaf = str(row.get("leafId") or "")
    tags = ["celine", "셀린느"]
    if "-men-" in leaf or leaf == "ce-men":
        tags += ["men", "남성"]
    if "-women-" in leaf or leaf == "ce-women":
        tags += ["women", "여성"]
    if any(x in leaf for x in ["shirts", "tshirts", "sweatshirts", "knitwear", "denim", "pants", "tailoring", "coats", "jackets", "leather", "rtw"]):
        tags += ["rtw", "ready-to-wear"]
    elif "swim" in leaf and not is_ce_swim_accessory(str(row.get("title") or ""), leaf):
        tags += ["rtw", "ready-to-wear", "swimwear", "스윔웨어"]
    elif "bags" in leaf or leaf.endswith("-bag"):
        tags += ["bags", "가방"]
    elif "shoes" in leaf or any(x in leaf for x in ["boots", "sneakers", "loafers", "sandals", "pumps"]):
        tags += ["shoes", "슈즈"]
    else:
        tags += ["accessories", "악세서리"]
    return list(dict.fromkeys(tags))


def extract_lines(row: dict, label: str) -> list[str]:
    details = row.get("details") or []
    for item in details:
        if (item.get("label") or "").strip().lower() == label.lower():
            html = item.get("html") or ""
            body = item.get("body") or ""
            raw = html if html else body
            lines = [
                clean_html_text(x)
                for x in re.split(r"<br\s*/?>|\n", raw, flags=re.I)
            ]
            lines = [x for x in lines if x and not x.lower().startswith("reference :")]
            if lines:
                return lines
            merged = clean_html_text(body)
            return [merged] if merged else []
    return []


def build_size_chart(row: dict) -> dict | None:
    guide = row.get("sizeGuide") or {}
    headers = guide.get("headers") or []
    rows = guide.get("rows") or []
    if not headers or not rows:
        return None
    title = headers[1] if len(headers) > 1 else "사이즈 가이드"
    title_ko = clean_title_ko(title.upper().title()) or title
    return {
        "id": f"ce-{slugify(title)}",
        "titleKo": f"셀린느 {title_ko} 사이즈 가이드",
        "noteKo": "공식 셀린느 사이즈 가이드를 기준으로 정리했습니다.",
        "headers": headers,
        "rows": rows,
    }


def size_sort_key(size: str) -> tuple:
    s = str(size or "").strip()
    order = ["XXXS", "XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL"]
    if s.upper() in order:
        return (0, order.index(s.upper()), s)
    m = re.search(r"(\d+(?:\.\d+)?)", s)
    if m:
        return (1, float(m.group(1)), s)
    return (2, s)


def build_variants(product_id: str, row: dict, price: int) -> list[dict]:
    sizes = sorted({str(x).strip() for x in (row.get("sizes") or []) if str(x).strip()}, key=size_sort_key)
    images = existing_ce_images(row.get("images") or [])
    image = images[0] if images else "/products/ce-pdp/placeholder.jpg"
    if not sizes:
        sizes = ["OS"]
    # Celine SKUs are one colourway each; sizes must share colorKey so PDP
    # shows size chips instead of identical image swatches per size.
    color = row.get("color") if isinstance(row.get("color"), dict) else {}
    color_label = str((color or {}).get("label") or (color or {}).get("label_int") or "").strip()
    color_key = product_id
    color_name_ko = color_label if color_label else "기본"
    out = []
    for size in sizes:
        out.append(
            {
                "id": f"{product_id}-sz-{slugify(size, max_len=24)}",
                "name": size,
                "nameKo": "원 사이즈" if size == "OS" else size,
                "sku": row.get("sku") or product_id,
                "gbpPrice": float(row.get("gbpPrice") or 0),
                "price": price,
                "image": image,
                "images": images,
                "sourceUrl": row.get("url") or "",
                "inStock": row_in_stock(row),
                "colorKey": color_key,
                "colorNameKo": color_name_ko,
                "size": size,
                "ceCollections": row.get("collections") or [],
            }
        )
    return out


def leaf_to_category(leaf: str) -> str:
    leaf = leaf or ""
    if "bags" in leaf:
        return "bags"
    if "shoes" in leaf or any(
        x in leaf for x in ["boots", "sneakers", "loafers", "sandals", "pumps", "ballet", "ballerina"]
    ):
        return "shoes"
    # Beach wraps / towels scraped under swimwear are accessories, not apparel.
    if "swim" in leaf:
        return "luxury"  # apparel swimsuits only; accessories overridden in resolve_placement
    # Celine RTW leaves must stay under luxury so /shop?category=luxury&sub=… matches.
    if any(
        x in leaf
        for x in [
            "shirts",
            "blouses",
            "tshirts",
            "tops",
            "sweatshirts",
            "knitwear",
            "denim",
            "pants",
            "shorts",
            "skirts",
            "dresses",
            "tailoring",
            "coats",
            "jackets",
            "leather",
            "rtw",
            "-rtw",
        ]
    ):
        return "luxury"
    return "accessories"


_CE_SWIM_ACCESSORY_RE = re.compile(
    r"\b(pareo|sarong|fouta|towel|beach\s*towel|beach\s*blanket)\b",
    re.I,
)
_CE_SWIM_APPAREL_RE = re.compile(
    r"\b(triangle|bandeau|balconette|swimsuit|swimwear|bikini|bottom|one[\s-]?piece)\b",
    re.I,
)


def is_ce_swim_accessory(title: str, leaf: str = "") -> bool:
    """Pareo / towel / fouta live under swim scrape but are not clothing."""
    if "swim" not in (leaf or "") and not _CE_SWIM_ACCESSORY_RE.search(title or ""):
        return False
    if _CE_SWIM_ACCESSORY_RE.search(title or ""):
        return True
    return False


def resolve_placement(row: dict) -> tuple[str, str, list[str]]:
    """Return (category, subcategory, ceCollections) with non-apparel corrections."""
    leaf = str(row.get("leafId") or "").strip() or "ce-men-rtw-all"
    title = str(row.get("title") or "")
    collections = list(dict.fromkeys(row.get("collections") or []))

    if is_ce_swim_accessory(title, leaf) or (
        "swim" in leaf and not _CE_SWIM_APPAREL_RE.search(title) and _CE_SWIM_ACCESSORY_RE.search(title)
    ):
        sub = "ce-women-other-accessories"
        cols = [
            "celine",
            "celine-accessories",
            "ce-women-accessories",
            "ce-women-other-accessories",
            "ce-women-acc-all",
        ]
        return "accessories", sub, list(dict.fromkeys(cols))

    return leaf_to_category(leaf), leaf, collections


def build_story(
    description_ko: str,
    images: list[str],
    features_ko: list[str],
    *,
    care_ko: list[str] | None = None,
    fit_ko: list[str] | None = None,
) -> list[dict]:
    sections = [
        {
            "titleKo": "제품 소개",
            "bodyKo": description_ko,
            "image": images[0] if images else "",
        }
    ]
    if features_ko:
        sections.append(
            {
                "titleKo": "디테일 & 특징",
                "bodyKo": " · ".join(features_ko[:10]),
                "image": images[min(1, len(images) - 1)] if images else "",
            }
        )
    if care_ko:
        sections.append(
            {
                "titleKo": "케어 & 관리",
                "bodyKo": " ".join(care_ko[:3]) if len(care_ko[0]) > 80 else " · ".join(care_ko[:4]),
                "image": images[min(2, len(images) - 1)] if images else "",
                "reverse": True,
            }
        )
    if fit_ko:
        sections.append(
            {
                "titleKo": "착용 & 스타일",
                "bodyKo": " · ".join(fit_ko[:4]),
                "image": images[min(3, len(images) - 1)] if images else "",
            }
        )
    if len(images) > 2:
        sections.append(
            {
                "titleKo": "스타일링",
                "bodyKo": "셀린느 공식 이미지로 실루엣과 소재의 분위기를 확인할 수 있습니다.",
                "image": images[min(len(images) - 1, 4)] if images else "",
                "reverse": True,
            }
        )
    return sections


def local_ce_images(sku_or_id: str) -> list[str]:
    folder = slugify(str(sku_or_id or "").replace(".", "-"))
    if not folder:
        return []
    paths = sorted((IMG_ROOT / folder).glob("*.jpg"))
    return [f"/products/ce-pdp/{folder}/{p.name}" for p in paths if p.stat().st_size >= 800]


def existing_ce_images(images: list[str] | None) -> list[str]:
    """Keep only gallery paths that exist on disk (avoids broken PDP thumbs)."""
    out: list[str] = []
    for rel in images or []:
        if not rel or "placeholder" in rel:
            continue
        local = ROOT / "public" / str(rel).lstrip("/")
        if local.is_file() and local.stat().st_size >= 800:
            out.append(rel)
    return out


def heal_raw_row(row: dict) -> dict:
    """Repair Access Denied poison, missing images, and false sold-out flags."""
    row = dict(row)
    title = (row.get("title") or "").strip()
    sku = str(row.get("sku") or row.get("id") or "").strip()
    if is_blocked_pdp_title(title) or not title:
        recovered = title_from_pdp_url(row.get("url") or "")
        if recovered:
            row["title"] = recovered
            title = recovered
    images = [x for x in (row.get("images") or []) if x and "placeholder" not in x]
    if not images:
        images = local_ce_images(sku) or local_ce_images(str(row.get("id") or ""))
    images = existing_ce_images(images) or local_ce_images(sku) or local_ce_images(str(row.get("id") or ""))
    row["images"] = images

    # Legacy scrapes used only `AVAILABLE NOW` body text → mass false sold-outs.
    # Fully scraped PDPs (images + details/sizes) with availability False and no
    # confident OOS signal should be treated as in stock.
    conf = str(row.get("availabilityConfidence") or "")
    if row.get("scrapeBlocked") or is_blocked_pdp_title(title):
        row["availability"] = None
        row["availabilityConfidence"] = "blocked"
    elif row.get("availability") is False and conf not in {
        "sold_out",
        "schema_oos",
        "sfcc_oos",
    }:
        blob = " ".join(
            [
                title,
                str(row.get("url") or ""),
                " ".join(str(d.get("body") or "") for d in (row.get("details") or []) if isinstance(d, dict)),
            ]
        )
        if re.search(r"\bsold[\s-]?out\b|\bout of stock\b|\bnotify me\b", blob, re.I):
            row["availabilityConfidence"] = "sold_out"
        elif images and (row.get("details") or row.get("sizes")):
            row["availability"] = True
            row["availabilityConfidence"] = "healed_full_pdp"
        elif images:
            # Listed with photos but weak availability scrape — stay available.
            row["availability"] = True
            row["availabilityConfidence"] = "healed_listed"
        else:
            row["availability"] = None
            row["availabilityConfidence"] = "unknown"
    return row


def row_in_stock(row: dict) -> bool:
    """Missing/None availability ⇒ in stock (do not coerce None→False)."""
    if "availability" not in row or row.get("availability") is None:
        return True
    return bool(row.get("availability"))


def build_product(row: dict, cache: dict[str, str], idx: int) -> dict:
    row = heal_raw_row(row)
    sku = str(row.get("sku") or row.get("id") or "").strip()
    pid = f"ce-{slugify(sku.replace('.', '-'))}"
    title_en = (row.get("title") or sku).strip()
    if is_blocked_pdp_title(title_en):
        title_en = title_from_pdp_url(row.get("url") or "") or sku
    title_ko = tr(title_en, cache, allow_remote=True) or clean_title_ko(title_en) or title_en
    # Force another translate pass when nameKo is still English-only.
    if title_ko and not has_hangul(title_ko) and title_en:
        title_ko = tr(title_en, cache, allow_remote=True) or title_ko
    gbp = float(row.get("gbpPrice") or 0)
    price = gbp_to_krw(gbp)
    images = existing_ce_images(row.get("images") or [])
    image = images[0] if images else "/products/ce-pdp/placeholder.jpg"
    details_en = extract_lines(row, "DETAILS")
    care_en = extract_lines(row, "CARE AND MAINTENANCE")
    fit_en = extract_lines(row, "Size and fit")
    features_ko = [
        y for x in details_en[:12] if (y := tr(x, cache, allow_remote=True, prose=True))
    ]
    # Prefer one natural care summary when official copy is a long multi-bullet guide.
    care_joined = " ".join(care_en)
    care_summary = tr(care_joined, cache, allow_remote=True, prose=True) if care_joined else ""
    if care_summary and len(care_joined) > 180:
        care_ko = [care_summary]
    else:
        care_ko = [y for x in care_en[:6] if (y := tr(x, cache, allow_remote=True, prose=True))]
    fit_ko = [y for x in fit_en[:6] if (y := tr(x, cache, allow_remote=True, prose=True))]
    desc_parts = []
    if features_ko:
        desc_parts.append(" / ".join(features_ko[:4]))
    if fit_ko:
        desc_parts.append(" ".join(fit_ko[:2]))
    description_ko = "\n\n".join([x for x in desc_parts if x]).strip() or title_ko
    size_chart = build_size_chart(row)
    variants = build_variants(pid, row, price)

    category, subcategory, ce_collections = resolve_placement(row)

    material_hit = [
        x
        for x in features_ko
        if any(
            k in x
            for k in (
                "%",
                "면",
                "레더",
                "램스킨",
                "카프스킨",
                "울",
                "캐시미어",
                "실크",
                "린넨",
                "코튼",
                "나일론",
                "폴리",
            )
        )
    ][:1]
    tech_specs = []
    for label, values in (
        ("디테일", features_ko[:1]),
        ("소재", material_hit),
    ):
        if values:
            tech_specs.append({"labelKo": label, "valueKo": values[0]})
    cat_ko_by_bucket = {
        "bags": "가방",
        "shoes": "슈즈",
        "accessories": "악세서리",
        "luxury": "시그니처 의류",
        "watches": "시계",
    }
    if category == "accessories" and is_ce_swim_accessory(title_en, str(row.get("leafId") or "")):
        tech_specs.append({"labelKo": "카테고리", "valueKo": "악세서리"})
    elif category in cat_ko_by_bucket:
        tech_specs.append({"labelKo": "카테고리", "valueKo": cat_ko_by_bucket[category]})
    elif row.get("categoryLabel"):
        category_ko = clean_title_ko(str(row["categoryLabel"]).replace("/", " / ").title())
        tech_specs.append({"labelKo": "카테고리", "valueKo": category_ko})
    elif subcategory:
        tech_specs.append(
            {
                "labelKo": "카테고리",
                "valueKo": clean_title_ko(subcategory.replace("ce-", "").replace("-", " ").title())
                or subcategory,
            }
        )

    features = []
    for block in (features_ko, care_ko, fit_ko):
        for line in block:
            if line and line not in features:
                features.append(line)

    return {
        "id": pid,
        "name": title_en,
        "nameKo": title_ko,
        "brand": "Celine",
        "category": category,
        "subcategory": subcategory,
        "ceCollections": ce_collections,
        "tags": tag_bundle(row),
        "descriptionKo": description_ko,
        "image": image,
        "images": images,
        "accent": ACCENTS[idx % len(ACCENTS)],
        "gbpPrice": gbp,
        "sku": sku,
        "sourceUrl": row.get("url") or "",
        "inStock": row_in_stock(row),
        "variants": variants,
        "storySections": build_story(
            description_ko, images, features_ko, care_ko=care_ko, fit_ko=fit_ko
        ),
        "techSpecs": tech_specs,
        "featuresKo": features,
        "sizeChart": size_chart,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    cache = translate_cache()
    by_id: dict[str, dict] = {}
    rows: list[dict] = []
    raw_paths = celine_raw_paths()
    if not raw_paths:
        raise SystemExit("no ce-*-catalog-raw.json files found")
    for path in raw_paths:
        payload = load_json(path, {"products": []})
        rows.extend(payload.get("products") or [])
    for idx, row in enumerate(rows):
        if not row.get("id"):
            continue
        p = build_product(row, cache, idx)
        by_id[p["id"]] = p
        if (idx + 1) % 10 == 0:
            save_json(CACHE, cache)
            print(f"built {idx+1}/{len(rows)}", flush=True)

    products = list(by_id.values())
    save_json(CACHE, cache)
    save_json(OUT_JSON, products)
    OUT_TS.parent.mkdir(parents=True, exist_ok=True)
    # Thin TS wrapper only — embedding the full catalog in .ts OOMs Vercel builds.
    OUT_TS.write_text(
        "/* Auto-generated by scripts/build-ce-catalog.py — do not edit */\n"
        'import type { Product } from "@/data/product-types";\n'
        'import data from "./ce-catalog.json";\n'
        "\n"
        "/** Celine catalog (JSON import keeps the TS module small for Vercel builds). */\n"
        "export const ceCatalogProducts = data as unknown as Product[];\n"
    )
    print(f"wrote {len(products)} products -> {OUT_JSON} + {OUT_TS}", flush=True)


if __name__ == "__main__":
    main()
