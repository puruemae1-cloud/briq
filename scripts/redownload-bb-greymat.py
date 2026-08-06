#!/usr/bin/env python3
"""Re-download Burberry PDP images from official Scene7 (no greymat/rembg).

Prior greymatting flattened on-model lifestyle shots onto solid grey mats.
Restore pristine Burberry.com crops.
"""
from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from curl_cffi import requests as cffi_requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "src/data/bb/bb-catalog-raw.json"
IMG_ROOT = ROOT / "public/products/bb-pdp"
WORKERS = 16


def remote_url(base: str) -> str:
    base = (base or "").split("?")[0]
    if not base:
        return ""
    # Match scrape-bb-women Scene7 preset used on burberry.com PLP/PDP.
    return f"{base}?$BBY_V2_SL_3x4$&wid=1200&hei=1600&fmt=jpg"


def download_one(product: dict) -> tuple[int, int]:
    s = cffi_requests.Session()
    pid = str(product.get("id") or "")
    ok = fail = 0
    for i, remote in enumerate((product.get("remoteImages") or [])[:12], start=1):
        url = remote_url(remote)
        if not url:
            fail += 1
            continue
        dest = IMG_ROOT / pid / f"{i}.jpg"
        dest.parent.mkdir(parents=True, exist_ok=True)
        got = False
        for attempt in range(3):
            try:
                r = s.get(
                    url,
                    headers={
                        "Accept": "image/jpeg,image/*,*/*",
                        "Referer": "https://uk.burberry.com/",
                    },
                    impersonate="chrome124",
                    timeout=90,
                )
                if r.status_code != 200 or len(r.content) < 1500:
                    raise RuntimeError(f"bad {r.status_code}")
                dest.write_bytes(r.content)
                ok += 1
                got = True
                break
            except Exception:
                time.sleep(0.4 * (attempt + 1))
        if not got:
            fail += 1
    return ok, fail


def main() -> None:
    products = json.loads(RAW.read_text()).get("products") or []
    print(
        f"BB official redownload products={len(products)} workers={WORKERS}",
        flush=True,
    )
    total_ok = total_fail = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(download_one, p) for p in products]
        done = 0
        for fut in as_completed(futs):
            ok, fail = fut.result()
            total_ok += ok
            total_fail += fail
            done += 1
            if done % 100 == 0 or done == len(products):
                print(
                    f"{done}/{len(products)} imgs_ok={total_ok} fail={total_fail}",
                    flush=True,
                )
    print(f"done ok={total_ok} fail={total_fail}", flush=True)


if __name__ == "__main__":
    main()
