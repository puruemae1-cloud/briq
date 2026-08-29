"""Curated Korean copy for Louis Vuitton Home / furniture PDPs."""
from __future__ import annotations

PHRASES: dict[str, str] = {
    "Louis Vuitton": "루이 비통",
    "Home Collections": "홈 컬렉션",
    "Signature Collection": "시그니처 컬렉션",
    "Furniture and Lighting": "가구와 라이트닝",
    "Objets Nomades": "옵제 누마드",
    "Made in Italy": "이탈리아 제작",
    "Made in France": "프랑스 제작",
    "Dimensions": "사이즈",
    "Materials": "소재",
    "Care": "케어",
    "One Size": "원 사이즈",
    "Width": "너비",
    "Height": "높이",
    "Depth": "깊이",
    "Length": "길이",
    "Diameter": "직경",
    "Weight": "무게",
    "Wood": "우드",
    "Leather": "레더",
    "Marquetry": "마케트리",
    "Lighting": "라이트닝",
    "Table": "테이블",
    "Chair": "체어",
    "Sofa": "소파",
    "Armchair": "암체어",
    "Sideboard": "사이드보드",
    "Lamp": "램프",
}


def apply_phrases(text: str) -> str:
    out = text or ""
    for en, ko in sorted(PHRASES.items(), key=lambda x: -len(x[0])):
        out = out.replace(en, ko)
    return out
