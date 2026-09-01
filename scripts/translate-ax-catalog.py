#!/usr/bin/env python3
"""Fill missing EN→KO strings for Arc'teryx PDP copy into ax-translate-cache.json.

Must cover footwear (`ax-pdp-cache.json`), apparel, gear, and outlet PDP caches.
Weekly sync calls this before catalogue rebuilds — wrong paths leave English
feature bodies on the live PDP (titles often already in the glossary/cache).
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from ko_qa import (  # noqa: E402
    MAX_KO_EN_RATIO,
    en_ratio,
    has_hangul,
    is_good_korean,
    translate_en_to_ko,
)
from ax_translate_common import normalize_en, load_ax_translate_cache  # noqa: E402

CACHE_PATH = ROOT / "src/data/ax/ax-translate-cache.json"
PDP_PATHS = [
    ROOT / "src/data/ax/ax-apparel-pdp-cache.json",
    ROOT / "src/data/ax/ax-outlet-pdp-cache.json",
    ROOT / "src/data/ax/ax-gear-pdp-cache.json",
    # Footwear — historical mistake used ax-footwear-pdp-cache.json (never written)
    ROOT / "src/data/ax/ax-pdp-cache.json",
]

SKIP_EXACT = {
    "Arc'teryx",
    "GORE-TEX",
    "GORE-TEX PRO",
    "GORE-TEX INFINIUM",
    "PrimaLoft",
    "Coreloft",
    "Down Contour",
    "FC0",
    "Vibram",
    "Vibram®",
    "Megagrip",
    "Matryx",
    "Matryx®",
    "LITEBASE",
    "Litebase",
}

# Prefer natural PDP labels over literal MT for short feature headings.
GLOSSARY: dict[str, str] = {
    "Technical features": "기술 특징",
    "Footwear construction": "슈즈 구조",
    "Footwear geometry": "슈즈 지오메트리",
    "Footwear liner construction": "안창 구조",
    "Footwear outsole construction": "아웃솔 구조",
    "Footwear upper construction": "갑피 구조",
    "Sustainability": "지속가능성",
    "Materials": "소재",
    "Care": "관리",
    "Surface clean only": "표면만 가볍게 닦아 관리하세요",
    "Fit": "핏",
    "Weight": "무게",
    "Activity": "활동",
    "Features": "특징",
    "Construction": "구조",
    "Regular": "레귤러",
    "Relaxed": "릴랙스드",
    "Oversized": "오버사이즈",
    "Slim": "슬림",
    "Fitted": "핏",
    "Next to Skin": "스킨핏",
    "Micro-serged seams": "마이크로 오버로크 솔기",
    "Fitted sleeves": "슬림핏 소매",
    "Two side pockets": "양옆 포켓 2개",
    "Stowable hood": "수납형 후드",
    "Mid-calf length": "종아리 중간 길이",
    "Shaped cuffs": "쉐입드 커프",
    "Laminated elastic hem": "라미네이트 탄성 밑단",
    "A-line design": "A라인 실루엣",
    "Adjustable waist drawcord": "조절 가능한 허리 드로우코드",
    "Adjustable hood drawcords": "조절 가능한 후드 드로우코드",
    "Low profile thumbholes": "로우 프로파일 엄지손가락 구멍",
    "Helmet compatible": "헬멧 호환",
    "Our classic fit is cut comfortably throughout the chest, waist, hip, and thigh. It allows freedom of movement, provides shape, and layers comfortably under our regular and relaxed fit shells.": "클래식 핏은 가슴, 허리, 엉덩이, 허벅지 전체에 걸쳐 편안하게 재단됩니다. 이는 자유로운 움직임을 허용하고, 레귤러하고 편안한 핏의 쉘 아래에 편안하게 모양과 레이어를 제공합니다.",
}


def strip_html(text: str) -> str:
    return normalize_en(text)


def collect_strings() -> set[str]:
    out: set[str] = set()
    missing_paths = [p for p in PDP_PATHS if not p.exists()]
    for path in missing_paths:
        print(f"WARN missing PDP cache (skipped): {path.name}", flush=True)
    for path in PDP_PATHS:
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        n = 0
        for rec in data.values() if isinstance(data, dict) else []:
            if not isinstance(rec, dict) or rec.get("error"):
                continue
            n += 1
            for key in (
                "title",
                "tagline",
                "description",
                "weight",
                "fit",
                "category",
                "subCategory",
            ):
                val = rec.get(key)
                if isinstance(val, str) and val.strip():
                    out.add(strip_html(val))
            for sec in rec.get("sections") or []:
                if not isinstance(sec, dict):
                    continue
                for key in ("heading", "title", "body", "text"):
                    val = sec.get(key)
                    if isinstance(val, str) and val.strip():
                        out.add(strip_html(val))
            for feat in rec.get("features") or []:
                if not isinstance(feat, dict):
                    continue
                for key in ("title", "body", "text"):
                    val = feat.get(key)
                    if isinstance(val, str) and val.strip():
                        out.add(strip_html(val))
            for row in rec.get("techSpecs") or rec.get("specs") or []:
                if isinstance(row, dict):
                    for key in ("label", "value", "title", "body"):
                        val = row.get(key)
                        if isinstance(val, str) and val.strip():
                            out.add(strip_html(val))
                elif isinstance(row, str) and row.strip():
                    out.add(strip_html(row))
        print(f"  {path.name}: {n} PDPs", flush=True)
    return {s for s in out if s}


def polish_ko(text: str) -> str:
    out = text
    for a, b in [
        ("고어텍스", "GORE-TEX"),
        ("프리마로프트", "PrimaLoft"),
        ("후드티", "후디"),
        ("후드 티", "후디"),
        ("신발 제작", "슈즈 구조"),
        ("신발 기하학", "슈즈 지오메트리"),
        ("신발 라이너 건설", "안창 구조"),
        ("신발 밑창 구조", "아웃솔 구조"),
        ("라이너 건설", "안창 구조"),
        ("지속 가능성", "지속가능성"),
        ("  ", " "),
    ]:
        out = out.replace(a, b)
    return out.strip()


def needs_translate(src: str, cached: str | None) -> bool:
    if src in SKIP_EXACT:
        return False
    if src in GLOSSARY:
        if cached != GLOSSARY[src]:
            return True
        return False
    if not re.search(r"[A-Za-z]{3,}", src or ""):
        return False
    if len(src) < 3:
        return False
    # Skip pure colourway / SKU-ish tokens
    if (
        re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 \-_/]{0,40}", src)
        and len(src.split()) <= 3
        and len(src) < 28
    ):
        if not re.search(r"\b(the|and|for|with|from|made|designed)\b", src, re.I):
            return False
    if cached and is_good_korean(cached, max_ratio=MAX_KO_EN_RATIO) and cached != src:
        # Still refresh awkward literal footwear titles from old MT
        if cached in {
            "신발 제작",
            "신발 기하학",
            "신발 라이너 건설",
            "신발 밑창 구조",
        }:
            return True
        return False
    if cached and has_hangul(cached) and not is_good_korean(cached, max_ratio=MAX_KO_EN_RATIO):
        return True
    return True


def main() -> None:
    cache: dict[str, str] = load_ax_translate_cache(CACHE_PATH)

    # Seed / refresh glossary first so builds never fall back to awkward MT titles.
    for en, ko in GLOSSARY.items():
        cache[normalize_en(en)] = ko

    strings = sorted(collect_strings())
    todo = [s for s in strings if needs_translate(s, cache.get(normalize_en(s)))]
    print(f"strings={len(strings)} todo={len(todo)} cached={len(cache)}", flush=True)

    def cache_hit(src: str) -> str | None:
        nk = normalize_en(src)
        if nk in cache and cache[nk] != nk:
            return cache[nk]
        extended = [k for k in cache if k.startswith(nk) and len(k) > len(nk)]
        if extended:
            return cache[max(extended, key=len)]
        return None

    done = 0
    failed = 0
    rate_limited = 0
    for s in todo:
        if s in GLOSSARY:
            cache[normalize_en(s)] = GLOSSARY[s]
            done += 1
            continue
        pref = cache_hit(s)
        if pref and is_good_korean(pref, max_ratio=MAX_KO_EN_RATIO):
            cache[normalize_en(s)] = pref
            done += 1
            continue
        try:
            ko = polish_ko(translate_en_to_ko(s, cache=None, max_ratio=MAX_KO_EN_RATIO))
        except Exception as e:
            msg = str(e)
            print(f"FAIL {s[:60]!r}: {e}", flush=True)
            failed += 1
            if "429" in msg or "Too Many" in msg:
                rate_limited += 1
                if rate_limited >= 5:
                    print(
                        "Rate-limited — stopping translate early. "
                        "Footwear seed + existing cache still apply.",
                        flush=True,
                    )
                    break
                time.sleep(8)
            else:
                time.sleep(1.2)
            continue
        if ko and is_good_korean(ko, max_ratio=0.45):
            cache[normalize_en(s)] = ko
            done += 1
            rate_limited = 0
            if done <= 12 or done % 25 == 0:
                print(f"[{done}/{len(todo)}] {s[:70]} => {ko[:70]}", flush=True)
        else:
            failed += 1
            if ko == s or (ko and en_ratio(ko) >= 0.9):
                rate_limited += 1
                if rate_limited >= 8:
                    print(
                        "Translations returning English — stopping early "
                        "(likely rate limit). Footwear seed still applies.",
                        flush=True,
                    )
                    break
            print(
                f"WARN weak KO (en_ratio={en_ratio(ko or s):.2f}): {s[:70]!r}",
                flush=True,
            )
        if done % 20 == 0:
            CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n")
            time.sleep(0.12)
        else:
            time.sleep(0.05)

    # Polish existing awkward titles already in cache
    for en, ko in list(cache.items()):
        polished = polish_ko(ko)
        if polished != ko:
            cache[en] = polished

    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n")
    print(
        f"Wrote {CACHE_PATH} entries={len(cache)} new/updated={done} weak/fail={failed}",
        flush=True,
    )
    if failed and done == 0 and rate_limited == 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
