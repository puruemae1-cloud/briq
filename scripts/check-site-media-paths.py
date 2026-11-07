#!/usr/bin/env python3
"""Fail if SEO/meta still points crawlers at broken www.briq.kr media paths.

Vercel does not ship /banners or /products — those live on the product-images
tag. Relative OG URLs become https://www.briq.kr/banners/... and Naver marks
them as 접근 불가 (4xx). Prefer mediaUrl() absolute CDN URLs, plus next.config
redirects as a safety net.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Relative site-root media in metadata / openGraph / twitter blocks.
BAD = re.compile(
    r"""(?:url|images)\s*[:=]\s*(?:\[\s*)?["']/((?:banners|products)/[^"']+)["']""",
    re.I,
)

SCAN = [
    ROOT / "src/lib/seo-metadata.ts",
    ROOT / "src/app/layout.tsx",
]


def main() -> int:
    hits: list[str] = []
    for path in SCAN:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for i, line in enumerate(text.splitlines(), 1):
            if "mediaUrl(" in line:
                continue
            m = BAD.search(line)
            if m:
                hits.append(f"{path.relative_to(ROOT)}:{i}: /{m.group(1)}")
    if hits:
        print("Relative /banners|/products URLs in SEO metadata:", file=sys.stderr)
        for h in hits:
            print(f"  {h}", file=sys.stderr)
        print(
            "\nUse mediaUrl('/banners/...') so crawlers hit the CDN, "
            "not www.briq.kr (404).",
            file=sys.stderr,
        )
        return 1
    print("ok: SEO metadata has no bare /banners|/products site paths")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
