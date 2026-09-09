#!/usr/bin/env python3
"""Fix hybrid EN/KO in Dior catalog — translate failing featuresKo & rebuild story sections.

  python3 scripts/fix-di-ko-hybrid.py
  python3 scripts/fix-di-ko-hybrid.py --scope acc-shoes
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

from di_slg_ko import FEATURE_KO, MATERIAL_KO, MADEIN_KO  # noqa: E402
from ko_qa import (  # noqa: E402
    check_brand,
    find_hybrid_fields,
    has_hangul,
    is_good_korean,
    load_products,
    translate_en_to_ko,
)

CAT = ROOT / "src/data/di/di-catalog.json"
CACHE_PATH = ROOT / "src/data/di/di-translate-cache.json"
CHECKPOINT = 40

ACC_COLS = {
    "di-men-accessories", "di-men-acc-all", "di-men-sunglasses", "di-men-belts",
    "di-men-ties-pocket-squares", "di-men-scarves", "di-men-hats-gloves", "di-men-socks",
    "di-men-fashion-jewelry", "di-men-silver-jewelry", "di-men-key-rings",
    "di-men-charm-jewelry", "di-men-lifestyle", "di-men-acc-tech", "di-men-pet-accessories",
    "di-men-slg", "di-men-slg-all", "di-men-card-holders", "di-men-compact-wallets",
    "di-men-long-wallets", "di-men-pouches", "di-men-tech-accessories",
}
SHOE_COLS = {
    "dior-shoes", "di-men-shoes", "di-men-shoes-all", "di-men-sneakers",
    "di-men-sandals-mules", "di-men-loafers", "di-men-lace-ups", "di-men-boots",
}
MEN_RTW_COLS = {
    "di-men-shirts", "di-men-knitwear-sweatshirts", "di-men-tshirts-polos",
    "di-men-trousers-shorts", "di-men-denim", "di-men-outerwear",
    "di-men-tailored-jackets", "di-men-suits-tuxedos", "di-men-beachwear",
    "di-men-leather", "di-men-rtw-all",
}
WOMEN_RTW_COLS = {
    "di-women-shirts", "di-women-sweaters-cardigans", "di-women-tshirts",
    "di-women-dresses", "di-women-skirts", "di-women-trousers-shorts",
    "di-women-denim", "di-women-coats", "di-women-jackets",
    "di-women-swimsuits", "di-women-homewear-lingerie", "di-women-rtw-all",
}
COLOR_KO = {
    "beige": "베이지",
    "black": "블랙",
    "blue": "블루",
    "brown": "브라운",
    "gold": "골드",
    "gray": "그레이",
    "grey": "그레이",
    "green": "그린",
    "ivory": "아이보리",
    "khaki": "카키",
    "navy": "네이비",
    "pink": "핑크",
    "red": "레드",
    "silver": "실버",
    "white": "화이트",
    "yellow": "옐로",
}
TITLE_PHRASE_KO = {
    "Book:": "도서:",
    "Set of Three Scented Mini Candles": "센티드 미니 캔들 3개 세트",
    "Dioriviera": "디올리비에라",
    "Lady Dior": "레이디 디올",
    "DiorTravel": "디올트래블",
    "Walk'n'Dior": "워크앤디올",
    "J'Adior": "J'Adior",
    "Dior Cœur": "디올 쿠르",
    "Dior Chrono": "디올 크로노",
    "Diorly": "디올리",
    "D-Quest": "D-Quest",
    "D-Town": "D-Town",
    "Belle Dior": "벨 디올",
    "Dior Flora": "디올 플로라",
    "Dior Nymphéas": "디올 님페아",
    "Dior Bloom": "디올 블룸",
    "Dior Qixi": "디올 칠석",
    "Dior Dentelle": "디올 당텔",
    "Dior Aurore": "디올 오로르",
    "Dior Palais": "디올 팔레",
    "Dior Ride": "디올 라이드",
    "Dior Black Suit": "디올 블랙수트",
    "DiorBlackSuit": "디올 블랙수트",
    "DiorTag": "디올태그",
    "Dior Timeless": "디올 타임리스",
    "Dior Or": "디올 오르",
    "Dio(r)evolution": "디오(레볼루션)",
    "Dior Infini": "디올 인피니",
    "Dior Avenue": "디올 애비뉴",
    "Inside Dior Avenue": "인사이드 디올 애비뉴",
    "Dior Treasures": "디올 트레저",
    "Dior Infini Tartan": "디올 인피니 타탄",
    "Diortwin": "디올트윈",
    "Dior Jardin": "디올 자르댕",
    "Voyageur": "보야주르",
    "Sun Stripes": "선 스트라이프",
    "Heeled Thong Sandal": "힐드 통 샌들",
    "Heeled Slingback Sandal": "힐드 슬링백 샌들",
    "Heeled Sandal": "힐드 샌들",
    "Heeled Slide": "힐드 슬라이드",
    "Wedge Sandal": "웨지 샌들",
    "Slingback Sandal": "슬링백 샌들",
    "Slingback Pump": "슬링백 펌프스",
    "Pump": "펌프스",
    "Ballet Flat": "발레 플랫",
    "Triangle Scarf": "트라이앵글 스카프",
    "Denim Shawl": "데님 숄",
    "Reversible Scarf": "리버서블 스카프",
    "Platform Sneaker": "플랫폼 스니커즈",
    "Platform Sandal": "플랫폼 샌들",
    "Sneaker": "스니커즈",
    "Swim Shorts": "스윔 쇼츠",
    "T-Shirt": "티셔츠",
    "Windbreaker": "윈드브레이커",
    "Jacket": "재킷",
    "Shirt": "셔츠",
    "Pants": "팬츠",
    "Shorts": "쇼츠",
    "Sarong": "사롱",
    "Passport Cover": "패스포트 커버",
    "Coin Purse": "코인 퍼스",
    "Slim Wallet": "슬림 월렛",
    "Long Wallet": "롱 월렛",
    "Wallet": "월렛",
    "Zipped Pouch": "지퍼 파우치",
    "Pouch": "파우치",
    "Travel Kit": "트래블 키트",
    "Zipped Key Case": "지퍼 키 케이스",
    "Belt": "벨트",
    "Bucket Hat": "버킷 햇",
    "Large Brim Hat": "라지 브림 햇",
    "Small Brim Hat": "스몰 브림 햇",
    "Slide": "슬라이드",
    "Square Scarf": "스퀘어 스카프",
    "Chelsea Boot": "첼시 부츠",
    "Heeled Boot": "힐드 부츠",
    "Ankle Boot": "앵클 부츠",
    "Mule": "뮬",
    "Loafer": "로퍼",
    "Derby shoe": "더비 슈즈",
    "Oxford Shoe": "옥스퍼드 슈즈",
    "Cloche": "클로슈",
    "Visor": "바이저",
    "Mitzah": "미차",
    "Pumps": "펌프스",
    "Sandals": "샌들",
    "Sneakers": "스니커즈",
    "Bio-Acetate": "바이오 아세테이트",
    "BioAcetate": "바이오 아세테이트",
    "Bag Charm": "백 참",
    "Earrings": "이어링",
    "Bangle": "뱅글",
    "Bracelet": "브레이슬릿",
    "Scented Candle": "센티드 캔들",
    "Portable Lantern": "포터블 랜턴",
}


def load_cache() -> dict[str, str]:
    if CACHE_PATH.is_file():
        return json.loads(CACHE_PATH.read_text())
    return {}


def save_cache(cache: dict[str, str]) -> None:
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n")


def in_scope(p: dict, scope: str) -> bool:
    cols = set(p.get("diCollections") or [])
    sub = str(p.get("subcategory") or "")
    if scope == "all":
        return True
    sc = ACC_COLS | SHOE_COLS
    return bool(cols.intersection(sc) or sub in sc)


def tr_line(line: str, cache: dict[str, str]) -> str:
    s = re.sub(r"\s+", " ", (line or "").strip())
    if not s or is_good_korean(s):
        return s
    if s in FEATURE_KO:
        return FEATURE_KO[s]
    direct = {
        "Made in Portugal": "포르투갈 제조",
        "Lambskin and technical fabric lining": "램스킨 및 테크니컬 패브릭 안감",
        "Dior Médaillon embroidery on the front": "앞면 Dior Médaillon 자수",
        "Dior Médaillon lambskin patch on the front": "앞면 Dior Médaillon 램스킨 패치",
        "Details: 100% lambskin": "디테일: 램스킨 100%",
        "Calfskin strap": "카프스킨 스트랩",
        "LED lamp": "엘이디 램프",
        "Touch-sensitive on/off dimmer button": "터치식 온/오프 디머 버튼",
        "Five different light settings": "5가지 조명 설정",
        "Cordless rechargeable lamp": "무선 충전식 램프",
        "Battery life of up to five hours on high intensity and 46 hours on low intensity": "고조도에서 최대 5시간, 저조도에서 최대 46시간 사용 가능",
        "Comes with a USB-C charging cable": "USB-C 충전 케이블 포함",
        "The device is charged using a 5V/2A maximum charger": "최대 5V/2A 충전기로 충전",
        "Does not include a power adapter": "전원 어댑터는 포함되지 않음",
        "Pink lambskin and thread": "핑크 램스킨 및 실",
        "Ice Blue lambskin bow": "아이스 블루 램스킨 보우",
        "100% cotton": "면 100%",
        "100% cashmere": "캐시미어 100%",
        "100% wool": "울 100%",
        "100% viscose": "비스코스 100%",
        "Rose des Vents and white embroidered band with Christian Dior Paris signature": "로즈 데 방 및 화이트 자수 밴드, 크리스챤 디올 파리 시그니처",
        "Rose des Vents & 그레이 양면 Dior Oblique Diortwin 모티브": "로즈 데 방 & 그레이 양면 디올 오블리크 디올트윈 모티프",
        "Dior Hortensia Garden 모티브와 Dior Médaillon 시그니처 디테일의 안창": "디올 오르텐시아 가든 모티프와 디올 메다이옹 시그니처 디테일이 돋보이는 안창",
        "Cassi Edition 출판": "카시 에디션 출판",
        "Musée des Arts Décoratifs 출판": "뮈제 데 자르 데코라티프 출판",
        "La Martinière 출판": "라 마르티니에르 출판",
        "Delpire & Co 출판": "델피르 앤드 코 출판",
        "Dior Secret Garden 모티브와 Dior Médaillon 시그니처가 돋보이는 가죽 안창": "디올 시크릿 가든 모티프와 디올 메다이옹 시그니처가 돋보이는 가죽 안창",
        "Dior Arabesque 모티브와 Dior Médaillon 시그니처 디테일의 깔창": "디올 아라베스크 모티프와 디올 메다이옹 시그니처 디테일의 깔창",
        "Dioresque 나비 모티프 가죽 안창": "디오레스크 나비 모티프 가죽 안창",
        "그레이 양면 Dior Oblique 모티브 Diortwin": "그레이 양면 디올 오블리크 모티프 디올트윈",
    }
    if s in direct:
        return direct[s]
    if s == "French version":
        return "프랑스어판"
    if s == "English version":
        return "영어판"
    if s.endswith(" Publishing"):
        return f"{s[:-11]} 출판"
    if s == "100% paper":
        return "종이 100%"
    if s == "Soft cover":
        return "소프트 커버"
    if s == "Shipped in a hard case":
        return "하드 케이스에 담아 제공"
    if s == "Japanese version with booklet in English":
        return "영문 소책자가 포함된 일본어판"
    if s == "Hard cover: bound in a Christian Dior limited edition case":
        return "하드 커버: Christian Dior 리미티드 에디션 케이스에 수납"
    if s == "Set of three volumes, each 84 pages":
        return "각 84페이지 구성의 3권 세트"
    m_pages = re.fullmatch(r"(\d+)\s+pages", s)
    if m_pages:
        return f"{m_pages.group(1)}페이지"
    m_pages_photos = re.fullmatch(r"(\d+)\s+pages,\s+(\d+)\s+photographs", s)
    if m_pages_photos:
        return f"{m_pages_photos.group(1)}페이지, 사진 {m_pages_photos.group(2)}장"
    if s.startswith("68% hand-blown Murano glass"):
        return (
            "68% 수공예 무라노 글라스, 18% 알루미늄, 7% 리튬, "
            "2% 스테인리스 스틸, 2% 흑연, 2% PC-ABS, 1% 폴리아미드"
        )
    if s == "주요 소재: Satin. 제조국: 이탈리아.":
        return "주요 소재: 새틴. 제조국: 이탈리아."
    material_words = {
        "cotton": "면",
        "silk": "실크",
        "viscose": "비스코스",
        "wool": "울",
        "cashmere": "캐시미어",
        "virgin wool": "버진 울",
        "metallic polyester": "메탈릭 폴리에스터",
        "polyester": "폴리에스터",
        "technical fabric": "테크니컬 패브릭",
        "lambskin": "램스킨",
        "calfskin": "카프스킨",
        "linen": "리넨",
        "thread": "실",
    }
    if re.search(r"\d+%", s):
        out = s
        for en, ko_word in sorted(material_words.items(), key=lambda x: len(x[0]), reverse=True):
            out = re.sub(rf"\b{re.escape(en)}\b", ko_word, out, flags=re.I)
        out = out.replace(" and lining:", " / 안감:").replace(" and ", ", ")
        if has_hangul(out):
            return out
    ko = translate_en_to_ko(s, cache)
    if ko and is_good_korean(ko):
        return ko
    return s


def load_acc_enrich():
    spec = importlib.util.spec_from_file_location(
        "enrich_di_men_accessories_pdp",
        ROOT / "scripts/enrich-di-men-accessories-pdp.py",
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


_acc = load_acc_enrich()


def load_men_rtw_enrich():
    spec = importlib.util.spec_from_file_location(
        "enrich_di_men_rtw_pdp",
        ROOT / "scripts/enrich-di-men-rtw-pdp.py",
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def load_women_rtw_enrich():
    spec = importlib.util.spec_from_file_location(
        "enrich_di_women_rtw_pdp",
        ROOT / "scripts/enrich-di-women-rtw-pdp.py",
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


_men_rtw = load_men_rtw_enrich()
_women_rtw = load_women_rtw_enrich()


def needs_korean_title(text: str | None) -> bool:
    s = (text or "").strip()
    if not s:
        return True
    return not has_hangul(s)


def size_sort_key(size: str | None) -> tuple:
    s = str(size or "").strip()
    m = re.search(r"(\d+(?:\.\d+)?)", s)
    if m:
        return (0, float(m.group(1)), s)
    order = ["XXXS", "XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL", "4XL"]
    su = s.upper()
    if su in order:
        return (1, order.index(su), s)
    return (2, s)


def translate_color(label: str | None, cache: dict[str, str]) -> str:
    s = re.sub(r"\s+", " ", (label or "").strip())
    if not s:
        return "기본"
    if has_hangul(s):
        return s
    mapped = COLOR_KO.get(s.lower())
    if mapped:
        return mapped
    ko = translate_en_to_ko(s, cache)
    return ko if ko and is_good_korean(ko) else s


def translate_title_text(text: str | None, cache: dict[str, str]) -> str:
    s = re.sub(r"\s+", " ", (text or "").strip())
    if not s or has_hangul(s):
        return s
    out = s
    for en in sorted(TITLE_PHRASE_KO, key=len, reverse=True):
        out = out.replace(en, TITLE_PHRASE_KO[en])
    if has_hangul(out):
        return out
    ko = translate_en_to_ko(s, cache)
    if ko and is_good_korean(ko):
        return ko
    return s


def rebuild_stories(p: dict) -> None:
    images = list(p.get("images") or [])
    desc = (p.get("descriptionKo") or "").strip()
    feats = list(p.get("featuresKo") or [])
    tech = p.get("techSpecs") or []
    mat = ""
    madein = ""
    dims = ""
    for row in tech:
        if not isinstance(row, dict):
            continue
        label = str(row.get("labelKo") or "")
        val = str(row.get("valueKo") or "")
        if label == "소재":
            mat = val
        elif label == "제조국":
            madein = f"제조국: {val}" if val else ""
        elif label == "크기":
            dims = val
    cols = set(p.get("diCollections") or [])
    if cols.intersection(MEN_RTW_COLS | SHOE_COLS):
        p["storySections"] = _men_rtw.story_sections_for_rtw(
            desc, images, features_ko=feats, material_ko=mat, madein=madein,
        )
    elif cols.intersection(WOMEN_RTW_COLS):
        p["storySections"] = _women_rtw.story_sections_for_rtw(
            desc, images, features_ko=feats, material_ko=mat, madein=madein,
        )
    else:
        p["storySections"] = _acc.story_sections_for_slg(
            desc, images, features_ko=feats, material_ko=mat, madein=madein, dims_ko=dims,
        )


def polish_tech(p: dict) -> bool:
    changed = False
    for row in p.get("techSpecs") or []:
        if not isinstance(row, dict):
            continue
        val = str(row.get("valueKo") or "").strip()
        if val in MATERIAL_KO:
            row["valueKo"] = MATERIAL_KO[val]
            changed = True
        elif val in MADEIN_KO:
            row["valueKo"] = MADEIN_KO[val]
            changed = True
    return changed


def apply_glossary(p: dict) -> bool:
    changed = False
    feats = p.get("featuresKo") or []
    new_feats = []
    for feat in feats:
        if isinstance(feat, str) and feat in FEATURE_KO:
            new_feats.append(FEATURE_KO[feat])
            changed = True
        else:
            new_feats.append(feat)
    if changed:
        p["featuresKo"] = new_feats
    return changed


def fix_product(p: dict, bad_fields: set[str], cache: dict[str, str]) -> int:
    fixed = 0
    title_en = (p.get("name") or "").strip()
    if needs_korean_title(p.get("nameKo")) and title_en:
        ko_title = translate_title_text(title_en, cache)
        if ko_title and has_hangul(ko_title):
            p["nameKo"] = ko_title
            fixed += 1
    gloss_changed = apply_glossary(p)
    tech_changed = polish_tech(p)
    if gloss_changed or tech_changed:
        fixed += 1
    if any(f == "descriptionKo" for f in bad_fields):
        old = (p.get("descriptionKo") or "").strip()
        new = tr_line(old, cache)
        if new != old:
            p["descriptionKo"] = new
            fixed += 1

    feats = list(p.get("featuresKo") or [])
    new_feats: list[str] = []
    feat_changed = False
    for feat in feats:
        if not isinstance(feat, str):
            new_feats.append(str(feat))
            continue
        if "featuresKo" in bad_fields and not is_good_korean(feat):
            ko = tr_line(feat, cache)
            new_feats.append(ko)
            if ko != feat:
                feat_changed = True
                fixed += 1
        else:
            new_feats.append(feat)
    if feat_changed:
        p["featuresKo"] = new_feats

    variants = list(p.get("variants") or [])
    variant_changed = False
    for vv in variants:
        if not isinstance(vv, dict):
            continue
        old_color = str(vv.get("colorNameKo") or "").strip()
        new_color = translate_color(old_color, cache)
        if new_color != old_color:
            vv["colorNameKo"] = new_color
            variant_changed = True
    sorted_variants = sorted(variants, key=lambda v: size_sort_key(v.get("size")))
    if sorted_variants != variants:
        p["variants"] = sorted_variants
        variant_changed = True
    if variant_changed:
        fixed += 1

    sections = list(p.get("storySections") or [])
    sec_changed = False
    for i, sec in enumerate(sections):
        if not isinstance(sec, dict):
            continue
        key = f"story[{i}].bodyKo"
        if key not in bad_fields:
            continue
        old = str(sec.get("bodyKo") or "").strip()
        if not old:
            continue
        # Detail sections built from features — rebuild wholesale below.
        if sec.get("titleKo") in ("디테일 & 특징", "소재 & 스펙", "디테일"):
            sec_changed = True
            continue
        new = tr_line(old, cache)
        if new != old:
            sec["bodyKo"] = new
            sec_changed = True
            fixed += 1
    if feat_changed or sec_changed or gloss_changed or tech_changed or any(
        f.startswith("story[") for f in bad_fields
    ):
        rebuild_stories(p)
        fixed += 1
    return fixed


def needs_variant_cleanup(p: dict) -> bool:
    variants = [v for v in (p.get("variants") or []) if isinstance(v, dict)]
    if len(variants) >= 2:
        sizes = [v.get("size") for v in variants]
        if sizes != [v.get("size") for v in sorted(variants, key=lambda x: size_sort_key(x.get("size")))]:
            return True
    for vv in variants:
        color = str(vv.get("colorNameKo") or "").strip()
        if color and not has_hangul(color) and color.lower() in COLOR_KO:
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", choices=("all", "acc-shoes"), default="all")
    args = ap.parse_args()

    products = load_products(CAT)
    by_id = {str(p.get("id")): p for p in products if p.get("id")}
    bad = check_brand("di")
    cache = load_cache()

    by_pid: dict[str, set[str]] = {}
    for _brand, pid, field, _ratio, _snippet in bad:
        p = by_id.get(pid)
        if not p or not in_scope(p, args.scope):
            continue
        by_pid.setdefault(pid, set()).add(field)

    # Also catch title/color/sort issues that Korean QA intentionally skips.
    for p in products:
        if not in_scope(p, args.scope):
            continue
        pid = str(p.get("id"))
        if needs_korean_title(p.get("nameKo")) or needs_variant_cleanup(p):
            by_pid.setdefault(pid, set())

    # Also polish acc/shoes products for glossary + tech even if not in bad list.
    if args.scope == "acc-shoes":
        for p in products:
            if in_scope(p, args.scope):
                by_pid.setdefault(str(p.get("id")), set())

    print(f"fix targets: {len(by_pid)} products (scope={args.scope})", flush=True)
    total_fixed = 0
    for i, (pid, fields) in enumerate(sorted(by_pid.items()), 1):
        n = fix_product(by_id[pid], fields, cache)
        total_fixed += n
        if i % CHECKPOINT == 0:
            CAT.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n")
            save_cache(cache)
            print(f"  checkpoint {i}/{len(by_pid)} fixed_ops={total_fixed}", flush=True)
        time.sleep(0.05)

    CAT.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n")
    save_cache(cache)

    remaining = check_brand("di")
    if args.scope == "acc-shoes":
        remaining = [
            b for b in remaining if in_scope(by_id.get(b[1], {}), "acc-shoes")
        ]
    print(f"DONE fixed_ops={total_fixed} remaining_bad={len(remaining)}", flush=True)
    for row in remaining[:15]:
        print(f"  {row[1]} {row[2]} en_ratio={row[3]:.2f} {row[4][:80]}", flush=True)
    return 0 if not remaining else 1


if __name__ == "__main__":
    raise SystemExit(main())
