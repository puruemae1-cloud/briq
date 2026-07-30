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
  | "cw-new-releases"
  | "cw-bestsellers"
  | "cw-hidden-gems"
  | "cw-clearance"
  | "cw-atelier"
  | "cw-dive"
  | "cw-integrated-sports"
  | "cw-adventure-field"
  | "cw-military"
  | "cw-bel-canto"
  | "cw-sealander"
  | "cw-twelve"
  | "cw-trident"
  | "cw-moonphase"
  | "gg-new-men"
  | "gg-new-women"
  | "gg-bestsellers-men"
  | "gg-bestsellers-women"
  | "gg-men"
  | "gg-women"
  | "gg-accessories"
  | "gg-sale"
  | "galvin-green"
  | "gg-new-arrivals"
  | "gg-bestsellers"
  | "luxury-shoes"
  | "training-shoes"
  | "luxury-womens"
  | "luxury-mens"
  | "training-womens"
  | "training-mens"
  | "burberry"
  | "bb-women"
  | "bb-women-latest"
  | "bb-women-new"
  | "bb-women-summer-styles"
  | "bb-women-classics"
  | "bb-women-coats-jackets"
  | "bb-women-coats"
  | "bb-women-jackets"
  | "bb-women-trench-coats"
  | "bb-women-quilted-jackets"
  | "bb-women-puffer-jackets"
  | "bb-women-ponchos-capes"
  | "bb-women-clothes"
  | "bb-women-knitwear"
  | "bb-women-polos-tshirts"
  | "bb-women-shirts-tops"
  | "bb-women-dresses"
  | "bb-women-skirts"
  | "bb-women-hoodies-sweatshirts"
  | "bb-women-blazers-tailoring"
  | "bb-women-trousers-shorts"
  | "bb-women-activewear"
  | "bb-women-denim"
  | "bb-women-swimwear"
  | "burberry-bags"
  | "bb-bags-womens"
  | "bb-women-bags"
  | "bb-women-mini-bags"
  | "bb-women-tote-bags"
  | "bb-women-crossbody-bags"
  | "bb-women-shoulder-bags"
  | "bb-women-top-handle-bags"
  | "bb-women-backpacks"
  | "burberry-shoes"
  | "bb-shoes-womens"
  | "bb-women-shoes"
  | "bb-women-sneakers"
  | "bb-women-sandals"
  | "bb-women-loafers-ballerinas"
  | "bb-women-boots"
  | "bb-women-pumps"
  | "burberry-accessories"
  | "bb-accessories-womens"
  | "bb-women-accessories"
  | "bb-women-scarves"
  | "bb-women-belts"
  | "bb-women-sunglasses"
  | "bb-women-caps-hats"
  | "bb-women-umbrellas"
  | "bb-women-jewellery"
  | "bb-women-home"
  | "bb-women-socks-tights"
  | "bb-women-tech-travel"
  | "bb-women-key-charms"
  | "bb-women-wallets"
  | "bb-women-card-cases"
  | "bb-women-long-wallets"
  | "bb-women-compact-wallets"
  | "bb-women-chain-strap-wallets"
  | "bb-women-gifts"
  | "bb-women-fragrance"
  | "bb-women-personalised-gifts"
  | "bb-women-personalised-scarves"
  | "bb-men"
  | "bb-men-latest"
  | "bb-men-new"
  | "bb-men-summer-styles"
  | "bb-men-classics"
  | "bb-men-coats-jackets"
  | "bb-men-coats"
  | "bb-men-jackets"
  | "bb-men-trench-coats"
  | "bb-men-quilted-jackets"
  | "bb-men-puffer-jackets"
  | "bb-men-clothes"
  | "bb-men-knitwear"
  | "bb-men-polos"
  | "bb-men-tshirts"
  | "bb-men-shirts"
  | "bb-men-hoodies-sweatshirts"
  | "bb-men-blazers-tailoring"
  | "bb-men-trousers-shorts"
  | "bb-men-activewear"
  | "bb-men-denim"
  | "bb-men-swimwear"
  | "bb-bags-mens"
  | "bb-men-bags"
  | "bb-men-crossbody-bags"
  | "bb-men-backpacks"
  | "bb-men-belt-bags"
  | "bb-men-tote-bags"
  | "bb-men-holdall-bags"
  | "bb-men-briefcases"
  | "bb-shoes-mens"
  | "bb-men-shoes"
  | "bb-men-sneakers"
  | "bb-men-sandals"
  | "bb-men-boots"
  | "bb-men-loafers-lace-ups"
  | "bb-accessories-mens"
  | "bb-men-accessories"
  | "bb-men-scarves"
  | "bb-men-ties-cufflinks"
  | "bb-men-belts"
  | "bb-men-sunglasses"
  | "bb-men-caps-hats"
  | "bb-men-umbrellas"
  | "bb-men-jewellery"
  | "bb-men-socks"
  | "bb-men-tech-travel"
  | "bb-men-home"
  | "bb-men-key-charms"
  | "bb-men-wallets"
  | "bb-men-bifold-wallets"
  | "bb-men-card-cases"
  | "bb-men-long-wallets"
  | "bb-men-pouches"
  | "bb-men-gifts"
  | "bb-men-fragrance"
  | "bb-men-personalised-gifts"
  | "bb-men-personalised-scarves";

