#!/usr/bin/env python3
"""Refresh Chanel beauty PDP copy from chanel.com/kr + GB stock.

Fills Product Information accordion (설명 / 효과 / 핵심 성분 / 사용 방법 /
상품 필수 정보) in Korean, falling back to GB English + gtx.

  python3 scripts/enrich-ch-beauty-copy.py
  python3 scripts/enrich-ch-beauty-copy.py --kinds skincare,makeup
  python3 scripts/enrich-ch-beauty-copy.py --sku 102020
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import threading
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from curl_cffi import requests as cffi_requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from ch_hybris_details import (  # noqa: E402
    parse_kr_product_name,
    parse_pdp_in_stock,
    parse_product_accordion,
)

CACHE_PATH = ROOT / "src/data/ch/ch-translate-cache.json"
_KO: dict[str, str] = {}
_ko_lock = threading.Lock()

KIND_FILES = {
    "skincare": ROOT / "src/data/ch/ch-skincare-catalog-raw.json",
    "makeup": ROOT / "src/data/ch/ch-makeup-catalog-raw.json",
    "fragrance": ROOT / "src/data/ch/ch-fragrance-catalog-raw.json",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-GB;q=0.6",
}

_tls = threading.local()


def log(msg: str) -> None:
    print(msg, flush=True)


def load_ko() -> None:
    global _KO
    if CACHE_PATH.exists():
        try:
            _KO = json.loads(CACHE_PATH.read_text())
        except Exception:
            _KO = {}


def save_ko() -> None:
    CACHE_PATH.write_text(json.dumps(_KO, ensure_ascii=False, indent=2) + "\n")


def hangul_ratio(text: str) -> float:
    letters = [c for c in text if c.isalpha() or ("\uac00" <= c <= "\ud7a3")]
    if not letters:
        return 0.0
    han = sum(1 for c in letters if "\uac00" <= c <= "\ud7a3")
    return han / len(letters)


def looks_korean(text: str) -> bool:
    if not text:
        return False
    han = sum(1 for c in text if "\uac00" <= c <= "\ud7a3")
    return han >= 10 or hangul_ratio(text) >= 0.18


def looks_inci(text: str) -> bool:
    if (text or "").count("|") >= 2:
        return True
    letters = [c for c in text if c.isalpha()]
    if len(letters) < 20:
        return False
    upper = sum(1 for c in letters if c.isupper())
    return upper / len(letters) > 0.72


def gtx(text: str) -> str:
    q = urllib.parse.quote(text[:4500])
    url = (
        "https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl=en&tl=ko&dt=t&q={q}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=35) as r:
        data = json.loads(r.read().decode())
    return "".join(part[0] for part in data[0] if part and part[0])


def t(en: str) -> str:
    src = (en or "").strip()
    if not src:
        return ""
    if looks_korean(src) or looks_inci(src):
        return src
    with _ko_lock:
        cached = _KO.get(src)
    if cached and (looks_korean(cached) or cached != src or len(src) < 40):
        if cached != src or looks_korean(cached):
            return cached
    try:
        ko = gtx(src).strip() or src
    except Exception:
        ko = src
    with _ko_lock:
        _KO[src] = ko
    return ko


def session() -> cffi_requests.Session:
    s = getattr(_tls, "session", None)
    if s is None:
        s = cffi_requests.Session()
        _tls.session = s
    return s


def to_cn(url: str) -> str:
    return (url or "").replace("://www.chanel.com/", "://www.chanel.cn/")


def to_locale(url: str, locale: str) -> str:
    u = to_cn(url)
    u = re.sub(r"/(gb|kr|us|fr)/", f"/{locale}/", u, count=1)
    return u


def candidate_urls(url: str, locale: str) -> list[str]:
    u = to_locale(url, locale)
    out = [u]
    m = re.search(r"(https://www\.chanel\.cn/.+?/p/)([^/]+)(/.*)", u)
    if m:
        short = f"{m.group(1)}{m.group(2)}/"
        if short not in out:
            out.append(short)
    return out


def fetch(url: str, attempts: int = 2) -> str:
    last = ""
    for i in range(attempts):
        try:
            r = session().get(
                url,
                impersonate="chrome124",
                timeout=50,
                headers=HEADERS,
            )
            last = r.text or ""
            if r.status_code == 200 and len(last) > 20000:
                return last
            if r.status_code == 500:
                return last
            log(f"  weak {r.status_code} {len(last)} {url}")
        except Exception as e:
            log(f"  fetch error {e} {url}")
        time.sleep(0.5 * (i + 1))
    return last


def fetch_locale(url: str, locale: str) -> str:
    for cand in candidate_urls(url, locale):
        html = fetch(cand)
        if html and len(html) > 20000:
            return html
        time.sleep(0.15)
    return ""


def translate_sections(sections: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for sec in sections:
        title = sec.get("title") or ""
        body = sec.get("body") or ""
        if not body:
            continue
        if looks_korean(body) or title == "전성분" or looks_inci(body):
            out.append({"title": title, "body": body})
            continue
        out.append({"title": title, "body": t(body)})
    return out


def already_good(row: dict) -> bool:
    details = row.get("details") if isinstance(row.get("details"), dict) else {}
    secs = details.get("infoSectionsKo") or []
    if len(secs) < 2:
        return False
    body = " ".join(str(s.get("body") or "") for s in secs if isinstance(s, dict))
    return looks_korean(body)


def enrich_row(row: dict) -> dict:
    url = row.get("url") or ""
    sku = str(row.get("sku") or row.get("id") or "")
    kr_html = ""
    gb_html = ""
    if url:
        with ThreadPoolExecutor(max_workers=2) as pool:
            f_kr = pool.submit(fetch_locale, url, "kr")
            f_gb = pool.submit(fetch_locale, url, "gb")
            kr_html = f_kr.result()
            gb_html = f_gb.result()

    kr_secs = parse_product_accordion(kr_html) if kr_html else []
    gb_secs = parse_product_accordion(gb_html) if gb_html else []
    if looks_korean(" ".join(s.get("body") or "" for s in kr_secs)):
        sections = kr_secs
    else:
        sections = translate_sections(gb_secs)

    details = row.get("details") if isinstance(row.get("details"), dict) else {}
    details = dict(details)
    if sections:
        details["infoSectionsKo"] = sections
        intro = next((s["body"] for s in sections if s["title"] == "제품 소개"), "")
        if intro:
            details["editorial"] = intro
            details["description"] = intro
    kr_name = parse_kr_product_name(kr_html) if kr_html else ""
    if kr_name and looks_korean(kr_name):
        details["titleKo"] = kr_name
    row["details"] = details

    html_for_stock = gb_html or kr_html
    if html_for_stock:
        in_stock = parse_pdp_in_stock(html_for_stock)
        row["inStock"] = in_stock
        sizes = row.get("sizes") if isinstance(row.get("sizes"), list) else []
        new_sizes = []
        for sz in sizes:
            if isinstance(sz, dict):
                sz = dict(sz)
                sz["inStock"] = in_stock
                new_sizes.append(sz)
        if new_sizes:
            row["sizes"] = new_sizes
    return row


def load_raw(path: Path) -> dict:
    return json.loads(path.read_text())


def save_raw(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kinds", default="skincare,makeup,fragrance")
    ap.add_argument("--sku", default="")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()
    kinds = [k.strip() for k in args.kinds.split(",") if k.strip()]
    want = {args.sku.strip().upper()} if args.sku.strip() else None

    load_ko()
    for kind in kinds:
        path = KIND_FILES[kind]
        data = load_raw(path)
        products = data.get("products") or []
        todo: list[int] = []
        for i, row in enumerate(products):
            sku = str(row.get("sku") or row.get("id") or "").upper()
            if want and sku not in want:
                continue
            if args.resume and already_good(row):
                continue
            todo.append(i)
        log(f"{kind}: {len(todo)}/{len(products)} to enrich")
        done = 0

        def work(idx: int) -> tuple[int, dict]:
            row = dict(products[idx])
            return idx, enrich_row(row)

        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            futs = [pool.submit(work, i) for i in todo]
            for fut in as_completed(futs):
                idx, row = fut.result()
                products[idx] = row
                done += 1
                sku = row.get("sku")
                nsec = len((row.get("details") or {}).get("infoSectionsKo") or [])
                log(
                    f"[{kind} {done}/{len(todo)}] {sku} "
                    f"sections={nsec} stock={row.get('inStock')}"
                )
                if done % 15 == 0:
                    data["products"] = products
                    save_raw(path, data)
                    save_ko()
        data["products"] = products
        save_raw(path, data)
        save_ko()
        log(f"{kind}: wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
