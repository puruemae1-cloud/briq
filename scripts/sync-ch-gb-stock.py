#!/usr/bin/env python3
"""Mark Chanel SKUs sold-out on Briq when GB PDPs say they are sold out.

Beauty (makeup / skincare / fragrance): schema.org OutOfStock or
"This product is sold out."
Fashion / jewellery / watches: only the explicit sold-out banner, because
chanel.com often omits schema stock for boutique special-order pieces.

  python3 scripts/sync-ch-gb-stock.py
  python3 scripts/sync-ch-gb-stock.py --skip-kinds skincare,makeup,fragrance
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from curl_cffi import requests as cffi_requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from ch_hybris_details import parse_pdp_in_stock  # noqa: E402

RAW_FILES = [
    ROOT / "src/data/ch/ch-skincare-catalog-raw.json",
    ROOT / "src/data/ch/ch-makeup-catalog-raw.json",
    ROOT / "src/data/ch/ch-fragrance-catalog-raw.json",
    ROOT / "src/data/ch/ch-rtw-catalog-raw.json",
    ROOT / "src/data/ch/ch-handbags-catalog-raw.json",
    ROOT / "src/data/ch/ch-slg-catalog-raw.json",
    ROOT / "src/data/ch/ch-shoes-catalog-raw.json",
    ROOT / "src/data/ch/ch-jewellery-catalog-raw.json",
    ROOT / "src/data/ch/ch-high-jewellery-catalog-raw.json",
    ROOT / "src/data/ch/ch-fine-jewellery-catalog-raw.json",
    ROOT / "src/data/ch/ch-sunglasses-catalog-raw.json",
    ROOT / "src/data/ch/ch-other-acc-catalog-raw.json",
    ROOT / "src/data/ch/ch-watches-catalog-raw.json",
]

BEAUTY_KINDS = {"skincare", "makeup", "fragrance"}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.8",
}

_tls = threading.local()


def log(msg: str) -> None:
    print(msg, flush=True)


def session() -> cffi_requests.Session:
    s = getattr(_tls, "session", None)
    if s is None:
        s = cffi_requests.Session()
        _tls.session = s
    return s


def to_gb_cn(url: str) -> str:
    u = (url or "").replace("://www.chanel.com/", "://www.chanel.cn/")
    u = re.sub(r"/(kr|us|fr)/", "/gb/", u, count=1)
    return u


def fetch(url: str) -> str:
    try:
        r = session().get(
            url, impersonate="chrome124", timeout=50, headers=HEADERS
        )
        if r.status_code == 200:
            return r.text or ""
    except Exception as e:
        log(f"  fetch error {e}")
    return ""


def fashion_sold_out(html: str) -> bool:
    """True only for the explicit GB sold-out banner, not boutique-availability."""
    if re.search(r"This product is sold out\.?", html or "", flags=re.I):
        return True
    return False


def apply_stock(row: dict, in_stock: bool) -> None:
    row["inStock"] = in_stock
    sizes = row.get("sizes")
    if not isinstance(sizes, list):
        return
    new = []
    for sz in sizes:
        if isinstance(sz, dict):
            sz = dict(sz)
            sz["inStock"] = in_stock
            new.append(sz)
        else:
            new.append(sz)
    row["sizes"] = new


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-kinds", default="")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    skip = {k.strip() for k in args.skip_kinds.split(",") if k.strip()}

    sold = 0
    checked = 0
    for path in RAW_FILES:
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        products = data.get("products") or []
        if not products:
            continue
        kind = str(products[0].get("kind") or path.name)
        if any(k in kind or k in path.name for k in skip):
            log(f"skip {path.name}")
            continue
        is_beauty = any(k in kind or k in path.name for k in BEAUTY_KINDS)
        log(f"{path.name}: {len(products)} stock checks (beauty={is_beauty})")

        def work(i: int) -> tuple[int, bool | None]:
            row = products[i]
            url = row.get("url") or ""
            if not url:
                return i, None
            html = fetch(to_gb_cn(url))
            if not html:
                return i, None
            if is_beauty:
                return i, parse_pdp_in_stock(html)
            if fashion_sold_out(html):
                return i, False
            return i, True

        results: list[tuple[int, bool | None]] = []
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            futs = [pool.submit(work, i) for i in range(len(products))]
            for n, fut in enumerate(as_completed(futs), start=1):
                results.append(fut.result())
                if n % 50 == 0:
                    log(f"  {path.name} {n}/{len(products)}")
        for i, flag in results:
            if flag is None:
                continue
            checked += 1
            apply_stock(products[i], flag)
            if not flag:
                sold += 1
        data["products"] = products
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        time.sleep(0.2)
    log(f"done checked={checked} sold_out={sold}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
