#!/usr/bin/env python3
"""Rich YouTube description + pinned-comment copy for Briq Shorts."""
from __future__ import annotations

import re


def _tag(s: str) -> str:
    s = re.sub(r"[^\w가-힣A-Za-z0-9]+", "", s or "", flags=re.UNICODE)
    return s[:40]


def build_description(meta: dict) -> str:
    brand_ko = meta.get("brandKo") or meta.get("brand") or ""
    brand_en = meta.get("brandEn") or meta.get("brand") or ""
    name_ko = meta.get("nameKo") or ""
    search = meta.get("search") or name_ko
    kind = meta.get("kind") or "상품"
    price = int(meta.get("price") or 0)
    gbp = float(meta.get("gbp") or 0)
    url = meta.get("productUrl") or "https://www.briq.kr"
    lines = meta.get("lines") or []
    hook = lines[0] if lines else f"{brand_ko} {search}을 브릭에서 소개합니다."

    price_line = f"브릭 안내가 약 {price:,}원"
    if gbp:
        price_line += f" · 영국 현지 £{gbp:,.0f}"

    tags = [
        "#Shorts",
        f"#{_tag(brand_ko)}" if brand_ko else "",
        f"#{_tag(brand_en)}" if brand_en and _tag(brand_en) != _tag(brand_ko) else "",
        f"#{_tag(search)}" if search else "",
        "#Briq",
        "#브릭",
        "#명품직구",
        "#영국명품",
        "#영국직송",
        "#관부가세포함",
        "#명품추천",
        "#명품숏츠",
        "#럭셔리",
        "#하이엔드",
        f"#{_tag(kind)}" if kind else "",
        "#쇼핑하울",
        "#데일리룩",
        "#투자아이템",
    ]
    if kind == "시계":
        tags += ["#시계추천", "#워치", "#툴워치", "#오토매틱"]
    elif kind in {"가방", "클러치"}:
        tags += ["#명품가방", "#백추천", "#데일리백"]
    elif kind == "신발":
        tags += ["#스니커즈", "#신발추천", "#데일리슈즈"]
    elif kind in {"패딩", "의류", "골프웨어"}:
        tags += ["#아우터추천", "#겨울코디", "#패션숏츠"]

    tag_line = " ".join(t for t in tags if t)

    return f"""{brand_ko} {search} | 영국 현지 명품 직송 Briq

{hook}

{name_ko}
{price_line}
관부가세·항공배송 포함 기준으로 안내합니다.

상품 바로가기
{url}

Briq 쇼핑몰
https://www.briq.kr

검색어: {search}
브랜드: {brand_ko} ({brand_en})

영국에서 실제로 파는 가격과 재고를 기준으로 소개합니다.
문의: support@hjstoryltd.com

{tag_line}
""".strip()


def build_pinned_comment(meta: dict) -> str:
    brand_ko = meta.get("brandKo") or ""
    search = meta.get("search") or meta.get("nameKo") or ""
    url = meta.get("productUrl") or "https://www.briq.kr"
    price = int(meta.get("price") or 0)
    return (
        f"상품 링크 (고정)\n{url}\n\n"
        f"{brand_ko} · {search}\n"
        f"브릭 안내가 약 {price:,}원 · 관부가세·항공 포함\n\n"
        f"검색어: {search}\n"
        f"Briq 쇼핑몰\nhttps://www.briq.kr\n\n"
        f"#{_tag(brand_ko)} #Briq #브릭 #명품직구 #영국직송 #Shorts"
    )
