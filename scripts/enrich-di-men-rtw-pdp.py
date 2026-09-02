#!/usr/bin/env python3
"""Enrich Dior men's RTW catalog: Algolia variants, size charts, rich PDP copy.

Fast by default (no live translate — glossary + cache + heuristics only).
Checkpoints every 25 SKUs so chat crashes do not lose progress.

  python3 scripts/enrich-di-men-rtw-pdp.py
  python3 scripts/enrich-di-men-rtw-pdp.py --only 013C501A4743_C080
  python3 scripts/enrich-di-men-rtw-pdp.py --translate   # slow: live translate missing
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from di_common import algolia_merch_hits_by_codes, algolia_variant_gbp, gbp_to_krw, slugify  # noqa: E402
from di_size_charts import size_chart_for_di_mens_rtw  # noqa: E402
from ko_qa import gtx_translate, is_good_korean  # noqa: E402

CAT = ROOT / "src/data/di/di-catalog.json"
PDP_CACHE = ROOT / "src/data/di/di-men-rtw-pdp-cache.json"
RAW = ROOT / "src/data/di/di-men-rtw-catalog-raw.json"
TRANSLATE_CACHE = ROOT / "src/data/di/di-translate-cache.json"
CHECKPOINT_EVERY = 25

RTW_LEAVES = {
    "di-mens",
    "di-men-rtw-all",
    "di-men-tshirts-polos",
    "di-men-shirts",
    "di-men-knitwear-sweatshirts",
    "di-men-trousers-shorts",
    "di-men-denim",
    "di-men-beachwear",
    "di-men-outerwear",
    "di-men-tailored-jackets",
    "di-men-leather",
    "di-men-suits-tuxedos",
}

MADEIN_KO = {
    "IT": "이탈리아",
    "FR": "프랑스",
    "GB": "영국",
    "UK": "영국",
    "PT": "포르투갈",
    "ES": "스페인",
    "RO": "루마니아",
    "BG": "불가리아",
    "TN": "튀니지",
    "MA": "모로코",
    "JP": "일본",
    "CN": "중국",
}

_MAT_KO = {
    "cotton": "면",
    "wool": "울",
    "cashmere": "캐시미어",
    "silk": "실크",
    "leather": "가죽",
    "linen": "리넨",
    "viscose": "비스코스",
    "polyester": "폴리에스터",
    "nylon": "나일론",
    "elastane": "엘라스틴",
    "denim": "데님",
    "jersey": "저지",
    "suede": "스웨이드",
    "shearling": "시어링",
    "polyurethane": "폴리우레탄",
    "virgin wool": "버진 울",
    "silk": "실크",
    "lyocell": "리오셀",
    "hemp": "헴프",
    "elastodiene": "엘라스토디엔",
    "goose down": "구스 다운",
    "goose feathers": "구스 깃털",
    "white goose down": "화이트 구스 다운",
    "white goose feathers": "화이트 구스 깃털",
    "white duck feathers": "화이트 덕 깃털",
    "polyamide": "폴리아미드",
    "alpaca": "알파카",
    "lambskin": "램스킨",
    "calfskin": "카프스킨",
    "suede lambskin": "스웨이드 램스킨",
    "suede": "스웨이드",
    "sea island cotton": "Sea Island 면",
    "cupro": "큐프로",
    "camel wool": "카멜 울",
    "mohair": "모헤어",
    "cowhide leather": "카우하이드 가죽",
    "lambskin shearling": "램스킨 시어링",
    "metallic polyamide": "메탈릭 폴리아미드",
    "metallic polyester": "메탈릭 폴리에스터",
    "polyester fiber": "폴리에스터 파이버",
    "viscose and": "비스코스",
}

_PHRASE_KO = {
    "Made in Italy": "이탈리아 제조",
    "Made in France": "프랑스 제조",
    "Made in Portugal": "포르투갈 제조",
    "Made in Romania": "루마니아 제조",
    "100% cotton": "100% 면",
    "100% wool": "100% 울",
    "100% cashmere": "100% 캐시미어",
    "100% silk": "100% 실크",
    "Mother-of-pearl buttons": "자개 버튼",
    "Mother-of-pearl buttons with Dior signature": "디올 시그니처 자개 버튼",
    "Concealed button placket": "히든 버튼 플래킷",
    "Shirttail hem": "셔츠테일 헴",
    "Tonal allover Dior Oblique jacquard": "톤온톤 전체 Dior Oblique 자카드",
    "Tonal CD Icon embroidery on the front": "앞면 톤온톤 CD Icon 자수",
    "Ribbed collar, cuffs and hem": "리브 칼라·커프·헴",
    "Regular fit": "레귤러 핏",
    "Relaxed fit": "릴랙스드 핏",
    "Slim fit": "슬림 핏",
    "Chest patch pocket": "가슴 패치 포켓",
    "Side pockets": "사이드 포켓",
    "Back patch pocket": "백 패치 포켓",
    "Button closure": "단추 여밈",
    "Zip closure": "지퍼 여밈",
    "Elasticated waistband": "신축성 허리밴드",
    "Drawstring waistband": "드로스트링 허리밴드",
    "Cotton": "면",
    "Wool": "울",
    "Cashmere": "캐시미어",
    "Silk": "실크",
    "Leather": "가죽",
    "Denim": "데님",
    "Notch lapels": "노치 라펠",
    "Peak lapels": "피크 라펠",
    "Rear vent": "백 벤트",
    "Side vents": "사이드 벤트",
    "Welt chest pocket": "가슴 웰트 포켓",
    "Traditional interfacing": "전통 인터페이싱",
    "Front flap pockets": "앞면 플랩 포켓",
    "Rear and side flap pockets": "뒷면·사이드 플랩 포켓",
    "Chest pocket and side flap pockets": "가슴·사이드 플랩 포켓",
    "Three interior piped pockets": "내부 파이핑 포켓 3개",
    "Two interior welt pockets": "내부 웰트 포켓 2개",
    "Half lined": "하프 라이닝",
    "Full lined": "풀 라이닝",
    "Jacket:": "재킷:",
    "Pants:": "팬츠:",
    "Single-breasted with two buttons and functional buttonhole": "기능성 버튼홀의 투 버튼 싱글 브레스트",
    "Single-breasted with two buttons": "투 버튼 싱글 브레스트",
    "Single-breasted with two horn buttons": "혼 버튼 투 버튼 싱글 브레스트",
    "Single-breasted with one button": "원 버튼 싱글 브레스트",
    "Double-breasted with six horn buttons": "혼 버튼 더블 브레스트 (6버튼)",
    "Dior Médaillon buttons": "Dior Médaillon 버튼",
    "CD horn buttons": "CD 혼 버튼",
    "Dior jacquard band": "Dior 자카드 밴드",
    "Allover Dior Byzance motif": "전체 Dior Byzance 모티프",
    "Tonal allover quilted Cannage motif": "톤온톤 퀼팅 Cannage 모티프",
    "Debossed Dior signature on the front": "앞면 Dior 시그니처 디보스",
    "Debossed Dior signature on the collar": "칼라 Dior 시그니처 디보스",
    "Dior patch on the back": "뒷면 Dior 패치",
    "Dior Blason print": "Dior Blason 프린트",
    "Metal CD signature detail": "CD Icon 메탈 시그니처 디테일",
    "Dior-engraved metal button": "Dior 각인 메탈 버튼",
    "CD metal snap closure": "CD Icon 메탈 스냅 클로저",
    "Leather jacron label with debossed Dior signature": "Dior 시그니처 디보스 가죽 자크론 라벨",
    "Leather collar": "가죽 칼라",
    "Laser-faded": "레이저 페이드",
    "Vintage effect": "빈티지 이펙트",
    "Medium-weight denim – 11 oz": "미디움 웨이트 데님 (11oz)",
    "Ruffle on the front": "앞면 러플",
    "Contrasting materials": "콘트라스트 소재",
    "Elastic hem and cuffs": "신축성 헴·커프",
    "Elastic cuffs": "신축성 커프",
    "Button tabs on the cuffs": "커프 버튼 탭",
    "Buttoned flap pockets": "버튼 플랩 포켓",
    "Zip pockets": "지퍼 포켓",
    "Hem with elastic in the back": "백 헴 신축 디테일",
    "Adjustable side tabs with buttons": "버튼 사이드 탭 (조절 가능)",
    "Interior chest pocket with snap": "스냅 내부 가슴 포켓",
    "Cape fastened with passementerie toggles": "패스먼트리 토글 여밈 케이프",
    "100% Sea Island cotton": "100% Sea Island 면",
    "100% cotton 120/2": "100% 면 120/2",
    "Allover Dior Oblique motif on the reverse side": "리버서블 톤온톤 Dior Oblique 모티프",
    "52% viscose and 48% cotton": "52% 비스코스, 48% 면",
}


def _load_merge():
    spec = importlib.util.spec_from_file_location(
        "merge_di_catalog_ko",
        ROOT / "scripts/merge-di-catalog-ko.py",
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


_merge = _load_merge()
list_price_from_variants = _merge.list_price_from_variants
translate = _merge.translate


def is_rtw(product: dict) -> bool:
    cols = set(product.get("diCollections") or [])
    leaf = product.get("subcategory") or ""
    return bool(cols.intersection(RTW_LEAVES) or leaf in RTW_LEAVES)


def load_translate_cache() -> dict[str, str]:
    if TRANSLATE_CACHE.is_file():
        return json.loads(TRANSLATE_CACHE.read_text())
    return {}


def save_translate_cache(cache: dict[str, str]) -> None:
    TRANSLATE_CACHE.write_text(
        json.dumps(cache, indent=2, ensure_ascii=False) + "\n"
    )


def _is_internal_code(text: str) -> bool:
    s = text.strip()
    if not s:
        return True
    if s in _PHRASE_KO or s in _MAT_KO.values():
        return False
    # Dior ERP style refs (POLO CL MC BtN B DIOR, CHEMISE CO ML …)
    if re.search(r"\b(BtN|CtR|BtP|BtDWN|COLH|MAILLE)\b", s):
        return True
    if re.fullmatch(r"[A-Z0-9][A-Z0-9\s\-\./,]+", s) and not re.search(r"[a-z]", s):
        return True
    words = s.split()
    if len(words) >= 3 and all(re.match(r"^[A-Z0-9][A-Za-z0-9/-]*$", w) for w in words):
        if any(w in {"DIOR", "POLO", "CHEMISE", "BLOUSON", "VESTE", "PANTALON"} for w in words):
            return True
    return False


def _translate_blend(line: str) -> str | None:
    s = line.strip()
    if re.search(r"\d+%[^,]+ and \d+%", s) and " and lining:" not in s.lower():
        parts = re.split(r"\s+and\s+", s)
        if len(parts) >= 2 and all(re.search(r"\d+%", p) for p in parts):
            out = []
            for part in parts:
                b = _translate_blend(part.strip()) or tr(part.strip(), {}, live=False)
                out.append(b)
            if all(out):
                return ", ".join(out)
    if " and lining:" in s.lower() or " and lining :" in s.lower():
        main, lining = re.split(r"\s+and lining:\s*", s, maxsplit=1, flags=re.I)
        main_ko = _translate_blend(main) or tr(main, {}, live=False)
        lining_ko = _translate_blend(lining) or tr(lining, {}, live=False)
        if main_ko and lining_ko:
            return f"{main_ko}, 안감: {lining_ko}"
    if " and back:" in s.lower():
        main, back = re.split(r"\s+and back:\s*", s, maxsplit=1, flags=re.I)
        main_ko = _translate_blend(main) or tr(main, {}, live=False)
        back_ko = _translate_blend(back) or tr(back, {}, live=False)
        if main_ko and back_ko:
            return f"{main_ko}, 백: {back_ko}"

    gauge = None
    gm = re.search(r"\((\d+)\s*-?\s*gauge\)\s*\*?\s*$", s, re.I)
    if gm:
        gauge = gm.group(1)
        s = s[: gm.start()].strip()

    super_m = re.match(
        r"^(\d+)%\s+virgin wool\s*\(Super\s+(\d+s)\)$", s, re.I
    )
    if super_m:
        base = f"{super_m.group(1)}% 버진 울 (Super {super_m.group(2)})"
        return f"{base} ({gauge}게이지)" if gauge else base

    parts = re.findall(r"(\d+)%\s*([^,]+)", s)
    if len(parts) >= 2:
        out = []
        for pct, mat in parts:
            mk = _MAT_KO.get(mat.strip().lower(), mat.strip())
            out.append(f"{pct}% {mk}")
        body = ", ".join(out)
        return f"{body} ({gauge}게이지)" if gauge else body

    m = re.match(r"^(\d+)%\s+(.+?)(?:\s*\((\d+)\s*gauge\)\s*\*)?$", s, re.I)
    if m:
        mat = _MAT_KO.get(m.group(2).strip().lower(), m.group(2).strip())
        base = f"{m.group(1)}% {mat}"
        g = m.group(3) or gauge
        if g:
            return f"{base} ({g}게이지)"
        return base
    if gauge:
        inner = _translate_blend(s)
        if inner:
            return f"{inner} ({gauge}게이지)"
    if s.lower().startswith("filling:"):
        body = s.split(":", 1)[1].strip()
        parts = re.findall(r"(\d+)%\s*([^,]+)", body)
        if parts:
            out = []
            for p, m in parts:
                mk = _MAT_KO.get(m.strip().lower(), m.strip())
                out.append(f"{p}% {mk}")
            return "충전재: " + ", ".join(out)
    return None


def _heuristic_ko(line: str) -> str | None:
    s = line.strip()
    if not s or _is_internal_code(s):
        return None
    if s in _PHRASE_KO:
        return _PHRASE_KO[s]

    blend = _translate_blend(s)
    if blend:
        return blend

    low = s.lower()
    if "made in italy" in low:
        return "이탈리아 제조"
    if "made in france" in low:
        return "프랑스 제조"
    if "made in portugal" in low:
        return "포르투갈 제조"
    if "made in romania" in low:
        return "루마니아 제조"

    m = re.match(r"^(\d+)%\s+(\w+)$", s, re.I)
    if m:
        mat = _MAT_KO.get(m.group(2).lower(), m.group(2))
        return f"{m.group(1)}% {mat}"

    if "dior oblique" in low and "jacquard" in low:
        return "톤온톤 전체 Dior Oblique 자카드"
    if "mother-of-pearl" in low:
        return "디올 시그니처 자개 버튼" if "dior" in low else "자개 버튼"
    if "concealed button" in low:
        return "히든 버튼 플래킷"
    if "shirttail hem" in low:
        return "셔츠테일 헴"
    if "regular fit" in low:
        return "레귤러 핏"
    if "slim fit" in low:
        return "슬림 핏"
    if "relaxed fit" in low:
        return "릴랙스드 핏"
    if "patch pocket" in low:
        where = "가슴" if "chest" in low else ("백" if "back" in low else "")
        return f"{where} 패치 포켓".strip()
    if "embroidery" in low or "embroidered" in low:
        where = "앞면" if "front" in low else ("가슴" if "chest" in low else "디올")
        if "médaillon" in low or "medaillon" in low:
            return f"{where} Dior Médaillon 자수"
        if "cd icon" in low:
            return f"{where} CD Icon 자수"
        if "tonal dior" in low:
            return f"{where} 톤온톤 Dior 자수"
        return f"{where} 자수".strip()
    if "ribbed" in low and "collar" in low:
        return "리브 칼라·커프·헴" if "hem" in low else "리브 칼라"
    if "drawstring" in low:
        return "드로스트링 디테일"
    if "elastic" in low and "waist" in low:
        return "신축성 허리밴드"
    if "button" in low and "closure" in low:
        return "단추 여밈"
    if "zip" in low and "closure" in low:
        return "지퍼 여밈"
    if "notch lapel" in low:
        return "노치 라펠"
    if "peak lapel" in low:
        return "피크 라펠"
    if "rear vent" in low or "side vent" in low:
        return "백 벤트" if "rear" in low else "사이드 벤트"
    if "welt" in low and "pocket" in low:
        return "웰트 포켓" if "chest" not in low else "가슴 웰트 포켓"
    if "single-breasted" in low:
        return "싱글 브레스트"
    if "double-breasted" in low:
        return "더블 브레스트"
    if "half lined" in low:
        return "하프 라이닝"
    if "virgin wool" in low:
        return "100% 버진 울" if s.startswith("100%") else "버진 울"
    if "goose down" in low or "goose feathers" in low:
        return "구스 다운 충전재"
    if "lambskin" in low:
        return "램스킨"
    if "hemp" in low:
        return "100% 헴프" if s.startswith("100%") else "헴프"
    if "cupro" in low:
        return "큐프로"
    if "elastane" in low or "elastodiene" in low:
        return s  # handled by blend parser mostly
    if s.endswith(":") and s[:-1] in ("Jacket", "Pants", "Vest", "Coat"):
        return {"Jacket": "재킷", "Pants": "팬츠", "Vest": "베스트", "Coat": "코트"}[s[:-1]] + ":"
    if s in _MAT_KO or low in _MAT_KO:
        return _MAT_KO.get(low, _MAT_KO.get(s, s))
    return None


def _polish_ko(s: str) -> str:
    out = s
    for en, ko in (
        (r"virgin wool", "버진 울"),
        (r"\bwool\b", "울"),
        (r"\bsilk\b", "실크"),
        (r"\bviscose\b", "비스코스"),
        (r"\bcupro\b", "큐프로"),
        (r"\bcotton\b", "면"),
    ):
        out = re.sub(en, ko, out, flags=re.I)
    return out


def tr(
    text: str,
    cache: dict[str, str],
    *,
    live: bool = False,
) -> str:
    s = re.sub(r"\s+", " ", (text or "").strip())
    if not s:
        return ""
    if _is_internal_code(s):
        return ""
    gloss = _heuristic_ko(s)
    if gloss:
        return _polish_ko(gloss)
    if s in cache and is_good_korean(cache[s]):
        return _polish_ko(cache[s])
    if is_good_korean(s):
        return s
    if not live:
        return s
    out = translate(s) or ""
    if not out or not is_good_korean(out):
        try:
            out = gtx_translate(s) or out
        except Exception:
            pass
    out = out or s
    if out != s and is_good_korean(out):
        cache[s] = out
    return _polish_ko(out)


def parse_characteristics(raw: str) -> list[str]:
    if not raw or not isinstance(raw, str):
        return []
    return [ln.strip() for ln in raw.replace("\r", "").split("\n") if ln.strip()]


def material_label(material: dict | None) -> str:
    if not isinstance(material, dict):
        return ""
    for key in ("label_int", "label", "group"):
        val = material.get(key)
        if isinstance(val, str) and val.strip() and not _is_internal_code(val):
            return val.strip()
    main = material.get("main")
    if isinstance(main, str) and main.strip() and not _is_internal_code(main):
        return main.strip()
    return ""


def madein_ko(code: str | None) -> str:
    c = (code or "").strip().upper()
    if not c:
        return ""
    return MADEIN_KO.get(c, c)


def _size_sort_key(size: str) -> tuple:
    s = str(size or "").strip()
    m = re.search(r"(\d+(?:\.\d+)?)", s)
    if m:
        return (0, float(m.group(1)), s)
    order = [
        "XXXS", "XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL", "4XL",
    ]
    su = s.upper()
    if su in order:
        return (1, order.index(su), s)
    return (2, s)


def rebuild_variants(
    product: dict,
    hit: dict | None,
    *,
    collections: list[str],
) -> list[dict]:
    hit = hit or {}
    pid = product["id"]
    images = product.get("images") or []
    image = images[0] if images else product.get("image") or ""
    gbp_f = float(product.get("gbpPrice") or 0)
    price = int(product.get("price") or 0)
    source_url = product.get("sourceUrl") or ""
    prev_vars = product.get("variants") or []
    color_key = prev_vars[0].get("colorKey") if prev_vars else "default"
    color_ko = prev_vars[0].get("colorNameKo") if prev_vars else "기본"

    raw_vars = hit.get("variants") if isinstance(hit.get("variants"), list) else []
    variants: list[dict] = []
    for vv in raw_vars:
        if not isinstance(vv, dict):
            continue
        sz = str(vv.get("sizeFormatted") or vv.get("size") or "").strip()
        if not sz or sz.upper() in ("OS", "ONE SIZE", "TU", "U", "ONESIZE"):
            continue
        v_gbp = algolia_variant_gbp(vv.get("price") if isinstance(vv.get("price"), dict) else None, gbp_f)
        in_stock = True
        status = str(vv.get("status") or vv.get("stockLevel") or "").lower()
        if status in ("outofstock", "out_of_stock", "unavailable"):
            in_stock = False
        variants.append(
            {
                "id": f"{pid}-sz-{slugify(sz, max_len=24)}",
                "name": sz,
                "nameKo": sz,
                "sku": str(vv.get("sku") or product.get("sku") or pid),
                "gbpPrice": v_gbp,
                "price": gbp_to_krw(v_gbp) if v_gbp else price,
                "image": image,
                "images": images,
                "sourceUrl": source_url,
                "inStock": in_stock,
                "colorKey": color_key,
                "colorNameKo": color_ko,
                "size": sz,
                "diCollections": collections,
            }
        )

    if variants:
        return sorted(variants, key=lambda v: _size_sort_key(v.get("size") or ""))
    if prev_vars:
        return prev_vars
    return [
        {
            "id": f"{pid}-os",
            "name": "One Size",
            "nameKo": "원 사이즈",
            "sku": str(product.get("sku") or pid),
            "gbpPrice": gbp_f,
            "price": price,
            "image": image,
            "images": images,
            "sourceUrl": source_url,
            "inStock": True,
            "colorKey": color_key,
            "colorNameKo": color_ko,
            "size": "OS",
            "diCollections": collections,
        }
    ]


def pick_leaf(product: dict, raw_row: dict | None) -> str:
    cols = product.get("diCollections") or []
    for leaf in (
        "di-men-shirts",
        "di-men-knitwear-sweatshirts",
        "di-men-tshirts-polos",
        "di-men-trousers-shorts",
        "di-men-denim",
        "di-men-outerwear",
        "di-men-tailored-jackets",
        "di-men-suits-tuxedos",
        "di-men-beachwear",
        "di-men-leather",
        "di-men-rtw-all",
    ):
        if leaf in cols:
            return leaf
    if raw_row:
        return raw_row.get("leafId") or "di-men-rtw-all"
    return product.get("subcategory") or "di-men-rtw-all"


def story_sections_for_rtw(
    description_ko: str,
    images: list[str],
    *,
    features_ko: list[str],
    material_ko: str,
    madein: str,
) -> list[dict]:
    if not images:
        return [{"titleKo": "제품 소개", "bodyKo": description_ko, "image": ""}]

    detail_body = (
        " · ".join(features_ko[:8])
        if features_ko
        else (
            "Dior 공식 제품 컷으로 확인하는 실루엣·소재·"
            "테일러링 디테일입니다."
        )
    )
    material_body = (
        f"주요 소재: {material_ko}. {madein}."
        if material_ko and madein
        else (f"주요 소재: {material_ko}." if material_ko else madein)
    )
    if material_ko and _is_internal_code(material_ko):
        material_body = madein or detail_body
    look_idx = next(
        (i for i, img in enumerate(images) if "look_" in img.lower()),
        None,
    )

    sections: list[dict] = [
        {"titleKo": "제품 소개", "bodyKo": description_ko, "image": images[0]},
    ]
    if len(images) > 3:
        sections.append(
            {
                "titleKo": "디테일 & 특징",
                "bodyKo": detail_body,
                "image": images[min(3, len(images) - 1)],
            }
        )
    if len(images) > 5:
        sections.append(
            {
                "titleKo": "소재 & 제작",
                "bodyKo": material_body or detail_body,
                "image": images[min(5, len(images) - 1)],
            }
        )
    if look_idx is not None:
        sections.append(
            {
                "titleKo": "디올 룩",
                "bodyKo": (
                    "Dior 남성 컬렉션 룩과 함께 제안되는 "
                    "스타일링 레퍼런스입니다. 공식 룩북 컷으로 "
                    "핏과 코디를 확인해 보세요."
                ),
                "image": images[look_idx],
            }
        )
    elif len(images) > 7:
        sections.append(
            {
                "titleKo": "착용 & 스타일",
                "bodyKo": (
                    "포멀부터 데일리까지 다양한 룩에 어울리는 "
                    "디올 남성 레디투웨어 실루엣입니다."
                ),
                "image": images[min(7, len(images) - 1)],
            }
        )
    return sections


def enrich_product(
    product: dict,
    *,
    pdp: dict | None,
    hit: dict | None,
    raw_row: dict | None,
    cache: dict[str, str],
    live_translate: bool,
) -> dict:
    pdp = pdp or {}
    hit = hit or {}
    raw_row = raw_row or {}
    collections = list(dict.fromkeys(product.get("diCollections") or []))
    leaf = pick_leaf(product, raw_row)
    images = product.get("images") or []
    title_en = product.get("name") or pdp.get("title") or ""

    variants = rebuild_variants(product, hit, collections=collections)
    product["variants"] = variants
    product["price"] = list_price_from_variants(
        variants, int(product.get("price") or 0)
    )

    subtitle_en = (raw_row.get("subtitle") or "").strip()
    desc_en = (pdp.get("description") or "").strip()
    if not desc_en:
        desc_en = re.sub(
            r"\s+",
            " ",
            ((raw_row.get("details") or {}).get("paragraphs") or [""])[0],
        ).strip()

    existing_desc = (product.get("descriptionKo") or "").strip()
    if is_good_korean(existing_desc):
        description_ko = existing_desc
    else:
        parts: list[str] = []
        if subtitle_en:
            sk = tr(subtitle_en, cache, live=live_translate)
            if sk:
                parts.append(sk)
        if desc_en:
            dk = tr(desc_en, cache, live=live_translate)
            if dk:
                parts.append(dk)
        description_ko = "\n\n".join(parts) or existing_desc or title_en
        product["descriptionKo"] = description_ko

    chars = parse_characteristics(
        pdp.get("characteristics") or hit.get("characteristics") or ""
    )
    features_ko: list[str] = []
    for line in chars:
        ko = tr(line, cache, live=live_translate)
        if ko:
            features_ko.append(ko)
    if features_ko:
        product["featuresKo"] = features_ko

    mat_en = material_label(pdp.get("material") or hit.get("material"))
    if _is_internal_code(mat_en):
        mat_en = ""
    mat_ko = tr(mat_en, cache, live=False) if mat_en else ""
    origin = madein_ko(pdp.get("madein") or hit.get("madein"))
    tech: list[dict] = []
    if mat_ko or mat_en:
        tech.append({"labelKo": "소재", "valueKo": mat_ko or mat_en})
    if origin:
        tech.append({"labelKo": "제조국", "valueKo": origin})
    if tech:
        product["techSpecs"] = tech

    product["storySections"] = story_sections_for_rtw(
        description_ko,
        images,
        features_ko=features_ko,
        material_ko=mat_ko or mat_en,
        madein=f"제조국: {origin}" if origin else "",
    )

    chart = size_chart_for_di_mens_rtw(
        variants, leaf_id=leaf, title_en=title_en,
    )
    if chart:
        product["sizeChart"] = chart

    product["subcategory"] = leaf
    return product


def warm_feature_cache(
    pdp_cache: dict,
    hits: dict[str, dict],
    skus: list[str],
    cache: dict[str, str],
) -> int:
    """GTX-translate unique EN characteristic lines into cache."""
    from ko_qa import en_ratio

    missing: set[str] = set()
    for sku in skus:
        pdp = pdp_cache.get(sku) or {}
        hit = hits.get(sku) or {}
        raw = pdp.get("characteristics") or hit.get("characteristics") or ""
        for line in parse_characteristics(raw):
            ko = tr(line, cache, live=False)
            if ko and (not is_good_korean(ko) or en_ratio(ko) > 0.3):
                missing.add(line)
    warmed = 0
    for i, line in enumerate(sorted(missing), 1):
        if line in cache and is_good_korean(cache[line]):
            continue
        try:
            ko = gtx_translate(line)
            if ko and is_good_korean(ko):
                cache[line] = ko
                warmed += 1
        except Exception:
            pass
        if i % 25 == 0:
            save_translate_cache(cache)
            print(f"  warm {i}/{len(missing)}", flush=True)
    save_translate_cache(cache)
    return warmed


def write_catalog(products: list[dict]) -> None:
    CAT.write_text(json.dumps(products, indent=2, ensure_ascii=False) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="Comma-separated SKUs")
    ap.add_argument(
        "--translate",
        action="store_true",
        help="Live-translate missing strings (slow)",
    )
    ap.add_argument(
        "--skip-warm",
        action="store_true",
        help="Skip GTX warm pass for EN characteristics",
    )
    args = ap.parse_args()

    products = json.loads(CAT.read_text())
    pdp_cache = json.loads(PDP_CACHE.read_text()) if PDP_CACHE.is_file() else {}
    raw_by = {}
    if RAW.is_file():
        raw_by = {
            p["id"]: p for p in json.loads(RAW.read_text()).get("products") or []
        }

    rtw = [p for p in products if is_rtw(p)]
    if args.only:
        want = {x.strip() for x in args.only.split(",") if x.strip()}
        rtw = [p for p in rtw if p.get("sku") in want]

    codes = [p["sku"] for p in rtw if p.get("sku")]
    hits: dict[str, dict] = {}
    for i in range(0, len(codes), 15):
        hits.update(algolia_merch_hits_by_codes(codes[i : i + 15]))
        if i and i % 120 == 0:
            print(f"  algolia {i}/{len(codes)}", flush=True)

    cache = load_translate_cache()
    live = bool(args.translate)
    if not args.skip_warm:
        n = warm_feature_cache(pdp_cache, hits, codes, cache)
        print(f"  warmed {n} characteristic lines", flush=True)

    stats = {"variants_rebuilt": 0, "with_features": 0, "with_chart": 0, "multi_size": 0}

    for i, p in enumerate(rtw, 1):
        before_os = len(p.get("variants") or []) == 1 and (
            p.get("variants") or [{}]
        )[0].get("size") in ("OS", "One Size")
        enrich_product(
            p,
            pdp=pdp_cache.get(p.get("sku") or ""),
            hit=hits.get(p.get("sku") or ""),
            raw_row=raw_by.get(p.get("sku") or ""),
            cache=cache,
            live_translate=live,
        )
        after = len(p.get("variants") or [])
        if before_os and after > 1:
            stats["variants_rebuilt"] += 1
        if p.get("featuresKo"):
            stats["with_features"] += 1
        if p.get("sizeChart"):
            stats["with_chart"] += 1
        if after > 1:
            stats["multi_size"] += 1
        if i % CHECKPOINT_EVERY == 0:
            print(f"  checkpoint {i}/{len(rtw)}", flush=True)
            write_catalog(products)
            save_translate_cache(cache)

    write_catalog(products)
    save_translate_cache(cache)

    shirt = next((p for p in rtw if p.get("sku") == "013C501A4743_C080"), {})
    print(
        f"DONE rtw={len(rtw)} rebuilt={stats['variants_rebuilt']} "
        f"multi={stats['multi_size']} features={stats['with_features']} "
        f"charts={stats['with_chart']}",
        flush=True,
    )
    if shirt:
        print(
            "sample shirt sizes:",
            [v.get("size") for v in shirt.get("variants") or []][:6],
            "chart:",
            (shirt.get("sizeChart") or {}).get("id"),
            "sections:",
            len(shirt.get("storySections") or []),
            "features:",
            len(shirt.get("featuresKo") or []),
            flush=True,
        )


if __name__ == "__main__":
    main()
