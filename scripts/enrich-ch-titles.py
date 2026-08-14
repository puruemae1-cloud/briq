#!/usr/bin/env python3
"""Refresh Chanel product titles to match official PDP headings.

Fetches each PDP (chanel.cn /gb/) and sets:
  titleShort  — short product title (e.g. "J12 watch, 28 mm")
  subtitle    — materials line (e.g. "Highly resistant white ceramic and steel")
  title       — composed official name = title + subtitle (+ colour)

  python3 scripts/enrich-ch-titles.py
  python3 scripts/enrich-ch-titles.py --only watches,fine
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ch_hybris_details import (  # noqa: E402
    compose_official_name,
    enrich_from_html,
)

_spec = importlib.util.spec_from_file_location(
    "scrape_ch_rtw", ROOT / "scripts" / "scrape-ch-rtw.py"
)
assert _spec and _spec.loader
_rtw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_rtw)

_espec = importlib.util.spec_from_file_location(
    "enrich_ch_details", ROOT / "scripts" / "enrich-ch-details.py"
)
assert _espec and _espec.loader
_enrich = importlib.util.module_from_spec(_espec)
_espec.loader.exec_module(_enrich)

ChanelClient = _rtw.ChanelClient
log = _rtw.log
RAW_FILES = _enrich.RAW_FILES
CACHE_FILES = _enrich.CACHE_FILES
fetch_html = _enrich.fetch_html
load_json = _enrich.load_json
save_json = _enrich.save_json


def needs_title_refresh(row: dict) -> bool:
    title = str(row.get("title") or "").strip()
    subtitle = str(row.get("subtitle") or "").strip()
    if not subtitle:
        return True
    if subtitle.lower() in title.lower():
        return False
    return True


def enrich_bucket(client: ChanelClient, key: str, force: bool = False) -> int:
    path = RAW_FILES[key]
    if not path.exists():
        log(f"skip missing {path}")
        return 0
    payload = load_json(path)
    if not isinstance(payload, dict):
        return 0
    products = payload.get("products") or []
    cache_path = CACHE_FILES.get(key)
    cache = load_json(cache_path) if cache_path else {}
    if not isinstance(cache, dict):
        cache = {}

    updated = 0
    for i, row in enumerate(products, start=1):
        if not isinstance(row, dict):
            continue
        sku = str(row.get("sku") or row.get("productCode") or row.get("id") or "").strip()
        url = str(row.get("url") or "").strip()
        if not sku or not url:
            continue
        if not force and not needs_title_refresh(row):
            continue

        status, html = fetch_html(client, url)
        if status != 200 or len(html) < 15000:
            log(f"[{key} {i}/{len(products)}] FAIL {sku} st={status}")
            time.sleep(0.3)
            continue

        details = row.get("details") if isinstance(row.get("details"), dict) else {}
        enriched = enrich_from_html(html, sku, details)
        parts = enriched.get("titleParts") or {}
        short = (parts.get("title") or row.get("titleShort") or row.get("title") or "").strip()
        subtitle = (parts.get("subtitle") or "").strip()
        color = (parts.get("color") or details.get("color") or "").strip()
        official = (
            enriched.get("officialName")
            or compose_official_name(short, subtitle, color)
            or short
        )
        if not official:
            log(f"[{key} {i}/{len(products)}] empty title {sku}")
            continue

        if short:
            row["titleShort"] = short
        if subtitle:
            row["subtitle"] = subtitle
        row["title"] = official
        row["details"] = enriched["details"]
        if color and isinstance(row.get("details"), dict) and not row["details"].get("color"):
            row["details"]["color"] = color

        cache[sku] = row
        updated += 1
        log(
            f"[{key} {i}/{len(products)}] {sku} → {official[:90]}"
            + ("…" if len(official) > 90 else "")
        )
        if i % 15 == 0:
            payload["products"] = products
            payload["titlesEnrichedAt"] = datetime.now(timezone.utc).isoformat()
            save_json(path, payload)
            if cache_path:
                save_json(cache_path, cache)
        time.sleep(0.2)

    payload["products"] = products
    payload["titlesEnrichedAt"] = datetime.now(timezone.utc).isoformat()
    save_json(path, payload)
    if cache_path:
        save_json(cache_path, cache)
    log(f"{key}: titles updated {updated}/{len(products)}")
    return updated


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    keys = list(RAW_FILES)
    if args.only.strip():
        keys = [k.strip() for k in args.only.split(",") if k.strip() in RAW_FILES]
        if not keys:
            log("ERROR: no valid --only buckets")
            return 1

    _rtw.IMPERSONATES = ("safari18_0_ios",)
    _rtw.SEED_PROXIES = []
    _skip = {"v": True}
    _orig = _rtw.ChanelClient.probe_direct

    def _probe(self) -> bool:
        if _skip["v"]:
            _skip["v"] = False
            log("skip proxy hunt — titles use chanel.cn")
            return True
        return _orig(self)

    _rtw.ChanelClient.probe_direct = _probe
    _rtw.ChanelClient.ensure_proxy = lambda self: log("skip proxy")
    _rtw.ChanelClient.rotate_proxy = lambda self, mark_dead=True: self.clear_proxy()

    client = ChanelClient()
    total = 0
    for key in keys:
        log(f"=== titles {key} ===")
        total += enrich_bucket(client, key, force=args.force)
    log(f"done total titles updated={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
