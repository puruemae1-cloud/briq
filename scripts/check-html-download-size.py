#!/usr/bin/env python3
"""Fail when key HTML pages exceed Naver-friendly uncompressed sizes.

Naver Search Advisor "웹 페이지 다운로드 크기" tracks decoded HTML bytes.
Keep /, /shop, and a sample PDP under the budgets below (4MB is the hard
error threshold; we fail earlier so crawl budget stays useful).
"""

from __future__ import annotations

import os
import sys
import urllib.request

SITE = os.environ.get("SITE", "https://www.briq.kr").rstrip("/")
UA = "Mozilla/5.0 (compatible; briq-html-size-guard/1.0; +https://www.briq.kr)"

# Uncompressed HTML budgets (bytes). Tuned after slim card DTOs + shop page-1 SSR.
BUDGETS = {
    "/": 520_000,
    "/shop": 320_000,
    "/brands": 200_000,
}


def fetch(path: str) -> bytes:
    req = urllib.request.Request(
        f"{SITE}{path}",
        headers={"User-Agent": UA, "Accept-Encoding": "identity"},
    )
    with urllib.request.urlopen(req, timeout=90) as res:
        return res.read()


def main() -> int:
    errors: list[str] = []
    for path, budget in BUDGETS.items():
        try:
            body = fetch(path)
        except Exception as exc:  # noqa: BLE001 — surface any fetch failure
            errors.append(f"{path}: fetch failed ({exc})")
            continue
        size = len(body)
        kb = size / 1024
        budget_kb = budget / 1024
        status = "ok" if size <= budget else "OVER"
        print(f"{status}: {path} {size:,} bytes ({kb:.1f} KB) budget={budget_kb:.0f} KB")
        if size > budget:
            errors.append(
                f"{path}: {size:,} bytes exceeds {budget:,} "
                "(slim card DTOs / avoid SSR page-2 shop grids)"
            )

    if errors:
        print("html download size check failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print("ok: key HTML pages within Naver download-size budgets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
