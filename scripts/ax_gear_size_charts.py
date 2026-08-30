#!/usr/bin/env python3
"""Official Arc'teryx GB gear size charts (harness / hat / glove / sock / pack / vest).

Sourced from arcteryx.com/gb/en/help/sizing/* centimetre tables.
Used by build-ax-gear-catalog.py so weekly sync keeps sizeChart attached.
"""
from __future__ import annotations

import re

NOTE_BODY = (
    "신체 치수(cm) 기준입니다. 사이즈 사이라면 상품 핏 가이드를 참고하고, "
    "두 수치 중 여유 있게 맞추고 싶을 때 큰 사이즈를 선택하세요."
)
NOTE_HAT = (
    "머리 둘레(cm) 기준입니다. SM은 S–M, LXL은 L–XL에 해당합니다. "
    "가장 넓은 부분의 둘레를 재어 선택하세요."
)
NOTE_GLOVE = (
    "손 길이·손바닥 둘레(cm) 기준입니다. 손을 편 상태에서 가운데손가락 끝부터 "
    "손바닥 주름까지, 그리고 너클 둘레를 재세요."
)
NOTE_SOCK = (
    "신발 사이즈 기준입니다. US / EU / UK / KR(mm) 환산을 함께 확인하세요."
)
NOTE_AERIOS = (
    "등길이(cm) 기준입니다. SRT=숏, REG=레귤러, TALL=톨에 해당합니다. "
    "어깨 스트랩·힙벨트는 별도 피팅 옵션이 있을 수 있습니다."
)
NOTE_NORVAN = (
    "가슴 둘레(cm) 기준입니다. 여성용/남성용 모델 열에서 본인 성별 수치를 확인하세요."
)

# Men's Skaha — help/sizing/mens/harnesses/skaha
MENS_SKAHA_HARNESS = {
    "id": "ax-mens-skaha-harness-cm",
    "titleKo": "아크테릭스 남성 Skaha 하네스 사이즈 (cm)",
    "noteKo": NOTE_BODY + " 허리: 가장 가는 부분 / 허벅지: 가장 두꺼운 부분.",
    "headers": ["사이즈", "허리", "허벅지"],
    "rows": [
        ["XS", "71 - 76", "50 - 53"],
        ["S", "76 - 84", "53 - 56"],
        ["M", "84 - 91", "56 - 60"],
        ["L", "91 - 101", "60 - 66"],
        ["XL", "101 - 109", "66 - 71"],
    ],
}

# Women's Skaha — help/sizing/womens/harnesses/skaha
WOMENS_SKAHA_HARNESS = {
    "id": "ax-womens-skaha-harness-cm",
    "titleKo": "아크테릭스 여성 Skaha 하네스 사이즈 (cm)",
    "noteKo": NOTE_BODY + " 허리: 가장 가는 부분 / 허벅지: 가장 두꺼운 부분.",
    "headers": ["사이즈", "허리", "허벅지"],
    "rows": [
        ["XXS", "58 - 63", "49 - 52"],
        ["XS", "63 - 68", "52 - 54"],
        ["S", "68 - 73", "54 - 57"],
        ["M", "73 - 81", "57 - 61"],
        ["L", "81 - 91", "61 - 66"],
        ["XL", "91 - 98", "66 - 72"],
    ],
}

# Men's general harness (AR-395a etc.) — help/sizing/mens/harnesses
MENS_HARNESS = {
    "id": "ax-mens-harness-cm",
    "titleKo": "아크테릭스 남성 하네스 사이즈 (cm)",
    "noteKo": NOTE_BODY + " 허리: 가장 가는 부분 / 허벅지: 가장 두꺼운 부분.",
    "headers": ["사이즈", "허리", "허벅지"],
    "rows": [
        ["XS", "67 - 75", "48 - 53"],
        ["S", "72 - 80", "52 - 57"],
        ["M", "78 - 87", "52 - 61"],
        ["L", "86 - 96", "59 - 66"],
        ["XL", "95 - 105", "63 - 68"],
    ],
}

