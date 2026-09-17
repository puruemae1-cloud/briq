#!/usr/bin/env python3
"""AllSaints UK SFCC scrape helpers."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from curl_cffi import requests

from al_config import IMG_ROOT, SFCC

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
    t = re.sub(r"</(?:p|li|div|h\d)>", "\n", t, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = (
        t.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&pound;", "£")
    )
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def _get(url: str, *, json_ok: bool = False, tries: int = 6) -> requests.Response:
    last: requests.Response | None = None
    headers = dict(UA_HEADERS)
    if json_ok:
        headers["Accept"] = "application/json,text/javascript,*/*"
        headers["X-Requested-With"] = "XMLHttpRequest"
    for i in range(tries):
        try:
            r = SESSION.get(url, impersonate="chrome131", timeout=55, headers=headers)
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


def fetch_plp_pids(cgid: str, *, sz: int = 48) -> list[str]:
    """Paginate Search-UpdateGrid for a category id."""
    all_pids: list[str] = []
    start = 0
    while start < 5000:
        q = urlencode({"cgid": cgid, "start": start, "sz": sz})
        url = f"{SFCC}/Search-UpdateGrid?{q}"
        html = _get(url).text
        pids = list(dict.fromkeys(re.findall(r'data-pid="([^"]+)"', html)))
        if not pids:
            break
        all_pids.extend(pids)
        # Site often caps page size below requested `sz` (e.g. 24). Advance by
        # whatever we actually received; stop only on a short/empty page vs prior.
        start += len(pids)
        if len(pids) < 12:
            break
        time.sleep(0.15)
    # unique preserve order
    seen: set[str] = set()
    out: list[str] = []
    for p in all_pids:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def fetch_product(pid: str, *, size: str | None = None, color: str | None = None) -> dict:
    params: dict[str, str] = {"pid": pid, "quantity": "1"}
    if color:
        params[f"dwvar_{pid}_color"] = color
    if size:
        params[f"dwvar_{pid}_size"] = size
    url = f"{SFCC}/Product-Variation?{urlencode(params)}"
    r = _get(url, json_ok=True)
    return r.json()


def gbp_from_price(price: dict | None) -> float | None:
    if not isinstance(price, dict):
        return None
    sales = price.get("sales") or {}
    lst = price.get("list") or {}
    for obj in (sales, lst):
        if isinstance(obj, dict) and obj.get("value") is not None:
            try:
                return float(obj["value"])
            except (TypeError, ValueError):
                continue
    return None


def list_gbp_from_price(price: dict | None) -> float | None:
    if not isinstance(price, dict):
        return None
    lst = price.get("list") or {}
    if isinstance(lst, dict) and lst.get("value") is not None:
        try:
            v = float(lst["value"])
            sale = gbp_from_price(price)
            if sale is not None and v > sale:
                return v
        except (TypeError, ValueError):
            return None
    return None


def image_urls_from_product(prod: dict) -> list[str]:
    """Prefer zoom gallery; force JPEG transform."""
    urls: list[str] = []
    zoom = ((prod.get("zoomImages") or {}).get("zoom")) or []
    large = ((prod.get("images") or {}).get("large")) or []
    src = zoom if zoom else large
    for img in src:
        if not isinstance(img, dict):
            continue
        if img.get("isVideo") or img.get("fitGuide") or img.get("empty"):
            continue
        u = str(img.get("absURL") or img.get("url") or "")
        if not u:
            continue
        u = u.replace("f_auto", "f_jpg")
        if u not in urls:
            urls.append(u)
    return urls


def download_image(url: str, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 2000:
        return True
    try:
        r = SESSION.get(url, impersonate="chrome131", timeout=60, headers=UA_HEADERS)
        if r.status_code != 200 or len(r.content) < 1500:
            return False
        ct = (r.headers.get("content-type") or "").lower()
        if "image" not in ct and not r.content[:3] in (b"\xff\xd8\xff", b"\x89PN"):
            # still save if looks like jpeg/png
            if r.content[:3] != b"\xff\xd8\xff" and r.content[:8] != b"\x89PNG\r\n\x1a\n":
                return False
        dest.write_bytes(r.content)
        return True
    except Exception:
        return False


def materialize_images(pid: str, urls: list[str], *, max_n: int = 8) -> list[str]:
    folder = IMG_ROOT / slugify(pid)
    local: list[str] = []
    for i, url in enumerate(urls[:max_n], start=1):
        dest = folder / f"{i}.jpg"
        if download_image(url, dest):
            local.append(f"/products/al-pdp/{folder.name}/{i}.jpg")
        time.sleep(0.05)
    return local


def html_list_items(html: str | None) -> list[str]:
    if not html:
        return []
    items = re.findall(r"<li[^>]*>(.*?)</li>", str(html), flags=re.I | re.S)
    out: list[str] = []
    for it in items:
        t = clean_html_text(it)
        if t:
            out.append(t)
    if out:
        return out
    t = clean_html_text(html)
    return [t] if t else []


def parse_size_guide_table(html: str | None) -> dict | None:
    """Parse official sizeAndFit HTML table into Briq sizeChart shape."""
    if not html:
        return None
    # Prefer first data table
    tables = re.findall(r"<table[\s\S]*?</table>", html, flags=re.I)
    if not tables:
        return None
    table = tables[0]
    rows_html = re.findall(r"<tr[\s\S]*?</tr>", table, flags=re.I)
    matrix: list[list[str]] = []
    for rh in rows_html:
        cells = re.findall(r"<t[hd][^>]*>([\s\S]*?)</t[hd]>", rh, flags=re.I)
        vals = [clean_html_text(c).replace("\xa0", "").strip() for c in cells]
        vals = [v if v != "" else "—" for v in vals]
        if any(v not in {"—", ""} for v in vals):
            matrix.append(vals)
    if len(matrix) < 2:
        return None
    # First data row often headers (blank + sizes)
    header = matrix[0]
    body = matrix[1:]
    # Normalize header: first cell blank / label
    if header and (header[0] in {"—", "", "&nbsp;"} or header[0].lower() in {"size", "uk"}):
        headers = ["구분", *[h for h in header[1:]]]
        rows = []
        for r in body:
            if not r:
                continue
            label = r[0]
            rest = r[1 : len(headers)]
            while len(rest) < len(headers) - 1:
                rest.append("—")
            rows.append([label, *rest[: len(headers) - 1]])
    else:
        headers = [f"C{i}" for i in range(len(header))]
        rows = matrix
    if len(rows) < 1 or len(headers) < 2:
        return None
    return {
        "headers": headers,
        "rows": rows,
    }


def extract_sizes(prod: dict) -> list[dict]:
    """Build size rows; fetch per-size price/availability when URLs present."""
    sizes: list[dict] = []
    vas = prod.get("variationAttributes") or []
    size_va = next(
        (va for va in vas if str(va.get("attributeId") or "").lower() == "size"),
        None,
    )
    if not size_va:
        # one-size / no size axis
        gbp = gbp_from_price(prod.get("price"))
        return [
            {
                "id": str(prod.get("id") or ""),
                "value": "OS",
                "displayValue": "OS",
                "inStock": bool(prod.get("available", True)),
                "gbpPrice": gbp,
                "listGbpPrice": list_gbp_from_price(prod.get("price")),
            }
        ]

    color_va = next(
        (va for va in vas if str(va.get("attributeId") or "").lower() == "color"),
        None,
    )
    color_val = None
    if color_va:
        for v in color_va.get("values") or []:
            if v.get("selected") or v.get("selectable"):
                color_val = v.get("value") or v.get("id")
                if v.get("selected"):
                    break

    pid = str(prod.get("id") or "")
    base_gbp = gbp_from_price(prod.get("price"))
    for val in size_va.get("values") or []:
        size_code = str(val.get("value") or val.get("id") or "").strip()
        if not size_code:
            continue
        display = str(val.get("displayValue") or size_code).strip()
        in_stock = bool(val.get("selectable", True)) and not bool(val.get("isSoldOut", False))
        gbp = base_gbp
        list_gbp = None
        # Hit variation URL for accurate stock/price when present.
        var_url = val.get("url")
        try:
            if var_url:
                rr = _get(str(var_url), json_ok=True)
                vp = (rr.json() or {}).get("product") or {}
                gbp = gbp_from_price(vp.get("price")) or gbp
                list_gbp = list_gbp_from_price(vp.get("price"))
                in_stock = bool(vp.get("available", in_stock))
            elif size_code.upper() != "OS":
                vp = fetch_product(pid, size=size_code, color=color_val).get("product") or {}
                gbp = gbp_from_price(vp.get("price")) or gbp
                list_gbp = list_gbp_from_price(vp.get("price"))
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
    return sizes


def scrape_leaf_rows(
    leaf: dict,
    *,
    limit: int = 0,
    skip_ids: set[str] | None = None,
    pdp: bool = True,
) -> list[dict]:
    skip_ids = skip_ids or set()
    cgid = leaf["cgid"]
    print(f"  PLP {leaf['id']} cgid={cgid}", flush=True)
    pids = fetch_plp_pids(cgid)
    print(f"  plp products={len(pids)}", flush=True)
    rows: list[dict] = []
    tagged = 0
    for i, pid in enumerate(pids, start=1):
        if pid in skip_ids:
            # Still emit a collections-only stub so merge unions leaf tags.
            rows.append(
                {
                    "id": pid,
                    "sku": pid,
                    "collections": list(leaf.get("collections") or []),
                    "leafId": leaf["id"],
                    "cgid": cgid,
                }
            )
            tagged += 1
            continue
        row: dict[str, Any] = {
            "id": pid,
            "sku": pid,
            "collections": list(leaf.get("collections") or []),
            "leafId": leaf["id"],
            "cgid": cgid,
            "url": f"https://www.allsaints.com/on/demandware.store/Sites-allsaints-uk-Site/en_GB/Product-Show?pid={pid}",
        }
        if pdp:
            try:
                data = fetch_product(pid)
                prod = data.get("product") or {}
                row["name"] = prod.get("productName") or pid
                row["brand"] = prod.get("brand") or "AllSaints"
                row["link"] = prod.get("selectedProductUrl") or prod.get("link") or ""
                row["gbpPrice"] = gbp_from_price(prod.get("price"))
                row["listGbpPrice"] = list_gbp_from_price(prod.get("price"))
                row["inStock"] = bool(prod.get("available", True))
                row["shortDescription"] = html_list_items(prod.get("shortDescription"))
                row["longDescription"] = html_list_items(prod.get("longDescription"))
                row["description"] = clean_html_text(prod.get("productIntroduction") or "")
                row["modelCopy"] = clean_html_text(prod.get("getFitGuideModelCopy") or "")
                row["stylistsTips"] = clean_html_text(prod.get("stylistsTips") or "")
                row["notesFromAtelier"] = clean_html_text(prod.get("notesFromAtelier") or "")
                row["sizeChartId"] = prod.get("sizeChartId") or ""
                row["sizeAndFit"] = prod.get("sizeAndFit") or ""
                row["sizeGuide"] = parse_size_guide_table(prod.get("sizeAndFit"))
                row["fabricAndCare"] = prod.get("fabricAndCare") or {}
                row["originCountry"] = prod.get("originCountryFullName") or prod.get("originCountry")
                # colour
                color_name = ""
                for va in prod.get("variationAttributes") or []:
                    if str(va.get("attributeId") or "").lower() == "color":
                        for v in va.get("values") or []:
                            if v.get("selected") or v.get("selectable"):
                                color_name = str(v.get("displayValue") or v.get("value") or "")
                                if v.get("selected"):
                                    break
                row["color"] = color_name
                row["imageUrls"] = image_urls_from_product(prod)
                row["sizes"] = extract_sizes(prod)
                row["localImages"] = materialize_images(pid, row["imageUrls"])
                time.sleep(0.12)
            except Exception as e:
                row["pdpError"] = f"{type(e).__name__}: {e}"
                print(f"    WARN pdp {pid}: {e}", flush=True)
        rows.append(row)
        if i % 5 == 0 or i == len(pids):
            print(f"    {i}/{len(pids)} saved_rows={len(rows)} tagged_skip={tagged}", flush=True)
        if limit and (len(rows) - tagged) >= limit:
            break
    return rows
