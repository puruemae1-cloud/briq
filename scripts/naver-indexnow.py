#!/usr/bin/env python3
"""Ask Naver to collect Briq product pages via IndexNow.

The key file already lives at the site root. One request holds at most
10,000 URLs. Stops when Naver asks us to slow down.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HOST = "www.briq.kr"
SITE = f"https://{HOST}"
ENDPOINT = "https://searchadvisor.naver.com/indexnow"
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
BATCH = 10000
ROOT = Path(__file__).resolve().parents[1]


def indexnow_key() -> str:
    matches = sorted(ROOT.glob("public/" + "[0-9a-f]" * 32 + ".txt"))
    if len(matches) != 1:
        raise SystemExit(f"expected one IndexNow key file, found {len(matches)}")
    key = matches[0].read_text().strip()
    if matches[0].name != f"{key}.txt":
        raise SystemExit("IndexNow key file name does not match its contents")
    return key


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "briq-indexnow"})
    with urllib.request.urlopen(req, timeout=90) as res:
        return res.read()


def locs(xml: bytes) -> list[str]:
    root = ET.fromstring(xml)
    return [node.text.strip() for node in root.findall(".//sm:loc", NS) if node.text]


def product_urls() -> list[str]:
    index = locs(fetch(f"{SITE}/sitemap-index.xml"))
    urls: list[str] = []
    for loc in index:
        if loc.rstrip("/").endswith("/sitemap/0.xml"):
            continue
        urls.extend(u for u in locs(fetch(loc)) if "/product/" in u)
    return list(dict.fromkeys(urls))


def submit(key: str, batch: list[str]) -> int:
    body = json.dumps(
        {
            "host": HOST,
            "key": key,
            "keyLocation": f"{SITE}/{key}.txt",
            "urlList": batch,
        }
    ).encode()
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "briq-indexnow",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as res:
            print(res.status, "accepted", len(batch), flush=True)
            return res.status
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", "replace")[:300]
        print(err.code, detail, "batch", len(batch), flush=True)
        return err.code


def main() -> None:
    key = indexnow_key()
    urls = product_urls()
    print("products", len(urls), flush=True)
    if not urls:
        raise SystemExit(1)
    for start in range(0, len(urls), BATCH):
        code = submit(key, urls[start : start + BATCH])
        if code == 429:
            raise SystemExit(2)
        if code not in (200, 202):
            raise SystemExit(1)
        if start + BATCH < len(urls):
            time.sleep(8)
    print("done", len(urls), flush=True)


if __name__ == "__main__":
    main()
