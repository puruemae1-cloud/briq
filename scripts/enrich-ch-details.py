#!/usr/bin/env python3
"""Re-enrich all Chanel raw catalogs: editorial copy, characteristics, full images.

Fetches chanel.cn /gb/ PDP HTML for each SKU, merges Details-of-the-piece specs +
marketing paragraphs, downloads any missing gallery photos, then writes raw/cache.

  python3 scripts/enrich-ch-details.py
  python3 scripts/enrich-ch-details.py --only watches,fine,high
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ch_hybris_details import enrich_from_html, to_cn_url  # noqa: E402

IMG_ROOT = ROOT / "public/products/ch-pdp"

RAW_FILES: dict[str, Path] = {
    "watches": ROOT / "src/data/ch/ch-watches-catalog-raw.json",
    "fine": ROOT / "src/data/ch/ch-fine-jewellery-catalog-raw.json",
    "high": ROOT / "src/data/ch/ch-high-jewellery-catalog-raw.json",
    "jewellery": ROOT / "src/data/ch/ch-jewellery-catalog-raw.json",
    "sunglasses": ROOT / "src/data/ch/ch-sunglasses-catalog-raw.json",
    "fragrance": ROOT / "src/data/ch/ch-fragrance-catalog-raw.json",
    "other-acc": ROOT / "src/data/ch/ch-other-acc-catalog-raw.json",
    "handbags": ROOT / "src/data/ch/ch-handbags-catalog-raw.json",
    "shoes": ROOT / "src/data/ch/ch-shoes-catalog-raw.json",
    "rtw": ROOT / "src/data/ch/ch-rtw-catalog-raw.json",
    "slg": ROOT / "src/data/ch/ch-slg-catalog-raw.json",
}

CACHE_FILES: dict[str, Path] = {
    "watches": ROOT / "src/data/ch/ch-watches-pdp-cache.json",
    "fine": ROOT / "src/data/ch/ch-fine-jewellery-pdp-cache.json",
    "high": ROOT / "src/data/ch/ch-high-jewellery-pdp-cache.json",
    "jewellery": ROOT / "src/data/ch/ch-jewellery-pdp-cache.json",
    "sunglasses": ROOT / "src/data/ch/ch-sunglasses-pdp-cache.json",
    "fragrance": ROOT / "src/data/ch/ch-fragrance-pdp-cache.json",
    "other-acc": ROOT / "src/data/ch/ch-other-acc-pdp-cache.json",
    "handbags": ROOT / "src/data/ch/ch-handbags-pdp-cache.json",
    "shoes": ROOT / "src/data/ch/ch-shoes-pdp-cache.json",
    "rtw": ROOT / "src/data/ch/ch-rtw-pdp-cache.json",
    "slg": ROOT / "src/data/ch/ch-slg-pdp-cache.json",
}

_spec = importlib.util.spec_from_file_location(
    "scrape_ch_rtw", ROOT / "scripts" / "scrape-ch-rtw.py"
)
assert _spec and _spec.loader
_rtw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_rtw)

ChanelClient = _rtw.ChanelClient
log = _rtw.log


def load_json(path: Path) -> dict | list:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def fetch_html(client: ChanelClient, url: str) -> tuple[int, str]:
    cn = to_cn_url(url)
    try:
        with _rtw._session_lock:
            r = client.session.get(
                cn,
                impersonate=client.impersonate,
                timeout=90,
                headers={
                    **_rtw.HTML_HEADERS,
                    "Referer": to_cn_url("https://www.chanel.com/gb/"),
                },
            )
            client._req_count += 1
            if r.status_code == 200 and len(r.text) > 20000:
                return r.status_code, r.text
            st, text = r.status_code, r.text
    except Exception as e:
        log(f"  CN error {e}")
        st, text = 0, ""
    # COM fallback
    status, html = client.get_html(url, max_attempts=1)
    if status == 200 and len(html) > 20000:
        return status, html
    return st, text


def download_images(client: ChanelClient, sku: str, urls: list[str]) -> list[str]:
    dest = IMG_ROOT / sku.lower()
    dest.mkdir(parents=True, exist_ok=True)
    local: list[str] = []
    for i, url in enumerate(urls[:24], start=1):
        path = dest / f"{i}.jpg"
        web = f"/products/ch-pdp/{sku.lower()}/{i}.jpg"
        if path.exists() and path.stat().st_size > 2048:
            local.append(web)
            continue
        data = client.get_bytes(url, referer="https://www.chanel.com/gb/")
        if not data:
            data = client.get_bytes(
                url.replace("www.chanel.com", "www.chanel.cn"),
                referer=to_cn_url("https://www.chanel.com/gb/"),
            )
        if not data:
            log(f"  skip img {sku} #{i}")
            continue
        path.write_bytes(data)
        local.append(web)
        time.sleep(0.04)
    return local


def needs_enrich(row: dict) -> bool:
    details = row.get("details") if isinstance(row.get("details"), dict) else {}
    chars = details.get("characteristics") or row.get("characteristics")
    editorial = details.get("editorial") or ""
    desc = (details.get("description") or "").strip()
    imgs = row.get("images") or []
    locals_ = row.get("localImages") or []
    if not chars:
        return True
    if not editorial and len(desc) < 100:
        return True
    if len(locals_) < max(2, min(len(imgs), 4)):
        return True
    return False


def enrich_bucket(client: ChanelClient, key: str, force: bool = False) -> int:
    path = RAW_FILES[key]
    if not path.exists():
        log(f"skip missing {path}")
        return 0
    payload = load_json(path)
    if not isinstance(payload, dict):
        log(f"skip bad payload {path}")
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
        if not force and not needs_enrich(row):
            continue

        status, html = fetch_html(client, url)
        if status != 200 or len(html) < 15000:
            log(f"[{key} {i}/{len(products)}] FAIL fetch {sku} st={status} len={len(html)}")
            time.sleep(0.4)
            continue

        details = row.get("details") if isinstance(row.get("details"), dict) else {}
        enriched = enrich_from_html(html, sku, details)
        row["details"] = enriched["details"]
        new_images = enriched["images"] or row.get("images") or []
        if new_images:
            # Prefer newly discovered gallery when longer.
            if len(new_images) >= len(row.get("images") or []):
                row["images"] = new_images

        locals_ = download_images(client, sku, row.get("images") or [])
        if locals_:
            row["localImages"] = locals_
            row["localImage"] = locals_[0]
            if len(locals_) > 1:
                row["localHover"] = locals_[1]

        cache[sku] = row
        updated += 1
        n_chars = len((row.get("details") or {}).get("characteristics") or [])
        ed_len = len((row.get("details") or {}).get("editorial") or "")
        log(
            f"[{key} {i}/{len(products)}] OK {sku} "
            f"chars={n_chars} editorial={ed_len} "
            f"imgs={len(row.get('images') or [])} local={len(row.get('localImages') or [])}"
        )
        if i % 10 == 0:
            payload["products"] = products
            payload["enrichedAt"] = datetime.now(timezone.utc).isoformat()
            save_json(path, payload)
            if cache_path:
                save_json(cache_path, cache)
        time.sleep(0.25)

    payload["products"] = products
    payload["enrichedAt"] = datetime.now(timezone.utc).isoformat()
    save_json(path, payload)
    if cache_path:
        save_json(cache_path, cache)
    log(f"{key}: updated {updated}/{len(products)}")
    return updated


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--only",
        default="",
        help="Comma list of buckets: watches,fine,high,jewellery,sunglasses,...",
    )
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
            log("skip proxy hunt — enrich uses chanel.cn")
            return True
        return _orig(self)

    _rtw.ChanelClient.probe_direct = _probe
    _rtw.ChanelClient.ensure_proxy = lambda self: log("skip proxy")
    _rtw.ChanelClient.rotate_proxy = lambda self, mark_dead=True: self.clear_proxy()

    client = ChanelClient()
    IMG_ROOT.mkdir(parents=True, exist_ok=True)

    total = 0
    for key in keys:
        log(f"=== enrich {key} ===")
        total += enrich_bucket(client, key, force=args.force)
    log(f"done total updated={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
