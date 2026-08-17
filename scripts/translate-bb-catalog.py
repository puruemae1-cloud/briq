#!/usr/bin/env python3
"""Translate Burberry catalog copy EN→KO via Google gtx + fashion glossary polish.

Replaces the old phrase-dictionary mangler that produced mixed EN/KO copy like
"our 헤리티지 styles, 서머사이드 트렌치 코트 is 테일러드…".

Weekly CI must run this before build-bb-catalog.py, then --check-catalog after.
"""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "src/data/bb/bb-catalog-raw.json"
CACHE_PATH = ROOT / "src/data/bb/bb-translate-cache.json"
CATALOG_JSON = ROOT / "src/data/bb/bb-catalog.json"

# Applied after MT so brand/material terms stay consistent with the rest of Briq.
GLOSSARY = [
    ("버버리 체크", "버버리 체크"),  # keep
    ("Burberry Check", "버버리 체크"),
    ("Burberry", "버버리"),
    ("Equestrian Knight Design", "에퀘스트리언 나이트 디자인"),
    ("Equestrian Knight", "에퀘스트리언 나이트"),
    ("에퀘스트리언 나이트 디자인", "에퀘스트리언 나이트 디자인"),
    ("Gabardine", "개버딘"),
    ("개버딘", "개버딘"),
    ("Prince of Wales", "프린스 오브 웨일스"),
    ("Tropical Gabardine", "트로피컬 개버딘"),
    ("Summerside", "서머사이드"),
    ("Kensington", "켄싱턴"),
    ("Chelsea", "첼시"),
    ("Waterloo", "워털루"),
    ("Camden", "캠든"),
    ("Islington", "이즐링턴"),
    ("Belmont", "벨몬트"),
    ("Mayfair", "메이페어"),
    ("Heritage", "헤리티지"),
    ("Trench Coat", "트렌치 코트"),
    ("Car Coat", "카 코트"),
    ("House Check", "하우스 체크"),
    ("Knight stamp", "나이트 스탬프"),
    ("Knight Stamp", "나이트 스탬프"),
    ("Garbardine", "개버딘"),
    ("Lakefield", "레이크필드"),
    ("Mews Espadrille", "뮤즈 에스파드리유"),
    ("Raining Cats and Dogs", "레이닝 캣츠 앤 독스"),
    ("Regular fit", "레귤러 핏"),
    ("Loose fit", "루즈 핏"),
    ("Classic fit", "클래식 핏"),
    ("Oversized fit", "오버사이즈 핏"),
    ("at side", "측면"),
    ("Made in Italy", "이탈리아 제작"),
    ("Made in Scotland", "스코틀랜드에서 제작됨"),
    ("Made in Korea", "한국에서 제작됨"),
    ("Made in Monaco", "모나코에서 제작됨"),
    ("Made in Spain", "스페인에서 제작됨"),
    ("Made in France", "프랑스에서 제작됨"),
    ("Made in Japan", "일본에서 제작됨"),
    ("Made in China", "중국에서 제작됨"),
    ("Made in UK", "영국에서 제작됨"),
    ("Made in the UK", "영국에서 제작됨"),
]

SKIP_EXACT = {
    "Burberry",
    "UK",
    "EU",
    "US",
    "ml",
    "cm",
    "in",
}

ALLOW_EN = {
    "uk",
    "eu",
    "us",
    "ml",
    "cm",
    "in",
    "xl",
    "xxl",
    "xxs",
    "xs",
    "ss",
    "aw",
    "id",
    "sku",
    "ip",
    "rfid",
}


def hangul_ratio(text: str) -> float:
    if not text:
        return 0.0
    h = sum(1 for c in text if "\uac00" <= c <= "\ud7a3")
    return h / max(len(text), 1)


def leftover_en_words(text: str) -> list[str]:
    return [
        w
        for w in re.findall(r"[A-Za-z]{3,}", text or "")
        if w.lower() not in ALLOW_EN
    ]


def is_good_ko(src: str, ko: str | None) -> bool:
    """True when cached KO looks like a real translation, not phrase-mangled mix."""
    if not ko or ko == src:
        return False
    if hangul_ratio(ko) < 0.28:
        return False
    leftovers = leftover_en_words(ko)
    # Mixed EN/KO mangling typically leaves several English tokens.
    if len(leftovers) >= 3:
        return False
    if leftovers and hangul_ratio(ko) < 0.45:
        return False
    # Classic mangler fingerprints
    if re.search(r"(?i)\b(is|are|to|for|our|the|and|with|in|of)\b", ko):
        if hangul_ratio(ko) < 0.7:
            return False
    if " 및 " in ko and leftover_en_words(ko):
        # "Neat 및 narrow" style
        if hangul_ratio(ko) < 0.55:
            return False
    return True


