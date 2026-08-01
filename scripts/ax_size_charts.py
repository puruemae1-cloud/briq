#!/usr/bin/env python3
"""CM-based Arc'teryx apparel size charts (from official sizing pages)."""

from __future__ import annotations

import re


WOMENS_JACKET_CM = {
    "id": "ax-womens-jacket-cm",
    "titleKo": "아크테릭스 여성 재킷·셔츠 사이즈 (cm)",
    "noteKo": "신체 치수(cm) 기준입니다. 두 사이즈 사이라면 여유 핏은 큰 사이즈, 슬림 핏은 작은 사이즈를 선택하세요.",
    "headers": ["사이즈", "소매", "가슴", "허리", "엉덩이"],
    "rows": [
        ["XXS", "72", "76", "60", "84"],
        ["XS", "75", "81", "65", "89"],
        ["S", "77", "86", "70", "94"],
        ["M", "80", "91", "75", "99"],
        ["L", "81", "99", "83", "107"],
        ["XL", "83", "109", "93", "117"],
        ["XXL", "85", "119", "103", "127"],
    ],
}

WOMENS_PANT_NUMERIC_CM = {
    "id": "ax-womens-pant-numeric-cm",
    "titleKo": "아크테릭스 여성 팬츠·쇼츠 사이즈 (숫자, cm)",
    "noteKo": "허리·엉덩이·안솔기 길이는 cm 기준입니다. S=Short, R=Regular, T=Tall 기장입니다. 사이즈 사이라면 여유 핏은 큰 사이즈를 선택하세요.",
    "headers": ["사이즈", "허리", "엉덩이", "Regular 안솔기", "Short 안솔기", "Tall 안솔기"],
    "rows": [
        ["00", "61", "85", "78", "73", "85"],
        ["0", "64", "88", "78", "73", "86"],
        ["2", "67", "91", "79", "74", "86"],
        ["4", "70", "94", "79", "74", "87"],
        ["6", "73", "97", "79", "74", "87"],
        ["8", "76", "100", "80", "75", "87"],
        ["10", "79", "103", "80", "75", "88"],
        ["12", "84", "108", "81", "76", "88"],
        ["14", "89", "113", "81", "76", "89"],
        ["16", "94", "118", "81", "76", "89"],
    ],
}

WOMENS_PANT_ALPHA_CM = {
    "id": "ax-womens-pant-alpha-cm",
    "titleKo": "아크테릭스 여성 팬츠·쇼츠 사이즈 (알파, cm)",
    "noteKo": "신체 치수(cm) 기준입니다. Short / Regular / Tall 기장 옵션은 상품별로 다를 수 있습니다.",
    "headers": ["사이즈", "허리", "엉덩이", "Regular 안솔기", "Short 안솔기", "Tall 안솔기"],
    "rows": [
        ["XXS", "60", "84", "78", "73", "85"],
        ["XS", "65", "89", "78", "73", "86"],
        ["S", "70", "94", "79", "74", "87"],
        ["M", "75", "99", "80", "75", "87"],
        ["L", "83", "107", "80", "75", "88"],
        ["XL", "93", "117", "81", "76", "89"],
        ["XXL", "103", "127", "81", "76", "89"],
    ],
}

MENS_JACKET_CM = {
    "id": "ax-mens-jacket-cm",
    "titleKo": "아크테릭스 남성 재킷·셔츠 사이즈 (cm)",
    "noteKo": "신체 치수(cm) 기준입니다. 두 사이즈 사이라면 여유 핏은 큰 사이즈, 슬림 핏은 작은 사이즈를 선택하세요.",
    "headers": ["사이즈", "소매", "가슴", "허리", "엉덩이"],
    "rows": [
        ["XXS", "78", "84", "69", "83"],
        ["XS", "81", "89", "74", "88"],
        ["S", "83", "94", "79", "93"],
        ["M", "86", "102", "86", "100"],
        ["L", "89", "109", "94", "108"],
        ["XL", "91", "119", "104", "118"],
        ["XXL", "94", "129", "114", "128"],
        ["3XL", "96", "139", "124", "138"],
    ],
}

MENS_PANT_NUMERIC_CM = {
    "id": "ax-mens-pant-numeric-cm",
    "titleKo": "아크테릭스 남성 팬츠·쇼츠 사이즈 (숫자, cm)",
    "noteKo": "허리·엉덩이·안솔기 길이는 cm 기준입니다. R=Regular 등 기장 표기는 상품 옵션을 확인하세요.",
    "headers": ["사이즈", "허리", "엉덩이", "Regular 안솔기", "Short 안솔기", "Tall 안솔기"],
    "rows": [
        ["28", "76", "90", "79", "74", "87"],
        ["29", "79", "93", "80", "75", "87"],
        ["30", "81", "95", "80", "75", "88"],
        ["31", "84", "98", "81", "76", "88"],
        ["32", "86", "100", "81", "76", "89"],
        ["33", "89", "103", "81", "76", "89"],
        ["34", "91", "105", "82", "77", "89"],
        ["36", "96", "110", "83", "78", "90"],
        ["38", "101", "115", "83", "78", "91"],
    ],
}

MENS_PANT_ALPHA_CM = {
    "id": "ax-mens-pant-alpha-cm",
    "titleKo": "아크테릭스 남성 팬츠·쇼츠 사이즈 (알파, cm)",
    "noteKo": "신체 치수(cm) 기준입니다. Short / Regular / Tall 기장 옵션은 상품별로 다를 수 있습니다.",
    "headers": ["사이즈", "허리", "엉덩이", "Regular 안솔기", "Short 안솔기", "Tall 안솔기"],
    "rows": [
        ["XXS", "69", "83", "78", "73", "86"],
        ["XS", "74", "88", "79", "74", "87"],
        ["S", "79", "93", "80", "75", "87"],
        ["M", "86", "100", "81", "76", "89"],
        ["L", "94", "108", "82", "77", "90"],
        ["XL", "104", "118", "83", "78", "91"],
        ["XXL", "114", "128", "83", "78", "91"],
    ],
}


def chart_for(name: str, gender: str, sizes: list[str] | None = None) -> dict:
    n = (name or "").lower()
    g = "womens" if "women" in (gender or "").lower() or gender == "womens" else "mens"
    sizes = sizes or []
    is_pant = any(
        k in n for k in ("pant", "short", "tight", "legging", "capri", "skirt", "bib")
    )
    # Numeric waist sizes: 00, 0-R, 32, 16-T, etc. (not alpha XS/S/M)
    numeric = any(re.search(r"\d", s) for s in sizes)
    if is_pant:
        if g == "womens":
            return WOMENS_PANT_NUMERIC_CM if numeric else WOMENS_PANT_ALPHA_CM
        return MENS_PANT_NUMERIC_CM if numeric else MENS_PANT_ALPHA_CM
    return WOMENS_JACKET_CM if g == "womens" else MENS_JACKET_CM