/** Christopher Ward leaf collections under the parent brand chip. */
export const CW_COLLECTION_IDS: SubcategoryId[] = [
  "cw-new-releases",
  "cw-bestsellers",
  "cw-hidden-gems",
  "cw-clearance",
  "cw-atelier",
  "cw-dive",
  "cw-integrated-sports",
  "cw-adventure-field",
  "cw-military",
  "cw-bel-canto",
  "cw-sealander",
  "cw-twelve",
  "cw-trident",
  "cw-moonphase",
];

export const GG_NEW_ARRIVAL_IDS: SubcategoryId[] = [
  "gg-new-men",
  "gg-new-women",
];

export const GG_BESTSELLER_IDS: SubcategoryId[] = [
  "gg-bestsellers-men",
  "gg-bestsellers-women",
];

/** Top-level Galvin Green shop chips (under the brand). */
export const GG_BRAND_LEAF_IDS: SubcategoryId[] = [
  "gg-men",
  "gg-women",
  "gg-accessories",
  "gg-sale",
];

export const GG_COLLECTION_IDS: SubcategoryId[] = [
  ...GG_NEW_ARRIVAL_IDS,
  ...GG_BESTSELLER_IDS,
  ...GG_BRAND_LEAF_IDS,
];

export const BB_WOMEN_LATEST_IDS: SubcategoryId[] = [
  "bb-women-new",
  "bb-women-summer-styles",
  "bb-women-classics",
];

export const BB_WOMEN_COATS_IDS: SubcategoryId[] = [
  "bb-women-coats-jackets",
  "bb-women-coats",
  "bb-women-jackets",
  "bb-women-trench-coats",
  "bb-women-quilted-jackets",
  "bb-women-puffer-jackets",
  "bb-women-ponchos-capes",
];

export const BB_WOMEN_CLOTHES_IDS: SubcategoryId[] = [
  "bb-women-clothes",
  "bb-women-knitwear",
  "bb-women-polos-tshirts",
  "bb-women-shirts-tops",
  "bb-women-dresses",
  "bb-women-skirts",
  "bb-women-hoodies-sweatshirts",
  "bb-women-blazers-tailoring",
  "bb-women-trousers-shorts",
  "bb-women-activewear",
  "bb-women-denim",
  "bb-women-swimwear",
];

export const BB_WOMEN_BAG_IDS: SubcategoryId[] = [
  "bb-women-bags",
  "bb-women-mini-bags",
  "bb-women-tote-bags",
  "bb-women-crossbody-bags",
  "bb-women-shoulder-bags",
  "bb-women-top-handle-bags",
  "bb-women-backpacks",
];

export const BB_WOMEN_SHOE_IDS: SubcategoryId[] = [
  "bb-women-shoes",
  "bb-women-sneakers",
  "bb-women-sandals",
  "bb-women-loafers-ballerinas",
  "bb-women-boots",
  "bb-women-pumps",
];

export const BB_WOMEN_ACCESSORY_LEAF_IDS: SubcategoryId[] = [
  "bb-women-scarves",
  "bb-women-belts",
  "bb-women-sunglasses",
  "bb-women-caps-hats",
  "bb-women-umbrellas",
  "bb-women-jewellery",
  "bb-women-home",
  "bb-women-socks-tights",
  "bb-women-tech-travel",
  "bb-women-key-charms",
];

export const BB_WOMEN_WALLET_IDS: SubcategoryId[] = [
  "bb-women-wallets",
  "bb-women-card-cases",
  "bb-women-long-wallets",
  "bb-women-compact-wallets",
  "bb-women-chain-strap-wallets",
];

export const BB_WOMEN_GIFT_IDS: SubcategoryId[] = [
  "bb-women-gifts",
  "bb-women-fragrance",
  "bb-women-personalised-gifts",
  "bb-women-personalised-scarves",
];

/** Burberry Women leaf collection ids used for PLP membership. */
export const BB_WOMEN_COLLECTION_IDS: SubcategoryId[] = [
  ...BB_WOMEN_LATEST_IDS,
  ...BB_WOMEN_COATS_IDS,
  ...BB_WOMEN_CLOTHES_IDS,
  ...BB_WOMEN_BAG_IDS,
  ...BB_WOMEN_SHOE_IDS,
  ...BB_WOMEN_ACCESSORY_LEAF_IDS,
  ...BB_WOMEN_WALLET_IDS,
  ...BB_WOMEN_GIFT_IDS,
];

export const BB_MEN_LATEST_IDS: SubcategoryId[] = [
  "bb-men-new",
  "bb-men-summer-styles",
  "bb-men-classics",
];

export const BB_MEN_COATS_IDS: SubcategoryId[] = [
  "bb-men-coats-jackets",
  "bb-men-coats",
  "bb-men-jackets",
  "bb-men-trench-coats",
  "bb-men-quilted-jackets",
  "bb-men-puffer-jackets",
];

