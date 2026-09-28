"""AllSaints clothing size guides — official body-measurement / conversion tables on every PDP.

Most AllSaints PDPs only reference a shared size chart (``sizechart-women-clothing``…) and
many have no product measurement table, so Briq showed no 사이즈표. This module fetches the
official shared charts (cached in ``al-official-size-guides.json``) and builds a tabbed
Korean chart: product measurements (when the PDP has them), body cm, body inch, conversion.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUIDES_JSON = ROOT / "src" / "data" / "al" / "al-official-size-guides.json"
SFCC = "https://www.allsaints.com/on/demandware.store/Sites-allsaints-uk-Site/en_GB"

OFFICIAL_IDS = (
    "sizechart-women-clothing",
    "sizechart-men-clothing",
    "sizechart-women-jeans",
    "sizechart-men-jeans",
)

LABEL_KO = {
    "size": "사이즈",
    "bust": "가슴둘레",
    "chest": "가슴둘레",
    "waist": "허리둘레",
    "hip": "엉덩이둘레",
    "low hip": "엉덩이둘레",
    "seat": "엉덩이둘레",
    "neck": "목둘레",
    "inside leg length": "안쪽 다리 길이",
    "inseam length": "안쪽 다리 길이",
    "inseam length - regular": "안쪽 다리 길이 (레귤러)",
    "inseam length - long": "안쪽 다리 길이 (롱)",
    "thigh width": "허벅지둘레",
    "calf": "종아리둘레",
    "knee": "무릎둘레",
    "hem": "밑단 둘레",
    "length": "총장",
    "sleeve length": "소매 길이",
    "shoulder width": "어깨너비",
    "sleeve opening": "소매 끝 둘레",
    "front rise": "앞 밑위",
    "back rise": "뒤 밑위",
    "france/spain": "프랑스/스페인",
    "germany": "독일",
    "italy": "이탈리아",
    "japan": "일본",
    "korea": "한국",
    "australia": "호주",
    "uk/australia": "UK/호주",
    "uk/us/australia": "UK/US/호주",
    "euro": "EU",
}


def label_ko(label: str) -> str:
    key = re.sub(r"\s+", " ", str(label or "")).strip()
    return LABEL_KO.get(key.lower(), key)


def _cells(tr: str) -> list[str]:
    out: list[str] = []
    for m in re.finditer(r"<t[hd]([^>]*)>([\s\S]*?)</t[hd]>", tr, re.I):
        attrs, body = m.group(1), m.group(2)
        text = html.unescape(re.sub(r"<[^>]+>", " ", body))
        text = re.sub(r"\s+", " ", text).strip()
        span = re.search(r'colspan="?(\d+)', attrs)
        out.extend([text] * (int(span.group(1)) if span else 1))
    return out


def _table(matrix: list[list[str]]) -> dict:
    """First row = header unless it repeats sizes (colspan); then the next row is the header."""
    first = matrix[0]
    if len(set(first[1:])) < len(first[1:]) and len(matrix) > 1:
        head, body = matrix[1], [first, *matrix[2:]]
    else:
        head, body = first, matrix[1:]
    width = len(head)
    rows = []
    for r in body:
        r = (r + ["—"] * width)[:width]
        rows.append([label_ko(r[0]), *r[1:]])
    return {"headers": [label_ko(head[0]), *head[1:]], "rows": rows}


def parse_official(content_html: str) -> dict | None:
    content = re.sub(r"<!--[\s\S]*?-->", "", content_html or "")
    tables = []
    for t in re.findall(r"<table[\s\S]*?</table>", content, re.I):
        matrix = [c for c in (_cells(tr) for tr in re.findall(r"<tr[\s\S]*?</tr>", t, re.I)) if c]
        if len(matrix) >= 2:
            tables.append(_table(matrix))
    if len(tables) < 3:
        return None
    return {"cm": tables[0], "inch": tables[1], "conversion": tables[2]}


def fetch_official_guides() -> dict[str, dict]:
    from curl_cffi import requests as crequests

    out: dict[str, dict] = {}
    for cid in OFFICIAL_IDS:
        r = crequests.get(f"{SFCC}/Product-SizeChart?cid={cid}", impersonate="chrome131", timeout=40)
        r.raise_for_status()
        parsed = parse_official(r.json().get("content") or "")
        if not parsed:
            raise ValueError(f"unparsed size chart {cid}")
        out[cid] = parsed
    return out


def load_guides(refresh: bool = False) -> dict[str, dict]:
    if refresh:
        try:
            guides = fetch_official_guides()
            GUIDES_JSON.write_text(json.dumps(guides, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return guides
        except Exception as e:  # keep last good copy when the site blocks / changes
            print(f"WARN AllSaints size guides refresh failed, using cached copy: {e}", flush=True)
    return json.loads(GUIDES_JSON.read_text(encoding="utf-8"))


def _feet_to_cm(note: str) -> str:
    def repl(m: re.Match) -> str:
        ft, inch = int(m.group(1)), int(m.group(2))
        return f"{round((ft * 12 + inch) * 2.54)}cm({ft}'{inch}\")"

    note = re.sub(r"(\d)\s*피트\s*(\d{1,2})\s*인치", repl, note or "")
    return re.sub(r"(\d)\s*'\s*(\d{1,2})(?![\d\"])", repl, note)


def guide_id_for(product: dict, raw_chart_id: str) -> str | None:
    if raw_chart_id in OFFICIAL_IDS:
        return raw_chart_id
    if raw_chart_id:  # shoes / other official charts are handled elsewhere
        return None
    cols = set(product.get("alCollections") or [])
    sub = str(product.get("subcategory") or "")
    gender = "men" if "al-men" in cols or sub.startswith("al-men") else "women"
    jeans = bool(re.search(r"jeans|trousers|leggings", sub))
    return f"sizechart-{gender}-{'jeans' if jeans else 'clothing'}"


def _has_sizes(product: dict) -> bool:
    sizes = {str(v.get("size") or "").strip().upper() for v in product.get("variants") or []}
    return bool(sizes - {"", "OS", "ONE SIZE"})


def build_chart(product: dict, raw_chart_id: str, guides: dict[str, dict]) -> dict | None:
    gid = guide_id_for(product, raw_chart_id)
    if not gid or gid not in guides or not _has_sizes(product):
        return None
    guide = guides[gid]
    old = product.get("sizeChart") or {}
    garment = next((t for t in old.get("tabs") or [] if t.get("id") == "garment"), None)
    if garment is None and old.get("rows") and not old.get("tabs"):
        garment = {"headers": old["headers"], "rows": old["rows"]}
    tabs = []
    if garment:
        tabs.append({
            "id": "garment",
            "labelKo": "제품 실측 (cm)",
            "headers": [label_ko(h) for h in garment["headers"]],
            "rows": [[label_ko(r[0]), *r[1:]] for r in garment["rows"]],
        })
    tabs += [
        {"id": "body-cm", "labelKo": "신체 치수 (cm)", **guide["cm"]},
        {"id": "body-inch", "labelKo": "신체 치수 (inch)", **guide["inch"]},
        {"id": "conversion", "labelKo": "국가별 사이즈", **guide["conversion"]},
    ]
    gender = "남성" if "-men-" in gid else "여성"
    kind = "청바지·팬츠" if gid.endswith("jeans") else "의류"
    old_note = str(old.get("noteKo") or "").split(" · ")[0]
    model = _feet_to_cm(old_note) if old_note.startswith("모델") else ""
    note = "신체 치수 기준 공식 사이즈 가이드입니다. 제품 실측은 스타일·소재에 따라 다를 수 있습니다."
    return {
        "id": gid,
        "titleKo": f"올세인츠 {gender} {kind} 사이즈 가이드",
        "noteKo": f"{model} · {note}" if model else note,
        "headers": tabs[0]["headers"],
        "rows": tabs[0]["rows"],
        "tabs": tabs,
    }
