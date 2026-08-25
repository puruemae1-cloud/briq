"""Official Prada women's RTW size guides (prada.com GB, Aug 2026).

Sourced from prada.com PDP size-chart tables (Ready to wear).
"""
from __future__ import annotations

import copy
import re

# Numeric Prada / IT sizes (e.g. knitwear, tailoring)
PR_WOMEN_RTW_NUMERIC = {
    "id": "pr-women-rtw-numeric",
    "titleKo": "프라다 여성 레디투웨어 사이즈 차트",
    "noteKo": (
        "prada.com(영국) 공식 사이즈 가이드입니다. "
        "가슴·허리·엉덩이 치수는 둘레(circumference) 기준 cm입니다."
    ),
    "headers": ["Prada size", "36", "38", "40", "42", "44", "46", "48", "50"],
    "rows": [
        ["United Kingdom", "4", "6", "8", "10", "12", "14", "16", "18"],
        [
            "Chest",
            "80.4 cm",
            "84.4 cm",
            "88 cm",
            "92 cm",
            "96 cm",
            "100 cm",
            "104 cm",
            "108 cm",
        ],
        [
            "Waist",
            "59 cm",
            "62.8 cm",
            "66 cm",
            "70 cm",
            "74 cm",
            "78 cm",
            "82 cm",
            "86 cm",
        ],
        [
            "Hips",
            "86 cm",
            "89.8 cm",
            "93 cm",
            "97 cm",
            "101 cm",
            "105 cm",
            "109 cm",
            "113 cm",
        ],
    ],
}

# Letter sizes (e.g. jersey tees, some shorts/skirts)
PR_WOMEN_RTW_LETTER = {
    "id": "pr-women-rtw-letter",
    "titleKo": "프라다 여성 레디투웨어 사이즈 차트",
    "noteKo": (
        "prada.com(영국) 공식 사이즈 가이드입니다. "
        "가슴·허리·엉덩이 치수는 둘레(circumference) 기준 cm입니다."
    ),
    "headers": ["Prada size", "XXS", "XS", "S", "M", "L", "XL", "XXL"],
    "rows": [
        ["United Kingdom", "XXS", "XS", "S", "M", "L", "XL", "XXL"],
        [
            "Chest",
            "80.4 cm",
            "84.4 cm",
            "88 cm",
            "92 cm",
            "96 cm",
            "100 cm",
            "104 cm",
        ],
        [
            "Waist",
            "59 cm",
            "62.8 cm",
            "66 cm",
            "70 cm",
            "74 cm",
            "78 cm",
            "82 cm",
        ],
        [
            "Hips",
            "86 cm",
            "89.8 cm",
            "93 cm",
            "97 cm",
            "101 cm",
            "105 cm",
            "109 cm",
        ],
    ],
}

_NUMERIC_SIZE = re.compile(r"^\d{2}S?$")
_LETTER_SIZE = re.compile(r"^(XXS|XXXL|XXL|XL|XS|[SML])$", re.I)


def _variant_labels(variants: list[dict]) -> list[str]:
    out: list[str] = []
    for v in variants:
        label = str(v.get("size") or "").strip()
        if label and label.lower() != "one size":
            out.append(label)
    return out


def _chart_mode(labels: list[str]) -> str:
    numeric = [lb for lb in labels if _NUMERIC_SIZE.match(lb.upper())]
    letters = [lb for lb in labels if _LETTER_SIZE.match(lb.upper())]
    if numeric and not letters:
        return "numeric"
    if letters and not numeric:
        return "letter"
    if numeric:
        nums: list[int] = []
        for lb in numeric:
            m = re.match(r"(\d{2})", lb)
            if m:
                nums.append(int(m.group(1)))
        if nums and any(n >= 34 for n in nums):
            return "numeric"
    return "letter"


