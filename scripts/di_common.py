#!/usr/bin/env python3
"""Shared Christian Dior (GB) Maison / tableware scrape helpers."""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMG_ROOT = ROOT / "public/products/di-pdp"

BASE = "https://www.dior.com"
LANG = "en_gb"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"
)

# Official tableware leaves (Art de la Table).
TABLEWARE_LEAVES: list[dict[str, str]] = [
    {
        "id": "di-tableware-all",
        "slug": "all-tableware",
        "label": "All Tableware",
        "labelKo": "전체",
        "url": f"{BASE}/{LANG}/fashion/maison/tableware/all-tableware",
        "stage": "3",
    },
    {
        "id": "di-plates-bowls",
        "slug": "plates-and-bowls",
        "label": "Plates & Bowls",
        "labelKo": "플레이트 & 보울",
        "url": f"{BASE}/{LANG}/fashion/maison/tableware/plates-and-bowls",
        "stage": "1",
    },
    {
        "id": "di-glasses",
        "slug": "glasses",
        "label": "Glasses",
        "labelKo": "글라스",
        "url": f"{BASE}/{LANG}/fashion/maison/tableware/glasses",
        "stage": "2",
    },
    {
        "id": "di-carafes",
        "slug": "carafes",
        "label": "Carafes",
        "labelKo": "카라페",
        "url": f"{BASE}/{LANG}/fashion/maison/tableware/carafes",
        "stage": "2",
    },
    {
        "id": "di-tea-coffee",
        "slug": "tea-coffee",
        "label": "Tea & Coffee",
        "labelKo": "티 & 커피",
        "url": f"{BASE}/{LANG}/fashion/maison/tableware/tea-coffee",
        "stage": "3",
    },
    {
        "id": "di-cutlery",
        "slug": "cutlery",
        "label": "Cutlery",
        "labelKo": "커트러리",
        "url": f"{BASE}/{LANG}/fashion/maison/tableware/cutlery",
        "stage": "2",
    },
]

# Official Objects leaves (Maison → Objects).
# Stages sized for pause-between-runs (machine stability):
#   1 — Books + Notebooks
#   2 — Desk Accessories + Paperweights + Leisure
#   3 — Candleholders & Candles
#   4 — Small Objects + Trinket Trays
#   5 — Trays (+ All Objects gap fill)
OBJECTS_LEAVES: list[dict[str, str]] = [
    {
        "id": "di-objects-all",
        "slug": "all-products",
        "label": "All Objects",
        "labelKo": "전체",
        "url": f"{BASE}/{LANG}/fashion/maison/objects/all-products",
        "stage": "5",
    },
    {
        "id": "di-books",
        "slug": "books",
        "label": "Books",
        "labelKo": "북",
        "url": f"{BASE}/{LANG}/fashion/maison/objects/books",
        "stage": "1",
    },
    {
        "id": "di-notebooks",
        "slug": "notebooks",
        "label": "Notebooks",
        "labelKo": "노트북",
        "url": f"{BASE}/{LANG}/fashion/maison/objects/notebooks",
        "stage": "1",
    },
    {
        "id": "di-desk-accessories",
        "slug": "desk-accessories",
        "label": "Desk Accessories",
        "labelKo": "데스크 악세서리",
        "url": f"{BASE}/{LANG}/fashion/maison/objects/desk-accessories",
        "stage": "2",
    },
    {
        "id": "di-paperweights",
        "slug": "paperweights",
        "label": "Paperweights",
        "labelKo": "페이퍼웨이트",
        # Facet-only leaf — scraped from All Objects and filtered (no dedicated PLP).
        "url": f"{BASE}/{LANG}/fashion/maison/objects/all-products",
        "categoryFilter": "Paperweights",
        "stage": "5",
    },
    {
        "id": "di-leisure",
        "slug": "leisure",
        "label": "Leisure",
        "labelKo": "레저",
        "url": f"{BASE}/{LANG}/fashion/maison/objects/leisure",
        "stage": "2",
    },
    {
        "id": "di-candleholders-candles",
        "slug": "candleholders-candles",
        "label": "Candleholders & Candles",
        "labelKo": "캔들홀더 & 캔들",
        "url": f"{BASE}/{LANG}/fashion/maison/objects/candleholders-candles",
        "stage": "3",
    },
    {
        "id": "di-small-objects",
        "slug": "small-objects",
        "label": "Small Objects",
        "labelKo": "스몰 오브젝트",
        "url": f"{BASE}/{LANG}/fashion/maison/objects/small-objects",
        "stage": "4",
    },
    {
        "id": "di-trinket-trays",
        "slug": "trinket-trays",
        "label": "Trinket Trays",
        "labelKo": "트링켓 트레이",
        "url": f"{BASE}/{LANG}/fashion/maison/objects/trinket-trays",
        "stage": "4",
    },
    {
        "id": "di-trays",
        "slug": "trays",
        "label": "Trays",
        "labelKo": "트레이",
        "url": f"{BASE}/{LANG}/fashion/maison/objects/trays",
        "stage": "5",
    },
]

