#!/usr/bin/env python3
"""Inject Paul Smith subcategory ids + nav into categories.ts."""
from __future__ import annotations

from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "src/data/categories.ts"
text = PATH.read_text()

CLOTHING = [
    ("ps-men-all-in-one", "올인원"),
    ("ps-men-coats", "코트"),
    ("ps-men-dressing-gown", "드레싱 가운"),
    ("ps-men-jackets", "재킷"),
    ("ps-men-jeans", "진"),
    ("ps-men-knitwear", "니트웨어"),
    ("ps-men-loungewear", "라운지웨어"),
    ("ps-men-polos", "폴로 셔츠"),
    ("ps-men-pyjamas", "파자마"),
    ("ps-men-shirts", "셔츠"),
    ("ps-men-shorts", "쇼츠"),
    ("ps-men-suits", "수트"),
    ("ps-men-sweat-pants", "스웻팬츠"),
    ("ps-men-sweatshirts", "스웻셔츠"),
    ("ps-men-swimwear", "스윔웨어"),
    ("ps-men-tshirts", "티셔츠"),
    ("ps-men-trousers", "트라우저"),
    ("ps-men-underwear", "언더웨어"),
    ("ps-men-waistcoats", "웨이스트코트"),
    ("ps-men-tailoring", "테일러링"),
    ("ps-men-other", "기타 의류"),
]

SHOES = [
    ("ps-shoes-boots", "부츠"),
    ("ps-shoes-brogues", "브로그"),
    ("ps-shoes-derby", "더비 슈즈"),
    ("ps-shoes-espadrilles", "에스파드리유"),
    ("ps-shoes-loafers", "로퍼"),
    ("ps-shoes-oxford", "옥스포드"),
    ("ps-shoes-sandals", "샌들"),
    ("ps-shoes-care", "슈케어"),
    ("ps-shoes-slides", "슬라이드"),
    ("ps-shoes-trainers", "스니커즈"),
    ("ps-shoes-other", "기타 슈즈"),
]

ACC = [
    ("ps-acc-bags", "백"),
    ("ps-acc-belts", "벨트"),
    ("ps-acc-boots", "부츠"),
    ("ps-acc-ceramics", "세라믹"),
    ("ps-acc-giftset", "기프트 세트"),
    ("ps-acc-gloves", "글러브"),
    ("ps-acc-hats", "모자"),
    ("ps-acc-jewellery", "주얼리"),
    ("ps-acc-keyrings", "키링"),
    ("ps-acc-knitwear", "니트웨어"),
    ("ps-acc-novelty", "노블티"),
    ("ps-acc-pocket-squares", "포켓 스퀘어"),
    ("ps-acc-pyjamas", "파자마"),
    ("ps-acc-scarves", "스카프"),
    ("ps-acc-slg", "가죽 소품"),
    ("ps-acc-socks", "삭스"),
    ("ps-acc-stationery", "스테이셔너리"),
    ("ps-acc-swimwear", "스윔웨어"),
    ("ps-acc-ties", "타이"),
    ("ps-acc-towels", "타월"),
    ("ps-acc-umbrellas", "우산"),
    ("ps-acc-underwear", "언더웨어"),
    ("ps-acc-other", "기타 악세서리"),
]

TOP = [
    "paul-smith",
    "ps-men",
    "paul-smith-shoes",
    "ps-shoes-men",
    "paul-smith-accessories",
    "ps-acc-men",
]

ALL_IDS = TOP + [i for i, _ in CLOTHING] + [i for i, _ in SHOES] + [i for i, _ in ACC]

# 1) Add to SubcategoryId union before trailing `;` of the big union ending bb-gifts-home
marker = '  | "bb-gifts-home";'
if "paul-smith" not in text:
    extra = "\n".join([f'  | "{i}"' for i in ALL_IDS]) + ";"
    text = text.replace(marker, '  | "bb-gifts-home"\n' + extra[:-1] + "\n  ;".replace("\n  ;", ";") if False else '  | "bb-gifts-home"\n' + "\n".join(f'  | "{i}"' for i in ALL_IDS) + ";")

# 2) Add group constants + subcategoryGroups entries before `export type NavChild`
const_block = """
export const PS_MEN_CLOTHING_IDS: SubcategoryId[] = [
""" + ",\n".join([f'  "{i}"' for i, _ in CLOTHING]) + ",\n];\n\n"

