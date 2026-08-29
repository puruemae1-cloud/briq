#!/usr/bin/env python3
"""Re-open each LV furniture PDP in WebKit and fill missing title/description.

  python3 scripts/enrich-lv-pdp-copy.py

Tips when Access Denied:
  1) Wait 15–30 minutes after a big scrape
  2) Open https://uk.louisvuitton.com in Safari first (page must load)
  3) Re-run this script once — do not spam retries
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

_spec = importlib.util.spec_from_file_location(
    "scrape_lv_furniture_lighting",
    ROOT / "scripts" / "scrape-lv-furniture-lighting.py",
)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

extract_pdp_details = _mod.extract_pdp_details
fetch_html = _mod.fetch_html
keep_open_if_headed = _mod.keep_open_if_headed
launch_browser = _mod.launch_browser
attach_api_sniffer = _mod.attach_api_sniffer
log = _mod.log
BASE = _mod.BASE

RAW = ROOT / "src/data/lv/lv-furniture-catalog-raw.json"
CACHE = ROOT / "src/data/lv/lv-furniture-pdp-cache.json"
HOME = f"{BASE}/eng-gb/"


def enrich_from_page(page, html: str) -> dict:
    details = extract_pdp_details(html)
    try:
        h1 = page.locator("h1").first
        if h1.count() and not details.get("title"):
            details["title"] = h1.inner_text(timeout=2000).strip()
    except Exception:
        pass
    try:
        for sel in (
            '[data-testid="productDescription"]',
            ".lv-product-page-description",
            ".lv-product-description",
            "#productDescription",
            "section[aria-label*='Description' i]",
            "[class*='description' i]",
        ):
            loc = page.locator(sel)
            if loc.count():
                text = loc.first.inner_text(timeout=1500).strip()
                if text and len(text) > 40:
                    if not details.get("paragraphs"):
                        details["paragraphs"] = [
                            re.sub(r"\s+", " ", p).strip()
                            for p in re.split(r"\n{2,}", text)
                            if p.strip()
                        ]
                    if not details.get("descriptionHtml"):
                        details["descriptionHtml"] = text
                    break
    except Exception:
        pass
    try:
        lis = page.locator("main li").all_inner_texts()
        bullets = [re.sub(r"\s+", " ", x).strip() for x in lis if 8 < len(x) < 200]
        if bullets and not details.get("bullets"):
            details["bullets"] = bullets[:30]
    except Exception:
        pass
    return details


def needs_copy(p: dict, cache: dict) -> bool:
    d = p.get("details") or {}
    if d.get("paragraphs") or d.get("descriptionHtml"):
        return False
    cached = cache.get(p.get("url") or "") or {}
    if cached.get("paragraphs") or cached.get("descriptionHtml"):
        return False
    return True


def save(raw: dict, cache: dict) -> None:
    CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False) + "\n")
    RAW.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n")


def main() -> int:
    if not RAW.is_file():
        log(f"missing {RAW}")
        return 1
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    products = raw.get("products") or []
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.is_file() else {}

    todo = [p for p in products if p.get("url") and needs_copy(p, cache)]
    log(f"Starting WebKit enrich… {len(todo)}/{len(products)} need copy")
    if not todo:
        log("Nothing to enrich — all products already have description.")
        return 0

    pw, browser, page, _ = launch_browser(True, False, engine="webkit")
    api_hits = attach_api_sniffer(page)
    ok = 0
    try:
        log(f"  warmup {HOME}")
        try:
            fetch_html(page, HOME, api_hits)
            time.sleep(2.0)
        except Exception as e:
            log(f"  warmup fail: {e}")
            log("Safari에서 LV가 열린 뒤에만 다시 실행하세요. 지금은 중단합니다.")
            keep_open_if_headed(True, str(e))
            return 1

        for i, p in enumerate(todo, start=1):
            url = p.get("url")
            log(f"[{i}/{len(todo)}] {url}")
            try:
                html = fetch_html(page, url, api_hits)
                details = enrich_from_page(page, html)
                details["url"] = url
                if details.get("gbpPrice") is None and p.get("gbpPrice"):
                    details["gbpPrice"] = p.get("gbpPrice")
                prev = cache.get(url) or {}
                if not details.get("images") and prev.get("images"):
                    details["images"] = prev["images"]
                cache[url] = details
                if details.get("title"):
                    p["title"] = details["title"]
                d = p.setdefault("details", {})
                d["paragraphs"] = details.get("paragraphs") or d.get("paragraphs") or []
                d["bullets"] = details.get("bullets") or d.get("bullets") or []
                d["specs"] = details.get("specs") or d.get("specs") or []
                d["descriptionHtml"] = (
                    details.get("descriptionHtml") or d.get("descriptionHtml") or ""
                )
                log(
                    f"  title={details.get('title')!r} "
                    f"paras={len(d['paragraphs'])} bullets={len(d['bullets'])}"
                )
                if d["paragraphs"] or d["descriptionHtml"]:
                    ok += 1
                save(raw, cache)
                time.sleep(2.5)
            except Exception as e:
                log(f"  fail: {e}")
                save(raw, cache)
                log("중간에 저장했습니다. Safari로 LV 확인 후 같은 명령으로 이어서 실행하세요.")
                keep_open_if_headed(True, str(e))
                return 1

        save(raw, cache)
        log(f"Updated copy on {ok}/{len(todo)} products")
        return 0
    finally:
        try:
            browser.close()
        except Exception:
            pass
        try:
            pw.stop()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
