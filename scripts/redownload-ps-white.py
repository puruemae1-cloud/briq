#!/usr/bin/env python3
"""Re-download Paul Smith pale colourway PDP images from official CDN (no greymat).

Prior rembg/soft greymat flattened white / ivory / cream / ecru garments onto
#e7e7e7 (grey blocks) or washed them out. Restore pristine assets.paulsmith.com
bytes — same approach as redownload-bb-greymat.py for Burberry.

When raw catalog rows lack content.images (common for older cached rows),
re-hit the official PDP once to recover CDN URLs.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ps_pale_colour import is_pale_ps_row, pale_ps_handles  # noqa: E402

SPEC = importlib.util.spec_from_file_location(
    "ps_mens", ROOT / "scripts/scrape-ps-mens.py"
)
mens = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mens)

RAW = ROOT / "src/data/ps/ps-catalog-raw.json"
WORKERS = 8


def remote_urls(row: dict) -> list[str]:
    urls = mens.content_image_urls(row)
    if urls:
        return urls
    plp = row.get("plp") or {}
    return mens.plp_image_urls(plp) if plp else []


def hover_url(row: dict) -> str | None:
    plp = row.get("plp") or {}
    urls = mens.plp_image_urls(plp) if plp else []
    if len(urls) > 1:
        return urls[1]
    return None


def ensure_content_urls(row: dict) -> dict:
    """Fill content.images from a live PDP when the raw row was slimmed."""
    if mens.content_image_urls(row):
        return row
    link = ""
    plp = row.get("plp") or {}
    if isinstance(plp, dict):
        link = str(plp.get("link") or "").strip().lstrip("/")
    if not link:
        link = str(row.get("handle") or "").strip()
    if not link:
        return row
    pdp = mens.scrape_pdp(link)
    if not pdp:
        return row
    if pdp.get("content"):
        row["content"] = pdp["content"]
    if pdp.get("entity") and not row.get("entity"):
        row["entity"] = pdp["entity"]
    if pdp.get("sourceUrl"):
        row["sourceUrl"] = pdp["sourceUrl"]
    return row


def download_one(row: dict) -> tuple[str, int, int, str, dict]:
    handle = str(row.get("handle") or "").strip()
    if not handle:
        return "", 0, 1, "no-handle", row
    row = ensure_content_urls(row)
    urls = remote_urls(row)
    if not urls:
        return handle, 0, 1, "no-urls", row
    # Always write official bytes — never greymat pale colourways.
    local = mens.download_images(handle, urls, greymat=False)
    ok = len(local)
    fail = max(0, min(8, len(urls)) - ok)
    hurl = hover_url(row)
    if hurl:
        hover = mens.download_hover(handle, hurl, greymat=False)
        if hover:
            ok += 1
        else:
            fail += 1
    return handle, ok, fail, "ok" if ok else "empty", row


def main() -> None:
    raw = json.loads(RAW.read_text())
    rows = [
        r for r in raw.values() if isinstance(r, dict) and is_pale_ps_row(r)
    ]
    handles = pale_ps_handles(raw)
    print(
        f"PS pale redownload products={len(rows)} handles={len(handles)} "
        f"workers={WORKERS}",
        flush=True,
    )
    total_ok = total_fail = 0
    updated = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(download_one, dict(r)) for r in rows]
        done = 0
        for fut in as_completed(futs):
            handle, ok, fail, status, row = fut.result()
            total_ok += ok
            total_fail += fail
            done += 1
            key = str(row.get("key") or "")
            if key and key in raw:
                if row.get("content") and row["content"] != raw[key].get(
                    "content"
                ):
                    raw[key]["content"] = row["content"]
                    updated += 1
                if row.get("entity") and not raw[key].get("entity"):
                    raw[key]["entity"] = row["entity"]
            if done <= 8 or done % 25 == 0 or done == len(rows):
                print(
                    f"{done}/{len(rows)} {handle} ok={ok} fail={fail} {status} "
                    f"(total_ok={total_ok} fail={total_fail})",
                    flush=True,
                )
            time.sleep(0.01)
    if updated:
        RAW.write_text(
            json.dumps(raw, ensure_ascii=False, separators=(",", ":")) + "\n"
        )
        print(f"updated raw content for {updated} products → {RAW}", flush=True)
    print(
        f"done products={len(rows)} imgs_ok={total_ok} fail={total_fail}",
        flush=True,
    )


if __name__ == "__main__":
    main()
