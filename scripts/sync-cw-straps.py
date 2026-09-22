#!/usr/bin/env python3
"""Sync Christopher Ward watch straps → Briq cw-straps category.

Source: https://www.christopherward.com/watch-straps?start=0&sz=60
Pricing: KRW = round(GBP × 2100 / 1000) × 1000  (no 1.16 / no +200k / no 1.05)
"""

from __future__ import annotations

import html as H
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from studio_whiten import save_product_image  # noqa: E402

RAW_PATH = ROOT / "src/data/cw/cw-straps-raw.json"
CATALOG_TS = ROOT / "src/data/cw/cw-straps-catalog.ts"
TX_CACHE_PATH = ROOT / "src/data/cw/cw-translate-cache.json"
IMG = ROOT / "public/products/cw-pdp"

UA = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept-Language": "en-GB,en;q=0.9",
}
BASE = "https://www.christopherward.com/on/demandware.store/Sites-cwgross-Site/en_GB/Search-UpdateGrid"
QV = "https://www.christopherward.com/on/demandware.store/Sites-cwgross-Site/en_GB/Product-ShowQuickView"
API = "https://www.christopherward.com/on/demandware.store/Sites-cwgross-Site/en_GB/Product-Variation"
SITE = "https://www.christopherward.com"

# Strap-oriented glossary (model codes C63 / C12 / … kept as-is)
PHRASES = [
    (r"Integrated Rubber", "통합 고무"),
    (r"Hybrid Rubber", "하이브리드 고무"),
    (r"Aquaflex Lume Rubber", "아쿠아플렉스 룸 고무"),
    (r"Aquaflex Rubber", "아쿠아플렉스 고무"),
    (r"Vintage Oak Leather", "빈티지 오크 가죽"),
    (r"The Twelve", "트웰브"),
    (r"Twelve X", "트웰브 X"),
    (r"Jump Hour", "점프아워"),
    (r"iLink™|iLink", "iLink"),
    (r"Light Blue", "라이트 블루"),
    (r"DLC Black", "DLC 블랙"),
]
WORDS = [
    ("Sealander", "시랜더"),
    ("Biscay", "비스케이"),
    ("Consort", "콘솔트"),
    ("Bader", "베이더"),
    ("Twelve", "트웰브"),
    ("Integrated", "통합"),
    ("Rubber", "고무"),
    ("rubber", "고무"),
    ("Bracelet", "브레이슬릿"),
    ("bracelet", "브레이슬릿"),
    ("Leather", "가죽"),
    ("Strap", "스트랩"),
    ("strap", "스트랩"),
    ("Hybrid", "하이브리드"),
    ("Aquaflex", "아쿠아플렉스"),
    ("Chronograph", "크로노그래프"),
    ("Titanium", "티타늄"),
    ("transparent", "투명"),
    ("Transparent", "투명"),
    ("Luminescent", "야광"),
    ("Vintage", "빈티지"),
    ("Oak", "오크"),
    ("Camel", "카멜"),
    ("Khaki", "카키"),
    ("Bronze", "브론즈"),
    ("Steel", "스틸"),
    ("Black", "블랙"),
    ("White", "화이트"),
    ("Blue", "블루"),
    ("Orange", "오렌지"),
    ("Silver", "실버"),
    ("Brown", "브라운"),
    ("Tan", "탄"),
    ("Turquoise", "터콰이즈"),
]

ACCENTS = ["#1A2A38", "#2C3E50", "#3D2914", "#1B3A4B", "#4A3728", "#0E2F3D"]


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


def is_strap_sku(pid: str) -> bool:
    """CW strap SKUs look like 20-RUB-08-SXW-BB-ST / 22-STL-38-SXS-MA3 (not C*/N* watches)."""
    s = (pid or "").strip()
    if not s or re.match(r"^[CN]\d", s):
        return False
    return bool(re.match(r"^\d{2}-(RUB|STL|TIT|HYB|LEA|MAS|TIDE)-", s, re.I)) or (
        s.count("-") >= 2 and not re.match(r"^[CN]\d", s)
    )


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


def round_strap_krw(gbp: float) -> int:
    """SRP × 2100, round to nearest 1,000원. No VAT/markup add-ons."""
    return int(round(float(gbp) * 2100 / 1000.0) * 1000)


