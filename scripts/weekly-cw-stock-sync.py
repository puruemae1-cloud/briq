#!/usr/bin/env python3
"""Weekly CW sync: refresh category PLPs, clearance/Nearly New, stock/prices.

Clearance notes (christopherward.com):
  - Sale PLP can be empty; `/sale` may redirect to `/watches`.
  - Scrape unions UpdateGrid + ShowAjax across sale / Nearly New filters.
  - Nearly New uniques that are OOS and off the live sale PLP are pruned
    (they do not restock — keeping them made Clearance look permanently sold-out).
  - New Nearly New SKUs are added when they reappear on the sale PLP.

  python3 scripts/weekly-cw-stock-sync.py
  python3 scripts/weekly-cw-stock-sync.py --clearance-only
"""
from __future__ import annotations

import argparse
import html as H
import json
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from studio_whiten import save_product_image  # noqa: E402

RAW_PATH = ROOT / "src/data/cw/cw-catalog-raw.json"
ENR_PATH = ROOT / "src/data/cw/cw-pdp-enriched.json"
IMG = ROOT / "public/products/cw-pdp"

UA = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept-Language": "en-GB,en;q=0.9",
}
DW = "https://www.christopherward.com/on/demandware.store/Sites-cwgross-Site/en_GB"
BASE = f"{DW}/Search-UpdateGrid"  # legacy alias; scrape_category tries UpdateGrid + ShowAjax
SHOW_AJAX = f"{DW}/Search-ShowAjax"
QV = f"{DW}/Product-ShowQuickView"
API = f"{DW}/Product-Variation"

CATEGORIES = [
    ("cw-new-releases", "new-watches", None),
    ("cw-bestsellers", "most-popular-watches", None),
    ("cw-hidden-gems", "hidden-gems", None),
    # Clearance uses scrape_clearance() — multi-endpoint (sale can be empty / redirect).
    ("cw-clearance", "sale", "prefn1=ID&prefv1=All%20watches"),
    ("cw-atelier", "atelier-watches", None),
    ("cw-dive", "dive-watches", None),
    ("cw-integrated-sports", "integrated-sports-watches", None),
    ("cw-adventure-field", "adventure-field-watches", None),
    ("cw-military", "military-watches", None),
    ("cw-bel-canto", "Bel-Canto-Watches", None),
    ("cw-sealander", "sealander", None),
    ("cw-twelve", "the-twelve-watches", None),
    ("cw-trident", "trident-watches", None),
    ("cw-moonphase", "moonphase-watches", None),
]

# CW sale/Nearly New PLPs have moved filters over time; try all known shapes.
CLEARANCE_SCRAPE_STRATEGIES: list[tuple[str, str | None]] = [
    ("sale", "prefn1=ID&prefv1=All%20watches"),
    ("sale", "prefn1=ID&prefv1=Nearly%20New"),
    ("sale", None),
    ("watches", "prefn1=ID&prefv1=Nearly%20New"),
]

COL_PRIORITY = [
    "cw-clearance",
    "cw-new-releases",
    "cw-bestsellers",
    "cw-hidden-gems",
    "cw-bel-canto",
    "cw-twelve",
    "cw-trident",
    "cw-sealander",
    "cw-moonphase",
    "cw-military",
    "cw-dive",
    "cw-integrated-sports",
    "cw-adventure-field",
    "cw-atelier",
]


