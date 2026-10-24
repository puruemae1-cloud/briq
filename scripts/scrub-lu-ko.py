#!/usr/bin/env python3
"""Re-translate any remaining English LU PDP strings and rebuild both LU catalogues."""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE_PATH = ROOT / "src/data/lu/lu-translate-cache.json"
RAW_PATHS = [
    ROOT / "src/data/lu/lu-pdp-raw.json",
    ROOT / "src/data/lu/lu-lifestyle-pdp-raw.json",
]


class ListHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.paras: list[str] = []
        self.bullets: list[str] = []
        self._buf: list[str] = []
        self._in_li = False
        self._in_p = False

    def handle_starttag(self, tag, attrs):
        if tag == "li":
            self._in_li = True
            self._buf = []
        elif tag == "p":
            self._in_p = True
            self._buf = []
        elif tag in ("br", "hr") and (self._in_li or self._in_p):
            self._buf.append(" ")

    def handle_endtag(self, tag):
        if tag == "li" and self._in_li:
            text = re.sub(r"\s+", " ", "".join(self._buf)).strip()
            if text:
                self.bullets.append(text)
            self._in_li = False
        elif tag == "p" and self._in_p:
            text = re.sub(r"\s+", " ", "".join(self._buf)).strip()
            if text:
                self.paras.append(text)
            self._in_p = False

    def handle_data(self, data):
        if self._in_li or self._in_p:
            self._buf.append(data)


def parse_body(html: str) -> list[str]:
    p = ListHTMLParser()
    try:
        p.feed(html or "")
    except Exception:
        pass
    return [*p.paras, *p.bullets]


def en_ratio(s: str) -> float:
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return 0.0
    latin = sum(1 for c in letters if ("A" <= c <= "Z") or ("a" <= c <= "z"))
    return latin / len(letters)


def needs_ko(s: str, cached: str | None) -> bool:
    s = (s or "").strip()
    if len(s) < 12:
        return False
    if not re.search(r"[A-Za-z]{4,}", s):
        return False
    if en_ratio(s) < 0.45:
        return False
    if cached and en_ratio(cached) < 0.35 and any("\uac00" <= c <= "\ud7a3" for c in cached):
        return False
    return True


def polish(text: str) -> str:
    out = text
    for a, b in [
        ("런던 언더커버", "런던언더커버"),
        ("토요 스틸", "토요 스틸"),
        ("툴 박스", "툴박스"),
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
    with urllib.request.urlopen(req, timeout=35) as r:
        data = json.loads(r.read().decode())
    return "".join(part[0] for part in data[0] if part and part[0])


def collect_from_raw() -> set[str]:
    out: set[str] = set()
    for path in RAW_PATHS:
        if not path.exists():
            continue
        raw = json.loads(path.read_text())
        for p in raw.values():
            for piece in parse_body(p.get("body_html") or ""):
                out.add(piece.strip())
            title = re.sub(r"^London Undercover\s+", "", p.get("title") or "", flags=re.I).strip()
            if title:
                out.add(title)
            # also full stripped body as one blob if paragraphs missed
            plain = re.sub(r"<[^>]+>", " ", p.get("body_html") or "")
            plain = re.sub(r"\s+", " ", plain).strip()
            if plain:
                out.add(plain)
    return out


def collect_from_catalogs() -> set[str]:
    out: set[str] = set()
    for path in [
        ROOT / "src/data/lu/lu-catalog.ts",
        ROOT / "src/data/lu/lu-lifestyle-catalog.ts",
    ]:
        if not path.exists():
            continue
        text = path.read_text()
        for key in ("descriptionKo", "bodyKo", "titleKo", "nameKo", "valueKo"):
            for m in re.finditer(rf'{key}: "((?:\\.|[^"\\])*)"', text):
                try:
                    s = json.loads(f'"{m.group(1)}"')
                except Exception:
                    s = m.group(1)
                out.add(s)
        for m in re.finditer(r'featuresKo: (\[[^\]]*\]),', text):
            try:
                arr = json.loads(m.group(1))
                for s in arr:
                    if isinstance(s, str):
                        out.add(s)
            except Exception:
                pass
    return out


def main() -> None:
    cache: dict[str, str] = {}
    if CACHE_PATH.exists():
        cache = json.loads(CACHE_PATH.read_text())

    strings = collect_from_raw() | collect_from_catalogs()
    todo = sorted({s for s in strings if needs_ko(s, cache.get(s))}, key=len, reverse=True)
    print(f"candidates={len(strings)} todo={len(todo)} cache={len(cache)}")

    done = 0
    for s in todo:
        try:
            ko = polish(gtx(s))
        except Exception as e:
            print("FAIL", s[:60], e)
            time.sleep(1.0)
            continue
        if ko and en_ratio(ko) < 0.5:
            cache[s] = ko
            done += 1
            if done <= 12 or done % 30 == 0:
                print(f"[{done}/{len(todo)}] {s[:70]} => {ko[:70]}")
        if done % 20 == 0:
            CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n")
            time.sleep(0.12)
        else:
            time.sleep(0.05)

    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote cache entries={len(cache)} new={done}")


if __name__ == "__main__":
    main()
