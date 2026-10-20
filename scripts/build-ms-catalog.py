#!/usr/bin/env python3
"""Build the Mismo bags catalogue from mismo.dk.

Colourways stay as the official site lists them (one product page per colour).
Belts keep the size options on that same page. Gift cards are skipped.
KRW = round(GBP × 2000 × 1.05) to the nearest 1,000.
"""

from __future__ import annotations

import html
import http.cookiejar
import json
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src/data/ms/ms-catalog.json"
CACHE = ROOT / "src/data/ms/ms-translate-cache.json"
IMG_ROOT = ROOT / "public/products/ms-pdp"
RAW = ROOT / "src/data/ms/ms-raw.json"

NAV = [
    ("ms-suit-carriers", "수트 캐리어", {"suit carrier"}),
    ("ms-washbags", "워시백", {"washbag"}),
    ("ms-cardholders", "카드홀더", {"cardholder"}),
    ("ms-home-storage", "홈 스토리지", {"storage"}),
    ("ms-pouches", "파우치 & 커버", {"pouch", "pouches & covers"}),
    ("ms-backpacks", "백팩", {"backpacks"}),
    ("ms-briefcases", "브리프케이스", {"briefcases", "briefcase"}),
    ("ms-crossbody", "크로스바디", {"cross body"}),
    ("ms-totes", "토트백", {"totebags", "tote bags", "tote bag"}),
    ("ms-weekend", "위켄드백", {"travel bags", "travel bag"}),
    ("ms-belts", "벨트 & 액세서리", {"accessories", "accessories aw18", "accessories aw19", "accessories aw20"}),
]


def opener():
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    op.addheaders = [("User-Agent", "Mozilla/5.0")]
    data = urllib.parse.urlencode(
        {"form_type": "localization", "utf8": "✓", "_method": "put", "country_code": "GB"}
    ).encode()
    op.open(
        urllib.request.Request("https://www.mismo.dk/localization", data=data, method="POST"),
        timeout=40,
    )
    return op


def get_json(op, url: str):
    with op.open(url, timeout=60) as res:
        return json.loads(res.read().decode())


def krw(gbp: float) -> int:
    return int(round(float(gbp) * 2000 * 1.05 / 1000.0) * 1000)


def plain(fragment: str) -> str:
    text = re.sub(r"(?i)<br\s*/?>", "\n", fragment or "")
    text = re.sub(r"(?i)</p>", "\n\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def gtx(text: str, cache: dict[str, str]) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    if text in cache and cache[text]:
        return cache[text]
    q = urllib.parse.quote(text[:4500])
    url = (
        "https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl=en&tl=ko&dt=t&q={q}"
    )
    last = ""
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=25) as res:
                data = json.loads(res.read().decode())
            out = "".join(part[0] for part in data[0] if part and part[0])
            out = out.strip()
            if out:
                cache[text] = out
                time.sleep(0.15)
                return out
        except Exception as exc:  # noqa: BLE001
            last = str(exc)
            time.sleep(1.5 * (attempt + 1))
    raise SystemExit(f"translate failed: {last[:120]} :: {text[:80]}")


def collection_map(op) -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    for handle in (
        "backpacks",
        "briefcases",
        "weekend-bags",
        "tote-bags",
        "cross-body",
        "suit-carriers",
        "washbags",
        "storage",
        "laptop-covers",
        "pouches",
        "wallets-and-cardholders",
        "accessories",
        "belts",
    ):
        page = 1
        while True:
            batch = get_json(
                op,
                f"https://www.mismo.dk/collections/{handle}/products.json?limit=250&page={page}",
            )["products"]
            for product in batch:
                found.setdefault(product["handle"], set()).add(handle)
            if len(batch) < 250:
                break
            page += 1
    return found


BAG_TYPES = {
    "backpacks",
    "briefcases",
    "briefcase",
    "totebags",
    "tote bags",
    "tote bag",
    "travel bags",
    "travel bag",
    "cross body",
    "suit carrier",
}


def subcategory(product_type: str, handle: str, cols: set[str]) -> str:
    key = (product_type or "").strip().lower()
    bag_cols = cols & {
        "backpacks",
        "briefcases",
        "weekend-bags",
        "tote-bags",
        "cross-body",
        "suit-carriers",
    }
    # Home storage pieces are sometimes typed as totes on Shopify.
    if "storage" in cols and not bag_cols:
        return "ms-home-storage"
    # Belt bags are filed under Cross body on the official site, not Backpacks.
    if cols == {"cross-body"}:
        return "ms-crossbody"
    if key not in BAG_TYPES:
        if "washbags" in cols:
            return "ms-washbags"
        if "storage" in cols:
            return "ms-home-storage"
        if "wallets-and-cardholders" in cols:
            return "ms-cardholders"
        if "pouches" in cols or "laptop-covers" in cols:
            return "ms-pouches"
    for sub, _label, types in NAV:
        if key in types:
            return sub
    return "ms-belts"


