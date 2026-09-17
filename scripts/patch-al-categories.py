#!/usr/bin/env python3
"""Wire AllSaints into categories.ts, product-types, products.ts."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

AL_IDS = [
    "all-saints",
    "al-men",
    "al-women",
    "al-men-rtw-all",
    "al-men-coats-jackets",
    "al-men-jeans",
    "al-men-knitwear",
    "al-men-leathers",
    "al-men-leather-jackets",
    "al-men-shirts",
    "al-men-sweatshirts-hoodies",
    "al-men-tshirts",
    "al-men-trousers",
    "al-men-sweatpants",
    "al-women-rtw-all",
    "al-women-coats-jackets",
    "al-women-dresses",
    "al-women-jeans",
    "al-women-knitwear",
    "al-women-leather",
    "al-women-leather-jackets",
    "al-women-shirts",
    "al-women-skirts-shorts",
    "al-women-sweatshirts-hoodies",
    "al-women-tshirts",
    "al-women-tops-shirts",
    "al-women-trousers-leggings",
    "all-saints-shoes",
    "al-men-shoes",
    "al-women-shoes",
    "al-men-shoes-all",
    "al-men-boots",
    "al-men-casual-shoes",
    "al-men-trainers",
    "al-women-shoes-all",
    "al-women-boots",
    "al-women-flats",
    "al-women-heels",
    "al-women-trainers",
    "all-saints-accessories",
    "al-men-accessories",
    "al-women-accessories",
    "al-men-acc-all",
    "al-men-sunglasses",
    "al-men-belts",
    "al-men-wallets",
    "al-men-hats",
    "al-men-jewellery",
    "al-men-bags",
    "al-women-acc-all",
    "al-women-sunglasses",
    "al-women-belts",
    "al-women-scarves",
    "al-women-hats",
    "al-women-jewellery",
    "al-women-handbags",
]

LEAF_CONSTS = '''
export const AL_MEN_RTW_LEAF_IDS: SubcategoryId[] = [
  "al-men-rtw-all","al-men-coats-jackets","al-men-jeans","al-men-knitwear","al-men-leathers",
  "al-men-leather-jackets","al-men-shirts","al-men-sweatshirts-hoodies","al-men-tshirts",
  "al-men-trousers","al-men-sweatpants",
];
export const AL_WOMEN_RTW_LEAF_IDS: SubcategoryId[] = [
  "al-women-rtw-all","al-women-coats-jackets","al-women-dresses","al-women-jeans","al-women-knitwear",
  "al-women-leather","al-women-leather-jackets","al-women-shirts","al-women-skirts-shorts",
  "al-women-sweatshirts-hoodies","al-women-tshirts","al-women-tops-shirts","al-women-trousers-leggings",
];
export const AL_MEN_SHOES_LEAF_IDS: SubcategoryId[] = [
  "al-men-shoes-all","al-men-boots","al-men-casual-shoes","al-men-trainers",
];
export const AL_WOMEN_SHOES_LEAF_IDS: SubcategoryId[] = [
  "al-women-shoes-all","al-women-boots","al-women-flats","al-women-heels","al-women-trainers",
];
export const AL_MEN_ACC_LEAF_IDS: SubcategoryId[] = [
  "al-men-acc-all","al-men-sunglasses","al-men-belts","al-men-wallets","al-men-hats",
  "al-men-jewellery","al-men-bags",
];
export const AL_WOMEN_ACC_LEAF_IDS: SubcategoryId[] = [
  "al-women-acc-all","al-women-sunglasses","al-women-belts","al-women-scarves","al-women-hats",
  "al-women-jewellery","al-women-handbags",
];

'''


def patch_categories() -> None:
    path = ROOT / "src/data/categories.ts"
    text = path.read_text(encoding="utf-8")
    if 'id: "all-saints"' in text and "AL_MEN_RTW_LEAF_IDS" in text:
        print("categories already patched")
        return

    if '| "all-saints"' not in text:
        # Insert union members after saint-laurent-accessories block-ish — after vivienne or belstaff
        anchor = '  | "belstaff"\n'
        if anchor in text:
            text = text.replace(anchor, anchor + "\n".join(f'  | "{i}"' for i in AL_IDS) + "\n", 1)
            print("CategoryId OK")
        else:
            raise SystemExit("CategoryId anchor missing")

    if "AL_MEN_RTW_LEAF_IDS" not in text:
        text = text.replace(
            "export const YS_MEN_RTW_LEAF_IDS",
            LEAF_CONSTS + "export const YS_MEN_RTW_LEAF_IDS",
            1,
        )
        print("leaf consts OK")

    # Expand map — insert before saint-laurent or after belstaff
    if '"all-saints":' not in text:
        expand = '''  "all-saints": ["all-saints", "al-women", ...AL_WOMEN_RTW_LEAF_IDS, "al-men", ...AL_MEN_RTW_LEAF_IDS],
  "al-women": ["al-women", ...AL_WOMEN_RTW_LEAF_IDS],
  "al-men": ["al-men", ...AL_MEN_RTW_LEAF_IDS],
  "all-saints-shoes": ["all-saints-shoes", "al-women-shoes", ...AL_WOMEN_SHOES_LEAF_IDS, "al-men-shoes", ...AL_MEN_SHOES_LEAF_IDS],
  "al-women-shoes": ["al-women-shoes", ...AL_WOMEN_SHOES_LEAF_IDS],
  "al-men-shoes": ["al-men-shoes", ...AL_MEN_SHOES_LEAF_IDS],
  "all-saints-accessories": ["all-saints-accessories", "al-women-accessories", ...AL_WOMEN_ACC_LEAF_IDS, "al-men-accessories", ...AL_MEN_ACC_LEAF_IDS],
  "al-women-accessories": ["al-women-accessories", ...AL_WOMEN_ACC_LEAF_IDS],
  "al-men-accessories": ["al-men-accessories", ...AL_MEN_ACC_LEAF_IDS],
'''
        # leaf self-maps
        for i in AL_IDS:
            if i.startswith("al-") and i not in {
                "al-men",
                "al-women",
                "al-men-shoes",
                "al-women-shoes",
                "al-men-accessories",
                "al-women-accessories",
            }:
                expand += f'  "{i}": ["{i}"],\n'
        text = text.replace(
            '  "saint-laurent": [',
            expand + '  "saint-laurent": [',
            1,
        )
        print("expand map OK")

    # Nav — insert AllSaints after Belstaff or before Saint Laurent in luxury
    if 'id: "all-saints"' not in text:
        nav = '''
      {
        id: "all-saints",
        labelKo: "올세인츠",
        href: "/shop?category=luxury&sub=all-saints",
        children: [
          {
            id: "al-women",
            labelKo: "여성용",
            href: "/shop?category=luxury&sub=al-women",
            navLeaf: true,
            children: [
              { id: "al-women-rtw-all", labelKo: "전체", href: "/shop?category=luxury&sub=al-women-rtw-all" },
              { id: "al-women-coats-jackets", labelKo: "코트 & 재킷", href: "/shop?category=luxury&sub=al-women-coats-jackets" },
              { id: "al-women-dresses", labelKo: "드레스", href: "/shop?category=luxury&sub=al-women-dresses" },
              { id: "al-women-jeans", labelKo: "진", href: "/shop?category=luxury&sub=al-women-jeans" },
              { id: "al-women-knitwear", labelKo: "니트웨어", href: "/shop?category=luxury&sub=al-women-knitwear" },
              { id: "al-women-leather", labelKo: "레더", href: "/shop?category=luxury&sub=al-women-leather" },
              { id: "al-women-leather-jackets", labelKo: "레더 재킷", href: "/shop?category=luxury&sub=al-women-leather-jackets" },
              { id: "al-women-shirts", labelKo: "셔츠", href: "/shop?category=luxury&sub=al-women-shirts" },
              { id: "al-women-skirts-shorts", labelKo: "스커트 & 쇼츠", href: "/shop?category=luxury&sub=al-women-skirts-shorts" },
              { id: "al-women-sweatshirts-hoodies", labelKo: "스웨트셔츠 & 후디", href: "/shop?category=luxury&sub=al-women-sweatshirts-hoodies" },
              { id: "al-women-tshirts", labelKo: "티셔츠", href: "/shop?category=luxury&sub=al-women-tshirts" },
              { id: "al-women-tops-shirts", labelKo: "탑 & 셔츠", href: "/shop?category=luxury&sub=al-women-tops-shirts" },
              { id: "al-women-trousers-leggings", labelKo: "트라우저 & 레깅스", href: "/shop?category=luxury&sub=al-women-trousers-leggings" },
            ],
          },
          {
            id: "al-men",
            labelKo: "남성용",
            href: "/shop?category=luxury&sub=al-men",
            navLeaf: true,
            children: [
              { id: "al-men-rtw-all", labelKo: "전체", href: "/shop?category=luxury&sub=al-men-rtw-all" },
              { id: "al-men-coats-jackets", labelKo: "코트 & 재킷", href: "/shop?category=luxury&sub=al-men-coats-jackets" },
              { id: "al-men-jeans", labelKo: "진", href: "/shop?category=luxury&sub=al-men-jeans" },
              { id: "al-men-knitwear", labelKo: "니트웨어", href: "/shop?category=luxury&sub=al-men-knitwear" },
              { id: "al-men-leathers", labelKo: "레더", href: "/shop?category=luxury&sub=al-men-leathers" },
              { id: "al-men-leather-jackets", labelKo: "레더 재킷", href: "/shop?category=luxury&sub=al-men-leather-jackets" },
              { id: "al-men-shirts", labelKo: "셔츠", href: "/shop?category=luxury&sub=al-men-shirts" },
              { id: "al-men-sweatshirts-hoodies", labelKo: "스웨트셔츠 & 후디", href: "/shop?category=luxury&sub=al-men-sweatshirts-hoodies" },
              { id: "al-men-tshirts", labelKo: "티셔츠", href: "/shop?category=luxury&sub=al-men-tshirts" },
              { id: "al-men-trousers", labelKo: "트라우저", href: "/shop?category=luxury&sub=al-men-trousers" },
              { id: "al-men-sweatpants", labelKo: "스웨트팬츠", href: "/shop?category=luxury&sub=al-men-sweatpants" },
            ],
          },
        ],
      },
'''
        text = text.replace(
            '{\n        id: "saint-laurent",\n        labelKo: "생로랑",',
            nav + '\n      {\n        id: "saint-laurent",\n        labelKo: "생로랑",',
            1,
        )
        print("luxury nav OK")

    # Shoes nav
    if 'id: "all-saints-shoes"' not in text:
        shoes_nav = '''
      {
        id: "all-saints-shoes",
        labelKo: "올세인츠",
        href: "/shop?category=shoes&sub=all-saints-shoes",
        children: [
          {
            id: "al-women-shoes",
            labelKo: "여성용",
            href: "/shop?category=shoes&sub=al-women-shoes",
            navLeaf: true,
            children: [
              { id: "al-women-shoes-all", labelKo: "전체", href: "/shop?category=shoes&sub=al-women-shoes-all" },
              { id: "al-women-boots", labelKo: "부츠", href: "/shop?category=shoes&sub=al-women-boots" },
              { id: "al-women-flats", labelKo: "플랫", href: "/shop?category=shoes&sub=al-women-flats" },
              { id: "al-women-heels", labelKo: "힐", href: "/shop?category=shoes&sub=al-women-heels" },
              { id: "al-women-trainers", labelKo: "스니커즈", href: "/shop?category=shoes&sub=al-women-trainers" },
            ],
          },
          {
            id: "al-men-shoes",
            labelKo: "남성용",
            href: "/shop?category=shoes&sub=al-men-shoes",
            navLeaf: true,
            children: [
              { id: "al-men-shoes-all", labelKo: "전체", href: "/shop?category=shoes&sub=al-men-shoes-all" },
              { id: "al-men-boots", labelKo: "부츠", href: "/shop?category=shoes&sub=al-men-boots" },
              { id: "al-men-casual-shoes", labelKo: "슈즈", href: "/shop?category=shoes&sub=al-men-casual-shoes" },
              { id: "al-men-trainers", labelKo: "스니커즈", href: "/shop?category=shoes&sub=al-men-trainers" },
            ],
          },
        ],
      },
'''
        # note: al-men-shoes leaf id conflicts with hub id — hub is al-men-shoes parent, leaf for shoes subcategory should be different
        # Fix: leaf for formal shoes is already "al-men-shoes" in config — conflict with hub!
        # In config I used al-men-shoes as hub parent AND leaf for /men/boots-and-shoes/shoes
        # Need to rename leaf to al-men-formal-shoes or al-men-shoes-flat
        text = text.replace(
            '{\n        id: "saint-laurent-shoes",\n        labelKo: "생로랑",',
            shoes_nav + '\n      {\n        id: "saint-laurent-shoes",\n        labelKo: "생로랑",',
            1,
        )
        print("shoes nav OK")

    # Accessories nav
    if 'id: "all-saints-accessories"' not in text:
        acc_nav = '''
      {
        id: "all-saints-accessories",
        labelKo: "올세인츠",
        href: "/shop?category=accessories&sub=all-saints-accessories",
        children: [
          {
            id: "al-women-accessories",
            labelKo: "여성용",
            href: "/shop?category=accessories&sub=al-women-accessories",
            navLeaf: true,
            children: [
              { id: "al-women-acc-all", labelKo: "전체", href: "/shop?category=accessories&sub=al-women-acc-all" },
              { id: "al-women-sunglasses", labelKo: "선글라스", href: "/shop?category=accessories&sub=al-women-sunglasses" },
              { id: "al-women-belts", labelKo: "벨트", href: "/shop?category=accessories&sub=al-women-belts" },
              { id: "al-women-scarves", labelKo: "스카프", href: "/shop?category=accessories&sub=al-women-scarves" },
              { id: "al-women-hats", labelKo: "모자", href: "/shop?category=accessories&sub=al-women-hats" },
              { id: "al-women-jewellery", labelKo: "주얼리", href: "/shop?category=accessories&sub=al-women-jewellery" },
              { id: "al-women-handbags", labelKo: "핸드백", href: "/shop?category=accessories&sub=al-women-handbags" },
            ],
          },
          {
            id: "al-men-accessories",
            labelKo: "남성용",
            href: "/shop?category=accessories&sub=al-men-accessories",
            navLeaf: true,
            children: [
              { id: "al-men-acc-all", labelKo: "전체", href: "/shop?category=accessories&sub=al-men-acc-all" },
              { id: "al-men-sunglasses", labelKo: "선글라스", href: "/shop?category=accessories&sub=al-men-sunglasses" },
              { id: "al-men-belts", labelKo: "벨트", href: "/shop?category=accessories&sub=al-men-belts" },
              { id: "al-men-wallets", labelKo: "지갑", href: "/shop?category=accessories&sub=al-men-wallets" },
              { id: "al-men-hats", labelKo: "모자", href: "/shop?category=accessories&sub=al-men-hats" },
              { id: "al-men-jewellery", labelKo: "주얼리", href: "/shop?category=accessories&sub=al-men-jewellery" },
              { id: "al-men-bags", labelKo: "가방", href: "/shop?category=accessories&sub=al-men-bags" },
            ],
          },
        ],
      },
'''
        text = text.replace(
            '{\n        id: "saint-laurent-accessories",\n        labelKo: "생로랑",',
            acc_nav + '\n      {\n        id: "saint-laurent-accessories",\n        labelKo: "생로랑",',
            1,
        )
        print("accessories nav OK")

    path.write_text(text, encoding="utf-8")
    print("wrote", path)


def patch_product_types() -> None:
    path = ROOT / "src/data/product-types.ts"
    text = path.read_text(encoding="utf-8")
    if "alCollections" in text:
        print("product-types already has alCollections")
        return
    text = text.replace(
        "  vwCollections?: SubcategoryId[];\n",
        "  vwCollections?: SubcategoryId[];\n  alCollections?: SubcategoryId[];\n",
    )
    # appears twice (product + variant)
    path.write_text(text, encoding="utf-8")
    print("product-types OK")


def patch_products_ts() -> None:
    path = ROOT / "src/data/products.ts"
    text = path.read_text(encoding="utf-8")
    if "alCatalogProducts" in text:
        print("products.ts already wired")
        return
    text = text.replace(
        'import { vwCatalogProducts } from "@/data/vw/vw-catalog";\n',
        'import { vwCatalogProducts } from "@/data/vw/vw-catalog";\n'
        'import { alCatalogProducts } from "@/data/al/al-catalog";\n',
        1,
    )
    # add to core list — after vw
    text = text.replace(
        "  ...vwCatalogProducts,\n",
        "  ...vwCatalogProducts,\n  ...alCatalogProducts,\n",
        1,
    )
    text = text.replace(
        "      if (p.vwCollections?.some((c) => expanded.includes(c))) return true;\n",
        "      if (p.vwCollections?.some((c) => expanded.includes(c))) return true;\n"
        "      if (p.alCollections?.some((c) => expanded.includes(c))) return true;\n",
        1,
    )
    text = text.replace(
        "      if (p.variants?.some((v) => v.vwCollections?.some((c) => expanded.includes(c))))\n",
        "      if (p.variants?.some((v) => v.vwCollections?.some((c) => expanded.includes(c))))\n"
        "        return true;\n"
        "      if (p.variants?.some((v) => v.alCollections?.some((c) => expanded.includes(c))))\n",
        1,
    )
    path.write_text(text, encoding="utf-8")
    print("products.ts OK")


def main() -> int:
    # Fix men shoes leaf id collision: hub al-men-shoes vs leaf al-men-shoes
    # Rename leaf in al_config to al-men-dress-shoes — already need fix before patch nav
    patch_categories()
    patch_product_types()
    patch_products_ts()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