# Official Decor leaves (Maison → Decor).
# Stages (pause ~5 min between for machine stability):
#   1 — Decorative Pieces + Vases
#   2 — Lighting + Baskets + Wallpapers
#   3 — Furniture + All Decor gaps
DECOR_LEAVES: list[dict[str, str]] = [
    {
        "id": "di-decor-all",
        "slug": "all-products",
        "label": "All Products",
        "labelKo": "전체",
        "url": f"{BASE}/{LANG}/fashion/maison/decor/all-products",
        "stage": "3",
    },
    {
        "id": "di-decorative-pieces",
        "slug": "decorative-pieces",
        "label": "Decorative Pieces",
        "labelKo": "데코러티브 피스",
        "url": f"{BASE}/{LANG}/fashion/maison/decor/decorative-pieces",
        "stage": "1",
    },
    {
        "id": "di-vases",
        "slug": "vases",
        "label": "Vases",
        "labelKo": "화병",
        "url": f"{BASE}/{LANG}/fashion/maison/decor/vases",
        "stage": "1",
    },
    {
        "id": "di-lighting",
        "slug": "lighting",
        "label": "Lighting",
        "labelKo": "조명",
        "url": f"{BASE}/{LANG}/fashion/maison/decor/lighting",
        "stage": "2",
    },
    {
        "id": "di-baskets",
        "slug": "baskets",
        "label": "Baskets",
        "labelKo": "바스켓",
        "url": f"{BASE}/{LANG}/fashion/maison/decor/baskets",
        "stage": "2",
    },
    {
        "id": "di-wallpapers",
        "slug": "wallpapers",
        "label": "Wallpapers",
        "labelKo": "월페이퍼",
        "url": f"{BASE}/{LANG}/fashion/maison/decor/wallpapers",
        "stage": "2",
    },
    {
        "id": "di-furniture",
        "slug": "furniture",
        "label": "Furniture",
        "labelKo": "가구",
        "url": f"{BASE}/{LANG}/fashion/maison/decor/furniture",
        "stage": "3",
    },
]

# Official Textile leaves (Maison → Textile). Single-run (~79 SKUs).
TEXTILE_LEAVES: list[dict[str, str]] = [
    {
        "id": "di-textile-all",
        "slug": "all-textiles",
        "label": "All Textiles",
        "labelKo": "전체",
        "url": f"{BASE}/{LANG}/fashion/maison/textile/all-textiles",
        "stage": "1",
    },
    {
        "id": "di-cushions",
        "slug": "cushions",
        "label": "Cushions",
        "labelKo": "쿠션",
        "url": f"{BASE}/{LANG}/fashion/maison/textile/cushions",
        "stage": "1",
    },
    {
        "id": "di-bath-linen",
        "slug": "bath-linen",
        "label": "Bath Linen",
        "labelKo": "배스 리넨",
        "url": f"{BASE}/{LANG}/fashion/maison/textile/bath-linen",
        "stage": "1",
    },
    {
        "id": "di-table-linen",
        "slug": "table-linen",
        "label": "Table Linen",
        "labelKo": "테이블 리넨",
        "url": f"{BASE}/{LANG}/fashion/maison/textile/table-linen",
        "stage": "1",
    },
    {
        "id": "di-throws",
        "slug": "throws",
        "label": "Throws",
        "labelKo": "스로우",
        "url": f"{BASE}/{LANG}/fashion/maison/textile/throws",
        "stage": "1",
    },
]

PARENT_COLS_OBJECTS = [
    "dior",
    "dior-accessories",
    "di-home",
    "di-objects",
]

PARENT_COLS_DECOR = [
    "dior",
    "dior-accessories",
    "di-home",
    "di-decor",
]

PARENT_COLS_TEXTILE = [
    "dior",
    "dior-accessories",
    "di-home",
    "di-textile",
]

