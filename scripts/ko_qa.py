#!/usr/bin/env python3
"""Shared EN→KO quality helpers for Briq product catalogues.

Goals:
  - Never treat hybrid EN/KO (glossary-only leftovers) as a successful translation
  - Fail builds / weekly syncs when newly updated PDP copy is still English
  - Provide one CLI (`check-catalog-korean.py`) for every brand
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]

# Latin-letter ratio above this on a KO field ⇒ treat as hybrid / untranslated.
MAX_KO_EN_RATIO = 0.30

# Brand / tech tokens that may remain Latin in otherwise-Korean copy.
_WHITELIST_TOKENS = (
    "Re-Nylon",
    "Re-Edition",
    "Linea Rossa",
    "GORE-TEX",
    "INFINIUM",
    "PrimaLoft",
    "Coreloft",
    "Symbole",
    "Shadowplay",
    "Eyewear Collection",
    "Oakley",
    "Prizm",
    "Switchlock",
    "Chanel",
    "Gucci",
    "Prada",
    "Burberry",
    "Arc'teryx",
    "Belstaff",
    "Vibram",
    "Megagrip",
    "Matryx",
    "LITEBASE",
    "Litebase",
    "Fair Trade Certified",
    "PFAS",
    "Norvan",
    "Aerios",
    "Konseal",
    "Sylan",
    "UVA",
    "UVB",
    "TSA",
    "EVA",
    "TPU",
    "SKU",
    "GB",
    "UK",
    "EU",
    "US",
    "mm",
    "cm",
    "kg",
)

CATALOG_PATHS: dict[str, list[Path]] = {
    "pr": [ROOT / "src/data/pr/pr-catalog.json"],
    "gc": [ROOT / "src/data/gc/gc-catalog.json"],
    "ch": [ROOT / "src/data/ch/ch-catalog.json"],
    "bb": [ROOT / "src/data/bb/bb-catalog.json"],
    "bs": [ROOT / "src/data/bs/bs-catalog.json"],
    "ps": [ROOT / "src/data/ps/ps-catalog.json"],
    "ax": [
        # Prefer JSON companions written by build-ax-*-catalog.py (used by KO gate).
        ROOT / "src/data/ax/ax-catalog.json",
        ROOT / "src/data/ax/ax-apparel-catalog.json",
        ROOT / "src/data/ax/ax-gear-catalog.json",
        ROOT / "src/data/ax/ax-outlet-catalog.json",
    ],
    "gg": [ROOT / "src/data/gg/gg-catalog.json"],
    "lu": [
        ROOT / "src/data/lu/lu-catalog.ts",
        ROOT / "src/data/lu/lu-lifestyle-catalog.ts",
    ],
    "cw": [ROOT / "src/data/cw/cw-catalog.ts"],
    "lv": [ROOT / "src/data/lv/lv-catalog.json"],
    "di": [ROOT / "src/data/di/di-catalog.json"],
}


def en_ratio(s: str) -> float:
    """Latin-letter ratio; whitelisted brand/tech tokens are ignored."""
    cleaned = s or ""
    for tok in _WHITELIST_TOKENS:
        cleaned = re.sub(re.escape(tok), "", cleaned, flags=re.I)
    letters = [c for c in cleaned if c.isalpha()]
    if not letters:
        return 0.0
    latin = sum(1 for c in letters if ("A" <= c <= "Z") or ("a" <= c <= "z"))
    return latin / len(letters)


def has_hangul(s: str) -> bool:
    return any("\uac00" <= c <= "\ud7a3" for c in (s or ""))


def is_good_korean(text: str | None, *, max_ratio: float = MAX_KO_EN_RATIO) -> bool:
    """True if text is empty, already Korean-enough, or short non-prose."""
    s = (text or "").strip()
    if not s:
        return True
    # Pure codes / dimensions / numbers
    if not re.search(r"[A-Za-z]{3,}", s):
        return True
    if len(s) < 4:
        return True
    return en_ratio(s) <= max_ratio


def load_products(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    if path.suffix == ".ts":
        return _load_ts_products(path)
    data = json.loads(path.read_text())
    if isinstance(data, list):
        return [p for p in data if isinstance(p, dict)]
    if isinstance(data, dict):
        prods = data.get("products")
        if isinstance(prods, list):
            return [p for p in prods if isinstance(p, dict)]
    return []


def _load_ts_products(path: Path) -> list[dict[str, Any]]:
    """Best-effort parse of generated catalogue .ts (JSON-like product array)."""
    text = path.read_text()
    m = re.search(r"export const \w+\s*=\s*(\[[\s\S]*\])\s*;?\s*$", text)
    if not m:
        return []
    body = m.group(1)
    body = re.sub(r"\s+as\s+Product\[[^\]]+\]", "", body)
    body = re.sub(r",\s*([}\]])", r"\1", body)
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return []
    return [p for p in data if isinstance(p, dict)] if isinstance(data, list) else []


def product_ko_fields(p: dict[str, Any]) -> list[tuple[str, str]]:
    """Fields that must be natural Korean on the PDP (body copy, not fashion titles)."""
    out: list[tuple[str, str]] = []
    # nameKo often keeps English style names / colourways on purpose — skip.
    for key in ("descriptionKo",):
        val = p.get(key)
        if isinstance(val, str) and val.strip():
            out.append((key, val.strip()))
    for feat in p.get("featuresKo") or []:
        if isinstance(feat, str) and feat.strip():
            # Colourway / logo callouts keep Latin colour names on purpose.
            if feat.startswith("로고") or "Logos" in feat:
                continue
            out.append(("featuresKo", feat.strip()))
    for i, sec in enumerate(p.get("storySections") or []):
        if not isinstance(sec, dict):
            continue
        title = str(sec.get("titleKo") or "")
        body = sec.get("bodyKo")
        if not isinstance(body, str) or not body.strip():
            continue
        # Gallery placeholders often embed English product titles — skip.
        if title == "갤러리" or body.strip().endswith("의 디테일.") or body.strip() == "제품 디테일.":
            continue
        # Colourway / logo callouts keep Latin colour names on purpose.
        if "Bird logo" in body or "로고가 있" in body or title.startswith("로고"):
            continue
        out.append((f"story[{i}].bodyKo", body.strip()))
    return out


def find_hybrid_fields(
    products: Iterable[dict[str, Any]],
    *,
    max_ratio: float = MAX_KO_EN_RATIO,
    ids: set[str] | None = None,
    new_since: str | None = None,
) -> list[tuple[str, str, float, str]]:
    """Return (product_id, field, en_ratio, snippet) for failing KO fields."""
    bad: list[tuple[str, str, float, str]] = []
    for p in products:
        pid = str(p.get("id") or "")
        if ids is not None and pid not in ids:
            continue
        if new_since:
            reg = str(p.get("registeredAt") or "")
            if not reg or reg < new_since:
                continue
        for field, val in product_ko_fields(p):
            if is_good_korean(val, max_ratio=max_ratio):
                continue
            bad.append((pid, field, en_ratio(val), val[:100]))
    bad.sort(key=lambda x: -x[2])
    return bad


def gtx_translate(text: str) -> str:
    """Google gtx EN→KO with MyMemory fallback."""

    def _gtx(chunk: str) -> str:
        q = urllib.parse.quote(chunk[:4500])
        url = (
            "https://translate.googleapis.com/translate_a/single"
            f"?client=gtx&sl=en&tl=ko&dt=t&q={q}"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=35) as r:
            data = json.loads(r.read().decode())
        return "".join(part[0] for part in data[0] if part and part[0])

    def _mymemory(chunk: str) -> str:
        url = (
            "https://api.mymemory.translated.net/get"
            f"?q={urllib.parse.quote(chunk[:480])}&langpair=en|ko"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=35) as r:
            data = json.loads(r.read().decode())
        return (data.get("responseData") or {}).get("translatedText") or ""

    text = (text or "").strip()
    if not text:
        return ""
    chunks: list[str]
    if len(text) <= 480:
        chunks = [text]
    else:
        parts = re.split(r"(?<=[.!?])\s+", text)
        chunks = []
        buf = ""
        for part in parts:
            if len(buf) + len(part) + 1 <= 480:
                buf = f"{buf} {part}".strip()
            else:
                if buf:
                    chunks.append(buf)
                buf = part
        if buf:
            chunks.append(buf)

    outs: list[str] = []
    for chunk in chunks:
        out = ""
        try:
            out = _gtx(chunk)
        except Exception:
            out = ""
        if not out or en_ratio(out) >= 0.55:
            try:
                out = _mymemory(chunk)
            except Exception:
                out = out or ""
        if not out:
            raise RuntimeError("translate-failed")
        outs.append(out)
        time.sleep(0.08)
    return " ".join(outs)


def translate_en_to_ko(
    text: str | None,
    cache: dict[str, str] | None = None,
    *,
    max_ratio: float = MAX_KO_EN_RATIO,
    retries: int = 4,
    offline: bool = False,
) -> str:
    """Translate EN→KO; only cache results that pass the Korean QA ratio."""
    s = re.sub(r"\s+", " ", (text or "").strip())
    if not s:
        return ""
    if cache is not None and s in cache and is_good_korean(cache[s], max_ratio=max_ratio):
        return cache[s]
    if is_good_korean(s, max_ratio=0.35) and has_hangul(s):
        if cache is not None:
            cache[s] = s
        return s
    if en_ratio(s) < 0.35 or len(s) < 3:
        if cache is not None:
            cache[s] = s
        return s
    if offline:
        return s
    last = s
    for attempt in range(retries):
        try:
            ko = gtx_translate(s).strip()
            if ko and is_good_korean(ko, max_ratio=max_ratio):
                if cache is not None:
                    cache[s] = ko
                return ko
            if ko:
                last = ko
        except Exception:
            pass
        time.sleep(0.15 * (attempt + 1))
    return last


def check_brand(
    brand: str,
    *,
    max_ratio: float = MAX_KO_EN_RATIO,
    ids: set[str] | None = None,
    new_since: str | None = None,
) -> list[tuple[str, str, str, float, str]]:
    """Return failures as (brand, product_id, field, ratio, snippet)."""
    paths = CATALOG_PATHS.get(brand)
    if not paths:
        raise KeyError(f"unknown brand {brand!r}; known={sorted(CATALOG_PATHS)}")
    out: list[tuple[str, str, str, float, str]] = []
    for path in paths:
        for pid, field, ratio, snippet in find_hybrid_fields(
            load_products(path),
            max_ratio=max_ratio,
            ids=ids,
            new_since=new_since,
        ):
            out.append((brand, pid, field, ratio, snippet))
    return out
