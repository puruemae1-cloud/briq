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
    """Return the Prada GB RTW chart matching the product's size picker labels."""
    labels = _variant_labels(variants)
    if not labels:
        return None
    mode = _chart_mode(labels)
    base = PR_WOMEN_RTW_NUMERIC if mode == "numeric" else PR_WOMEN_RTW_LETTER
    return copy.deepcopy(base)
