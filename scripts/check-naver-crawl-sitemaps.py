#!/usr/bin/env python3
"""Guard Naver crawl-friendly sitemap setup.

Fails when:
- /sitemap.xml is configured as a 3xx redirect (Naver drops redirected sitemaps)
- sitemap.ts lists query-string shop URLs (wastes Yeti budget)
- NAVER_PRODUCT_CAP is below the current daily "완료" band
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NEXT_CONFIG = ROOT / "next.config.ts"
SITEMAP_TS = ROOT / "src" / "app" / "sitemap.ts"
CHUNKS = ROOT / "src" / "lib" / "sitemap-chunks.ts"

# Recent Naver "완료" is ~150–200/day; keep priority sitemap at least that large.
MIN_NAVER_PRODUCT_CAP = 200


def main() -> int:
    errors: list[str] = []

    next_cfg = NEXT_CONFIG.read_text(encoding="utf-8")
    if re.search(
        r"redirects\s*\(\s*\)[\s\S]*?source:\s*[\"']/sitemap\.xml[\"']",
        next_cfg,
    ):
        errors.append(
            "next.config.ts redirects /sitemap.xml — use rewrites() so Yeti gets 200"
        )
    if not re.search(
        r"rewrites\s*\(\s*\)[\s\S]*?source:\s*[\"']/sitemap\.xml[\"']",
        next_cfg,
    ):
        errors.append("next.config.ts missing rewrite /sitemap.xml → /sitemap-index.xml")

    sitemap_ts = SITEMAP_TS.read_text(encoding="utf-8")
    if re.search(r"/shop\?[^\"'\s]+", sitemap_ts):
        errors.append(
            "src/app/sitemap.ts lists /shop?… URLs — drop query variants from the sitemap"
        )

    chunks = CHUNKS.read_text(encoding="utf-8")
    m = re.search(r"NAVER_PRODUCT_CAP\s*=\s*(\d+)", chunks)
    if not m:
        errors.append("NAVER_PRODUCT_CAP missing from src/lib/sitemap-chunks.ts")
    else:
        cap = int(m.group(1))
        if cap < MIN_NAVER_PRODUCT_CAP:
            errors.append(
                f"NAVER_PRODUCT_CAP={cap} < {MIN_NAVER_PRODUCT_CAP} "
                "(raise to match Naver daily 완료 volume)"
            )

    if errors:
        print("naver crawl sitemap check failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(
        "ok: sitemap.xml rewrite, no shop query URLs, "
        f"NAVER_PRODUCT_CAP>={MIN_NAVER_PRODUCT_CAP}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
