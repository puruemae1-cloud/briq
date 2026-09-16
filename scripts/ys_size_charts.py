#!/usr/bin/env python3
"""Official Saint Laurent clothing size charts (UK/GB site + retailer mirrors).

Sources:
  - Saint Laurent size-guide PDF (EN): https://saint-laurent.dam.kering.com/m/7b5691e71cfe23a1/original/Size-guide-EN.pdf
  - Neiman Marcus Saint Laurent Size Guide (official conversion + body cm)
  - Product PDP size labels: "YSL F34 / GB 6", "YSL 46 / GB 36", "YSL 41 / GB 16"
"""
from __future__ import annotations

import re
from typing import Iterable


def _norm_ysl(token: str) -> str:
    s = (token or "").strip().upper().replace("_", ".")
    s = re.sub(r"^YSL\s*", "", s)
    s = re.sub(r"^F\s*", "", s)
    s = s.strip()
    # Drop trailing half markers already in token; keep numeric core when possible.
    m = re.match(r"^(\d+(?:\.\d+)?)", s)
    return m.group(1) if m else s


def parse_ys_size_token(display: str) -> tuple[str, str]:
    """Parse PDP display into (YSL, GB).

    Handles:
      YSL F34 / GB 6
      F34 / GB 6
      YSL 41 / GB 16
      YSL 40 / GB 15 ¾
      46
    """
    text = (display or "").strip()
    m = re.search(
        r"(?:YSL\s*)?(?:F\s*)?([0-9]+(?:[._][0-9]+)?)\s*/\s*GB\s*([0-9]+(?:[._][0-9]+)?(?:\s*[½¾¼])?)",
        text,
        re.I,
    )
    if m:
        ysl = m.group(1).replace("_", ".")
        gb = re.sub(r"\s+", " ", m.group(2).replace("_", ".")).strip()
        gb = gb.replace("1/2", "½").replace("3/4", "¾").replace("1/4", "¼")
        return ysl, gb
    m = re.search(r"(?:YSL\s*)?(?:F\s*)?([0-9]+(?:[._][0-9]+)?)", text, re.I)
    if m:
        return m.group(1).replace("_", "."), ""
    return text, ""