# Women's general harness (AR-385a etc.) — help/sizing/womens/harnesses
WOMENS_HARNESS = {
    "id": "ax-womens-harness-cm",
    "titleKo": "아크테릭스 여성 하네스 사이즈 (cm)",
    "noteKo": NOTE_BODY + " 허리: 가장 가는 부분 / 허벅지: 가장 두꺼운 부분.",
    "headers": ["사이즈", "허리", "허벅지"],
    "rows": [
        ["XS", "64 - 69", "52 - 56"],
        ["S", "69 - 74", "55 - 59"],
        ["M", "74 - 81", "58 - 62"],
        ["L", "82 - 91", "62 - 66"],
        ["XL", "92 - 100", "67 - 71"],
    ],
}

# Lithos SL — help/sizing/harnesses/lithos-sl-harness
# Product sizes are 1A/1B … 6A/6B (no hyphen).
LITHOS_SL_HARNESS = {
    "id": "ax-lithos-sl-harness-cm",
    "titleKo": "아크테릭스 Lithos SL 하네스 사이즈 (cm)",
    "noteKo": (
        NOTE_BODY
        + " Size Range(1–6)와 A/B(허벅지) 조합으로 고르세요. "
        "Briq 표기 1A = 공홈 1-A."
    ),
    "headers": ["사이즈", "사이즈 레인지", "허리", "허벅지"],
    "rows": [
        ["1A", "1", "64.5 - 72", "50 - 54"],
        ["1B", "1", "64.5 - 72", "51 - 55"],
        ["2A", "2", "71.5 - 79", "50 - 54"],
        ["2B", "2", "71.5 - 79", "54 - 58"],
        ["3A", "3", "78.5 - 86", "53 - 57"],
        ["3B", "3", "78.5 - 86", "58 - 62"],
        ["4A", "4", "85.5 - 93", "57 - 61"],
        ["4B", "4", "85.5 - 93", "62.5 - 66.5"],
        ["5A", "5", "92.5 - 100", "61.5 - 65.5"],
        ["5B", "5", "92.5 - 100", "68 - 72"],
        ["6A", "6", "99.5 - 107", "67 - 71"],
        ["6B", "6", "99.5 - 107", "68 - 72"],
    ],
}

HATS = {
    "id": "ax-hats-cm",
    "titleKo": "아크테릭스 모자·헤드웨어 사이즈 (cm)",
    "noteKo": NOTE_HAT,
    "headers": ["사이즈", "머리 둘레"],
    "rows": [
        ["SM", "55 - 57"],
        ["LXL", "58 - 60"],
        ["OS", "55 - 60"],
    ],
}

GLOVES = {
    "id": "ax-gloves-cm",
    "titleKo": "아크테릭스 글러브·미튼 사이즈 (cm)",
    "noteKo": NOTE_GLOVE,
    "headers": ["사이즈", "손 길이", "손바닥 둘레"],
    "rows": [
        ["XS", "17.8 - 18.4", "18.5 - 19.7"],
        ["S", "18.4 - 19.0", "19.7 - 20.6"],
        ["M", "19.0 - 19.6", "20.6 - 21.8"],
        ["L", "19.6 - 20.2", "21.8 - 22.6"],
        ["XL", "20.2 - 20.8", "22.6 - 23.5"],
        ["XXL", "20.8 - 21.4", "23.5 - 24.4"],
    ],
}

SOCKS = {
    "id": "ax-socks",
    "titleKo": "아크테릭스 양말 사이즈",
    "noteKo": NOTE_SOCK,
    "headers": ["사이즈", "US Men", "US Women", "EU", "UK", "KR"],
    "rows": [
        ["S", "N/A", "4 - 6.5", "36 - 38", "3.5 - 5", "220 - 235mm"],
        ["M", "6 - 8.5", "7 - 9.5", "38⅔ - 42", "5.5 - 8", "240 - 265mm"],
        ["L", "9 - 11.5", "10 - 12.5", "42⅔ - 46", "8.5 - 11", "270 - 295mm"],
        ["XL", "12 - 14.5", "N/A", "46⅔ - 49⅓", "11.5 - 14", "300 - 320mm"],
    ],
}

