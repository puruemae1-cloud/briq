#!/usr/bin/env python3
"""Re-download Gucci women's RTW images as official DarkGray studio crops.

White_Center + whitening made RTW look unlike gucci.com (grey studio / on-model).
This pass rewrites remote URLs to DarkGray_Center JPEG and overwrites local files
without studio whitening.
"""
from __future__ import annotations

import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from curl_cffi import requests as cffi_requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

RAW = ROOT / "src/data/gc/gc-rtw-catalog-raw.json"
IMG_ROOT = ROOT / "public/products/gc-pdp"
WORKERS = 10


def to_darkgray(url: str) -> str:
    u = url or ""
    if "media.gucci.com/style/" not in u:
        return u
    # Prefer sharp DarkGray centre crop matching gucci.com PDP/PLP
    u = re.sub(
        r"/style/[^/]+/",
        "/style/DarkGray_Center_0_0_1200x1200/",
        u,
        count=1,
    )
    return u


def download(s: cffi_requests.Session, url: str, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(4):
        try:
            r = s.get(
                url,
                headers={
                    "Accept": "image/jpeg,image/*,*/*",
                    "Referer": "https://www.gucci.com/",
                },
                impersonate="chrome124",
                timeout=90,
            )
            if r.status_code != 200 or len(r.content) < 1500:
                raise RuntimeError(f"bad {r.status_code} {len(r.content)}")
            ctype = (r.headers.get("content-type") or "").lower()
            if "avif" in ctype or r.content[:4] == b"\x00\x00\x00\x1c":
                raise RuntimeError("got avif instead of jpeg")
            if r.content[:3] != b"\xff\xd8\xff":
                raise RuntimeError(f"not jpeg {r.content[:12]!r}")
            dest.write_bytes(r.content)
            return True
        except Exception:
            time.sleep(0.6 * (attempt + 1))
    return False


def one(prod: dict) -> tuple[str, int, int]:
    s = cffi_requests.Session()
    code = prod["productCode"]
    remotes = prod.get("images") or []
    ok = fail = 0
    new_remotes: list[str] = []
    for i, url in enumerate(remotes[:12], start=1):
        dg = to_darkgray(url)
        new_remotes.append(dg)
        dest = IMG_ROOT / code / f"{i}.jpg"
        if download(s, dg, dest):
            ok += 1
        else:
            fail += 1
    # Update raw row remotes to DarkGray for future builds / hover keys
    prod["images"] = new_remotes
    if new_remotes:
        prod["image"] = new_remotes[0]
    if prod.get("plpHoverUrl"):
        prod["plpHoverUrl"] = to_darkgray(prod["plpHoverUrl"])
    return code, ok, fail


def main() -> None:
    data = json.loads(RAW.read_text())
    products = data.get("products") or []
    print(f"redownloading {len(products)} RTW colourways as DarkGray…", flush=True)
    total_ok = total_fail = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(one, p) for p in products]
        done = 0
        for fut in as_completed(futs):
            code, ok, fail = fut.result()
            total_ok += ok
            total_fail += fail
            done += 1
            if done % 40 == 0 or done == len(products):
                print(
                    f"{done}/{len(products)} ok_imgs={total_ok} fail={total_fail}",
                    flush=True,
                )
    RAW.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"done ok={total_ok} fail={total_fail} wrote {RAW}", flush=True)


if __name__ == "__main__":
    main()
