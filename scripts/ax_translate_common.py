"""Shared EN→KO lookup for Arc'teryx catalogue builds."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CACHE = ROOT / "src/data/ax/ax-translate-cache.json"


def normalize_en(text: str | None) -> str:
    if not text:
        return ""
    s = str(text).strip()
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"</p\s*>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("\u2019", "'").replace("\u2018", "'")
    s = s.replace("\u201c", '"').replace("\u201d", '"')
    s = s.replace("\u2014", "—").replace("\u2013", "–")
    s = re.sub(r"&nbsp;", " ", s)
    s = re.sub(r"&amp;", "&", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def load_ax_translate_cache(path: Path | None = None) -> dict[str, str]:
    p = path or DEFAULT_CACHE
    if not p.is_file():
        return {}
    raw = json.loads(p.read_text())
    # Keys on disk may use curly quotes; normalize so PDP lookups match.
    out: dict[str, str] = {}
    for k, v in raw.items():
        nk = normalize_en(k)
        if nk:
            out[nk] = v
    return out


def make_translate_fn(cache: dict[str, str]):
    """Return ``t(en)`` with exact + prefix cache lookup."""
    keys = list(cache.keys())
    long_keys = [k for k in keys if len(k) >= 40]
    long_keys.sort(key=len, reverse=True)
    buckets: dict[str, list[str]] = {}
    for k in long_keys:
        buckets.setdefault(k[:32], []).append(k)

    @lru_cache(maxsize=65536)
    def t(text: str | None) -> str:
        s = normalize_en(text)
        if not s:
            return ""
        hit = cache.get(s)
        if hit:
            return hit
        if len(s) >= 24:
            bucket = buckets.get(s[:32], ())
            extended = [k for k in bucket if k.startswith(s) and len(k) > len(s)]
            if extended:
                return cache[max(extended, key=len)]
            prefixes = [k for k in bucket if s.startswith(k) and len(k) >= 20]
            if prefixes:
                return cache[max(prefixes, key=len)]
        return s

    return t