const_block += "export const PS_MEN_SHOE_IDS: SubcategoryId[] = [\n" + ",\n".join([f'  "{i}"' for i, _ in SHOES]) + ",\n];\n\n"
const_block += "export const PS_MEN_ACC_IDS: SubcategoryId[] = [\n" + ",\n".join([f'  "{i}"' for i, _ in ACC]) + ",\n];\n\n"

if "PS_MEN_CLOTHING_IDS" not in text:
    text = text.replace("export type NavChild = {", const_block + "export type NavChild = {")

# 3) subcategoryGroups entries
group_snip = """
  "paul-smith": ["ps-men", ...PS_MEN_CLOTHING_IDS],
  "ps-men": [...PS_MEN_CLOTHING_IDS],
  "paul-smith-shoes": ["ps-shoes-men", ...PS_MEN_SHOE_IDS],
  "ps-shoes-men": [...PS_MEN_SHOE_IDS],
  "paul-smith-accessories": ["ps-acc-men", ...PS_MEN_ACC_IDS],
  "ps-acc-men": [...PS_MEN_ACC_IDS],
"""
if '"paul-smith":' not in text:
    # insert after burberry line start of subcategoryGroups - after opening
    text = text.replace(
        "export const subcategoryGroups: Partial<Record<SubcategoryId, SubcategoryId[]>> = {\n",
        "export const subcategoryGroups: Partial<Record<SubcategoryId, SubcategoryId[]>> = {\n" + group_snip,
    )

def nav_children(pairs, cat, parent):
    lines = []
    for i, label in pairs:
        lines.append(
            "              {\n"
            f'                id: "{i}",\n'
            f'                labelKo: "{label}",\n'
            f'                href: "/shop?category={cat}&sub={i}",\n'
            "              }"
        )
    return ",\n".join(lines)

luxury_nav = f"""
      {{
        id: "paul-smith",
        labelKo: "폴 스미스",
        href: "/shop?category=luxury&sub=paul-smith",
        children: [
          {{
            id: "ps-men",
            labelKo: "남성용",
            href: "/shop?category=luxury&sub=ps-men",
            navLeaf: true,
            children: [
{nav_children(CLOTHING, "luxury", "ps-men")}
            ],
          }},
        ],
      }},
"""

shoes_nav = f"""
      {{
        id: "paul-smith-shoes",
        labelKo: "폴 스미스",
        href: "/shop?category=shoes&sub=paul-smith-shoes",
        children: [
          {{
            id: "ps-shoes-men",
            labelKo: "남성용",
            href: "/shop?category=shoes&sub=ps-shoes-men",
            navLeaf: true,
            children: [
{nav_children(SHOES, "shoes", "ps-shoes-men")}
            ],
          }},
        ],
      }},
"""

acc_nav = f"""
      {{
        id: "paul-smith-accessories",
        labelKo: "폴 스미스",
        href: "/shop?category=accessories&sub=paul-smith-accessories",
        children: [
          {{
            id: "ps-acc-men",
            labelKo: "남성용",
            href: "/shop?category=accessories&sub=ps-acc-men",
            navLeaf: true,
            children: [
{nav_children(ACC, "accessories", "ps-acc-men")}
            ],
          }},
        ],
      }},
"""

# Insert before the full Burberry brand object so we don't leave an orphan `{`.
if 'id: "paul-smith"' not in text:
    text = text.replace(
        '      {\n        id: "burberry",\n        labelKo: "버버리",',
        luxury_nav + '      {\n        id: "burberry",\n        labelKo: "버버리",',
        1,
    )

if 'id: "paul-smith-shoes"' not in text:
    text = text.replace(
        '      {\n        id: "burberry-shoes",\n        labelKo: "버버리",',
        shoes_nav + '      {\n        id: "burberry-shoes",\n        labelKo: "버버리",',
        1,
    )

if 'id: "paul-smith-accessories"' not in text:
    # Newest brand first in accessories nav
    text = text.replace(
        '      {\n        id: "arcteryx-accessories",\n        labelKo: "아크테릭스",',
        acc_nav + '      {\n        id: "arcteryx-accessories",\n        labelKo: "아크테릭스",',
        1,
    )

PATH.write_text(text)
print("patched", PATH)
print("ids", len(ALL_IDS))