def to_ko(s: str) -> str:
    if not s:
        return ""
    out = s
    for a, b in PHRASES:
        out = re.sub(a, b, out, flags=re.I)
    for a, b in WORDS:
        out = re.sub(rf"\b{re.escape(a)}\b", b, out)
    out = re.sub(r"\bThe\b", "", out)
    out = out.replace("팔찌", "브레이슬릿")
    out = out.replace("러버", "고무")
    out = out.replace("실랜더", "시랜더")
    out = out.replace("콘소트", "콘솔트")
    out = out.replace("크리스토퍼 워드", "크리스토퍼와드")
    return re.sub(r"\s{2,}", " ", out).strip(" ·")


_TX_CACHE: dict[str, str] = (
    json.loads(TX_CACHE_PATH.read_text()) if TX_CACHE_PATH.exists() else {}
)


def translate_en(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    cached = _TX_CACHE.get(text)
    if cached and re.search(r"[가-힣]", cached) and len(re.findall(r"[A-Za-z]", cached)) < len(re.findall(r"[가-힣]", cached)):
        return to_ko(cached)
    # Protect model codes
    protected: dict[str, str] = {}

    def hold(m: re.Match[str]) -> str:
        k = f"⟦{len(protected)}⟧"
        protected[k] = m.group(0)
        return k

    held = re.sub(r"\b(?:C\d{1,3}|N\d{2}|Mk\.?\s*[IVX]+|GMT|COSC|Ti|iLink|FKM|DLC|316L)\b", hold, text)

    def _gtx(src: str) -> str:
        q = urllib.parse.quote(src[:4500])
        url = (
            "https://translate.googleapis.com/translate_a/single"
            f"?client=gtx&sl=en&tl=ko&dt=t&q={q}"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.loads(r.read().decode())
        return "".join(part[0] for part in data[0] if part and part[0])

    out = ""
    try:
        out = _gtx(held)
        time.sleep(0.15)
    except Exception:
        out = ""
    if not out or (
        len(re.findall(r"[가-힣]", out)) < 8 and len(text) > 40
    ):
        # MyMemory fallback for stubborn EN leftovers
        try:
            q = urllib.parse.quote(held[:450])
            url = f"https://api.mymemory.translated.net/get?q={q}&langpair=en|ko"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode())
            out = (data.get("responseData") or {}).get("translatedText") or out
            time.sleep(0.2)
        except Exception:
            pass
    if not out:
        out = to_ko(text)
    for k, v in protected.items():
        out = out.replace(k, v)
    out = to_ko(out)
    _TX_CACHE[text] = out
    return out


def scrape_strap_pids(sz: int = 60) -> list[str]:
    all_pids: list[str] = []
    start = 0
    while True:
        q = f"cgid=watch-straps&srule=most-popular&start={start}&sz={sz}"
        html = fetch(f"{BASE}?{q}")
        pids = list(dict.fromkeys(re.findall(r'data-pid="([^"]+)"', html)))
        if not pids:
            break
        all_pids.extend(pids)
        print(f"  PLP start={start} +{len(pids)}")
        if len(pids) < sz:
            break
        start += sz
        time.sleep(0.12)
    seen: set[str] = set()
    out: list[str] = []
    for p in all_pids:
        if p not in seen and is_strap_sku(p):
            seen.add(p)
            out.append(p)
    return out


def download_imgs(sku: str, urls: list[str]) -> list[str]:
    out: list[str] = []
    folder = IMG / slugify(sku)
    folder.mkdir(parents=True, exist_ok=True)
    for i, url in enumerate(urls[:8], 1):
        url = H.unescape(url.split("?")[0]) + "?sw=1200&sh=1500"
        dest = folder / f"{i}.jpg"
        local = f"/products/cw-pdp/{slugify(sku)}/{i}.jpg"
        if dest.exists() and dest.stat().st_size > 2500:
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


def enrich_sku(sku: str) -> dict:
    row: dict = {"sku": sku, "collections": ["cw-straps"], "primaryCollection": "cw-straps"}
    try:
        data = fetch_json(f"{QV}?pid={urllib.parse.quote(sku)}")
        prod = data.get("product") or {}
    except Exception as e:
        row["error"] = f"qv:{e}"
        return row

    gbp, list_gbp = parse_price(prod)
    name = (prod.get("productName") or sku).strip()
    short = H.unescape(re.sub(r"<[^>]+>", " ", prod.get("shortDescription") or ""))
    short = re.sub(r"\s+", " ", short).strip()
    features = []
    for f in prod.get("productFeatures") or []:
        if isinstance(f, str) and f.strip():
            features.append(f.strip())
        elif isinstance(f, dict):
            t = (f.get("text") or f.get("value") or f.get("label") or "").strip()
            if t:
                features.append(t)
    technicals = []
    for t in prod.get("productTechnicals") or []:
        if isinstance(t, dict):
            lab = (t.get("label") or t.get("name") or "").strip()
            val = (t.get("value") or t.get("text") or "").strip()
            if lab or val:
                technicals.append({"label": lab, "value": val})

    images = prod.get("images") or {}
    large = images.get("large") or images.get("hi-res") or images.get("medium") or []
    img_urls = [i.get("url") for i in large if isinstance(i, dict) and i.get("url")]

    # Prefer zoom from variation API
    try:
        var = fetch_json(f"{API}?pid={urllib.parse.quote(sku)}&quantity=1")
        ap = var.get("product") or {}
        zoom = [i["url"] for i in (ap.get("images") or {}).get("zoomImage") or [] if i.get("url")]
        if not zoom:
            zoom = [i["url"] for i in (ap.get("images") or {}).get("large") or [] if i.get("url")]
        if zoom:
            img_urls = zoom
        if ap.get("productName"):
            name = ap["productName"].strip()
        if ap.get("available") is not None:
            row["inStock"] = bool(ap.get("available"))
        elif prod.get("available") is not None:
            row["inStock"] = bool(prod.get("available"))
        else:
            row["inStock"] = True
        time.sleep(0.08)
    except Exception:
        row["inStock"] = bool(prod.get("available", True))

    sel = prod.get("selectedProductUrl") or prod.get("productUrl") or ""
    url = urllib.parse.urljoin(SITE, sel.split("?")[0]) if sel else f"{SITE}/watch-straps/{sku}.html"

    local_imgs = download_imgs(sku, img_urls) if img_urls else []

    row.update(
        {
            "name": name,
            "shortDescriptionEn": short,
            "featuresEn": features[:16],
            "technicals": technicals[:20],
            "gbpPrice": gbp,
            "gbpListPrice": list_gbp,
            "url": url,
            "imageUrls": img_urls[:8],
            "images": local_imgs,
            "scrapedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    )
    return row


def build_product(row: dict, idx: int) -> dict | None:
    sku = row.get("sku") or ""
    gbp = row.get("gbpPrice")
    if gbp is None:
        return None
    name_en = row.get("name") or sku
    # Colour-only subtitle (avoid dumping every technical into the title)
    colour = ""
    for t in row.get("technicals") or []:
        lab = (t.get("label") or "").lower()
        val = (t.get("value") or "").strip()
        if val and any(x in lab for x in ("colour", "color")):
            colour = val
            break
    name_ko = to_ko(name_en)
    if colour:
        colour_ko = to_ko(colour)
        if colour_ko and colour_ko not in name_ko:
            name_ko = f"{name_ko} · {colour_ko}"
    # Drop leftover English fragments
    name_ko = re.sub(r"\b(rubber|bracelet|leather|strap|titanium|steel)\b", "", name_ko, flags=re.I)
    name_ko = re.sub(r"\s{2,}", " ", name_ko).strip(" ·")

    desc_en = row.get("shortDescriptionEn") or ""
    desc_ko = translate_en(desc_en) if desc_en else f"크리스토퍼와드 {name_ko} 스트랩."

    features_ko = [translate_en(f) if re.search(r"[A-Za-z]{4,}", f) else to_ko(f) for f in (row.get("featuresEn") or [])[:12]]
    tech_specs = []
    for t in row.get("technicals") or []:
        lab = t.get("label") or ""
        val = t.get("value") or ""
        lab_ko = {
            "Strap Material": "스트랩 소재",
            "Strap Colour": "스트랩 컬러",
            "Colour": "컬러",
            "Color": "컬러",
            "Material": "소재",
            "Size": "사이즈",
            "Width": "폭",
            "Buckle": "버클",
            "Lug Width": "러그 폭",
            "Range": "라인",
        }.get(lab, to_ko(lab) if lab else "")
        val_ko = to_ko(val) if re.search(r"[A-Za-z]{3,}", val) else val
        if lab_ko or val_ko:
            tech_specs.append({"labelKo": lab_ko or lab, "valueKo": val_ko or val})

    images = [x for x in (row.get("images") or []) if x]
    if not images and row.get("imageUrls"):
        # fallback remote URLs (should be rare)
        images = [H.unescape(u.split("?")[0]) + "?sw=1200&sh=1500" for u in row["imageUrls"][:4]]
    if not images:
        return None

    price = round_strap_krw(float(gbp))
    compare = None
    if row.get("gbpListPrice") and float(row["gbpListPrice"]) > float(gbp):
        compare = round_strap_krw(float(row["gbpListPrice"]))

    story = [
        {
            "titleKo": "제품 소개",
            "bodyKo": desc_ko,
            "image": images[0],
        }
    ]
    if features_ko:
        story.append(
            {
                "titleKo": "디테일 & 특징",
                "bodyKo": " · ".join(features_ko[:8]),
                "image": images[min(1, len(images) - 1)],
                "reverse": True,
            }
        )
    if tech_specs:
        story.append(
            {
                "titleKo": "스펙",
                "bodyKo": " · ".join(f"{t['labelKo']}: {t['valueKo']}" for t in tech_specs[:8]),
                "image": images[min(2, len(images) - 1)],
            }
        )

    return {
        "id": f"cw-strap-{slugify(sku)}",
        "name": name_en,
        "nameKo": name_ko[:140],
        "brand": "Christopher Ward",
        "price": price,
        "compareAtPrice": compare,
        "gbpPrice": float(gbp),
        "gbpListPrice": float(row["gbpListPrice"]) if row.get("gbpListPrice") else None,
        "category": "watches",
        "subcategory": "cw-straps",
        "cwCollections": ["cw-straps"],
        "tags": ["christopher-ward", "cw-straps", "strap"],
        "descriptionKo": desc_ko,
        "image": images[0],
        "images": images,
        "hoverImage": images[1] if len(images) > 1 else None,
        "accent": ACCENTS[idx % len(ACCENTS)],
        "sku": sku,
        "sourceUrl": row.get("url") or f"{SITE}/watch-straps/{sku}.html",
        "inStock": bool(row.get("inStock", True)),
        "registeredAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "editTier": "signature",
        "storySections": story,
        "techSpecs": tech_specs,
        "featuresKo": features_ko,
    }


def emit_ts(products: list[dict]) -> None:
    lines = [
        "/** Auto-generated CW straps — SRP×2100 / 천원 반올림 · subcategory cw-straps. */",
        'import type { Product } from "@/data/products";',
        "",
        "export const cwStrapProducts: Product[] = [",
    ]
    for p in products:
        lines.append("  {")
        lines.append(f'    id: {json.dumps(p["id"])},')
        lines.append(f'    name: {json.dumps(p["name"], ensure_ascii=False)},')
        lines.append(f'    nameKo: {json.dumps(p["nameKo"], ensure_ascii=False)},')
        lines.append('    brand: "Christopher Ward",')
        lines.append(f'    price: {p["price"]},')
        if p.get("compareAtPrice"):
            lines.append(f'    compareAtPrice: {p["compareAtPrice"]},')
        lines.append(f'    gbpPrice: {p["gbpPrice"]},')
        if p.get("gbpListPrice"):
            lines.append(f'    gbpListPrice: {p["gbpListPrice"]},')
        lines.append('    category: "watches",')
        lines.append('    subcategory: "cw-straps",')
        lines.append('    cwCollections: ["cw-straps"] as Product["cwCollections"],')
        lines.append(f'    tags: {json.dumps(p["tags"], ensure_ascii=False)},')
        lines.append(f'    descriptionKo: {json.dumps(p["descriptionKo"], ensure_ascii=False)},')
        lines.append(f'    image: {json.dumps(p["image"])},')
        lines.append(f'    images: {json.dumps(p["images"])},')
        if p.get("hoverImage"):
            lines.append(f'    hoverImage: {json.dumps(p["hoverImage"])},')
        lines.append(f'    accent: {json.dumps(p["accent"])},')
        lines.append(f'    sku: {json.dumps(p["sku"])},')
        lines.append(f'    sourceUrl: {json.dumps(p.get("sourceUrl"))},')
        lines.append(f'    inStock: {str(p.get("inStock", True)).lower()},')
        lines.append(f'    registeredAt: {json.dumps(p["registeredAt"])},')
        lines.append('    editTier: "signature",')
        if p.get("storySections"):
            lines.append(f'    storySections: {json.dumps(p["storySections"], ensure_ascii=False)},')
        if p.get("techSpecs"):
            lines.append(f'    techSpecs: {json.dumps(p["techSpecs"], ensure_ascii=False)},')
        if p.get("featuresKo"):
            lines.append(f'    featuresKo: {json.dumps(p["featuresKo"], ensure_ascii=False)},')
        lines.append("  },")
    lines.append("];")
    lines.append("")
    CATALOG_TS.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--rebuild-only",
        action="store_true",
        help="Skip PLP/QV scrape; rebuild catalog from cw-straps-raw.json",
    )
    args = ap.parse_args()

    if args.rebuild_only and RAW_PATH.exists():
        print("1) Loading existing cw-straps-raw.json…")
        raw_doc = json.loads(RAW_PATH.read_text())
        ordered = raw_doc.get("products") or []
        print(f"   {len(ordered)} strap rows")
    else:
        print("1) Scraping CW watch-straps PLP…")
        pids = scrape_strap_pids(sz=60)
        print(f"   {len(pids)} strap SKUs")

        prev = {}
        if RAW_PATH.exists():
            prev = {
                p["sku"]: p
                for p in json.loads(RAW_PATH.read_text()).get("products", [])
                if p.get("sku")
            }

        print("2) Enriching SKUs (QV + images)…")
        products_raw: list[dict] = []
        with ThreadPoolExecutor(max_workers=4) as ex:
            futs = {ex.submit(enrich_sku, sku): sku for sku in pids}
            done = 0
            for fut in as_completed(futs):
                sku = futs[fut]
                try:
                    row = fut.result()
                except Exception as e:
                    row = prev.get(sku) or {"sku": sku, "error": str(e)}
                if not row.get("images") and prev.get(sku, {}).get("images"):
                    row["images"] = prev[sku]["images"]
                products_raw.append(row)
                done += 1
                if done % 20 == 0:
                    print(f"   enriched {done}/{len(pids)}")

        by = {p["sku"]: p for p in products_raw}
        ordered = [by[s] for s in pids if s in by]

        raw_doc = {
            "scrapedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": "https://www.christopherward.com/watch-straps?start=0&sz=60",
            "cgid": "watch-straps",
            "count": len(ordered),
            "products": ordered,
        }
        RAW_PATH.write_text(json.dumps(raw_doc, indent=2, ensure_ascii=False) + "\n")

    print("3) Building Korean catalog…")
    # Clear bad EN-only cache entries so we retranslate
    bad_keys = [
        k
        for k, v in list(_TX_CACHE.items())
        if isinstance(v, str)
        and len(k) > 40
        and len(re.findall(r"[가-힣]", v)) < 12
    ]
    for k in bad_keys:
        _TX_CACHE.pop(k, None)

    catalog: list[dict] = []
    for i, row in enumerate(ordered):
        p = build_product(row, i)
        if p:
            catalog.append(p)
        if (i + 1) % 25 == 0:
            print(f"   built {i + 1}/{len(ordered)}")

    emit_ts(catalog)
    TX_CACHE_PATH.write_text(json.dumps(_TX_CACHE, ensure_ascii=False, indent=2) + "\n")

    print(f"OK {len(catalog)} straps → {CATALOG_TS.relative_to(ROOT)}")
    if catalog:
        sample = catalog[0]
        print(
            f"  sample: {sample['nameKo']} · £{sample['gbpPrice']} → {sample['price']:,}원 · imgs={len(sample['images'])}"
        )
        print(f"  desc: {sample['descriptionKo'][:120]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