def slugify(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            **UA,
            "Accept": "application/json,text/javascript,*/*",
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def is_watch_sku(pid: str) -> bool:
    if not re.match(r"^[CN]\d", pid):
        return False
    if re.match(r"^N\d{2}-(STL|TIT|RUB|HYB|MAS|TIDE)-", pid, re.I):
        return False
    return True


def is_full_watch_sku(pid: str) -> bool:
    """Configurable variant ids are full SKUs (C60-42AGM1-S0BW0-HB), not model codes (C642)."""
    s = (pid or "").strip()
    return is_watch_sku(s) and s.count("-") >= 2 and len(s) > 10


def _scrape_endpoint(endpoint: str, cgid: str, extra: str | None, sz: int = 36) -> list[str]:
    all_pids: list[str] = []
    start = 0
    while True:
        q = f"cgid={urllib.parse.quote(cgid)}&srule=most-popular&start={start}&sz={sz}"
        if extra:
            q = f"{q}&{extra}"
        html = fetch(f"{endpoint}?{q}")
        pids = list(dict.fromkeys(re.findall(r'data-pid="([^"]+)"', html)))
        if not pids:
            break
        all_pids.extend(pids)
        if len(pids) < sz:
            break
        start += sz
        time.sleep(0.1)
    seen: set[str] = set()
    out: list[str] = []
    for p in all_pids:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def scrape_category(cgid: str, extra: str | None, sz: int = 36) -> list[str]:
    """PLP scrape — try UpdateGrid first, fall back to ShowAjax (sale often empty on UpdateGrid)."""
    for endpoint in (BASE, SHOW_AJAX):
        pids = _scrape_endpoint(endpoint, cgid, extra, sz=sz)
        if pids:
            return pids
    return []


def scrape_clearance() -> list[str]:
    """Live clearance / Nearly New watches from every known CW sale PLP shape.

    christopherward.com `/sale` currently redirects when empty; UpdateGrid with
    cgid=sale often returns an empty fragment even when ShowAjax reports
    "no results". When Nearly New returns, any of these strategies may work —
    union them so weekly sync never misses restocks.
    """
    seen: set[str] = set()
    out: list[str] = []
    for cgid, extra in CLEARANCE_SCRAPE_STRATEGIES:
        for endpoint in (BASE, SHOW_AJAX):
            pids = _scrape_endpoint(endpoint, cgid, extra)
            for p in pids:
                if not is_watch_sku(p) or p in seen:
                    continue
                seen.add(p)
                out.append(p)
            if pids:
                label = extra or "(no filter)"
                print(f"    clearance via {endpoint.rsplit('/', 1)[-1]} cgid={cgid} {label}: +{len(pids)}")
    return out


def is_nearly_new_sku(sku: str, name: str = "") -> bool:
    return sku.upper().startswith("N") or "nearly new" in (name or "").lower()


def parse_price(product: dict) -> tuple[float | None, float | None]:
    price = product.get("price") or {}
    sales = price.get("sales") or {}
    lst = price.get("list") or {}
    sale_v = sales.get("value")
    list_v = lst.get("value")
    gbp = float(sale_v) if sale_v is not None else (float(list_v) if list_v is not None else None)
    list_gbp = float(list_v) if list_v is not None else None
    if list_gbp is not None and gbp is not None and list_gbp <= gbp:
        list_gbp = None
    return gbp, list_gbp


def download_imgs(sku: str, urls: list[str], *, force: bool = False) -> list[str]:
    out: list[str] = []
    folder = IMG / slugify(sku)
    folder.mkdir(parents=True, exist_ok=True)
    if force:
        for stale in folder.glob("*.jpg"):
            try:
                stale.unlink()
            except OSError:
                pass
    for i, url in enumerate(urls[:8], 1):
        url = H.unescape(url.split("?")[0]) + "?sw=1200&sh=1500"
        dest = folder / f"{i}.jpg"
        local = f"/products/cw-pdp/{slugify(sku)}/{i}.jpg"
        if not force and dest.exists() and dest.stat().st_size > 2500:
            out.append(local)
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA["User-Agent"]})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            if len(data) > 1000:
                save_product_image(dest, data)
                out.append(local)
        except Exception:
            pass
    return out


