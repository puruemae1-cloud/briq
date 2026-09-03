#!/usr/bin/env python3
"""Fill missing CW editorial pages + PDP copy (short/long/features/technicals).

Used for new models (e.g. Trident Biscay GMT) that landed with galleries but
stub Korean descriptions and no story/video blocks from christopherward.com.
"""
from __future__ import annotations

import html as H
import importlib.util
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
RAW = json.loads((ROOT / "src/data/cw/cw-catalog-raw.json").read_text())["products"]
ED_PATH = ROOT / "src/data/cw/cw-editorial.json"
ENR_PATH = ROOT / "src/data/cw/cw-pdp-enriched.json"

UA = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json,text/javascript,*/*",
    "X-Requested-With": "XMLHttpRequest",
}
API = "https://www.christopherward.com/on/demandware.store/Sites-cwgross-Site/en_GB/Product-Variation"

SKIP_MODEL_KEYS = {
    "c60-trident-pro-300---bundle",
}


def model_key(url: str) -> str | None:
    path = urlparse(url.split("?")[0]).path.strip("/")
    parts = [p for p in path.split("/") if p]
    if len(parts) >= 2 and parts[-1].endswith(".html"):
        return parts[-2]
    return parts[-1].replace(".html", "") if parts else None


def load_editorial_scraper():
    spec = importlib.util.spec_from_file_location(
        "cw_ed_scrape", ROOT / "scripts/rescrape-cw-editorial-full.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


def fetch_json(url: str, retries: int = 3) -> dict:
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=55) as r:
                return json.load(r)
        except Exception:
            if i == retries - 1:
                raise
            time.sleep(1.2 * (i + 1))
    return {}


def parse_technicals(product: dict) -> list[dict]:
    rows = []
    for t in product.get("productTechnicals") or []:
        label = str(t.get("label") or "").strip()
        value = t.get("value")
        if isinstance(value, list):
            value = ", ".join(str(x) for x in value)
        value = str(value).strip() if value is not None else ""
        if label and value:
            rows.append({"labelEn": label, "valueEn": value})
    return rows


def parse_features(product: dict) -> list[str]:
    features = product.get("productFeatures") or []
    if not isinstance(features, list):
        return []
    return [H.unescape(str(f)).replace("\xa0", " ").strip() for f in features if f]


def needs_copy(row: dict) -> bool:
    if row.get("error"):
        return True
    if not (row.get("shortDescriptionEn") or "").strip():
        return True
    if not (row.get("featuresEn") or []):
        return True
    if not (row.get("technicalsEn") or []):
        return True
    return False


def apply_copy(row: dict, product: dict) -> bool:
    short = H.unescape(product.get("shortDescription") or "").strip()
    long = H.unescape(product.get("longDescription") or "").strip()
    features = parse_features(product)
    technicals = parse_technicals(product)
    changed = False
    if short and short != row.get("shortDescriptionEn"):
        row["shortDescriptionEn"] = short
        changed = True
    if long and long != row.get("longDescriptionEn"):
        row["longDescriptionEn"] = long
        changed = True
    if features and features != row.get("featuresEn"):
        row["featuresEn"] = features
        changed = True
    if technicals and technicals != row.get("technicalsEn"):
        row["technicalsEn"] = technicals
        changed = True
    name = (product.get("productName") or "").strip()
    if name and not row.get("nameEn"):
        row["nameEn"] = name
        changed = True
    return changed


def enrich_missing_editorial(*, only_keys: set[str] | None = None) -> list[str]:
    mod = load_editorial_scraper()
    existing = json.loads(ED_PATH.read_text()) if ED_PATH.exists() else {"models": {}}
    models = existing.get("models") or {}
    seeds: dict[str, str] = {}
    for p in RAW:
        u = p.get("url") or ""
        if not u or "nearly-new" in u.lower() or "/sale/" in u:
            continue
        k = model_key(u)
        if not k or k in SKIP_MODEL_KEYS:
            continue
        if only_keys is not None and k not in only_keys:
            continue
        if k not in seeds:
            seeds[k] = u

    todo = [
        (k, u)
        for k, u in sorted(seeds.items())
        if not ((models.get(k) or {}).get("sections") or [])
    ]
    print(f"editorial missing {len(todo)} / seeds {len(seeds)}", flush=True)
    updated: list[str] = []
    for i, (key, url) in enumerate(todo, 1):
        print(f"  [{i}/{len(todo)}] scrape {key}", flush=True)
        try:
            data = mod.scrape_editorial(url, key)
        except Exception as e:
            print(f"   FAIL {e}", flush=True)
            continue
        n = len(data.get("sections") or [])
        with_text = sum(
            1 for s in data.get("sections") or [] if (s.get("bodyEn") or "").strip()
        )
        print(f"   sections {n} withText {with_text}", flush=True)
        if n:
            models[key] = data
            updated.append(key)
        time.sleep(0.35)

    ED_PATH.write_text(
        json.dumps(
            {
                "scrapedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "models": models,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    return updated


def dial_family(sku: str) -> str:
    parts = sku.split("-")
    return "-".join(parts[:-1]) if len(parts) > 3 else sku


def enrich_missing_copy(*, sku_prefix: str | None = None) -> int:
    enr = json.loads(ENR_PATH.read_text()) if ENR_PATH.exists() else {"products": {}}
    products: dict = enr.get("products") or {}
    # One API call per dial family (copy is shared across straps)
    seeds: list[str] = []
    seen_dial: set[str] = set()
    for p in RAW:
        sku = (p.get("sku") or "").strip()
        if sku.count("-") < 2:
            continue
        if sku_prefix and sku_prefix.upper() not in sku.upper():
            continue
        dial = dial_family(sku)
        if dial in seen_dial:
            continue
        # Any member of this dial family still missing copy?
        family_skus = [
            x.get("sku") or ""
            for x in RAW
            if dial_family(x.get("sku") or "") == dial and (x.get("sku") or "").count("-") >= 2
        ]
        if not any(needs_copy(products.get(s) or {}) for s in family_skus):
            continue
        seen_dial.add(dial)
        seeds.append(sku)

    print(f"copy dial families needing enrich {len(seeds)}", flush=True)
    changed_n = 0
    for i, sku in enumerate(seeds, 1):
        try:
            data = fetch_json(f"{API}?pid={urllib.parse.quote(sku)}&quantity=1")
            ap = data.get("product") or {}
            if not ap.get("id"):
                print(f"  skip {sku}: no product", flush=True)
                continue
            dial = dial_family(sku)
            targets = [
                s
                for s in products
                if dial_family(s) == dial or (products.get(s) or {}).get("derivedFrom") == sku
            ]
            if sku not in targets:
                targets.append(sku)
            for target in targets:
                row = products.setdefault(target, {"sku": target})
                if apply_copy(row, ap):
                    changed_n += 1
            # Also ensure raw family SKUs exist with copy even if not yet in enrich index
            for p in RAW:
                s = p.get("sku") or ""
                if dial_family(s) != dial:
                    continue
                row = products.setdefault(s, {"sku": s})
                if apply_copy(row, ap):
                    changed_n += 1
            print(f"  copy {i}/{len(seeds)} {sku} changed≈{changed_n}", flush=True)
            time.sleep(0.08)
        except Exception as e:
            print(f"  FAIL {sku}: {e}", flush=True)

    enr["scrapedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    enr["products"] = products
    ENR_PATH.write_text(json.dumps(enr, ensure_ascii=False, indent=2) + "\n")
    return changed_n


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--models",
        default="",
        help="Comma-separated model keys (default: all missing)",
    )
    ap.add_argument(
        "--sku-prefix",
        default="",
        help="Only enrich copy for SKUs containing this token (e.g. AGM1)",
    )
    ap.add_argument("--skip-editorial", action="store_true")
    ap.add_argument("--skip-copy", action="store_true")
    args = ap.parse_args()

    only = {k.strip() for k in args.models.split(",") if k.strip()} or None
    if not args.skip_editorial:
        updated = enrich_missing_editorial(only_keys=only)
        print("editorial updated", updated, flush=True)
    if not args.skip_copy:
        n = enrich_missing_copy(sku_prefix=args.sku_prefix or None)
        print("copy rows touched", n, flush=True)


if __name__ == "__main__":
    main()