export const BB_MEN_CLOTHES_IDS: SubcategoryId[] = [
  "bb-men-clothes",
  "bb-men-knitwear",
  "bb-men-polos",
  "bb-men-tshirts",
  "bb-men-shirts",
  "bb-men-hoodies-sweatshirts",
  "bb-men-blazers-tailoring",
  "bb-men-trousers-shorts",
  "bb-men-activewear",
  "bb-men-denim",
  "bb-men-swimwear",
];

export const BB_MEN_BAG_IDS: SubcategoryId[] = [
  "bb-men-bags",
  "bb-men-crossbody-bags",
  "bb-men-backpacks",
  "bb-men-belt-bags",
  "bb-men-tote-bags",
  "bb-men-holdall-bags",
  "bb-men-briefcases",
];

export const BB_MEN_SHOE_IDS: SubcategoryId[] = [
  "bb-men-shoes",
  "bb-men-sneakers",
  "bb-men-sandals",
  "bb-men-boots",
  "bb-men-loafers-lace-ups",
];

export const BB_MEN_ACCESSORY_LEAF_IDS: SubcategoryId[] = [
  "bb-men-scarves",
  "bb-men-ties-cufflinks",
  "bb-men-belts",
  "bb-men-sunglasses",
  "bb-men-caps-hats",
  "bb-men-umbrellas",
  "bb-men-jewellery",
  "bb-men-socks",
  "bb-men-tech-travel",
  "bb-men-home",
  "bb-men-key-charms",
];

export const BB_MEN_WALLET_IDS: SubcategoryId[] = [
  "bb-men-wallets",
  "bb-men-bifold-wallets",
  "bb-men-card-cases",
  "bb-men-long-wallets",
  "bb-men-pouches",
];

export const BB_MEN_GIFT_IDS: SubcategoryId[] = [
  "bb-men-gifts",
  "bb-men-fragrance",
  "bb-men-personalised-gifts",
  "bb-men-personalised-scarves",
];

/** Burberry Men leaf collection ids used for PLP membership. */
export const BB_MEN_COLLECTION_IDS: SubcategoryId[] = [
  ...BB_MEN_LATEST_IDS,
  ...BB_MEN_COATS_IDS,
  ...BB_MEN_CLOTHES_IDS,
  ...BB_MEN_BAG_IDS,
  ...BB_MEN_SHOE_IDS,
  ...BB_MEN_ACCESSORY_LEAF_IDS,
  ...BB_MEN_WALLET_IDS,
  ...BB_MEN_GIFT_IDS,
];

/** All Burberry leaf ids (women + men) used for PLP membership. */
export const BB_COLLECTION_IDS: SubcategoryId[] = [
  ...BB_WOMEN_COLLECTION_IDS,
  ...BB_MEN_COLLECTION_IDS,
];

export const BB_LUXURY_WOMEN_IDS: SubcategoryId[] = [
  ...BB_WOMEN_LATEST_IDS,
  ...BB_WOMEN_COATS_IDS,
  ...BB_WOMEN_CLOTHES_IDS,
];

export const BB_LUXURY_MEN_IDS: SubcategoryId[] = [
  ...BB_MEN_LATEST_IDS,
  ...BB_MEN_COATS_IDS,
  ...BB_MEN_CLOTHES_IDS,
];