def split_title(title: str) -> tuple[str, str]:
    parts = re.split(r"\s+[–—-]\s+", title, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return title.strip(), ""


def fetch_products(op) -> list[dict]:
    products = []
    page = 1
    while True:
        batch = get_json(
            op,
            f"https://www.mismo.dk/collections/all/products.json?limit=250&page={page}",
        )["products"]
        if not batch:
            break
        products.extend(batch)
        if len(batch) < 250:
            break
        page += 1
    return [p for p in products if (p.get("product_type") or "").lower() != "gift card"]


def save_image(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 1000:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    src = url.split("?")[0] + "?width=2000"
    req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as res:
        data = res.read()
    dest.write_bytes(data)


def main() -> None:
    op = opener()
    products = fetch_products(op)
    columns = collection_map(op)
    print(f"products {len(products)}", flush=True)
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(products), encoding="utf-8")

    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    texts: list[str] = []
    for product in products:
        model, color = split_title(product["title"])
        texts.append(model)
        if color:
            texts.append(color)
        body = plain(product.get("body_html") or "")
        if body:
            texts.append(body)
        material = ""
        for opt in product.get("options") or []:
            if opt.get("name") == "Material" and opt.get("values"):
                material = opt["values"][0]
        if material:
            texts.append(material)
    unique = [t for t in dict.fromkeys(texts) if t not in cache]
    print(f"translate {len(unique)} new / {len(set(texts))} unique", flush=True)
    for i, text in enumerate(unique, 1):
        gtx(text, cache)
        if i % 20 == 0:
            CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  translated {i}/{len(unique)}", flush=True)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")

    jobs = []
    catalog = []
    registered = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    for product in products:
        handle = product["handle"]
        pid = "ms-" + handle
        model, color = split_title(product["title"])
        model_ko = cache.get(model, model)
        color_ko = cache.get(color, color) if color else ""
        name_ko = f"{model_ko} – {color_ko}" if color_ko else model_ko
        body = plain(product.get("body_html") or "")
        description = cache.get(body, "") if body else ""
        material = ""
        for opt in product.get("options") or []:
            if opt.get("name") == "Material" and opt.get("values"):
                material = opt["values"][0]
        material_ko = cache.get(material, material) if material else ""
        images = product.get("images") or []
        rels = []
        for index, image in enumerate(images, 1):
            ext = ".png" if ".png" in image["src"].lower() else ".jpg"
            rel = f"/products/ms-pdp/{handle}/{index}{ext}"
            rels.append(rel)
            jobs.append((image["src"], IMG_ROOT / handle / f"{index}{ext}"))
        if not rels:
            print("skip no image", handle)
            continue
        variants = []
        for variant in product["variants"]:
            gbp = float(variant["price"])
            size = variant["title"] if variant["title"] not in ("Default Title",) and len(product["variants"]) > 1 else ""
            label = size or color or model
            label_ko = size or color_ko or model_ko
            variants.append(
                {
                    "id": f"{pid}-{variant['id']}",
                    "name": label,
                    "nameKo": label_ko,
                    "sku": variant.get("sku") or str(variant["id"]),
                    "gbpPrice": gbp,
                    "price": krw(gbp),
                    "image": rels[0],
                    "images": rels,
                    "sourceUrl": f"https://www.mismo.dk/products/{handle}",
                    "inStock": bool(variant.get("available")),
                    **({"size": size, "colorNameKo": color_ko} if size else {"colorNameKo": color_ko}),
                }
            )
        lead = variants[0]
        specs = []
        if material_ko:
            specs.append({"labelKo": "소재", "valueKo": material_ko})
        if color_ko:
            specs.append({"labelKo": "컬러", "valueKo": color_ko})
        grams = product["variants"][0].get("grams") or 0
        if grams:
            specs.append({"labelKo": "무게", "valueKo": f"{grams / 1000:g}kg" if grams >= 1000 else f"{grams}g"})
        sub = subcategory(product.get("product_type") or "", handle, columns.get(handle, set()))
        catalog.append(
            {
                "id": pid,
                "name": product["title"],
                "nameKo": name_ko,
                "brand": "Mismo",
                "price": lead["price"],
                "gbpPrice": lead["gbpPrice"],
                "category": "bags",
                "subcategory": sub,
                "tags": ["mismo", sub],
                "descriptionKo": description,
                "featuresKo": [line for line in [material_ko, color_ko] if line],
                "techSpecs": specs,
                "image": rels[0],
                "images": rels,
                "hoverImage": rels[1] if len(rels) > 1 else rels[0],
                "accent": "#1F3A34",
                "sku": lead["sku"],
                "sourceUrl": f"https://www.mismo.dk/products/{handle}",
                "inStock": any(v["inStock"] for v in variants),
                "registeredAt": registered,
                "variants": variants,
            }
        )

    print(f"download {len(jobs)} images", flush=True)
    failed = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(save_image, url, dest): dest for url, dest in jobs}
        done = 0
        for future in as_completed(futures):
            done += 1
            try:
                future.result()
            except Exception as exc:  # noqa: BLE001
                failed += 1
                print("image fail", futures[future], exc)
            if done % 100 == 0:
                print(f"  images {done}/{len(jobs)}", flush=True)
    OUT.write_text(json.dumps(catalog, ensure_ascii=False, indent=1), encoding="utf-8")
    from collections import Counter
    print("wrote", len(catalog), "image fails", failed)
    print(Counter(p["subcategory"] for p in catalog))


if __name__ == "__main__":
    main()