def gtx(text: str) -> str:
    q = urllib.parse.quote(text[:4500])
    url = (
        "https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl=en&tl=ko&dt=t&q={q}"
    )
    last_err: Exception | None = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=45) as r:
                data = json.loads(r.read().decode())
            return "".join(part[0] for part in data[0] if part and part[0])
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(0.6 * (attempt + 1))
    raise RuntimeError(last_err)


def prepare_en(text: str) -> str:
    """Nudge gtx so Burberry 'Check' is the pattern, not the verb '확인'."""
    s = (text or "").strip()
    s = s.replace("Garbardine", "Gabardine")
    s = re.sub(r"\bCheck\b", "Burberry Check", s)
    return s


def polish(text: str) -> str:
    out = (text or "").strip()
    # Glossary longest-first
    for en, ko in sorted(GLOSSARY, key=lambda x: -len(x[0])):
        out = re.sub(re.escape(en), ko, out, flags=re.I)
    out = out.replace("Burberry", "버버리")
    out = re.sub(r"Max\.\s*", "최대 ", out, flags=re.I)
    # MT sometimes renders the Check pattern as the verb '확인'
    out = re.sub(r"(펌프|펌프스)\s*확인", r"체크 \1", out)
    out = re.sub(r"확인\s*(펌프|펌프스)", r"체크 \1", out)
    # Light cleanup of MT artifacts
    out = re.sub(r"\s{2,}", " ", out)
    out = re.sub(r"\s+([,.!?])", r"\1", out)
    out = out.replace(" .", ".")
    return out.strip()


def collect_strings(raw: dict) -> set[str]:
    strings: set[str] = set()
    for p in raw.get("products") or []:
        for key in (
            "title",
            "color",
            "description",
            "measurements",
            "materialComposition",
        ):
            val = p.get(key)
            if not val:
                continue
            if key == "description":
                for part in str(val).split("##"):
                    if part.strip():
                        strings.add(part.strip())
            else:
                strings.add(str(val).strip())
        for acc in p.get("accordion") or []:
            if acc.get("label"):
                strings.add(str(acc["label"]).strip())
            for text in acc.get("texts") or []:
                for piece in str(text).split("#"):
                    if piece.strip():
                        strings.add(piece.strip())
    return strings


_CHECK_NOISE = re.compile(
    r"Made in (?:the )?([A-Za-z]+)|"
    r"\d+(?:\.\d+)?\s*(?:cm|mm|in|ft|oz|ml|g)|"
    r"\b(?:fl|oz|Max)\b",
    re.I,
)


def catalog_field_ok(text: str | None) -> bool:
    """True when shop-facing copy is Korean enough to show on briq.kr.

    Allows leftover Latin in measurements, 'Made in …', and a couple of
    proper nouns once the sentence is already mostly Hangul.
    """
    s = (text or "").strip()
    if not s:
        return True
    ratio = hangul_ratio(s)
    if ratio >= 0.28:
        return True
    cleaned = _CHECK_NOISE.sub(" ", s)
    leftover = leftover_en_words(cleaned)
    if not leftover:
        return True
    if hangul_ratio(cleaned) >= 0.28:
        return True
    if hangul_ratio(cleaned) >= 0.18 and len(leftover) <= 2:
        return True
    return False


def check_catalog() -> int:
    if not CATALOG_JSON.is_file():
        print(f"missing {CATALOG_JSON}", flush=True)
        return 1
    products = json.loads(CATALOG_JSON.read_text())
    bad: list[str] = []
    for p in products:
        pid = str(p.get("id") or "")
        if not catalog_field_ok(p.get("nameKo")):
            bad.append(f"nameKo {pid}: {p.get('nameKo')}")
        if not catalog_field_ok(p.get("descriptionKo")):
            snippet = str(p.get("descriptionKo") or "")[:90]
            bad.append(f"descriptionKo {pid}: {snippet}")
        for i, sec in enumerate(p.get("storySections") or []):
            if not catalog_field_ok(sec.get("titleKo")):
                bad.append(f"story.title {pid}#{i}: {sec.get('titleKo')}")
            if not catalog_field_ok(sec.get("bodyKo")):
                snippet = str(sec.get("bodyKo") or "")[:90]
                bad.append(f"story.body {pid}#{i}: {snippet}")
    print(f"bb korean check products={len(products)} bad={len(bad)}", flush=True)
    for row in bad[:40]:
        print(f"  {row}", flush=True)
    if len(bad) > 40:
        print(f"  … +{len(bad) - 40} more", flush=True)
    if bad:
        print(
            "Burberry shop copy still has English. Run translate-bb-catalog.py "
            "then build-bb-catalog.py.",
            flush=True,
        )
        return 1
    print("OK — Burberry name/description/story copy is Korean.", flush=True)
    return 0