# Official Jewelry leaves (Jewelry & Timepieces → Jewelry by Category).
# ~167 SKUs — single run (All + Earrings + Bracelets + Rings + Necklaces).
JEWELRY_LEAVES: list[dict[str, str]] = [
    {
        "id": "di-jewelry-all",
        "slug": "all-jewelry",
        "label": "All Jewelry",
        "labelKo": "전체",
        "url": f"{BASE}/{LANG}/fashion/jewelry-timepieces/jewelry-by-category/all-jewelry",
        "stage": "1",
    },
    {
        "id": "di-earrings",
        "slug": "earrings",
        "label": "Earrings",
        "labelKo": "이어링스",
        "url": f"{BASE}/{LANG}/fashion/jewelry-timepieces/jewelry-by-category/earrings",
        "stage": "1",
    },
    {
        "id": "di-bracelets",
        "slug": "bracelets",
        "label": "Bracelets",
        "labelKo": "브레이슬릿",
        "url": f"{BASE}/{LANG}/fashion/jewelry-timepieces/jewelry-by-category/bracelets",
        "stage": "1",
    },
    {
        "id": "di-rings",
        "slug": "rings",
        "label": "Rings",
        "labelKo": "링",
        "url": f"{BASE}/{LANG}/fashion/jewelry-timepieces/jewelry-by-category/rings",
        "stage": "1",
    },
    {
        "id": "di-necklaces",
        "slug": "necklaces",
        "label": "Necklaces",
        "labelKo": "네크리스",
        "url": f"{BASE}/{LANG}/fashion/jewelry-timepieces/jewelry-by-category/necklaces",
        "stage": "1",
    },
]

PARENT_COLS_JEWELRY = [
    "dior",
    "dior-accessories",
    "di-jewelry-timepieces",
]

# Official Dior Icons hub (Jewelry & Timepieces → Dior Icons). ~14 curated SKUs.
ICONS_LEAVES: list[dict[str, str]] = [
    {
        "id": "di-dior-icons",
        "slug": "dior-icons",
        "label": "Dior Icons",
        "labelKo": "디올 아이콘즈",
        "url": f"{BASE}/{LANG}/fashion/jewelry-timepieces/dior-icons",
        "stage": "1",
    },
]

PARENT_COLS_ICONS = [
    "dior",
    "dior-accessories",
    "di-jewelry-timepieces",
]

# Official Timepieces leaves (Jewelry & Timepieces → Timepieces by Collection).
# Shop nav: Watches → Dior. Single run (~26 SKUs).
TIMEPIECE_LEAVES: list[dict[str, str]] = [
    {
        "id": "di-timepieces-all",
        "slug": "all-pieces",
        "label": "All Pieces",
        "labelKo": "전체",
        "url": f"{BASE}/{LANG}/fashion/jewelry-timepieces/timepieces-by-collection/all-pieces",
        "stage": "1",
    },
    {
        "id": "di-la-d-de-dior",
        "slug": "la-d-de-dior",
        "label": "La D de Dior",
        "labelKo": "라 D 드 디올",
        "url": f"{BASE}/{LANG}/fashion/jewelry-timepieces/timepieces-by-collection/la-d-de-dior",
        "stage": "1",
    },
    {
        "id": "di-straps",
        "slug": "straps",
        "label": "Straps",
        "labelKo": "스트랩",
        "url": f"{BASE}/{LANG}/fashion/jewelry-timepieces/timepieces-by-collection/straps",
        "stage": "1",
    },
]

PARENT_COLS_TIMEPIECE = [
    "dior",
    "dior-watches",
]


PARENT_COLS = [
    "dior",
    "dior-accessories",
    "di-home",
    "di-tableware",
]


def gbp_to_krw(gbp: float | None) -> int:
    if gbp is None:
        return 0
    raw = float(gbp) * 2100 * 1.05 * 1.15
    return int(round(raw / 10_000) * 10_000)


def slugify(text: str, *, max_len: int = 72) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return (s[:max_len] or "item").strip("-")


def extract_next_data(html: str) -> dict | None:
    m = re.search(
        r'<script[^>]+id="__NEXT_DATA__"[^>]*>([\s\S]*?)</script>',
        html,
        re.I,
    )
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def plp_hits_from_next(data: dict) -> list[dict]:
    pp = (data.get("props") or {}).get("pageProps") or {}
    qpd = pp.get("queriesProductsDictionnary") or {}
    hits: list[dict] = []
    for _key, block in qpd.items():
        if isinstance(block, dict) and isinstance(block.get("hits"), list):
            hits.extend(block["hits"])
    return hits


def image_urls_from_hit(hit: dict) -> list[str]:
    """Collect unique Scene7 / DAM image URLs from a PLP hit."""
    seen: set[str] = set()
    out: list[str] = []

    def add(uri: str | None) -> None:
        if not uri or not isinstance(uri, str):
            return
        # Prefer high-quality raw Scene7 without tiny crop presets when possible
        u = uri.split("?")[0]
        if u in seen:
            return
        if "christiandior.com" not in u and "dam-broadcast.com" not in u:
            return
        seen.add(u)
        # Request a large web-friendly JPEG
        if "christiandior.com/is/image" in u:
            out.append(f"{u}?$r2x3_default$&wid=1334&hei=2000&bfc=on&qlt=90")
        else:
            out.append(uri)

    views = hit.get("views") or {}
    for section in ("listing", "transparent"):
        block = views.get(section) or {}
        images = (block.get("images") or {}) if isinstance(block, dict) else {}
        for key in ("r2x3listing", "r9x10listing", "r2x3detail", "r9x10detail"):
            node = images.get(key)
            if isinstance(node, dict):
                add(node.get("uri"))
    for alt in views.get("alternatives") or []:
        images = ((alt or {}).get("images") or {}) if isinstance(alt, dict) else {}
        for key in ("r2x3listing", "r9x10listing"):
            node = images.get(key)
            if isinstance(node, dict):
                add(node.get("uri"))
    return out


