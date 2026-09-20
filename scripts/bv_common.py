#!/usr/bin/env python3
"""Bottega Veneta UK SFCC scrape helpers."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urljoin

from curl_cffi import requests

from bv_config import BASE, IMG_ROOT, SFCC

SESSION = requests.Session()
UA_HEADERS = {
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
}
IMPERSONATE = "chrome131"
PLP_SZ = 36
SITEWIDE_COUNT = 2000  # bogus cgids return ~2817
MAX_WORKERS = 4


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


def html_to_text(html: str | None) -> str:
    if not html:
        return ""
    t = re.sub(r"<br\s*/?>", "\n", str(html), flags=re.I)
    t = re.sub(r"</(?:p|li|div|h\d)>", "\n", t, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = (
        t.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&#39;", "'")
        .replace("&quot;", '"')
        .replace("&pound;", "£")
    )
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def _get(
    url: str,
    *,
    json_ok: bool = False,
    referer: str | None = None,
    tries: int = 6,
) -> requests.Response:
    last: requests.Response | None = None
    headers = dict(UA_HEADERS)
    if json_ok:
        headers["Accept"] = "application/json,text/javascript,*/*"
        headers["X-Requested-With"] = "XMLHttpRequest"
    if referer:
        headers["Referer"] = referer
    for i in range(tries):
        try:
            r = SESSION.get(url, impersonate=IMPERSONATE, timeout=55, headers=headers)
            last = r
            if r.status_code == 200:
                if json_ok:
                    if r.text.strip().startswith("{"):
                        return r
                else:
                    return r
        except Exception:
            pass
        time.sleep(0.8 + i * 0.5)
    if last is None:
        raise RuntimeError(f"fetch-failed {url}")
    return last


def resolve_cgid_from_path(path: str) -> str | None:
    """Read leaf HTML and extract cgid= from searchajax / data-querystring."""
    url = path if path.startswith("http") else f"{BASE}{path}"
    r = _get(url)
    m = re.search(r'data-querystring="[^"]*cgid=([a-zA-Z0-9_-]+)', r.text)
    if m:
        return m.group(1)
    ajax = re.findall(r"searchajax\?[^\"'\s<>]*cgid=([a-zA-Z0-9_-]+)", r.text)
    return ajax[0] if ajax else None


def _plp_url(cgid: str, start: int, sz: int = PLP_SZ) -> str:
    q = urlencode(
        {
            "cgid": cgid,
            "prefn1": "akeneo_employeesSalesVisible",
            "prefv1": "false",
            "prefn2": "akeneo_markDownInto",
            "prefv2": "no_season",
            "prefn3": "countryInclusion",
            "prefv3": "GB",
            "start": start,
            "sz": sz,
        }
    )
    return f"{BASE}/en-gb/searchajax?{q}"


def parse_official_count(html: str) -> int | None:
    m = re.search(r"c-filters__count[^>]*>\s*([\d,]+)", html)
    if not m:
        return None
    try:
        return int(m.group(1).replace(",", ""))
    except ValueError:
        return None


def iter_plp(cgid: str, *, max_pages: int = 80) -> list[dict]:
    """Paginate searchajax; advance start by unique pid count in each batch.

    Returns list of {pid, url, officialCount}.
    """
    items: list[dict] = []
    seen: set[str] = set()
    start = 0
    official: int | None = None
    for _ in range(max_pages):
        html = _get(_plp_url(cgid, start)).text
        if official is None:
            official = parse_official_count(html)
            if official is not None and official >= SITEWIDE_COUNT:
                print(
                    f"  WARN cgid={cgid} official={official} looks site-wide — check leaf mapping",
                    flush=True,
                )
        # Pair tiles: data-pid + nearby product href
        batch_pids: list[str] = []
        for m in re.finditer(
            r'data-pid="([^"]+)"[\s\S]{0,600}?href="(/en-gb/[^"]+\.html)"',
            html,
        ):
            pid, href = m.group(1), m.group(2)
            if pid not in batch_pids:
                batch_pids.append(pid)
            if pid not in seen:
                seen.add(pid)
                items.append(
                    {
                        "pid": pid,
                        "url": f"{BASE}{href}",
                        "officialCount": official,
                    }
                )
        # Fallback if regex pairing fails
        if not batch_pids:
            batch_pids = list(dict.fromkeys(re.findall(r'data-pid="([^"]+)"', html)))
            hrefs = list(dict.fromkeys(re.findall(r'href="(/en-gb/[^"]+\.html)"', html)))
            for i, pid in enumerate(batch_pids):
                if pid in seen:
                    continue
                seen.add(pid)
                href = hrefs[i] if i < len(hrefs) else ""
                items.append(
                    {
                        "pid": pid,
                        "url": f"{BASE}{href}" if href else "",
                        "officialCount": official,
                    }
                )
        unique_in_batch = len(batch_pids)
        if unique_in_batch == 0:
            break
        # Advance by unique pid count (NOT sz) — editorial duplicates inflate tiles.
        start += unique_in_batch
        if official is not None and len(items) >= official:
            break
        time.sleep(0.12)

    if official is not None and len(items) != official:
        print(
            f"  WARN cgid={cgid} official={official} scraped={len(items)} mismatch",
            flush=True,
        )
    for it in items:
        it["officialCount"] = official
    return items


def fetch_product(pid: str, *, size: str | None = None, color: str | None = None) -> dict:
    params: dict[str, str] = {"pid": pid}
    if color:
        params[f"dwvar_{pid}_color"] = color
    if size:
        params[f"dwvar_{pid}_size"] = size
    url = f"{SFCC}/Product-Variation?{urlencode(params)}"
    r = _get(url, json_ok=True)
    return r.json()


def gbp_price(product: dict | None) -> float | None:
    if not isinstance(product, dict):
        return None
    price = product.get("price")
    if not isinstance(price, dict):
        return None
    for key in ("sales", "list"):
        obj = price.get(key) or {}
        if isinstance(obj, dict) and obj.get("value") is not None:
            try:
                return float(obj["value"])
            except (TypeError, ValueError):
                continue
    return None


def list_gbp_price(product: dict | None) -> float | None:
    if not isinstance(product, dict):
        return None
    price = product.get("price")
    if not isinstance(price, dict):
        return None
    lst = price.get("list") or {}
    if isinstance(lst, dict) and lst.get("value") is not None:
        try:
            v = float(lst["value"])
            sale = gbp_price(product)
            if sale is not None and v > sale:
                return v
        except (TypeError, ValueError):
            return None
    return None


def image_urls(product: dict) -> list[str]:
    """Collect official DAM URLs — packshot first, then other akeneo sets, then gallery."""
    urls: list[str] = []

    def _add(u: str) -> None:
        u = str(u or "").strip()
        if u and u not in urls:
            urls.append(u)

    def _from_list(items) -> None:
        if not isinstance(items, list):
            return
        for img in items:
            if not isinstance(img, dict) or img.get("missingImages"):
                continue
            _add(img.get("ecom") or img.get("large") or img.get("small") or "")

    ak = product.get("akeneoImages") or {}
    if isinstance(ak, dict):
        # Packshots first (canonical PDP order A/B/C…)
        _from_list(ak.get("packshot"))
        for key, items in ak.items():
            if key == "packshot":
                continue
            _from_list(items)
    # Fallback / supplemental SFCC gallery
    for key in ("hi-res", "large", "medium", "small"):
        items = (product.get("images") or {}).get(key) or []
        if not isinstance(items, list):
            continue
        for img in items:
            if not isinstance(img, dict):
                continue
            _add(img.get("ecom") or img.get("absURL") or img.get("url") or img.get("large") or "")
    return urls


def download_images(sku: str, urls: list[str], *, max_n: int = 12) -> list[str]:
    folder = IMG_ROOT / slugify(sku)
    folder.mkdir(parents=True, exist_ok=True)
    local: list[str] = []
    for i, url in enumerate(urls[:max_n], start=1):
        dest = folder / f"{i}.jpg"
        if dest.exists() and dest.stat().st_size > 2000:
            local.append(f"/products/bv-pdp/{folder.name}/{i}.jpg")
            continue
        try:
            r = SESSION.get(url, impersonate=IMPERSONATE, timeout=60, headers=UA_HEADERS)
            if r.status_code != 200 or len(r.content) < 1500:
                continue
            dest.write_bytes(r.content)
            local.append(f"/products/bv-pdp/{folder.name}/{i}.jpg")
        except Exception:
            continue
        time.sleep(0.05)
    return local


_SIZE_ALPHA_ORDER = {
    "XXS": 0,
    "XS": 1,
    "S": 2,
    "M": 3,
    "L": 4,
    "XL": 5,
    "XXL": 6,
    "XXXL": 7,
}


def _size_sort_key(val: str) -> tuple:
    s = (val or "").strip()
    up = s.upper()
    if up in {"U", "OS", "ONE SIZE", "ONESIZE", "TU", "N/A", ""}:
        return (2, 9999.0, up)
    # EU numeric (incl. half sizes)
    m = re.match(r"^(\d+(?:\.\d+)?)$", s.replace(",", "."))
    if m:
        return (0, float(m.group(1)), "")
    if up in _SIZE_ALPHA_ORDER:
        return (1, float(_SIZE_ALPHA_ORDER[up]), up)
    return (1, 500.0, up)


def sort_sizes(values: list[dict]) -> list[dict]:
    return sorted(
        values,
        key=lambda v: _size_sort_key(str(v.get("displayValue") or v.get("value") or "")),
    )


def parse_size_guide_html(html: str, *, chart_id: str = "") -> dict | None:
    """Parse Product-SizeGuideContent into Briq sizeChart shape.

    Prefer KR / UK / US / IT(EU) columns aligned on Bottega Veneta size.
    """
    if not html:
        return None
    title = html_to_text(
        (re.search(r'c-sizeguide__category[^>]*>([\s\S]*?)</', html) or [None, ""])[1]
        or ""
    )
    # Collect country tables: id → list of (bv_size, country_size)
    tables: dict[str, list[tuple[str, str]]] = {}
    for tm in re.finditer(
        r'<table[^>]*id="([^"]+)"[^>]*>([\s\S]*?)</table>',
        html,
        flags=re.I,
    ):
        tid, body = tm.group(1), tm.group(2)
        rows: list[tuple[str, str]] = []
        for tr in re.finditer(r"<tr[^>]*>([\s\S]*?)</tr>", body, flags=re.I):
            cells = [
                html_to_text(c)
                for c in re.findall(r"<td[^>]*>([\s\S]*?)</td>", tr.group(1), flags=re.I)
            ]
            if len(cells) >= 2 and cells[0]:
                rows.append((cells[0], cells[1] or "—"))
        if rows:
            tables[tid] = rows

    if not tables:
        return None

    def pick(suffix: str) -> list[tuple[str, str]] | None:
        for tid, rows in tables.items():
            if tid.endswith(suffix):
                return rows
        return None

    bv_it = pick("-IT") or pick("-FR") or next(iter(tables.values()))
    uk = pick("-UK")
    us = pick("-US")
    kr = pick("-KR")

    bv_sizes = [r[0] for r in bv_it]
    uk_map = {a: b for a, b in (uk or [])}
    us_map = {a: b for a, b in (us or [])}
    kr_map = {a: b for a, b in (kr or [])}
    it_map = {a: b for a, b in bv_it}

    headers = ["BV"]
    if uk:
        headers.append("UK")
    if us:
        headers.append("US")
    if kr:
        headers.append("KR")
    if not uk and not us and not kr:
        headers.append("사이즈")

    out_rows: list[list[str]] = []
    for sz in bv_sizes:
        row = [sz]
        if uk:
            row.append(uk_map.get(sz, "—"))
        if us:
            row.append(us_map.get(sz, "—"))
        if kr:
            row.append(kr_map.get(sz, "—"))
        if not uk and not us and not kr:
            row.append(it_map.get(sz, "—"))
        out_rows.append(row)

    if len(out_rows) < 1 or len(headers) < 2:
        return None
    return {
        "id": chart_id or "bv-size",
        "titleKo": title or "사이즈 가이드",
        "noteKo": "보테가 베네타 공홈 사이즈 가이드 기준입니다.",
        "headers": headers,
        "rows": out_rows,
    }


def fetch_size_guide(size_chart_id: str, pid: str, *, product_url: str = "") -> dict | None:
    if not size_chart_id or not pid:
        return None
    referer = product_url or f"{BASE}/en-gb/"
    # Warm PDP first (cookie / session)
    try:
        _get(referer.split("?")[0] if referer.startswith("http") else f"{BASE}{referer}")
    except Exception:
        pass
    url = f"{SFCC}/Product-SizeGuideContent?{urlencode({'fdid': size_chart_id, 'pid': pid})}"
    r = _get(url, referer=referer if referer.startswith("http") else f"{BASE}{referer}")
    return parse_size_guide_html(r.text, chart_id=size_chart_id)


def extract_sizes(prod: dict, *, refresh: bool = True) -> list[dict]:
    """Build size rows; optionally hit each size variation URL for GBP/availability."""
    vas = prod.get("variationAttributes") or []
    size_va = next(
        (va for va in vas if str(va.get("attributeId") or "").lower() == "size"),
        None,
    )
    base_gbp = gbp_price(prod)
    if not size_va:
        return [
            {
                "id": str(prod.get("id") or prod.get("productSMC") or ""),
                "value": "OS",
                "displayValue": "One Size",
                "inStock": bool(prod.get("available", True)),
                "gbpPrice": base_gbp,
                "listGbpPrice": list_gbp_price(prod),
            }
        ]

    sizes: list[dict] = []
    for val in size_va.get("values") or []:
        size_code = str(val.get("value") or val.get("id") or "").strip()
        if not size_code:
            continue
        display = str(val.get("displayValue") or size_code).strip()
        in_stock = bool(val.get("selectable", True)) and not bool(val.get("isSoldOut", False))
        gbp = base_gbp
        list_gbp = None
        var_url = val.get("url")
        if refresh and var_url:
            try:
                full = var_url if str(var_url).startswith("http") else urljoin(BASE, str(var_url))
                rr = _get(str(full), json_ok=True)
                vp = (rr.json() or {}).get("product") or {}
                gbp = gbp_price(vp) or gbp
                list_gbp = list_gbp_price(vp)
                in_stock = bool(vp.get("available", in_stock))
                time.sleep(0.08)
            except Exception:
                pass
        sizes.append(
            {
                "id": str(val.get("productId") or size_code),
                "value": size_code,
                "displayValue": display,
                "inStock": in_stock,
                "gbpPrice": gbp,
                "listGbpPrice": list_gbp,
            }
        )
    return sort_sizes(sizes)


def _bullets(html_or_list: Any) -> list[str]:
    if isinstance(html_or_list, list):
        out = []
        for x in html_or_list:
            t = html_to_text(str(x)).lstrip("• ").strip()
            if t:
                out.append(t)
        return out
    if not html_or_list:
        return []
    text = html_to_text(str(html_or_list))
    parts = re.split(r"[\n•]+", text)
    return [p.strip() for p in parts if p.strip()]


def product_row_from_pdp(
    pid: str,
    prod: dict,
    *,
    leaf: dict,
    plp_url: str = "",
    refresh_sizes: bool = True,
) -> dict:
    smc = str(prod.get("productSMC") or prod.get("styleMaterialColor") or pid)
    name = str(prod.get("productName") or prod.get("productTitle") or smc)
    color = ""
    for va in prod.get("variationAttributes") or []:
        if str(va.get("attributeId") or "").lower() == "color":
            color = str(va.get("selectedValue") or "")
            if not color:
                for v in va.get("values") or []:
                    if v.get("selected"):
                        color = str(v.get("displayValue") or v.get("value") or "")
                        break
            break

    link = prod.get("selectedProductUrl") or plp_url or ""
    if link and not str(link).startswith("http"):
        link = f"{BASE}{link}"
    size_chart_id = str(prod.get("sizeChartId") or "") or ""
    size_guide = None
    if size_chart_id:
        try:
            size_guide = fetch_size_guide(size_chart_id, smc, product_url=str(link))
        except Exception as e:
            print(f"    WARN sizeguide {smc}: {e}", flush=True)

    imgs = image_urls(prod)
    local = download_images(smc, imgs)
    sizes = extract_sizes(prod, refresh=refresh_sizes)
    gbp = gbp_price(prod)
    if gbp is None:
        gbps = [float(s["gbpPrice"]) for s in sizes if s.get("gbpPrice")]
        gbp = min(gbps) if gbps else None

    return {
        "id": smc,
        "sku": smc,
        "internalId": str(prod.get("id") or ""),
        "name": name,
        "brand": prod.get("brand") or "Bottega Veneta",
        "color": color,
        "gender": prod.get("productGender") or prod.get("gender") or "",
        "link": link.split("?")[0] if link else "",
        "url": link.split("?")[0] if link else plp_url,
        "gbpPrice": gbp,
        "listGbpPrice": list_gbp_price(prod),
        "inStock": bool(prod.get("available", True)),
        "shortDescription": _bullets(
            prod.get("shortDescriptionListSanitized")
            or prod.get("shortDescriptionList")
            or prod.get("shortDescription")
        ),
        "longDescription": _bullets(prod.get("longDescription")),
        "compactedLongDesc": html_to_text(prod.get("compactedLongDesc") or ""),
        "composition": html_to_text(prod.get("composition") or ""),
        "material": html_to_text(prod.get("material") or ""),
        "productCare": html_to_text(prod.get("productCare") or ""),
        "sizeModel": html_to_text(prod.get("sizeModel") or ""),
        "sizeChartId": size_chart_id,
        "sizeGuide": size_guide,
        "imageUrls": imgs,
        "localImages": local,
        "sizes": sizes,
        "collections": list(leaf.get("collections") or []),
        "leafId": leaf.get("id"),
        "cgid": leaf.get("cgid"),
        "hubCategory": leaf.get("_hubCategory"),
    }
