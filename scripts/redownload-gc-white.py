#!/usr/bin/env python3
"""Re-download Gucci pale colourway PDP images as official DarkGray studio crops.

White / ivory / cream / light garments must stay as gucci.com intends
(DarkGray_Center JPEG). Never run greymat/rembg on these — it crushes pale
subjects the same way Paul Smith whites were ruined (see ps_pale_colour.py).

Scans all src/data/gc/*catalog-raw.json rows, force-overwrites
public/products/gc-pdp/<CODE>/*.jpg from the CDN.
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
sys.path.insert(0, str(ROOT / "scripts"))

from gc_pale_colour import is_pale_gc_row, iter_gc_raw_products, pale_gc_codes  # noqa: E402

IMG_ROOT = ROOT / "public/products/gc-pdp"
GC_DATA = ROOT / "src/data/gc"
WORKERS = 10


def to_darkgray(url: str) -> str:
    u = url or ""
    if "media.gucci.com/style/" not in u:
        return u
    return re.sub(
        r"/style/[^/]+/",
        "/style/DarkGray_Center_0_0_1200x1200/",
        u,
        count=1,
    )


def download(s: cffi_requests.Session, url: str, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    candidates = [url]
    if "1200x1200" in url:
        candidates.append(url.replace("1200x1200", "2400x2400"))
    for candidate in candidates:
        for attempt in range(4):
            try:
                r = s.get(
                    candidate,
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
                time.sleep(0.5 * (attempt + 1))
    return False


def one(prod: dict) -> tuple[str, int, int, str]:
    s = cffi_requests.Session()
    code = str(prod.get("productCode") or "").strip()
    if not code:
        return "", 0, 1, "no-code"
    remotes = [to_darkgray(u) for u in (prod.get("images") or []) if u]
    if not remotes:
        return code, 0, 1, "no-urls"
    ok = fail = 0
    new_remotes: list[str] = []
    for i, url in enumerate(remotes[:12], start=1):
        new_remotes.append(url)
        dest = IMG_ROOT / code / f"{i}.jpg"
        if download(s, url, dest):
            ok += 1
        else:
            fail += 1
    # Keep raw row remotes on DarkGray for future builds / hover keys
    prod["images"] = new_remotes
    if new_remotes:
        prod["image"] = new_remotes[0]
    if prod.get("plpHoverUrl"):
        prod["plpHoverUrl"] = to_darkgray(str(prod["plpHoverUrl"]))
    # local paths
    if ok:
        prod["localImages"] = [f"/products/gc-pdp/{code}/{i}.jpg" for i in range(1, ok + 1)]
        prod["localImage"] = prod["localImages"][0]
        if ok >= 2:
            prod["localHover"] = prod["localImages"][1]
    return code, ok, fail, "ok" if ok else "empty"


def main() -> None:
    rows = [r for r in iter_gc_raw_products() if is_pale_gc_row(r)]
    # Prefer rows that still have remote image URLs
    with_urls = [r for r in rows if r.get("images")]
    codes = pale_gc_codes()
    print(
        f"GC pale redownload products={len(with_urls)} "
        f"(rows={len(rows)} codes={len(codes)}) workers={WORKERS}",
        flush=True,
    )
    total_ok = total_fail = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(one, dict(r)) for r in with_urls]
        done = 0
        for fut in as_completed(futs):
            code, ok, fail, status = fut.result()
            total_ok += ok
            total_fail += fail
            done += 1
            if done <= 8 or done % 40 == 0 or done == len(with_urls):
                print(
                    f"{done}/{len(with_urls)} {code} ok={ok} fail={fail} {status} "
                    f"(total_ok={total_ok} fail={total_fail})",
                    flush=True,
                )
            time.sleep(0.01)

    # Persist DarkGray URL rewrites into each raw file that contains pale rows
    rewritten = 0
    for path in sorted(GC_DATA.glob("*catalog-raw.json")):
        try:
            data = json.loads(path.read_text())
        except Exception:
            continue
        products = data.get("products") if isinstance(data, dict) else None
        if not isinstance(products, list):
            continue
        dirty = False
        for prod in products:
            if not isinstance(prod, dict) or not is_pale_gc_row(prod):
                continue
            imgs = prod.get("images") or []
            if not imgs:
                continue
            new_imgs = [to_darkgray(u) for u in imgs]
            if new_imgs != imgs:
                prod["images"] = new_imgs
                prod["image"] = new_imgs[0]
                dirty = True
                rewritten += 1
            if prod.get("plpHoverUrl"):
                dg = to_darkgray(str(prod["plpHoverUrl"]))
                if dg != prod["plpHoverUrl"]:
                    prod["plpHoverUrl"] = dg
                    dirty = True
        if dirty:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
            print(f"updated remotes → {path.name}", flush=True)

    print(
        f"done products={len(with_urls)} imgs_ok={total_ok} fail={total_fail} "
        f"url_rewrites={rewritten} pale_codes={len(codes)}",
        flush=True,
    )


if __name__ == "__main__":
    main()