def download_image(url: str, dest: Path, *, retries: int = 3) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > 2000:
        return True
    headers = {
        "User-Agent": UA,
        "Accept": "image/avif,image/webp,image/*,*/*",
        "Referer": f"{BASE}/{LANG}/",
    }
    last: Exception | None = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = resp.read()
            if len(data) < 500:
                raise RuntimeError("tiny image")
            dest.write_bytes(data)
            return True
        except Exception as e:
            last = e
            time.sleep(1 + i)
    print(f"  WARN image fail {dest.name}: {last}")
    return False


# Public search-only Algolia keys (also inlined in window.__ENV__ on dior.com).
ALGOLIA_MERCH_APP_ID = "KPGNQ6FJI9"
ALGOLIA_MERCH_API_KEY = "f5f95d38b9817d397651b87ba567669d"
ALGOLIA_MERCH_INDEX = "merch_prod_live_en_gb"
ALGOLIA_MERCH_INDEX_KO = "merch_prod_live_ko_kr"


def dior_code_to_object_id(code: str) -> str:
    """Algolia merch objectID: HYJ01GOP1U_C500 → prd-HYJ01GOP1UC500."""
    return "prd-" + (code or "").replace("_", "")


def algolia_merch_hits_by_codes(codes: list[str], *, batch: int = 15) -> dict[str, dict]:
    """Fetch merch index hits keyed by product code (with underscore)."""
    import urllib.parse

    by_code: dict[str, dict] = {}
    oids = [dior_code_to_object_id(c) for c in codes if c]
    oid_to_code = {dior_code_to_object_id(c): c for c in codes if c}
    url = f"https://{ALGOLIA_MERCH_APP_ID}-dsn.algolia.net/1/indexes/*/queries"
    for i in range(0, len(oids), batch):
        chunk = oids[i : i + batch]
        filt = " OR ".join(f"objectID:{oid}" for oid in chunk)
        params = urllib.parse.urlencode(
            {
                "filters": filt,
                "hitsPerPage": len(chunk) + 5,
                "attributesToRetrieve": "*",
            }
        )
        body = json.dumps(
            {"requests": [{"indexName": ALGOLIA_MERCH_INDEX, "params": params}]}
        ).encode()
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-Algolia-Application-Id": ALGOLIA_MERCH_APP_ID,
                "X-Algolia-API-Key": ALGOLIA_MERCH_API_KEY,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read())
        for h in (data.get("results") or [{}])[0].get("hits") or []:
            oid = h.get("objectID") or ""
            code = oid_to_code.get(oid)
            if code:
                by_code[code] = h
        time.sleep(0.15)
    return by_code


def gallery_urls_from_merch_hit(hit: dict) -> list[str]:
    """Scene7 gallery from Algolia merch damAssets (+ views fallback)."""
    seen: set[str] = set()
    out: list[str] = []

    def add(path: str | None) -> None:
        if not path or not isinstance(path, str):
            return
        base = path.split("?")[0]
        if base in seen:
            return
        if "christiandior.com/is/image" not in base and "dam-broadcast.com" not in base:
            return
        seen.add(base)
        if "christiandior.com/is/image" in base:
            out.append(f"{base}?$r2x3_default$&wid=1334&hei=2000&bfc=on&qlt=90")
        else:
            out.append(path)

    dam = hit.get("damAssets") or {}
    source = dam.get("sourceType") or {}
    if isinstance(source, dict):
        for arr in source.values():
            if not isinstance(arr, list):
                continue
            for asset in arr:
                if isinstance(asset, dict):
                    add(asset.get("scene7Path"))
    # Prefer PLP views when dam is sparse
    for u in image_urls_from_hit(hit):
        add(u.split("?")[0] if "?" in u else u)
    return out[:16]


def clean_dior_description(text: str | None) -> str:
    s = (text or "").strip()
    for cut in (
        "See more Gifts",
        "We use cookies",
        "Cookie Settings",
        "Delivery estimated",
        "You may also like",
        "Express payment",
    ):
        if cut in s:
            s = s.split(cut)[0].strip()
    return re.sub(r"\s+", " ", s).strip()