def size_chart_for_variants(variants: list[dict]) -> dict | None:
    """Return the Prada GB women's RTW chart matching the product's size picker labels."""
    labels = _variant_labels(variants)
    if not labels:
        return None
    mode = _chart_mode(labels)
    base = PR_WOMEN_RTW_NUMERIC if mode == "numeric" else PR_WOMEN_RTW_LETTER
    return copy.deepcopy(base)


# Men's ready-to-wear (prada.com GB, Aug 2026)
PR_MEN_RTW_NUMERIC = {
    "id": "pr-men-rtw-numeric",
    "titleKo": "프라다 남성 레디투웨어 사이즈 차트",
    "noteKo": (
        "prada.com(영국) 공식 사이즈 가이드입니다. "
        "Prada size는 이탈리아(IT) 기준이며, 가슴·허리 치수는 둘레(circumference) 기준 cm입니다."
    ),
    "headers": ["Prada size", "44", "46", "48", "50", "52", "54", "56"],
    "rows": [
        ["United Kingdom", "34", "36", "38", "40", "42", "44", "46"],
        [
            "Chest",
            "96 cm",
            "98 cm",
            "102 cm",
            "106 cm",
            "110 cm",
            "114 cm",
            "118 cm",
        ],
        [
            "Waist",
            "94 cm",
            "96 cm",
            "100 cm",
            "104 cm",
            "108 cm",
            "112 cm",
            "116 cm",
        ],
    ],
}

PR_MEN_RTW_LETTER = {
    "id": "pr-men-rtw-letter",
    "titleKo": "프라다 남성 레디투웨어 사이즈 차트",
    "noteKo": (
        "prada.com(영국) 공식 사이즈 가이드입니다. "
        "가슴·허리 치수는 둘레(circumference) 기준 cm입니다."
    ),
    "headers": ["Prada size", "XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL"],
    "rows": [
        ["United Kingdom", "—", "34.5", "36.5", "38.5", "40.5", "42.5", "44.5", "46.5"],
        [
            "Chest",
            "88 cm",
            "92 cm",
            "96 cm",
            "100 cm",
            "104 cm",
            "108 cm",
            "112 cm",
            "120 cm",
        ],
        [
            "Waist",
            "76 cm",
            "80 cm",
            "84 cm",
            "88 cm",
            "92 cm",
            "96 cm",
            "100 cm",
            "108 cm",
        ],
    ],
}

# Men's denim waist sizes (jeans / denim PLP)
PR_MEN_RTW_DENIM = {
    "id": "pr-men-denim-waist",
    "titleKo": "프라다 남성 데님 사이즈 차트",
    "noteKo": (
        "prada.com(영국) 데님 사이즈 가이드입니다. "
        "표기 사이즈는 허리(waist) 인치 기준이며, 허리·엉덩이 치수는 cm입니다."
    ),
    "headers": ["Waist", "29", "30", "31", "32", "33", "34", "36", "38"],
    "rows": [
        ["Waist (cm)", "74 cm", "77 cm", "79 cm", "82 cm", "84 cm", "87 cm", "92 cm", "97 cm"],
        ["Hips (cm)", "94 cm", "97 cm", "99 cm", "102 cm", "104 cm", "107 cm", "112 cm", "117 cm"],
    ],
}


def _variant_size_numbers(variants: list[dict]) -> list[int]:
    nums: list[int] = []
    for v in variants:
        label = str(v.get("size") or "")
        m = re.search(r"(\d{2})", label)
        if m:
            nums.append(int(m.group(1)))
    return nums


def size_chart_for_mens_rtw_variants(variants: list[dict]) -> dict | None:
    """Return Prada GB men's RTW chart (numeric IT, letter, or denim waist)."""
    labels = _variant_labels(variants)
    if not labels:
        return None
    nums = _variant_size_numbers(variants)
    if nums and max(nums) <= 40 and min(nums) <= 34 and max(nums) - min(nums) <= 22:
        if max(nums) < 44 or min(nums) < 40:
            return copy.deepcopy(PR_MEN_RTW_DENIM)
    mode = _chart_mode(labels)
    base = PR_MEN_RTW_NUMERIC if mode == "numeric" else PR_MEN_RTW_LETTER
    return copy.deepcopy(base)


