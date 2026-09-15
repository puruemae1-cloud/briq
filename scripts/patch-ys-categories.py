#!/usr/bin/env python3
"""One-shot patch: wire Saint Laurent into categories.ts."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "src/data/categories.ts"
text = path.read_text(encoding="utf-8")
if 'id: "saint-laurent"' in text and "| \"saint-laurent\"" in text:
    print("already patched")
    raise SystemExit(0)

YS_IDS = [
    "saint-laurent",
    "ys-men",
    "ys-women",
    "ys-men-rtw-all",
    "ys-men-shirts",
    "ys-men-jersey",
    "ys-men-knitwear",
    "ys-men-denim",
    "ys-men-jackets-pants",
    "ys-men-outerwear",
    "ys-men-coats-trench",
    "ys-men-leather",
    "ys-women-rtw-all",
    "saint-laurent-bags",
    "ys-men-bags",
    "ys-women-bags",
    "ys-men-bags-all",
    "ys-men-backpacks",
    "ys-men-briefcases",
    "ys-men-messengers",
    "ys-men-totes",
    "ys-men-travel-bags",
    "ys-women-bags-all",
    "saint-laurent-shoes",
    "ys-men-shoes",
    "ys-women-shoes",
    "ys-men-shoes-all",
    "ys-men-sneakers",
    "ys-men-loafers",
    "ys-men-derbies",
    "ys-men-boots",
    "ys-men-sandals",
    "ys-women-shoes-all",
    "ys-women-sneakers",
    "ys-women-pumps",
    "ys-women-sandals",
    "ys-women-flat-sandals",
    "ys-women-flats-loafers",
    "ys-women-ballerinas",
    "ys-women-mules-wedges",
    "ys-women-boots",
    "ys-women-booties",
    "saint-laurent-accessories",
    "ys-men-accessories",
    "ys-women-accessories",
    "ys-men-slg-all",
    "ys-men-card-cases",
    "ys-men-wallets",
    "ys-men-pouches",
    "ys-men-cases-holders",
    "ys-men-slg-other",
    "ys-men-acc-all",
    "ys-men-belts",
    "ys-men-hats-gloves",
    "ys-men-jewelry",
    "ys-men-scarves-ties",
    "ys-men-sunglasses",
    "ys-women-slg-all",
    "ys-women-acc-all",
    "ys-women-belts",
    "ys-women-gloves",
    "ys-women-hats",
    "ys-women-scarves-silk",
    "ys-women-sunglasses",
    "ys-women-jewelry-all",
    "ys-women-earrings",
    "ys-women-necklaces",
    "ys-women-cuffs-bracelets",
    "ys-women-brooches-rings",
    "ys-women-lucky-charms",
]

if '| "saint-laurent"' not in text:
    text = text.replace('  | "celine"\n', '  | "celine"\n' + "\n".join(f'  | "{i}"' for i in YS_IDS) + "\n", 1)
    print("CategoryId OK")

leaf_consts = '''
export const YS_MEN_RTW_LEAF_IDS: SubcategoryId[] = [
  "ys-men-rtw-all","ys-men-shirts","ys-men-jersey","ys-men-knitwear","ys-men-denim",
  "ys-men-jackets-pants","ys-men-outerwear","ys-men-coats-trench","ys-men-leather",
];
export const YS_WOMEN_RTW_LEAF_IDS: SubcategoryId[] = ["ys-women-rtw-all"];
export const YS_MEN_BAGS_LEAF_IDS: SubcategoryId[] = [
  "ys-men-bags-all","ys-men-backpacks","ys-men-briefcases","ys-men-messengers","ys-men-totes","ys-men-travel-bags",
];
export const YS_WOMEN_BAGS_LEAF_IDS: SubcategoryId[] = ["ys-women-bags-all"];
export const YS_MEN_SHOES_LEAF_IDS: SubcategoryId[] = [
  "ys-men-shoes-all","ys-men-sneakers","ys-men-loafers","ys-men-derbies","ys-men-boots","ys-men-sandals",
];
export const YS_WOMEN_SHOES_LEAF_IDS: SubcategoryId[] = [
  "ys-women-shoes-all","ys-women-sneakers","ys-women-pumps","ys-women-sandals","ys-women-flat-sandals",
  "ys-women-flats-loafers","ys-women-ballerinas","ys-women-mules-wedges","ys-women-boots","ys-women-booties",
];
export const YS_MEN_ACC_LEAF_IDS: SubcategoryId[] = [
  "ys-men-slg-all","ys-men-card-cases","ys-men-wallets","ys-men-pouches","ys-men-cases-holders","ys-men-slg-other",
  "ys-men-acc-all","ys-men-belts","ys-men-hats-gloves","ys-men-jewelry","ys-men-scarves-ties","ys-men-sunglasses",
];
export const YS_WOMEN_ACC_LEAF_IDS: SubcategoryId[] = [
  "ys-women-slg-all",
  "ys-women-acc-all","ys-women-belts","ys-women-gloves","ys-women-hats","ys-women-scarves-silk","ys-women-sunglasses",
  "ys-women-jewelry-all","ys-women-earrings","ys-women-necklaces","ys-women-cuffs-bracelets","ys-women-brooches-rings","ys-women-lucky-charms",
];

'''
if "YS_MEN_RTW_LEAF_IDS" not in text:
    text = text.replace(
        "export const CE_MEN_RTW_LEAF_IDS: SubcategoryId[] = [",
        leaf_consts + "export const CE_MEN_RTW_LEAF_IDS: SubcategoryId[] = [",
        1,
    )
    print("leaf consts OK")

children = '''
  "saint-laurent": ["saint-laurent", "ys-women", ...YS_WOMEN_RTW_LEAF_IDS, "ys-men", ...YS_MEN_RTW_LEAF_IDS],
  "ys-women": ["ys-women", ...YS_WOMEN_RTW_LEAF_IDS],
  "ys-men": ["ys-men", ...YS_MEN_RTW_LEAF_IDS],
  "saint-laurent-bags": ["saint-laurent-bags", "ys-women-bags", ...YS_WOMEN_BAGS_LEAF_IDS, "ys-men-bags", ...YS_MEN_BAGS_LEAF_IDS],
  "ys-women-bags": ["ys-women-bags", ...YS_WOMEN_BAGS_LEAF_IDS],
  "ys-men-bags": ["ys-men-bags", ...YS_MEN_BAGS_LEAF_IDS],
  "saint-laurent-shoes": ["saint-laurent-shoes", "ys-women-shoes", ...YS_WOMEN_SHOES_LEAF_IDS, "ys-men-shoes", ...YS_MEN_SHOES_LEAF_IDS],
  "ys-women-shoes": ["ys-women-shoes", ...YS_WOMEN_SHOES_LEAF_IDS],
  "ys-men-shoes": ["ys-men-shoes", ...YS_MEN_SHOES_LEAF_IDS],
  "saint-laurent-accessories": ["saint-laurent-accessories", "ys-women-accessories", ...YS_WOMEN_ACC_LEAF_IDS, "ys-men-accessories", ...YS_MEN_ACC_LEAF_IDS],
  "ys-women-accessories": ["ys-women-accessories", ...YS_WOMEN_ACC_LEAF_IDS],
  "ys-men-accessories": ["ys-men-accessories", ...YS_MEN_ACC_LEAF_IDS],
'''
for i in YS_IDS:
    if i.startswith("ys-") and i not in {
        "ys-men",
        "ys-women",
        "ys-men-bags",
        "ys-women-bags",
        "ys-men-shoes",
        "ys-women-shoes",
        "ys-men-accessories",
        "ys-women-accessories",
    }:
        children += f'  "{i}": ["{i}"],\n'

if '"saint-laurent":' not in text:
    text = text.replace("  celine: [", children + "  celine: [", 1)
    print("SUBCATEGORY_CHILDREN OK")


def nav_items(pairs, cat: str) -> str:
    return "\n".join(
        f'              {{ id: "{i}", labelKo: "{ko}", href: "/shop?category={cat}&sub={i}" }},'
        for i, ko in pairs
    )


luxury = f'''
      {{
        id: "saint-laurent",
        labelKo: "생로랑",
        href: "/shop?category=luxury&sub=saint-laurent",
        children: [
          {{
            id: "ys-women",
            labelKo: "여성용",
            href: "/shop?category=luxury&sub=ys-women",
            navLeaf: true,
            children: [
              {{ id: "ys-women-rtw-all", labelKo: "전체", href: "/shop?category=luxury&sub=ys-women-rtw-all" }},
            ],
          }},
          {{
            id: "ys-men",
            labelKo: "남성용",
            href: "/shop?category=luxury&sub=ys-men",
            navLeaf: true,
            children: [
{nav_items([
("ys-men-rtw-all","전체"),("ys-men-shirts","셔츠"),("ys-men-jersey","저지"),("ys-men-knitwear","니트웨어"),
("ys-men-denim","데님"),("ys-men-jackets-pants","재킷 & 팬츠"),("ys-men-outerwear","아우터웨어"),
("ys-men-coats-trench","코트 & 트렌치"),("ys-men-leather","레더"),
], "luxury")}
            ],
          }},
        ],
      }},
'''

bags = f'''
      {{
        id: "saint-laurent-bags",
        labelKo: "생로랑",
        href: "/shop?category=bags&sub=saint-laurent-bags",
        children: [
          {{
            id: "ys-women-bags",
            labelKo: "여성용",
            href: "/shop?category=bags&sub=ys-women-bags",
            navLeaf: true,
            children: [
              {{ id: "ys-women-bags-all", labelKo: "전체", href: "/shop?category=bags&sub=ys-women-bags-all" }},
            ],
          }},
          {{
            id: "ys-men-bags",
            labelKo: "남성용",
            href: "/shop?category=bags&sub=ys-men-bags",
            navLeaf: true,
            children: [
{nav_items([
("ys-men-bags-all","전체"),("ys-men-backpacks","백팩"),("ys-men-briefcases","브리프케이스"),
("ys-men-messengers","메신저"),("ys-men-totes","토트"),("ys-men-travel-bags","트래블 백"),
], "bags")}
            ],
          }},
        ],
      }},
'''

shoes = f'''
      {{
        id: "saint-laurent-shoes",
        labelKo: "생로랑",
        href: "/shop?category=shoes&sub=saint-laurent-shoes",
        children: [
          {{
            id: "ys-women-shoes",
            labelKo: "여성용",
            href: "/shop?category=shoes&sub=ys-women-shoes",
            navLeaf: true,
            children: [
{nav_items([
("ys-women-shoes-all","전체"),("ys-women-sneakers","스니커즈"),("ys-women-pumps","펌프스 & 슬링백"),
("ys-women-sandals","샌들"),("ys-women-flat-sandals","플랫 샌들"),("ys-women-flats-loafers","플랫 & 로퍼"),
("ys-women-ballerinas","발레리나"),("ys-women-mules-wedges","뮬 & 웨지"),("ys-women-boots","부츠"),("ys-women-booties","부티"),
], "shoes")}
            ],
          }},
          {{
            id: "ys-men-shoes",
            labelKo: "남성용",
            href: "/shop?category=shoes&sub=ys-men-shoes",
            navLeaf: true,
            children: [
{nav_items([
("ys-men-shoes-all","전체"),("ys-men-sneakers","스니커즈"),("ys-men-loafers","로퍼"),
("ys-men-derbies","더비"),("ys-men-boots","부츠"),("ys-men-sandals","샌들"),
], "shoes")}
            ],
          }},
        ],
      }},
'''

acc = f'''
      {{
        id: "saint-laurent-accessories",
        labelKo: "생로랑",
        href: "/shop?category=accessories&sub=saint-laurent-accessories",
        children: [
          {{
            id: "ys-women-accessories",
            labelKo: "여성용",
            href: "/shop?category=accessories&sub=ys-women-accessories",
            navLeaf: true,
            children: [
{nav_items([
("ys-women-slg-all","SLG 전체"),("ys-women-acc-all","악세서리 전체"),("ys-women-belts","벨트"),
("ys-women-gloves","장갑"),("ys-women-hats","모자"),("ys-women-scarves-silk","스카프 & 실크"),
("ys-women-sunglasses","선글라스"),("ys-women-jewelry-all","주얼리 전체"),("ys-women-earrings","이어링"),
("ys-women-necklaces","네크리스"),("ys-women-cuffs-bracelets","커프 & 브레이슬릿"),
("ys-women-brooches-rings","브로치 & 링"),("ys-women-lucky-charms","럭키 참"),
], "accessories")}
            ],
          }},
          {{
            id: "ys-men-accessories",
            labelKo: "남성용",
            href: "/shop?category=accessories&sub=ys-men-accessories",
            navLeaf: true,
            children: [
{nav_items([
("ys-men-slg-all","SLG 전체"),("ys-men-card-cases","카드 케이스"),("ys-men-wallets","지갑"),
("ys-men-pouches","파우치"),("ys-men-cases-holders","케이스 & 홀더"),("ys-men-slg-other","기타 SLG"),
("ys-men-acc-all","악세서리 전체"),("ys-men-belts","벨트"),("ys-men-hats-gloves","모자 & 장갑"),
("ys-men-jewelry","주얼리"),("ys-men-scarves-ties","스카프 & 타이"),("ys-men-sunglasses","선글라스"),
], "accessories")}
            ],
          }},
        ],
      }},
'''

if 'id: "saint-laurent"' not in text:
    text = text.replace('        id: "celine",\n        labelKo: "셀린",', luxury + '\n        id: "celine",\n        labelKo: "셀린",', 1)
    print("luxury nav OK")
if 'id: "saint-laurent-bags"' not in text:
    text = text.replace('        id: "celine-bags",\n        labelKo: "셀린",', bags + '\n        id: "celine-bags",\n        labelKo: "셀린",', 1)
    print("bags nav OK")
if 'id: "saint-laurent-shoes"' not in text:
    text = text.replace('        id: "celine-shoes",\n        labelKo: "셀린",', shoes + '\n        id: "celine-shoes",\n        labelKo: "셀린",', 1)
    print("shoes nav OK")
if 'id: "saint-laurent-accessories"' not in text:
    text = text.replace('        id: "celine-accessories",\n        labelKo: "셀린",', acc + '\n        id: "celine-accessories",\n        labelKo: "셀린",', 1)
    print("accessories nav OK")

path.write_text(text, encoding="utf-8")
print("done", path, "bytes", path.stat().st_size)