export type NavChild = {
  id: SubcategoryId;
  labelKo: string;
  href: string;
  children?: NavChild[];
  /** Header/drawer: link only — nested children stay for shop filter chips. */
  navLeaf?: boolean;
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
  "christopher-ward": [...CW_COLLECTION_IDS],
  golf: [
    "golf",
    "galvin-green",
    "gg-new-arrivals",
    "gg-bestsellers",
    ...GG_COLLECTION_IDS,
  ],
  "galvin-green": [
    "gg-new-arrivals",
    "gg-bestsellers",
    ...GG_COLLECTION_IDS,
  ],
  "gg-new-arrivals": [...GG_NEW_ARRIVAL_IDS],
  "gg-bestsellers": [...GG_BESTSELLER_IDS],
  burberry: [...BB_LUXURY_WOMEN_IDS, ...BB_LUXURY_MEN_IDS],
  "bb-women": [...BB_LUXURY_WOMEN_IDS],
  "bb-women-latest": [...BB_WOMEN_LATEST_IDS],
  "bb-women-coats-jackets": [...BB_WOMEN_COATS_IDS],
  "bb-women-clothes": [...BB_WOMEN_CLOTHES_IDS],
  "bb-men": [...BB_LUXURY_MEN_IDS],
  "bb-men-latest": [...BB_MEN_LATEST_IDS],
  "bb-men-coats-jackets": [...BB_MEN_COATS_IDS],
  "bb-men-clothes": [...BB_MEN_CLOTHES_IDS],
  "burberry-bags": [
    "bb-bags-womens",
    "bb-bags-mens",
    ...BB_WOMEN_BAG_IDS,
    ...BB_MEN_BAG_IDS,
  ],
  "bb-bags-womens": [...BB_WOMEN_BAG_IDS],
  "bb-women-bags": [...BB_WOMEN_BAG_IDS],
  "bb-bags-mens": [...BB_MEN_BAG_IDS],
  "bb-men-bags": [...BB_MEN_BAG_IDS],
  "burberry-shoes": [
    "bb-shoes-womens",
    "bb-shoes-mens",
    ...BB_WOMEN_SHOE_IDS,
    ...BB_MEN_SHOE_IDS,
  ],
  "bb-shoes-womens": [...BB_WOMEN_SHOE_IDS],
  "bb-women-shoes": [...BB_WOMEN_SHOE_IDS],
  "bb-shoes-mens": [...BB_MEN_SHOE_IDS],
  "bb-men-shoes": [...BB_MEN_SHOE_IDS],
  "burberry-accessories": [
    "bb-accessories-womens",
    "bb-accessories-mens",
    ...BB_WOMEN_ACCESSORY_LEAF_IDS,
    ...BB_WOMEN_WALLET_IDS,
    ...BB_WOMEN_GIFT_IDS,
    ...BB_MEN_ACCESSORY_LEAF_IDS,
    ...BB_MEN_WALLET_IDS,
    ...BB_MEN_GIFT_IDS,
  ],
  "bb-accessories-womens": [
    ...BB_WOMEN_ACCESSORY_LEAF_IDS,
    ...BB_WOMEN_WALLET_IDS,
    ...BB_WOMEN_GIFT_IDS,
  ],
  "bb-women-accessories": [...BB_WOMEN_ACCESSORY_LEAF_IDS],
  "bb-women-wallets": [...BB_WOMEN_WALLET_IDS],
  "bb-women-gifts": [...BB_WOMEN_GIFT_IDS],
  "bb-accessories-mens": [
    ...BB_MEN_ACCESSORY_LEAF_IDS,
    ...BB_MEN_WALLET_IDS,
    ...BB_MEN_GIFT_IDS,
  ],
  "bb-men-accessories": [...BB_MEN_ACCESSORY_LEAF_IDS],
  "bb-men-wallets": [...BB_MEN_WALLET_IDS],
  "bb-men-gifts": [...BB_MEN_GIFT_IDS],
};