def collect_ysl_sizes(sizes: Iterable[dict] | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for s in sizes or []:
        disp = str(s.get("displayValue") or s.get("value") or "")
        ysl, _ = parse_ys_size_token(disp)
        key = _norm_ysl(ysl)
        if not key or key in {"U", "TU", "OS"}:
            continue
        if key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


# --- Women RTW (official conversion + body cm) ---
_WOMEN_YSL = ["32", "34", "36", "38", "40", "42", "44", "46", "48"]
_WOMEN_LETTER = ["XXS", "XS", "S", "M", "L", "XL", "XXL", "XXL", ""]
_WOMEN_FR = _WOMEN_YSL
_WOMEN_DE = ["30", "32", "34", "36", "38", "40", "42", "44", "46"]
_WOMEN_IT = ["36", "38", "40", "42", "44", "46", "48", "50", "52"]
_WOMEN_JP = ["5", "7", "9", "11", "13", "15", "17", "19", "21"]
_WOMEN_KR = ["33", "44", "55", "66", "77", "88", "90", "95", "100"]
_WOMEN_ES = _WOMEN_YSL
_WOMEN_GB = ["4", "6", "8", "10", "12", "14", "16", "18", "20"]
_WOMEN_US = ["0", "2", "4", "6", "8", "10", "12", "14", "16"]
_WOMEN_CHEST = ["78", "81", "84", "87", "91", "95", "99", "103", "107"]
_WOMEN_WAIST = ["58", "61", "64", "67", "70", "75", "79", "83", "87"]
_WOMEN_HIP = ["81", "85", "89", "93", "97", "101", "105", "109", "113"]

# --- Men RTW ---
# YSL menswear labels match IT; GB/US chest from official guide / PDP (YSL−10).
_MEN_YSL = ["42", "44", "46", "48", "50", "52", "54", "56", "58"]
_MEN_LETTER = ["", "XXXS", "XXS", "XS", "S", "M", "L", "XL", "XXL"]
_MEN_GB = ["32", "34", "36", "38", "40", "42", "44", "46", "48"]
_MEN_US = _MEN_GB
_MEN_FR = _MEN_YSL
_MEN_IT = _MEN_YSL
_MEN_DE = _MEN_YSL
_MEN_ES = _MEN_YSL
_MEN_KR = ["90", "90", "95", "100", "105", "110", "115", "120", "125"]
_MEN_COLLAR_CM = ["33", "34", "35", "36", "37", "38", "39", "40", "41"]
_MEN_CHEST = ["76", "80", "84", "88", "92", "96", "100", "104", "108"]
_MEN_WAIST = ["60", "64", "68", "72", "76", "80", "84", "88", "92"]

# --- Men shirts (collar) ---
_SHIRT_YSL = ["36", "37", "38", "39", "40", "41", "42", "43", "44"]
_SHIRT_GB = ["14", "14½", "15", "15½", "15¾", "16", "16½", "17", "17½"]
_SHIRT_COLLAR = _SHIRT_YSL
_SHIRT_CHEST = ["86", "88", "90", "92", "96", "100", "104", "108", "112"]
_SHIRT_WAIST = ["72", "74", "76", "78", "82", "86", "90", "94", "98"]


def _filter_indices(all_ysl: list[str], wanted: list[str] | None) -> list[int]:
    if not wanted:
        return list(range(len(all_ysl)))
    want = {_norm_ysl(x) for x in wanted}
    idxs = [i for i, y in enumerate(all_ysl) if _norm_ysl(y) in want]
    return idxs or list(range(len(all_ysl)))


def _pick(rows: list[str], idxs: list[int]) -> list[str]:
    return [rows[i] for i in idxs]


def women_rtw_size_chart(sizes: list[dict] | None = None) -> dict:
    wanted = collect_ysl_sizes(sizes)
    idxs = _filter_indices(_WOMEN_YSL, wanted)
    ysl = _pick(_WOMEN_YSL, idxs)
    conv_headers = ["구분", *ysl]
    conv_rows = [
        ["YSL", *ysl],
        ["국제", *_pick(_WOMEN_LETTER, idxs)],
        ["FR", *_pick(_WOMEN_FR, idxs)],
        ["IT", *_pick(_WOMEN_IT, idxs)],
        ["GB", *_pick(_WOMEN_GB, idxs)],
        ["US", *_pick(_WOMEN_US, idxs)],
        ["DE", *_pick(_WOMEN_DE, idxs)],
        ["KR", *_pick(_WOMEN_KR, idxs)],
        ["JP", *_pick(_WOMEN_JP, idxs)],
        ["ES", *_pick(_WOMEN_ES, idxs)],
    ]
    body_rows = [
        ["YSL", *ysl],
        ["가슴 (cm)", *_pick(_WOMEN_CHEST, idxs)],
        ["허리 (cm)", *_pick(_WOMEN_WAIST, idxs)],
        ["엉덩이 (cm)", *_pick(_WOMEN_HIP, idxs)],
    ]
    return {
        "id": "ys-women-rtw",
        "titleKo": "생로랑 여성 의류 사이즈 가이드",
        "noteKo": "공홈·공식 사이즈 가이드 기준입니다. 스타일·소재에 따라 핏이 달라질 수 있습니다.",
        "headers": conv_headers,
        "rows": conv_rows,
        "tabs": [
            {
                "id": "conversion",
                "labelKo": "국가별 환산",
                "headers": conv_headers,
                "rows": conv_rows,
            },
            {
                "id": "body",
                "labelKo": "신체 치수 (cm)",
                "headers": conv_headers,
                "rows": body_rows,
            },
        ],
    }


def men_rtw_size_chart(sizes: list[dict] | None = None) -> dict:
    wanted = collect_ysl_sizes(sizes)
    # Shirt-like collar sizes (36–44 continuous) use shirt chart.
    if wanted and all(
        re.fullmatch(r"\d+", w) and 36 <= int(float(w)) <= 44 for w in wanted
    ):
        # Distinguish jackets (even 46+) vs shirts: if max <= 44 and includes odd → shirt
        nums = [int(float(w)) for w in wanted]
        if max(nums) <= 44 and any(n % 2 == 1 for n in nums):
            return men_shirt_size_chart(sizes)

    idxs = _filter_indices(_MEN_YSL, wanted)
    ysl = _pick(_MEN_YSL, idxs)
    conv_headers = ["구분", *ysl]
    conv_rows = [
        ["YSL", *ysl],
        ["국제", *_pick(_MEN_LETTER, idxs)],
        ["IT / FR", *_pick(_MEN_IT, idxs)],
        ["GB / US", *_pick(_MEN_GB, idxs)],
        ["DE", *_pick(_MEN_DE, idxs)],
        ["KR", *_pick(_MEN_KR, idxs)],
    ]
    body_rows = [
        ["YSL", *ysl],
        ["목둘레 (cm)", *_pick(_MEN_COLLAR_CM, idxs)],
        ["가슴 (cm)", *_pick(_MEN_CHEST, idxs)],
        ["허리 (cm)", *_pick(_MEN_WAIST, idxs)],
    ]
    return {
        "id": "ys-men-rtw",
        "titleKo": "생로랑 남성 의류 사이즈 가이드",
        "noteKo": "공홈·공식 사이즈 가이드 기준입니다. 슬림 핏이 많아 한 사이즈 업을 권장하는 스타일도 있습니다.",
        "headers": conv_headers,
        "rows": conv_rows,
        "tabs": [
            {
                "id": "conversion",
                "labelKo": "국가별 환산",
                "headers": conv_headers,
                "rows": conv_rows,
            },
            {
                "id": "body",
                "labelKo": "신체 치수 (cm)",
                "headers": conv_headers,
                "rows": body_rows,
            },
        ],
    }


def men_shirt_size_chart(sizes: list[dict] | None = None) -> dict:
    wanted = collect_ysl_sizes(sizes)
    idxs = _filter_indices(_SHIRT_YSL, wanted)
    ysl = _pick(_SHIRT_YSL, idxs)
    headers = ["구분", *ysl]
    conv_rows = [
        ["YSL (목둘레)", *ysl],
        ["GB", *_pick(_SHIRT_GB, idxs)],
        ["목둘레 (cm)", *_pick(_SHIRT_COLLAR, idxs)],
    ]
    body_rows = [
        ["YSL", *ysl],
        ["가슴 (cm)", *_pick(_SHIRT_CHEST, idxs)],
        ["허리 (cm)", *_pick(_SHIRT_WAIST, idxs)],
    ]
    return {
        "id": "ys-men-shirts",
        "titleKo": "생로랑 남성 셔츠 사이즈 가이드",
        "noteKo": "공홈 표기(YSL 목둘레 / GB)와 공식 가이드를 따릅니다.",
        "headers": headers,
        "rows": conv_rows,
        "tabs": [
            {
                "id": "conversion",
                "labelKo": "칼라 환산",
                "headers": headers,
                "rows": conv_rows,
            },
            {
                "id": "body",
                "labelKo": "신체 치수 (cm)",
                "headers": headers,
                "rows": body_rows,
            },
        ],
    }


def size_chart_for_rtw(
    sizes: list[dict] | None,
    *,
    mens: bool,
    leaf_hint: str = "",
) -> dict | None:
    usable = collect_ysl_sizes(sizes)
    if len(usable) < 1:
        return None
    hint = (leaf_hint or "").lower()
    if mens:
        if "shirt" in hint:
            return men_shirt_size_chart(sizes)
        return men_rtw_size_chart(sizes)
    return women_rtw_size_chart(sizes)
