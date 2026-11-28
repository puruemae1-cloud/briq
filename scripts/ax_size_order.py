"""Arc'teryx size ordering — match official site (inseam S→R→T, then numeric)."""
from __future__ import annotations

import re

_LETTER_ORDER = {
    "XXS": 0,
    "XS": 1,
    "S": 2,
    "M": 3,
    "L": 4,
    "XL": 5,
    "XXL": 6,
    "2XL": 6,
    "XXXL": 7,
    "3XL": 7,
    "4XL": 8,
    "OS": 9,
    "ONE SIZE": 9,
}

# Pant / short waist + inseam: 00S, 0-R, 30 R, 32S, …
_INSEAM_RE = re.compile(
    r"^(\d+(?:\.\d+)?)\s*[- ]?\s*([SRT])$",
    re.IGNORECASE,
)


def _waist_rank(raw: str) -> float:
    """00 before 0 before 2 … (float('00')==float('0') so special-case)."""
    s = raw.strip()
    if s == "00":
        return -1.0
    try:
        return float(s)
    except ValueError:
        return 9999.0


def ax_size_sort_key(size: str) -> tuple:
    s = (size or "").strip()
    if not s:
        return (9, 0, 0, "")

    m = _INSEAM_RE.match(s)
    if m:
        waist, length = m.group(1), m.group(2).upper()
        return (0, "SRT".index(length), _waist_rank(waist), s)

    letter = _LETTER_ORDER.get(s.upper())
    if letter is not None:
        return (1, letter, 0, s)

    try:
        return (2, float(s), 0, s)
    except ValueError:
        return (3, 0, 0, s.lower())


def sort_ax_sizes(sizes: list[str]) -> list[str]:
    """Stable unique sort in Arc'teryx official display order."""
    seen: set[str] = set()
    uniq: list[str] = []
    for s in sizes:
        if s is None:
            continue
        t = str(s).strip()
        if not t or t in seen:
            continue
        seen.add(t)
        uniq.append(t)
    return sorted(uniq, key=ax_size_sort_key)
