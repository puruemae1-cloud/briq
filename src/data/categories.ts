export type CategoryId =
  | "luxury"
  | "watches"
  | "clothing"
  | "bags"
  | "shoes"
  | "accessories"
  | "sports";

export type SubcategoryId =
  | "womens"
  | "mens"
  | "jewelry"
  | "cosmetics"
  | "wallets"
  | "snacks"
  | "health-food"
  | "british-tea"
  | "golf"
  | "running"
  | "swimming"
  | "cycling"
  | "tennis"
  | "christopher-ward"
  | "luxury-shoes"
  | "training-shoes"
  | "luxury-womens"
  | "luxury-mens"
  | "training-womens"
  | "training-mens";

export type NavChild = {
  id: SubcategoryId;
  labelKo: string;
  href: string;
  children?: NavChild[];
};

export type NavCategory = {
  id: CategoryId;
  labelKo: string;
  href: string;
  children?: NavChild[];
};

/** Expands group subcategory ids (e.g. luxury-shoes → womens/mens leaf ids). */
export const subcategoryGroups: Partial<Record<SubcategoryId, SubcategoryId[]>> = {
  "luxury-shoes": ["luxury-womens", "luxury-mens"],
  "training-shoes": ["training-womens", "training-mens"],
};

/** Top nav order: Shop first (handled separately), then these left→right, sports last */
export const navCategories: NavCategory[] = [
  {
    id: "luxury",
    labelKo: "명품럭셔리 의류",
    href: "/shop?category=luxury",
    children: [
      { id: "womens", labelKo: "Womens", href: "/shop?category=luxury&sub=womens" },
      { id: "mens", labelKo: "Mens", href: "/shop?category=luxury&sub=mens" },
    ],
  },
  {
    id: "watches",
    labelKo: "시계",
    href: "/shop?category=watches",
    children: [
      {
        id: "christopher-ward",
        labelKo: "크리스토퍼와드",
        href: "/shop?category=watches&sub=christopher-ward",
      },
    ],
  },
  {
    id: "clothing",
    labelKo: "패션의류",
    href: "/shop?category=clothing",
    children: [
      { id: "womens", labelKo: "Womens", href: "/shop?category=clothing&sub=womens" },
      { id: "mens", labelKo: "Mens", href: "/shop?category=clothing&sub=mens" },
    ],
  },
  {
    id: "bags",
    labelKo: "가방",
    href: "/shop?category=bags",
  },
  {
    id: "shoes",
    labelKo: "슈즈",
    href: "/shop?category=shoes",
    children: [
      {
        id: "luxury-shoes",
        labelKo: "럭셔리 슈즈",
        href: "/shop?category=shoes&sub=luxury-shoes",
        children: [
          {
            id: "luxury-womens",
            labelKo: "Womens",
            href: "/shop?category=shoes&sub=luxury-womens",
          },
          {
            id: "luxury-mens",
            labelKo: "Mens",
            href: "/shop?category=shoes&sub=luxury-mens",
          },
        ],
      },
      {
        id: "training-shoes",
        labelKo: "트레이닝 슈즈",
        href: "/shop?category=shoes&sub=training-shoes",
        children: [
          {
            id: "training-womens",
            labelKo: "Womens",
            href: "/shop?category=shoes&sub=training-womens",
          },
          {
            id: "training-mens",
            labelKo: "Mens",
            href: "/shop?category=shoes&sub=training-mens",
          },
        ],
      },
    ],
  },
  {
    id: "accessories",
    labelKo: "악세서리",
    href: "/shop?category=accessories",
    children: [
      { id: "jewelry", labelKo: "쥬얼리", href: "/shop?category=accessories&sub=jewelry" },
      { id: "cosmetics", labelKo: "화장품", href: "/shop?category=accessories&sub=cosmetics" },
      { id: "wallets", labelKo: "지갑", href: "/shop?category=accessories&sub=wallets" },
      { id: "snacks", labelKo: "스낵", href: "/shop?category=accessories&sub=snacks" },
      { id: "health-food", labelKo: "건강식품", href: "/shop?category=accessories&sub=health-food" },
      { id: "british-tea", labelKo: "영국 Tea", href: "/shop?category=accessories&sub=british-tea" },
    ],
  },
  {
    id: "sports",
    labelKo: "스포츠",
    href: "/shop?category=sports",
    children: [
      { id: "golf", labelKo: "골프", href: "/shop?category=sports&sub=golf" },
      { id: "running", labelKo: "러닝", href: "/shop?category=sports&sub=running" },
      { id: "swimming", labelKo: "수영", href: "/shop?category=sports&sub=swimming" },
      { id: "cycling", labelKo: "자전거", href: "/shop?category=sports&sub=cycling" },
      { id: "tennis", labelKo: "테니스", href: "/shop?category=sports&sub=tennis" },
    ],
  },
];

export function findCategory(id: string) {
  return navCategories.find((c) => c.id === id);
}

export function categoryLabel(id?: string) {
  if (!id || id === "all") return "전체상품";
  return findCategory(id)?.labelKo ?? id;
}

/** Depth-first search for a subcategory node under a category. */
export function findSubcategory(
  categoryId: string,
  subId: string,
): NavChild | undefined {
  const category = findCategory(categoryId);
  if (!category?.children) return undefined;

  const walk = (nodes: NavChild[]): NavChild | undefined => {
    for (const node of nodes) {
      if (node.id === subId) return node;
      if (node.children) {
        const found = walk(node.children);
        if (found) return found;
      }
    }
    return undefined;
  };

  return walk(category.children);
}

export function subcategoryLabel(categoryId: string, subId: string) {
  return findSubcategory(categoryId, subId)?.labelKo ?? subId;
}

/** Leaf + group chips for shop filter rows (keeps nested groups intact). */
export function getShopFilterChildren(categoryId: string): NavChild[] {
  return findCategory(categoryId)?.children ?? [];
}

/** Flat list of navigable children for homepage rails / simple menus. */
export function flattenNavChildren(children?: NavChild[]): NavChild[] {
  if (!children?.length) return [];
  const out: NavChild[] = [];
  for (const child of children) {
    if (child.children?.length) {
      out.push(child);
      for (const nested of child.children) out.push(nested);
    } else {
      out.push(child);
    }
  }
  return out;
}

export function expandSubcategoryFilter(sub?: string): string[] | undefined {
  if (!sub) return undefined;
  const group = subcategoryGroups[sub as SubcategoryId];
  return group ? group : [sub];
}
