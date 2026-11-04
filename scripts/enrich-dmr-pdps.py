#!/usr/bin/env python3
"""Enrich DMR watch PDPs: full KO copy + extra Rolex.com gallery frames.

Usage (from briq root or briq-ship):
  python3 scripts/enrich-dmr-pdps.py translate   # body EN→KO for non-tiny bodies
  python3 scripts/enrich-dmr-pdps.py rolex-imgs  # download Rolex media extras
  python3 scripts/enrich-dmr-pdps.py catalog     # rebuild JSON catalogues
  python3 scripts/enrich-dmr-pdps.py all
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

# Prefer working tree with catalogues
ROOT = Path(__file__).resolve().parents[1]
if not (ROOT / "src/data/om/om-catalog.json").exists():
    alt = Path("/Users/jeonghyunlee/briq-ship")
    if (alt / "src/data/om/om-catalog.json").exists():
        ROOT = alt

import importlib.util

_dmr_path = ROOT / "scripts" / "import-dmr-watches.py"
_spec = importlib.util.spec_from_file_location("import_dmr_watches", _dmr_path)
dmr = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(dmr)

CACHE = dmr.CACHE
PRODUCTS_JSON = dmr.PRODUCTS_JSON
KO_CACHE = dmr.KO_CACHE
ROLEX_ENRICH = CACHE / "rolex-enrich.json"

RX_FAMILY = {
    "rx-datejust": "datejust",
    "rx-daytona": "cosmograph-daytona",
    "rx-day-date": "day-date",
    "rx-oyster-perpetual": "oyster-perpetual",
    "rx-sky-dweller": "sky-dweller",
    "rx-lady-datejust": "lady-datejust",
    "rx-gmt-master-ii": "gmt-master-ii",
    "rx-yacht-master": "yacht-master",
    "rx-land-dweller": "land-dweller",
    "rx-submariner": "submariner",
    "rx-explorer": "explorer",
    "rx-sea-dweller": "sea-dweller",
    "rx-air-king": "air-king",
    "rx-1908": "1908",
    "rx-deepsea": "deepsea",
    "rx-other": "watches",
}

# Official Rolex media asset folders that usually exist per RMC.
RX_MEDIA_KINDS = [
    "upright-c",
    "bezel-constant-size-with-shadow",
    "raw-dial-constant-size-with-shadow",
    "luminescence",
]


def media_url(kind: str, rmc: str, w: int = 1600) -> str:
    return (
        "https://media.rolex.com/image/upload/q_auto/f_auto/"
        f"t_v7-cover-majesty-landscape/c_limit,w_{w}/v1/a677b2c664f6/"
        f"catalogue/2026/{kind}/{rmc}"
    )


def download(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 5000:
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=60).read()
        if len(data) < 3000:
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return True
    except Exception:
        return False


def cmd_rolex_imgs() -> None:
    rows = json.loads(PRODUCTS_JSON.read_text())
    rx = [r for r in rows if r["brand_key"] == "rx"]
    print(f"rolex-imgs {len(rx)} models", flush=True)
    for i, r in enumerate(rx, 1):
        rmc = r["handle"].lower()
        dest = dmr.local_dir("rx", r["handle"])
        dest.mkdir(parents=True, exist_ok=True)
        # Keep existing DMR frames 1..N, append Rolex media after
        existing = sorted(
            [p for p in dest.glob("*.jpg") if re.match(r"^\d+\.jpg$", p.name)],
            key=lambda p: int(p.stem),
        )
        next_n = (max((int(p.stem) for p in existing), default=0) + 1)
        added = 0
        for kind in RX_MEDIA_KINDS:
            out = dest / f"{next_n}.jpg"
            # skip if we already have this kind content (by size proxy / marker)
            marker = dest / f".rx-{kind}"
            if marker.exists():
                continue
            ok = download(media_url(kind, rmc), out)
            if ok:
                marker.write_text("1")
                next_n += 1
                added += 1
            time.sleep(0.05)
        # refresh story frames from gallery
        gallery = sorted(
            [p for p in dest.glob("*.jpg") if re.match(r"^\d+\.jpg$", p.name)],
            key=lambda p: int(p.stem),
        )
        for s_i, src in enumerate(gallery[:3], 1):
            story = dest / f"story-{s_i}.jpg"
            story.write_bytes(src.read_bytes())
        if i % 20 == 0 or i == len(rx):
            print(f"  {i}/{len(rx)} {rmc} +{added} (gallery={len(gallery)})", flush=True)


def cmd_translate_bodies() -> None:
    """Translate full body_en for every product (Rolex short lines included)."""
    rows = json.loads(PRODUCTS_JSON.read_text())
    # Merge Rolex enrich text into body when present
    enrich = json.loads(ROLEX_ENRICH.read_text()) if ROLEX_ENRICH.exists() else {}
    cache = dmr.load_ko_cache()
    jobs = []
    for i, r in enumerate(rows, 1):
        body = (r.get("body_en") or "").strip()
        if r["brand_key"] == "rx" and r["handle"] in enrich:
            e = enrich[r["handle"]]
            meta = re.sub(
                r"^Discover .+? on Rolex\.com\.\s*",
                "",
                e.get("meta") or "",
                flags=re.I,
            ).strip()
            parts = [meta, e.get("lede") or "", e.get("body") or ""]
            body = "\n\n".join(p.strip() for p in parts if p and p.strip())
        # Must match import-dmr-watches.ko_get truncate (default 900).
        body = dmr.truncate_body(body) if body else ""
        if not body:
            continue
        key = hashlib.sha1(f"body:{body}".encode()).hexdigest()
        if key in cache:
            continue
        jobs.append((key, body, f"[{i}/{len(rows)}] {r['handle'][:40]}"))

    print(f"translate bodies queue={len(jobs)} cached={len(cache)}", flush=True)
    n_new = 0

    def work(job):
        key, src, label = job
        print(label, flush=True)
        return key, dmr.polish_ko(dmr.gtx(src))

    with ThreadPoolExecutor(max_workers=10) as pool:
        futs = [pool.submit(work, j) for j in jobs]
        for fut in as_completed(futs):
            try:
                key, ko = fut.result()
            except Exception as e:
                print(" fail", e, flush=True)
                continue
            cache[key] = ko
            n_new += 1
            if n_new % 25 == 0:
                dmr.save_ko_cache(cache)
                print(f"  progress {n_new}/{len(jobs)}", flush=True)
    dmr.save_ko_cache(cache)
    print(f"translate bodies done new={n_new} cache={len(cache)}", flush=True)


def fix_title_ko(title_en: str, title_ko: str) -> str:
    """Prefer glossary-polished EN when MT invents nonsense (e.g. Submariner→잠수함)."""
    polished = dmr.polish_ko(title_en)
    # If MT dropped known collection tokens that glossary still has, use polished.
    bad = ["잠수함", "주니어", "사례"]
    if any(b in (title_ko or "") for b in bad):
        return polished
    if len(re.findall(r"[가-힣]", title_ko or "")) < 1:
        return polished or title_en
    return title_ko


def build_product_rich(r: dict, cache: dict[str, str], enrich: dict) -> dict | None:
    # Temporarily put Rolex enrich into body_en for builder
    r2 = dict(r)
    if r["brand_key"] == "rx" and r["handle"] in enrich:
        e = enrich[r["handle"]]
        # Keep Discover-prefix so body hash matches the translated ko-cache keys.
        parts = [e.get("meta") or "", e.get("lede") or "", e.get("body") or ""]
        merged = "\n\n".join(p.strip() for p in parts if p and p.strip())
        if merged:
            r2["body_en"] = merged

    body_en = r2.get("body_en") or ""
    body_src = dmr.truncate_body(body_en)
    # Catalog rebuild must not call gtx synchronously — translate step fills cache.

    prod = dmr.build_product(r2, cache)
    if not prod:
        return None
    prod["nameKo"] = fix_title_ko(prod["name"], prod.get("nameKo") or "")

    def polish_desc(text: str) -> str:
        t = dmr.polish_ko(text or "")
        t = re.sub(r"[가-힣A-Za-z0-9\- ]{0,40}심판을 만나보세요\.?\s*", "", t)
        t = re.sub(r"롤렉스\.com의\s*m[\w-]+\.\s*", "", t)
        t = t.replace("잠수함", "서브마리너")
        return t.strip()

    body_ko = dmr.ko_get(cache, "body", body_src) if body_src else ""
    if not body_ko and body_src:
        legacy = dmr.truncate_body(body_en, limit=1800)
        body_ko = cache.get(hashlib.sha1(f"body:{legacy}".encode()).hexdigest()) or ""
    body_ko = polish_desc(body_ko)
    prod["descriptionKo"] = polish_desc(prod.get("descriptionKo") or "")
    thin = (
        "상세 스펙은 상품 정보" in (prod.get("descriptionKo") or "")
        or len(re.findall(r"[가-힣]", prod.get("descriptionKo") or "")) < 80
    )
    if thin and len(re.findall(r"[가-힣]", body_ko)) >= 40:
        prod["descriptionKo"] = body_ko
        paras = [p.strip() for p in re.split(r"\n\n+", body_ko) if p.strip()]
        titles = ["디자인", "다이얼 & 마감", "무브먼트 & 착용감"]
        stories = []
        for i in range(min(3, max(1, len(paras)))):
            stories.append(
                {
                    "titleKo": titles[i] if i < len(titles) else f"디테일 {i+1}",
                    "bodyKo": polish_desc((paras[i] if i < len(paras) else body_ko)[:500]),
                    "image": prod["images"][min(i, len(prod["images"]) - 1)],
                    **({"reverse": True} if i == 1 else {}),
                }
            )
        prod["storySections"] = stories
        feats = []
        for line in re.split(r"[\n•.]+", body_en):
            line = line.strip()
            if 25 <= len(line) <= 110:
                feat = dmr.ko_get(cache, "body", line) or dmr.polish_ko(line)
                feat = polish_desc(feat)
                if len(re.findall(r"[가-힣]", feat)) >= 4:
                    feats.append(feat[:90])
            if len(feats) >= 8:
                break
        if feats:
            prod["featuresKo"] = feats
    else:
        # Still polish story bodies already built by build_product
        for s in prod.get("storySections") or []:
            if s.get("bodyKo"):
                s["bodyKo"] = polish_desc(s["bodyKo"])
    # Re-scan local gallery (Rolex extras may have been added)
    meta = dmr.BRANDS[r["brand_key"]]
    dest_rel = f"/products/{meta['pdp']}/{dmr.slugify(r['handle'])}"
    local = dmr.local_dir(r["brand_key"], r["handle"])
    gallery = []
    for n in range(1, 21):
        p = local / f"{n}.jpg"
        if p.exists() and p.stat().st_size > 2000:
            gallery.append(f"{dest_rel}/{n}.jpg")
    if gallery:
        prod["images"] = gallery
        prod["image"] = gallery[0]
        prod["hoverImage"] = gallery[1] if len(gallery) > 1 else gallery[0]
        if prod.get("variants"):
            prod["variants"][0]["images"] = gallery
            prod["variants"][0]["image"] = gallery[0]
        for i, s in enumerate(prod.get("storySections") or []):
            s["image"] = gallery[min(i, len(gallery) - 1)]
    return prod


def cmd_catalog() -> None:
    rows = json.loads(PRODUCTS_JSON.read_text())
    cache = dmr.load_ko_cache()
    enrich = json.loads(ROLEX_ENRICH.read_text()) if ROLEX_ENRICH.exists() else {}
    by_brand: dict[str, list] = {k: [] for k in dmr.BRANDS}
    skipped = 0
    for r in rows:
        prod = build_product_rich(r, cache, enrich)
        if not prod:
            skipped += 1
            continue
        by_brand[r["brand_key"]].append(prod)
    dmr.save_ko_cache(cache)
    for bkey, products in by_brand.items():
        out_dir = ROOT / "src" / "data" / bkey
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{bkey}-catalog.json").write_text(
            json.dumps(products, ensure_ascii=False, separators=(",", ":")) + "\n"
        )
        print(f"catalog {bkey}: {len(products)}", flush=True)
    print(f"skipped={skipped}", flush=True)


def write_rolex_enrich_batch(batch: dict[str, dict]) -> None:
    cur = json.loads(ROLEX_ENRICH.read_text()) if ROLEX_ENRICH.exists() else {}
    cur.update(batch)
    ROLEX_ENRICH.write_text(json.dumps(cur, ensure_ascii=False, indent=2))
    print(f"rolex-enrich saved {len(cur)}", flush=True)


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    # Catalogues live in briq-ship; product JPGs + scrape cache live in Documents/briq.
    docs = Path("/Users/jeonghyunlee/Documents/briq")
    dmr.ROOT = ROOT
    img_docs = docs / "public" / "products"
    dmr.IMG_ROOT = img_docs if img_docs.exists() else (ROOT / "public" / "products")
    dmr.CACHE = docs / "tmp" / "dmr-import"
    if not dmr.CACHE.exists():
        dmr.CACHE = ROOT / "tmp" / "dmr-import"
        dmr.CACHE.mkdir(parents=True, exist_ok=True)
    dmr.PRODUCTS_JSON = dmr.CACHE / "products.json"
    dmr.KO_CACHE = dmr.CACHE / "ko-cache.json"
    global PRODUCTS_JSON, KO_CACHE, CACHE, ROLEX_ENRICH
    CACHE = dmr.CACHE
    PRODUCTS_JSON = dmr.PRODUCTS_JSON
    KO_CACHE = dmr.KO_CACHE
    ROLEX_ENRICH = CACHE / "rolex-enrich.json"

    if cmd == "rolex-imgs":
        cmd_rolex_imgs()
    elif cmd == "translate":
        cmd_translate_bodies()
    elif cmd == "catalog":
        cmd_catalog()
    elif cmd == "all":
        cmd_rolex_imgs()
        cmd_translate_bodies()
        cmd_catalog()
    elif cmd == "merge-rolex-json":
        # stdin: JSON object of handle -> enrich fields
        data = json.loads(sys.stdin.read())
        write_rolex_enrich_batch(data)
    else:
        raise SystemExit(f"unknown {cmd}")


if __name__ == "__main__":
    main()
