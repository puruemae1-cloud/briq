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

# Shirts — collar (cm) conversion + body measurements from dior.com Size Chart drawer.
DI_MEN_RTW_SHIRT = {
    "id": "di-men-rtw-shirt",
    "titleKo": "디올 남성 셔츠 사이즈 가이드",
    "noteKo": (
        "dior.com(영국) 공식 셔츠 사이즈 가이드입니다. "
        "Briq 사이즈 선택란의 숫자(37·38 등)는 목둘레(cm) 기준 Dior Size와 "
        "대응합니다. 실측(cm) 탭에서 어깨·가슴·소매·기장 치수를 확인할 수 있습니다."
    ),
    "headers": ["목둘레 (cm)", "목둘레 (inch)", "SML", "CN"],
    "rows": [
        ["37", "14.5", "S", "165/80A"],
        ["38", "15", "S", "170/84A"],
        ["39", "15.5", "M", "170/88A"],
        ["40", "15.75", "M", "175/92A"],
        ["41", "16", "L", "175/96A"],
        ["42", "16.5", "L", "180/100A"],
        ["43", "17", "XL", "180/104A"],
        ["44", "17.5", "XL", "185/100A"],
        ["45", "17.75", "XXL", "185/108B"],
        ["46", "18", "XXL", "185/104A"],
    ],
    "tabs": [
        {
            "id": "convert",
            "labelKo": "사이즈 변환",
            "headers": ["목둘레 (cm)", "목둘레 (inch)", "SML", "CN"],
            "rows": [
                ["37", "14.5", "S", "165/80A"],
                ["38", "15", "S", "170/84A"],
                ["39", "15.5", "M", "170/88A"],
                ["40", "15.75", "M", "175/92A"],
                ["41", "16", "L", "175/96A"],
                ["42", "16.5", "L", "180/100A"],
                ["43", "17", "XL", "180/104A"],
                ["44", "17.5", "XL", "185/100A"],
                ["45", "17.75", "XXL", "185/108B"],
                ["46", "18", "XXL", "185/104A"],
            ],
        },
        {
            "id": "measure",
            "labelKo": "실측 (cm)",
            "headers": [
                "Dior Size",
                "칼라 폭",
                "어깨",
                "가슴",
                "소매",
                "기장",
            ],
            "rows": [
                ["37", "22", "16", "39", "26", "31"],
                ["38", "22", "16", "40", "26", "31"],
                ["39", "22", "17", "42", "26", "32"],
                ["40", "22", "17", "43", "26", "32"],
                ["41", "22", "17", "45", "27", "32"],
                ["42", "22", "18", "46", "27", "32"],
                ["43", "22", "18", "48", "27", "33"],
                ["44", "22", "18", "50", "27", "33"],
                ["45", "22", "19", "51", "27", "33"],
                ["46", "22", "19", "52", "27", "33"],
            ],
        },
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

_SHIRT_LEAVES = {"di-men-shirts"}
_SML_LEAVES = {
    "di-men-knitwear-sweatshirts",
    "di-men-tshirts-polos",
    "di-men-beachwear",
    "di-men-outerwear",
    "di-men-leather",
}
_DENIM_LEAVES = {"di-men-denim"}
_IT_LEAVES = {
    "di-men-trousers-shorts",
    "di-men-tailored-jackets",
    "di-men-suits-tuxedos",
}


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


def _is_shirt_collar(labels: list[str]) -> bool:
    nums = _nums(labels)
    return bool(nums) and min(nums) >= 36 and max(nums) <= 46


def _chart_by_leaf(leaf_id: str) -> dict | None:
    leaf = leaf_id or ""
    if leaf in _SHIRT_LEAVES or "shirt" in leaf:
        return copy.deepcopy(DI_MEN_RTW_SHIRT)
    if leaf in _DENIM_LEAVES or leaf.endswith("-denim"):
        return copy.deepcopy(DI_MEN_RTW_DENIM)
    if leaf in _SML_LEAVES:
        return copy.deepcopy(DI_MEN_RTW_SML)
    if leaf in _IT_LEAVES:
        return copy.deepcopy(DI_MEN_RTW_IT)
    return copy.deepcopy(DI_MEN_RTW_SML)


def size_chart_for_di_mens_rtw(
    variants: list[dict],
    *,
    leaf_id: str = "",
    title_en: str = "",
) -> dict | None:
    """Pick shirt / IT / SML / denim chart from variant labels + leaf."""
    labels = _variant_labels(variants)
    leaf = leaf_id or ""
    title = (title_en or "").lower()

    if not labels:
        if leaf or title:
            return _chart_by_leaf(leaf)
        return None

    nums = _nums(labels)
    letterish = sum(1 for lab in labels if _LETTER.match(lab.strip())) >= max(
        1, len(labels) // 2
    )

    if (
        leaf in _SHIRT_LEAVES
        or "shirt" in title
        or _is_shirt_collar(labels)
    ):
        return copy.deepcopy(DI_MEN_RTW_SHIRT)

    if leaf.endswith("-denim") or leaf in _DENIM_LEAVES or (
        nums
        and max(nums) <= 42
        and min(nums) <= 36
        and max(nums) - min(nums) <= 16
        and not letterish
        and max(nums) < 44
    ):
        return copy.deepcopy(DI_MEN_RTW_DENIM)

    if letterish or (not nums and any(re.search(r"[A-Za-z]", lab) for lab in labels)):
        return copy.deepcopy(DI_MEN_RTW_SML)

    return copy.deepcopy(DI_MEN_RTW_IT)


# Official Dior shoe size guide from dior.com en_gb PDP Size Chart drawer
# (B30 Countdown sneaker, Sep 2026). Transposed for row-per-size readability.
_DI_SHOE_EU = [
    "35", "35.5", "36", "36.5", "37", "37.5", "38", "38.5", "39", "39.5",
    "40", "40.5", "41", "41.5", "42", "42.5", "43", "43.5", "44", "44.5",
    "45", "45.5", "46", "46.5", "47", "47.5", "48", "48.5", "49", "49.5", "50",
]
_DI_SHOE_UK = [
    "1", "1.5", "2", "2.5", "3", "3.5", "4", "4.5", "5", "5.5",
    "6", "6.5", "7", "7.5", "8", "8.5", "9", "9.5", "10", "10.5",
    "11", "11.5", "12", "12.5", "13", "13.5", "14", "14.5", "15", "15.5", "16",
]
_DI_SHOE_US = [
    "2", "2.5", "3", "3.5", "4", "4.5", "5", "5.5", "6", "6.5",
    "7", "7.5", "8", "8.5", "9", "9.5", "10", "10.5", "11", "11.5",
    "12", "12.5", "13", "13.5", "14", "14.5", "15", "15.5", "16", "16.5", "17",
]
_DI_SHOE_KR = [
    "200", "205", "210", "215", "220", "225", "230", "235", "240", "245",
    "250", "255", "260", "265", "270", "275", "280", "285", "290", "295",
    "300", "305", "310", "315", "320", "325", "330", "335", "340", "345", "350",
]
_DI_SHOE_CM = [
    "22.2", "22.6", "22.9", "23.3", "23.7", "24.0", "24.4", "24.7", "25.1", "25.4",
    "25.8", "26.1", "26.5", "26.8", "27.2", "27.6", "27.9", "28.3", "28.6", "29.0",
    "29.3", "29.7", "30.0", "30.4", "30.8", "31.1", "31.5", "31.8", "32.2", "32.5", "32.9",
]

DI_MEN_SHOES = {
    "id": "di-men-shoes",
    "titleKo": "디올 남성 슈즈 사이즈 가이드",
    "noteKo": (
        "dior.com(영국) 공식 Size Chart입니다. "
        "Briq 사이즈 선택란의 숫자(41·42.5 등)는 아래 Dior Size (IT/EU/FR) 열과 "
        "대응합니다. UK·US-AU·KR(mm)·발길이(cm)는 환산값이며, 모델·라스트에 따라 "
        "핏이 다를 수 있으니 참고용으로 확인해 주세요."
    ),
    "headers": ["Dior Size (IT/EU/FR)", "UK", "US-AU", "KR (mm)", "발길이 (cm)"],
    "rows": [
        [eu, uk, us, kr, cm]
        for eu, uk, us, kr, cm in zip(
            _DI_SHOE_EU, _DI_SHOE_UK, _DI_SHOE_US, _DI_SHOE_KR, _DI_SHOE_CM
        )
    ],
}


def size_chart_for_di_mens_shoes() -> dict:
    return copy.deepcopy(DI_MEN_SHOES)


# Official Dior women RTW conversion (FR base) — aligned with dior.com GB size
# drawers / House equivalences (FR ↔ IT ↔ UK ↔ US ↔ SML + body cm).
DI_WOMEN_RTW_FR = {
    "id": "di-women-rtw-fr",
    "titleKo": "디올 여성 레디투웨어 사이즈 가이드",
    "noteKo": (
        "dior.com(영국) 공식 사이즈 환산을 기준으로 정리한 가이드입니다. "
        "Briq 사이즈 선택란의 숫자(34·36 등)는 아래 Dior Size (FR) 열과 대응합니다. "
        "스타일·소재에 따라 핏이 다를 수 있으니 참고용으로 확인해 주세요."
    ),
    "headers": ["Dior Size (FR)", "IT", "UK", "US", "SML", "가슴 (cm)", "허리 (cm)", "힙 (cm)"],
    "rows": [
        ["32", "36", "4", "0", "XXS", "78", "58", "84"],
        ["34", "38", "6", "2", "XS", "82", "62", "88"],
        ["36", "40", "8", "4", "S", "86", "66", "92"],
        ["38", "42", "10", "6", "M", "90", "70", "96"],
        ["40", "44", "12", "8", "L", "94", "74", "100"],
        ["42", "46", "14", "10", "XL", "98", "78", "104"],
        ["44", "48", "16", "12", "XXL", "104", "84", "110"],
        ["46", "50", "18", "14", "3XL", "110", "90", "116"],
    ],
}

DI_WOMEN_RTW_SML = {
    "id": "di-women-rtw-sml",
    "titleKo": "디올 여성 레디투웨어 사이즈 가이드",
    "noteKo": (
        "dior.com(영국) 공식 사이즈 환산을 기준으로 정리한 가이드입니다. "
        "Briq 사이즈 선택란의 S·M·L 등은 아래 Dior Size (SML) 열과 대응합니다."
    ),
    "headers": ["Dior Size (SML)", "FR", "IT", "UK", "US", "가슴 (cm)", "허리 (cm)", "힙 (cm)"],
    "rows": [
        ["XXS", "32", "36", "4", "0", "78", "58", "84"],
        ["XS", "34", "38", "6", "2", "82", "62", "88"],
        ["S", "36", "40", "8", "4", "86", "66", "92"],
        ["M", "38", "42", "10", "6", "90", "70", "96"],
        ["L", "40", "44", "12", "8", "94", "74", "100"],
        ["XL", "42", "46", "14", "10", "98", "78", "104"],
        ["XXL", "44", "48", "16", "12", "104", "84", "110"],
        ["3XL", "46", "50", "18", "14", "110", "90", "116"],
    ],
}

DI_WOMEN_RTW_DENIM = {
    "id": "di-women-rtw-denim",
    "titleKo": "디올 여성 데님 사이즈 가이드",
    "noteKo": (
        "dior.com(영국) 공식 사이즈 환산을 기준으로 정리한 가이드입니다. "
        "데님 표기 숫자(또는 FR)는 아래 열과 대응하며, 핏은 스타일마다 다를 수 있습니다."
    ),
    "headers": ["Dior Size (FR)", "IT", "UK", "US", "허리 (cm)", "힙 (cm)"],
    "rows": [
        ["32", "36", "4", "0", "58", "84"],
        ["34", "38", "6", "2", "62", "88"],
        ["36", "40", "8", "4", "66", "92"],
        ["38", "42", "10", "6", "70", "96"],
        ["40", "44", "12", "8", "74", "100"],
        ["42", "46", "14", "10", "78", "104"],
        ["44", "48", "16", "12", "84", "110"],
        ["46", "50", "18", "14", "90", "116"],
    ],
}

_WOMEN_LETTER = re.compile(
    r"^(XXXS|XXS|XS|S|M|L|XL|XXL|XXXL|3XL|4XL)$",
    re.I,
)
_WOMEN_SML_LEAVES = {
    "di-women-tshirts",
    "di-women-sweaters-cardigans",
    "di-women-swimsuits",
    "di-women-homewear-lingerie",
}
_WOMEN_DENIM_LEAVES = {"di-women-denim"}
_WOMEN_FR_LEAVES = {
    "di-women-shirts",
    "di-women-dresses",
    "di-women-skirts",
    "di-women-trousers-shorts",
    "di-women-coats",
    "di-women-jackets",
    "di-women-rtw-all",
}


def size_chart_for_di_womens_rtw(
    variants: list[dict],
    *,
    leaf_id: str = "",
    title_en: str = "",
) -> dict | None:
    """Pick FR / SML / denim chart for Dior women's RTW."""
    labels = _variant_labels(variants)
    leaf = leaf_id or ""
    title = (title_en or "").lower()

    if leaf in _WOMEN_DENIM_LEAVES or "denim" in leaf or "jean" in title:
        return copy.deepcopy(DI_WOMEN_RTW_DENIM)

    letterish = False
    if labels:
        letterish = sum(1 for lab in labels if _WOMEN_LETTER.match(lab.strip())) >= max(
            1, len(labels) // 2
        )

    if leaf in _WOMEN_SML_LEAVES or letterish:
        return copy.deepcopy(DI_WOMEN_RTW_SML)

    if leaf in _WOMEN_FR_LEAVES or leaf or labels or title:
        return copy.deepcopy(DI_WOMEN_RTW_FR)
    return None
