#!/usr/bin/env python3
"""Fill missing EN→KO strings for Arc'teryx PDP copy into ax-translate-cache.json."""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE_PATH = ROOT / "src/data/ax/ax-translate-cache.json"
PDP_PATHS = [
    ROOT / "src/data/ax/ax-apparel-pdp-cache.json",
    ROOT / "src/data/ax/ax-outlet-pdp-cache.json",
    ROOT / "src/data/ax/ax-gear-pdp-cache.json",
    ROOT / "src/data/ax/ax-footwear-pdp-cache.json",
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
}


def has_latin(s: str) -> bool:
    return bool(re.search(r"[A-Za-z]{3,}", s or ""))


def has_hangul(s: str) -> bool:
    return any("\uac00" <= c <= "\ud7a3" for c in (s or ""))


def strip_html(text: str) -> str:
    s = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", s).strip()


def collect_strings() -> set[str]:
    out: set[str] = set()
    for path in PDP_PATHS:
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        for rec in data.values() if isinstance(data, dict) else []:
            if not isinstance(rec, dict) or rec.get("error"):
                continue
            for key in ("title", "tagline", "description", "weight", "fit", "category", "subCategory"):
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
    return {s for s in out if s}


def polish_ko(text: str) -> str:
    out = text
    for a, b in [
        ("아크테릭스", "아크테릭스"),
        ("고어텍스", "GORE-TEX"),
        ("프리마로프트", "PrimaLoft"),
        ("후드티", "후디"),
        ("후드 티", "후디"),
        ("  ", " "),
    ]:
        out = out.replace(a, b)
    return out.strip()


def gtx(text: str) -> str:
    q = urllib.parse.quote(text[:4500])
    url = (
        "https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl=en&tl=ko&dt=t&q={q}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode())
    return "".join(part[0] for part in data[0] if part and part[0])


def needs_translate(src: str, cached: str | None) -> bool:
    if src in SKIP_EXACT:
        return False
    if not has_latin(src):
        return False
    if len(src) < 3:
        return False
    # Skip pure colourway / SKU-ish tokens
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 \-_/]{0,40}", src) and len(src.split()) <= 3 and len(src) < 28:
        if not re.search(r"\b(the|and|for|with|from|made|designed)\b", src, re.I):
            return False
    if cached and has_hangul(cached) and cached != src:
        return False
    return True


def main() -> None:
    cache: dict[str, str] = {}
    if CACHE_PATH.exists():
        cache = json.loads(CACHE_PATH.read_text())

    strings = sorted(collect_strings())
    todo = [s for s in strings if needs_translate(s, cache.get(s))]
    print(f"strings={len(strings)} todo={len(todo)} cached={len(cache)}")

    done = 0
    for s in todo:
        try:
            ko = polish_ko(gtx(s))
        except Exception as e:
            print(f"FAIL {s[:60]!r}: {e}")
            time.sleep(1.2)
            continue
        if ko:
            cache[s] = ko
            done += 1
            if done <= 8 or done % 25 == 0:
                print(f"[{done}/{len(todo)}] {s[:70]} => {ko[:70]}")
        if done % 20 == 0:
            CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n")
            time.sleep(0.15)
        else:
            time.sleep(0.05)

    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {CACHE_PATH} entries={len(cache)} new={done}")


if __name__ == "__main__":
    main()