def ensure_product(raw: dict, sku: str, collection: str) -> dict:
    by = {p["sku"]: p for p in raw["products"]}
    if sku in by:
        return by[sku]

    print(f"  + new SKU {sku}")
    try:
        data = fetch_json(f"{QV}?pid={urllib.parse.quote(sku)}")
        prod = data.get("product") or {}
    except Exception as e:
        print(f"    QV ERR {e}")
        prod = {}

    gbp, list_gbp = parse_price(prod)
    name = (prod.get("productName") or sku).strip()
    images = prod.get("images") or {}
    large = images.get("large") or images.get("hi-res") or images.get("medium") or []
    img = ""
    if large and isinstance(large, list) and large[0].get("url"):
        img = large[0]["url"]
    url = ""
    sel = prod.get("selectedProductUrl") or prod.get("productUrl") or ""
    if sel:
        url = urllib.parse.urljoin("https://www.christopherward.com", sel.split("?")[0])

    p = {
        "sku": sku,
        "name": name,
        "subtitle": "",
        "url": url,
        "image": img,
        "badge": "Nearly New" if ("nearly new" in name.lower() or sku.upper().startswith("N")) else None,
        "gbpPrice": gbp,
        "gbpListPrice": list_gbp,
        "collections": [collection],
        "primaryCollection": collection,
        "inStock": bool(prod.get("available", True)),
    }
    raw["products"].append(p)
    time.sleep(0.12)
    return p


def selected_attr(product: dict, attr_id: str) -> str:
    for a in product.get("variationAttributes") or []:
        if a.get("attributeId") == attr_id or a.get("id") == attr_id:
            for v in a.get("values") or []:
                if v.get("selected"):
                    return str(v.get("displayValue") or v.get("value") or "").strip()
    return ""


def sync_gallery_and_enrich(sku: str, enr_products: dict, force: bool = False) -> dict:
    e = enr_products.setdefault(sku, {"sku": sku})
    folder = IMG / slugify(sku)
    good = [f for f in folder.glob("*.jpg") if f.stat().st_size >= 2500] if folder.exists() else []
    need_attrs = not (e.get("size") and e.get("strap"))
    if force or len(good) < 3 or need_attrs:
        try:
            data = fetch_json(f"{API}?pid={urllib.parse.quote(sku)}&quantity=1")
            ap = data.get("product") or {}
            zoom = [i["url"] for i in (ap.get("images") or {}).get("zoomImage") or []]
            if not zoom:
                zoom = [i["url"] for i in (ap.get("images") or {}).get("large") or []]
            if force or len(good) < 3:
                imgs = download_imgs(sku, zoom, force=force)
                if imgs:
                    e["images"] = imgs
            if ap.get("productName"):
                e["nameEn"] = ap["productName"]
            size = selected_attr(ap, "WSize")
            colour = selected_attr(ap, "WDialBezelColour")
            strap = selected_attr(ap, "WStrapColourMaterialType")
            if size:
                e["size"] = size
            if colour:
                e["colour"] = colour
            if strap:
                e["strap"] = strap
            time.sleep(0.1)
        except Exception as ex:
            print(f"  gallery ERR {sku}: {ex}")
    if not e.get("images"):
        e["images"] = [
            f"/products/cw-pdp/{slugify(sku)}/{f.name}"
            for f in sorted(good, key=lambda x: int(re.sub(r"\D", "", x.stem) or "0"))
        ]
    return e


def fetch_stock(sku: str) -> dict:
    """Return {sku, available, gbp, list_gbp, name} or error."""
    try:
        data = fetch_json(f"{QV}?pid={urllib.parse.quote(sku)}")
        prod = data.get("product") or {}
        gbp, list_gbp = parse_price(prod)
        return {
            "sku": sku,
            "available": bool(prod.get("available")),
            "gbp": gbp,
            "list_gbp": list_gbp,
            "name": (prod.get("productName") or "").strip(),
            "ok": True,
        }
    except Exception as e:
        return {"sku": sku, "ok": False, "error": str(e), "available": False}


def variation_urls(product: dict) -> list[str]:
    urls: list[str] = []
    for attr in product.get("variationAttributes") or []:
        for v in attr.get("values") or []:
            if not isinstance(v, dict):
                continue
            if not v.get("selectable"):
                continue
            u = v.get("url")
            if isinstance(u, str) and u.strip():
                urls.append(u.strip())
    # stable uniq
    out: list[str] = []
    seen: set[str] = set()
    for u in urls:
        if u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out


