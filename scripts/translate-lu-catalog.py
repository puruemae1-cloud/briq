#!/usr/bin/env python3
"""Translate London Undercover PDP copy EN→KO into lu-translate-cache.json."""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "src/data/lu/lu-pdp-raw.json"
CACHE_PATH = ROOT / "src/data/lu/lu-translate-cache.json"

SKIP = {"London Undercover", "GORE-TEX", "Whangee", "PET"}


def strip_html(text: str) -> str:
    s = re.sub(r"<[^>]+>", "\n", text or "")
    s = re.sub(r"&nbsp;", " ", s)
    s = re.sub(r"&amp;", "&", s)
    s = re.sub(r"&#39;|'", "'", s)
    s = re.sub(r"\n+", "\n", s)
    return re.sub(r"[ \t]+", " ", s).strip()


def collect() -> set[str]:
    raw = json.loads(RAW_PATH.read_text())
    out: set[str] = set()
    for p in raw.values():
        title = re.sub(r"^London Undercover\s+", "", p.get("title") or "", flags=re.I)
        if title:
            out.add(title)
        body = strip_html(p.get("body_html") or "")
        for part in re.split(r"[\n•]+", body):
            part = part.strip(" -•\t")
            if len(part) >= 3:
                out.add(part)
        for v in p.get("variants") or []:
            c = (v.get("option1") or v.get("title") or "").strip()
            if c:
                out.add(c)
        for t in (p.get("tags") or "").split(",") if isinstance(p.get("tags"), str) else (p.get("tags") or []):
            t = str(t).strip()
            if t and t not in ("Best Selling", "Eco", "Folding", "Lightweight", "Recycled Canopy", "Wooden handle"):
                out.add(t)
    return out


def polish(text: str) -> str:
    out = text
    for a, b in [
        ("런던 언더커버", "런던언더커버"),
        ("런던 언더 커버", "런던언더커버"),
        ("우산 산", "우산"),
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


def needs(src: str, cached: str | None) -> bool:
    if src in SKIP:
        return False
    if not re.search(r"[A-Za-z]{3,}", src):
        return False
    if cached and any("\uac00" <= c <= "\ud7a3" for c in cached) and cached != src:
        return False
    return True


def main() -> None:
    cache: dict[str, str] = {}
    if CACHE_PATH.exists():
        cache = json.loads(CACHE_PATH.read_text())
    strings = sorted(collect())
    todo = [s for s in strings if needs(s, cache.get(s))]
    print(f"strings={len(strings)} todo={len(todo)} cached={len(cache)}")
    done = 0
    for s in todo:
        try:
            ko = polish(gtx(s))
        except Exception as e:
            print("FAIL", s[:60], e)
            time.sleep(1)
            continue
        if ko:
            cache[s] = ko
            done += 1
            if done <= 10 or done % 20 == 0:
                print(f"[{done}/{len(todo)}] {s[:70]} => {ko[:70]}")
        if done % 15 == 0:
            CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n")
            time.sleep(0.12)
        else:
            time.sleep(0.05)
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {CACHE_PATH} entries={len(cache)} new={done}")


if __name__ == "__main__":
    main()
