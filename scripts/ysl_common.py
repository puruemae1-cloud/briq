#!/usr/bin/env python3
"""Saint Laurent GB scrape helpers (Next.js + curl_cffi)."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from curl_cffi import requests

from ysl_config import BASE, IMG_ROOT, LOCALE, NEXT_BUILD, RAW_DIR

SESSION = requests.Session()
UA_HEADERS = {
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
}


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", (text or "").strip().lower()).strip("-")
    return s or "item"


def clean_html_text(html: str | None) -> str:
    if not html:
        return ""
    t = re.sub(r"<br\s*/?>", "\n", str(html), flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"&nbsp;", " ", t)
    t = re.sub(r"&amp;", "&", t)
    t = re.sub(r"&lt;", "<", t)
    t = re.sub(r"&gt;", ">", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _get(url: str, *, json_ok: bool = False, tries: int = 8) -> requests.Response:
    last: requests.Response | None = None
    headers = dict(UA_HEADERS)
    if json_ok:
        headers["x-nextjs-data"] = "1"
    for i in range(tries):
        try:
            r = SESSION.get(url, impersonate="chrome131", timeout=55, headers=headers)
            last = r
            if json_ok:
                if r.status_code == 200 and r.text.startswith("{"):
                    return r
            else:
                if r.status_code == 200 and (
                    len(r.text) > 80_000 or "__NEXT_DATA__" in r.text or r.text.startswith("{")
                ):
                    return r
                if r.status_code == 200 and len(r.content) > 1000 and "image" in (
                    r.headers.get("content-type") or ""
                ):
                    return r
        except Exception:
            pass
        time.sleep(1.2 + i * 0.6)
    if last is None:
        raise RuntimeError(f"fetch-failed {url}")
    return last


def fetch_plp_page(slug: str, *, page: int = 0, hits_per_page: int = 60) -> dict:
    url = (
        f"{BASE}/_next/data/{NEXT_BUILD}/{LOCALE}/ca/{slug}.json"
        f"?slug={slug}&page={page}&hitsPerPage={hits_per_page}"
    )
    r = _get(url, json_ok=True)
    return r.json()["pageProps"]


def iter_plp_products(slug: str, *, hits_per_page: int = 60, limit: int = 0) -> list[dict]:
    first = fetch_plp_page(slug, page=0, hits_per_page=hits_per_page)
    stats = first["results"]["stats"]
    products = list(first["results"]["products"] or [])
    prices = {p["id"]: p for p in (first["results"].get("prices") or []) if p.get("id")}
    hits = {h.get("objectID") or h.get("smId"): h for h in (first["results"].get("hitsAlgolia") or [])}
    nb_pages = int(stats.get("nbPages") or 1)
    for page in range(1, nb_pages):
        if limit and len(products) >= limit:
            break
        pp = fetch_plp_page(slug, page=page, hits_per_page=hits_per_page)
        products.extend(pp["results"]["products"] or [])
        for p in pp["results"].get("prices") or []:
            if p.get("id"):
                prices[p["id"]] = p
        for h in pp["results"].get("hitsAlgolia") or []:
            hits[h.get("objectID") or h.get("smId")] = h
        time.sleep(0.25)
    # attach price/stock hints
    out = []
    for p in products:
        pid = p.get("id")
        row = dict(p)
        if pid in prices:
            row["_price"] = prices[pid]
        if pid in hits:
            row["_hit"] = hits[pid]
        out.append(row)
        if limit and len(out) >= limit:
            break
    return out


def fetch_pdp(path: str) -> dict:
    """path like 'pr/foo-BAR.html' (no leading slash, no locale)."""
    path = path.lstrip("/")
    if path.startswith(f"{LOCALE}/"):
        path = path[len(LOCALE) + 1 :]
    url = f"{BASE}/_next/data/{NEXT_BUILD}/{LOCALE}/{path}.json"
    r = _get(url, json_ok=True)
    return r.json()["pageProps"]


def pdp_path_from_url(url: str) -> str:
    u = (url or "").strip()
    if u.startswith("http"):
        u = re.sub(r"^https?://[^/]+", "", u)
    u = u.split("?")[0].split("#")[0]
    if u.startswith(f"/{LOCALE}/"):
        u = u[len(LOCALE) + 2 :]
    return u.lstrip("/")


def best_image_urls(images: list[dict] | None, *, max_n: int = 12) -> list[str]:
    out: list[str] = []
    for img in images or []:
        src = img.get("src") or img.get("url") or ""
        if not src:
            continue
        # Prefer eCom / Large studio frames.
        src = re.sub(r"/(Small_thumbnail|Thumbnail|Small|Medium2?)/", "/eCom/", src)
        if src not in out:
            out.append(src)
        if len(out) >= max_n:
            break
    return out


def download_image(url: str, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 2500:
        return True
    try:
        r = _get(url, tries=5)
        if r.status_code != 200 or len(r.content) < 1500:
            return False
        dest.write_bytes(r.content)
        return True
    except Exception:
        return False


def materialize_images(sku: str, urls: list[str]) -> list[str]:
    folder = IMG_ROOT / slugify(sku)
    local: list[str] = []
    for i, url in enumerate(urls, start=1):
        dest = folder / f"{i}.jpg"
        if download_image(url, dest):
            local.append(f"/products/ys-pdp/{folder.name}/{i}.jpg")
        time.sleep(0.05)
    return local


def gbp_from_price_obj(price: dict | None) -> float | None:
    if not isinstance(price, dict):
        return None
    for key in ("salePriceValue", "listPriceValue"):
        v = price.get(key)
        if v is None:
            continue
        try:
            return float(v)
        except (TypeError, ValueError):
            continue
    return None


def scrape_leaf_rows(
    leaf: dict,
    *,
    limit: int = 0,
    skip_ids: set[str] | None = None,
    pdp: bool = True,
) -> list[dict]:
    skip_ids = skip_ids or set()
    slug = leaf["slug"]
    print(f"  PLP {leaf['id']} {slug}", flush=True)
    plp_rows = iter_plp_products(slug, limit=limit)
    print(f"  plp products={len(plp_rows)}", flush=True)
    rows: list[dict] = []
    for i, p in enumerate(plp_rows, start=1):
        pid = str(p.get("id") or "")
        if not pid or pid in skip_ids:
            continue
        url = p.get("url") or p.get("smcUrl") or ""
        source = urljoin(BASE, url) if url else ""
        path = pdp_path_from_url(url)
        price_obj = p.get("_price") or {}
        gbp = gbp_from_price_obj(price_obj)
        hit = p.get("_hit") or {}
        images = best_image_urls(p.get("images") or [])
        row: dict[str, Any] = {
            "id": pid,
            "sku": pid,
            "masterId": p.get("masterId"),
            "name": p.get("name") or p.get("shortName") or pid,
            "color": p.get("macroColor") or p.get("microColor") or p.get("color"),
            "microColor": p.get("microColor"),
            "colorCode": p.get("color"),
            "url": source,
            "path": path,
            "collections": list(leaf.get("collections") or []),
            "leafId": leaf["id"],
            "gbpPrice": gbp if gbp is not None else hit.get("price"),
            "inStock": bool(hit.get("inStock", True)),
            "compositions": p.get("compositions"),
            "imageUrls": images,
        }
        if pdp and path:
            try:
                pp = fetch_pdp(path)
                prod = pp.get("product") or {}
                variants = pp.get("variants") or {}
                price = pp.get("price") or price_obj
                row["gbpPrice"] = gbp_from_price_obj(price) or row.get("gbpPrice")
                row["description"] = prod.get("description") or ""
                row["shortDescription"] = prod.get("shortDescription") or []
                row["productCare"] = clean_html_text(prod.get("productCare"))
                row["compositions"] = prod.get("compositions") or row.get("compositions")
                row["madeIn"] = prod.get("madeIn")
                row["categories"] = prod.get("categories") or {}
                row["imageUrls"] = best_image_urls(prod.get("images") or images) or images
                # sizes
                sizes = []
                for s in variants.get("sizes") or []:
                    sizes.append(
                        {
                            "id": s.get("id"),
                            "value": s.get("value") or s.get("size"),
                            "displayValue": s.get("displayValue") or s.get("formattedSize"),
                            "inStock": bool(s.get("isComplete", True)),
                        }
                    )
                row["sizes"] = sizes
                # colourways (separate SMC URLs — keep for related)
                colors = []
                for c in variants.get("colors") or []:
                    colors.append(
                        {
                            "id": c.get("id") or c.get("smcId"),
                            "name": c.get("macroColor") or c.get("microColor"),
                            "url": urljoin(BASE, c.get("url") or ""),
                            "hex": c.get("microColorHexa"),
                        }
                    )
                row["colors"] = colors
                time.sleep(0.2)
            except Exception as e:
                row["pdpError"] = f"{type(e).__name__}: {e}"
                print(f"    WARN pdp {pid}: {e}", flush=True)
        # download images
        local = materialize_images(pid, row.get("imageUrls") or [])
        row["localImages"] = local
        rows.append(row)
        if i % 10 == 0 or i == len(plp_rows):
            print(f"    {i}/{len(plp_rows)} saved_rows={len(rows)}", flush=True)
        if limit and len(rows) >= limit:
            break
    return rows