def discover_family_skus(seed_sku: str, max_requests: int = 40, timeout_s: float = 45.0) -> list[str]:
    """Discover sibling SKUs across selectable variation URLs (size/strap axes).

    Soft-timeout per seed so one hung CW variation crawl cannot stall the weekly job.
    """
    deadline = time.monotonic() + timeout_s
    out: list[str] = []
    seen_sku: set[str] = set()
    seen_url: set[str] = set()

    try:
        root = fetch_json(f"{API}?pid={urllib.parse.quote(seed_sku)}&quantity=1").get("product") or {}
    except Exception:
        return []

    root_id = str(root.get("id") or seed_sku).strip()
    if is_full_watch_sku(root_id):
        out.append(root_id)
        seen_sku.add(root_id)

    queue = variation_urls(root)
    for u in queue:
        seen_url.add(u)

    reqs = 0
    while queue and reqs < max_requests:
        if time.monotonic() > deadline:
            print(f"  family timeout seed={seed_sku} after {reqs} reqs", flush=True)
            break
        u = queue.pop(0)
        reqs += 1
        try:
            row = fetch_json(u).get("product") or {}
        except Exception:
            continue
        rid = str(row.get("id") or "").strip()
        if is_full_watch_sku(rid) and rid not in seen_sku:
            seen_sku.add(rid)
            out.append(rid)
        for nu in variation_urls(row):
            if nu in seen_url:
                continue
            seen_url.add(nu)
            queue.append(nu)
        time.sleep(0.03)
    return out


def rebuild_collections(raw: dict) -> None:
    membership: dict[str, list[str]] = {}
    for cat, skus in raw["categories"].items():
        for sku in skus:
            membership.setdefault(sku, []).append(cat)

    for p in raw["products"]:
        cols = list(dict.fromkeys(membership.get(p["sku"], [])))
        if cols:
            p["collections"] = cols
            p["primaryCollection"] = next((c for c in COL_PRIORITY if c in cols), cols[0])
        else:
            new = [c for c in (p.get("collections") or []) if c != "cw-clearance"]
            p["collections"] = new
            if p.get("primaryCollection") == "cw-clearance":
                p["primaryCollection"] = new[0] if new else None


