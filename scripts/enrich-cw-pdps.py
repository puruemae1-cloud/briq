#!/usr/bin/env python3
"""Enrich all CW SKUs: gallery, strap variants, descriptions → cw-pdp-enriched.json"""
from __future__ import annotations

import json, re, time, html as H, urllib.request, urllib.parse
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
            with urllib.request.urlopen(req, timeout=50) as r:
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
    # if strike-through list present, first is list, sales follows — detect
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


def download_imgs(sku: str, urls: list[str]) -> list[str]:
    out = []
    folder = IMG / slugify(sku)
    folder.mkdir(parents=True, exist_ok=True)
    for i, url in enumerate(urls[:8], 1):
        url = H.unescape(url.split("?")[0]) + "?sw=1200&sh=1500"
        dest = folder / f"{i}.jpg"
        local = f"/products/cw-pdp/{slugify(sku)}/{i}.jpg"
        if dest.exists() and dest.stat().st_size > 3000:
            out.append(local)
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA["User-Agent"]})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            if len(data) > 1000:
                dest.write_bytes(data)
                out.append(local)
        except Exception:
            pass
    return out


def enrich_sku(sku: str) -> dict | None:
    try:
        data = fetch_json(f"{API}?pid={urllib.parse.quote(sku)}&quantity=1")
    except Exception as e:
        return {"sku": sku, "error": str(e)}
    p = data.get("product") or {}
    if not p.get("id"):
        return {"sku": sku, "error": "no-product"}

    gbp, list_gbp = parse_price(p)
    size = selected_attr(p, "WSize")
    colour = selected_attr(p, "WDialBezelColour")
    strap = selected_attr(p, "WStrapColourMaterialType")

    zoom = [i["url"] for i in (p.get("images") or {}).get("zoomImage") or []]
    if not zoom:
        zoom = [i["url"] for i in (p.get("images") or {}).get("large") or []]
    images = download_imgs(p["id"], zoom[:6])

    # Strap sister variants (same size+colour)
    strap_variants = []
    for a in p.get("variationAttributes") or []:
        if a.get("attributeId") != "WStrapColourMaterialType":
            continue
        for v in a.get("values") or []:
            if not v.get("selectable"):
                continue
            url = v.get("url")
            if not url:
                continue
            try:
                vd = fetch_json(url)
                vp = vd.get("product") or {}
                vgbp, vlist = parse_price(vp)
                vsku = vp.get("id") or sku
                # Prefer existing PLP hero; one PDP hero only if needed (no full gallery for sisters)
                plp = ROOT / "public/products/cw" / f"{slugify(vsku)}.jpg"
                if plp.exists() and plp.stat().st_size > 3000:
                    vimgs = [f"/products/cw/{slugify(vsku)}.jpg"]
                else:
                    vzoom = [i["url"] for i in (vp.get("images") or {}).get("large") or []][:1]
                    vimgs = download_imgs(vsku, vzoom) if vzoom else []
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
                    }
                )
                time.sleep(0.05)
            except Exception as e:
                strap_variants.append({"labelEn": v.get("displayValue"), "error": str(e)})

    # Bracelet resize fee (£10 on CW)
    has_resize = any(
        o.get("id") == "braceletResizing" for o in (p.get("options") or [])
    )

    features = p.get("productFeatures") or []
    if isinstance(features, list):
        features = [H.unescape(str(f)).replace("\xa0", " ").strip() for f in features if f]
    else:
        features = []

    return {
        "sku": p.get("id") or sku,
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
        "featuresEn": features,
        "images": images,
        "image": images[0] if images else None,
        "strapVariants": strap_variants,
        "braceletResize": has_resize,
        "braceletResizeFeeKrw": gbp_addon(10) if has_resize else 0,
        "inStock": bool(p.get("available") or p.get("inStock")),
        "collections": [],  # filled later
    }


def main():
    skus = [p["sku"] for p in RAW["products"] if p.get("sku")]
    # unique preserve order
    seen = set()
    ordered = []
    for s in skus:
        if s in seen:
            continue
        seen.add(s)
        ordered.append(s)

    results = {}
    if OUT.exists():
        try:
            prev = json.loads(OUT.read_text()).get("products") or {}
            for k, v in prev.items():
                if v and not v.get("error") and (v.get("images") or v.get("shortDescriptionEn")):
                    results[k] = v
            print("resume cached", len(results))
        except Exception:
            pass

    todo = [s for s in ordered if s not in results]
    print("enriching", len(todo), "skus (", len(ordered), "total)")
    processed = 0
    while todo:
        batch = todo[:24]
        todo = todo[24:]
        with ThreadPoolExecutor(max_workers=6) as ex:
            futs = {ex.submit(enrich_sku, sku): sku for sku in batch}
            for f in as_completed(futs):
                sku = futs[f]
                try:
                    results[sku] = f.result()
                except Exception as e:
                    results[sku] = {"sku": sku, "error": str(e)}
                processed += 1
                row = results.get(sku) or {}
                for sv in row.get("strapVariants") or []:
                    ssku = sv.get("sku")
                    if not ssku or ssku in results:
                        continue
                    results[ssku] = {
                        **{k: row.get(k) for k in (
                            "nameEn", "size", "colour", "shortDescriptionEn", "featuresEn",
                            "braceletResize", "braceletResizeFeeKrw", "collections", "primaryCollection",
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
                        "derivedFrom": sku,
                    }
        # drop sisters that were covered mid-flight
        todo = [s for s in todo if s not in results]
        print(" ", processed, "fetched, cached", len(results), "remaining", len(todo))
        OUT.write_text(json.dumps({"products": results}, ensure_ascii=False, indent=2))

    # attach collections from raw
    by_sku = {p["sku"]: p for p in RAW["products"]}
    for sku, row in results.items():
        src = by_sku.get(sku) or {}
        row["collections"] = src.get("collections") or []
        row["primaryCollection"] = src.get("primaryCollection")
        if not row.get("sourceUrl") and src.get("url"):
            row["sourceUrl"] = src["url"]

    OUT.write_text(json.dumps({"scrapedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "products": results}, ensure_ascii=False, indent=2))
    ok = sum(1 for v in results.values() if not v.get("error"))
    print("done ok", ok, "fail", len(results) - ok, "→", OUT)


if __name__ == "__main__":
    main()