/** Top nav order: Shop first (handled separately), then these left→right, sports last */
export const navCategories: NavCategory[] = [
  {
    id: "luxury",
    labelKo: "명품 하이엔드 의류",
    href: "/shop?category=luxury",
    children: [
      {
        id: "burberry",
        labelKo: "버버리",
        href: "/shop?category=luxury&sub=burberry",
        navLeaf: true,
        children: [
          {
            id: "bb-women",
            labelKo: "Women",
            href: "/shop?category=luxury&sub=bb-women",
            children: [
              {
                id: "bb-women-latest",
                labelKo: "Latest",
                href: "/shop?category=luxury&sub=bb-women-latest",
                children: [
                  { id: "bb-women-new", labelKo: "New", href: "/shop?category=luxury&sub=bb-women-new" },
                  { id: "bb-women-summer-styles", labelKo: "Summer Styles", href: "/shop?category=luxury&sub=bb-women-summer-styles" },
                  { id: "bb-women-classics", labelKo: "버버리 Classics", href: "/shop?category=luxury&sub=bb-women-classics" },
                ],
              },
              {
                id: "bb-women-coats-jackets",
                labelKo: "Coats & Jackets",
                href: "/shop?category=luxury&sub=bb-women-coats-jackets",
                children: [
                  { id: "bb-women-coats", labelKo: "Coats", href: "/shop?category=luxury&sub=bb-women-coats" },
                  { id: "bb-women-jackets", labelKo: "Jackets", href: "/shop?category=luxury&sub=bb-women-jackets" },
                  { id: "bb-women-trench-coats", labelKo: "Trench Coats", href: "/shop?category=luxury&sub=bb-women-trench-coats" },
                  { id: "bb-women-quilted-jackets", labelKo: "Quilted Jackets", href: "/shop?category=luxury&sub=bb-women-quilted-jackets" },
                  { id: "bb-women-puffer-jackets", labelKo: "Puffer Jackets", href: "/shop?category=luxury&sub=bb-women-puffer-jackets" },
                  { id: "bb-women-ponchos-capes", labelKo: "Ponchos & Capes", href: "/shop?category=luxury&sub=bb-women-ponchos-capes" },
                ],
              },
              {
                id: "bb-women-clothes",
                labelKo: "Clothes",
                href: "/shop?category=luxury&sub=bb-women-clothes",
                children: [
                  { id: "bb-women-knitwear", labelKo: "Knitwear", href: "/shop?category=luxury&sub=bb-women-knitwear" },
                  { id: "bb-women-polos-tshirts", labelKo: "Polos & T-shirts", href: "/shop?category=luxury&sub=bb-women-polos-tshirts" },
                  { id: "bb-women-shirts-tops", labelKo: "Shirts & Tops", href: "/shop?category=luxury&sub=bb-women-shirts-tops" },
                  { id: "bb-women-dresses", labelKo: "Dresses", href: "/shop?category=luxury&sub=bb-women-dresses" },
                  { id: "bb-women-skirts", labelKo: "Skirts", href: "/shop?category=luxury&sub=bb-women-skirts" },
                  { id: "bb-women-hoodies-sweatshirts", labelKo: "Hoodies & Sweatshirts", href: "/shop?category=luxury&sub=bb-women-hoodies-sweatshirts" },
                  { id: "bb-women-blazers-tailoring", labelKo: "Blazers & Tailoring", href: "/shop?category=luxury&sub=bb-women-blazers-tailoring" },
                  { id: "bb-women-trousers-shorts", labelKo: "Trousers & Shorts", href: "/shop?category=luxury&sub=bb-women-trousers-shorts" },
                  { id: "bb-women-activewear", labelKo: "Activewear", href: "/shop?category=luxury&sub=bb-women-activewear" },
                  { id: "bb-women-denim", labelKo: "Denim", href: "/shop?category=luxury&sub=bb-women-denim" },
                  { id: "bb-women-swimwear", labelKo: "Swimwear", href: "/shop?category=luxury&sub=bb-women-swimwear" },
                ],
              },
            ],
          },
          {
            id: "bb-men",
            labelKo: "Men",
            href: "/shop?category=luxury&sub=bb-men",
            children: [
              {
                id: "bb-men-latest",
                labelKo: "Latest",
                href: "/shop?category=luxury&sub=bb-men-latest",
                children: [
                  { id: "bb-men-new", labelKo: "New", href: "/shop?category=luxury&sub=bb-men-new" },
                  { id: "bb-men-summer-styles", labelKo: "Summer Styles", href: "/shop?category=luxury&sub=bb-men-summer-styles" },
                  { id: "bb-men-classics", labelKo: "버버리 Classics", href: "/shop?category=luxury&sub=bb-men-classics" },
                ],
              },
              {
                id: "bb-men-coats-jackets",
                labelKo: "Coats & Jackets",
                href: "/shop?category=luxury&sub=bb-men-coats-jackets",
                children: [
                  { id: "bb-men-coats", labelKo: "Coats", href: "/shop?category=luxury&sub=bb-men-coats" },
                  { id: "bb-men-jackets", labelKo: "Jackets", href: "/shop?category=luxury&sub=bb-men-jackets" },
                  { id: "bb-men-trench-coats", labelKo: "Trench Coats", href: "/shop?category=luxury&sub=bb-men-trench-coats" },
                  { id: "bb-men-quilted-jackets", labelKo: "Quilted Jackets", href: "/shop?category=luxury&sub=bb-men-quilted-jackets" },
                  { id: "bb-men-puffer-jackets", labelKo: "Puffer Jackets", href: "/shop?category=luxury&sub=bb-men-puffer-jackets" },
                ],
              },
              {
                id: "bb-men-clothes",
                labelKo: "Clothes",
                href: "/shop?category=luxury&sub=bb-men-clothes",
                children: [
                  { id: "bb-men-knitwear", labelKo: "Knitwear", href: "/shop?category=luxury&sub=bb-men-knitwear" },
                  { id: "bb-men-polos", labelKo: "Polos", href: "/shop?category=luxury&sub=bb-men-polos" },
                  { id: "bb-men-tshirts", labelKo: "T-shirts", href: "/shop?category=luxury&sub=bb-men-tshirts" },
                  { id: "bb-men-shirts", labelKo: "Shirts", href: "/shop?category=luxury&sub=bb-men-shirts" },
                  { id: "bb-men-hoodies-sweatshirts", labelKo: "Hoodies & Sweatshirts", href: "/shop?category=luxury&sub=bb-men-hoodies-sweatshirts" },
                  { id: "bb-men-blazers-tailoring", labelKo: "Blazers & Tailoring", href: "/shop?category=luxury&sub=bb-men-blazers-tailoring" },
                  { id: "bb-men-trousers-shorts", labelKo: "Trousers & Shorts", href: "/shop?category=luxury&sub=bb-men-trousers-shorts" },
                  { id: "bb-men-activewear", labelKo: "Activewear", href: "/shop?category=luxury&sub=bb-men-activewear" },
                  { id: "bb-men-denim", labelKo: "Denim", href: "/shop?category=luxury&sub=bb-men-denim" },
                  { id: "bb-men-swimwear", labelKo: "Swimwear", href: "/shop?category=luxury&sub=bb-men-swimwear" },
                ],
              },
            ],
          },
        ],
      },
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
        children: [
          {
            id: "cw-new-releases",
            labelKo: "New Releases",
            href: "/shop?category=watches&sub=cw-new-releases",
          },
          {
            id: "cw-bestsellers",
            labelKo: "Bestsellers",
            href: "/shop?category=watches&sub=cw-bestsellers",
          },
          {
            id: "cw-hidden-gems",
            labelKo: "Hidden Gems",
            href: "/shop?category=watches&sub=cw-hidden-gems",
          },
          {
            id: "cw-clearance",
            labelKo: "Clearance",
            href: "/shop?category=watches&sub=cw-clearance",
          },
          {
            id: "cw-atelier",
            labelKo: "Atelier",
            href: "/shop?category=watches&sub=cw-atelier",
          },
          {
            id: "cw-dive",
            labelKo: "Dive",
            href: "/shop?category=watches&sub=cw-dive",
          },
          {
            id: "cw-integrated-sports",
            labelKo: "Integrated Sports",
            href: "/shop?category=watches&sub=cw-integrated-sports",
          },
          {
            id: "cw-adventure-field",
            labelKo: "Adventure & Field",
            href: "/shop?category=watches&sub=cw-adventure-field",
          },
          {
            id: "cw-military",
            labelKo: "Military",
            href: "/shop?category=watches&sub=cw-military",
          },
          {
            id: "cw-bel-canto",
            labelKo: "Bel Canto",
            href: "/shop?category=watches&sub=cw-bel-canto",
          },
          {
            id: "cw-sealander",
            labelKo: "Sealander",
            href: "/shop?category=watches&sub=cw-sealander",
          },
          {
            id: "cw-twelve",
            labelKo: "Twelve",
            href: "/shop?category=watches&sub=cw-twelve",
          },
          {
            id: "cw-trident",
            labelKo: "Trident",
            href: "/shop?category=watches&sub=cw-trident",
          },
          {
            id: "cw-moonphase",
            labelKo: "Moonphase",
            href: "/shop?category=watches&sub=cw-moonphase",
          },
        ],
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
    children: [
      {
        id: "burberry-bags",
        labelKo: "버버리",
        href: "/shop?category=bags&sub=burberry-bags",
        navLeaf: true,
        children: [
          {
            id: "bb-bags-womens",
            labelKo: "여성용",
            href: "/shop?category=bags&sub=bb-bags-womens",
            children: [
              {
                id: "bb-women-bags",
                labelKo: "Bags",
                href: "/shop?category=bags&sub=bb-women-bags",
                children: [
                  { id: "bb-women-mini-bags", labelKo: "Mini Bags", href: "/shop?category=bags&sub=bb-women-mini-bags" },
                  { id: "bb-women-tote-bags", labelKo: "Tote Bags", href: "/shop?category=bags&sub=bb-women-tote-bags" },
                  { id: "bb-women-crossbody-bags", labelKo: "Crossbody Bags", href: "/shop?category=bags&sub=bb-women-crossbody-bags" },
                  { id: "bb-women-shoulder-bags", labelKo: "Shoulder Bags", href: "/shop?category=bags&sub=bb-women-shoulder-bags" },
                  { id: "bb-women-top-handle-bags", labelKo: "Top Handle Bags", href: "/shop?category=bags&sub=bb-women-top-handle-bags" },
                  { id: "bb-women-backpacks", labelKo: "Backpacks", href: "/shop?category=bags&sub=bb-women-backpacks" },
                ],
              },
            ],
          },
          {
            id: "bb-bags-mens",
            labelKo: "남성용",
            href: "/shop?category=bags&sub=bb-bags-mens",
            children: [
              {
                id: "bb-men-bags",
                labelKo: "Bags",
                href: "/shop?category=bags&sub=bb-men-bags",
                children: [
                  { id: "bb-men-crossbody-bags", labelKo: "Crossbody Bags", href: "/shop?category=bags&sub=bb-men-crossbody-bags" },
                  { id: "bb-men-backpacks", labelKo: "Backpacks", href: "/shop?category=bags&sub=bb-men-backpacks" },
                  { id: "bb-men-belt-bags", labelKo: "Belt Bags", href: "/shop?category=bags&sub=bb-men-belt-bags" },
                  { id: "bb-men-tote-bags", labelKo: "Tote Bags", href: "/shop?category=bags&sub=bb-men-tote-bags" },
                  { id: "bb-men-holdall-bags", labelKo: "Holdall Bags", href: "/shop?category=bags&sub=bb-men-holdall-bags" },
                  { id: "bb-men-briefcases", labelKo: "Briefcases", href: "/shop?category=bags&sub=bb-men-briefcases" },
                ],
              },
            ],
          },
        ],
      },
    ],
  },
  {
    id: "shoes",
    labelKo: "슈즈",
    href: "/shop?category=shoes",
    children: [
      {
        id: "burberry-shoes",
        labelKo: "버버리",
        href: "/shop?category=shoes&sub=burberry-shoes",
        navLeaf: true,
        children: [
          {
            id: "bb-shoes-womens",
            labelKo: "여성용",
            href: "/shop?category=shoes&sub=bb-shoes-womens",
            children: [
              {
                id: "bb-women-shoes",
                labelKo: "Shoes",
                href: "/shop?category=shoes&sub=bb-women-shoes",
                children: [
                  { id: "bb-women-sneakers", labelKo: "Sneakers", href: "/shop?category=shoes&sub=bb-women-sneakers" },
                  { id: "bb-women-sandals", labelKo: "Sandals", href: "/shop?category=shoes&sub=bb-women-sandals" },
                  { id: "bb-women-loafers-ballerinas", labelKo: "Loafers & Ballerinas", href: "/shop?category=shoes&sub=bb-women-loafers-ballerinas" },
                  { id: "bb-women-boots", labelKo: "Boots", href: "/shop?category=shoes&sub=bb-women-boots" },
                  { id: "bb-women-pumps", labelKo: "Pumps", href: "/shop?category=shoes&sub=bb-women-pumps" },
                ],
              },
            ],
          },
          {
            id: "bb-shoes-mens",
            labelKo: "남성용",
            href: "/shop?category=shoes&sub=bb-shoes-mens",
            children: [
              {
                id: "bb-men-shoes",
                labelKo: "Shoes",
                href: "/shop?category=shoes&sub=bb-men-shoes",
                children: [
                  { id: "bb-men-sneakers", labelKo: "Sneakers", href: "/shop?category=shoes&sub=bb-men-sneakers" },
                  { id: "bb-men-sandals", labelKo: "Sandals", href: "/shop?category=shoes&sub=bb-men-sandals" },
                  { id: "bb-men-boots", labelKo: "Boots", href: "/shop?category=shoes&sub=bb-men-boots" },
                  { id: "bb-men-loafers-lace-ups", labelKo: "Loafers & Lace-ups", href: "/shop?category=shoes&sub=bb-men-loafers-lace-ups" },
                ],
              },
            ],
          },
        ],
      },
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
      {
        id: "burberry-accessories",
        labelKo: "버버리",
        href: "/shop?category=accessories&sub=burberry-accessories",
        navLeaf: true,
        children: [
          {
            id: "bb-accessories-womens",
            labelKo: "여성용",
            href: "/shop?category=accessories&sub=bb-accessories-womens",
            children: [
              {
                id: "bb-women-accessories",
                labelKo: "Accessories",
                href: "/shop?category=accessories&sub=bb-women-accessories",
                children: [
                  { id: "bb-women-scarves", labelKo: "Scarves", href: "/shop?category=accessories&sub=bb-women-scarves" },
                  { id: "bb-women-belts", labelKo: "Belts", href: "/shop?category=accessories&sub=bb-women-belts" },
                  { id: "bb-women-sunglasses", labelKo: "Sunglasses", href: "/shop?category=accessories&sub=bb-women-sunglasses" },
                  { id: "bb-women-caps-hats", labelKo: "Caps & Bucket Hats", href: "/shop?category=accessories&sub=bb-women-caps-hats" },
                  { id: "bb-women-umbrellas", labelKo: "Umbrellas", href: "/shop?category=accessories&sub=bb-women-umbrellas" },
                  { id: "bb-women-jewellery", labelKo: "Jewellery", href: "/shop?category=accessories&sub=bb-women-jewellery" },
                  { id: "bb-women-home", labelKo: "Home", href: "/shop?category=accessories&sub=bb-women-home" },
                  { id: "bb-women-socks-tights", labelKo: "Socks & Tights", href: "/shop?category=accessories&sub=bb-women-socks-tights" },
                  { id: "bb-women-tech-travel", labelKo: "Tech & Travel", href: "/shop?category=accessories&sub=bb-women-tech-travel" },
                  { id: "bb-women-key-charms", labelKo: "Key & Bag Charms", href: "/shop?category=accessories&sub=bb-women-key-charms" },
                ],
              },
              {
                id: "bb-women-wallets",
                labelKo: "Wallets & Card Cases",
                href: "/shop?category=accessories&sub=bb-women-wallets",
                children: [
                  { id: "bb-women-card-cases", labelKo: "Card Cases", href: "/shop?category=accessories&sub=bb-women-card-cases" },
                  { id: "bb-women-long-wallets", labelKo: "Long Wallets", href: "/shop?category=accessories&sub=bb-women-long-wallets" },
                  { id: "bb-women-compact-wallets", labelKo: "Compact Wallets", href: "/shop?category=accessories&sub=bb-women-compact-wallets" },
                  { id: "bb-women-chain-strap-wallets", labelKo: "Chain Strap Wallets", href: "/shop?category=accessories&sub=bb-women-chain-strap-wallets" },
                ],
              },
              {
                id: "bb-women-gifts",
                labelKo: "Gifts",
                href: "/shop?category=accessories&sub=bb-women-gifts",
                children: [
                  { id: "bb-women-fragrance", labelKo: "Fragrance", href: "/shop?category=accessories&sub=bb-women-fragrance" },
                  { id: "bb-women-personalised-gifts", labelKo: "Personalised Gifts", href: "/shop?category=accessories&sub=bb-women-personalised-gifts" },
                  { id: "bb-women-personalised-scarves", labelKo: "Personalised Scarves", href: "/shop?category=accessories&sub=bb-women-personalised-scarves" },
                ],
              },
            ],
          },
          {
            id: "bb-accessories-mens",
            labelKo: "남성용",
            href: "/shop?category=accessories&sub=bb-accessories-mens",
            children: [
              {
                id: "bb-men-accessories",
                labelKo: "Accessories",
                href: "/shop?category=accessories&sub=bb-men-accessories",
                children: [
                  { id: "bb-men-scarves", labelKo: "Scarves", href: "/shop?category=accessories&sub=bb-men-scarves" },
                  { id: "bb-men-ties-cufflinks", labelKo: "Ties & Cufflinks", href: "/shop?category=accessories&sub=bb-men-ties-cufflinks" },
                  { id: "bb-men-belts", labelKo: "Belts", href: "/shop?category=accessories&sub=bb-men-belts" },
                  { id: "bb-men-sunglasses", labelKo: "Sunglasses", href: "/shop?category=accessories&sub=bb-men-sunglasses" },
                  { id: "bb-men-caps-hats", labelKo: "Caps & Bucket Hats", href: "/shop?category=accessories&sub=bb-men-caps-hats" },
                  { id: "bb-men-umbrellas", labelKo: "Umbrellas", href: "/shop?category=accessories&sub=bb-men-umbrellas" },
                  { id: "bb-men-jewellery", labelKo: "Jewellery", href: "/shop?category=accessories&sub=bb-men-jewellery" },
                  { id: "bb-men-socks", labelKo: "Socks", href: "/shop?category=accessories&sub=bb-men-socks" },
                  { id: "bb-men-tech-travel", labelKo: "Tech & Travel", href: "/shop?category=accessories&sub=bb-men-tech-travel" },
                  { id: "bb-men-home", labelKo: "Home", href: "/shop?category=accessories&sub=bb-men-home" },
                  { id: "bb-men-key-charms", labelKo: "Key & Bag Charms", href: "/shop?category=accessories&sub=bb-men-key-charms" },
                ],
              },
              {
                id: "bb-men-wallets",
                labelKo: "Wallets & Card Cases",
                href: "/shop?category=accessories&sub=bb-men-wallets",
                children: [
                  { id: "bb-men-bifold-wallets", labelKo: "Bifold Wallets", href: "/shop?category=accessories&sub=bb-men-bifold-wallets" },
                  { id: "bb-men-card-cases", labelKo: "Card Cases", href: "/shop?category=accessories&sub=bb-men-card-cases" },
                  { id: "bb-men-long-wallets", labelKo: "Long Wallets", href: "/shop?category=accessories&sub=bb-men-long-wallets" },
                  { id: "bb-men-pouches", labelKo: "Pouches", href: "/shop?category=accessories&sub=bb-men-pouches" },
                ],
              },
              {
                id: "bb-men-gifts",
                labelKo: "Gifts",
                href: "/shop?category=accessories&sub=bb-men-gifts",
                children: [
                  { id: "bb-men-fragrance", labelKo: "Fragrance", href: "/shop?category=accessories&sub=bb-men-fragrance" },
                  { id: "bb-men-personalised-gifts", labelKo: "Personalised Gifts", href: "/shop?category=accessories&sub=bb-men-personalised-gifts" },
                  { id: "bb-men-personalised-scarves", labelKo: "Personalised Scarves", href: "/shop?category=accessories&sub=bb-men-personalised-scarves" },
                ],
              },
            ],
          },
        ],
      },
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
      {
        id: "golf",
        labelKo: "골프",
        href: "/shop?category=sports&sub=golf",
        children: [
          {
            id: "galvin-green",
            labelKo: "Galvin Green",
            href: "/shop?category=sports&sub=galvin-green",
            navLeaf: true,
            children: [
              {
                id: "gg-new-arrivals",
                labelKo: "New Arrivals",
                href: "/shop?category=sports&sub=gg-new-arrivals",
                children: [
                  {
                    id: "gg-new-men",
                    labelKo: "Men",
                    href: "/shop?category=sports&sub=gg-new-men",
                  },
                  {
                    id: "gg-new-women",
                    labelKo: "Women",
                    href: "/shop?category=sports&sub=gg-new-women",
                  },
                ],
              },
              {
                id: "gg-bestsellers",
                labelKo: "Bestsellers",
                href: "/shop?category=sports&sub=gg-bestsellers",
                children: [
                  {
                    id: "gg-bestsellers-men",
                    labelKo: "Men",
                    href: "/shop?category=sports&sub=gg-bestsellers-men",
                  },
                  {
                    id: "gg-bestsellers-women",
                    labelKo: "Women",
                    href: "/shop?category=sports&sub=gg-bestsellers-women",
                  },
                ],
              },
              {
                id: "gg-men",
                labelKo: "Men",
                href: "/shop?category=sports&sub=gg-men",
              },
              {
                id: "gg-women",
                labelKo: "Women",
                href: "/shop?category=sports&sub=gg-women",
              },
              {
                id: "gg-accessories",
                labelKo: "악세서리",
                href: "/shop?category=sports&sub=gg-accessories",
              },
              {
                id: "gg-sale",
                labelKo: "Sale",
                href: "/shop?category=sports&sub=gg-sale",
              },
            ],
          },
        ],
      },
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

/** Path from a category's top children down to `subId` (inclusive). */
export function findNavPath(
  children: NavChild[] | undefined,
  subId: string,
): NavChild[] | undefined {
  if (!children?.length) return undefined;
  for (const child of children) {
    if (child.id === subId) return [child];
    const rest = findNavPath(child.children, subId);
    if (rest) return [child, ...rest];
  }
  return undefined;
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
