#!/usr/bin/env python3
"""Fail if src/ ships <img> / BannerImage / ProductImage with empty alt.

Naver Search Advisor treats missing or empty alt as SEO errors
(Alt 속성 누락). Decorative intent must still use a short non-empty alt.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

# Explicit empty-string alt in JSX / TSX.
EMPTY_ALT = re.compile(
    r"""\balt\s*=\s*(?:""|'')"""
    r"""|\balt\s*=\s*\{\s*(?:""|'')\s*\}""",
)

# BannerImage default that used to coerce empty alts.
BAD_DEFAULT = re.compile(r"""alt\s*=\s*""\s*,""")


def main() -> int:
    hits: list[str] = []
    for path in sorted(SRC.rglob("*")):
        if path.suffix not in {".ts", ".tsx", ".js", ".jsx"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for i, line in enumerate(text.splitlines(), 1):
            if EMPTY_ALT.search(line) or BAD_DEFAULT.search(line):
                rel = path.relative_to(ROOT)
                hits.append(f"{rel}:{i}: {line.strip()}")
    if hits:
        print("Empty img alt text found (Naver SEO / a11y):", file=sys.stderr)
        for h in hits:
            print(f"  {h}", file=sys.stderr)
        print(
            "\nUse a short descriptive alt (see src/lib/image-alt.ts).",
            file=sys.stderr,
        )
        return 1
    print("ok: no empty alt= in src/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