def needs_translate(src: str) -> bool:
    if src in SKIP_EXACT:
        return False
    if len(src) < 2:
        return False
    if not re.search(r"[A-Za-z]{3,}", src):
        return False
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--fresh",
        action="store_true",
        help="Ignore previous cache and re-translate everything",
    )
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--sleep", type=float, default=0.08)
    ap.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Parallel gtx workers (weekly CI should stay 1–4)",
    )
    ap.add_argument(
        "--check-catalog",
        action="store_true",
        help="Exit 1 if bb-catalog.json still has English shop copy",
    )
    ap.add_argument(
        "--repolish",
        action="store_true",
        help="Re-apply glossary polish to the existing cache without calling gtx",
    )
    args = ap.parse_args()
    if args.check_catalog:
        raise SystemExit(check_catalog())
    if args.repolish:
        if not CACHE_PATH.exists():
            print(f"missing {CACHE_PATH}", flush=True)
            raise SystemExit(1)
        prev = json.loads(CACHE_PATH.read_text())
        polished = {k: polish(v) for k, v in prev.items()}
        # Force a few titles gtx treated as English verbs / untranslated names.
        overrides = {
            "Garbardine Lakefield Trench Jacket": "개버딘 레이크필드 트렌치 재킷",
            "Check Mews Espadrille Pumps": "체크 뮤즈 에스파드리유 펌프스",
            "Raining Cats and Dogs Silk Scarf": "레이닝 캣츠 앤 독스 실크 스카프",
        }
        for en, ko in overrides.items():
            polished[en] = ko
        CACHE_PATH.write_text(json.dumps(polished, ensure_ascii=False, indent=2) + "\n")
        print(f"repolished {len(polished)} cache entries", flush=True)
        return

    raw = json.loads(RAW_PATH.read_text())
    prev: dict[str, str] = {}
    if CACHE_PATH.exists() and not args.fresh:
        prev = json.loads(CACHE_PATH.read_text())

    strings = sorted(collect_strings(raw))
    if args.limit:
        strings = strings[: args.limit]

    cache: dict[str, str] = {}
    todo: list[str] = []
    kept = 0
    for s in strings:
        if not needs_translate(s):
            cache[s] = prev.get(s) or s
            continue
        old = prev.get(s)
        if old and is_good_ko(s, old):
            cache[s] = polish(old)
            kept += 1
        else:
            todo.append(s)

    # Titles/short phrases first so PDP names land even if a long run is cut short.
    todo.sort(key=lambda s: (len(s) > 80, len(s), s))

    print(
        f"strings={len(strings)} keep={kept} translate={len(todo)} "
        f"sleep={args.sleep} workers={args.workers}",
        flush=True,
    )

    ok = fail = 0

    def one(s: str) -> tuple[str, str | None, str | None]:
        try:
            ko = polish(gtx(prepare_en(s)))
            if not ko:
                raise RuntimeError("empty")
            return s, ko, None
        except Exception as e:  # noqa: BLE001
            return s, polish(prev.get(s) or s), str(e)

    workers = max(1, args.workers)
    if workers == 1:
        for i, s in enumerate(todo, start=1):
            _, ko, err = one(s)
            cache[s] = ko or s
            if err:
                fail += 1
                if fail <= 15:
                    print(f"fail [{i}]: {err} :: {s[:80]}", flush=True)
            else:
                ok += 1
            if i % 50 == 0 or i == len(todo):
                print(f"{i}/{len(todo)} ok={ok} fail={fail}", flush=True)
                CACHE_PATH.write_text(
                    json.dumps(cache, ensure_ascii=False, indent=2) + "\n"
                )
            time.sleep(args.sleep)
    else:
        done = 0
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(one, s) for s in todo]
            for fut in as_completed(futs):
                s, ko, err = fut.result()
                cache[s] = ko or s
                done += 1
                if err:
                    fail += 1
                    if fail <= 15:
                        print(f"fail [{done}]: {err} :: {s[:80]}", flush=True)
                else:
                    ok += 1
                if done % 50 == 0 or done == len(todo):
                    print(f"{done}/{len(todo)} ok={ok} fail={fail}", flush=True)
                    CACHE_PATH.write_text(
                        json.dumps(cache, ensure_ascii=False, indent=2) + "\n"
                    )

    for k, v in prev.items():
        if k not in cache and v:
            cache[k] = v

    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n")

    sample = None
    for p in raw.get("products") or []:
        if str(p.get("id")) == "81262671":
            sample = (p.get("description") or "").split("##")[0].strip()
            break
    if sample:
        print("SAMPLE EN:", sample[:160], flush=True)
        print("SAMPLE KO:", cache.get(sample, "")[:220], flush=True)
    print(f"wrote {CACHE_PATH} entries={len(cache)}", flush=True)


if __name__ == "__main__":
    main()
