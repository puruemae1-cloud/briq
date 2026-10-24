#!/usr/bin/env python3
"""Add Paul Smith women + gifts nav/ids into categories.ts (idempotent)."""
from __future__ import annotations

import re
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "src/data/categories.ts"
text = PATH.read_text()

WOMEN_CLOTHING = [
    ("ps-women-coats", "코트"),
    ("ps-women-dresses", "드레스"),
    ("ps-women-jackets", "재킷"),
    ("ps-women-jeans", "진"),
    ("ps-women-knitwear", "니트웨어"),
    ("ps-women-loungewear", "라운지웨어"),
    ("ps-women-pyjamas", "파자마"),
    ("ps-women-shirts", "셔츠"),
    ("ps-women-shorts", "쇼츠"),
    ("ps-women-skirts", "스커트"),
    ("ps-women-suits", "수트"),
    ("ps-women-sweatshirts", "스웻셔츠"),
    ("ps-women-swimwear", "스윔웨어"),
    ("ps-women-tshirts", "티셔츠"),
    ("ps-women-trousers", "트라우저"),
    ("ps-women-waistcoats", "웨이스트코트"),
    ("ps-women-tailoring", "테일러링"),
    ("ps-women-other", "기타 의류"),
]

WOMEN_SHOES = [
    ("ps-shoes-women-boots", "부츠"),
    ("ps-shoes-women-flats", "플랫"),
    ("ps-shoes-women-loafers", "로퍼"),
    ("ps-shoes-women-sandals", "샌들"),
    ("ps-shoes-women-care", "슈케어"),
    ("ps-shoes-women-trainers", "스니커즈"),
    ("ps-shoes-women-other", "기타 슈즈"),
]

WOMEN_ACC = [
    ("ps-acc-women-bags", "백"),
    ("ps-acc-women-belts", "벨트"),
    ("ps-acc-women-gloves", "글러브"),
    ("ps-acc-women-hats", "모자"),
    ("ps-acc-women-jewellery", "주얼리"),
    ("ps-acc-women-keyrings", "키링"),
    ("ps-acc-women-novelty", "노블티"),
    ("ps-acc-women-scarves", "스카프"),
    ("ps-acc-women-slg", "가죽 소품"),
    ("ps-acc-women-socks", "삭스"),
    ("ps-acc-women-stationery", "스테이셔너리"),
    ("ps-acc-women-swimwear", "스윔웨어"),
    ("ps-acc-women-towels", "타월"),
    ("ps-acc-women-umbrellas", "우산"),
    ("ps-acc-women-other", "기타 악세서리"),
]

GIFTS = [
    ("ps-gifts-him", "남성용"),
    ("ps-gifts-her", "여성용"),
    ("ps-gifts-homeware", "홈웨어"),
]

TOP = ["ps-women", "ps-shoes-women", "ps-acc-women", "ps-gifts"]
ALL_NEW = (
    TOP
    + [i for i, _ in WOMEN_CLOTHING]
    + [i for i, _ in WOMEN_SHOES]
    + [i for i, _ in WOMEN_ACC]
    + [i for i, _ in GIFTS]
)

# 1) SubcategoryId union
if "ps-women" not in text:
    text = text.replace(
        '  | "ps-acc-other";',
        '  | "ps-acc-other"\n'
        + "\n".join(f'  | "{i}"' for i in ALL_NEW)
        + ";",
    )

# 2) Constants
const_block = (
    "\nexport const PS_WOMEN_CLOTHING_IDS: SubcategoryId[] = [\n"
    + ",\n".join(f'  "{i}"' for i, _ in WOMEN_CLOTHING)
    + ",\n];\n\n"
    + "export const PS_WOMEN_SHOE_IDS: SubcategoryId[] = [\n"
    + ",\n".join(f'  "{i}"' for i, _ in WOMEN_SHOES)
    + ",\n];\n\n"
    + "export const PS_WOMEN_ACC_IDS: SubcategoryId[] = [\n"
    + ",\n".join(f'  "{i}"' for i, _ in WOMEN_ACC)
    + ",\n];\n\n"
    + "export const PS_GIFTS_IDS: SubcategoryId[] = [\n"
    + ",\n".join(f'  "{i}"' for i, _ in GIFTS)
    + ",\n];\n\n"
)
if "PS_WOMEN_CLOTHING_IDS" not in text:
    text = text.replace(
        "export type NavChild = {",
        const_block + "export type NavChild = {",
    )

# 3) subcategoryGroups — replace Paul Smith block
old_groups = '''  "paul-smith": ["ps-men", ...PS_MEN_CLOTHING_IDS],
  "ps-men": [...PS_MEN_CLOTHING_IDS],
  "paul-smith-shoes": ["ps-shoes-men", ...PS_MEN_SHOE_IDS],
  "ps-shoes-men": [...PS_MEN_SHOE_IDS],
  "paul-smith-accessories": ["ps-acc-men", ...PS_MEN_ACC_IDS],
  "ps-acc-men": [...PS_MEN_ACC_IDS],'''