# Official Prada women's shoes size guide (prada.com GB PDP size chart).
PR_WOMEN_SHOES_SIZE_CHART = {
    "id": "pr-women-shoes",
    "titleKo": "프라다 여성 슈즈 사이즈 차트",
    "noteKo": (
        "prada.com(영국) 공식 슈즈 사이즈 가이드입니다. "
        "Prada size는 이탈리아(IT) 기준이며, Foot은 발 길이(cm)입니다. "
        "Briq 표기 사이즈(35, 35,5 등)는 아래 Prada size 열과 대응합니다."
    ),
    "headers": ["Prada size", "UK", "Foot (CM)"],
    "rows": [
        ["34", "1", "22 cm"],
        ["34.5", "1.5", "22.3 cm"],
        ["35", "2", "22.6 cm"],
        ["35.5", "2.5", "23 cm"],
        ["36", "3", "23.3 cm"],
        ["36.5", "3.5", "23.6 cm"],
        ["37", "4", "24 cm"],
        ["37.5", "4.5", "24.3 cm"],
        ["38", "5", "24.6 cm"],
        ["38.5", "5.5", "25 cm"],
        ["39", "6", "25.3 cm"],
        ["39.5", "6.5", "25.6 cm"],
        ["40", "7", "26 cm"],
        ["40.5", "7.5", "26.3 cm"],
        ["41", "8", "26.6 cm"],
        ["41.5", "8.5", "27 cm"],
        ["42", "9", "27.3 cm"],
    ],
}

# Prada GB men's shoes display UK-equivalent labels as Prada size (5, 5,5 …).
PR_MEN_SHOES_SIZE_CHART = {
    "id": "pr-men-shoes",
    "titleKo": "프라다 남성 슈즈 사이즈 차트",
    "noteKo": (
        "prada.com(영국) 남성 슈즈 사이즈 가이드입니다. "
        "Briq 표기 사이즈(5, 5,5, 6 등)는 아래 Prada size(UK) 열과 대응합니다. "
        "Foot은 발 길이(cm)입니다."
    ),
    "headers": ["Prada size", "US", "IT", "Foot (CM)"],
    "rows": [
        ["5", "6", "39", "24.5 cm"],
        ["5.5", "6.5", "39.5", "24.9 cm"],
        ["6", "7", "40", "25.3 cm"],
        ["6.5", "7.5", "40.5", "25.7 cm"],
        ["7", "8", "41", "26.1 cm"],
        ["7.5", "8.5", "41.5", "26.5 cm"],
        ["8", "9", "42", "26.9 cm"],
        ["8.5", "9.5", "42.5", "27.3 cm"],
        ["9", "10", "43", "27.7 cm"],
        ["9.5", "10.5", "43.5", "28.1 cm"],
        ["10", "11", "44", "28.5 cm"],
        ["10.5", "11.5", "44.5", "28.9 cm"],
        ["11", "12", "45", "29.3 cm"],
        ["11.5", "12.5", "45.5", "29.7 cm"],
        ["12", "13", "46", "30.1 cm"],
        ["12.5", "13.5", "46.5", "30.5 cm"],
        ["13", "14", "47", "30.9 cm"],
    ],
}


def size_chart_for_shoes(
    variants: list[dict], *, mens: bool | None = None
) -> dict | None:
    labels = _variant_labels(variants)
    if not labels:
        return None
    if mens is None:
        nums = _variant_size_numbers(variants)
        # GB men's shoes use UK-scale labels (~5–14); women's use IT (~34–42).
        mens = bool(nums) and max(nums) <= 20
    return copy.deepcopy(
        PR_MEN_SHOES_SIZE_CHART if mens else PR_WOMEN_SHOES_SIZE_CHART
    )
