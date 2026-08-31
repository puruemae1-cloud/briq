#!/usr/bin/env python3
"""Official Dior GB men's ready-to-wear size charts (LegacySizeGuide).

Captured from dior.com en_gb PDP GraphQL `LegacySizeGuide` (Aug 2026):
  - IT / waist equivalent table (bottoms & tailored numeric sizes)
  - SML / EU equivalent table (letter-sized knits & tops)
"""
from __future__ import annotations

import copy
import re

# Dior Size (IT) ↔ SML ↔ US/UK waist ↔ CN — cargo/shorts & numeric RTW.
DI_MEN_RTW_IT = {
    "id": "di-men-rtw-it",
    "titleKo": "디올 남성 레디투웨어 사이즈 가이드",
    "noteKo": (
        "dior.com(영국) 공식 사이즈 가이드입니다. "
        "Dior Size는 이탈리아(IT) 기준이며, Briq 사이즈 선택란의 숫자(44·46 등)는 "
        "아래 Dior Size (IT) 열과 대응합니다. US·UK는 허리(waist) 인치 환산이며, "
        "스타일·소재에 따라 핏이 다를 수 있으니 참고용으로 확인해 주세요."
    ),
    "headers": ["Dior Size (IT)", "SML", "US", "UK", "CN"],
    "rows": [
        ["42", "XXS", "26", "26", "165/66A"],
        ["44", "XS", "28", "28", "165/68A"],
        ["46", "S", "30", "30", "170/70A"],
        ["48", "M", "32", "32", "170/72A"],
        ["50", "L", "33-34", "33-34", "175/74A"],
        ["52", "XL", "35-36", "35-36", "175/76A"],
        ["54", "XXL", "37-38", "37-38", "180/78A"],
        ["56", "XXL", "39", "39", "180/80A"],
        ["58", "XXXL", "40", "40", "185/82A"],
        ["60", "XXXL", "42", "42", "185/84A"],
        ["62", "4XL", "52", "52", "190/86A"],
        ["64", "4XL", "54", "54", "195/88A"],
    ],
}

# Letter sizes (SML) ↔ EU ↔ CN — knits / some tops.
DI_MEN_RTW_SML = {
    "id": "di-men-rtw-sml",
    "titleKo": "디올 남성 레디투웨어 사이즈 가이드",
    "noteKo": (
        "dior.com(영국) 공식 사이즈 가이드입니다. "
        "Briq 사이즈 선택란의 S·M·L 등은 아래 Dior Size (SML) 열과 대응하며, "
        "EU는 이탈리아(IT) 환산 사이즈입니다. 스타일·소재에 따라 핏이 다를 수 있으니 "
        "참고용으로 확인해 주세요."
    ),
    "headers": ["Dior Size (SML)", "EU", "CN"],
    "rows": [
        ["XXXS - XXS", "42", "160/80A-165/84A"],
        ["XS", "44", "170/92A"],
        ["S", "46", "175/92A"],
        ["M", "48", "180/96A"],
        ["L", "50", "180/100A"],
        ["XL", "52", "185/100A"],
        ["XXL", "54", "190/96A"],
        ["XXL", "56", "190/96A"],
        ["XXXL", "58", "190/100A"],
        ["XXXL", "60", "190/100A"],
        ["4XL", "62", ""],
        ["4XL", "64", ""],
    ],
}

# Denim / waist-inch SKUs — same official mapping, waist-first columns.
DI_MEN_RTW_DENIM = {
    "id": "di-men-rtw-denim",
    "titleKo": "디올 남성 데님 사이즈 가이드",
    "noteKo": (
        "dior.com(영국) 공식 사이즈 가이드입니다. "
        "데님·팬츠 표기 사이즈는 허리(US/UK) 인치 기준이며, Dior Size (IT)·SML은 "
        "동일 가이드의 환산입니다. 핏은 스타일마다 다를 수 있습니다."
    ),
    "headers": ["Waist (US/UK)", "Dior Size (IT)", "SML", "CN"],
    "rows": [
        ["26", "42", "XXS", "165/66A"],
        ["28", "44", "XS", "165/68A"],
        ["30", "46", "S", "170/70A"],
        ["32", "48", "M", "170/72A"],
        ["33-34", "50", "L", "175/74A"],
        ["35-36", "52", "XL", "175/76A"],
        ["37-38", "54", "XXL", "180/78A"],
        ["39", "56", "XXL", "180/80A"],
        ["40", "58", "XXXL", "185/82A"],
        ["42", "60", "XXXL", "185/84A"],
    ],
}

_LETTER = re.compile(
    r"^(XXXS|XXS|XS|S|M|L|XL|XXL|XXXL|4XL|XXXS\s*-\s*XXS)$",
    re.I,
)


def _variant_labels(variants: list[dict]) -> list[str]:
    out: list[str] = []
    for v in variants or []:
        for key in ("size", "name", "nameKo"):
            s = str(v.get(key) or "").strip()
            if s and s.upper() not in ("OS", "ONE SIZE", "TU", "U"):
                out.append(s)
                break
    return out


def _nums(labels: list[str]) -> list[int]:
    nums: list[int] = []
    for lab in labels:
        m = re.search(r"(\d{2})", lab)
        if m:
            nums.append(int(m.group(1)))
    return nums


def size_chart_for_di_mens_rtw(
    variants: list[dict],
    *,
    leaf_id: str = "",
) -> dict | None:
    """Pick IT / SML / denim chart from variant labels + leaf."""
    labels = _variant_labels(variants)
    if not labels:
        return None
    leaf = leaf_id or ""
    nums = _nums(labels)
    letterish = sum(1 for lab in labels if _LETTER.match(lab.strip())) >= max(
        1, len(labels) // 2
    )

    if leaf.endswith("-denim") or (
        nums
        and max(nums) <= 42
        and min(nums) <= 36
        and max(nums) - min(nums) <= 16
        and not letterish
        and (not nums or max(nums) < 44)
    ):
        # Waist inches (26–40), not IT 44+
        if nums and max(nums) < 44:
            return copy.deepcopy(DI_MEN_RTW_DENIM)

    if letterish or (not nums and any(re.search(r"[A-Za-z]", lab) for lab in labels)):
        return copy.deepcopy(DI_MEN_RTW_SML)

    return copy.deepcopy(DI_MEN_RTW_IT)
