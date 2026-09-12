#!/usr/bin/env python3
"""Enrich sparse Celine raw PDP copy from official SFCC Product-Variation.

Fills empty DETAILS / CARE AND MAINTENANCE from longDescription +
custom.celCareAndMaintenance so Briq PDPs match official GB content.

  python3 scripts/enrich-ce-pdp-copy-sfcc.py
  python3 scripts/enrich-ce-pdp-copy-sfcc.py --limit 50
  python3 scripts/enrich-ce-pdp-copy-sfcc.py --sku 123662J79.GFY5
"""
from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from celine_common import SFCC_VARIATION, UA, load_json, save_json  # noqa: E402
from celine_config import celine_raw_paths  # noqa: E402


def fetch_sfcc_product(pid: str) -> dict | None:
    sku = (pid or "").strip()
    if not sku:
        return None
    url = f"{SFCC_VARIATION}?{urllib.parse.urlencode({'pid': sku})}"
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=35) as resp:
            data = json.loads(resp.read().decode("utf-8", "ignore"))
    except Exception as e:
        print(f"  sfcc fail {sku}: {e}", flush=True)
        return None
    prod = data.get("product") if isinstance(data, dict) else None
    return prod if isinstance(prod, dict) else None


def split_html_lines(raw: str) -> list[str]:
    text = html_lib.unescape(raw or "")
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</p\s*>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    lines = []
    for part in re.split(r"[\n\r]+", text):
        s = re.sub(r"\s+", " ", part).strip(" ·;-")
        if not s:
            continue
        if re.match(r"(?i)^reference\s*:", s):
            continue
        if re.match(r"(?i)^closure_system_", s):
            continue
        lines.append(s)
    return lines


def detail_count(row: dict) -> int:
    n = 0
    for item in row.get("details") or []:
        if not isinstance(item, dict):
            continue
        body = (item.get("body") or item.get("html") or "").strip()
        if body:
            n += len(split_html_lines(body)) or 1
    return n


def needs_enrich(row: dict) -> bool:
    return detail_count(row) < 3


def build_details_blocks(prod: dict) -> list[dict]:
    blocks: list[dict] = []
    detail_lines = split_html_lines(str(prod.get("longDescription") or ""))
    # Drop size-chart noise that is only a reference line
    detail_lines = [x for x in detail_lines if x]
    if detail_lines:
        blocks.append(
            {
                "label": "DETAILS",
                "body": "\n".join(detail_lines),
                "html": "<br>".join(html_lib.escape(x) for x in detail_lines),
            }
        )
    custom = prod.get("custom") if isinstance(prod.get("custom"), dict) else {}
    care_raw = str(custom.get("celCareAndMaintenance") or "").strip()
    if care_raw:
        care_lines = split_html_lines(care_raw)
        if care_lines:
            # Prefer one joined care guide (match_care_fit handles long guides)
            blocks.append(
                {
                    "label": "CARE AND MAINTENANCE",
                    "body": "\n".join(care_lines),
                    "html": "<br>".join(html_lib.escape(x) for x in care_lines),
                }
            )
    # Carry / function as size-and-fit style guidance when useful
    extras = []
    carry = str(custom.get("celCarryOption") or "").replace(",", ", ").strip()
    if carry:
        extras.append(carry)
    fabric = str(custom.get("celFabricStyle") or custom.get("celMaterial") or "").strip()
    if fabric and fabric.upper() not in " ".join(detail_lines).upper():
        extras.append(fabric)
    func = str(custom.get("celFunction") or "").strip()
    if func:
        extras.append(func)
    if extras:
        blocks.append(
            {
                "label": "Size and fit",
                "body": "\n".join(extras),
                "html": "<br>".join(html_lib.escape(x) for x in extras),
            }
        )
    return blocks


def enrich_row(row: dict) -> bool:
    sku = str(row.get("sku") or row.get("id") or "").strip()
    if not sku or not needs_enrich(row):
        return False
    prod = fetch_sfcc_product(sku)
    if not prod:
        return False
    blocks = build_details_blocks(prod)
    if not blocks:
        return False
    row["details"] = blocks
    # Keep title from SFCC when scrape title was blocked / empty
    name = str(prod.get("productName") or "").strip()
    if name and (
        not (row.get("title") or "").strip()
        or "access denied" in str(row.get("title") or "").lower()
    ):
        row["title"] = name.title() if name.isupper() else name
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--sku", default="")
    ap.add_argument("--sleep", type=float, default=0.12)
    args = ap.parse_args()

    want = (args.sku or "").strip().upper()
    fixed = 0
    failed = 0
    skipped = 0

    for path in celine_raw_paths():
        payload = load_json(path, {"products": []})
        products = payload.get("products") or []
        changed = False
        for row in products:
            sku = str(row.get("sku") or row.get("id") or "").strip()
            if want and sku.upper() != want and want not in sku.upper():
                continue
            if not needs_enrich(row):
                skipped += 1
                continue
            print(f"enrich {sku}", flush=True)
            ok = enrich_row(row)
            if ok:
                fixed += 1
                changed = True
                print(f"  ok details={detail_count(row)}", flush=True)
            else:
                failed += 1
            time.sleep(args.sleep)
            if args.limit and fixed >= args.limit:
                break
        if changed:
            payload["products"] = products
            save_json(path, payload)
            print(f"saved {path.name}", flush=True)
        if args.limit and fixed >= args.limit:
            break

    print(f"DONE fixed={fixed} failed={failed} skipped_ok={skipped}", flush=True)
    return 0 if fixed or not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
