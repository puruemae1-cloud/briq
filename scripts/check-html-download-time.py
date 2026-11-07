#!/usr/bin/env python3
"""Fail when key HTML pages are too slow for Naver Yeti.

Naver Search Advisor "웹 페이지 다운로드 소요 시간" flags pages that take too
long to download (hard failure around 60s; we fail earlier so crawl stays useful).
"""

from __future__ import annotations

import os
import sys
import time
import urllib.request

SITE = os.environ.get("SITE", "https://www.briq.kr").rstrip("/")
UA = "Mozilla/5.0 (compatible; Yeti/1.1; +https://naver.me/spd)"

# Warm-hit budgets (seconds). Cold catalogue parse is covered by a second pass.
BUDGETS = {
    "/": 2.0,
    "/shop": 2.5,
    "/brands": 2.0,
}

# Sample PDP — must stay well under Naver's 60s cutoff after QA-SSR removal.
PRODUCT_PATH = "/product/nq-wild-one-skeleton-titanium-limited-edition"
PRODUCT_BUDGET = 3.0


def timed_fetch(path: str) -> tuple[int, float, str]:
    req = urllib.request.Request(
        f"{SITE}{path}",
        headers={"User-Agent": UA, "Accept-Encoding": "identity"},
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=90) as res:
        body = res.read()
        cache = res.headers.get("x-vercel-cache", "")
    return len(body), time.perf_counter() - t0, cache


def main() -> int:
    errors: list[str] = []

    # Prime edge/origin once, then measure.
    for path in list(BUDGETS) + [PRODUCT_PATH]:
        try:
            timed_fetch(path)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{path}: warm fetch failed ({exc})")

    for path, budget in BUDGETS.items():
        try:
            size, elapsed, cache = timed_fetch(path)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{path}: fetch failed ({exc})")
            continue
        status = "ok" if elapsed <= budget else "SLOW"
        print(
            f"{status}: {path} {elapsed:.2f}s "
            f"budget={budget:.1f}s size={size:,} cache={cache or '-'}"
        )
        if elapsed > budget:
            errors.append(
                f"{path}: {elapsed:.2f}s exceeds {budget:.1f}s "
                "(edge-cache shop/product; keep PDP free of Blob listQa SSR)"
            )

    try:
        size, elapsed, cache = timed_fetch(PRODUCT_PATH)
        status = "ok" if elapsed <= PRODUCT_BUDGET else "SLOW"
        print(
            f"{status}: {PRODUCT_PATH} {elapsed:.2f}s "
            f"budget={PRODUCT_BUDGET:.1f}s size={size:,} cache={cache or '-'}"
        )
        if elapsed > PRODUCT_BUDGET:
            errors.append(
                f"{PRODUCT_PATH}: {elapsed:.2f}s exceeds {PRODUCT_BUDGET:.1f}s"
            )
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{PRODUCT_PATH}: fetch failed ({exc})")

    if errors:
        print("html download time check failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print("ok: key HTML pages within Naver download-time budgets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
