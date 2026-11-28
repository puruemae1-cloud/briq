#!/usr/bin/env python3
"""Scrape Paul Smith UK women + gifts/homeware into existing ps-catalog-raw.json.

Reuses helpers from scrape-ps-mens.py. Merges channels onto existing keys.
"""
from __future__ import annotations

import importlib.util
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("ps_mens", ROOT / "scripts/scrape-ps-mens.py")
mens = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mens)

SECTIONS = [
    {"key": "clothing-women", "pageReference": "363", "path": "womens/clothing", "channel": "clothing-women"},
    {"key": "shoes-women", "pageReference": "380", "path": "womens/shoes", "channel": "shoes-women"},
    {"key": "accessories-women", "pageReference": "346", "path": "womens/accessories", "channel": "accessories-women"},
    {"key": "suits-women", "pageReference": "389", "path": "womens/suits", "channel": "suits-women"},
    {"key": "gifts-him", "pageReference": "436", "path": "gifts/gifts-for-him", "channel": "gifts-him"},
    {"key": "gifts-her", "pageReference": "423", "path": "gifts/gifts-for-her", "channel": "gifts-her"},
    {"key": "homeware", "pageReference": "490", "path": "homeware/all", "channel": "homeware"},
]


def main() -> None:
    mens.OUT_DIR.mkdir(parents=True, exist_ok=True)
    existing: dict[str, dict] = {}
    if mens.RAW_PATH.exists():
        existing = json.loads(mens.RAW_PATH.read_text())
        print(f"loaded existing raw={len(existing)}")

    plp_by_key: dict[str, dict] = {}
    membership: dict[str, set[str]] = {}
    # Preserve previous channels
    for key, row in existing.items():
        membership[key] = set(row.get("channels") or [])

    for section in SECTIONS:
        items = mens.scrape_section(section)
        for p in items:
            key = str(p.get("key") or "")
            if not key:
                continue
            membership.setdefault(key, set()).add(section["channel"])
            prev = plp_by_key.get(key)
            if not prev or len(p.get("variants") or []) > len(prev.get("variants") or []):
                plp_by_key[key] = p
        time.sleep(0.2)

    print(f"extend PLP unique keys={len(plp_by_key)}")

    todos = []
    for key, p in plp_by_key.items():
        link = (p.get("link") or "").strip().lstrip("/")
        if key in existing and existing[key].get("entity") and existing[key].get("images"):
            existing[key]["channels"] = sorted(membership.get(key, set()))
            existing[key]["plp"] = {
                "key": key,
                "title": p.get("title"),
                "link": link,
                "sellingPrice": p.get("sellingPrice"),
                "listPrice": p.get("listPrice"),
                "variants": p.get("variants") or [],
                "custom": p.get("custom") or {},
                "style": mens.custom_label(p.get("custom"), "style"),
                "product_type": mens.custom_label(p.get("custom"), "product_type"),
            }
            continue
        todos.append((key, p, link))

    print(f"PDP todo={len(todos)} cached-update={len(plp_by_key) - len(todos)}")

    def work(item):
        key, p, link = item
        pdp = mens.scrape_pdp(link)
        handle = link.replace("/", "-") or key
        urls = []
        if pdp:
            for img in (pdp.get("content") or {}).get("images") or []:
                if isinstance(img, dict) and img.get("url"):
                    urls.append(img["url"])
        if not urls:
            urls = mens.plp_image_urls(p)
        local = mens.download_images(handle, urls)
        row = {
            "key": key,
            "handle": handle,
            "channels": sorted(membership.get(key, set())),
            "plp": {
                "key": key,
                "title": p.get("title"),
                "link": link,
                "sellingPrice": p.get("sellingPrice"),
                "listPrice": p.get("listPrice"),
                "variants": p.get("variants") or [],
                "custom": p.get("custom") or {},
                "style": mens.custom_label(p.get("custom"), "style"),
                "product_type": mens.custom_label(p.get("custom"), "product_type"),
            },
            "entity": (pdp or {}).get("entity") or {},
            "content": (pdp or {}).get("content") or {},
            "measurementChart": (pdp or {}).get("measurementChart") or {},
            "configurableOptions": (pdp or {}).get("configurableOptions") or [],
            "selectedPrice": (pdp or {}).get("selectedPrice") or {},
            "images": local,
            "sourceUrl": f"{mens.BASE}/uk/{link}",
            "isOutOfStock": bool((pdp or {}).get("isOutOfStock")),
        }
        return key, row

    from concurrent.futures import ThreadPoolExecutor, as_completed

    done = 0
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = [ex.submit(work, t) for t in todos]
        for fut in as_completed(futs):
            try:
                key, row = fut.result()
                existing[key] = row
                done += 1
                if done <= 5 or done % 25 == 0:
                    print(f"pdp {done}/{len(todos)} {row.get('handle')}", flush=True)
                if done % 20 == 0:
                    mens.RAW_PATH.write_text(json.dumps(existing, ensure_ascii=False) + "\n")
            except Exception as e:
                print("worker fail", e)

    for key, p in plp_by_key.items():
        if key not in existing:
            link = (p.get("link") or "").strip().lstrip("/")
            handle = link.replace("/", "-") or key
            existing[key] = {
                "key": key,
                "handle": handle,
                "channels": sorted(membership.get(key, set())),
                "plp": {
                    "key": key,
                    "title": p.get("title"),
                    "link": link,
                    "sellingPrice": p.get("sellingPrice"),
                    "listPrice": p.get("listPrice"),
                    "variants": p.get("variants") or [],
                    "custom": p.get("custom") or {},
                    "style": mens.custom_label(p.get("custom"), "style"),
                    "product_type": mens.custom_label(p.get("custom"), "product_type"),
                },
                "entity": {},
                "content": {},
                "measurementChart": {},
                "configurableOptions": [],
                "selectedPrice": {},
                "images": mens.download_images(handle, mens.plp_image_urls(p)),
                "sourceUrl": f"{mens.BASE}/uk/{link}",
            }
        else:
            existing[key]["channels"] = sorted(membership.get(key, set()))

    # Slim write (compact) for size
    mens.RAW_PATH.write_text(json.dumps(existing, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"Wrote {len(existing)} products → {mens.RAW_PATH}")


if __name__ == "__main__":
    main()
