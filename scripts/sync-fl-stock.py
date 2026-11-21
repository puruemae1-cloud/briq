#!/usr/bin/env python3
"""Sync Flannels catalogue size stock from live flannels.com PDPs.

Matches each Briq product's sourceUrl / colcode, parses escaped Next.js
variant payloads (`isOnStock` + `size` + `sku`), then updates:

  - variant.inStock  (by full Flannels SKU, then normalized size label)
  - product.inStock  (true iff any size variant is in stock)

Also adds missing in-stock sizes (cloned from a sibling variant) so sizes
that returned to Flannels stock become buyable on Briq again.

  python3 scripts/sync-fl-stock.py
  python3 scripts/sync-fl-stock.py --limit 20
  python3 scripts/sync-fl-stock.py --ids-file /tmp/fl-ids.txt
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from curl_cffi import requests as cffi_requests

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "src/data/fl/fl-catalog.json"
WORKERS = 8
TIMEOUT = 40

SIZE_PAIR_RE = re.compile(
    r'\\"isOnStock\\":(true|false),'
    r'\\"preorderAvailableDate\\":null,'
    r'\\"size\\":\\"([^\\"]+)\\",'
    r'\\"sku\\":\\"([^\\"]+)\\"'
)
# Fallback when field order differs
SIZE_LOOSE_RE = re.compile(
    r'\\"isOnStock\\":(true|false).{0,120}?\\"size\\":\\"([^\\"]+)\\".{0,60}?\\"sku\\":\\"([^\\"]+)\\"'
)


def normalize_size(label: str | None) -> str:
    if not label:
        return ""
    s = re.sub(r"\s+", " ", str(label)).strip().lower()
    s = s.replace("uk ", "uk").replace("eu ", "eu")
    return s


def size_keys(label: str | None) -> set[str]:
    """Match keys across Briq `UK 2 (EU 35)` and Flannels `2 (35)` / `4 (3XS)`."""
    if not label:
        return set()
    raw = str(label).strip()
    keys = {normalize_size(raw)}
    # Alpha tokens: XS / S / M / 3XS / 2XL …
    for tok in re.findall(r"\b([0-9]*x{0,2}s|x{0,2}l|m|one size|os)\b", raw, re.I):
        keys.add(f"alpha:{tok.lower()}")
    # Explicit UK
    m = re.search(r"\buk\s*([0-9]+(?:\.[0-9]+)?)\b", raw, re.I)
    if m:
        keys.add(f"uk:{m.group(1)}")
    # Leading number before paren — Flannels footwear/clothing "2 (35)" / "4 (3XS)"
    m = re.match(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*(?:\(|$)", raw)
    if m:
        keys.add(f"uk:{m.group(1)}")
        keys.add(f"num:{m.group(1)}")
    # Bare letter sizes
    if re.fullmatch(r"\s*(XXS|XS|S|M|L|XL|XXL|2XL|3XL|4XL|One Size|ONE SIZE)\s*", raw, re.I):
        keys.add(f"alpha:{raw.strip().lower().replace(' ', '')}")
    # EU in paren
    m = re.search(r"\(\s*(?:eu\s*)?([0-9]+(?:\.[0-9]+)?)\s*\)", raw, re.I)
    if m:
        keys.add(f"eu:{m.group(1)}")
    # Waist styles 28W R / 29 inch — keep normalized full string only
    return {k for k in keys if k}


def colcode_from_product(p: dict) -> str | None:
    sku = str(p.get("sku") or "")
    m = re.search(r"(\d{6,})", sku)
    if m:
        return m.group(1)
    src = p.get("sourceUrl") or ""
    qs = parse_qs(urlparse(src).fragment) or parse_qs(urlparse(src).query)
    if qs.get("colcode"):
        return qs["colcode"][0]
    m = re.search(r"colcode=(\d+)", src)
    if m:
        return m.group(1)
    m = re.search(r"-(\d{6,})$", p.get("id") or "")
    return m.group(1) if m else None


def pdp_url(p: dict) -> str | None:
    src = (p.get("sourceUrl") or "").strip()
    if src:
        # Strip hash for cleaner fetch; colcode still in query if present
        base = src.split("#")[0]
        code = colcode_from_product(p)
        if code and "colcode=" not in base:
            sep = "&" if "?" in base else "?"
            return f"{base}{sep}colcode={code}"
        return base
    code = colcode_from_product(p)
    if not code:
        return None
    # slug from id: fl-brand-...-CODE → brand-...-CODE without fl-
    slug = re.sub(r"^fl-", "", p.get("id") or "")
    return f"https://www.flannels.com/{slug}?colcode={code}"


def fetch_sizes(session: cffi_requests.Session, url: str) -> list[tuple[bool, str, str]]:
    r = session.get(
        url,
        timeout=TIMEOUT,
        headers={
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-GB,en;q=0.9",
            "Referer": "https://www.flannels.com/",
        },
    )
    if r.status_code != 200:
        raise RuntimeError(f"http {r.status_code}")
    t = r.text
    pairs = SIZE_PAIR_RE.findall(t)
    if not pairs:
        pairs = SIZE_LOOSE_RE.findall(t)
    out: list[tuple[bool, str, str]] = []
    seen: set[str] = set()
    for stock, size, sku in pairs:
        if sku in seen:
            continue
        seen.add(sku)
        out.append((stock == "true", size, sku))
    return out


def clone_variant(template: dict, *, product_id: str, size: str, sku: str, in_stock: bool) -> dict:
    size_slug = re.sub(r"[^a-z0-9]+", "", size.lower()) or sku[-4:]
    v = dict(template)
    v["id"] = f"{product_id}-{size_slug}"
    v["sku"] = sku
    v["size"] = size
    v["inStock"] = in_stock
    # Keep prices/images from template; tweak names
    base_name = re.sub(r"\s*[—-]\s*.*$", "", str(template.get("name") or product_id))
    base_ko = re.sub(r"\s*[—-]\s*.*$", "", str(template.get("nameKo") or base_name))
    v["name"] = f"{base_name} — {size}"
    v["nameKo"] = f"{base_ko} — {size}"
    return v


def apply_stock(p: dict, live: list[tuple[bool, str, str]]) -> dict:
    """Returns stats dict: matched, flipped_true, flipped_false, added, unchanged."""
    stats = {
        "matched": 0,
        "flipped_true": 0,
        "flipped_false": 0,
        "added": 0,
        "unchanged": 0,
        "live_in": 0,
        "live_out": 0,
    }
    if not live:
        return stats

    by_sku = {sku: (instock, size) for instock, size, sku in live}
    # Map every size key → (instock, sku, size_label); prefer in-stock on collision
    by_key: dict[str, tuple[bool, str, str]] = {}
    for instock, size, sku in live:
        for key in size_keys(size) | {normalize_size(size)}:
            prev = by_key.get(key)
            if prev is None or (instock and not prev[0]):
                by_key[key] = (instock, sku, size)
    stats["live_in"] = sum(1 for instock, _, _ in live if instock)
    stats["live_out"] = sum(1 for instock, _, _ in live if not instock)

    variants = list(p.get("variants") or [])
    matched_live_skus: set[str] = set()

    for v in variants:
        sku = str(v.get("sku") or "")
        size = str(v.get("size") or "")
        before = bool(v.get("inStock"))
        new_val = None
        live_sku = None
        if sku in by_sku:
            new_val, _ = by_sku[sku]
            live_sku = sku
        else:
            for key in size_keys(size):
                hit = by_key.get(key)
                if hit is not None:
                    new_val, live_sku, live_size = hit
                    # Prefer Flannels' own size label when ours was UK-prefixed
                    if live_size and size.startswith("UK ") and not live_size.upper().startswith("UK"):
                        pass  # keep Briq UK label for shoppers
                    break
        if new_val is None:
            # Successful live payload but this size absent → sold out on Flannels
            new_val = False
            stats["matched"] += 1
            if before:
                v["inStock"] = False
                stats["flipped_false"] += 1
            else:
                stats["unchanged"] += 1
            continue
        if live_sku:
            matched_live_skus.add(live_sku)
            # Keep Briq display size; refresh SKU to Flannels size SKU when synthetic
            if live_sku != sku and ("-UK" in sku or not re.search(r"\d{9,}", sku)):
                v["sku"] = live_sku
        stats["matched"] += 1
        if before == new_val:
            stats["unchanged"] += 1
        elif new_val:
            v["inStock"] = True
            stats["flipped_true"] += 1
        else:
            v["inStock"] = False
            stats["flipped_false"] += 1

    # Add live in-stock sizes Briq is missing (matched by no shared size key)
    template = variants[0] if variants else None
    if template is not None:
        existing_keys: set[str] = set()
        for v in variants:
            existing_keys |= size_keys(v.get("size"))
        existing_skus = {str(v.get("sku") or "") for v in variants}
        for instock, size, sku in live:
            if not instock:
                continue
            if sku in existing_skus or sku in matched_live_skus:
                continue
            if size_keys(size) & existing_keys:
                continue
            variants.append(
                clone_variant(
                    template,
                    product_id=p["id"],
                    size=size,
                    sku=sku,
                    in_stock=True,
                )
            )
            existing_keys |= size_keys(size)
            existing_skus.add(sku)
            stats["added"] += 1

    p["variants"] = variants
    if variants:
        p["inStock"] = any(bool(v.get("inStock")) for v in variants)
    elif live:
        # No variants listed — fall back to any live size in stock
        p["inStock"] = any(instock for instock, _, _ in live)
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=WORKERS)
    ap.add_argument("--ids-file", type=str, default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    products = json.loads(CATALOG.read_text())
    if not isinstance(products, list):
        print("catalog is not a list", file=sys.stderr)
        return 1

    if args.ids_file:
        want = {ln.strip() for ln in Path(args.ids_file).read_text().splitlines() if ln.strip()}
        targets = [p for p in products if p.get("id") in want]
    else:
        targets = list(products)
    if args.limit:
        targets = targets[: args.limit]

    print(f"syncing {len(targets)}/{len(products)} products workers={args.workers}", flush=True)

    session = cffi_requests.Session(impersonate="chrome")
    session.get("https://www.flannels.com/", timeout=TIMEOUT)

    by_id = {p["id"]: p for p in products}
    ok = fail = 0
    totals = {
        "flipped_true": 0,
        "flipped_false": 0,
        "added": 0,
        "matched": 0,
        "empty_live": 0,
    }

    def mark_all_oos(p: dict) -> None:
        p["inStock"] = False
        for v in p.get("variants") or []:
            v["inStock"] = False

    def one(p: dict):
        url = pdp_url(p)
        if not url:
            return p["id"], None, "no-url"
        last = ""
        for attempt in range(3):
            try:
                live = fetch_sizes(session, url)
                return p["id"], live, "ok"
            except Exception as e:
                last = f"{type(e).__name__}: {e}"
                time.sleep(0.6 * (attempt + 1))
        return p["id"], None, last

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(one, p): p["id"] for p in targets}
        done = 0
        for fut in as_completed(futs):
            pid, live, msg = fut.result()
            done += 1
            p = by_id[pid]
            if live is None:
                fail += 1
                print(f"FAIL {pid}: {msg}", flush=True)
                # Delisted / 404 on Flannels → sell out every size on Briq
                if "404" in msg or msg == "no-url":
                    mark_all_oos(p)
                    print(f"OOS {pid}: marked sold out after Flannels miss", flush=True)
            else:
                ok += 1
                if not live:
                    totals["empty_live"] += 1
                stats = apply_stock(p, live)
                for k in ("flipped_true", "flipped_false", "added", "matched"):
                    totals[k] += stats[k]
                if stats["flipped_true"] or stats["flipped_false"] or stats["added"]:
                    print(
                        f"UPD {pid}: +buyable={stats['flipped_true']} "
                        f"oos={stats['flipped_false']} added={stats['added']} "
                        f"live={stats['live_in']}/{stats['live_in']+stats['live_out']}",
                        flush=True,
                    )
            if done % 25 == 0 or done == len(targets):
                print(f"… {done}/{len(targets)} ok={ok} fail={fail}", flush=True)

    print(
        f"done ok={ok} fail={fail} matched={totals['matched']} "
        f"buyable={totals['flipped_true']} oos={totals['flipped_false']} "
        f"added={totals['added']} empty_live={totals['empty_live']}",
        flush=True,
    )
    if args.dry_run:
        print("dry-run — catalog not written", flush=True)
        return 0 if fail == 0 else 2

    CATALOG.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n")
    print(f"wrote {CATALOG}", flush=True)
    return 0 if fail < max(5, len(targets) * 0.1) else 2


if __name__ == "__main__":
    raise SystemExit(main())
