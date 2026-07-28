#!/usr/bin/env python3
"""Refresh CW PDP enrich: correct strap SKUs/images, full galleries, tech specs."""
from __future__ import annotations

import html as H
import json
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path("/Users/jeonghyunlee/Documents/briq")
RAW = json.loads((ROOT / "src/data/cw/cw-catalog-raw.json").read_text())
OUT = ROOT / "src/data/cw/cw-pdp-enriched.json"
IMG = ROOT / "public/products/cw-pdp"
IMG.mkdir(parents=True, exist_ok=True)

UA = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept": "application/json,text/javascript,*/*",
    "X-Requested-With": "XMLHttpRequest",
}
API = "https://www.christopherward.com/on/demandware.store/Sites-cwgross-Site/en_GB/Product-Variation"


def gbp_product(gbp: float) -> int:
    return int(round((gbp * 2100 * 1.05 + 200_000) / 10_000) * 10_000)


def gbp_addon(gbp: float) -> int:
    return int(round((gbp * 2100 * 1.05) / 10_000) * 10_000)


def slugify(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()


def fetch_json(url: str, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=55) as r:
                return json.load(r)
        except Exception:
            if i == retries - 1:
                raise
            time.sleep(1.2 * (i + 1))


def parse_price(product: dict):
    html = (product.get("price") or {}).get("html") or ""
    vals = re.findall(r'content="([\d.]+)"', html)
    if not vals:
        return None, None
    if "strike-through list" in html and len(vals) >= 2:
        return float(vals[1]), float(vals[0])
    return float(vals[0]), None


def selected_attr(product: dict, attr_id: str):
    for a in product.get("variationAttributes") or []:
        if a.get("attributeId") == attr_id or a.get("id") == attr_id:
            for v in a.get("values") or []:
                if v.get("selected"):
                    return v.get("displayValue") or v.get("value")
    return None


def sku_from_urls(urls: list[str], fallback: str) -> str:
    for u in urls:
        m = re.search(r"/WATCHES/([A-Za-z0-9][A-Za-z0-9\-]+)/", u)
        if m and "-" in m.group(1) and len(m.group(1)) > 8:
            return m.group(1)
    vid = fallback or ""
    if "-" in vid and len(vid) > 8:
        return vid
    return fallback


def collect_image_urls(product: dict) -> list[str]:
    urls: list[str] = []
    imgs = product.get("images") or {}
    for key in ("zoomImage", "large", "hiRes", "medium"):
        for i in imgs.get(key) or []:
            u = i.get("url") if isinstance(i, dict) else None
            if u:
                urls.append(u)
    for html_key in (
        "watchGalleryHtml",
        "secondaryWatchGalleryHtml",
        "imageCarouselHtml",
    ):
        html = product.get(html_key) or ""
        urls.extend(
            re.findall(
                r"https://www\.christopherward\.com/dw/image/[^\"'\s>]+",
                html,
            )
        )
    # de-dupe preserve order, drop tiny swatches
    out, seen = [], set()
    for u in urls:
        base = H.unescape(u.split("?")[0])
        if "/SWATCHES/" in base or base in seen:
            continue
        seen.add(base)
        out.append(base)
    return out[:16]


def download_imgs(sku: str, urls: list[str]) -> list[str]:
    out = []
    folder = IMG / slugify(sku)
    folder.mkdir(parents=True, exist_ok=True)
    for i, url in enumerate(urls[:16], 1):
        dest = folder / f"{i}.jpg"
        local = f"/products/cw-pdp/{slugify(sku)}/{i}.jpg"
        if dest.exists() and dest.stat().st_size > 2500:
            out.append(local)
            continue
        try:
            full = url + ("&" if "?" in url else "?") + "sw=1200&sh=1500"
            req = urllib.request.Request(full, headers={"User-Agent": UA["User-Agent"]})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            if len(data) > 1000:
                dest.write_bytes(data)
                out.append(local)
        except Exception:
            pass
    return out


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


def enrich_one(seed_sku: str) -> dict:
    data = fetch_json(f"{API}?pid={urllib.parse.quote(seed_sku)}&quantity=1")
    p = data.get("product") or {}
    if not p.get("id"):
        return {"sku": seed_sku, "error": "no-product"}

    remote_urls = collect_image_urls(p)
    real_sku = sku_from_urls(remote_urls, p.get("id") or seed_sku)
    # Prefer the seed full SKU when API collapses to master id
    if ("-" not in (p.get("id") or "") or len(p.get("id") or "") < 10) and "-" in seed_sku:
        real_sku = seed_sku

    gbp, list_gbp = parse_price(p)
    size = selected_attr(p, "WSize")
    colour = selected_attr(p, "WDialBezelColour")
    strap = selected_attr(p, "WStrapColourMaterialType")
    images = download_imgs(real_sku, remote_urls)

    strap_variants = []
    for a in p.get("variationAttributes") or []:
        if a.get("attributeId") != "WStrapColourMaterialType":
            continue
        for v in a.get("values") or []:
            if not v.get("selectable") or not v.get("url"):
                continue
            try:
                vd = fetch_json(v["url"])
                vp = vd.get("product") or {}
                vurls = collect_image_urls(vp)
                # Resolve real sellable SKU from image path / seed colour family
                vsku = sku_from_urls(vurls, vp.get("id") or "")
                if "-" not in vsku or len(vsku) < 10:
                    # Build from seed colour code when possible: keep dial part of seed
                    # e.g. C01-39AJH4-S00B0-MT → replace strap suffix using image folder
                    m = re.search(r"/WATCHES/([A-Za-z0-9\-]+)/", " ".join(vurls))
                    if m and "-" in m.group(1):
                        vsku = m.group(1)
                    elif colour and seed_sku.count("-") >= 3:
                        # keep same dial SKU prefix; leave for rebuild mapper
                        vsku = vp.get("id") or vsku
                vimgs = download_imgs(vsku, vurls) if vurls else []
                # If still master-only and no images, fall back to PLP hero for colour-matched full SKU later
                vgbp, vlist = parse_price(vp)
                strap_variants.append(
                    {
                        "sku": vsku,
                        "labelEn": v.get("displayValue") or v.get("value"),
                        "gbpPrice": vgbp,
                        "gbpListPrice": vlist,
                        "price": gbp_product(vgbp) if vgbp is not None else None,
                        "compareAtPrice": gbp_product(vlist)
                        if vlist and vgbp is not None and vlist > vgbp
                        else None,
                        "images": vimgs,
                        "image": vimgs[0] if vimgs else None,
                        "inStock": bool(vp.get("available") or vp.get("inStock")),
                        "sourceUrl": "https://www.christopherward.com"
                        + (vp.get("selectedProductUrl") or ""),
                        "colour": selected_attr(vp, "WDialBezelColour") or colour,
                        "size": selected_attr(vp, "WSize") or size,
                    }
                )
                time.sleep(0.05)
            except Exception as e:
                strap_variants.append({"labelEn": v.get("displayValue"), "error": str(e)})

    features = p.get("productFeatures") or []
    if isinstance(features, list):
        features = [H.unescape(str(f)).replace("\xa0", " ").strip() for f in features if f]
    else:
        features = []

    has_resize = any(o.get("id") == "braceletResizing" for o in (p.get("options") or []))

    return {
        "sku": real_sku,
        "seedSku": seed_sku,
        "nameEn": p.get("productName"),
        "size": size,
        "colour": colour,
        "strap": strap,
        "gbpPrice": gbp,
        "gbpListPrice": list_gbp,
        "price": gbp_product(gbp) if gbp is not None else None,
        "compareAtPrice": gbp_product(list_gbp)
        if list_gbp and gbp is not None and list_gbp > gbp
        else None,
        "shortDescriptionEn": H.unescape(p.get("shortDescription") or "").strip(),
        "longDescriptionEn": H.unescape(p.get("longDescription") or "").strip(),
        "featuresEn": features,
        "technicalsEn": parse_technicals(p),
        "images": images,
        "image": images[0] if images else None,
        "strapVariants": strap_variants,
        "braceletResize": has_resize,
        "braceletResizeFeeKrw": gbp_addon(10) if has_resize else 0,
        "inStock": bool(p.get("available") or p.get("inStock")),
        "sourceUrl": "https://www.christopherward.com" + (p.get("selectedProductUrl") or ""),
    }


def main():
    # One seed SKU per name+size+colour group from raw
    prev = {}
    if OUT.exists():
        try:
            prev = json.loads(OUT.read_text()).get("products") or {}
        except Exception:
            prev = {}

    # Prefer full SKUs
    seeds = []
    seen_group = set()
    for raw in RAW["products"]:
        sku = raw.get("sku") or ""
        if not sku or sku.count("-") < 2:
            continue
        name = raw.get("name") or ""
        # rough group from sku dial portion (drop last strap token)
        parts = sku.split("-")
        dial_key = "-".join(parts[:-1]) if len(parts) > 3 else sku
        g = f"{name}|{dial_key}"
        if g in seen_group:
            continue
        seen_group.add(g)
        seeds.append(sku)

    print("refreshing", len(seeds), "dial groups")
    results = dict(prev)
    done = 0
    with ThreadPoolExecutor(max_workers=5) as ex:
        futs = {ex.submit(enrich_one, sku): sku for sku in seeds}
        for f in as_completed(futs):
            seed = futs[f]
            try:
                row = f.result()
            except Exception as e:
                row = {"sku": seed, "error": str(e)}
            # Index under seed + resolved sku + all strap skus
            results[seed] = row
            if row.get("sku"):
                results[row["sku"]] = row
            for sv in row.get("strapVariants") or []:
                ssku = sv.get("sku")
                if not ssku:
                    continue
                results[ssku] = {
                    **{k: row.get(k) for k in (
                        "nameEn", "size", "colour", "shortDescriptionEn", "longDescriptionEn",
                        "featuresEn", "technicalsEn", "braceletResize", "braceletResizeFeeKrw",
                    )},
                    "sku": ssku,
                    "strap": sv.get("labelEn"),
                    "gbpPrice": sv.get("gbpPrice"),
                    "gbpListPrice": sv.get("gbpListPrice"),
                    "price": sv.get("price"),
                    "compareAtPrice": sv.get("compareAtPrice"),
                    "images": sv.get("images") or row.get("images"),
                    "image": sv.get("image") or row.get("image"),
                    "strapVariants": row.get("strapVariants"),
                    "inStock": sv.get("inStock", True),
                    "sourceUrl": sv.get("sourceUrl"),
                    "derivedFrom": row.get("sku") or seed,
                }
            done += 1
            if done % 10 == 0:
                print(" ", done, "/", len(seeds))
                OUT.write_text(
                    json.dumps({"products": results}, ensure_ascii=False, indent=2)
                )

    by_sku = {p["sku"]: p for p in RAW["products"]}
    for sku, row in results.items():
        src = by_sku.get(sku) or {}
        row["collections"] = src.get("collections") or row.get("collections") or []
        row["primaryCollection"] = src.get("primaryCollection") or row.get("primaryCollection")
        if not row.get("sourceUrl") and src.get("url"):
            row["sourceUrl"] = src["url"]

    OUT.write_text(
        json.dumps(
            {
                "scrapedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "products": results,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    ok = sum(1 for v in results.values() if not v.get("error") and v.get("images"))
    print("done indexed", len(results), "with images", ok, "→", OUT)


if __name__ == "__main__":
    main()
