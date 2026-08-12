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
  | "bb-trench"
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
  | "bb-bags-collections"
  | "bb-bags-collections-check"
  | "bb-bags-collections-check-men"
  | "bb-bags-collections-cotswolds"
  | "bb-bags-collections-highlands"
  | "bb-bags-collections-horseshoe"
  | "bb-bags-collections-bloomsbury"
  | "bb-bags-collections-b-clip"
  | "bb-bags-collections-margate"
  | "burberry-shoes"
  | "arcteryx-shoes"
  | "ax-shoes-womens"
  | "ax-shoes-mens"
  | "arcteryx"
  | "ax-womens"
  | "ax-mens"
  | "ax-outlet"
  | "ax-outlet-womens"
  | "ax-outlet-mens"
  | "arcteryx-accessories"
  | "ax-acc-womens"
  | "ax-acc-mens"
  | "umbrellas"
  | "london-undercover"
  | "lu-auto-compact"
  | "lu-telescopic"
  | "lu-full-length"
  | "lu-lifestyle"
  | "arcteryx-bags"
  | "ax-bags-womens"
  | "ax-bags-mens"
  | "bb-shoes-womens"
  | "bb-women-shoes"
  | "bb-women-sneakers"
  | "bb-women-sandals"
  | "bb-women-loafers-ballerinas"
  | "bb-women-boots"
  | "bb-women-pumps"
  | "burberry-accessories"
  | "bb-scarves"
  | "bb-scarves-women"
  | "bb-scarves-women-cashmere"
  | "bb-scarves-women-wool"
  | "bb-scarves-women-silk"
  | "bb-scarves-women-lightweight"
  | "bb-scarves-women-personalised"
  | "bb-scarves-men"
  | "bb-scarves-men-cashmere"
  | "bb-scarves-men-wool"
  | "bb-scarves-men-lightweight"
  | "bb-scarves-men-personalised"
  | "bb-scarves-kids"
  | "bb-scarves-kids-girls"
  | "bb-scarves-kids-boys"
  | "bb-beauty"
  | "bb-beauty-makeup"
  | "bb-beauty-makeup-face"
  | "bb-beauty-makeup-lips"
  | "bb-beauty-makeup-eyes"
  | "bb-beauty-fragrances"
  | "bb-beauty-fragrances-women"
  | "bb-beauty-fragrances-men"
  | "bb-beauty-fragrances-signatures"
  | "bb-beauty-fragrances-signatures-men"
  | "bb-beauty-fragrances-goddess"
  | "bb-beauty-fragrances-her"
  | "bb-beauty-fragrances-hero"
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
  | "bb-men-personalised-scarves"
  | "bb-kids"
  | "bb-kids-latest"
  | "bb-kids-new"
  | "bb-kids-back-to-school"
  | "bb-kids-summer-styles"
  | "bb-kids-classics"
  | "bb-kids-newborn"
  | "bb-kids-newborn-onesies-dresses"
  | "bb-kids-newborn-shoes-accessories"
  | "bb-kids-baby"
  | "bb-kids-baby-coats-jackets"
  | "bb-kids-baby-dresses"
  | "bb-kids-baby-tops"
  | "bb-kids-baby-knitwear"
  | "bb-kids-baby-skirts-trousers"
  | "bb-kids-baby-swimwear"
  | "bb-kids-baby-shoes-accessories"
  | "bb-kids-girls"
  | "bb-kids-girls-coats-jackets"
  | "bb-kids-girls-dresses"
  | "bb-kids-girls-tops"
  | "bb-kids-girls-hoodies-sweatshirts"
  | "bb-kids-girls-knitwear"
  | "bb-kids-girls-skirts-trousers"
  | "bb-kids-girls-swimwear"
  | "bb-kids-girls-scarves"
  | "bb-kids-girls-shoes-accessories"
  | "bb-kids-boys"
  | "bb-kids-boys-coats-jackets"
  | "bb-kids-boys-polos-tshirts"
  | "bb-kids-boys-shirts"
  | "bb-kids-boys-knitwear"
  | "bb-kids-boys-hoodies-sweatshirts"
  | "bb-kids-boys-trousers-shorts"
  | "bb-kids-boys-swimwear"
  | "bb-kids-boys-scarves"
  | "bb-kids-boys-shoes-accessories"
  | "bb-bags-kids"
  | "bb-kids-bags"
  | "bb-shoes-kids"
  | "bb-kids-shoes"
  | "bb-accessories-kids"
  | "bb-kids-accessories"
  | "bb-kids-hats-socks"
  | "bb-kids-hair-accessories"
  | "bb-kids-scarves"
  | "bb-kids-gifts"
  | "bb-kids-gift-girls-scarves"
  | "bb-kids-gift-boys-scarves"
  | "bb-kids-newborn-gifts"
  | "bb-kids-newborn-gift-sets"
  | "bb-kids-baby-gifts"
  | "burberry-gifts"
  | "bb-gifts-her"
  | "bb-gifts-her-scarves"
  | "bb-gifts-her-jewellery"
  | "bb-gifts-her-fragrance"
  | "bb-gifts-her-personalised"
  | "bb-gifts-her-personalised-scarves"
  | "bb-gifts-her-classics"
  | "bb-gifts-him"
  | "bb-gifts-him-scarves"
  | "bb-gifts-him-ties-cufflinks"
  | "bb-gifts-him-fragrance"
  | "bb-gifts-him-personalised"
  | "bb-gifts-him-personalised-scarves"
  | "bb-gifts-him-classics"
  | "bb-gifts-children"
  | "bb-gifts-children-girls-scarves"
  | "bb-gifts-children-boys-scarves"
  | "bb-gifts-children-baby"
  | "bb-gifts-children-newborn"
  | "bb-gifts-children-accessories"
  | "bb-gifts-home"
  | "paul-smith"
  | "ps-men"
  | "paul-smith-shoes"
  | "ps-shoes-men"
  | "paul-smith-accessories"
  | "ps-acc-men"
  | "ps-men-all-in-one"
  | "ps-men-coats"
  | "ps-men-dressing-gown"
  | "ps-men-jackets"
  | "ps-men-jeans"
  | "ps-men-knitwear"
  | "ps-men-loungewear"
  | "ps-men-polos"
  | "ps-men-pyjamas"
  | "ps-men-shirts"
  | "ps-men-shorts"
  | "ps-men-suits"
  | "ps-men-sweat-pants"
  | "ps-men-sweatshirts"
  | "ps-men-swimwear"
  | "ps-men-tshirts"
  | "ps-men-trousers"
  | "ps-men-underwear"
  | "ps-men-waistcoats"
  | "ps-men-tailoring"
  | "ps-men-other"
  | "ps-shoes-boots"
  | "ps-shoes-brogues"
  | "ps-shoes-derby"
  | "ps-shoes-espadrilles"
  | "ps-shoes-loafers"
  | "ps-shoes-oxford"
  | "ps-shoes-sandals"
  | "ps-shoes-care"
  | "ps-shoes-slides"
  | "ps-shoes-trainers"
  | "ps-shoes-other"
  | "ps-acc-bags"
  | "ps-acc-belts"
  | "ps-acc-boots"
  | "ps-acc-ceramics"
  | "ps-acc-giftset"
  | "ps-acc-gloves"
  | "ps-acc-hats"
  | "ps-acc-jewellery"
  | "ps-acc-keyrings"
  | "ps-acc-knitwear"
  | "ps-acc-novelty"
  | "ps-acc-pocket-squares"
  | "ps-acc-pyjamas"
  | "ps-acc-scarves"
  | "ps-acc-slg"
  | "ps-acc-socks"
  | "ps-acc-stationery"
  | "ps-acc-swimwear"
  | "ps-acc-ties"
  | "ps-acc-towels"
  | "ps-acc-umbrellas"
  | "ps-acc-underwear"
  | "ps-acc-other"
  | "ps-women"
  | "ps-shoes-women"
  | "ps-acc-women"
  | "ps-gifts"
  | "ps-women-coats"
  | "ps-women-dresses"
  | "ps-women-jackets"
  | "ps-women-jeans"
  | "ps-women-knitwear"
  | "ps-women-loungewear"
  | "ps-women-pyjamas"
  | "ps-women-shirts"
  | "ps-women-shorts"
  | "ps-women-skirts"
  | "ps-women-suits"
  | "ps-women-sweatshirts"
  | "ps-women-swimwear"
  | "ps-women-tshirts"
  | "ps-women-trousers"
  | "ps-women-waistcoats"
  | "ps-women-tailoring"
  | "ps-women-other"
  | "ps-shoes-women-boots"
  | "ps-shoes-women-flats"
  | "ps-shoes-women-loafers"
  | "ps-shoes-women-sandals"
  | "ps-shoes-women-care"
  | "ps-shoes-women-trainers"
  | "ps-shoes-women-other"
  | "ps-acc-women-bags"
  | "ps-acc-women-belts"
  | "ps-acc-women-gloves"
  | "ps-acc-women-hats"
  | "ps-acc-women-jewellery"
  | "ps-acc-women-keyrings"
  | "ps-acc-women-novelty"
  | "ps-acc-women-scarves"
  | "ps-acc-women-slg"
  | "ps-acc-women-socks"
  | "ps-acc-women-stationery"
  | "ps-acc-women-swimwear"
  | "ps-acc-women-towels"
  | "ps-acc-women-umbrellas"
  | "ps-acc-women-other"
  | "ps-gifts-him"
  | "ps-gifts-her"
  | "ps-gifts-homeware"
  | "belstaff"
  | "bs-men"
  | "bs-men-new"
  | "bs-men-outerwear"
  | "bs-men-clothing"
  | "bs-men-icons"
  | "bs-men-motorcycle"
  | "bs-women"
  | "bs-women-new"
  | "bs-women-outerwear"
  | "bs-women-clothing"
  | "bs-women-icons"
  | "bs-women-motorcycle"
  | "bs-sale"
  | "bs-sale-men"
  | "bs-sale-women"
  | "belstaff-shoes"
  | "bs-shoes-men"
  | "bs-shoes-women"
  | "belstaff-bags"
  | "belstaff-accessories"
  | "bs-acc-men"
  | "bs-acc-women"
  | "gucci-bags"
  | "gc-handbags"
  | "gc-women-shoulder-bags"
  | "gc-women-mini-bags"
  | "gc-women-crossbody-bags"
  | "gc-women-tote-bags"
  | "gc-women-top-handle-bags"
  | "gc-women-backpacks-beltbags"
  | "gc-women-clutches-evening"
  | "gc-women-personalised"
  | "gc-mens-handbags"
  | "gc-men-crossbody-messengers"
  | "gc-men-backpacks"
  | "gc-men-tote-bags"
  | "gc-men-small-bags-pouches"
  | "gc-men-belt-slingbags"
  | "gc-men-duffle-bags"
  | "gucci"
  | "gc-women"
  | "gc-women-rtw"
  | "gc-women-knitwear"
  | "gc-women-tops-shirts"
  | "gc-women-tshirts-sweatshirts"
  | "gc-women-dresses"
  | "gc-women-pants-shorts"
  | "gc-women-denim"
  | "gc-women-skirts"
  | "gc-women-swimwear"
  | "gc-women-coats-jackets"
  | "gc-women-outerwear"
  | "gc-women-leather"
  | "gc-women-activewear"
  | "gc-women-cocktail-evening"
  | "gc-men"
  | "gc-men-rtw"
  | "gc-men-tshirts-polos"
  | "gc-men-tracksuit-sweatshirts"
  | "gc-men-shirts"
  | "gc-men-knitwear"
  | "gc-men-denim"
  | "gc-men-trousers-shorts"
  | "gc-men-swimwear"
  | "gc-men-outerwear"
  | "gc-men-leather"
  | "gc-men-formal-wear"
  | "gc-men-coats-jackets"
  | "gucci-shoes"
  | "gc-shoes-womens"
  | "gc-women-shoes"
  | "gc-women-sneakers"
  | "gc-women-moccasins"
  | "gc-women-slippers-mules"
  | "gc-women-sandals"
  | "gc-women-slides"
  | "gc-women-pumps"
  | "gc-women-ballet-flats"
  | "gc-women-boots"
  | "gc-shoes-mens"
  | "gc-men-shoes"
  | "gc-men-sneakers"
  | "gc-men-loafers-moccasins"
  | "gc-men-slides-sandals"
  | "gc-men-driving"
  | "gc-men-lace-ups"
  | "gc-men-boots"
  | "gucci-accessories"
  | "gc-accessories-womens"
  | "gc-accessories-mens"
  | "gc-women-wallets"
  | "gc-women-long-wallets"
  | "gc-women-chain-wallets"
  | "gc-women-compact-wallets"
  | "gc-women-card-holders"
  | "gc-women-bag-charms-keychains"
  | "gc-women-pouches"
  | "gc-women-tech-accessories"
  | "gc-men-wallets"
  | "gc-men-wallets-wallets"
  | "gc-men-wallets-small-bags-pouches"
  | "gc-men-card-coin-cases"
  | "gc-men-keyrings-keycases"
  | "gc-men-tech-accessories"
  | "gc-women-fashion-accessories"
  | "gc-women-belts"
  | "gc-women-scarves-silks"
  | "gc-women-hats-gloves"
  | "gc-women-eyewear"
  | "gc-women-hair-accessories"
  | "gc-women-socks-tights"
  | "gc-men-fashion-accessories"
  | "gc-men-belts"
  | "gc-men-eyewear"
  | "gc-men-hats-gloves"
  | "gc-men-ties"
  | "gc-men-scarves"
  | "gc-men-socks"
  | "gc-men-bag-charms-keychains"
  | "gc-women-travel"
  | "gc-women-trolley"
  | "gc-women-weekend-duffle"
  | "gc-women-travel-accessories"
  | "gc-women-hard-shell-luggage"
  | "gc-men-travel"
  | "gc-men-trolley"
  | "gc-men-weekend-duffle"
  | "gc-men-travel-accessories"
  | "gc-men-hard-shell-luggage"
  | "gc-men-jewellery"
  | "gc-men-fashion-jewellery"
  | "gc-jewellery-watches"
  | "gc-gold-jewellery"
  | "gc-gold-jewellery-women"
  | "gc-gold-jewellery-men"
  | "gc-silver-jewellery"
  | "gc-silver-jewellery-women"
  | "gc-silver-jewellery-men"
  | "gc-fashion-jewellery"
  | "gc-watches"
  | "gc-watches-women"
  | "gc-watches-men"
  | "gc-gifts"
  | "gc-gifts-her"
  | "gc-gifts-him"
  | "gc-gifts-personalised"
  | "gc-gifts-beauty"
  | "gc-gifts-jewellery"
  | "gc-gifts-children"
  | "gc-men-gifts"
  | "gc-men-gifts-bags"
  | "gc-men-gifts-belts"
  | "gc-men-gifts-jewellery-watches"
  | "gc-men-gifts-shoes"
  | "gc-men-gifts-small-accessories"
  | "gc-men-gifts-small-leathergoods"
  | "gc-men-gifts-sunglasses"
  | "gc-men-gifts-watches"
  | "gc-men-gifts-personalised"
  | "chanel"
  | "ch-women"
  | "ch-women-rtw"
  | "ch-women-looks"
  | "ch-women-jackets"
  | "ch-women-dresses"
  | "ch-women-blouses-tops"
  | "ch-women-cardigans-sweaters"
  | "ch-women-skirts"
  | "ch-women-trousers-shorts"
  | "ch-women-swimwear"
  | "ch-women-outerwear"
  | "chanel-bags"
  | "ch-handbags"
  | "ch-women-flap-bags"
  | "ch-women-hobo-bags"
  | "ch-women-tote-bowling-bags"
  | "ch-women-bucket-bags"
  | "ch-women-backpacks"
  | "ch-women-evening-bags"
  | "ch-women-mini-bags"
  | "ch-the-chanel-handbag"
  | "ch-slg"
  | "ch-women-wallets-on-chain"
  | "ch-women-micro-bags"
  | "ch-women-vanity"
  | "ch-women-card-holders-wallets"
  | "ch-women-pouches-cases"
  | "ch-women-leather-accessories"
  | "chanel-shoes"
  | "ch-shoes"
  | "ch-women-pumps-slingbacks"
  | "ch-women-ballet-mary-janes"
  | "ch-women-elegant-sandals"
  | "ch-women-casual-sandals"
  | "ch-women-loafers"
  | "ch-women-boots"
  | "ch-women-sneakers"
  | "chanel-accessories"
  | "ch-jewellery"
  | "ch-women-earrings"
  | "ch-women-necklaces"
  | "ch-women-bracelets-cuffs"
  | "ch-women-brooches"
  | "ch-women-rings";

/** Chanel Ready-to-Wear official GB fashion leaves. */
export const CH_WOMEN_RTW_LEAF_IDS: SubcategoryId[] = [
  "ch-women-looks",
  "ch-women-jackets",
  "ch-women-dresses",
  "ch-women-blouses-tops",
  "ch-women-cardigans-sweaters",
  "ch-women-skirts",
  "ch-women-trousers-shorts",
  "ch-women-swimwear",
  "ch-women-outerwear",
];

/** Chanel handbags leaf collections (official GB handbag PLPs). */
export const CH_HANDBAG_LEAF_IDS: SubcategoryId[] = [
  "ch-women-flap-bags",
  "ch-women-hobo-bags",
  "ch-women-tote-bowling-bags",
  "ch-women-bucket-bags",
  "ch-women-backpacks",
  "ch-women-evening-bags",
  "ch-women-mini-bags",
  "ch-the-chanel-handbag",
];

/** Chanel small leather goods leaves (official GB SLG PLPs). */
export const CH_SLG_LEAF_IDS: SubcategoryId[] = [
  "ch-women-wallets-on-chain",
  "ch-women-micro-bags",
  "ch-women-vanity",
  "ch-women-card-holders-wallets",
  "ch-women-pouches-cases",
  "ch-women-leather-accessories",
];

/** Chanel women's shoes leaves (official GB shoes PLPs). */
export const CH_SHOE_LEAF_IDS: SubcategoryId[] = [
  "ch-women-pumps-slingbacks",
  "ch-women-ballet-mary-janes",
  "ch-women-elegant-sandals",
  "ch-women-casual-sandals",
  "ch-women-loafers",
  "ch-women-boots",
  "ch-women-sneakers",
];

/** Chanel costume jewellery leaves (official GB costume jewellery PLPs). */
export const CH_JEWELLERY_LEAF_IDS: SubcategoryId[] = [
  "ch-women-earrings",
  "ch-women-necklaces",
  "ch-women-bracelets-cuffs",
  "ch-women-brooches",
  "ch-women-rings",
];

