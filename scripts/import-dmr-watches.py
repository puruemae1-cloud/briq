#!/usr/bin/env python3
"""Import DMR (dmr.co.uk) watches into Briq — brands, subcollections, KO copy, images.

Usage:
  python3 scripts/import-dmr-watches.py scrape          # fetch product JSON
  python3 scripts/import-dmr-watches.py translate       # EN→KO cache
  python3 scripts/import-dmr-watches.py images          # download local JPGs
  python3 scripts/import-dmr-watches.py catalog         # write src/data/*/dmr catalogs
  python3 scripts/import-dmr-watches.py all             # scrape→translate→images→catalog
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "tmp" / "dmr-import"
CACHE.mkdir(parents=True, exist_ok=True)
PRODUCTS_JSON = CACHE / "products.json"
KO_CACHE = CACHE / "ko-cache.json"
IMG_ROOT = ROOT / "public" / "products"

UA = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
}

# brand_key → hub collection + sub id → (dmr handle, labelKo)
BRANDS: dict[str, dict[str, Any]] = {
    "om": {
        "brand": "OMEGA",
        "brandKo": "오메가",
        "hub_id": "omega",
        "hub_handle": "omega",
        "prefix": "om",
        "pdp": "om-pdp",
        "subs": {
            "om-seamaster": ("omega-seamaster", "씨마스터"),
            "om-speedmaster": ("omega-speedmaster", "스피드마스터"),
            "om-de-ville": ("omega-de-ville", "드 빌"),
            "om-constellation": ("omega-constellation", "컨스텔레이션"),
        },
        "other": ("om-other", "기타"),
    },
    "th": {
        "brand": "TAG Heuer",
        "brandKo": "태그호이어",
        "hub_id": "tag-heuer",
        "hub_handle": "tag-heuer",
        "prefix": "th",
        "pdp": "th-pdp",
        "subs": {
            "th-carrera": ("tag-heuer-carrera", "카레라"),
            "th-aquaracer": ("tag-heuer-aquaracer", "아쿠아레이서"),
            "th-formula-1": ("tag-heuer-formula-1", "포뮬러 1"),
            "th-monaco": ("tag-heuer-monaco", "모나코"),
            "th-connected": ("tag-heuer-connected", "커넥티드"),
            "th-link": ("tag-heuer-link", "링크"),
        },
        "other": ("th-other", "기타"),
    },
    "td": {
        "brand": "TUDOR",
        "brandKo": "튜더",
        "hub_id": "tudor",
        "hub_handle": "tudor",
        "prefix": "td",
        "pdp": "td-pdp",
        "subs": {
            "td-black-bay": ("tudor-black-bay", "블랙 베이"),
            "td-royal": ("tudor-royal", "로열"),
            "td-1926": ("tudor-1926", "1926"),
            "td-pelagos": ("tudor-pelagos", "펠라고스"),
            "td-clair-de-rose": ("tudor-clair-de-rose", "클레르 드 로즈"),
            "td-ranger": ("tudor-ranger", "레인저"),
        },
        "other": ("td-other", "기타"),
    },
    "iw": {
        "brand": "IWC Schaffhausen",
        "brandKo": "IWC",
        "hub_id": "iwc",
        "hub_handle": "iwc-schaffhausen",
        "prefix": "iw",
        "pdp": "iw-pdp",
        "subs": {
            "iw-pilots": ("iwc-pilots", "파일럿"),
            "iw-portugieser": ("iwc-portugieser", "포르투기저"),
            "iw-portofino": ("iwc-portofino", "포르토피노"),
            "iw-ingenieur": ("iwc-ingenieur", "인제니어"),
            "iw-aquatimer": ("iwc-aquatimer", "아쿠아타이머"),
        },
        "other": ("iw-other", "기타"),
    },
    "rx": {
        "brand": "Rolex",
        "brandKo": "롤렉스",
        "hub_id": "rolex",
        "hub_handle": "rolex-watches-selection",
        "prefix": "rx",
        "pdp": "rx-pdp",
        "subs": {
            "rx-datejust": ("rolex-watches-datejust", "데이트저스트"),
            "rx-daytona": ("rolex-watches-cosmograph-daytona", "데이토나"),
            "rx-day-date": ("rolex-watches-day-date", "데이데이트"),
            "rx-oyster-perpetual": ("rolex-watches-oyster-perpetual", "오이스터 퍼페츄얼"),
            "rx-sky-dweller": ("rolex-watches-sky-dweller", "스카이-듀엘러"),
            "rx-lady-datejust": ("rolex-watches-lady-datejust", "레이디 데이트저스트"),
            "rx-gmt-master-ii": ("rolex-watches-gmt-master-ii", "GMT-마스터 II"),
            "rx-yacht-master": ("rolex-watches-yacht-master", "요트-마스터"),
            "rx-land-dweller": ("rolex-watches-land-dweller", "랜드-듀엘러"),
            "rx-submariner": ("rolex-watches-submariner", "서브마리너"),
            "rx-explorer": ("rolex-watches-explorer", "익스플로러"),
            "rx-sea-dweller": ("rolex-watches-sea-dweller", "시-듀엘러"),
            "rx-air-king": ("rolex-watches-air-king", "에어-킹"),
            "rx-1908": ("rolex-watches-1908", "1908"),
            "rx-deepsea": ("rolex-watches-deepsea", "딥씨"),
        },
        "other": ("rx-other", "기타"),
    },
    "pp": {
        "brand": "Patek Philippe",
        "brandKo": "파텍 필립",
        "hub_id": "patek-philippe",
        "hub_handle": "patek-philippe",
        "prefix": "pp",
        "pdp": "pp-pdp",
        "subs": {
            "pp-nautilus": ("patek-philippe-nautilus", "노틸러스"),
            "pp-aquanaut": ("patek-philippe-aquanaut", "아쿠아넛"),
            "pp-calatrava": ("patek-philippe-calatrava", "칼라트라바"),
            "pp-complications": ("patek-philippe-complications", "컴플리케이션"),
            "pp-grand-complications": ("patek-philippe-grand-complications", "그랜드 컴플리케이션"),
            "pp-twenty-4": ("patek-philippe-twenty-4", "트웬티-4"),
            "pp-gondolo": ("gondolo", "곤돌로"),
            "pp-cubitus": ("patek-philippe-cubitus", "큐비투스"),
            "pp-golden-ellipse": ("golden-ellipse", "골든 엘립스"),
        },
        "other": ("pp-other", "기타"),
    },
}

GLOSSARY = [
    (r"\bOMEGA\b", "오메가"),
    (r"\bTAG Heuer\b", "태그호이어"),
    (r"\bTUDOR\b", "튜더"),
    (r"\bIWC Schaffhausen\b", "IWC"),
    (r"\bIWC\b", "IWC"),
    (r"\bRolex\b", "롤렉스"),
    (r"\bPatek Philippe\b", "파텍 필립"),
    (r"\bSeamaster\b", "씨마스터"),
    (r"\bAqua Terra\b", "아쿠아 테라"),
    (r"\bSpeedmaster\b", "스피드마스터"),
    (r"\bPlanet Ocean\b", "플래닛 오션"),
    (r"\bCarrera\b", "카레라"),
    (r"\bAquaracer\b", "아쿠아레이서"),
    (r"\bFormula 1\b", "포뮬러 1"),
    (r"\bMonaco\b", "모나코"),
    (r"\bBlack Bay\b", "블랙 베이"),
    (r"\bPelagos\b", "펠라고스"),
    (r"\bPortugieser\b", "포르투기저"),
    (r"\bPortofino\b", "포르토피노"),
    (r"\bIngenieur\b", "인제니어"),
    (r"\bPilot'?s?\b", "파일럿"),
    (r"\bDatejust\b", "데이트저스트"),
    (r"\bDaytona\b", "데이토나"),
    (r"\bSubmariner\b", "서브마리너"),
    (r"\bNautilus\b", "노틸러스"),
    (r"\bAquanaut\b", "아쿠아넛"),
    (r"\bCalatrava\b", "칼라트라바"),
    (r"\bCo-Axial\b", "코액시얼"),
    (r"\bMaster Chronometer\b", "마스터 크로노미터"),
    (r"\bSuper-LumiNova\b", "슈퍼루미노바"),
    (r"\bSwiss Made\b", "스위스 메이드"),
    (r"\bstainless steel\b", "스테인리스 스틸"),
    (r"\bwater resistance\b", "방수"),
    (r"\bpower reserve\b", "파워리저브"),
    (r"\bself-winding\b", "오토매틱"),
    (r"\bautomatic\b", "오토매틱"),
    (r"\bchronograph\b", "크로노그래프"),
    (r"\bchronometer\b", "크로노미터"),
    (r"\bWatch\b", "워치"),
]


def http_json(url: str, retries: int = 8) -> Any:
    last: Exception | None = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            last = e
            time.sleep(min(30, 1.5 * (i + 1) * (2 if "429" in str(e) else 1)))
    raise RuntimeError(f"GET failed {url}: {last}")


def strip_html(raw: str) -> str:
    if not raw:
        return ""
    t = html.unescape(raw)
    t = re.sub(r"(?is)<script.*?>.*?</script>", " ", t)
    t = re.sub(r"(?is)<style.*?>.*?</style>", " ", t)
    t = re.sub(r"(?i)<br\s*/?>", "\n", t)
    t = re.sub(r"(?i)</p>", "\n\n", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t.strip()


def krw_from_gbp(gbp: float) -> int:
    return int(round((gbp * 1900 * 1.16) / 10000) * 10000)


def slugify(handle: str) -> str:
    s = handle.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:80] or "watch"


def fetch_collection_products(handle: str) -> list[dict]:
    out: list[dict] = []
    page = 1
    while True:
        url = f"https://dmr.co.uk/collections/{handle}/products.json?limit=50&page={page}"
        data = http_json(url)
        prods = data.get("products") or []
        if not prods:
            break
        out.extend(prods)
        print(f"  {handle} page {page}: +{len(prods)} (total {len(out)})", flush=True)
        if len(prods) < 50:
            break
        page += 1
        time.sleep(0.4)
    return out


def _rows_from_maps(
    by_handle: dict[str, dict], membership: dict[str, set[str]]
) -> list[dict]:
    rows: list[dict] = []
    for h, p in by_handle.items():
        bkey = p["_brand_key"]
        meta = BRANDS[bkey]
        subs = sorted(membership.get(h) or [meta["other"][0]])
        sub = next((s for s in subs if not s.endswith("-other")), subs[0])
        v = (p.get("variants") or [{}])[0]
        try:
            gbp = float(v.get("price") or 0)
        except Exception:
            gbp = 0.0
        if gbp <= 0:
            continue
        imgs = []
        for im in p.get("images") or []:
            src = im.get("src") if isinstance(im, dict) else im
            if src:
                imgs.append(str(src).split("?")[0])
        if not imgs:
            continue
        body = strip_html(p.get("body_html") or "")
        body = re.split(
            r"\n(?:DELIVERY|SEE IT IN A SHOWROOM|Discover more from)\b",
            body,
            maxsplit=1,
        )[0].strip()
        rows.append(
            {
                "handle": h,
                "brand_key": bkey,
                "brand": meta["brand"],
                "subcategory": sub,
                "title": p.get("title") or h,
                "vendor": p.get("vendor") or meta["brand"],
                "sku": v.get("sku") or "",
                "shopify_variant_id": v.get("id"),
                "gbp": gbp,
                "available": bool(v.get("available", True)),
                "body_en": body,
                "images": imgs[:12],
                "tags": p.get("tags") or [],
                "product_type": p.get("product_type") or "",
                "sourceUrl": f"https://dmr.co.uk/products/{h}",
            }
        )
    rows.sort(key=lambda r: (r["brand_key"], r["subcategory"], r["handle"]))
    return rows


def cmd_scrape(only_brand: str | None = None) -> None:
    by_handle: dict[str, dict] = {}
    membership: dict[str, set[str]] = {}
    ck = CACHE / "scrape-checkpoint.json"
    if ck.exists():
        raw = json.loads(ck.read_text())
        by_handle = raw.get("by_handle") or {}
        membership = {k: set(v) for k, v in (raw.get("membership") or {}).items()}
        print(f"resumed checkpoint handles={len(by_handle)}", flush=True)

    done_path = CACHE / "scrape-done-brands.json"
    done_brands = set(json.loads(done_path.read_text())) if done_path.exists() else set()
    brand_keys = [only_brand] if only_brand else list(BRANDS.keys())

    for bkey in brand_keys:
        meta = BRANDS[bkey]
        if bkey in done_brands and not only_brand:
            print(f"skip done brand {bkey}", flush=True)
            continue
        print(f"\n== scrape {meta['brand']} ==", flush=True)
        for sub_id, (handle, _ko) in meta["subs"].items():
            try:
                prods = fetch_collection_products(handle)
            except Exception as e:
                print(f"  SKIP sub {handle}: {e}", flush=True)
                continue
            for p in prods:
                h = p["handle"]
                membership.setdefault(h, set()).add(sub_id)
                by_handle[h] = {**p, "_brand_key": bkey}
            time.sleep(0.45)
        try:
            hub_prods = fetch_collection_products(meta["hub_handle"])
        except Exception as e:
            print(f"  SKIP hub {meta['hub_handle']}: {e}", flush=True)
            hub_prods = []
        other_id = meta["other"][0]
        for p in hub_prods:
            h = p["handle"]
            by_handle[h] = {**p, "_brand_key": bkey}
            membership.setdefault(h, set())
            if not membership[h]:
                membership[h].add(other_id)
        done_brands.add(bkey)
        done_path.write_text(json.dumps(sorted(done_brands)))
        ck.write_text(
            json.dumps(
                {
                    "by_handle": by_handle,
                    "membership": {k: sorted(v) for k, v in membership.items()},
                },
                ensure_ascii=False,
            )
        )
        rows = _rows_from_maps(by_handle, membership)
        PRODUCTS_JSON.write_text(json.dumps(rows, ensure_ascii=False, indent=2))
        print(f"  checkpoint brands={sorted(done_brands)} products={len(rows)}", flush=True)
        time.sleep(0.8)

    rows = _rows_from_maps(by_handle, membership)
    PRODUCTS_JSON.write_text(json.dumps(rows, ensure_ascii=False, indent=2))
    print(f"\nWrote {len(rows)} products → {PRODUCTS_JSON}", flush=True)
    from collections import Counter

    print("by brand:", dict(Counter(r["brand_key"] for r in rows)))
    print("by sub:", dict(Counter(r["subcategory"] for r in rows).most_common(50)))


def load_ko_cache() -> dict[str, str]:
    if KO_CACHE.exists():
        return json.loads(KO_CACHE.read_text())
    return {}


def save_ko_cache(cache: dict[str, str]) -> None:
    KO_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2))


def gtx(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    out_parts: list[str] = []
    # chunk by paragraphs
    chunks = re.split(r"(\n\n+)", text)
    buf = ""
    for ch in chunks:
        if len(buf) + len(ch) > 4000 and buf:
            out_parts.append(_gtx_one(buf))
            buf = ch
        else:
            buf += ch
    if buf:
        out_parts.append(_gtx_one(buf))
    return "".join(out_parts).strip()


def _gtx_one(chunk: str) -> str:
    q = urllib.parse.quote(chunk[:4500])
    url = (
        "https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl=en&tl=ko&dt=t&q={q}"
    )
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.loads(r.read().decode())
            return "".join(part[0] for part in data[0] if part and part[0])
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2 + attempt * 3)
                continue
            raise
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return chunk  # fallback leave EN rather than crash


def polish_ko(text: str) -> str:
    t = text
    for pat, rep in GLOSSARY:
        t = re.sub(pat, rep, t, flags=re.I)
    # common MT fixes
    fixes = [
        (r"사례", "케이스"),
        (r"다이얼 크기", "케이스 사이즈"),
        (r"손목시계", "시계"),
        (r"심판을 만나보세요\.?", ""),
        (r"롤렉스\.com의\s*", "레퍼런스 "),
        (r"잠수함", "서브마리너"),
    ]
    for a, b in fixes:
        t = t.replace(a, b)
    return t


def truncate_body(text: str, limit: int = 1400) -> str:
    """Keep PDP copy short enough for one gtx call (~3–5 paragraphs)."""
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    # Prefer ending on a paragraph / sentence boundary.
    for sep in ("\n\n", "\n", ". ", "。"):
        idx = cut.rfind(sep)
        if idx >= limit // 2:
            return cut[: idx + len(sep)].strip()
    return cut.strip()


def cmd_translate(titles_only: bool = False) -> None:
    rows = json.loads(PRODUCTS_JSON.read_text())
    cache = load_ko_cache()
    lock = threading.Lock()
    jobs: list[tuple[str, str, str, str]] = []  # key, kind, src, label
    for i, r in enumerate(rows, 1):
        title = (r.get("title") or "").strip()
        if title:
            key = hashlib.sha1(f"title:{title}".encode()).hexdigest()
            if key not in cache:
                jobs.append((key, "title", title, f"[{i}/{len(rows)}] title {r['handle'][:40]}"))
        if not titles_only:
            body = truncate_body(r.get("body_en") or "")
            if body:
                key = hashlib.sha1(f"body:{body}".encode()).hexdigest()
                if key not in cache:
                    jobs.append((key, "body", body, f"[{i}/{len(rows)}] body {r['handle'][:40]}"))

    print(f"translate queue={len(jobs)} cached={len(cache)} titles_only={titles_only}", flush=True)
    n_new = 0

    def work(job: tuple[str, str, str, str]) -> tuple[str, str]:
        key, _kind, src, label = job
        print(label, flush=True)
        return key, polish_ko(gtx(src))

    workers = min(12, max(4, (os.cpu_count() or 4)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(work, j) for j in jobs]
        for fut in as_completed(futures):
            try:
                key, ko = fut.result()
            except Exception as e:
                print("  fail", e, flush=True)
                continue
            with lock:
                cache[key] = ko
                n_new += 1
                if n_new % 25 == 0:
                    save_ko_cache(cache)
                    print(f"  progress new={n_new}/{len(jobs)}", flush=True)
    save_ko_cache(cache)
    print(f"translate done, cache={len(cache)} new={n_new}", flush=True)


def ko_get(cache: dict[str, str], kind: str, src: str) -> str:
    if not src:
        return ""
    if kind == "body":
        src = truncate_body(src)
    key = hashlib.sha1(f"{kind}:{src}".encode()).hexdigest()
    return cache.get(key) or polish_ko(src if kind == "title" else "")


def product_id(brand_key: str, handle: str) -> str:
    return f"{brand_key}-{slugify(handle)}"


def local_dir(brand_key: str, handle: str) -> Path:
    meta = BRANDS[brand_key]
    return IMG_ROOT / meta["pdp"] / slugify(handle)


def cmd_images() -> None:
    rows = json.loads(PRODUCTS_JSON.read_text())
    for i, r in enumerate(rows, 1):
        dest = local_dir(r["brand_key"], r["handle"])
        dest.mkdir(parents=True, exist_ok=True)
        imgs = r.get("images") or []
        ok = 0
        for n, url in enumerate(imgs, 1):
            out = dest / f"{n}.jpg"
            if out.exists() and out.stat().st_size > 5000:
                ok += 1
                continue
            full = url if url.startswith("http") else "https:" + url
            full = full.split("?")[0] + "?width=1600"
            try:
                req = urllib.request.Request(full, headers={"User-Agent": "Mozilla/5.0"})
                data = urllib.request.urlopen(req, timeout=60).read()
                if len(data) < 2000:
                    continue
                out.write_bytes(data)
                ok += 1
            except Exception as e:
                print(f"  img fail {r['handle']} #{n}: {e}", flush=True)
            time.sleep(0.12)
        # story frames
        for s_i, src_n in enumerate([1, min(3, ok or 1), max(1, ok)], 1):
            src = dest / f"{src_n}.jpg"
            story = dest / f"story-{s_i}.jpg"
            if src.exists() and not story.exists():
                story.write_bytes(src.read_bytes())
        if i % 25 == 0 or i == len(rows):
            print(f"images {i}/{len(rows)} last={r['handle']} ok={ok}", flush=True)


def ts_str(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def build_product(r: dict, cache: dict[str, str]) -> dict | None:
    bkey = r["brand_key"]
    meta = BRANDS[bkey]
    handle = r["handle"]
    pid = product_id(bkey, handle)
    dest_rel = f"/products/{meta['pdp']}/{slugify(handle)}"
    local = local_dir(bkey, handle)
    gallery = []
    for n in range(1, 13):
        p = local / f"{n}.jpg"
        if p.exists() and p.stat().st_size > 2000:
            gallery.append(f"{dest_rel}/{n}.jpg")
    if not gallery:
        return None
    title_en = r["title"]
    title_ko = ko_get(cache, "title", title_en) or title_en
    # if title still mostly latin, light glossary polish on EN title words
    if len(re.findall(r"[가-힣]", title_ko)) < 2:
        title_ko = polish_ko(title_en)
    body_en = r.get("body_en") or ""
    body_ko = ko_get(cache, "body", body_en)
    hangul = len(re.findall(r"[가-힣]", body_ko or ""))
    latin = len(re.findall(r"[A-Za-z]", body_ko or ""))
    # Reject glossary-only EN leftovers that slipped into the KO cache.
    if hangul >= 40 and latin > hangul * 2.5 and re.search(
        r"\b(the|and|with|from|this|that|has|have|for)\b", body_ko or "", re.I
    ):
        hangul = 0
        body_ko = ""
    if hangul < 40:
        # Prefer a clean KO blurb over leftover EN catalogue copy.
        coll = next((ko for sid, (_h, ko) in meta["subs"].items() if sid == r["subcategory"]), meta["brandKo"])
        body_ko = (
            f"{title_ko} — {meta['brandKo']} {coll} 컬렉션. "
            f"DMR(David M Robinson) 영국 정품 매장 기준으로 옵션·가격을 반영했습니다. "
            f"스위스 메이드 시계로, 상세 스펙은 상품 정보와 테크 스펙을 확인해 주세요."
        )

    # features / specs from body lines when possible
    features = []
    for line in re.split(r"[\n•]+", body_en):
        line = line.strip(" -•\t")
        if 20 <= len(line) <= 120:
            features.append(polish_ko(ko_get(cache, "body", line) or line)[:80])
        if len(features) >= 8:
            break
    if len(features) < 3:
        features = [
            f"{meta['brandKo']} 정품",
            "스위스 메이드",
            "DMR 영국 공식 취급",
        ]

    gbp = float(r["gbp"])
    price = krw_from_gbp(gbp)
    stories = []
    paras = [p.strip() for p in re.split(r"\n\n+", body_ko) if p.strip()]
    titles_story = ["디자인", "다이얼 & 마감", "무브먼트 & 착용감"]
    for i in range(min(3, max(1, len(paras)))):
        img = f"{dest_rel}/story-{i+1}.jpg"
        if not (local / f"story-{i+1}.jpg").exists():
            img = gallery[min(i, len(gallery) - 1)]
        body = paras[i] if i < len(paras) else body_ko[:180]
        if len(body) < 40:
            body = body_ko[:220]
        stories.append(
            {
                "titleKo": titles_story[i] if i < len(titles_story) else f"디테일 {i+1}",
                "bodyKo": body[:500],
                "image": img,
                **({"reverse": True} if i == 1 else {}),
            }
        )

    model_ref = ""
    m = re.search(r"(?:Model Reference|레퍼런스)[^\n\d]*([0-9][0-9./\-]+)", body_en + "\n" + body_ko, re.I)
    if m:
        model_ref = m.group(1).strip()

    tech = [
        {"labelKo": "브랜드", "valueKo": meta["brandKo"]},
        {"labelKo": "컬렉션", "valueKo": next((ko for sid, (_h, ko) in meta["subs"].items() if sid == r["subcategory"]), meta["brandKo"])},
    ]
    if model_ref:
        tech.append({"labelKo": "모델 레퍼런스", "valueKo": model_ref})
    if r.get("sku"):
        tech.append({"labelKo": "DMR SKU", "valueKo": str(r["sku"])})
    tech.extend(
        [
            {"labelKo": "원산지", "valueKo": "스위스 메이드"},
            {"labelKo": "취급", "valueKo": "DMR 영국"},
        ]
    )

    return {
        "id": pid,
        "name": title_en,
        "nameKo": title_ko,
        "brand": meta["brand"],
        "price": price,
        "gbpPrice": gbp,
        "category": "watches",
        "subcategory": r["subcategory"],
        "tags": [meta["hub_id"], r["subcategory"], "dmr"],
        "descriptionKo": body_ko,
        "image": gallery[0],
        "images": gallery,
        "hoverImage": gallery[1] if len(gallery) > 1 else gallery[0],
        "sku": str(r.get("sku") or pid),
        "productCode": model_ref or str(r.get("sku") or ""),
        "sourceUrl": r["sourceUrl"],
        "inStock": bool(r.get("available", True)),
        "featuresKo": features[:12],
        "techSpecs": tech,
        "storySections": stories,
        "variants": [
            {
                "id": f"{pid}-default",
                "name": title_en,
                "nameKo": title_ko,
                "sku": str(r.get("sku") or pid),
                "gbpPrice": gbp,
                "price": price,
                "image": gallery[0],
                "images": gallery,
                "sourceUrl": r["sourceUrl"],
                "inStock": bool(r.get("available", True)),
            }
        ],
    }


def emit_catalog_ts(brand_key: str, products: list[dict]) -> str:
    meta = BRANDS[brand_key]
    lines = [
        'import type { Product } from "@/data/product-types";',
        "",
        f"/** DMR {meta['brand']} watches — GBP×1900×1.16. */",
        "const _products: Product[] = [",
    ]
    for p in products:
        lines.append("  {")
        for k, v in p.items():
            lines.append(f"    {k}: {json.dumps(v, ensure_ascii=False)},")
        lines.append("  },")
    lines += [
        "];",
        "",
        f"export const {brand_key}CatalogProducts: Product[] = _products;",
        "",
    ]
    return "\n".join(lines)


def cmd_catalog() -> None:
    rows = json.loads(PRODUCTS_JSON.read_text())
    cache = load_ko_cache()
    by_brand: dict[str, list[dict]] = {k: [] for k in BRANDS}
    skipped = 0
    for r in rows:
        prod = build_product(r, cache)
        if not prod:
            skipped += 1
            continue
        by_brand[r["brand_key"]].append(prod)

    for bkey, products in by_brand.items():
        out_dir = ROOT / "src" / "data" / bkey
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{bkey}-catalog.ts").write_text(emit_catalog_ts(bkey, products))
        (out_dir / f"{bkey}-products.ts").write_text(
            "\n".join(
                [
                    'import type { Product } from "@/data/product-types";',
                    f'import {{ {bkey}CatalogProducts }} from "@/data/{bkey}/{bkey}-catalog";',
                    "",
                    f"export const {bkey}Products: Product[] = {bkey}CatalogProducts;",
                    "",
                ]
            )
        )
        print(f"catalog {bkey}: {len(products)} products", flush=True)
    print(f"skipped (no images): {skipped}", flush=True)
    # summary json
    (CACHE / "catalog-summary.json").write_text(
        json.dumps({k: len(v) for k, v in by_brand.items()}, indent=2)
    )


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    only = None
    if len(sys.argv) >= 3 and sys.argv[1] == "scrape":
        only = sys.argv[2]
    if cmd == "scrape":
        cmd_scrape(only_brand=only)
    elif cmd == "translate":
        titles_only = "--titles-only" in sys.argv
        cmd_translate(titles_only=titles_only)
    elif cmd == "images":
        cmd_images()
    elif cmd == "catalog":
        cmd_catalog()
    elif cmd == "all":
        cmd_scrape()
        cmd_translate(titles_only=True)
        cmd_images()
        cmd_catalog()
    else:
        raise SystemExit(f"unknown command {cmd}")



if __name__ == "__main__":
    main()