new_groups = '''  "paul-smith": ["ps-men", "ps-women", ...PS_MEN_CLOTHING_IDS, ...PS_WOMEN_CLOTHING_IDS],
  "ps-men": [...PS_MEN_CLOTHING_IDS],
  "ps-women": [...PS_WOMEN_CLOTHING_IDS],
  "paul-smith-shoes": ["ps-shoes-men", "ps-shoes-women", ...PS_MEN_SHOE_IDS, ...PS_WOMEN_SHOE_IDS],
  "ps-shoes-men": [...PS_MEN_SHOE_IDS],
  "ps-shoes-women": [...PS_WOMEN_SHOE_IDS],
  "paul-smith-accessories": ["ps-acc-men", "ps-acc-women", "ps-gifts", ...PS_MEN_ACC_IDS, ...PS_WOMEN_ACC_IDS, ...PS_GIFTS_IDS],
  "ps-acc-men": [...PS_MEN_ACC_IDS],
  "ps-acc-women": [...PS_WOMEN_ACC_IDS],
  "ps-gifts": [...PS_GIFTS_IDS],'''

if '"ps-women":' not in text or "PS_WOMEN_CLOTHING_IDS" not in text.split("subcategoryGroups")[1][:800]:
    if old_groups in text:
        text = text.replace(old_groups, new_groups)
    elif '"paul-smith": ["ps-men"' in text and "ps-women" not in text[
        text.find('"paul-smith"') : text.find('"paul-smith"') + 200
    ]:
        text = text.replace(old_groups, new_groups)


def nav_children(pairs, cat: str) -> str:
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


women_lux = f"""
          {{
            id: "ps-women",
            labelKo: "여성용",
            href: "/shop?category=luxury&sub=ps-women",
            navLeaf: true,
            children: [
{nav_children(WOMEN_CLOTHING, "luxury")}
            ],
          }},"""

women_shoes = f"""
          {{
            id: "ps-shoes-women",
            labelKo: "여성용",
            href: "/shop?category=shoes&sub=ps-shoes-women",
            navLeaf: true,
            children: [
{nav_children(WOMEN_SHOES, "shoes")}
            ],
          }},"""

women_acc = f"""
          {{
            id: "ps-acc-women",
            labelKo: "여성용",
            href: "/shop?category=accessories&sub=ps-acc-women",
            navLeaf: true,
            children: [
{nav_children(WOMEN_ACC, "accessories")}
            ],
          }},
          {{
            id: "ps-gifts",
            labelKo: "선물용",
            href: "/shop?category=accessories&sub=ps-gifts",
            navLeaf: true,
            children: [
{nav_children(GIFTS, "accessories")}
            ],
          }},"""

# 4) Luxury: insert women after men block closes (before paul-smith children close)
if 'id: "ps-women"' not in text:
    # After ps-men-other block, before closing of paul-smith children
    marker = (
        '                href: "/shop?category=luxury&sub=ps-men-other",\n'
        "              },\n"
        "            ],\n"
        "          },\n"
        "        ],\n"
        "      },\n"
        "      {\n"
        '        id: "burberry",'
    )
    replacement = (
        '                href: "/shop?category=luxury&sub=ps-men-other",\n'
        "              },\n"
        "            ],\n"
        "          },"
        + women_lux
        + "\n"
        "        ],\n"
        "      },\n"
        "      {\n"
        '        id: "burberry",'
    )
    if marker not in text:
        raise SystemExit("luxury marker not found")
    text = text.replace(marker, replacement, 1)

# 5) Shoes: insert women after men shoes
if 'id: "ps-shoes-women"' not in text:
    marker = (
        '                href: "/shop?category=shoes&sub=ps-shoes-other",\n'
        "              },\n"
        "            ],\n"
        "          },\n"
        "        ],\n"
        "      },\n"
        "      {\n"
        '        id: "burberry-shoes",'
    )
    replacement = (
        '                href: "/shop?category=shoes&sub=ps-shoes-other",\n'
        "              },\n"
        "            ],\n"
        "          },"
        + women_shoes
        + "\n"
        "        ],\n"
        "      },\n"
        "      {\n"
        '        id: "burberry-shoes",'
    )
    if marker not in text:
        raise SystemExit("shoes marker not found")
    text = text.replace(marker, replacement, 1)

# 6) Accessories: insert women + gifts after men acc
if 'id: "ps-acc-women"' not in text:
    marker = (
        '                href: "/shop?category=accessories&sub=ps-acc-other",\n'
        "              },\n"
        "            ],\n"
        "          },\n"
        "        ],\n"
        "      },\n"
        "      {\n"
        '        id: "arcteryx-accessories",'
    )
    replacement = (
        '                href: "/shop?category=accessories&sub=ps-acc-other",\n'
        "              },\n"
        "            ],\n"
        "          },"
        + women_acc
        + "\n"
        "        ],\n"
        "      },\n"
        "      {\n"
        '        id: "arcteryx-accessories",'
    )
    if marker not in text:
        raise SystemExit("acc marker not found")
    text = text.replace(marker, replacement, 1)

# Ensure groups updated even if partial
if "PS_WOMEN_CLOTHING_IDS" in text and '"ps-women": [...PS_WOMEN_CLOTHING_IDS]' not in text:
    text = re.sub(
        r'"paul-smith": \["ps-men", \.\.\.PS_MEN_CLOTHING_IDS\],\n'
        r'  "ps-men": \[\.\.\.PS_MEN_CLOTHING_IDS\],\n'
        r'  "paul-smith-shoes": \["ps-shoes-men", \.\.\.PS_MEN_SHOE_IDS\],\n'
        r'  "ps-shoes-men": \[\.\.\.PS_MEN_SHOE_IDS\],\n'
        r'  "paul-smith-accessories": \["ps-acc-men", \.\.\.PS_MEN_ACC_IDS\],\n'
        r'  "ps-acc-men": \[\.\.\.PS_MEN_ACC_IDS\],',
        new_groups,
        text,
        count=1,
    )

PATH.write_text(text)
print("patched", PATH)
print("new ids", len(ALL_NEW))