/** Gucci Handbags leaf collections (official UK handbag PLPs). */
export const GC_HANDBAG_LEAF_IDS: SubcategoryId[] = [
  "gc-women-shoulder-bags",
  "gc-women-mini-bags",
  "gc-women-crossbody-bags",
  "gc-women-tote-bags",
  "gc-women-top-handle-bags",
  "gc-women-backpacks-beltbags",
  "gc-women-clutches-evening",
  "gc-women-personalised",
];

/** Gucci men's bags leaf collections (official UK men bags PLPs). */
export const GC_MENS_HANDBAG_LEAF_IDS: SubcategoryId[] = [
  "gc-men-crossbody-messengers",
  "gc-men-backpacks",
  "gc-men-tote-bags",
  "gc-men-small-bags-pouches",
  "gc-men-belt-slingbags",
  "gc-men-duffle-bags",
];

/** Gucci women's ready-to-wear Clothing leaves (official UK RTW PLPs). */
export const GC_WOMEN_RTW_LEAF_IDS: SubcategoryId[] = [
  "gc-women-knitwear",
  "gc-women-tops-shirts",
  "gc-women-tshirts-sweatshirts",
  "gc-women-dresses",
  "gc-women-pants-shorts",
  "gc-women-denim",
  "gc-women-skirts",
  "gc-women-swimwear",
  "gc-women-coats-jackets",
  "gc-women-outerwear",
  "gc-women-leather",
  "gc-women-activewear",
  "gc-women-cocktail-evening",
];

/** Gucci men's ready-to-wear Clothing leaves (official UK men RTW PLPs). */
export const GC_MEN_RTW_LEAF_IDS: SubcategoryId[] = [
  "gc-men-tshirts-polos",
  "gc-men-tracksuit-sweatshirts",
  "gc-men-shirts",
  "gc-men-knitwear",
  "gc-men-denim",
  "gc-men-trousers-shorts",
  "gc-men-swimwear",
  "gc-men-outerwear",
  "gc-men-leather",
  "gc-men-formal-wear",
  "gc-men-coats-jackets",
];

/** Gucci women's shoes leaves (official UK women shoes PLPs). */
export const GC_WOMEN_SHOE_LEAF_IDS: SubcategoryId[] = [
  "gc-women-sneakers",
  "gc-women-moccasins",
  "gc-women-slippers-mules",
  "gc-women-sandals",
  "gc-women-slides",
  "gc-women-pumps",
  "gc-women-ballet-flats",
  "gc-women-boots",
];

/** Gucci men's shoes leaves (official UK men shoes PLPs). */
export const GC_MEN_SHOE_LEAF_IDS: SubcategoryId[] = [
  "gc-men-sneakers",
  "gc-men-loafers-moccasins",
  "gc-men-slides-sandals",
  "gc-men-driving",
  "gc-men-lace-ups",
  "gc-men-boots",
];

/** Gucci women's wallets & small accessories leaves (official UK PLPs). */
export const GC_WOMEN_WALLET_LEAF_IDS: SubcategoryId[] = [
  "gc-women-long-wallets",
  "gc-women-chain-wallets",
  "gc-women-compact-wallets",
  "gc-women-card-holders",
  "gc-women-bag-charms-keychains",
  "gc-women-pouches",
  "gc-women-tech-accessories",
];

/** Gucci men's wallets & small accessories leaves (official UK PLPs). */
export const GC_MEN_WALLET_LEAF_IDS: SubcategoryId[] = [
  "gc-men-wallets-wallets",
  "gc-men-wallets-small-bags-pouches",
  "gc-men-card-coin-cases",
  "gc-men-keyrings-keycases",
  "gc-men-tech-accessories",
];

/** Gucci women's fashion accessories leaves (official UK soft-accessory PLPs).
 * Bag charms reuse `gc-women-bag-charms-keychains` under wallets nav — not listed here.
 */
export const GC_WOMEN_FASHION_ACCESSORY_LEAF_IDS: SubcategoryId[] = [
  "gc-women-belts",
  "gc-women-scarves-silks",
  "gc-women-hats-gloves",
  "gc-women-eyewear",
  "gc-women-hair-accessories",
  "gc-women-socks-tights",
];

/** Gucci men's fashion accessories leaves (official UK soft-accessory PLPs). */
export const GC_MEN_FASHION_ACCESSORY_LEAF_IDS: SubcategoryId[] = [
  "gc-men-belts",
  "gc-men-eyewear",
  "gc-men-hats-gloves",
  "gc-men-ties",
  "gc-men-scarves",
  "gc-men-socks",
  "gc-men-bag-charms-keychains",
];

/** Gucci women's travel bags leaves (official UK travel PLPs). */
export const GC_WOMEN_TRAVEL_LEAF_IDS: SubcategoryId[] = [
  "gc-women-trolley",
  "gc-women-weekend-duffle",
  "gc-women-travel-accessories",
  "gc-women-hard-shell-luggage",
];

/** Gucci men's travel bags leaves (official UK men travel PLPs). */
export const GC_MEN_TRAVEL_LEAF_IDS: SubcategoryId[] = [
  "gc-men-trolley",
  "gc-men-weekend-duffle",
  "gc-men-travel-accessories",
  "gc-men-hard-shell-luggage",
];

/** Men's accessories → 쥬얼리 leaves (reuse hub gold/silver men; fashion men split). */
export const GC_MEN_JEWELLERY_LEAF_IDS: SubcategoryId[] = [
  "gc-gold-jewellery-men",
  "gc-silver-jewellery-men",
  "gc-men-fashion-jewellery",
];

/** Gucci jewellery & watches hub leaves (official UK jewellery-watches PLPs). */
export const GC_JEWELLERY_LEAF_IDS: SubcategoryId[] = [
  "gc-gold-jewellery-women",
  "gc-gold-jewellery-men",
  "gc-silver-jewellery-women",
  "gc-silver-jewellery-men",
  "gc-fashion-jewellery",
  "gc-men-fashion-jewellery",
  "gc-watches-women",
  "gc-watches-men",
];

export const GC_GOLD_JEWELLERY_LEAF_IDS: SubcategoryId[] = [
  "gc-gold-jewellery-women",
  "gc-gold-jewellery-men",
];

export const GC_SILVER_JEWELLERY_LEAF_IDS: SubcategoryId[] = [
  "gc-silver-jewellery-women",
  "gc-silver-jewellery-men",
];

export const GC_WATCHES_LEAF_IDS: SubcategoryId[] = [
  "gc-watches-women",
  "gc-watches-men",
];

/** Gucci gifts leaves (official UK gifts hub PLPs). */
export const GC_GIFTS_LEAF_IDS: SubcategoryId[] = [
  "gc-gifts-her",
  "gc-gifts-him",
  "gc-gifts-personalised",
  "gc-gifts-beauty",
  "gc-gifts-jewellery",
  "gc-gifts-children",
];

/** Gucci men's accessories → 선물용 leaves (gifts-for-him Category filters). */
export const GC_MEN_GIFTS_LEAF_IDS: SubcategoryId[] = [
  "gc-men-gifts-bags",
  "gc-men-gifts-belts",
  "gc-men-gifts-jewellery-watches",
  "gc-men-gifts-shoes",
  "gc-men-gifts-small-accessories",
  "gc-men-gifts-small-leathergoods",
  "gc-men-gifts-sunglasses",
  "gc-men-gifts-watches",
  "gc-men-gifts-personalised",
];


export const BS_MEN_CLOTHING_IDS: SubcategoryId[] = [
  "bs-men-new",
  "bs-men-outerwear",
  "bs-men-clothing",
  "bs-men-icons",
  "bs-men-motorcycle",
];

export const BS_WOMEN_CLOTHING_IDS: SubcategoryId[] = [
  "bs-women-new",
  "bs-women-outerwear",
  "bs-women-clothing",
  "bs-women-icons",
  "bs-women-motorcycle",
];

export const BS_SALE_IDS: SubcategoryId[] = ["bs-sale-men", "bs-sale-women"];

export const BS_MEN_SHOE_IDS: SubcategoryId[] = ["bs-shoes-men"];
export const BS_WOMEN_SHOE_IDS: SubcategoryId[] = ["bs-shoes-women"];

export const BS_MEN_ACC_IDS: SubcategoryId[] = ["bs-acc-men"];
export const BS_WOMEN_ACC_IDS: SubcategoryId[] = ["bs-acc-women"];

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

/** Burberry Bags → Collections (from /c/bags/). Check includes women + men PLPs. */
export const BB_BAGS_COLLECTION_LEAF_IDS: SubcategoryId[] = [
  "bb-bags-collections-check",
  "bb-bags-collections-check-men",
  "bb-bags-collections-cotswolds",
  "bb-bags-collections-highlands",
  "bb-bags-collections-horseshoe",
  "bb-bags-collections-bloomsbury",
  "bb-bags-collections-b-clip",
  "bb-bags-collections-margate",
];

