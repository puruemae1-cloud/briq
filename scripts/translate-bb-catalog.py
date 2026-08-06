#!/usr/bin/env python3
"""Translate Burberry catalog copy EN→KO via Google gtx + fashion glossary polish.

Replaces the old phrase-dictionary mangler that produced mixed EN/KO copy like
"our 헤리티지 styles, 서머사이드 트렌치 코트 is 테일러드…".
"""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "src/data/bb/bb-catalog-raw.json"
CACHE_PATH = ROOT / "src/data/bb/bb-translate-cache.json"

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
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=45) as r:
        data = json.loads(r.read().decode())
    return "".join(part[0] for part in data[0] if part and part[0])


def polish(text: str) -> str:
    out = (text or "").strip()
    # Glossary longest-first
    for en, ko in sorted(GLOSSARY, key=lambda x: -len(x[0])):
        out = re.sub(re.escape(en), ko, out, flags=re.I)
    out = out.replace("Burberry", "버버리")
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
    args = ap.parse_args()

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
            # Keep Korean-only / numeric as-is when already KO, else identity
            cache[s] = prev.get(s) or s
            continue
        old = prev.get(s)
        if old and is_good_ko(s, old):
            cache[s] = polish(old)
            kept += 1
        else:
            todo.append(s)

    print(
        f"strings={len(strings)} keep={kept} translate={len(todo)} sleep={args.sleep}",
        flush=True,
    )

    ok = fail = 0
    for i, s in enumerate(todo, start=1):
        try:
            ko = polish(gtx(s))
            if not ko:
                raise RuntimeError("empty")
            cache[s] = ko
            ok += 1
        except Exception as e:  # noqa: BLE001
            fail += 1
            # Prefer previous mangled over dropping the key entirely
            cache[s] = polish(prev.get(s) or s)
            if fail <= 15:
                print(f"fail [{i}]: {e} :: {s[:80]}", flush=True)
        if i % 50 == 0 or i == len(todo):
            print(f"{i}/{len(todo)} ok={ok} fail={fail}", flush=True)
            CACHE_PATH.write_text(
                json.dumps(cache, ensure_ascii=False, indent=2) + "\n"
            )
        time.sleep(args.sleep)

    # Preserve unrelated previous keys (colours etc. from older runs)
    for k, v in prev.items():
        if k not in cache and v:
            cache[k] = v

    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n")

    # Sample the summerside trench description
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
