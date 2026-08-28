"""Re-download Paul Smith PDP images from official CDN (no greymat).

Prior rembg/soft greymat flattened apparel and pale colourways onto #e7e7e7
(patchy mats / grey blocks / sand garments eaten by the mat). Restore pristine
assets.paulsmith.com bytes — same approach as redownload-bb-greymat.py.

Default: pale colourways only. Use --clothing for all PS apparel (recommended
after greymat policy change). --grey-only refreshes Grey/Silver only.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ps_pale_colour import (  # noqa: E402
    _label,
    is_pale_ps_row,
    is_ps_clothing_row,
)

SPEC = importlib.util.spec_from_file_location(
    "ps_mens", ROOT / "scripts/scrape-ps-mens.py"
)
mens = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mens)

RAW = ROOT / "src/data/ps/ps-catalog-raw.json"
WORKERS = 8

_HANDLE_GREY_RE = re.compile(
    r"^(?:mens?|womens?|men-s|women-s)-?"
    r"(grey|gray|silver|grey-marl|gray-marl)\b"
    r"|^(grey|gray|silver|grey-marl|gray-marl)\b",
    re.I,
)


def is_grey_ps_row(row: dict | None) -> bool:
    """Grey / Silver family only (subset of pale_ps)."""
    if not row:
        return False
    ent = row.get("entity") if isinstance(row.get("entity"), dict) else {}
    cg = _label(ent.get("colour_group"))
    if cg and re.match(r"^(grey|gray|silver)$", cg, re.I):
        return True
    handle = str(row.get("handle") or "").strip().replace("_", "-")
    return bool(handle and _HANDLE_GREY_RE.search(handle))


def remote_urls(row: dict) -> list[str]:
    urls = mens.gallery_image_urls(row)
    if urls:
        return urls
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
    if mens.content_image_urls(row) or mens.gallery_image_urls(row):
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
    # Always write official bytes — never greymat pale/grey colourways.
    local = mens.download_images(handle, urls, greymat=False)
    ok = len(local)
    fail = max(0, min(8, len(urls)) - ok)
    row["images"] = local
    hurl = hover_url(row)
    if hurl:
        hover = mens.download_hover(handle, hurl, greymat=False)
        if hover:
            ok += 1
        else:
            fail += 1
    return handle, ok, fail, "ok" if ok else "empty", row


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--clothing",
        action="store_true",
        help="All PS apparel (clothing / tailoring / suits)",
    )
    ap.add_argument(
        "--grey-only",
        action="store_true",
        help="Only Grey/Silver colourways and grey-* handles",
    )
    ap.add_argument(
        "--handles",
        nargs="*",
        default=None,
        help="Optional explicit handles to refresh",
    )
    args = ap.parse_args()

    raw = json.loads(RAW.read_text())
    if args.handles:
        want = {h.strip().lstrip("/") for h in args.handles if h.strip()}
        rows = [
            r
            for r in raw.values()
            if isinstance(r, dict) and str(r.get("handle") or "") in want
        ]
    elif args.clothing:
        rows = [
            r for r in raw.values() if isinstance(r, dict) and is_ps_clothing_row(r)
        ]
    elif args.grey_only:
        rows = [
            r for r in raw.values() if isinstance(r, dict) and is_grey_ps_row(r)
        ]
    else:
        rows = [
            r for r in raw.values() if isinstance(r, dict) and is_pale_ps_row(r)
        ]
    handles = {str(r.get("handle") or "") for r in rows}
    print(
        f"PS redownload products={len(rows)} handles={len(handles)} "
        f"workers={WORKERS} clothing={args.clothing} grey_only={args.grey_only}",
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
                if row.get("images") and row["images"] != raw[key].get("images"):
                    raw[key]["images"] = row["images"]
                    updated += 1
                if row.get("content") and row["content"] != raw[key].get(
                    "content"
                ):
                    raw[key]["content"] = row["content"]
                    updated += 1
                if row.get("entity") and not raw[key].get("entity"):
                    raw[key]["entity"] = row["entity"]
                    updated += 1
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