export const BB_BAGS_COLLECTION_NAV_IDS: SubcategoryId[] = [
  "bb-bags-collections-check",
  "bb-bags-collections-cotswolds",
  "bb-bags-collections-highlands",
  "bb-bags-collections-horseshoe",
  "bb-bags-collections-bloomsbury",
  "bb-bags-collections-b-clip",
  "bb-bags-collections-margate",
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

/** Signature Burberry trench coats — luxury → 버버리 → 트렌치. */
export const BB_TRENCH_IDS: SubcategoryId[] = [
  "bb-women-trench-coats",
  "bb-men-trench-coats",
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

export const BB_KIDS_LATEST_IDS: SubcategoryId[] = [
  "bb-kids-new",
  "bb-kids-back-to-school",
  "bb-kids-summer-styles",
  "bb-kids-classics",
];

export const BB_KIDS_NEWBORN_IDS: SubcategoryId[] = [
  "bb-kids-newborn",
  "bb-kids-newborn-onesies-dresses",
  "bb-kids-newborn-shoes-accessories",
];

export const BB_KIDS_NEWBORN_APPAREL_IDS: SubcategoryId[] = [
  "bb-kids-newborn",
  "bb-kids-newborn-onesies-dresses",
];

export const BB_KIDS_BABY_IDS: SubcategoryId[] = [
  "bb-kids-baby",
  "bb-kids-baby-coats-jackets",
  "bb-kids-baby-dresses",
  "bb-kids-baby-tops",
  "bb-kids-baby-knitwear",
  "bb-kids-baby-skirts-trousers",
  "bb-kids-baby-swimwear",
  "bb-kids-baby-shoes-accessories",
];

export const BB_KIDS_BABY_APPAREL_IDS: SubcategoryId[] = [
  "bb-kids-baby",
  "bb-kids-baby-coats-jackets",
  "bb-kids-baby-dresses",
  "bb-kids-baby-tops",
  "bb-kids-baby-knitwear",
  "bb-kids-baby-skirts-trousers",
  "bb-kids-baby-swimwear",
];

export const BB_KIDS_GIRLS_IDS: SubcategoryId[] = [
  "bb-kids-girls",
  "bb-kids-girls-coats-jackets",
  "bb-kids-girls-dresses",
  "bb-kids-girls-tops",
  "bb-kids-girls-hoodies-sweatshirts",
  "bb-kids-girls-knitwear",
  "bb-kids-girls-skirts-trousers",
  "bb-kids-girls-swimwear",
  "bb-kids-girls-scarves",
  "bb-kids-girls-shoes-accessories",
];

export const BB_KIDS_GIRLS_APPAREL_IDS: SubcategoryId[] = [
  "bb-kids-girls",
  "bb-kids-girls-coats-jackets",
  "bb-kids-girls-dresses",
  "bb-kids-girls-tops",
  "bb-kids-girls-hoodies-sweatshirts",
  "bb-kids-girls-knitwear",
  "bb-kids-girls-skirts-trousers",
  "bb-kids-girls-swimwear",
  "bb-kids-girls-scarves",
];

export const BB_KIDS_BOYS_IDS: SubcategoryId[] = [
  "bb-kids-boys",
  "bb-kids-boys-coats-jackets",
  "bb-kids-boys-polos-tshirts",
  "bb-kids-boys-shirts",
  "bb-kids-boys-knitwear",
  "bb-kids-boys-hoodies-sweatshirts",
  "bb-kids-boys-trousers-shorts",
  "bb-kids-boys-swimwear",
  "bb-kids-boys-scarves",
  "bb-kids-boys-shoes-accessories",
];

export const BB_KIDS_BOYS_APPAREL_IDS: SubcategoryId[] = [
  "bb-kids-boys",
  "bb-kids-boys-coats-jackets",
  "bb-kids-boys-polos-tshirts",
  "bb-kids-boys-shirts",
  "bb-kids-boys-knitwear",
  "bb-kids-boys-hoodies-sweatshirts",
  "bb-kids-boys-trousers-shorts",
  "bb-kids-boys-swimwear",
  "bb-kids-boys-scarves",
];

export const BB_KIDS_BAG_IDS: SubcategoryId[] = ["bb-kids-bags"];

export const BB_KIDS_SHOE_IDS: SubcategoryId[] = [
  "bb-kids-shoes",
  "bb-kids-newborn-shoes-accessories",
  "bb-kids-baby-shoes-accessories",
  "bb-kids-girls-shoes-accessories",
  "bb-kids-boys-shoes-accessories",
];

export const BB_KIDS_ACCESSORY_LEAF_IDS: SubcategoryId[] = [
  "bb-kids-hats-socks",
  "bb-kids-hair-accessories",
  "bb-kids-scarves",
  "bb-kids-girls-scarves",
  "bb-kids-boys-scarves",
];

export const BB_KIDS_GIFT_IDS: SubcategoryId[] = [
  "bb-kids-gifts",
  "bb-kids-gift-girls-scarves",
  "bb-kids-gift-boys-scarves",
  "bb-kids-newborn-gifts",
  "bb-kids-newborn-gift-sets",
  "bb-kids-baby-gifts",
];

/** Burberry Kids leaf collection ids used for PLP membership. */
export const BB_KIDS_COLLECTION_IDS: SubcategoryId[] = [
  ...BB_KIDS_LATEST_IDS,
  ...BB_KIDS_NEWBORN_IDS,
  ...BB_KIDS_BABY_IDS,
  ...BB_KIDS_GIRLS_IDS,
  ...BB_KIDS_BOYS_IDS,
  ...BB_KIDS_BAG_IDS,
  ...BB_KIDS_SHOE_IDS,
  ...BB_KIDS_ACCESSORY_LEAF_IDS,
  ...BB_KIDS_GIFT_IDS,
];

export const BB_GIFTS_HER_IDS: SubcategoryId[] = [
  "bb-gifts-her",
  "bb-gifts-her-scarves",
  "bb-gifts-her-jewellery",
  "bb-gifts-her-fragrance",
  "bb-gifts-her-personalised",
  "bb-gifts-her-personalised-scarves",
  "bb-gifts-her-classics",
];

export const BB_GIFTS_HIM_IDS: SubcategoryId[] = [
  "bb-gifts-him",
  "bb-gifts-him-scarves",
  "bb-gifts-him-ties-cufflinks",
  "bb-gifts-him-fragrance",
  "bb-gifts-him-personalised",
  "bb-gifts-him-personalised-scarves",
  "bb-gifts-him-classics",
];

export const BB_GIFTS_CHILDREN_IDS: SubcategoryId[] = [
  "bb-gifts-children",
  "bb-gifts-children-girls-scarves",
  "bb-gifts-children-boys-scarves",
  "bb-gifts-children-baby",
  "bb-gifts-children-newborn",
  "bb-gifts-children-accessories",
];

export const BB_GIFTS_HOME_IDS: SubcategoryId[] = ["bb-gifts-home"];

export const BB_SCARVES_WOMEN_IDS: SubcategoryId[] = [
  "bb-scarves-women",
  "bb-scarves-women-cashmere",
  "bb-scarves-women-wool",
  "bb-scarves-women-silk",
  "bb-scarves-women-lightweight",
  "bb-scarves-women-personalised",
];

export const BB_SCARVES_MEN_IDS: SubcategoryId[] = [
  "bb-scarves-men",
  "bb-scarves-men-cashmere",
  "bb-scarves-men-wool",
  "bb-scarves-men-lightweight",
  "bb-scarves-men-personalised",
];

export const BB_SCARVES_KIDS_IDS: SubcategoryId[] = [
  "bb-scarves-kids",
  "bb-scarves-kids-girls",
  "bb-scarves-kids-boys",
];

export const BB_SCARVES_ALL_IDS: SubcategoryId[] = [
  ...BB_SCARVES_WOMEN_IDS,
  ...BB_SCARVES_MEN_IDS,
  ...BB_SCARVES_KIDS_IDS,
];

export const BB_BEAUTY_MAKEUP_IDS: SubcategoryId[] = [
  "bb-beauty-makeup",
  "bb-beauty-makeup-face",
  "bb-beauty-makeup-lips",
  "bb-beauty-makeup-eyes",
];

export const BB_BEAUTY_FRAGRANCE_LEAF_IDS: SubcategoryId[] = [
  "bb-beauty-fragrances",
  "bb-beauty-fragrances-women",
  "bb-beauty-fragrances-men",
  "bb-beauty-fragrances-signatures",
  "bb-beauty-fragrances-signatures-men",
  "bb-beauty-fragrances-goddess",
  "bb-beauty-fragrances-her",
  "bb-beauty-fragrances-hero",
];

export const BB_BEAUTY_ALL_IDS: SubcategoryId[] = [
  ...BB_BEAUTY_MAKEUP_IDS,
  ...BB_BEAUTY_FRAGRANCE_LEAF_IDS,
];

/** Burberry gift-recommendation leaf ids used for PLP membership. */
export const BB_GIFTS_ALL_IDS: SubcategoryId[] = [
  ...BB_GIFTS_HER_IDS,
  ...BB_GIFTS_HIM_IDS,
  ...BB_GIFTS_CHILDREN_IDS,
  ...BB_GIFTS_HOME_IDS,
];

/** All Burberry leaf ids (women + men + kids + gifts) used for PLP membership. */
export const BB_COLLECTION_IDS: SubcategoryId[] = [
  ...BB_WOMEN_COLLECTION_IDS,
  ...BB_MEN_COLLECTION_IDS,
  ...BB_KIDS_COLLECTION_IDS,
  ...BB_GIFTS_ALL_IDS,
  ...BB_SCARVES_ALL_IDS,
  ...BB_BEAUTY_ALL_IDS,
  ...BB_BAGS_COLLECTION_LEAF_IDS,
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

export const BB_LUXURY_KIDS_IDS: SubcategoryId[] = [
  ...BB_KIDS_LATEST_IDS,
  ...BB_KIDS_NEWBORN_APPAREL_IDS,
  ...BB_KIDS_BABY_APPAREL_IDS,
  ...BB_KIDS_GIRLS_APPAREL_IDS,
  ...BB_KIDS_BOYS_APPAREL_IDS,
];


export const PS_MEN_CLOTHING_IDS: SubcategoryId[] = [
  "ps-men-all-in-one",
  "ps-men-coats",
  "ps-men-dressing-gown",
  "ps-men-jackets",
  "ps-men-jeans",
  "ps-men-knitwear",
  "ps-men-loungewear",
  "ps-men-polos",
  "ps-men-pyjamas",
  "ps-men-shirts",
  "ps-men-shorts",
  "ps-men-suits",
  "ps-men-sweat-pants",
  "ps-men-sweatshirts",
  "ps-men-swimwear",
  "ps-men-tshirts",
  "ps-men-trousers",
  "ps-men-underwear",
  "ps-men-waistcoats",
  "ps-men-tailoring",
  "ps-men-other",
];

export const PS_MEN_SHOE_IDS: SubcategoryId[] = [
  "ps-shoes-boots",
  "ps-shoes-brogues",
  "ps-shoes-derby",
  "ps-shoes-espadrilles",
  "ps-shoes-loafers",
  "ps-shoes-oxford",
  "ps-shoes-sandals",
  "ps-shoes-care",
  "ps-shoes-slides",
  "ps-shoes-trainers",
  "ps-shoes-other",
];

export const PS_MEN_ACC_IDS: SubcategoryId[] = [
  "ps-acc-bags",
  "ps-acc-belts",
  "ps-acc-boots",
  "ps-acc-ceramics",
  "ps-acc-giftset",
  "ps-acc-gloves",
  "ps-acc-hats",
  "ps-acc-jewellery",
  "ps-acc-keyrings",
  "ps-acc-knitwear",
  "ps-acc-novelty",
  "ps-acc-pocket-squares",
  "ps-acc-pyjamas",
  "ps-acc-scarves",
  "ps-acc-slg",
  "ps-acc-socks",
  "ps-acc-stationery",
  "ps-acc-swimwear",
  "ps-acc-ties",
  "ps-acc-towels",
  "ps-acc-umbrellas",
  "ps-acc-underwear",
  "ps-acc-other",
];


export const PS_WOMEN_CLOTHING_IDS: SubcategoryId[] = [
  "ps-women-coats",
  "ps-women-dresses",
  "ps-women-jackets",
  "ps-women-jeans",
  "ps-women-knitwear",
  "ps-women-loungewear",
  "ps-women-pyjamas",
  "ps-women-shirts",
  "ps-women-shorts",
  "ps-women-skirts",
  "ps-women-suits",
  "ps-women-sweatshirts",
  "ps-women-swimwear",
  "ps-women-tshirts",
  "ps-women-trousers",
  "ps-women-waistcoats",
  "ps-women-tailoring",
  "ps-women-other",
];

export const PS_WOMEN_SHOE_IDS: SubcategoryId[] = [
  "ps-shoes-women-boots",
  "ps-shoes-women-flats",
  "ps-shoes-women-loafers",
  "ps-shoes-women-sandals",
  "ps-shoes-women-care",
  "ps-shoes-women-trainers",
  "ps-shoes-women-other",
];

export const PS_WOMEN_ACC_IDS: SubcategoryId[] = [
  "ps-acc-women-bags",
  "ps-acc-women-belts",
  "ps-acc-women-gloves",
  "ps-acc-women-hats",
  "ps-acc-women-jewellery",
  "ps-acc-women-keyrings",
  "ps-acc-women-novelty",
  "ps-acc-women-scarves",
  "ps-acc-women-slg",
  "ps-acc-women-socks",
  "ps-acc-women-stationery",
  "ps-acc-women-swimwear",
  "ps-acc-women-towels",
  "ps-acc-women-umbrellas",
  "ps-acc-women-other",
];

export const PS_GIFTS_IDS: SubcategoryId[] = [
  "ps-gifts-him",
  "ps-gifts-her",
  "ps-gifts-homeware",
];

export type NavChild = {
  id: SubcategoryId;
  labelKo: string;
  href: string;
  children?: NavChild[];
  /** When true, shop treats this node as a leaf filter; children still nest in header. */
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

  "paul-smith": ["ps-men", "ps-women", ...PS_MEN_CLOTHING_IDS, ...PS_WOMEN_CLOTHING_IDS],
  "ps-men": [...PS_MEN_CLOTHING_IDS],
  "ps-women": [...PS_WOMEN_CLOTHING_IDS],
  "paul-smith-shoes": ["ps-shoes-men", "ps-shoes-women", ...PS_MEN_SHOE_IDS, ...PS_WOMEN_SHOE_IDS],
  "ps-shoes-men": [...PS_MEN_SHOE_IDS],
  "ps-shoes-women": [...PS_WOMEN_SHOE_IDS],
  "paul-smith-accessories": ["ps-acc-men", "ps-acc-women", "ps-gifts", ...PS_MEN_ACC_IDS, ...PS_WOMEN_ACC_IDS, ...PS_GIFTS_IDS],
  "ps-acc-men": [...PS_MEN_ACC_IDS],
  "ps-acc-women": [...PS_WOMEN_ACC_IDS],
  "ps-gifts": [...PS_GIFTS_IDS],
  belstaff: [
    "bs-men",
    "bs-women",
    "bs-sale",
    ...BS_MEN_CLOTHING_IDS,
    ...BS_WOMEN_CLOTHING_IDS,
    ...BS_SALE_IDS,
  ],
  "bs-men": [...BS_MEN_CLOTHING_IDS],
  "bs-women": [...BS_WOMEN_CLOTHING_IDS],
  "bs-sale": [...BS_SALE_IDS],
  "belstaff-shoes": [...BS_MEN_SHOE_IDS, ...BS_WOMEN_SHOE_IDS],
  "belstaff-bags": ["belstaff-bags"],
  "belstaff-accessories": [...BS_MEN_ACC_IDS, ...BS_WOMEN_ACC_IDS],
  "gucci-bags": [
    "gc-handbags",
    ...GC_HANDBAG_LEAF_IDS,
    "gc-mens-handbags",
    ...GC_MENS_HANDBAG_LEAF_IDS,
  ],
  "gc-handbags": ["gc-handbags", ...GC_HANDBAG_LEAF_IDS],
  "chanel-bags": [
    "chanel-bags",
    "ch-handbags",
    ...CH_HANDBAG_LEAF_IDS,
    "ch-slg",
    ...CH_SLG_LEAF_IDS,
  ],
  "ch-handbags": ["ch-handbags", ...CH_HANDBAG_LEAF_IDS],
  "ch-women-flap-bags": ["ch-women-flap-bags"],
  "ch-women-hobo-bags": ["ch-women-hobo-bags"],
  "ch-women-tote-bowling-bags": ["ch-women-tote-bowling-bags"],
  "ch-women-bucket-bags": ["ch-women-bucket-bags"],
  "ch-women-backpacks": ["ch-women-backpacks"],
  "ch-women-evening-bags": ["ch-women-evening-bags"],
  "ch-women-mini-bags": ["ch-women-mini-bags"],
  "ch-the-chanel-handbag": ["ch-the-chanel-handbag"],
  "ch-slg": ["ch-slg", ...CH_SLG_LEAF_IDS],
  "ch-women-wallets-on-chain": ["ch-women-wallets-on-chain"],
  "ch-women-micro-bags": ["ch-women-micro-bags"],
  "ch-women-vanity": ["ch-women-vanity"],
  "ch-women-card-holders-wallets": ["ch-women-card-holders-wallets"],
  "ch-women-pouches-cases": ["ch-women-pouches-cases"],
  "ch-women-leather-accessories": ["ch-women-leather-accessories"],
  "chanel-shoes": ["chanel-shoes", "ch-shoes", ...CH_SHOE_LEAF_IDS],
  "ch-shoes": ["ch-shoes", ...CH_SHOE_LEAF_IDS],
  "ch-women-pumps-slingbacks": ["ch-women-pumps-slingbacks"],
  "ch-women-ballet-mary-janes": ["ch-women-ballet-mary-janes"],
  "ch-women-elegant-sandals": ["ch-women-elegant-sandals"],
  "ch-women-casual-sandals": ["ch-women-casual-sandals"],
  "ch-women-loafers": ["ch-women-loafers"],
  "ch-women-boots": ["ch-women-boots"],
  "ch-women-sneakers": ["ch-women-sneakers"],
  "chanel-accessories": [
    "chanel-accessories",
    "ch-jewellery",
    ...CH_JEWELLERY_LEAF_IDS,
  ],
  "ch-jewellery": ["ch-jewellery", ...CH_JEWELLERY_LEAF_IDS],
  "ch-women-earrings": ["ch-women-earrings"],
  "ch-women-necklaces": ["ch-women-necklaces"],
  "ch-women-bracelets-cuffs": ["ch-women-bracelets-cuffs"],
  "ch-women-brooches": ["ch-women-brooches"],
  "ch-women-rings": ["ch-women-rings"],
  "gc-mens-handbags": ["gc-mens-handbags", ...GC_MENS_HANDBAG_LEAF_IDS],
  "gc-men-crossbody-messengers": ["gc-men-crossbody-messengers"],
  "gc-men-backpacks": ["gc-men-backpacks"],
  "gc-men-tote-bags": ["gc-men-tote-bags"],
  "gc-men-small-bags-pouches": ["gc-men-small-bags-pouches"],
  "gc-men-belt-slingbags": ["gc-men-belt-slingbags"],
  "gc-men-duffle-bags": ["gc-men-duffle-bags"],
  gucci: [
    "gucci",
    "gc-women",
    "gc-women-rtw",
    ...GC_WOMEN_RTW_LEAF_IDS,
    "gc-men",
    "gc-men-rtw",
    ...GC_MEN_RTW_LEAF_IDS,
  ],
  "gc-women": ["gc-women", "gc-women-rtw", ...GC_WOMEN_RTW_LEAF_IDS],
  "gc-women-rtw": ["gc-women-rtw", ...GC_WOMEN_RTW_LEAF_IDS],
  "gc-women-knitwear": ["gc-women-knitwear"],
  "gc-women-tops-shirts": ["gc-women-tops-shirts"],
  "gc-women-tshirts-sweatshirts": ["gc-women-tshirts-sweatshirts"],
  "gc-women-dresses": ["gc-women-dresses"],
  "gc-women-pants-shorts": ["gc-women-pants-shorts"],
  "gc-women-denim": ["gc-women-denim"],
  "gc-women-skirts": ["gc-women-skirts"],
  "gc-women-swimwear": ["gc-women-swimwear"],
  "gc-women-coats-jackets": ["gc-women-coats-jackets"],
  "gc-women-outerwear": ["gc-women-outerwear"],
  "gc-women-leather": ["gc-women-leather"],
  "gc-women-activewear": ["gc-women-activewear"],
  "gc-women-cocktail-evening": ["gc-women-cocktail-evening"],
  "gc-men": ["gc-men", "gc-men-rtw", ...GC_MEN_RTW_LEAF_IDS],
  "gc-men-rtw": ["gc-men-rtw", ...GC_MEN_RTW_LEAF_IDS],
  "gc-men-tshirts-polos": ["gc-men-tshirts-polos"],
  "gc-men-tracksuit-sweatshirts": ["gc-men-tracksuit-sweatshirts"],
  "gc-men-shirts": ["gc-men-shirts"],
  "gc-men-knitwear": ["gc-men-knitwear"],
  "gc-men-denim": ["gc-men-denim"],
  "gc-men-trousers-shorts": ["gc-men-trousers-shorts"],
  "gc-men-swimwear": ["gc-men-swimwear"],
  "gc-men-outerwear": ["gc-men-outerwear"],
  "gc-men-leather": ["gc-men-leather"],
  "gc-men-formal-wear": ["gc-men-formal-wear"],
  "gc-men-coats-jackets": ["gc-men-coats-jackets"],
  chanel: ["chanel", "ch-women", "ch-women-rtw", ...CH_WOMEN_RTW_LEAF_IDS],
  "ch-women": ["ch-women", "ch-women-rtw", ...CH_WOMEN_RTW_LEAF_IDS],
  "ch-women-rtw": ["ch-women-rtw", ...CH_WOMEN_RTW_LEAF_IDS],
  "ch-women-looks": ["ch-women-looks"],
  "ch-women-jackets": ["ch-women-jackets"],
  "ch-women-dresses": ["ch-women-dresses"],
  "ch-women-blouses-tops": ["ch-women-blouses-tops"],
  "ch-women-cardigans-sweaters": ["ch-women-cardigans-sweaters"],
  "ch-women-skirts": ["ch-women-skirts"],
  "ch-women-trousers-shorts": ["ch-women-trousers-shorts"],
  "ch-women-swimwear": ["ch-women-swimwear"],
  "ch-women-outerwear": ["ch-women-outerwear"],
  "gc-women-shoulder-bags": ["gc-women-shoulder-bags"],
  "gc-women-mini-bags": ["gc-women-mini-bags"],
  "gc-women-crossbody-bags": ["gc-women-crossbody-bags"],
  "gc-women-tote-bags": ["gc-women-tote-bags"],
  "gc-women-top-handle-bags": ["gc-women-top-handle-bags"],
  "gc-women-backpacks-beltbags": ["gc-women-backpacks-beltbags"],
  "gc-women-clutches-evening": ["gc-women-clutches-evening"],
  "gc-women-personalised": ["gc-women-personalised"],
  "gucci-shoes": [
    "gucci-shoes",
    "gc-shoes-womens",
    "gc-women-shoes",
    ...GC_WOMEN_SHOE_LEAF_IDS,
    "gc-shoes-mens",
    "gc-men-shoes",
    ...GC_MEN_SHOE_LEAF_IDS,
  ],
  "gc-shoes-womens": ["gc-shoes-womens", "gc-women-shoes", ...GC_WOMEN_SHOE_LEAF_IDS],
  "gc-women-shoes": ["gc-women-shoes", ...GC_WOMEN_SHOE_LEAF_IDS],
  "gc-women-sneakers": ["gc-women-sneakers"],
  "gc-women-moccasins": ["gc-women-moccasins"],
  "gc-women-slippers-mules": ["gc-women-slippers-mules"],
  "gc-women-sandals": ["gc-women-sandals"],
  "gc-women-slides": ["gc-women-slides"],
  "gc-women-pumps": ["gc-women-pumps"],
  "gc-women-ballet-flats": ["gc-women-ballet-flats"],
  "gc-women-boots": ["gc-women-boots"],
  "gc-shoes-mens": ["gc-shoes-mens", "gc-men-shoes", ...GC_MEN_SHOE_LEAF_IDS],
  "gc-men-shoes": ["gc-men-shoes", ...GC_MEN_SHOE_LEAF_IDS],
  "gc-men-sneakers": ["gc-men-sneakers"],
  "gc-men-loafers-moccasins": ["gc-men-loafers-moccasins"],
  "gc-men-slides-sandals": ["gc-men-slides-sandals"],
  "gc-men-driving": ["gc-men-driving"],
  "gc-men-lace-ups": ["gc-men-lace-ups"],
  "gc-men-boots": ["gc-men-boots"],
  "gucci-accessories": [
    "gucci-accessories",
    "gc-accessories-womens",
    "gc-women-wallets",
    ...GC_WOMEN_WALLET_LEAF_IDS,
    "gc-women-fashion-accessories",
    ...GC_WOMEN_FASHION_ACCESSORY_LEAF_IDS,
    "gc-women-travel",
    ...GC_WOMEN_TRAVEL_LEAF_IDS,
    "gc-accessories-mens",
    "gc-men-wallets",
    ...GC_MEN_WALLET_LEAF_IDS,
    "gc-men-fashion-accessories",
    ...GC_MEN_FASHION_ACCESSORY_LEAF_IDS,
    "gc-men-travel",
    ...GC_MEN_TRAVEL_LEAF_IDS,
    "gc-men-jewellery",
    ...GC_MEN_JEWELLERY_LEAF_IDS,
    "gc-men-gifts",
    ...GC_MEN_GIFTS_LEAF_IDS,
    "gc-jewellery-watches",
    "gc-gold-jewellery",
    ...GC_GOLD_JEWELLERY_LEAF_IDS,
    "gc-silver-jewellery",
    ...GC_SILVER_JEWELLERY_LEAF_IDS,
    "gc-fashion-jewellery",
    "gc-watches",
    ...GC_WATCHES_LEAF_IDS,
    "gc-gifts",
    ...GC_GIFTS_LEAF_IDS,
  ],
  "gc-gifts": ["gc-gifts", ...GC_GIFTS_LEAF_IDS],
  "gc-gifts-her": ["gc-gifts-her"],
  "gc-gifts-him": ["gc-gifts-him"],
  "gc-gifts-personalised": ["gc-gifts-personalised"],
  "gc-gifts-beauty": ["gc-gifts-beauty"],
  "gc-gifts-jewellery": ["gc-gifts-jewellery"],
  "gc-gifts-children": ["gc-gifts-children"],
  "gc-accessories-womens": [
    "gc-accessories-womens",
    "gc-women-wallets",
    ...GC_WOMEN_WALLET_LEAF_IDS,
    "gc-women-fashion-accessories",
    ...GC_WOMEN_FASHION_ACCESSORY_LEAF_IDS,
    "gc-women-travel",
    ...GC_WOMEN_TRAVEL_LEAF_IDS,
    "gc-jewellery-watches",
    "gc-gold-jewellery",
    ...GC_GOLD_JEWELLERY_LEAF_IDS,
    "gc-silver-jewellery",
    ...GC_SILVER_JEWELLERY_LEAF_IDS,
    "gc-fashion-jewellery",
    "gc-watches",
    ...GC_WATCHES_LEAF_IDS,
  ],
  "gc-accessories-mens": [
    "gc-accessories-mens",
    "gc-men-wallets",
    ...GC_MEN_WALLET_LEAF_IDS,
    "gc-men-fashion-accessories",
    ...GC_MEN_FASHION_ACCESSORY_LEAF_IDS,
    "gc-men-travel",
    ...GC_MEN_TRAVEL_LEAF_IDS,
    "gc-men-jewellery",
    ...GC_MEN_JEWELLERY_LEAF_IDS,
    "gc-men-gifts",
    ...GC_MEN_GIFTS_LEAF_IDS,
  ],
  "gc-men-jewellery": ["gc-men-jewellery", ...GC_MEN_JEWELLERY_LEAF_IDS],
  "gc-men-fashion-jewellery": ["gc-men-fashion-jewellery"],
  "gc-men-gifts": ["gc-men-gifts", ...GC_MEN_GIFTS_LEAF_IDS],
  "gc-men-gifts-bags": ["gc-men-gifts-bags"],
  "gc-men-gifts-belts": ["gc-men-gifts-belts"],
  "gc-men-gifts-jewellery-watches": ["gc-men-gifts-jewellery-watches"],
  "gc-men-gifts-shoes": ["gc-men-gifts-shoes"],
  "gc-men-gifts-small-accessories": ["gc-men-gifts-small-accessories"],
  "gc-men-gifts-small-leathergoods": ["gc-men-gifts-small-leathergoods"],
  "gc-men-gifts-sunglasses": ["gc-men-gifts-sunglasses"],
  "gc-men-gifts-watches": ["gc-men-gifts-watches"],
  "gc-men-gifts-personalised": ["gc-men-gifts-personalised"],
  "gc-women-wallets": ["gc-women-wallets", ...GC_WOMEN_WALLET_LEAF_IDS],
  "gc-women-long-wallets": ["gc-women-long-wallets"],
  "gc-women-chain-wallets": ["gc-women-chain-wallets"],
  "gc-women-compact-wallets": ["gc-women-compact-wallets"],
  "gc-women-card-holders": ["gc-women-card-holders"],
  "gc-women-bag-charms-keychains": ["gc-women-bag-charms-keychains"],
  "gc-women-pouches": ["gc-women-pouches"],
  "gc-women-tech-accessories": ["gc-women-tech-accessories"],
  "gc-men-wallets": ["gc-men-wallets", ...GC_MEN_WALLET_LEAF_IDS],
  "gc-men-wallets-wallets": ["gc-men-wallets-wallets"],
  "gc-men-wallets-small-bags-pouches": ["gc-men-wallets-small-bags-pouches"],
  "gc-men-card-coin-cases": ["gc-men-card-coin-cases"],
  "gc-men-keyrings-keycases": ["gc-men-keyrings-keycases"],
  "gc-men-tech-accessories": ["gc-men-tech-accessories"],
  "gc-women-fashion-accessories": [
    "gc-women-fashion-accessories",
    ...GC_WOMEN_FASHION_ACCESSORY_LEAF_IDS,
  ],
  "gc-women-belts": ["gc-women-belts"],
  "gc-women-scarves-silks": ["gc-women-scarves-silks"],
  "gc-women-hats-gloves": ["gc-women-hats-gloves"],
  "gc-women-eyewear": ["gc-women-eyewear"],
  "gc-women-hair-accessories": ["gc-women-hair-accessories"],
  "gc-women-socks-tights": ["gc-women-socks-tights"],
  "gc-men-fashion-accessories": [
    "gc-men-fashion-accessories",
    ...GC_MEN_FASHION_ACCESSORY_LEAF_IDS,
  ],
  "gc-men-belts": ["gc-men-belts"],
  "gc-men-eyewear": ["gc-men-eyewear"],
  "gc-men-hats-gloves": ["gc-men-hats-gloves"],
  "gc-men-ties": ["gc-men-ties"],
  "gc-men-scarves": ["gc-men-scarves"],
  "gc-men-socks": ["gc-men-socks"],
  "gc-men-bag-charms-keychains": ["gc-men-bag-charms-keychains"],
  "gc-women-travel": ["gc-women-travel", ...GC_WOMEN_TRAVEL_LEAF_IDS],
  "gc-women-trolley": ["gc-women-trolley"],
  "gc-women-weekend-duffle": ["gc-women-weekend-duffle"],
  "gc-women-travel-accessories": ["gc-women-travel-accessories"],
  "gc-women-hard-shell-luggage": ["gc-women-hard-shell-luggage"],
  "gc-men-travel": ["gc-men-travel", ...GC_MEN_TRAVEL_LEAF_IDS],
  "gc-men-trolley": ["gc-men-trolley"],
  "gc-men-weekend-duffle": ["gc-men-weekend-duffle"],
  "gc-men-travel-accessories": ["gc-men-travel-accessories"],
  "gc-men-hard-shell-luggage": ["gc-men-hard-shell-luggage"],
  "gc-jewellery-watches": [
    "gc-jewellery-watches",
    "gc-gold-jewellery",
    ...GC_GOLD_JEWELLERY_LEAF_IDS,
    "gc-silver-jewellery",
    ...GC_SILVER_JEWELLERY_LEAF_IDS,
    "gc-fashion-jewellery",
    "gc-men-fashion-jewellery",
    "gc-watches",
    ...GC_WATCHES_LEAF_IDS,
  ],
  "gc-gold-jewellery": ["gc-gold-jewellery", ...GC_GOLD_JEWELLERY_LEAF_IDS],
  "gc-gold-jewellery-women": ["gc-gold-jewellery-women"],
  "gc-gold-jewellery-men": ["gc-gold-jewellery-men"],
  "gc-silver-jewellery": ["gc-silver-jewellery", ...GC_SILVER_JEWELLERY_LEAF_IDS],
  "gc-silver-jewellery-women": ["gc-silver-jewellery-women"],
  "gc-silver-jewellery-men": ["gc-silver-jewellery-men"],
  "gc-fashion-jewellery": ["gc-fashion-jewellery", "gc-men-fashion-jewellery"],
  "gc-watches": ["gc-watches", ...GC_WATCHES_LEAF_IDS],
  "gc-watches-women": ["gc-watches-women"],
  "gc-watches-men": ["gc-watches-men"],
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
  burberry: [...BB_LUXURY_WOMEN_IDS, ...BB_LUXURY_MEN_IDS, ...BB_LUXURY_KIDS_IDS],
  "bb-trench": [...BB_TRENCH_IDS],
  "bb-women": [...BB_LUXURY_WOMEN_IDS],
  "bb-women-latest": [...BB_WOMEN_LATEST_IDS],
  "bb-women-coats-jackets": [...BB_WOMEN_COATS_IDS],
  "bb-women-clothes": [...BB_WOMEN_CLOTHES_IDS],
  "bb-men": [...BB_LUXURY_MEN_IDS],
  "bb-men-latest": [...BB_MEN_LATEST_IDS],
  "bb-men-coats-jackets": [...BB_MEN_COATS_IDS],
  "bb-men-clothes": [...BB_MEN_CLOTHES_IDS],
  "bb-kids": [...BB_LUXURY_KIDS_IDS],
  "bb-kids-latest": [...BB_KIDS_LATEST_IDS],
  "bb-kids-newborn": [...BB_KIDS_NEWBORN_IDS],
  "bb-kids-baby": [...BB_KIDS_BABY_IDS],
  "bb-kids-girls": [...BB_KIDS_GIRLS_IDS],
  "bb-kids-boys": [...BB_KIDS_BOYS_IDS],
  "burberry-bags": [
    "bb-bags-collections",
    "bb-bags-womens",
    "bb-bags-mens",
    "bb-bags-kids",
    ...BB_BAGS_COLLECTION_LEAF_IDS,
    ...BB_WOMEN_BAG_IDS,
    ...BB_MEN_BAG_IDS,
    ...BB_KIDS_BAG_IDS,
  ],
  "bb-bags-collections": [...BB_BAGS_COLLECTION_LEAF_IDS],
  "bb-bags-collections-check": [
    "bb-bags-collections-check",
    "bb-bags-collections-check-men",
  ],
  "bb-bags-womens": [...BB_WOMEN_BAG_IDS],
  "bb-women-bags": [...BB_WOMEN_BAG_IDS],
  "bb-bags-mens": [...BB_MEN_BAG_IDS],
  "bb-men-bags": [...BB_MEN_BAG_IDS],
  "bb-bags-kids": [...BB_KIDS_BAG_IDS],
  "bb-kids-bags": [...BB_KIDS_BAG_IDS],
  "burberry-shoes": [
    "bb-shoes-womens",
    "bb-shoes-mens",
    "bb-shoes-kids",
    ...BB_WOMEN_SHOE_IDS,
    ...BB_MEN_SHOE_IDS,
    ...BB_KIDS_SHOE_IDS,
  ],
  "arcteryx-shoes": ["ax-shoes-womens", "ax-shoes-mens"],
  "ax-shoes-womens": ["ax-shoes-womens"],
  "ax-shoes-mens": ["ax-shoes-mens"],
  "arcteryx": [
    "ax-womens",
    "ax-mens",
    "ax-outlet",
    "ax-outlet-womens",
    "ax-outlet-mens",
  ],
  "ax-womens": ["ax-womens"],
  "ax-mens": ["ax-mens"],
  "ax-outlet": ["ax-outlet-womens", "ax-outlet-mens"],
  "ax-outlet-womens": ["ax-outlet-womens"],
  "ax-outlet-mens": ["ax-outlet-mens"],
  "arcteryx-accessories": ["ax-acc-womens", "ax-acc-mens"],
  "ax-acc-womens": ["ax-acc-womens"],
  "ax-acc-mens": ["ax-acc-mens"],
  "umbrellas": ["lu-auto-compact", "lu-telescopic", "lu-full-length"],
  "london-undercover": [
    "lu-auto-compact",
    "lu-telescopic",
    "lu-full-length",
    "lu-lifestyle",
  ],
  "lu-auto-compact": ["lu-auto-compact"],
  "lu-telescopic": ["lu-telescopic"],
  "lu-full-length": ["lu-full-length"],
  "lu-lifestyle": ["lu-lifestyle"],
  "arcteryx-bags": ["ax-bags-womens", "ax-bags-mens"],
  "ax-bags-womens": ["ax-bags-womens"],
  "ax-bags-mens": ["ax-bags-mens"],
  "bb-shoes-womens": [...BB_WOMEN_SHOE_IDS],
  "bb-women-shoes": [...BB_WOMEN_SHOE_IDS],
  "bb-shoes-mens": [...BB_MEN_SHOE_IDS],
  "bb-men-shoes": [...BB_MEN_SHOE_IDS],
  "bb-shoes-kids": [...BB_KIDS_SHOE_IDS],
  "bb-kids-shoes": [...BB_KIDS_SHOE_IDS],
  "burberry-accessories": [
    "bb-scarves",
    "burberry-gifts",
    "bb-beauty",
    "bb-accessories-womens",
    "bb-accessories-mens",
    "bb-accessories-kids",
    ...BB_SCARVES_ALL_IDS,
    ...BB_GIFTS_ALL_IDS,
    ...BB_BEAUTY_ALL_IDS,
    ...BB_WOMEN_ACCESSORY_LEAF_IDS,
    ...BB_WOMEN_WALLET_IDS,
    ...BB_WOMEN_GIFT_IDS,
    ...BB_MEN_ACCESSORY_LEAF_IDS,
    ...BB_MEN_WALLET_IDS,
    ...BB_MEN_GIFT_IDS,
    ...BB_KIDS_ACCESSORY_LEAF_IDS,
    ...BB_KIDS_GIFT_IDS,
  ],
  "bb-scarves": [...BB_SCARVES_ALL_IDS],
  "bb-scarves-women": [...BB_SCARVES_WOMEN_IDS],
  "bb-scarves-men": [...BB_SCARVES_MEN_IDS],
  "bb-scarves-kids": [...BB_SCARVES_KIDS_IDS],
  "bb-beauty": [...BB_BEAUTY_ALL_IDS],
  "bb-beauty-makeup": [...BB_BEAUTY_MAKEUP_IDS],
  "bb-beauty-fragrances": [...BB_BEAUTY_FRAGRANCE_LEAF_IDS],
  "bb-beauty-fragrances-signatures": [
    "bb-beauty-fragrances-signatures",
    "bb-beauty-fragrances-signatures-men",
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
  "bb-accessories-kids": [
    ...BB_KIDS_ACCESSORY_LEAF_IDS,
    ...BB_KIDS_GIFT_IDS,
  ],
  "bb-kids-accessories": [...BB_KIDS_ACCESSORY_LEAF_IDS],
  "bb-kids-gifts": [...BB_KIDS_GIFT_IDS],
  "burberry-gifts": [...BB_GIFTS_ALL_IDS],
  "bb-gifts-her": [...BB_GIFTS_HER_IDS],
  "bb-gifts-him": [...BB_GIFTS_HIM_IDS],
  "bb-gifts-children": [...BB_GIFTS_CHILDREN_IDS],
  "bb-gifts-home": [...BB_GIFTS_HOME_IDS],
};

/** Top nav order: Shop first (handled separately), then these left→right, sports last */
export const navCategories: NavCategory[] = [
  {
    id: "luxury",
    labelKo: "명품 하이엔드 의류",
    href: "/shop?category=luxury",
    children: [
      {
        id: "arcteryx",
        labelKo: "아크테릭스",
        href: "/shop?category=luxury&sub=arcteryx",
        children: [
          {
            id: "ax-womens",
            labelKo: "여성용",
            href: "/shop?category=luxury&sub=ax-womens",
            navLeaf: true,
          },
          {
            id: "ax-mens",
            labelKo: "남성용",
            href: "/shop?category=luxury&sub=ax-mens",
            navLeaf: true,
          },
          {
            id: "ax-outlet",
            labelKo: "아울렛",
            href: "/shop?category=luxury&sub=ax-outlet",
            navLeaf: true,
            children: [
              {
                id: "ax-outlet-womens",
                labelKo: "여성용",
                href: "/shop?category=luxury&sub=ax-outlet-womens",
              },
              {
                id: "ax-outlet-mens",
                labelKo: "남성용",
                href: "/shop?category=luxury&sub=ax-outlet-mens",
              },
            ],
          },
        ],
      },
      {
        id: "paul-smith",
        labelKo: "폴 스미스",
        href: "/shop?category=luxury&sub=paul-smith",
        children: [
          {
            id: "ps-men",
            labelKo: "남성용",
            href: "/shop?category=luxury&sub=ps-men",
            navLeaf: true,
            children: [
              {
                id: "ps-men-all-in-one",
                labelKo: "올인원",
                href: "/shop?category=luxury&sub=ps-men-all-in-one",
              },
              {
                id: "ps-men-coats",
                labelKo: "코트",
                href: "/shop?category=luxury&sub=ps-men-coats",
              },
              {
                id: "ps-men-dressing-gown",
                labelKo: "드레싱 가운",
                href: "/shop?category=luxury&sub=ps-men-dressing-gown",
              },
              {
                id: "ps-men-jackets",
                labelKo: "재킷",
                href: "/shop?category=luxury&sub=ps-men-jackets",
              },
              {
                id: "ps-men-jeans",
                labelKo: "진",
                href: "/shop?category=luxury&sub=ps-men-jeans",
              },
              {
                id: "ps-men-knitwear",
                labelKo: "니트웨어",
                href: "/shop?category=luxury&sub=ps-men-knitwear",
              },
              {
                id: "ps-men-loungewear",
                labelKo: "라운지웨어",
                href: "/shop?category=luxury&sub=ps-men-loungewear",
              },
              {
                id: "ps-men-polos",
                labelKo: "폴로 셔츠",
                href: "/shop?category=luxury&sub=ps-men-polos",
              },
              {
                id: "ps-men-pyjamas",
                labelKo: "파자마",
                href: "/shop?category=luxury&sub=ps-men-pyjamas",
              },
              {
                id: "ps-men-shirts",
                labelKo: "셔츠",
                href: "/shop?category=luxury&sub=ps-men-shirts",
              },
              {
                id: "ps-men-shorts",
                labelKo: "쇼츠",
                href: "/shop?category=luxury&sub=ps-men-shorts",
              },
              {
                id: "ps-men-suits",
                labelKo: "수트",
                href: "/shop?category=luxury&sub=ps-men-suits",
              },
              {
                id: "ps-men-sweat-pants",
                labelKo: "스웻팬츠",
                href: "/shop?category=luxury&sub=ps-men-sweat-pants",
              },
              {
                id: "ps-men-sweatshirts",
                labelKo: "스웻셔츠",
                href: "/shop?category=luxury&sub=ps-men-sweatshirts",
              },
              {
                id: "ps-men-swimwear",
                labelKo: "스윔웨어",
                href: "/shop?category=luxury&sub=ps-men-swimwear",
              },
              {
                id: "ps-men-tshirts",
                labelKo: "티셔츠",
                href: "/shop?category=luxury&sub=ps-men-tshirts",
              },
              {
                id: "ps-men-trousers",
                labelKo: "트라우저",
                href: "/shop?category=luxury&sub=ps-men-trousers",
              },
              {
                id: "ps-men-underwear",
                labelKo: "언더웨어",
                href: "/shop?category=luxury&sub=ps-men-underwear",
              },
              {
                id: "ps-men-waistcoats",
                labelKo: "웨이스트코트",
                href: "/shop?category=luxury&sub=ps-men-waistcoats",
              },
              {
                id: "ps-men-tailoring",
                labelKo: "테일러링",
                href: "/shop?category=luxury&sub=ps-men-tailoring",
              },
              {
                id: "ps-men-other",
                labelKo: "기타 의류",
                href: "/shop?category=luxury&sub=ps-men-other",
              },
            ],
          },
          {
            id: "ps-women",
            labelKo: "여성용",
            href: "/shop?category=luxury&sub=ps-women",
            navLeaf: true,
            children: [
              {
                id: "ps-women-coats",
                labelKo: "코트",
                href: "/shop?category=luxury&sub=ps-women-coats",
              },
              {
                id: "ps-women-dresses",
                labelKo: "드레스",
                href: "/shop?category=luxury&sub=ps-women-dresses",
              },
              {
                id: "ps-women-jackets",
                labelKo: "재킷",
                href: "/shop?category=luxury&sub=ps-women-jackets",
              },
              {
                id: "ps-women-jeans",
                labelKo: "진",
                href: "/shop?category=luxury&sub=ps-women-jeans",
              },
              {
                id: "ps-women-knitwear",
                labelKo: "니트웨어",
                href: "/shop?category=luxury&sub=ps-women-knitwear",
              },
              {
                id: "ps-women-loungewear",
                labelKo: "라운지웨어",
                href: "/shop?category=luxury&sub=ps-women-loungewear",
              },
              {
                id: "ps-women-pyjamas",
                labelKo: "파자마",
                href: "/shop?category=luxury&sub=ps-women-pyjamas",
              },
              {
                id: "ps-women-shirts",
                labelKo: "셔츠",
                href: "/shop?category=luxury&sub=ps-women-shirts",
              },
              {
                id: "ps-women-shorts",
                labelKo: "쇼츠",
                href: "/shop?category=luxury&sub=ps-women-shorts",
              },
              {
                id: "ps-women-skirts",
                labelKo: "스커트",
                href: "/shop?category=luxury&sub=ps-women-skirts",
              },
              {
                id: "ps-women-suits",
                labelKo: "수트",
                href: "/shop?category=luxury&sub=ps-women-suits",
              },
              {
                id: "ps-women-sweatshirts",
                labelKo: "스웻셔츠",
                href: "/shop?category=luxury&sub=ps-women-sweatshirts",
              },
              {
                id: "ps-women-swimwear",
                labelKo: "스윔웨어",
                href: "/shop?category=luxury&sub=ps-women-swimwear",
              },
              {
                id: "ps-women-tshirts",
                labelKo: "티셔츠",
                href: "/shop?category=luxury&sub=ps-women-tshirts",
              },
              {
                id: "ps-women-trousers",
                labelKo: "트라우저",
                href: "/shop?category=luxury&sub=ps-women-trousers",
              },
              {
                id: "ps-women-waistcoats",
                labelKo: "웨이스트코트",
                href: "/shop?category=luxury&sub=ps-women-waistcoats",
              },
              {
                id: "ps-women-tailoring",
                labelKo: "테일러링",
                href: "/shop?category=luxury&sub=ps-women-tailoring",
              },
              {
                id: "ps-women-other",
                labelKo: "기타 의류",
                href: "/shop?category=luxury&sub=ps-women-other",
              }
            ],
          },
        ],
      },
      {
        id: "belstaff",
        labelKo: "벨스타프",
        href: "/shop?category=luxury&sub=belstaff",
        children: [
          {
            id: "bs-men",
            labelKo: "남성용",
            href: "/shop?category=luxury&sub=bs-men",
            navLeaf: true,
            children: [
              {
                id: "bs-men-new",
                labelKo: "신상품",
                href: "/shop?category=luxury&sub=bs-men-new",
              },
              {
                id: "bs-men-outerwear",
                labelKo: "아웃웨어",
                href: "/shop?category=luxury&sub=bs-men-outerwear",
              },
              {
                id: "bs-men-clothing",
                labelKo: "의류",
                href: "/shop?category=luxury&sub=bs-men-clothing",
              },
              {
                id: "bs-men-icons",
                labelKo: "Icons",
                href: "/shop?category=luxury&sub=bs-men-icons",
              },
              {
                id: "bs-men-motorcycle",
                labelKo: "Motorcycle",
                href: "/shop?category=luxury&sub=bs-men-motorcycle",
              },
            ],
          },
          {
            id: "bs-women",
            labelKo: "여성용",
            href: "/shop?category=luxury&sub=bs-women",
            navLeaf: true,
            children: [
              {
                id: "bs-women-new",
                labelKo: "신상품",
                href: "/shop?category=luxury&sub=bs-women-new",
              },
              {
                id: "bs-women-outerwear",
                labelKo: "아웃웨어",
                href: "/shop?category=luxury&sub=bs-women-outerwear",
              },
              {
                id: "bs-women-clothing",
                labelKo: "의류",
                href: "/shop?category=luxury&sub=bs-women-clothing",
              },
              {
                id: "bs-women-icons",
                labelKo: "Icons",
                href: "/shop?category=luxury&sub=bs-women-icons",
              },
              {
                id: "bs-women-motorcycle",
                labelKo: "Motorcycle",
                href: "/shop?category=luxury&sub=bs-women-motorcycle",
              },
            ],
          },
          {
            id: "bs-sale",
            labelKo: "세일",
            href: "/shop?category=luxury&sub=bs-sale",
            navLeaf: true,
            children: [
              {
                id: "bs-sale-men",
                labelKo: "남성용",
                href: "/shop?category=luxury&sub=bs-sale-men",
              },
              {
                id: "bs-sale-women",
                labelKo: "여성용",
                href: "/shop?category=luxury&sub=bs-sale-women",
              },
            ],
          },
        ],
      },
      {
        id: "gucci",
        labelKo: "구찌",
        href: "/shop?category=luxury&sub=gucci",
        children: [
          {
            id: "gc-women",
            labelKo: "여성용",
            href: "/shop?category=luxury&sub=gc-women",
            navLeaf: true,
            children: [
              {
                id: "gc-women-rtw",
                labelKo: "전체보기",
                href: "/shop?category=luxury&sub=gc-women-rtw",
              },
              {
                id: "gc-women-knitwear",
                labelKo: "니트웨어",
                href: "/shop?category=luxury&sub=gc-women-knitwear",
              },
              {
                id: "gc-women-tops-shirts",
                labelKo: "탑 & 셔츠",
                href: "/shop?category=luxury&sub=gc-women-tops-shirts",
              },
              {
                id: "gc-women-tshirts-sweatshirts",
                labelKo: "티셔츠 & 스웻셔츠",
                href: "/shop?category=luxury&sub=gc-women-tshirts-sweatshirts",
              },
              {
                id: "gc-women-dresses",
                labelKo: "원피스 & 점프수트",
                href: "/shop?category=luxury&sub=gc-women-dresses",
              },
              {
                id: "gc-women-pants-shorts",
                labelKo: "팬츠 & 쇼츠",
                href: "/shop?category=luxury&sub=gc-women-pants-shorts",
              },
              {
                id: "gc-women-denim",
                labelKo: "데님",
                href: "/shop?category=luxury&sub=gc-women-denim",
              },
              {
                id: "gc-women-skirts",
                labelKo: "스커트",
                href: "/shop?category=luxury&sub=gc-women-skirts",
              },
              {
                id: "gc-women-swimwear",
                labelKo: "스윔웨어",
                href: "/shop?category=luxury&sub=gc-women-swimwear",
              },
              {
                id: "gc-women-coats-jackets",
                labelKo: "코트 & 재킷",
                href: "/shop?category=luxury&sub=gc-women-coats-jackets",
              },
              {
                id: "gc-women-outerwear",
                labelKo: "아우터웨어",
                href: "/shop?category=luxury&sub=gc-women-outerwear",
              },
              {
                id: "gc-women-leather",
                labelKo: "레더",
                href: "/shop?category=luxury&sub=gc-women-leather",
              },
              {
                id: "gc-women-activewear",
                labelKo: "액티브웨어",
                href: "/shop?category=luxury&sub=gc-women-activewear",
              },
              {
                id: "gc-women-cocktail-evening",
                labelKo: "칵테일 & 이브닝",
                href: "/shop?category=luxury&sub=gc-women-cocktail-evening",
              },
            ],
          },
          {
            id: "gc-men",
            labelKo: "남성용",
            href: "/shop?category=luxury&sub=gc-men",
            navLeaf: true,
            children: [
              {
                id: "gc-men-rtw",
                labelKo: "전체보기",
                href: "/shop?category=luxury&sub=gc-men-rtw",
              },
              {
                id: "gc-men-tshirts-polos",
                labelKo: "티셔츠 & 폴로",
                href: "/shop?category=luxury&sub=gc-men-tshirts-polos",
              },
              {
                id: "gc-men-tracksuit-sweatshirts",
                labelKo: "트랙수트 & 스웻셔츠",
                href: "/shop?category=luxury&sub=gc-men-tracksuit-sweatshirts",
              },
              {
                id: "gc-men-shirts",
                labelKo: "셔츠",
                href: "/shop?category=luxury&sub=gc-men-shirts",
              },
              {
                id: "gc-men-knitwear",
                labelKo: "니트웨어",
                href: "/shop?category=luxury&sub=gc-men-knitwear",
              },
              {
                id: "gc-men-denim",
                labelKo: "데님",
                href: "/shop?category=luxury&sub=gc-men-denim",
              },
              {
                id: "gc-men-trousers-shorts",
                labelKo: "팬츠 & 쇼츠",
                href: "/shop?category=luxury&sub=gc-men-trousers-shorts",
              },
              {
                id: "gc-men-swimwear",
                labelKo: "스윔웨어",
                href: "/shop?category=luxury&sub=gc-men-swimwear",
              },
              {
                id: "gc-men-outerwear",
                labelKo: "아우터웨어",
                href: "/shop?category=luxury&sub=gc-men-outerwear",
              },
              {
                id: "gc-men-leather",
                labelKo: "레더",
                href: "/shop?category=luxury&sub=gc-men-leather",
              },
              {
                id: "gc-men-formal-wear",
                labelKo: "포멀웨어",
                href: "/shop?category=luxury&sub=gc-men-formal-wear",
              },
              {
                id: "gc-men-coats-jackets",
                labelKo: "코트 & 재킷",
                href: "/shop?category=luxury&sub=gc-men-coats-jackets",
              },
            ],
          },
        ],
      },
      {
        id: "chanel",
        labelKo: "샤넬",
        href: "/shop?category=luxury&sub=chanel",
        children: [
          {
            id: "ch-women",
            labelKo: "여성용",
            href: "/shop?category=luxury&sub=ch-women",
            navLeaf: true,
            children: [
              {
                id: "ch-women-rtw",
                labelKo: "전체보기",
                href: "/shop?category=luxury&sub=ch-women-rtw",
              },
              {
                id: "ch-women-looks",
                labelKo: "전체 룩",
                href: "/shop?category=luxury&sub=ch-women-looks",
              },
              {
                id: "ch-women-jackets",
                labelKo: "재킷",
                href: "/shop?category=luxury&sub=ch-women-jackets",
              },
              {
                id: "ch-women-dresses",
                labelKo: "드레스",
                href: "/shop?category=luxury&sub=ch-women-dresses",
              },
              {
                id: "ch-women-blouses-tops",
                labelKo: "블라우스 & 탑",
                href: "/shop?category=luxury&sub=ch-women-blouses-tops",
              },
              {
                id: "ch-women-cardigans-sweaters",
                labelKo: "가디건 & 스웨터",
                href: "/shop?category=luxury&sub=ch-women-cardigans-sweaters",
              },
              {
                id: "ch-women-skirts",
                labelKo: "스커트",
                href: "/shop?category=luxury&sub=ch-women-skirts",
              },
              {
                id: "ch-women-trousers-shorts",
                labelKo: "팬츠 & 쇼츠",
                href: "/shop?category=luxury&sub=ch-women-trousers-shorts",
              },
              {
                id: "ch-women-swimwear",
                labelKo: "스윔웨어",
                href: "/shop?category=luxury&sub=ch-women-swimwear",
              },
              {
                id: "ch-women-outerwear",
                labelKo: "아우터웨어",
                href: "/shop?category=luxury&sub=ch-women-outerwear",
              },
            ],
          },
        ],
      },
      {
        id: "burberry",
        labelKo: "버버리",
        href: "/shop?category=luxury&sub=burberry",
        children: [
          {
            id: "bb-trench",
            labelKo: "트렌치",
            href: "/shop?category=luxury&sub=bb-trench",
            navLeaf: true,
            children: [
              {
                id: "bb-women-trench-coats",
                labelKo: "여성용",
                href: "/shop?category=luxury&sub=bb-women-trench-coats",
              },
              {
                id: "bb-men-trench-coats",
                labelKo: "남성용",
                href: "/shop?category=luxury&sub=bb-men-trench-coats",
              },
            ],
          },
          {
            id: "bb-women",
            labelKo: "여성용",
            href: "/shop?category=luxury&sub=bb-women",
            navLeaf: true,
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
            labelKo: "남성용",
            href: "/shop?category=luxury&sub=bb-men",
            navLeaf: true,
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
          {
            id: "bb-kids",
            labelKo: "키즈용",
            href: "/shop?category=luxury&sub=bb-kids",
            navLeaf: true,
            children: [
              {
                id: "bb-kids-latest",
                labelKo: "Latest",
                href: "/shop?category=luxury&sub=bb-kids-latest",
                children: [
                  { id: "bb-kids-new", labelKo: "New", href: "/shop?category=luxury&sub=bb-kids-new" },
                  { id: "bb-kids-back-to-school", labelKo: "Back to School", href: "/shop?category=luxury&sub=bb-kids-back-to-school" },
                  { id: "bb-kids-summer-styles", labelKo: "Summer Styles", href: "/shop?category=luxury&sub=bb-kids-summer-styles" },
                  { id: "bb-kids-classics", labelKo: "버버리 Classics", href: "/shop?category=luxury&sub=bb-kids-classics" },
                ],
              },
              {
                id: "bb-kids-newborn",
                labelKo: "Newborn",
                href: "/shop?category=luxury&sub=bb-kids-newborn",
                children: [
                  { id: "bb-kids-newborn-onesies-dresses", labelKo: "Onesies & Dresses", href: "/shop?category=luxury&sub=bb-kids-newborn-onesies-dresses" },
                  { id: "bb-kids-newborn-shoes-accessories", labelKo: "Shoes & Accessories", href: "/shop?category=luxury&sub=bb-kids-newborn-shoes-accessories" },
                ],
              },
              {
                id: "bb-kids-baby",
                labelKo: "Baby",
                href: "/shop?category=luxury&sub=bb-kids-baby",
                children: [
                  { id: "bb-kids-baby-coats-jackets", labelKo: "Coats & Jackets", href: "/shop?category=luxury&sub=bb-kids-baby-coats-jackets" },
                  { id: "bb-kids-baby-dresses", labelKo: "Dresses", href: "/shop?category=luxury&sub=bb-kids-baby-dresses" },
                  { id: "bb-kids-baby-tops", labelKo: "Tops", href: "/shop?category=luxury&sub=bb-kids-baby-tops" },
                  { id: "bb-kids-baby-knitwear", labelKo: "Knitwear", href: "/shop?category=luxury&sub=bb-kids-baby-knitwear" },
                  { id: "bb-kids-baby-skirts-trousers", labelKo: "Skirts & Trousers", href: "/shop?category=luxury&sub=bb-kids-baby-skirts-trousers" },
                  { id: "bb-kids-baby-swimwear", labelKo: "Swimwear", href: "/shop?category=luxury&sub=bb-kids-baby-swimwear" },
                  { id: "bb-kids-baby-shoes-accessories", labelKo: "Shoes & Accessories", href: "/shop?category=luxury&sub=bb-kids-baby-shoes-accessories" },
                ],
              },
              {
                id: "bb-kids-girls",
                labelKo: "Girls",
                href: "/shop?category=luxury&sub=bb-kids-girls",
                children: [
                  { id: "bb-kids-girls-coats-jackets", labelKo: "Coats & Jackets", href: "/shop?category=luxury&sub=bb-kids-girls-coats-jackets" },
                  { id: "bb-kids-girls-dresses", labelKo: "Dresses", href: "/shop?category=luxury&sub=bb-kids-girls-dresses" },
                  { id: "bb-kids-girls-tops", labelKo: "Tops", href: "/shop?category=luxury&sub=bb-kids-girls-tops" },
                  { id: "bb-kids-girls-hoodies-sweatshirts", labelKo: "Hoodies & Sweatshirts", href: "/shop?category=luxury&sub=bb-kids-girls-hoodies-sweatshirts" },
                  { id: "bb-kids-girls-knitwear", labelKo: "Knitwear", href: "/shop?category=luxury&sub=bb-kids-girls-knitwear" },
                  { id: "bb-kids-girls-skirts-trousers", labelKo: "Skirts & Trousers", href: "/shop?category=luxury&sub=bb-kids-girls-skirts-trousers" },
                  { id: "bb-kids-girls-swimwear", labelKo: "Swimwear", href: "/shop?category=luxury&sub=bb-kids-girls-swimwear" },
                  { id: "bb-kids-girls-scarves", labelKo: "Scarves", href: "/shop?category=luxury&sub=bb-kids-girls-scarves" },
                  { id: "bb-kids-girls-shoes-accessories", labelKo: "Shoes & Accessories", href: "/shop?category=luxury&sub=bb-kids-girls-shoes-accessories" },
                ],
              },
              {
                id: "bb-kids-boys",
                labelKo: "Boys",
                href: "/shop?category=luxury&sub=bb-kids-boys",
                children: [
                  { id: "bb-kids-boys-coats-jackets", labelKo: "Coats & Jackets", href: "/shop?category=luxury&sub=bb-kids-boys-coats-jackets" },
                  { id: "bb-kids-boys-polos-tshirts", labelKo: "Polos & T-shirts", href: "/shop?category=luxury&sub=bb-kids-boys-polos-tshirts" },
                  { id: "bb-kids-boys-shirts", labelKo: "Shirts", href: "/shop?category=luxury&sub=bb-kids-boys-shirts" },
                  { id: "bb-kids-boys-knitwear", labelKo: "Knitwear", href: "/shop?category=luxury&sub=bb-kids-boys-knitwear" },
                  { id: "bb-kids-boys-hoodies-sweatshirts", labelKo: "Hoodies & Sweatshirts", href: "/shop?category=luxury&sub=bb-kids-boys-hoodies-sweatshirts" },
                  { id: "bb-kids-boys-trousers-shorts", labelKo: "Trousers & Shorts", href: "/shop?category=luxury&sub=bb-kids-boys-trousers-shorts" },
                  { id: "bb-kids-boys-swimwear", labelKo: "Swimwear", href: "/shop?category=luxury&sub=bb-kids-boys-swimwear" },
                  { id: "bb-kids-boys-scarves", labelKo: "Scarves", href: "/shop?category=luxury&sub=bb-kids-boys-scarves" },
                  { id: "bb-kids-boys-shoes-accessories", labelKo: "Shoes & Accessories", href: "/shop?category=luxury&sub=bb-kids-boys-shoes-accessories" },
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
      { id: "womens", labelKo: "여성용", href: "/shop?category=clothing&sub=womens" },
      { id: "mens", labelKo: "남성용", href: "/shop?category=clothing&sub=mens" },
    ],
  },
  {
    id: "bags",
    labelKo: "가방",
    href: "/shop?category=bags",
    children: [
      {
        id: "arcteryx-bags",
        labelKo: "아크테릭스",
        href: "/shop?category=bags&sub=arcteryx-bags",
        children: [
          {
            id: "ax-bags-womens",
            labelKo: "여성용",
            href: "/shop?category=bags&sub=ax-bags-womens",
            navLeaf: true,
          },
          {
            id: "ax-bags-mens",
            labelKo: "남성용",
            href: "/shop?category=bags&sub=ax-bags-mens",
            navLeaf: true,
          },
        ],
      },
      {
        id: "belstaff-bags",
        labelKo: "벨스타프",
        href: "/shop?category=bags&sub=belstaff-bags",
        navLeaf: true,
      },
      {
        id: "chanel-bags",
        labelKo: "샤넬",
        href: "/shop?category=bags&sub=chanel-bags",
        children: [
          {
            id: "ch-handbags",
            labelKo: "핸드백 전체",
            href: "/shop?category=bags&sub=ch-handbags",
            navLeaf: true,
          },
          {
            id: "ch-women-flap-bags",
            labelKo: "플랩백",
            href: "/shop?category=bags&sub=ch-women-flap-bags",
            navLeaf: true,
          },
          {
            id: "ch-women-hobo-bags",
            labelKo: "호보백",
            href: "/shop?category=bags&sub=ch-women-hobo-bags",
            navLeaf: true,
          },
          {
            id: "ch-women-tote-bowling-bags",
            labelKo: "토트 & 볼링백",
            href: "/shop?category=bags&sub=ch-women-tote-bowling-bags",
            navLeaf: true,
          },
          {
            id: "ch-women-bucket-bags",
            labelKo: "버킷백",
            href: "/shop?category=bags&sub=ch-women-bucket-bags",
            navLeaf: true,
          },
          {
            id: "ch-women-backpacks",
            labelKo: "백팩",
            href: "/shop?category=bags&sub=ch-women-backpacks",
            navLeaf: true,
          },
          {
            id: "ch-women-evening-bags",
            labelKo: "이브닝백",
            href: "/shop?category=bags&sub=ch-women-evening-bags",
            navLeaf: true,
          },
          {
            id: "ch-women-mini-bags",
            labelKo: "미니백",
            href: "/shop?category=bags&sub=ch-women-mini-bags",
            navLeaf: true,
          },
          {
            id: "ch-the-chanel-handbag",
            labelKo: "더 샤넬 핸드백",
            href: "/shop?category=bags&sub=ch-the-chanel-handbag",
            navLeaf: true,
          },
          {
            id: "ch-slg",
            labelKo: "스몰 레더 굿즈 전체",
            href: "/shop?category=bags&sub=ch-slg",
            navLeaf: true,
          },
          {
            id: "ch-women-wallets-on-chain",
            labelKo: "월렛 온 체인",
            href: "/shop?category=bags&sub=ch-women-wallets-on-chain",
            navLeaf: true,
          },
          {
            id: "ch-women-micro-bags",
            labelKo: "마이크로백",
            href: "/shop?category=bags&sub=ch-women-micro-bags",
            navLeaf: true,
          },
          {
            id: "ch-women-vanity",
            labelKo: "배니티",
            href: "/shop?category=bags&sub=ch-women-vanity",
            navLeaf: true,
          },
          {
            id: "ch-women-card-holders-wallets",
            labelKo: "카드홀더 & 월렛",
            href: "/shop?category=bags&sub=ch-women-card-holders-wallets",
            navLeaf: true,
          },
          {
            id: "ch-women-pouches-cases",
            labelKo: "파우치 & 케이스",
            href: "/shop?category=bags&sub=ch-women-pouches-cases",
            navLeaf: true,
          },
          {
            id: "ch-women-leather-accessories",
            labelKo: "레더 액세서리",
            href: "/shop?category=bags&sub=ch-women-leather-accessories",
            navLeaf: true,
          },
        ],
      },
      {
        id: "gucci-bags",
        labelKo: "구찌",
        href: "/shop?category=bags&sub=gucci-bags",
        children: [
          {
            id: "gc-handbags",
            labelKo: "여성용 핸드백",
            href: "/shop?category=bags&sub=gc-handbags",
            navLeaf: true,
            children: [
              {
                id: "gc-women-shoulder-bags",
                labelKo: "숄더백",
                href: "/shop?category=bags&sub=gc-women-shoulder-bags",
              },
              {
                id: "gc-women-mini-bags",
                labelKo: "미니백",
                href: "/shop?category=bags&sub=gc-women-mini-bags",
              },
              {
                id: "gc-women-crossbody-bags",
                labelKo: "크로스바디백",
                href: "/shop?category=bags&sub=gc-women-crossbody-bags",
              },
              {
                id: "gc-women-tote-bags",
                labelKo: "토트백",
                href: "/shop?category=bags&sub=gc-women-tote-bags",
              },
              {
                id: "gc-women-top-handle-bags",
                labelKo: "탑 핸들백",
                href: "/shop?category=bags&sub=gc-women-top-handle-bags",
              },
              {
                id: "gc-women-backpacks-beltbags",
                labelKo: "백팩 & 벨트백",
                href: "/shop?category=bags&sub=gc-women-backpacks-beltbags",
              },
              {
                id: "gc-women-clutches-evening",
                labelKo: "클러치 & 이브닝백",
                href: "/shop?category=bags&sub=gc-women-clutches-evening",
              },
              {
                id: "gc-women-personalised",
                labelKo: "퍼스널라이즈드 핸드백",
                href: "/shop?category=bags&sub=gc-women-personalised",
              },
            ],
          },
          {
            id: "gc-mens-handbags",
            labelKo: "남성용 핸드백",
            href: "/shop?category=bags&sub=gc-mens-handbags",
            navLeaf: true,
            children: [
              {
                id: "gc-men-crossbody-messengers",
                labelKo: "크로스바디 & 메신저",
                href: "/shop?category=bags&sub=gc-men-crossbody-messengers",
              },
              {
                id: "gc-men-backpacks",
                labelKo: "백팩",
                href: "/shop?category=bags&sub=gc-men-backpacks",
              },
              {
                id: "gc-men-tote-bags",
                labelKo: "토트백",
                href: "/shop?category=bags&sub=gc-men-tote-bags",
              },
              {
                id: "gc-men-small-bags-pouches",
                labelKo: "스몰백 & 파우치",
                href: "/shop?category=bags&sub=gc-men-small-bags-pouches",
              },
              {
                id: "gc-men-belt-slingbags",
                labelKo: "벨트백 & 슬링백",
                href: "/shop?category=bags&sub=gc-men-belt-slingbags",
              },
              {
                id: "gc-men-duffle-bags",
                labelKo: "더플백",
                href: "/shop?category=bags&sub=gc-men-duffle-bags",
              },
            ],
          },
        ],
      },
      {
        id: "burberry-bags",
        labelKo: "버버리",
        href: "/shop?category=bags&sub=burberry-bags",
        children: [
          {
            id: "bb-bags-collections",
            labelKo: "컬렉션",
            href: "/shop?category=bags&sub=bb-bags-collections",
            navLeaf: true,
            children: [
              {
                id: "bb-bags-collections-check",
                labelKo: "Check Bags",
                href: "/shop?category=bags&sub=bb-bags-collections-check",
              },
              {
                id: "bb-bags-collections-cotswolds",
                labelKo: "Cotswolds",
                href: "/shop?category=bags&sub=bb-bags-collections-cotswolds",
              },
              {
                id: "bb-bags-collections-highlands",
                labelKo: "Highlands",
                href: "/shop?category=bags&sub=bb-bags-collections-highlands",
              },
              {
                id: "bb-bags-collections-horseshoe",
                labelKo: "Horseshoe",
                href: "/shop?category=bags&sub=bb-bags-collections-horseshoe",
              },
              {
                id: "bb-bags-collections-bloomsbury",
                labelKo: "Bloomsbury",
                href: "/shop?category=bags&sub=bb-bags-collections-bloomsbury",
              },
              {
                id: "bb-bags-collections-b-clip",
                labelKo: "B Clip",
                href: "/shop?category=bags&sub=bb-bags-collections-b-clip",
              },
              {
                id: "bb-bags-collections-margate",
                labelKo: "Margate",
                href: "/shop?category=bags&sub=bb-bags-collections-margate",
              },
            ],
          },
          {
            id: "bb-bags-womens",
            labelKo: "여성용",
            href: "/shop?category=bags&sub=bb-bags-womens",
            navLeaf: true,
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
            navLeaf: true,
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
          {
            id: "bb-bags-kids",
            labelKo: "키즈용",
            href: "/shop?category=bags&sub=bb-bags-kids",
            navLeaf: true,
            children: [
              {
                id: "bb-kids-bags",
                labelKo: "Bags",
                href: "/shop?category=bags&sub=bb-kids-bags",
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
        id: "arcteryx-shoes",
        labelKo: "아크테릭스",
        href: "/shop?category=shoes&sub=arcteryx-shoes",
        children: [
          {
            id: "ax-shoes-womens",
            labelKo: "여성용",
            href: "/shop?category=shoes&sub=ax-shoes-womens",
            navLeaf: true,
          },
          {
            id: "ax-shoes-mens",
            labelKo: "남성용",
            href: "/shop?category=shoes&sub=ax-shoes-mens",
            navLeaf: true,
          },
        ],
      },
      {
        id: "paul-smith-shoes",
        labelKo: "폴 스미스",
        href: "/shop?category=shoes&sub=paul-smith-shoes",
        children: [
          {
            id: "ps-shoes-men",
            labelKo: "남성용",
            href: "/shop?category=shoes&sub=ps-shoes-men",
            navLeaf: true,
            children: [
              {
                id: "ps-shoes-boots",
                labelKo: "부츠",
                href: "/shop?category=shoes&sub=ps-shoes-boots",
              },
              {
                id: "ps-shoes-brogues",
                labelKo: "브로그",
                href: "/shop?category=shoes&sub=ps-shoes-brogues",
              },
              {
                id: "ps-shoes-derby",
                labelKo: "더비 슈즈",
                href: "/shop?category=shoes&sub=ps-shoes-derby",
              },
              {
                id: "ps-shoes-espadrilles",
                labelKo: "에스파드리유",
                href: "/shop?category=shoes&sub=ps-shoes-espadrilles",
              },
              {
                id: "ps-shoes-loafers",
                labelKo: "로퍼",
                href: "/shop?category=shoes&sub=ps-shoes-loafers",
              },
              {
                id: "ps-shoes-oxford",
                labelKo: "옥스포드",
                href: "/shop?category=shoes&sub=ps-shoes-oxford",
              },
              {
                id: "ps-shoes-sandals",
                labelKo: "샌들",
                href: "/shop?category=shoes&sub=ps-shoes-sandals",
              },
              {
                id: "ps-shoes-care",
                labelKo: "슈케어",
                href: "/shop?category=shoes&sub=ps-shoes-care",
              },
              {
                id: "ps-shoes-slides",
                labelKo: "슬라이드",
                href: "/shop?category=shoes&sub=ps-shoes-slides",
              },
              {
                id: "ps-shoes-trainers",
                labelKo: "스니커즈",
                href: "/shop?category=shoes&sub=ps-shoes-trainers",
              },
              {
                id: "ps-shoes-other",
                labelKo: "기타 슈즈",
                href: "/shop?category=shoes&sub=ps-shoes-other",
              },
            ],
          },
          {
            id: "ps-shoes-women",
            labelKo: "여성용",
            href: "/shop?category=shoes&sub=ps-shoes-women",
            navLeaf: true,
            children: [
              {
                id: "ps-shoes-women-boots",
                labelKo: "부츠",
                href: "/shop?category=shoes&sub=ps-shoes-women-boots",
              },
              {
                id: "ps-shoes-women-flats",
                labelKo: "플랫",
                href: "/shop?category=shoes&sub=ps-shoes-women-flats",
              },
              {
                id: "ps-shoes-women-loafers",
                labelKo: "로퍼",
                href: "/shop?category=shoes&sub=ps-shoes-women-loafers",
              },
              {
                id: "ps-shoes-women-sandals",
                labelKo: "샌들",
                href: "/shop?category=shoes&sub=ps-shoes-women-sandals",
              },
              {
                id: "ps-shoes-women-care",
                labelKo: "슈케어",
                href: "/shop?category=shoes&sub=ps-shoes-women-care",
              },
              {
                id: "ps-shoes-women-trainers",
                labelKo: "스니커즈",
                href: "/shop?category=shoes&sub=ps-shoes-women-trainers",
              },
              {
                id: "ps-shoes-women-other",
                labelKo: "기타 슈즈",
                href: "/shop?category=shoes&sub=ps-shoes-women-other",
              }
            ],
          },
        ],
      },
      {
        id: "belstaff-shoes",
        labelKo: "벨스타프",
        href: "/shop?category=shoes&sub=belstaff-shoes",
        children: [
          {
            id: "bs-shoes-men",
            labelKo: "남성용",
            href: "/shop?category=shoes&sub=bs-shoes-men",
            navLeaf: true,
          },
          {
            id: "bs-shoes-women",
            labelKo: "여성용",
            href: "/shop?category=shoes&sub=bs-shoes-women",
            navLeaf: true,
          },
        ],
      },
      {
        id: "chanel-shoes",
        labelKo: "샤넬",
        href: "/shop?category=shoes&sub=chanel-shoes",
        children: [
          {
            id: "ch-shoes",
            labelKo: "슈즈 전체",
            href: "/shop?category=shoes&sub=ch-shoes",
            navLeaf: true,
          },
          {
            id: "ch-women-pumps-slingbacks",
            labelKo: "펌프스 & 슬링백",
            href: "/shop?category=shoes&sub=ch-women-pumps-slingbacks",
            navLeaf: true,
          },
          {
            id: "ch-women-ballet-mary-janes",
            labelKo: "발레 플랫 & 메리제인",
            href: "/shop?category=shoes&sub=ch-women-ballet-mary-janes",
            navLeaf: true,
          },
          {
            id: "ch-women-elegant-sandals",
            labelKo: "엘레강트 샌들",
            href: "/shop?category=shoes&sub=ch-women-elegant-sandals",
            navLeaf: true,
          },
          {
            id: "ch-women-casual-sandals",
            labelKo: "캐주얼 샌들",
            href: "/shop?category=shoes&sub=ch-women-casual-sandals",
            navLeaf: true,
          },
          {
            id: "ch-women-loafers",
            labelKo: "로퍼",
            href: "/shop?category=shoes&sub=ch-women-loafers",
            navLeaf: true,
          },
          {
            id: "ch-women-boots",
            labelKo: "부츠",
            href: "/shop?category=shoes&sub=ch-women-boots",
            navLeaf: true,
          },
          {
            id: "ch-women-sneakers",
            labelKo: "스니커즈",
            href: "/shop?category=shoes&sub=ch-women-sneakers",
            navLeaf: true,
          },
        ],
      },
      {
        id: "gucci-shoes",
        labelKo: "구찌",
        href: "/shop?category=shoes&sub=gucci-shoes",
        children: [
          {
            id: "gc-shoes-womens",
            labelKo: "여성용",
            href: "/shop?category=shoes&sub=gc-shoes-womens",
            navLeaf: true,
            children: [
              {
                id: "gc-women-sneakers",
                labelKo: "스니커즈",
                href: "/shop?category=shoes&sub=gc-women-sneakers",
              },
              {
                id: "gc-women-moccasins",
                labelKo: "모카신 & 레이스업",
                href: "/shop?category=shoes&sub=gc-women-moccasins",
              },
              {
                id: "gc-women-slippers-mules",
                labelKo: "슬리퍼 & 뮬",
                href: "/shop?category=shoes&sub=gc-women-slippers-mules",
              },
              {
                id: "gc-women-sandals",
                labelKo: "샌들",
                href: "/shop?category=shoes&sub=gc-women-sandals",
              },
              {
                id: "gc-women-slides",
                labelKo: "슬라이드",
                href: "/shop?category=shoes&sub=gc-women-slides",
              },
              {
                id: "gc-women-pumps",
                labelKo: "펌프스",
                href: "/shop?category=shoes&sub=gc-women-pumps",
              },
              {
                id: "gc-women-ballet-flats",
                labelKo: "발레 플랫",
                href: "/shop?category=shoes&sub=gc-women-ballet-flats",
              },
              {
                id: "gc-women-boots",
                labelKo: "부츠 & 앵클부츠",
                href: "/shop?category=shoes&sub=gc-women-boots",
              },
            ],
          },
          {
            id: "gc-shoes-mens",
            labelKo: "남성용",
            href: "/shop?category=shoes&sub=gc-shoes-mens",
            navLeaf: true,
            children: [
              {
                id: "gc-men-sneakers",
                labelKo: "스니커즈",
                href: "/shop?category=shoes&sub=gc-men-sneakers",
              },
              {
                id: "gc-men-loafers-moccasins",
                labelKo: "로퍼 & 모카신",
                href: "/shop?category=shoes&sub=gc-men-loafers-moccasins",
              },
              {
                id: "gc-men-slides-sandals",
                labelKo: "슬라이드 & 샌들",
                href: "/shop?category=shoes&sub=gc-men-slides-sandals",
              },
              {
                id: "gc-men-driving",
                labelKo: "드라이빙 슈즈",
                href: "/shop?category=shoes&sub=gc-men-driving",
              },
              {
                id: "gc-men-lace-ups",
                labelKo: "레이스업 슈즈",
                href: "/shop?category=shoes&sub=gc-men-lace-ups",
              },
              {
                id: "gc-men-boots",
                labelKo: "부츠 & 앵클부츠",
                href: "/shop?category=shoes&sub=gc-men-boots",
              },
            ],
          },
        ],
      },
      {
        id: "burberry-shoes",
        labelKo: "버버리",
        href: "/shop?category=shoes&sub=burberry-shoes",
        children: [
          {
            id: "bb-shoes-womens",
            labelKo: "여성용",
            href: "/shop?category=shoes&sub=bb-shoes-womens",
            navLeaf: true,
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
            navLeaf: true,
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
          {
            id: "bb-shoes-kids",
            labelKo: "키즈용",
            href: "/shop?category=shoes&sub=bb-shoes-kids",
            navLeaf: true,
            children: [
              {
                id: "bb-kids-shoes",
                labelKo: "Shoes & Accessories",
                href: "/shop?category=shoes&sub=bb-kids-shoes",
                children: [
                  { id: "bb-kids-newborn-shoes-accessories", labelKo: "Newborn", href: "/shop?category=shoes&sub=bb-kids-newborn-shoes-accessories" },
                  { id: "bb-kids-baby-shoes-accessories", labelKo: "Baby", href: "/shop?category=shoes&sub=bb-kids-baby-shoes-accessories" },
                  { id: "bb-kids-girls-shoes-accessories", labelKo: "Girls", href: "/shop?category=shoes&sub=bb-kids-girls-shoes-accessories" },
                  { id: "bb-kids-boys-shoes-accessories", labelKo: "Boys", href: "/shop?category=shoes&sub=bb-kids-boys-shoes-accessories" },
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
            labelKo: "여성용",
            href: "/shop?category=shoes&sub=luxury-womens",
          },
          {
            id: "luxury-mens",
            labelKo: "남성용",
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
            labelKo: "여성용",
            href: "/shop?category=shoes&sub=training-womens",
          },
          {
            id: "training-mens",
            labelKo: "남성용",
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
        id: "paul-smith-accessories",
        labelKo: "폴 스미스",
        href: "/shop?category=accessories&sub=paul-smith-accessories",
        children: [
          {
            id: "ps-acc-men",
            labelKo: "남성용",
            href: "/shop?category=accessories&sub=ps-acc-men",
            navLeaf: true,
            children: [
              {
                id: "ps-acc-bags",
                labelKo: "백",
                href: "/shop?category=accessories&sub=ps-acc-bags",
              },
              {
                id: "ps-acc-belts",
                labelKo: "벨트",
                href: "/shop?category=accessories&sub=ps-acc-belts",
              },
              {
                id: "ps-acc-boots",
                labelKo: "부츠",
                href: "/shop?category=accessories&sub=ps-acc-boots",
              },
              {
                id: "ps-acc-ceramics",
                labelKo: "세라믹",
                href: "/shop?category=accessories&sub=ps-acc-ceramics",
              },
              {
                id: "ps-acc-giftset",
                labelKo: "기프트 세트",
                href: "/shop?category=accessories&sub=ps-acc-giftset",
              },
              {
                id: "ps-acc-gloves",
                labelKo: "글러브",
                href: "/shop?category=accessories&sub=ps-acc-gloves",
              },
              {
                id: "ps-acc-hats",
                labelKo: "모자",
                href: "/shop?category=accessories&sub=ps-acc-hats",
              },
              {
                id: "ps-acc-jewellery",
                labelKo: "주얼리",
                href: "/shop?category=accessories&sub=ps-acc-jewellery",
              },
              {
                id: "ps-acc-keyrings",
                labelKo: "키링",
                href: "/shop?category=accessories&sub=ps-acc-keyrings",
              },
              {
                id: "ps-acc-knitwear",
                labelKo: "니트웨어",
                href: "/shop?category=accessories&sub=ps-acc-knitwear",
              },
              {
                id: "ps-acc-novelty",
                labelKo: "노블티",
                href: "/shop?category=accessories&sub=ps-acc-novelty",
              },
              {
                id: "ps-acc-pocket-squares",
                labelKo: "포켓 스퀘어",
                href: "/shop?category=accessories&sub=ps-acc-pocket-squares",
              },
              {
                id: "ps-acc-pyjamas",
                labelKo: "파자마",
                href: "/shop?category=accessories&sub=ps-acc-pyjamas",
              },
              {
                id: "ps-acc-scarves",
                labelKo: "스카프",
                href: "/shop?category=accessories&sub=ps-acc-scarves",
              },
              {
                id: "ps-acc-slg",
                labelKo: "가죽 소품",
                href: "/shop?category=accessories&sub=ps-acc-slg",
              },
              {
                id: "ps-acc-socks",
                labelKo: "삭스",
                href: "/shop?category=accessories&sub=ps-acc-socks",
              },
              {
                id: "ps-acc-stationery",
                labelKo: "스테이셔너리",
                href: "/shop?category=accessories&sub=ps-acc-stationery",
              },
              {
                id: "ps-acc-swimwear",
                labelKo: "스윔웨어",
                href: "/shop?category=accessories&sub=ps-acc-swimwear",
              },
              {
                id: "ps-acc-ties",
                labelKo: "타이",
                href: "/shop?category=accessories&sub=ps-acc-ties",
              },
              {
                id: "ps-acc-towels",
                labelKo: "타월",
                href: "/shop?category=accessories&sub=ps-acc-towels",
              },
              {
                id: "ps-acc-umbrellas",
                labelKo: "우산",
                href: "/shop?category=accessories&sub=ps-acc-umbrellas",
              },
              {
                id: "ps-acc-underwear",
                labelKo: "언더웨어",
                href: "/shop?category=accessories&sub=ps-acc-underwear",
              },
              {
                id: "ps-acc-other",
                labelKo: "기타 악세서리",
                href: "/shop?category=accessories&sub=ps-acc-other",
              },
            ],
          },
          {
            id: "ps-acc-women",
            labelKo: "여성용",
            href: "/shop?category=accessories&sub=ps-acc-women",
            navLeaf: true,
            children: [
              {
                id: "ps-acc-women-bags",
                labelKo: "백",
                href: "/shop?category=accessories&sub=ps-acc-women-bags",
              },
              {
                id: "ps-acc-women-belts",
                labelKo: "벨트",
                href: "/shop?category=accessories&sub=ps-acc-women-belts",
              },
              {
                id: "ps-acc-women-gloves",
                labelKo: "글러브",
                href: "/shop?category=accessories&sub=ps-acc-women-gloves",
              },
              {
                id: "ps-acc-women-hats",
                labelKo: "모자",
                href: "/shop?category=accessories&sub=ps-acc-women-hats",
              },
              {
                id: "ps-acc-women-jewellery",
                labelKo: "주얼리",
                href: "/shop?category=accessories&sub=ps-acc-women-jewellery",
              },
              {
                id: "ps-acc-women-keyrings",
                labelKo: "키링",
                href: "/shop?category=accessories&sub=ps-acc-women-keyrings",
              },
              {
                id: "ps-acc-women-novelty",
                labelKo: "노블티",
                href: "/shop?category=accessories&sub=ps-acc-women-novelty",
              },
              {
                id: "ps-acc-women-scarves",
                labelKo: "스카프",
                href: "/shop?category=accessories&sub=ps-acc-women-scarves",
              },
              {
                id: "ps-acc-women-slg",
                labelKo: "가죽 소품",
                href: "/shop?category=accessories&sub=ps-acc-women-slg",
              },
              {
                id: "ps-acc-women-socks",
                labelKo: "삭스",
                href: "/shop?category=accessories&sub=ps-acc-women-socks",
              },
              {
                id: "ps-acc-women-stationery",
                labelKo: "스테이셔너리",
                href: "/shop?category=accessories&sub=ps-acc-women-stationery",
              },
              {
                id: "ps-acc-women-swimwear",
                labelKo: "스윔웨어",
                href: "/shop?category=accessories&sub=ps-acc-women-swimwear",
              },
              {
                id: "ps-acc-women-towels",
                labelKo: "타월",
                href: "/shop?category=accessories&sub=ps-acc-women-towels",
              },
              {
                id: "ps-acc-women-umbrellas",
                labelKo: "우산",
                href: "/shop?category=accessories&sub=ps-acc-women-umbrellas",
              },
              {
                id: "ps-acc-women-other",
                labelKo: "기타 악세서리",
                href: "/shop?category=accessories&sub=ps-acc-women-other",
              }
            ],
          },
          {
            id: "ps-gifts",
            labelKo: "선물용",
            href: "/shop?category=accessories&sub=ps-gifts",
            navLeaf: true,
            children: [
              {
                id: "ps-gifts-him",
                labelKo: "남성용",
                href: "/shop?category=accessories&sub=ps-gifts-him",
              },
              {
                id: "ps-gifts-her",
                labelKo: "여성용",
                href: "/shop?category=accessories&sub=ps-gifts-her",
              },
              {
                id: "ps-gifts-homeware",
                labelKo: "홈웨어",
                href: "/shop?category=accessories&sub=ps-gifts-homeware",
              }
            ],
          },
        ],
      },
      {
        id: "belstaff-accessories",
        labelKo: "벨스타프",
        href: "/shop?category=accessories&sub=belstaff-accessories",
        children: [
          {
            id: "bs-acc-men",
            labelKo: "남성용",
            href: "/shop?category=accessories&sub=bs-acc-men",
            navLeaf: true,
          },
          {
            id: "bs-acc-women",
            labelKo: "여성용",
            href: "/shop?category=accessories&sub=bs-acc-women",
            navLeaf: true,
          },
        ],
      },
      {
        id: "chanel-accessories",
        labelKo: "샤넬",
        href: "/shop?category=accessories&sub=chanel-accessories",
        children: [
          {
            id: "ch-jewellery",
            labelKo: "주얼리 전체",
            href: "/shop?category=accessories&sub=ch-jewellery",
            navLeaf: true,
          },
          {
            id: "ch-women-earrings",
            labelKo: "이어링",
            href: "/shop?category=accessories&sub=ch-women-earrings",
            navLeaf: true,
          },
          {
            id: "ch-women-necklaces",
            labelKo: "네크리스",
            href: "/shop?category=accessories&sub=ch-women-necklaces",
            navLeaf: true,
          },
          {
            id: "ch-women-bracelets-cuffs",
            labelKo: "브레이슬릿 & 커프",
            href: "/shop?category=accessories&sub=ch-women-bracelets-cuffs",
            navLeaf: true,
          },
          {
            id: "ch-women-brooches",
            labelKo: "브로치",
            href: "/shop?category=accessories&sub=ch-women-brooches",
            navLeaf: true,
          },
          {
            id: "ch-women-rings",
            labelKo: "링",
            href: "/shop?category=accessories&sub=ch-women-rings",
            navLeaf: true,
          },
        ],
      },
      {
        id: "gucci-accessories",
        labelKo: "구찌",
        href: "/shop?category=accessories&sub=gucci-accessories",
        children: [
          {
            id: "gc-accessories-womens",
            labelKo: "여성용",
            href: "/shop?category=accessories&sub=gc-accessories-womens",
            navLeaf: true,
            children: [
              {
                id: "gc-women-long-wallets",
                labelKo: "롱 월렛",
                href: "/shop?category=accessories&sub=gc-women-long-wallets",
              },
              {
                id: "gc-women-chain-wallets",
                labelKo: "체인 월렛",
                href: "/shop?category=accessories&sub=gc-women-chain-wallets",
              },
              {
                id: "gc-women-compact-wallets",
                labelKo: "컴팩트 월렛",
                href: "/shop?category=accessories&sub=gc-women-compact-wallets",
              },
              {
                id: "gc-women-card-holders",
                labelKo: "카드홀더",
                href: "/shop?category=accessories&sub=gc-women-card-holders",
              },
              {
                id: "gc-women-bag-charms-keychains",
                labelKo: "백 참 & 키체인",
                href: "/shop?category=accessories&sub=gc-women-bag-charms-keychains",
              },
              {
                id: "gc-women-pouches",
                labelKo: "파우치",
                href: "/shop?category=accessories&sub=gc-women-pouches",
              },
              {
                id: "gc-women-tech-accessories",
                labelKo: "테크 액세서리",
                href: "/shop?category=accessories&sub=gc-women-tech-accessories",
              },
              {
                id: "gc-women-fashion-accessories",
                labelKo: "패션 액세서리",
                href: "/shop?category=accessories&sub=gc-women-fashion-accessories",
                navLeaf: true,
                children: [
                  {
                    id: "gc-women-belts",
                    labelKo: "벨트",
                    href: "/shop?category=accessories&sub=gc-women-belts",
                  },
                  {
                    id: "gc-women-scarves-silks",
                    labelKo: "스카프 & 실크",
                    href: "/shop?category=accessories&sub=gc-women-scarves-silks",
                  },
                  {
                    id: "gc-women-hats-gloves",
                    labelKo: "모자 & 장갑",
                    href: "/shop?category=accessories&sub=gc-women-hats-gloves",
                  },
                  {
                    id: "gc-women-eyewear",
                    labelKo: "아이웨어",
                    href: "/shop?category=accessories&sub=gc-women-eyewear",
                  },
                  {
                    id: "gc-women-hair-accessories",
                    labelKo: "헤어 액세서리",
                    href: "/shop?category=accessories&sub=gc-women-hair-accessories",
                  },
                  {
                    id: "gc-women-socks-tights",
                    labelKo: "삭스 & 타이즈",
                    href: "/shop?category=accessories&sub=gc-women-socks-tights",
                  },
                ],
              },
              {
                id: "gc-women-travel",
                labelKo: "여행",
                href: "/shop?category=accessories&sub=gc-women-travel",
                navLeaf: true,
                children: [
                  {
                    id: "gc-women-trolley",
                    labelKo: "트롤리",
                    href: "/shop?category=accessories&sub=gc-women-trolley",
                  },
                  {
                    id: "gc-women-weekend-duffle",
                    labelKo: "위켄드백 & 더플백",
                    href: "/shop?category=accessories&sub=gc-women-weekend-duffle",
                  },
                  {
                    id: "gc-women-travel-accessories",
                    labelKo: "여행 액세서리",
                    href: "/shop?category=accessories&sub=gc-women-travel-accessories",
                  },
                  {
                    id: "gc-women-hard-shell-luggage",
                    labelKo: "하드셸 러기지",
                    href: "/shop?category=accessories&sub=gc-women-hard-shell-luggage",
                  },
                ],
              },
              {
                id: "gc-jewellery-watches",
                labelKo: "쥬얼리 & 시계",
                href: "/shop?category=accessories&sub=gc-jewellery-watches",
                navLeaf: true,
                children: [
                  {
                    id: "gc-gold-jewellery",
                    labelKo: "골드 쥬얼리",
                    href: "/shop?category=accessories&sub=gc-gold-jewellery",
                    children: [
                      {
                        id: "gc-gold-jewellery-women",
                        labelKo: "여성용",
                        href: "/shop?category=accessories&sub=gc-gold-jewellery-women",
                      },
                      {
                        id: "gc-gold-jewellery-men",
                        labelKo: "남성용",
                        href: "/shop?category=accessories&sub=gc-gold-jewellery-men",
                      },
                    ],
                  },
                  {
                    id: "gc-silver-jewellery",
                    labelKo: "실버 쥬얼리",
                    href: "/shop?category=accessories&sub=gc-silver-jewellery",
                    children: [
                      {
                        id: "gc-silver-jewellery-women",
                        labelKo: "여성용",
                        href: "/shop?category=accessories&sub=gc-silver-jewellery-women",
                      },
                      {
                        id: "gc-silver-jewellery-men",
                        labelKo: "남성용",
                        href: "/shop?category=accessories&sub=gc-silver-jewellery-men",
                      },
                    ],
                  },
                  {
                    id: "gc-fashion-jewellery",
                    labelKo: "패션 쥬얼리",
                    href: "/shop?category=accessories&sub=gc-fashion-jewellery",
                  },
                  {
                    id: "gc-watches",
                    labelKo: "시계",
                    href: "/shop?category=accessories&sub=gc-watches",
                    children: [
                      {
                        id: "gc-watches-women",
                        labelKo: "여성용",
                        href: "/shop?category=accessories&sub=gc-watches-women",
                      },
                      {
                        id: "gc-watches-men",
                        labelKo: "남성용",
                        href: "/shop?category=accessories&sub=gc-watches-men",
                      },
                    ],
                  },
                ],
              },
            ],
          },
          {
            id: "gc-accessories-mens",
            labelKo: "남성용",
            href: "/shop?category=accessories&sub=gc-accessories-mens",
            navLeaf: true,
            children: [
              {
                id: "gc-men-wallets",
                labelKo: "지갑 & 악세서리",
                href: "/shop?category=accessories&sub=gc-men-wallets",
                navLeaf: true,
                children: [
                  {
                    id: "gc-men-wallets-wallets",
                    labelKo: "지갑",
                    href: "/shop?category=accessories&sub=gc-men-wallets-wallets",
                  },
                  {
                    id: "gc-men-wallets-small-bags-pouches",
                    labelKo: "스몰백 & 파우치",
                    href: "/shop?category=accessories&sub=gc-men-wallets-small-bags-pouches",
                  },
                  {
                    id: "gc-men-card-coin-cases",
                    labelKo: "카드홀더 & 코인케이스",
                    href: "/shop?category=accessories&sub=gc-men-card-coin-cases",
                  },
                  {
                    id: "gc-men-keyrings-keycases",
                    labelKo: "키링 & 키케이스",
                    href: "/shop?category=accessories&sub=gc-men-keyrings-keycases",
                  },
                  {
                    id: "gc-men-tech-accessories",
                    labelKo: "테크 액세서리",
                    href: "/shop?category=accessories&sub=gc-men-tech-accessories",
                  },
                ],
              },
              {
                id: "gc-men-fashion-accessories",
                labelKo: "패션 액세서리",
                href: "/shop?category=accessories&sub=gc-men-fashion-accessories",
                navLeaf: true,
                children: [
                  {
                    id: "gc-men-belts",
                    labelKo: "벨트",
                    href: "/shop?category=accessories&sub=gc-men-belts",
                  },
                  {
                    id: "gc-men-eyewear",
                    labelKo: "아이웨어",
                    href: "/shop?category=accessories&sub=gc-men-eyewear",
                  },
                  {
                    id: "gc-men-hats-gloves",
                    labelKo: "모자 & 장갑",
                    href: "/shop?category=accessories&sub=gc-men-hats-gloves",
                  },
                  {
                    id: "gc-men-ties",
                    labelKo: "타이",
                    href: "/shop?category=accessories&sub=gc-men-ties",
                  },
                  {
                    id: "gc-men-scarves",
                    labelKo: "스카프",
                    href: "/shop?category=accessories&sub=gc-men-scarves",
                  },
                  {
                    id: "gc-men-socks",
                    labelKo: "삭스",
                    href: "/shop?category=accessories&sub=gc-men-socks",
                  },
                  {
                    id: "gc-men-bag-charms-keychains",
                    labelKo: "백 참 & 키체인",
                    href: "/shop?category=accessories&sub=gc-men-bag-charms-keychains",
                  },
                ],
              },
              {
                id: "gc-men-travel",
                labelKo: "여행",
                href: "/shop?category=accessories&sub=gc-men-travel",
                navLeaf: true,
                children: [
                  {
                    id: "gc-men-trolley",
                    labelKo: "트롤리",
                    href: "/shop?category=accessories&sub=gc-men-trolley",
                  },
                  {
                    id: "gc-men-weekend-duffle",
                    labelKo: "위켄드백 & 더플백",
                    href: "/shop?category=accessories&sub=gc-men-weekend-duffle",
                  },
                  {
                    id: "gc-men-travel-accessories",
                    labelKo: "여행 액세서리",
                    href: "/shop?category=accessories&sub=gc-men-travel-accessories",
                  },
                  {
                    id: "gc-men-hard-shell-luggage",
                    labelKo: "하드셸 러기지",
                    href: "/shop?category=accessories&sub=gc-men-hard-shell-luggage",
                  },
                ],
              },
              {
                id: "gc-men-jewellery",
                labelKo: "쥬얼리",
                href: "/shop?category=accessories&sub=gc-men-jewellery",
                navLeaf: true,
                children: [
                  {
                    id: "gc-gold-jewellery-men",
                    labelKo: "골드 쥬얼리",
                    href: "/shop?category=accessories&sub=gc-gold-jewellery-men",
                  },
                  {
                    id: "gc-silver-jewellery-men",
                    labelKo: "실버 쥬얼리",
                    href: "/shop?category=accessories&sub=gc-silver-jewellery-men",
                  },
                  {
                    id: "gc-men-fashion-jewellery",
                    labelKo: "패션 쥬얼리",
                    href: "/shop?category=accessories&sub=gc-men-fashion-jewellery",
                  },
                ],
              },
              {
                id: "gc-men-gifts",
                labelKo: "선물용",
                href: "/shop?category=accessories&sub=gc-men-gifts",
                navLeaf: true,
                children: [
                  {
                    id: "gc-men-gifts-bags",
                    labelKo: "가방",
                    href: "/shop?category=accessories&sub=gc-men-gifts-bags",
                  },
                  {
                    id: "gc-men-gifts-belts",
                    labelKo: "벨트",
                    href: "/shop?category=accessories&sub=gc-men-gifts-belts",
                  },
                  {
                    id: "gc-men-gifts-jewellery-watches",
                    labelKo: "쥬얼리 & 시계",
                    href: "/shop?category=accessories&sub=gc-men-gifts-jewellery-watches",
                  },
                  {
                    id: "gc-men-gifts-shoes",
                    labelKo: "슈즈",
                    href: "/shop?category=accessories&sub=gc-men-gifts-shoes",
                  },
                  {
                    id: "gc-men-gifts-small-accessories",
                    labelKo: "스몰 액세서리",
                    href: "/shop?category=accessories&sub=gc-men-gifts-small-accessories",
                  },
                  {
                    id: "gc-men-gifts-small-leathergoods",
                    labelKo: "스몰 레더굿즈",
                    href: "/shop?category=accessories&sub=gc-men-gifts-small-leathergoods",
                  },
                  {
                    id: "gc-men-gifts-sunglasses",
                    labelKo: "선글라스",
                    href: "/shop?category=accessories&sub=gc-men-gifts-sunglasses",
                  },
                  {
                    id: "gc-men-gifts-watches",
                    labelKo: "시계",
                    href: "/shop?category=accessories&sub=gc-men-gifts-watches",
                  },
                  {
                    id: "gc-men-gifts-personalised",
                    labelKo: "퍼스널라이즈드 선물",
                    href: "/shop?category=accessories&sub=gc-men-gifts-personalised",
                  },
                ],
              },
            ],
          },
          {
            id: "gc-gifts",
            labelKo: "선물용",
            href: "/shop?category=accessories&sub=gc-gifts",
            navLeaf: true,
            children: [
              {
                id: "gc-gifts-her",
                labelKo: "여성을 위한 선물",
                href: "/shop?category=accessories&sub=gc-gifts-her",
              },
              {
                id: "gc-gifts-him",
                labelKo: "남성을 위한 선물",
                href: "/shop?category=accessories&sub=gc-gifts-him",
              },
              {
                id: "gc-gifts-personalised",
                labelKo: "퍼스널라이즈드 선물",
                href: "/shop?category=accessories&sub=gc-gifts-personalised",
              },
              {
                id: "gc-gifts-beauty",
                labelKo: "향수 & 메이크업 선물",
                href: "/shop?category=accessories&sub=gc-gifts-beauty",
              },
              {
                id: "gc-gifts-jewellery",
                labelKo: "쥬얼리 선물",
                href: "/shop?category=accessories&sub=gc-gifts-jewellery",
              },
              {
                id: "gc-gifts-children",
                labelKo: "키즈 선물",
                href: "/shop?category=accessories&sub=gc-gifts-children",
              },
            ],
          },
        ],
      },
      {
        id: "arcteryx-accessories",
        labelKo: "아크테릭스",
        href: "/shop?category=accessories&sub=arcteryx-accessories",
        children: [
          {
            id: "ax-acc-womens",
            labelKo: "여성용",
            href: "/shop?category=accessories&sub=ax-acc-womens",
            navLeaf: true,
          },
          {
            id: "ax-acc-mens",
            labelKo: "남성용",
            href: "/shop?category=accessories&sub=ax-acc-mens",
            navLeaf: true,
          },
        ],
      },
      {
        id: "london-undercover",
        labelKo: "런던언더커버",
        href: "/shop?category=accessories&sub=london-undercover",
        children: [
          {
            id: "umbrellas",
            labelKo: "우산",
            href: "/shop?category=accessories&sub=umbrellas",
            navLeaf: true,
            children: [
              {
                id: "lu-auto-compact",
                labelKo: "오토컴팩트",
                href: "/shop?category=accessories&sub=lu-auto-compact",
              },
              {
                id: "lu-telescopic",
                labelKo: "텔레스코픽",
                href: "/shop?category=accessories&sub=lu-telescopic",
              },
              {
                id: "lu-full-length",
                labelKo: "장우산",
                href: "/shop?category=accessories&sub=lu-full-length",
              },
            ],
          },
          {
            id: "lu-lifestyle",
            labelKo: "라이프스타일",
            href: "/shop?category=accessories&sub=lu-lifestyle",
            navLeaf: true,
          },
        ],
      },
      {
        id: "burberry-accessories",
        labelKo: "버버리",
        href: "/shop?category=accessories&sub=burberry-accessories",
        children: [
          {
            id: "bb-scarves",
            labelKo: "스카프",
            href: "/shop?category=accessories&sub=bb-scarves",
            navLeaf: true,
            children: [
              {
                id: "bb-scarves-women",
                labelKo: "여성용",
                href: "/shop?category=accessories&sub=bb-scarves-women",
                navLeaf: true,
                children: [
                  {
                    id: "bb-scarves-women",
                    labelKo: "전체 보기",
                    href: "/shop?category=accessories&sub=bb-scarves-women",
                  },
                  {
                    id: "bb-scarves-women-cashmere",
                    labelKo: "캐시미어",
                    href: "/shop?category=accessories&sub=bb-scarves-women-cashmere",
                  },
                  {
                    id: "bb-scarves-women-wool",
                    labelKo: "울",
                    href: "/shop?category=accessories&sub=bb-scarves-women-wool",
                  },
                  {
                    id: "bb-scarves-women-silk",
                    labelKo: "실크",
                    href: "/shop?category=accessories&sub=bb-scarves-women-silk",
                  },
                  {
                    id: "bb-scarves-women-lightweight",
                    labelKo: "라이트웨이트",
                    href: "/shop?category=accessories&sub=bb-scarves-women-lightweight",
                  },
                  {
                    id: "bb-scarves-women-personalised",
                    labelKo: "퍼스널라이즈",
                    href: "/shop?category=accessories&sub=bb-scarves-women-personalised",
                  },
                ],
              },
              {
                id: "bb-scarves-men",
                labelKo: "남성용",
                href: "/shop?category=accessories&sub=bb-scarves-men",
                navLeaf: true,
                children: [
                  {
                    id: "bb-scarves-men",
                    labelKo: "전체 보기",
                    href: "/shop?category=accessories&sub=bb-scarves-men",
                  },
                  {
                    id: "bb-scarves-men-cashmere",
                    labelKo: "캐시미어",
                    href: "/shop?category=accessories&sub=bb-scarves-men-cashmere",
                  },
                  {
                    id: "bb-scarves-men-wool",
                    labelKo: "울",
                    href: "/shop?category=accessories&sub=bb-scarves-men-wool",
                  },
                  {
                    id: "bb-scarves-men-lightweight",
                    labelKo: "라이트웨이트",
                    href: "/shop?category=accessories&sub=bb-scarves-men-lightweight",
                  },
                  {
                    id: "bb-scarves-men-personalised",
                    labelKo: "퍼스널라이즈",
                    href: "/shop?category=accessories&sub=bb-scarves-men-personalised",
                  },
                ],
              },
              {
                id: "bb-scarves-kids",
                labelKo: "키즈용",
                href: "/shop?category=accessories&sub=bb-scarves-kids",
                navLeaf: true,
                children: [
                  {
                    id: "bb-scarves-kids",
                    labelKo: "전체 보기",
                    href: "/shop?category=accessories&sub=bb-scarves-kids",
                  },
                  {
                    id: "bb-scarves-kids-girls",
                    labelKo: "걸즈 스카프",
                    href: "/shop?category=accessories&sub=bb-scarves-kids-girls",
                  },
                  {
                    id: "bb-scarves-kids-boys",
                    labelKo: "보이즈 스카프",
                    href: "/shop?category=accessories&sub=bb-scarves-kids-boys",
                  },
                ],
              },
            ],
          },
          {
            id: "burberry-gifts",
            labelKo: "선물추천",
            href: "/shop?category=accessories&sub=burberry-gifts",
            navLeaf: true,
            children: [
              {
                id: "bb-gifts-her",
                labelKo: "For Her",
                href: "/shop?category=accessories&sub=bb-gifts-her",
                navLeaf: true,
                children: [
                  { id: "bb-gifts-her", labelKo: "View All", href: "/shop?category=accessories&sub=bb-gifts-her" },
                  { id: "bb-gifts-her-scarves", labelKo: "Scarves", href: "/shop?category=accessories&sub=bb-gifts-her-scarves" },
                  { id: "bb-gifts-her-jewellery", labelKo: "Jewellery", href: "/shop?category=accessories&sub=bb-gifts-her-jewellery" },
                  { id: "bb-gifts-her-fragrance", labelKo: "Fragrance", href: "/shop?category=accessories&sub=bb-gifts-her-fragrance" },
                  { id: "bb-gifts-her-personalised", labelKo: "Personalised Gifts", href: "/shop?category=accessories&sub=bb-gifts-her-personalised" },
                  { id: "bb-gifts-her-personalised-scarves", labelKo: "Personalised Scarves", href: "/shop?category=accessories&sub=bb-gifts-her-personalised-scarves" },
                  { id: "bb-gifts-her-classics", labelKo: "버버리 Classics", href: "/shop?category=accessories&sub=bb-gifts-her-classics" },
                ],
              },
              {
                id: "bb-gifts-him",
                labelKo: "For Him",
                href: "/shop?category=accessories&sub=bb-gifts-him",
                navLeaf: true,
                children: [
                  { id: "bb-gifts-him", labelKo: "View All", href: "/shop?category=accessories&sub=bb-gifts-him" },
                  { id: "bb-gifts-him-scarves", labelKo: "Scarves", href: "/shop?category=accessories&sub=bb-gifts-him-scarves" },
                  { id: "bb-gifts-him-ties-cufflinks", labelKo: "Ties & Cufflinks", href: "/shop?category=accessories&sub=bb-gifts-him-ties-cufflinks" },
                  { id: "bb-gifts-him-fragrance", labelKo: "Fragrance", href: "/shop?category=accessories&sub=bb-gifts-him-fragrance" },
                  { id: "bb-gifts-him-personalised", labelKo: "Personalised Gifts", href: "/shop?category=accessories&sub=bb-gifts-him-personalised" },
                  { id: "bb-gifts-him-personalised-scarves", labelKo: "Personalised Scarves", href: "/shop?category=accessories&sub=bb-gifts-him-personalised-scarves" },
                  { id: "bb-gifts-him-classics", labelKo: "버버리 Classics", href: "/shop?category=accessories&sub=bb-gifts-him-classics" },
                ],
              },
              {
                id: "bb-gifts-children",
                labelKo: "For Children",
                href: "/shop?category=accessories&sub=bb-gifts-children",
                navLeaf: true,
                children: [
                  { id: "bb-gifts-children", labelKo: "View All", href: "/shop?category=accessories&sub=bb-gifts-children" },
                  { id: "bb-gifts-children-girls-scarves", labelKo: "Girls’ Scarves", href: "/shop?category=accessories&sub=bb-gifts-children-girls-scarves" },
                  { id: "bb-gifts-children-boys-scarves", labelKo: "Boys’ Scarves", href: "/shop?category=accessories&sub=bb-gifts-children-boys-scarves" },
                  { id: "bb-gifts-children-baby", labelKo: "Baby Gifts", href: "/shop?category=accessories&sub=bb-gifts-children-baby" },
                  { id: "bb-gifts-children-newborn", labelKo: "Newborn Gifts", href: "/shop?category=accessories&sub=bb-gifts-children-newborn" },
                  { id: "bb-gifts-children-accessories", labelKo: "Accessories", href: "/shop?category=accessories&sub=bb-gifts-children-accessories" },
                ],
              },
              {
                id: "bb-gifts-home",
                labelKo: "For the Home",
                href: "/shop?category=accessories&sub=bb-gifts-home",
              },
            ],
          },
          {
            id: "bb-beauty",
            labelKo: "뷰티",
            href: "/shop?category=accessories&sub=bb-beauty",
            navLeaf: true,
            children: [
              {
                id: "bb-beauty-makeup",
                labelKo: "메이크업",
                href: "/shop?category=accessories&sub=bb-beauty-makeup",
                navLeaf: true,
                children: [
                  {
                    id: "bb-beauty-makeup",
                    labelKo: "전체 보기",
                    href: "/shop?category=accessories&sub=bb-beauty-makeup",
                  },
                  {
                    id: "bb-beauty-makeup-face",
                    labelKo: "Face",
                    href: "/shop?category=accessories&sub=bb-beauty-makeup-face",
                  },
                  {
                    id: "bb-beauty-makeup-lips",
                    labelKo: "Lips",
                    href: "/shop?category=accessories&sub=bb-beauty-makeup-lips",
                  },
                  {
                    id: "bb-beauty-makeup-eyes",
                    labelKo: "Eyes",
                    href: "/shop?category=accessories&sub=bb-beauty-makeup-eyes",
                  },
                ],
              },
              {
                id: "bb-beauty-fragrances",
                labelKo: "프래그런스",
                href: "/shop?category=accessories&sub=bb-beauty-fragrances",
                navLeaf: true,
                children: [
                  {
                    id: "bb-beauty-fragrances",
                    labelKo: "전체 보기",
                    href: "/shop?category=accessories&sub=bb-beauty-fragrances",
                  },
                  {
                    id: "bb-beauty-fragrances-women",
                    labelKo: "여성 프래그런스",
                    href: "/shop?category=accessories&sub=bb-beauty-fragrances-women",
                  },
                  {
                    id: "bb-beauty-fragrances-men",
                    labelKo: "남성 프래그런스",
                    href: "/shop?category=accessories&sub=bb-beauty-fragrances-men",
                  },
                  {
                    id: "bb-beauty-fragrances-signatures",
                    labelKo: "Burberry Signatures",
                    href: "/shop?category=accessories&sub=bb-beauty-fragrances-signatures",
                  },
                  {
                    id: "bb-beauty-fragrances-goddess",
                    labelKo: "Burberry Goddess",
                    href: "/shop?category=accessories&sub=bb-beauty-fragrances-goddess",
                  },
                  {
                    id: "bb-beauty-fragrances-her",
                    labelKo: "Burberry Her",
                    href: "/shop?category=accessories&sub=bb-beauty-fragrances-her",
                  },
                  {
                    id: "bb-beauty-fragrances-hero",
                    labelKo: "Burberry Hero",
                    href: "/shop?category=accessories&sub=bb-beauty-fragrances-hero",
                  },
                ],
              },
            ],
          },
          {
            id: "bb-accessories-womens",
            labelKo: "여성용",
            href: "/shop?category=accessories&sub=bb-accessories-womens",
            navLeaf: true,
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
            navLeaf: true,
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
          {
            id: "bb-accessories-kids",
            labelKo: "키즈용",
            href: "/shop?category=accessories&sub=bb-accessories-kids",
            navLeaf: true,
            children: [
              {
                id: "bb-kids-accessories",
                labelKo: "Accessories",
                href: "/shop?category=accessories&sub=bb-kids-accessories",
                children: [
                  { id: "bb-kids-hats-socks", labelKo: "Hats & Socks", href: "/shop?category=accessories&sub=bb-kids-hats-socks" },
                  { id: "bb-kids-hair-accessories", labelKo: "Hair Accessories", href: "/shop?category=accessories&sub=bb-kids-hair-accessories" },
                  { id: "bb-kids-scarves", labelKo: "Scarves", href: "/shop?category=accessories&sub=bb-kids-scarves" },
                  { id: "bb-kids-girls-scarves", labelKo: "Girls Scarves", href: "/shop?category=accessories&sub=bb-kids-girls-scarves" },
                  { id: "bb-kids-boys-scarves", labelKo: "Boys Scarves", href: "/shop?category=accessories&sub=bb-kids-boys-scarves" },
                ],
              },
              {
                id: "bb-kids-gifts",
                labelKo: "Gifts",
                href: "/shop?category=accessories&sub=bb-kids-gifts",
                children: [
                  { id: "bb-kids-gift-girls-scarves", labelKo: "Girls Scarves", href: "/shop?category=accessories&sub=bb-kids-gift-girls-scarves" },
                  { id: "bb-kids-gift-boys-scarves", labelKo: "Boys Scarves", href: "/shop?category=accessories&sub=bb-kids-gift-boys-scarves" },
                  { id: "bb-kids-newborn-gifts", labelKo: "Newborn Gifts", href: "/shop?category=accessories&sub=bb-kids-newborn-gifts" },
                  { id: "bb-kids-newborn-gift-sets", labelKo: "Newborn Gift Sets", href: "/shop?category=accessories&sub=bb-kids-newborn-gift-sets" },
                  { id: "bb-kids-baby-gifts", labelKo: "Baby Gifts", href: "/shop?category=accessories&sub=bb-kids-baby-gifts" },
                ],
              },
            ],
          },
        ],
      },
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
                    labelKo: "남성용",
                    href: "/shop?category=sports&sub=gg-new-men",
                  },
                  {
                    id: "gg-new-women",
                    labelKo: "여성용",
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
                    labelKo: "남성용",
                    href: "/shop?category=sports&sub=gg-bestsellers-men",
                  },
                  {
                    id: "gg-bestsellers-women",
                    labelKo: "여성용",
                    href: "/shop?category=sports&sub=gg-bestsellers-women",
                  },
                ],
              },
              {
                id: "gg-men",
                labelKo: "남성용",
                href: "/shop?category=sports&sub=gg-men",
              },
              {
                id: "gg-women",
                labelKo: "여성용",
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