def main() -> int:
    from weekly_korean_gate import check_new_korean, utc_now_iso

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--family-only",
        action="store_true",
        help="Skip PLP scrape; expand size/strap families then rebuild.",
    )
    ap.add_argument(
        "--skip-family",
        action="store_true",
        help="Skip new-release family expansion (faster; clearance/stock still run).",
    )
    ap.add_argument(
        "--clearance-only",
        action="store_true",
        help="Only refresh clearance PLP membership + stock for clearance SKUs, then rebuild.",
    )
    args = ap.parse_args()

    since = utc_now_iso()
    raw = json.loads(RAW_PATH.read_text())
    enr = json.loads(ENR_PATH.read_text()) if ENR_PATH.exists() else {"scrapedAt": "", "products": {}}
    enr_products = enr.setdefault("products", {})

    summary = {
        "added": [],
        "restocked": [],
        "sold_out": [],
        "pruned": [],
        "live_clearance": 0,
    }

    print("1) Scraping CW category PLPs…")
    live: dict[str, list[str]] = {}
    if args.family_only:
        print("  skip PLP scrape (--family-only)", flush=True)
        for briq_id, _, _ in CATEGORIES:
            live[briq_id] = [s for s in (raw["categories"].get(briq_id) or []) if is_watch_sku(s)]
        print("2) Merging category membership… skip")
    elif args.clearance_only:
        print("  clearance-only mode", flush=True)
        for briq_id, _, _ in CATEGORIES:
            live[briq_id] = [s for s in (raw["categories"].get(briq_id) or []) if is_watch_sku(s)]
        live["cw-clearance"] = scrape_clearance()
        print(f"  cw-clearance: {len(live['cw-clearance'])} watches")
        print("2) Merging clearance membership…")
        by_prev = {p["sku"]: p for p in raw["products"]}
        prev = list(raw["categories"].get("cw-clearance", []))
        watches = live["cw-clearance"]
        keep = []
        for s in prev:
            if s in watches or not is_watch_sku(s):
                continue
            row = by_prev.get(s) or {}
            if row.get("inStock") is True:
                keep.append(s)
        merged = list(dict.fromkeys(watches + keep))
        added = [s for s in watches if s not in prev]
        dropped = [s for s in prev if s not in merged]
        if dropped:
            summary["pruned"].extend(dropped)
            print(f"  cw-clearance pruned {len(dropped)} off-PLP OOS: {dropped[:8]}")
        raw["categories"]["cw-clearance"] = merged
        raw["categoryCounts"]["cw-clearance"] = len(merged)
        if added:
            print(f"  cw-clearance +{len(added)} {added[:8]}")
            summary["added"].extend(added)
        summary["live_clearance"] = len(watches)
    else:
        for briq_id, cgid, extra in CATEGORIES:
            if briq_id == "cw-clearance":
                watches = scrape_clearance()
            else:
                pids = scrape_category(cgid, extra)
                watches = [p for p in pids if is_watch_sku(p)]
            live[briq_id] = watches
            print(f"  {briq_id}: {len(watches)} watches")

        print("2) Merging category membership…")
        by_prev = {p["sku"]: p for p in raw["products"]}
        for briq_id, watches in live.items():
            prev = list(raw["categories"].get(briq_id, []))
            if briq_id == "cw-clearance":
                # Keep only previous clearance SKUs that are still buyable.
                # Nearly New pieces are unique — once off the live sale PLP and
                # OOS they will not restock; keeping them forever made Clearance
                # look permanently sold-out even when CW sale was empty.
                keep = []
                for s in prev:
                    if s in watches or not is_watch_sku(s):
                        continue
                    row = by_prev.get(s) or {}
                    if row.get("inStock") is True:
                        keep.append(s)
                merged = list(dict.fromkeys(watches + keep))
                added = [s for s in watches if s not in prev]
                dropped = [s for s in prev if s not in merged]
                if dropped:
                    summary["pruned"].extend(dropped)
                    print(f"  cw-clearance pruned {len(dropped)} off-PLP OOS: {dropped[:8]}")
            else:
                merged = list(dict.fromkeys(prev + watches))
                added = [s for s in watches if s not in prev]
            raw["categories"][briq_id] = merged
            raw["categoryCounts"][briq_id] = len(merged)
            if added:
                print(f"  {briq_id} +{len(added)} {added[:8]}")
                if briq_id == "cw-clearance":
                    summary["added"].extend(added)

    summary["live_clearance"] = len(live["cw-clearance"])

    # Step 3: ensure product rows + downloadable PDP galleries for any SKU that
    # exists on the official CW PLPs but is missing from our catalog row store.
    #
    # Previously we only ensured clearance ("cw-clearance") new SKUs, which
    # meant newly announced watches (e.g. Trident) could appear on PLPs
    # (and in category membership) but never become real PDP products because
    # we didn't download images / create the raw["products"] row.
    print("3) Ensuring product rows for newly seen SKUs…")
    by = {p["sku"]: p for p in raw["products"]}

    all_cat_skus: set[str] = set()
    for skus in raw["categories"].values():
        all_cat_skus.update(skus)

    new_skus = sorted([sku for sku in all_cat_skus if sku not in by])
    print(f"  missing products: {len(new_skus)}")

    def primary_collection_for(sku: str) -> str:
        # Pick the highest priority category where this SKU is present.
        for c in COL_PRIORITY:
            if sku in raw["categories"].get(c, []):
                return c
        return COL_PRIORITY[-1]

    for sku in new_skus:
        primary = primary_collection_for(sku)
        ensure_product(raw, sku, primary)
        by = {p["sku"]: p for p in raw["products"]}
        sync_gallery_and_enrich(sku, enr_products, force=True)

    # Also expand new-release families so dial size × strap siblings do not get
    # dropped when PLP only lists a subset of configurable options.
    if args.skip_family or args.clearance_only:
        print("3b) Expanding new-release variant families… skip", flush=True)
    else:
        print("3b) Expanding new-release variant families (size/strap)…")
        family_added = 0
        seeds = list(dict.fromkeys(raw["categories"].get("cw-new-releases", [])))
        for i, seed in enumerate(seeds, 1):
            if not is_full_watch_sku(seed):
                continue
            siblings = discover_family_skus(seed)
            if i % 5 == 0:
                print(
                    f"  family {i}/{len(seeds)} seed={seed} found={len(siblings)} added={family_added}",
                    flush=True,
                )
            if not siblings:
                continue
            seed_row = by.get(seed) or {}
            seed_cols = list(seed_row.get("collections") or [primary_collection_for(seed)])
            for sib in siblings:
                if sib in by:
                    continue
                primary = primary_collection_for(seed)
                ensure_product(raw, sib, primary)
                by = {p["sku"]: p for p in raw["products"]}
                sib_row = by.get(sib)
                if sib_row:
                    sib_row["collections"] = list(dict.fromkeys(seed_cols + [primary]))
                    sib_row["primaryCollection"] = seed_row.get("primaryCollection") or primary
                sync_gallery_and_enrich(sib, enr_products, force=True)
                family_added += 1
            sync_gallery_and_enrich(seed, enr_products, force=False)
            RAW_PATH.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n")
            ENR_PATH.write_text(json.dumps(enr, indent=2, ensure_ascii=False) + "\n")
        if family_added:
            print(f"  + family siblings added {family_added}")

    rebuild_collections(raw)

    print("4) Refreshing stock + prices…")
    if args.clearance_only:
        stock_skus = sorted(
            {
                s
                for s in raw["categories"].get("cw-clearance", [])
                if is_full_watch_sku(s)
            }
            | {
                # Also re-check any previously known NN that we just pruned, so
                # restocks aren't missed if QV flips before the next PLP list.
                p["sku"]
                for p in raw["products"]
                if is_nearly_new_sku(p.get("sku") or "", p.get("name") or "")
                and is_full_watch_sku(p.get("sku") or "")
            }
        )
        print(f"  clearance-only stock targets: {len(stock_skus)}", flush=True)
    else:
        stock_skus = sorted(
            {p["sku"] for p in raw["products"] if is_full_watch_sku(p.get("sku") or "")}
        )

    results: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(fetch_stock, s): s for s in stock_skus}
        done = 0
        for fut in as_completed(futs):
            row = fut.result()
            results[row["sku"]] = row
            done += 1
            if done % 40 == 0:
                print(f"  stock {done}/{len(stock_skus)}")

    by = {p["sku"]: p for p in raw["products"]}
    for sku, row in results.items():
        if not row.get("ok"):
            # Treat fetch failure as sold out only for clearance Nearly New previously known
            if sku in raw["categories"].get("cw-clearance", []):
                p = by.get(sku)
                if p is not None:
                    prev = bool(p.get("inStock", True))
                    p["inStock"] = False
                    enr_products.setdefault(sku, {"sku": sku})["inStock"] = False
                    if prev:
                        summary["sold_out"].append(sku)
            continue

        p = by.get(sku)
        if p is None:
            continue
        avail = bool(row["available"])
        prev = p.get("inStock")
        # Default unknown previous to True so first sold-out transition is logged
        if prev is None:
            prev = True
        p["inStock"] = avail
        if row.get("gbp") is not None:
            p["gbpPrice"] = row["gbp"]
        if row.get("list_gbp") is not None:
            p["gbpListPrice"] = row["list_gbp"]
        if row.get("name") and not p.get("name"):
            p["name"] = row["name"]

        e = enr_products.setdefault(sku, {"sku": sku})
        e["inStock"] = avail
        if row.get("gbp") is not None:
            e["gbpPrice"] = row["gbp"]
        if row.get("list_gbp") is not None:
            e["gbpListPrice"] = row["list_gbp"]
        if row.get("name"):
            e["nameEn"] = row["name"]
        e["collections"] = list(p.get("collections") or e.get("collections") or [])
        e["primaryCollection"] = p.get("primaryCollection") or e.get("primaryCollection")

        if sku in raw["categories"].get("cw-clearance", []):
            if avail and not prev:
                summary["restocked"].append(sku)
            if (not avail) and prev:
                summary["sold_out"].append(sku)

    # After stock refresh: drop clearance SKUs that are OOS and not on the live
    # sale PLP (Nearly New uniques will not return; stale OOS cluttered the PLP).
    live_clearance = set(live.get("cw-clearance") or [])
    clearance_now = list(raw["categories"].get("cw-clearance") or [])
    pruned_after: list[str] = []
    kept_clearance: list[str] = []
    by = {p["sku"]: p for p in raw["products"]}
    for sku in clearance_now:
        if sku in live_clearance:
            kept_clearance.append(sku)
            continue
        row = by.get(sku) or {}
        if row.get("inStock") is True:
            kept_clearance.append(sku)
            continue
        pruned_after.append(sku)
    if pruned_after:
        raw["categories"]["cw-clearance"] = list(dict.fromkeys(kept_clearance))
        raw["categoryCounts"]["cw-clearance"] = len(raw["categories"]["cw-clearance"])
        for sku in pruned_after:
            if sku not in summary["pruned"]:
                summary["pruned"].append(sku)
        print(f"  pruned {len(pruned_after)} OOS off-PLP from clearance after stock refresh")
        rebuild_collections(raw)

    raw["scrapedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    enr["scrapedAt"] = raw["scrapedAt"]
    RAW_PATH.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n")
    ENR_PATH.write_text(json.dumps(enr, indent=2, ensure_ascii=False) + "\n")

    print("5) Filling missing editorial + PDP copy…")
    if args.clearance_only:
        print("  skip enrich (--clearance-only)", flush=True)
    else:
        subprocess.check_call(
            [sys.executable, str(ROOT / "scripts/enrich-cw-missing-editorial-and-copy.py")],
            cwd=str(ROOT),
        )

    print("6) Rebuilding cw-catalog.ts…")
    subprocess.check_call([sys.executable, str(ROOT / "scripts/rebuild-cw-catalog.py")], cwd=str(ROOT))

    if args.clearance_only:
        print("7) Syncing CW watch straps… skip (--clearance-only)")
        print("8) Refreshing homepage rail picks… skip (--clearance-only)")
    else:
        print("7) Syncing CW watch straps (SRP×2100)…")
        subprocess.check_call([sys.executable, str(ROOT / "scripts/sync-cw-straps.py")], cwd=str(ROOT))

        print("8) Refreshing homepage rail picks (watches → CW New Releases)…")
        subprocess.check_call(
            [sys.executable, str(ROOT / "scripts/refresh-homepage-rail-picks.py")],
            cwd=str(ROOT),
        )

    if not args.clearance_only:
        check_new_korean("cw", since)

    by = {p["sku"]: p for p in raw["products"]}
    print("\n=== Weekly CW sync summary ===")
    print(f"Live clearance watches (CW sale PLP): {summary['live_clearance']}")
    print(f"Clearance listed on Briq: {len(raw['categories']['cw-clearance'])}")
    print(f"Added: {summary['added'] or '—'}")
    print(f"Restocked: {summary['restocked'] or '—'}")
    print(f"Sold out: {summary['sold_out'] or '—'}")
    print(f"Pruned (OOS + off sale PLP): {summary['pruned'] or '—'}")
    in_stock = sum(
        1
        for s in raw["categories"]["cw-clearance"]
        if (by.get(s) or {}).get("inStock") is True
    )
    print(f"Clearance in stock now: {in_stock}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