AERIOS_PACK = {
    "id": "ax-aerios-pack-cm",
    "titleKo": "아크테릭스 Aerios 팩 사이즈 (등길이 cm)",
    "noteKo": NOTE_AERIOS,
    "headers": ["사이즈", "등길이"],
    "rows": [
        ["SRT", "42.5 - 47.5"],
        ["REG", "46.5 - 51.5"],
        ["TALL", "50.5 - 55.5"],
    ],
}

NORVAN_7_VEST = {
    "id": "ax-norvan-7-vest-cm",
    "titleKo": "아크테릭스 Norvan 7 베스트 사이즈 (가슴 cm)",
    "noteKo": NOTE_NORVAN,
    "headers": ["사이즈", "여성용", "남성용"],
    "rows": [
        ["S", "85 - 94", "85 - 96"],
        ["M", "93 - 105", "95 - 109"],
        ["L", "102 - 117", "106 - 122"],
    ],
}


def _norm_url(url: str | None) -> str:
    u = (url or "").strip().lower()
    if not u:
        return ""
    u = u.split("?")[0]
    if u.startswith("https://arcteryx.com"):
        u = u[len("https://arcteryx.com") :]
    if not u.startswith("/"):
        u = "/" + u
    return u.rstrip("/")


def chart_from_sizing_url(url: str | None) -> dict | None:
    """Map PDP sizingChart.url → Briq ProductSizeChart."""
    u = _norm_url(url)
    if not u:
        return None
    # strip locale prefix /gb/en
    u = re.sub(r"^/(gb|us|ca|au|jp|kr)/[a-z]{2}", "", u)
    if u.endswith("/mens/harnesses/skaha"):
        return dict(MENS_SKAHA_HARNESS)
    if u.endswith("/womens/harnesses/skaha"):
        return dict(WOMENS_SKAHA_HARNESS)
    if u.endswith("/mens/harnesses"):
        return dict(MENS_HARNESS)
    if u.endswith("/womens/harnesses"):
        return dict(WOMENS_HARNESS)
    if "lithos-sl-harness" in u:
        return dict(LITHOS_SL_HARNESS)
    if u.endswith("/hats"):
        return dict(HATS)
    if u.endswith("/gloves"):
        return dict(GLOVES)
    if u.endswith("/socks"):
        return dict(SOCKS)
    if "aerios-backpacks" in u or u.endswith("/aerios-backpacks"):
        return dict(AERIOS_PACK)
    if "norvan-7-vest" in u:
        return dict(NORVAN_7_VEST)
    return None


def chart_for_gear_product(
    *,
    name: str,
    gender: str = "",
    sizes: list[str] | None = None,
    sizing_url: str | None = None,
) -> dict | None:
    """Resolve size chart for an Arc'teryx gear/accessory/bag product."""
    by_url = chart_from_sizing_url(sizing_url)
    if by_url:
        return by_url

    n = (name or "").lower()
    g = (gender or "").lower()
    sizes = [str(s) for s in (sizes or [])]

    if "lithos" in n and "harness" in n:
        return dict(LITHOS_SL_HARNESS)
    if "harness" in n:
        if "skaha" in n:
            if "women" in n or g in ("womens", "women", "female"):
                return dict(WOMENS_SKAHA_HARNESS)
            if "men" in n or g in ("mens", "men", "male"):
                return dict(MENS_SKAHA_HARNESS)
            # unisex Skaha listing is the women's model on Arc'teryx GB
            return dict(WOMENS_SKAHA_HARNESS)
        if "women" in n or g in ("womens", "women", "female"):
            return dict(WOMENS_HARNESS)
        if "men" in n or g in ("mens", "men", "male"):
            return dict(MENS_HARNESS)
        return dict(MENS_HARNESS)

    if "norvan" in n and "vest" in n:
        return dict(NORVAN_7_VEST)
    if "aerios" in n and ("backpack" in n or "pack" in n):
        return dict(AERIOS_PACK)

    if any(k in n for k in ("glove", "mitten")):
        return dict(GLOVES)
    if "sock" in n:
        return dict(SOCKS)
    if any(
        k in n
        for k in ("hat", "cap", "toque", "beanie", "bucket", "headband", "visor")
    ):
        # Only when sized (SM/LXL etc.); one-size NA/OS still gets OS row guidance
        return dict(HATS)

    return None
