import { sortNavChildrenByBrandOrder } from "@/lib/brand-nav-order";

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
  | "ax-climbing-gear"
  | "ax-climbing-womens"
  | "ax-climbing-mens"
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
  | "prada-bags"
  | "pr-handbags"
  | "pr-women-shoulder-bags"
  | "pr-women-top-handle-bags"
  | "pr-women-tote-bags"
  | "pr-women-mini-bags"
  | "pr-women-backpacks"
  | "pr-women-briefcases"
  | "pr-women-travel"
  | "pr-women-travel-bags"
  | "pr-women-luggage-carry-on"
  | "pr-women-travel-accessories"
  | "pr-mens-handbags"
  | "pr-men-backpacks-belt-bags"
  | "pr-men-briefcases"
  | "pr-men-clutches"
  | "pr-men-messenger-bags"
  | "pr-men-tote-bags"
  | "pr-men-travel"
  | "pr-men-travel-bags"
  | "pr-men-luggage-carry-on"
  | "pr-men-travel-accessories"
  | "prada"
  | "prada-luxury"
  | "pr-women"
  | "pr-women-rtw"
  | "pr-women-knitwear"
  | "pr-women-shirts-tops"
  | "pr-women-tshirts-sweatshirts"
  | "pr-women-dresses"
  | "pr-women-skirts"
  | "pr-women-trousers-shorts"
  | "pr-women-denim"
  | "pr-women-jackets-coats"
  | "pr-women-outerwear"
  | "pr-women-leather"
  | "pr-women-swimwear"
  | "pr-women-pajamas-underwear"
  | "pr-men"
  | "pr-men-rtw"
  | "pr-men-denim"
  | "pr-men-jackets-coats"
  | "pr-men-jogging-suits-sweatshirts"
  | "pr-men-knitwear"
  | "pr-men-leather"
  | "pr-men-outerwear"
  | "pr-men-pajamas-underwear"
  | "pr-men-shirts"
  | "pr-men-suits"
  | "pr-men-swimwear"
  | "pr-men-trousers-bermudas"
  | "pr-men-tshirts-polos"
  | "prada-shoes"
  | "pr-women-shoes"
  | "pr-women-ankle-boots-boots"
  | "pr-women-loafers-lace-ups"
  | "pr-women-pumps-ballerinas"
  | "pr-women-sneakers"
  | "pr-women-sandals-mules"
  | "pr-women-new-formal"
  | "pr-women-chocolate"
  | "pr-men-shoes"
  | "pr-men-loafers"
  | "pr-men-sneakers"
  | "pr-men-sandals"
  | "pr-men-lace-ups"
  | "pr-men-boots"
  | "pr-men-americas-cup"
  | "prada-accessories"
  | "pr-women-accessories"
  | "pr-mens-accessories"
  | "pr-women-sunglasses"
  | "pr-women-silks-scarves"
  | "pr-women-hats-gloves"
  | "pr-women-headbands-hair"
  | "pr-women-bag-charms"
  | "pr-women-jewels"
  | "pr-women-belts"
  | "pr-women-pouches"
  | "pr-women-slg"
  | "pr-women-card-holders"
  | "pr-women-small-wallets"
  | "pr-women-large-wallets"
  | "pr-women-wallets-on-chain"
  | "pr-women-high-tech-accessories"
  | "pr-mens-slg"
  | "pr-men-card-holders"
  | "pr-men-small-wallets"
  | "pr-men-large-wallets"
  | "pr-men-high-tech-accessories"
  | "pr-men-sunglasses"
  | "pr-men-hats-gloves"
  | "pr-men-bag-charms"
  | "pr-men-belts"
  | "pr-men-custom-belts"
  | "pr-men-silks-scarves"
  | "pr-men-ties-bow-ties"
  | "pr-men-jewels"
  | "pr-linea-rossa"
  | "pr-linea-rossa-women"
  | "pr-linea-rossa-men"
  | "pr-linea-rossa-sunglasses"
  | "pr-linea-rossa-shoes"
  | "pr-linea-rossa-fragrances"
  | "pr-beauty"
  | "pr-beauty-face"
  | "pr-beauty-eyes"
  | "pr-beauty-lips"
  | "pr-beauty-skincare"
  | "pr-beauty-brushes"
  | "pr-fragrances"
  | "pr-fragrances-women"
  | "pr-fragrances-men"
  | "pr-fragrances-exclusive"
  | "pr-fine-jewelry"
  | "pr-fine-jewelry-bracelets"
  | "pr-fine-jewelry-necklaces"
  | "pr-fine-jewelry-rings"
  | "pr-fine-jewelry-earrings-brooches"
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
  | "ch-women-rings"
  | "ch-high-jewellery"
  | "ch-fine-jewellery"
  | "ch-sunglasses"
  | "ch-women-sunglasses"
  | "ch-fragrance"
  | "ch-makeup"
  | "ch-makeup-complexion"
  | "ch-makeup-foundations"
  | "ch-makeup-base"
  | "ch-makeup-healthy-glow"
  | "ch-makeup-blush"
  | "ch-makeup-powders"
  | "ch-makeup-bronzers"
  | "ch-makeup-concealer"
  | "ch-makeup-highlighter"
  | "ch-makeup-eyes"
  | "ch-makeup-eyeshadows"
  | "ch-makeup-mascara"
  | "ch-makeup-brows"
  | "ch-makeup-eyeliners"
  | "ch-makeup-eye-palette"
  | "ch-makeup-lips"
  | "ch-makeup-lip-gloss"
  | "ch-makeup-lipsticks"
  | "ch-makeup-lip-pencils"
  | "ch-makeup-lip-balms"
  | "ch-makeup-liquid-lipsticks"
  | "ch-makeup-nails"
  | "ch-makeup-manicure"
  | "ch-makeup-nail-colour"
  | "ch-makeup-brushes"
  | "ch-makeup-eye-brushes"
  | "ch-makeup-complexion-brushes"
  | "ch-makeup-lip-brushes"
  | "ch-skincare"
  | "ch-skincare-cleansers"
  | "ch-skincare-serums"
  | "ch-skincare-moisturisers"
  | "ch-skincare-eyes-lips"
  | "ch-skincare-body"
  | "ch-skincare-masks"
  | "ch-skincare-oils"
  | "ch-skincare-protection"
  | "ch-skincare-toners"
  | "ch-skincare-mists"
  | "ch-other-accessories"
  | "ch-women-headwear"
  | "ch-women-belts"
  | "ch-women-scarves"
  | "ch-women-camellias"
  | "ch-women-winter-accessories"
  | "ch-women-summer-accessories"
  | "louis-vuitton"
  | "louis-vuitton-accessories"
  | "lv-home-lifestyle"
  | "lv-furniture-lighting"
  | "lv-furniture-lighting-all"
  | "lv-seating"
  | "lv-tables"
  | "lv-lighting"
  | "lv-storage"
  | "dior"
  | "dior-accessories"
  | "di-home"
  | "di-tableware"
  | "di-tableware-all"
  | "di-plates-bowls"
  | "di-glasses"
  | "di-carafes"
  | "di-tea-coffee"
  | "di-cutlery"
  | "di-objects"
  | "di-objects-all"
  | "di-books"
  | "di-notebooks"
  | "di-desk-accessories"
  | "di-candleholders-candles"
  | "di-small-objects"
  | "di-trinket-trays"
  | "di-trays"
  | "di-leisure"
  | "di-paperweights"
  | "di-decor"
  | "di-decor-all"
  | "di-decorative-pieces"
  | "di-lighting"
  | "di-baskets"
  | "di-wallpapers"
  | "di-vases"
  | "di-furniture"
  | "di-textile"
  | "di-textile-all"
  | "di-cushions"
  | "di-bath-linen"
  | "di-table-linen"
  | "di-throws"
  | "di-jewelry-timepieces"
  | "di-jewelry-all"
  | "di-earrings"
  | "di-bracelets"
  | "di-rings"
  | "di-necklaces"
  | "di-dior-icons"
  | "dior-watches"
  | "di-timepieces-all"
  | "di-la-d-de-dior"
  | "di-straps"
  | "dior-bags"
  | "di-bags-womens"
  | "di-bags-all"
  | "di-handbags"
  | "di-crossbody-shoulder-bags"
  | "di-tote-bags"
  | "di-bucket-bags"
  | "di-clutches"
  | "di-mini-bags"
  | "di-accessorize-bag"
  | "di-acc-bag-jewelry"
  | "di-acc-bag-totes"
  | "di-acc-bag-mini"
  | "di-acc-bag-shoulder"
  | "di-acc-bag-bucket"
  | "di-acc-bag-clutches"
  | "di-acc-bag-key-rings"
  | "di-acc-bag-mitzah"
  | "di-acc-bag-purse"
  | "di-bags-mens"
  | "di-men-bags-all"
  | "di-men-crossbody-shoulder-bags"
  | "di-men-backpacks"
  | "di-men-small-bags"
  | "di-men-tote-bags"
  | "di-men-travel-bags"
  | "di-men-briefcases"
  | "di-men-accessorize-bag"
  | "di-mens"
  | "di-men-rtw-all"
  | "di-men-tshirts-polos"
  | "di-men-shirts"
  | "di-men-knitwear-sweatshirts"
  | "di-men-trousers-shorts"
  | "di-men-denim"
  | "di-men-beachwear"
  | "di-men-outerwear"
  | "di-men-tailored-jackets"
  | "di-men-leather"
  | "di-men-suits-tuxedos"
  | "di-womens"
  | "di-women-rtw-all"
  | "di-women-tshirts"
  | "di-women-shirts"
  | "di-women-sweaters-cardigans"
  | "di-women-dresses"
  | "di-women-skirts"
  | "di-women-trousers-shorts"
  | "di-women-denim"
  | "di-women-swimsuits"
  | "di-women-homewear-lingerie"
  | "di-women-coats"
  | "di-women-jackets"
  | "dior-shoes"
  | "di-men-shoes"
  | "di-men-shoes-all"
  | "di-men-sneakers"
  | "di-men-sandals-mules"
  | "di-men-loafers"
  | "di-men-lace-ups"
  | "di-men-boots"
  | "di-men-accessories"
  | "di-men-acc-all"
  | "di-men-sunglasses"
  | "di-men-belts"
  | "di-men-ties-pocket-squares"
  | "di-men-scarves"
  | "di-men-hats-gloves"
  | "di-men-socks"
  | "di-men-fashion-jewelry"
  | "di-men-silver-jewelry"
  | "di-men-key-rings"
  | "di-men-charm-jewelry"
  | "di-men-lifestyle"
  | "di-men-acc-tech"
  | "di-men-pet-accessories"
  | "di-men-slg"
  | "di-men-slg-all"
  | "di-men-card-holders"
  | "di-men-compact-wallets"
  | "di-men-long-wallets"
  | "di-men-pouches"
  | "di-men-tech-accessories"
  | "di-women-accessories"
  | "di-women-acc-all"
  | "di-women-sunglasses"
  | "di-women-optical-glasses"
  | "di-women-belts"
  | "di-women-jewelry"
  | "di-women-jewelry-all"
  | "di-women-earrings"
  | "di-women-necklaces"
  | "di-women-brooches"
  | "di-women-bracelets"
  | "di-women-rings"
  | "di-women-dior-tribales"
  | "di-women-hats-gloves"
  | "di-women-hair-accessories"
  | "di-women-silk-scarves-mitzah"
  | "di-women-scarves-shawls"
  | "di-women-beach-accessories"
  | "di-women-key-rings"
  | "di-women-slg"
  | "di-women-slg-all"
  | "di-women-card-holders"
  | "di-women-wallets"
  | "di-women-pouches"
  | "di-women-slg-tech"
  | "chanel-watches"
  | "ch-watches"
  | "ch-watches-j12"
  | "ch-watches-premiere"
  | "ch-watches-boy-friend"
  | "ch-watches-monsieur"
  | "ch-watches-code-coco";

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

/** Chanel High Jewellery (official GB https://www.chanel.com/gb/high-jewellery/). */
export const CH_HIGH_JEWELLERY_LEAF_IDS: SubcategoryId[] = ["ch-high-jewellery"];

/** Chanel watches collection leaves (official GB Watches Collections PLPs). */
export const CH_WATCH_LEAF_IDS: SubcategoryId[] = [
  "ch-watches-j12",
  "ch-watches-premiere",
  "ch-watches-boy-friend",
  "ch-watches-monsieur",
  "ch-watches-code-coco",
];

/** Chanel Fine Jewellery (official GB https://www.chanel.com/gb/fine-jewellery/). */
export const CH_FINE_JEWELLERY_LEAF_IDS: SubcategoryId[] = ["ch-fine-jewellery"];

/** Chanel sunglasses (official GB See All Sunglasses PLP). */
export const CH_SUNGLASSES_LEAF_IDS: SubcategoryId[] = ["ch-women-sunglasses"];

/** Chanel fragrance (official GB https://www.chanel.com/gb/fragrance/). */
export const CH_FRAGRANCE_LEAF_IDS: SubcategoryId[] = ["ch-fragrance"];

/** Chanel makeup group hubs (official GB https://www.chanel.com/gb/makeup/). */
export const CH_MAKEUP_GROUP_IDS: SubcategoryId[] = [
  "ch-makeup-complexion",
  "ch-makeup-eyes",
  "ch-makeup-lips",
  "ch-makeup-nails",
  "ch-makeup-brushes",
];

export const CH_MAKEUP_COMPLEXION_LEAF_IDS: SubcategoryId[] = [
  "ch-makeup-foundations",
  "ch-makeup-base",
  "ch-makeup-healthy-glow",
  "ch-makeup-blush",
  "ch-makeup-powders",
  "ch-makeup-bronzers",
  "ch-makeup-concealer",
  "ch-makeup-highlighter",
];

export const CH_MAKEUP_EYE_LEAF_IDS: SubcategoryId[] = [
  "ch-makeup-eyeshadows",
  "ch-makeup-mascara",
  "ch-makeup-brows",
  "ch-makeup-eyeliners",
  "ch-makeup-eye-palette",
];

export const CH_MAKEUP_LIP_LEAF_IDS: SubcategoryId[] = [
  "ch-makeup-lip-gloss",
  "ch-makeup-lipsticks",
  "ch-makeup-lip-pencils",
  "ch-makeup-lip-balms",
  "ch-makeup-liquid-lipsticks",
];

export const CH_MAKEUP_NAIL_LEAF_IDS: SubcategoryId[] = [
  "ch-makeup-manicure",
  "ch-makeup-nail-colour",
];

export const CH_MAKEUP_BRUSH_LEAF_IDS: SubcategoryId[] = [
  "ch-makeup-eye-brushes",
  "ch-makeup-complexion-brushes",
  "ch-makeup-lip-brushes",
];

export const CH_MAKEUP_LEAF_IDS: SubcategoryId[] = [
  ...CH_MAKEUP_GROUP_IDS,
  ...CH_MAKEUP_COMPLEXION_LEAF_IDS,
  ...CH_MAKEUP_EYE_LEAF_IDS,
  ...CH_MAKEUP_LIP_LEAF_IDS,
  ...CH_MAKEUP_NAIL_LEAF_IDS,
  ...CH_MAKEUP_BRUSH_LEAF_IDS,
];

/** Chanel skincare product-type leaves (official GB https://www.chanel.com/gb/skincare/). */
export const CH_SKINCARE_LEAF_IDS: SubcategoryId[] = [
  "ch-skincare-cleansers",
  "ch-skincare-serums",
  "ch-skincare-moisturisers",
  "ch-skincare-eyes-lips",
  "ch-skincare-body",
  "ch-skincare-masks",
  "ch-skincare-oils",
  "ch-skincare-protection",
  "ch-skincare-toners",
  "ch-skincare-mists",
];

/** Chanel other accessories leaves (official GB other-accessories PLPs). */
export const CH_OTHER_ACC_LEAF_IDS: SubcategoryId[] = [
  "ch-women-headwear",
  "ch-women-belts",
  "ch-women-scarves",
  "ch-women-camellias",
  "ch-women-winter-accessories",
  "ch-women-summer-accessories",
];

/** Louis Vuitton Home — furniture & lighting leaves (GB PLPs under 가구와 라이트닝). */
export const LV_FURNITURE_LEAF_IDS: SubcategoryId[] = [
  "lv-furniture-lighting-all",
  "lv-seating",
  "lv-tables",
  "lv-lighting",
  "lv-storage",
];

/** Dior Maison — tableware leaves (official GB Art de la Table PLPs). */
export const DI_TABLEWARE_LEAF_IDS: SubcategoryId[] = [
  "di-tableware-all",
  "di-plates-bowls",
  "di-glasses",
  "di-carafes",
  "di-tea-coffee",
  "di-cutlery",
];

/** Dior Maison — objects leaves (official GB Objects PLPs). */
export const DI_OBJECTS_LEAF_IDS: SubcategoryId[] = [
  "di-objects-all",
  "di-books",
  "di-notebooks",
  "di-desk-accessories",
  "di-candleholders-candles",
  "di-small-objects",
  "di-trinket-trays",
  "di-trays",
  "di-leisure",
  "di-paperweights",
];

/** Dior Maison — decor leaves (official GB Decor PLPs). */
export const DI_DECOR_LEAF_IDS: SubcategoryId[] = [
  "di-decor-all",
  "di-decorative-pieces",
  "di-lighting",
  "di-baskets",
  "di-wallpapers",
  "di-vases",
  "di-furniture",
];

/** Dior Maison — textile leaves (official GB Textile PLPs). */
export const DI_TEXTILE_LEAF_IDS: SubcategoryId[] = [
  "di-textile-all",
  "di-cushions",
  "di-bath-linen",
  "di-table-linen",
  "di-throws",
];

/** Dior Jewelry & Timepieces — jewelry-by-category + Dior Icons leaves (official GB). */
export const DI_JEWELRY_LEAF_IDS: SubcategoryId[] = [
  "di-jewelry-all",
  "di-earrings",
  "di-bracelets",
  "di-rings",
  "di-necklaces",
  "di-dior-icons",
];

/** Dior Watches — timepieces-by-collection leaves (official GB). */
export const DI_TIMEPIECE_LEAF_IDS: SubcategoryId[] = [
  "di-timepieces-all",
  "di-la-d-de-dior",
  "di-straps",
];

/** Dior Accessorize Your Bag leaves (official GB category.lvl2). */
export const DI_ACCESSORIZE_BAG_LEAF_IDS: SubcategoryId[] = [
  "di-acc-bag-jewelry",
  "di-acc-bag-totes",
  "di-acc-bag-mini",
  "di-acc-bag-shoulder",
  "di-acc-bag-bucket",
  "di-acc-bag-clutches",
  "di-acc-bag-key-rings",
  "di-acc-bag-mitzah",
  "di-acc-bag-purse",
];

/** Dior women's bags by category (official GB bags PLPs). */
export const DI_BAGS_WOMEN_LEAF_IDS: SubcategoryId[] = [
  "di-bags-all",
  "di-handbags",
  "di-crossbody-shoulder-bags",
  "di-tote-bags",
  "di-bucket-bags",
  "di-clutches",
  "di-mini-bags",
  "di-accessorize-bag",
  ...DI_ACCESSORIZE_BAG_LEAF_IDS,
];

/** Dior men's bags by category (official GB mens bags PLPs). */
export const DI_BAGS_MEN_LEAF_IDS: SubcategoryId[] = [
  "di-men-bags-all",
  "di-men-crossbody-shoulder-bags",
  "di-men-backpacks",
  "di-men-small-bags",
  "di-men-tote-bags",
  "di-men-travel-bags",
  "di-men-briefcases",
  "di-men-accessorize-bag",
];


/** Dior men's ready-to-wear by category (official GB mens RTW PLPs). */
export const DI_MEN_RTW_LEAF_IDS: SubcategoryId[] = [
  "di-men-rtw-all",
  "di-men-tshirts-polos",
  "di-men-shirts",
  "di-men-knitwear-sweatshirts",
  "di-men-trousers-shorts",
  "di-men-denim",
  "di-men-beachwear",
  "di-men-outerwear",
  "di-men-tailored-jackets",
  "di-men-leather",
  "di-men-suits-tuxedos",
];

/** Dior women's ready-to-wear by category (official GB womens RTW PLPs). */
export const DI_WOMEN_RTW_LEAF_IDS: SubcategoryId[] = [
  "di-women-rtw-all",
  "di-women-tshirts",
  "di-women-shirts",
  "di-women-sweaters-cardigans",
  "di-women-dresses",
  "di-women-skirts",
  "di-women-trousers-shorts",
  "di-women-denim",
  "di-women-swimsuits",
  "di-women-homewear-lingerie",
  "di-women-coats",
  "di-women-jackets",
];

/** Dior men's shoes (official GB all-shoes PLPs). */
export const DI_MEN_SHOES_LEAF_IDS: SubcategoryId[] = [
  "di-men-shoes-all",
  "di-men-sneakers",
  "di-men-sandals-mules",
  "di-men-loafers",
  "di-men-lace-ups",
  "di-men-boots",
];

/** Dior men's accessories (official GB all-accessories PLPs). */
export const DI_MEN_ACCESSORIES_LEAF_IDS: SubcategoryId[] = [
  "di-men-acc-all",
  "di-men-sunglasses",
  "di-men-belts",
  "di-men-ties-pocket-squares",
  "di-men-scarves",
  "di-men-hats-gloves",
  "di-men-socks",
  "di-men-fashion-jewelry",
  "di-men-silver-jewelry",
  "di-men-key-rings",
  "di-men-charm-jewelry",
  "di-men-lifestyle",
  "di-men-acc-tech",
  "di-men-pet-accessories",
];

/** Dior men's small leather goods (official GB mens SLG PLPs). */
export const DI_MEN_SLG_LEAF_IDS: SubcategoryId[] = [
  "di-men-slg-all",
  "di-men-card-holders",
  "di-men-compact-wallets",
  "di-men-long-wallets",
  "di-men-pouches",
  "di-men-tech-accessories",
];

/** Dior women's accessories (official GB all-accessories PLPs). */
export const DI_WOMEN_ACCESSORIES_LEAF_IDS: SubcategoryId[] = [
  "di-women-acc-all",
  "di-women-sunglasses",
  "di-women-optical-glasses",
  "di-women-belts",
  "di-women-hats-gloves",
  "di-women-hair-accessories",
  "di-women-silk-scarves-mitzah",
  "di-women-scarves-shawls",
  "di-women-beach-accessories",
  "di-women-key-rings",
];

/** Dior women's fashion jewellery (official GB womens-fashion leaves). */
export const DI_WOMEN_JEWELRY_LEAF_IDS: SubcategoryId[] = [
  "di-women-jewelry-all",
  "di-women-earrings",
  "di-women-necklaces",
  "di-women-brooches",
  "di-women-bracelets",
  "di-women-rings",
  "di-women-dior-tribales",
];

/** Dior women's small leather goods (official GB womens SLG PLPs). */
export const DI_WOMEN_SLG_LEAF_IDS: SubcategoryId[] = [
  "di-women-slg-all",
  "di-women-card-holders",
  "di-women-wallets",
  "di-women-pouches",
  "di-women-slg-tech",
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

/** Prada women's handbags leaf collections (official GB bags PLPs). */
export const PR_HANDBAG_LEAF_IDS: SubcategoryId[] = [
  "pr-women-shoulder-bags",
  "pr-women-top-handle-bags",
  "pr-women-tote-bags",
  "pr-women-mini-bags",
  "pr-women-backpacks",
  "pr-women-briefcases",
];

/** Prada men's handbags leaf collections (official GB bags PLPs). */
export const PR_MENS_HANDBAG_LEAF_IDS: SubcategoryId[] = [
  "pr-men-backpacks-belt-bags",
  "pr-men-briefcases",
  "pr-men-clutches",
  "pr-men-messenger-bags",
  "pr-men-tote-bags",
];

/** Prada women's travel leaves (official GB travel PLPs). */
export const PR_WOMEN_TRAVEL_LEAF_IDS: SubcategoryId[] = [
  "pr-women-travel-bags",
  "pr-women-luggage-carry-on",
  "pr-women-travel-accessories",
];

/** Prada men's travel leaves (official GB travel PLPs). */
export const PR_MEN_TRAVEL_LEAF_IDS: SubcategoryId[] = [
  "pr-men-travel-bags",
  "pr-men-luggage-carry-on",
  "pr-men-travel-accessories",
];

/** Prada women's ready-to-wear leaves (official GB RTW PLPs). */
export const PR_WOMEN_RTW_LEAF_IDS: SubcategoryId[] = [
  "pr-women-knitwear",
  "pr-women-shirts-tops",
  "pr-women-tshirts-sweatshirts",
  "pr-women-dresses",
  "pr-women-skirts",
  "pr-women-trousers-shorts",
  "pr-women-denim",
  "pr-women-jackets-coats",
  "pr-women-outerwear",
  "pr-women-leather",
  "pr-women-swimwear",
  "pr-women-pajamas-underwear",
];

/** Prada men's ready-to-wear leaves (official GB RTW PLPs). */
export const PR_MEN_RTW_LEAF_IDS: SubcategoryId[] = [
  "pr-men-denim",
  "pr-men-jackets-coats",
  "pr-men-jogging-suits-sweatshirts",
  "pr-men-knitwear",
  "pr-men-leather",
  "pr-men-outerwear",
  "pr-men-pajamas-underwear",
  "pr-men-shirts",
  "pr-men-suits",
  "pr-men-swimwear",
  "pr-men-trousers-bermudas",
  "pr-men-tshirts-polos",
];

export const PR_WOMEN_SHOE_LEAF_IDS: SubcategoryId[] = [
  "pr-women-ankle-boots-boots",
  "pr-women-loafers-lace-ups",
  "pr-women-pumps-ballerinas",
  "pr-women-sneakers",
  "pr-women-sandals-mules",
  "pr-women-new-formal",
  "pr-women-chocolate",
];

/** Prada men's shoes leaves (official GB men's shoes PLPs). */
export const PR_MEN_SHOE_LEAF_IDS: SubcategoryId[] = [
  "pr-men-loafers",
  "pr-men-sneakers",
  "pr-men-sandals",
  "pr-men-lace-ups",
  "pr-men-boots",
  "pr-men-americas-cup",
];

/** Prada women's small leather goods leaves (official GB SLG PLPs). */
export const PR_WOMEN_SLG_LEAF_IDS: SubcategoryId[] = [
  "pr-women-card-holders",
  "pr-women-small-wallets",
  "pr-women-large-wallets",
  "pr-women-wallets-on-chain",
  "pr-women-high-tech-accessories",
];

/** Prada men's small leather goods leaves (official GB SLG PLPs under 10346EU). */
export const PR_MEN_SLG_LEAF_IDS: SubcategoryId[] = [
  "pr-men-card-holders",
  "pr-men-small-wallets",
  "pr-men-large-wallets",
  "pr-men-high-tech-accessories",
];

/** Prada men's accessories leaves (official GB accessories PLPs, excl. SLG hub). */
export const PR_MEN_ACCESSORIES_LEAF_IDS: SubcategoryId[] = [
  "pr-men-sunglasses",
  "pr-men-hats-gloves",
  "pr-men-bag-charms",
  "pr-men-belts",
  "pr-men-custom-belts",
  "pr-men-silks-scarves",
  "pr-men-ties-bow-ties",
  "pr-men-jewels",
];

/** Prada Linea Rossa leaves (official GB landing + hub menu PLPs). */
export const PR_LINEA_ROSSA_LEAF_IDS: SubcategoryId[] = [
  "pr-linea-rossa-women",
  "pr-linea-rossa-men",
  "pr-linea-rossa-sunglasses",
  "pr-linea-rossa-shoes",
  "pr-linea-rossa-fragrances",
];

/** Prada Beauty leaves (official GB beauty PLPs under 10565EU). */
export const PR_BEAUTY_LEAF_IDS: SubcategoryId[] = [
  "pr-beauty-face",
  "pr-beauty-eyes",
  "pr-beauty-lips",
  "pr-beauty-skincare",
  "pr-beauty-brushes",
];

/** Prada Fragrances leaves (official GB fragrance PLPs under 10566EU). */
export const PR_FRAGRANCE_LEAF_IDS: SubcategoryId[] = [
  "pr-fragrances-women",
  "pr-fragrances-men",
  "pr-fragrances-exclusive",
];

/** Prada Fine Jewelry leaves (official GB categories hub 10628EU). */
export const PR_FINE_JEWELRY_LEAF_IDS: SubcategoryId[] = [
  "pr-fine-jewelry-bracelets",
  "pr-fine-jewelry-necklaces",
  "pr-fine-jewelry-rings",
  "pr-fine-jewelry-earrings-brooches",
];

/** Prada women's accessories leaves (official GB accessories PLPs, excl. SLG hub). */
export const PR_WOMEN_ACCESSORIES_LEAF_IDS: SubcategoryId[] = [
  "pr-women-sunglasses",
  "pr-women-silks-scarves",
  "pr-women-hats-gloves",
  "pr-women-headbands-hair",
  "pr-women-bag-charms",
  "pr-women-jewels",
  "pr-women-belts",
  "pr-women-pouches",
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

/** Expands group subcategory ids (e.g. brand hubs → leaf collection ids). */
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
  "prada-bags": [
    "prada-bags",
    "pr-handbags",
    ...PR_HANDBAG_LEAF_IDS,
    "pr-women-travel",
    ...PR_WOMEN_TRAVEL_LEAF_IDS,
    "pr-mens-handbags",
    ...PR_MENS_HANDBAG_LEAF_IDS,
    "pr-men-travel",
    ...PR_MEN_TRAVEL_LEAF_IDS,
  ],
  prada: [
    "prada",
    "prada-luxury",
    "pr-women",
    "pr-women-rtw",
    ...PR_WOMEN_RTW_LEAF_IDS,
    "pr-men",
    "pr-men-rtw",
    ...PR_MEN_RTW_LEAF_IDS,
    "prada-bags",
    "pr-handbags",
    ...PR_HANDBAG_LEAF_IDS,
    "pr-women-travel",
    ...PR_WOMEN_TRAVEL_LEAF_IDS,
    "pr-mens-handbags",
    ...PR_MENS_HANDBAG_LEAF_IDS,
    "pr-men-travel",
    ...PR_MEN_TRAVEL_LEAF_IDS,
    "prada-shoes",
    "pr-women-shoes",
    ...PR_WOMEN_SHOE_LEAF_IDS,
    "pr-men-shoes",
    ...PR_MEN_SHOE_LEAF_IDS,
    "prada-accessories",
    "pr-women-accessories",
    ...PR_WOMEN_ACCESSORIES_LEAF_IDS,
    "pr-women-slg",
    ...PR_WOMEN_SLG_LEAF_IDS,
    "pr-mens-accessories",
    "pr-mens-slg",
    ...PR_MEN_SLG_LEAF_IDS,
    ...PR_MEN_ACCESSORIES_LEAF_IDS,
    "pr-linea-rossa",
    ...PR_LINEA_ROSSA_LEAF_IDS,
    "pr-beauty",
    ...PR_BEAUTY_LEAF_IDS,
    "pr-fragrances",
    ...PR_FRAGRANCE_LEAF_IDS,
    "pr-fine-jewelry",
    ...PR_FINE_JEWELRY_LEAF_IDS,
  ],
  "prada-luxury": [
    "prada-luxury",
    "pr-women",
    "pr-women-rtw",
    ...PR_WOMEN_RTW_LEAF_IDS,
    "pr-men",
    "pr-men-rtw",
    ...PR_MEN_RTW_LEAF_IDS,
  ],
  "pr-women": ["pr-women", "pr-women-rtw", ...PR_WOMEN_RTW_LEAF_IDS],
  "pr-men": ["pr-men", "pr-men-rtw", ...PR_MEN_RTW_LEAF_IDS],
  "pr-men-rtw": ["pr-men-rtw", ...PR_MEN_RTW_LEAF_IDS],
  "pr-men-denim": ["pr-men-denim"],
  "pr-men-jackets-coats": ["pr-men-jackets-coats"],
  "pr-men-jogging-suits-sweatshirts": ["pr-men-jogging-suits-sweatshirts"],
  "pr-men-knitwear": ["pr-men-knitwear"],
  "pr-men-leather": ["pr-men-leather"],
  "pr-men-outerwear": ["pr-men-outerwear"],
  "pr-men-pajamas-underwear": ["pr-men-pajamas-underwear"],
  "pr-men-shirts": ["pr-men-shirts"],
  "pr-men-suits": ["pr-men-suits"],
  "pr-men-swimwear": ["pr-men-swimwear"],
  "pr-men-trousers-bermudas": ["pr-men-trousers-bermudas"],
  "pr-men-tshirts-polos": ["pr-men-tshirts-polos"],
  "pr-women-rtw": ["pr-women-rtw", ...PR_WOMEN_RTW_LEAF_IDS],
  "pr-women-knitwear": ["pr-women-knitwear"],
  "pr-women-shirts-tops": ["pr-women-shirts-tops"],
  "pr-women-tshirts-sweatshirts": ["pr-women-tshirts-sweatshirts"],
  "pr-women-dresses": ["pr-women-dresses"],
  "pr-women-skirts": ["pr-women-skirts"],
  "pr-women-trousers-shorts": ["pr-women-trousers-shorts"],
  "pr-women-denim": ["pr-women-denim"],
  "pr-women-jackets-coats": ["pr-women-jackets-coats"],
  "pr-women-outerwear": ["pr-women-outerwear"],
  "pr-women-leather": ["pr-women-leather"],
  "pr-women-swimwear": ["pr-women-swimwear"],
  "pr-women-pajamas-underwear": ["pr-women-pajamas-underwear"],
  "pr-handbags": [
    "pr-handbags",
    ...PR_HANDBAG_LEAF_IDS,
    "pr-women-travel",
    ...PR_WOMEN_TRAVEL_LEAF_IDS,
  ],
  "pr-women-shoulder-bags": ["pr-women-shoulder-bags"],
  "pr-women-top-handle-bags": ["pr-women-top-handle-bags"],
  "pr-women-tote-bags": ["pr-women-tote-bags"],
  "pr-women-mini-bags": ["pr-women-mini-bags"],
  "pr-women-backpacks": ["pr-women-backpacks"],
  "pr-women-briefcases": ["pr-women-briefcases"],
  "pr-women-travel": ["pr-women-travel", ...PR_WOMEN_TRAVEL_LEAF_IDS],
  "pr-women-travel-bags": ["pr-women-travel-bags"],
  "pr-women-luggage-carry-on": ["pr-women-luggage-carry-on"],
  "pr-women-travel-accessories": ["pr-women-travel-accessories"],
  "pr-mens-handbags": [
    "pr-mens-handbags",
    ...PR_MENS_HANDBAG_LEAF_IDS,
    "pr-men-travel",
    ...PR_MEN_TRAVEL_LEAF_IDS,
  ],
  "pr-men-backpacks-belt-bags": ["pr-men-backpacks-belt-bags"],
  "pr-men-briefcases": ["pr-men-briefcases"],
  "pr-men-clutches": ["pr-men-clutches"],
  "pr-men-messenger-bags": ["pr-men-messenger-bags"],
  "pr-men-tote-bags": ["pr-men-tote-bags"],
  "pr-men-travel": ["pr-men-travel", ...PR_MEN_TRAVEL_LEAF_IDS],
  "pr-men-travel-bags": ["pr-men-travel-bags"],
  "pr-men-luggage-carry-on": ["pr-men-luggage-carry-on"],
  "pr-men-travel-accessories": ["pr-men-travel-accessories"],
  "prada-shoes": [
    "prada-shoes",
    "pr-women-shoes",
    ...PR_WOMEN_SHOE_LEAF_IDS,
    "pr-men-shoes",
    ...PR_MEN_SHOE_LEAF_IDS,
  ],
  "pr-women-shoes": ["pr-women-shoes", ...PR_WOMEN_SHOE_LEAF_IDS],
  "pr-women-ankle-boots-boots": ["pr-women-ankle-boots-boots"],
  "pr-women-loafers-lace-ups": ["pr-women-loafers-lace-ups"],
  "pr-women-pumps-ballerinas": ["pr-women-pumps-ballerinas"],
  "pr-women-sneakers": ["pr-women-sneakers"],
  "pr-women-sandals-mules": ["pr-women-sandals-mules"],
  "pr-women-new-formal": ["pr-women-new-formal"],
  "pr-women-chocolate": ["pr-women-chocolate"],
  "pr-men-shoes": ["pr-men-shoes", ...PR_MEN_SHOE_LEAF_IDS],
  "pr-men-loafers": ["pr-men-loafers"],
  "pr-men-sneakers": ["pr-men-sneakers"],
  "pr-men-sandals": ["pr-men-sandals"],
  "pr-men-lace-ups": ["pr-men-lace-ups"],
  "pr-men-boots": ["pr-men-boots"],
  "pr-men-americas-cup": ["pr-men-americas-cup"],
  "prada-accessories": [
    "prada-accessories",
    "pr-women-accessories",
    ...PR_WOMEN_ACCESSORIES_LEAF_IDS,
    "pr-women-slg",
    ...PR_WOMEN_SLG_LEAF_IDS,
    "pr-mens-accessories",
    "pr-mens-slg",
    ...PR_MEN_SLG_LEAF_IDS,
    ...PR_MEN_ACCESSORIES_LEAF_IDS,
    "pr-linea-rossa",
    ...PR_LINEA_ROSSA_LEAF_IDS,
    "pr-beauty",
    ...PR_BEAUTY_LEAF_IDS,
    "pr-fragrances",
    ...PR_FRAGRANCE_LEAF_IDS,
    "pr-fine-jewelry",
    ...PR_FINE_JEWELRY_LEAF_IDS,
  ],
  "pr-women-accessories": [
    "pr-women-accessories",
    ...PR_WOMEN_ACCESSORIES_LEAF_IDS,
    "pr-women-slg",
    ...PR_WOMEN_SLG_LEAF_IDS,
  ],
  "pr-mens-accessories": [
    "pr-mens-accessories",
    "pr-mens-slg",
    ...PR_MEN_SLG_LEAF_IDS,
    ...PR_MEN_ACCESSORIES_LEAF_IDS,
  ],
  "pr-mens-slg": ["pr-mens-slg", ...PR_MEN_SLG_LEAF_IDS],
  "pr-men-card-holders": ["pr-men-card-holders"],
  "pr-men-small-wallets": ["pr-men-small-wallets"],
  "pr-men-large-wallets": ["pr-men-large-wallets"],
  "pr-men-high-tech-accessories": ["pr-men-high-tech-accessories"],
  "pr-men-sunglasses": ["pr-men-sunglasses"],
  "pr-men-hats-gloves": ["pr-men-hats-gloves"],
  "pr-men-bag-charms": ["pr-men-bag-charms"],
  "pr-men-belts": ["pr-men-belts"],
  "pr-men-custom-belts": ["pr-men-custom-belts"],
  "pr-men-silks-scarves": ["pr-men-silks-scarves"],
  "pr-men-ties-bow-ties": ["pr-men-ties-bow-ties"],
  "pr-men-jewels": ["pr-men-jewels"],
  "pr-linea-rossa": ["pr-linea-rossa", ...PR_LINEA_ROSSA_LEAF_IDS],
  "pr-linea-rossa-women": ["pr-linea-rossa-women"],
  "pr-linea-rossa-men": ["pr-linea-rossa-men"],
  "pr-linea-rossa-sunglasses": ["pr-linea-rossa-sunglasses"],
  "pr-linea-rossa-shoes": ["pr-linea-rossa-shoes"],
  "pr-linea-rossa-fragrances": ["pr-linea-rossa-fragrances"],
  "pr-beauty": ["pr-beauty", ...PR_BEAUTY_LEAF_IDS],
  "pr-beauty-face": ["pr-beauty-face"],
  "pr-beauty-eyes": ["pr-beauty-eyes"],
  "pr-beauty-lips": ["pr-beauty-lips"],
  "pr-beauty-skincare": ["pr-beauty-skincare"],
  "pr-beauty-brushes": ["pr-beauty-brushes"],
  "pr-fragrances": ["pr-fragrances", ...PR_FRAGRANCE_LEAF_IDS],
  "pr-fragrances-women": ["pr-fragrances-women"],
  "pr-fragrances-men": ["pr-fragrances-men"],
  "pr-fragrances-exclusive": ["pr-fragrances-exclusive"],
  "pr-fine-jewelry": ["pr-fine-jewelry", ...PR_FINE_JEWELRY_LEAF_IDS],
  "pr-fine-jewelry-bracelets": ["pr-fine-jewelry-bracelets"],
  "pr-fine-jewelry-necklaces": ["pr-fine-jewelry-necklaces"],
  "pr-fine-jewelry-rings": ["pr-fine-jewelry-rings"],
  "pr-fine-jewelry-earrings-brooches": ["pr-fine-jewelry-earrings-brooches"],
  "pr-women-sunglasses": ["pr-women-sunglasses"],
  "pr-women-silks-scarves": ["pr-women-silks-scarves"],
  "pr-women-hats-gloves": ["pr-women-hats-gloves"],
  "pr-women-headbands-hair": ["pr-women-headbands-hair"],
  "pr-women-bag-charms": ["pr-women-bag-charms"],
  "pr-women-jewels": ["pr-women-jewels"],
  "pr-women-belts": ["pr-women-belts"],
  "pr-women-pouches": ["pr-women-pouches"],
  "pr-women-slg": ["pr-women-slg", ...PR_WOMEN_SLG_LEAF_IDS],
  "pr-women-card-holders": ["pr-women-card-holders"],
  "pr-women-small-wallets": ["pr-women-small-wallets"],
  "pr-women-large-wallets": ["pr-women-large-wallets"],
  "pr-women-wallets-on-chain": ["pr-women-wallets-on-chain"],
  "pr-women-high-tech-accessories": ["pr-women-high-tech-accessories"],
  "chanel-bags": [
    "chanel-bags",
    "ch-handbags",
    ...CH_HANDBAG_LEAF_IDS,
  ],
  "ch-handbags": ["ch-handbags", ...CH_HANDBAG_LEAF_IDS],
  "ch-women-flap-bags": ["ch-women-flap-bags"],
  "ch-women-hobo-bags": ["ch-women-hobo-bags"],
  "ch-women-tote-bowling-bags": ["ch-women-tote-bowling-bags"],
  "ch-women-bucket-bags": ["ch-women-bucket-bags"],
  "ch-women-backpacks": ["ch-women-backpacks"],
  "ch-women-evening-bags": ["ch-women-evening-bags"],
  "ch-women-mini-bags": ["ch-women-mini-bags"],
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
    ...CH_HIGH_JEWELLERY_LEAF_IDS,
    ...CH_FINE_JEWELLERY_LEAF_IDS,
    "ch-slg",
    ...CH_SLG_LEAF_IDS,
    "ch-sunglasses",
    ...CH_SUNGLASSES_LEAF_IDS,
    "ch-fragrance",
    ...CH_FRAGRANCE_LEAF_IDS,
    "ch-makeup",
    ...CH_MAKEUP_LEAF_IDS,
    "ch-skincare",
    ...CH_SKINCARE_LEAF_IDS,
    "ch-other-accessories",
    ...CH_OTHER_ACC_LEAF_IDS,
  ],
  "louis-vuitton": [
    "louis-vuitton",
    "louis-vuitton-accessories",
    "lv-home-lifestyle",
    "lv-furniture-lighting",
    ...LV_FURNITURE_LEAF_IDS,
  ],
  "louis-vuitton-accessories": [
    "louis-vuitton-accessories",
    "lv-home-lifestyle",
    "lv-furniture-lighting",
    ...LV_FURNITURE_LEAF_IDS,
  ],
  "lv-home-lifestyle": [
    "lv-home-lifestyle",
    "lv-furniture-lighting",
    ...LV_FURNITURE_LEAF_IDS,
  ],
  "lv-furniture-lighting": ["lv-furniture-lighting", ...LV_FURNITURE_LEAF_IDS],
  "lv-furniture-lighting-all": ["lv-furniture-lighting-all"],
  "lv-seating": ["lv-seating"],
  "lv-tables": ["lv-tables"],
  "lv-lighting": ["lv-lighting"],
  "lv-storage": ["lv-storage"],
  dior: [
    "dior",
    "dior-accessories",
    "di-home",
    "di-tableware",
    ...DI_TABLEWARE_LEAF_IDS,
    "di-objects",
    ...DI_OBJECTS_LEAF_IDS,
    "di-decor",
    ...DI_DECOR_LEAF_IDS,
    "di-textile",
    ...DI_TEXTILE_LEAF_IDS,
    "di-jewelry-timepieces",
    ...DI_JEWELRY_LEAF_IDS,
    "dior-bags",
    "di-bags-womens",
    ...DI_BAGS_WOMEN_LEAF_IDS,
    "di-bags-mens",
    ...DI_BAGS_MEN_LEAF_IDS,
    "di-mens",
    ...DI_MEN_RTW_LEAF_IDS,
    "di-womens",
    ...DI_WOMEN_RTW_LEAF_IDS,
    "dior-shoes",
    "di-men-shoes",
    ...DI_MEN_SHOES_LEAF_IDS,
  ],
  "dior-shoes": [
    "dior-shoes",
    "di-men-shoes",
    ...DI_MEN_SHOES_LEAF_IDS,
  ],
  "di-men-shoes": ["di-men-shoes", ...DI_MEN_SHOES_LEAF_IDS],
  "di-men-shoes-all": ["di-men-shoes-all"],
  "di-men-sneakers": ["di-men-sneakers"],
  "di-men-sandals-mules": ["di-men-sandals-mules"],
  "di-men-loafers": ["di-men-loafers"],
  "di-men-lace-ups": ["di-men-lace-ups"],
  "di-men-boots": ["di-men-boots"],
  "dior-accessories": [
    "dior-accessories",
    "di-home",
    "di-tableware",
    ...DI_TABLEWARE_LEAF_IDS,
    "di-objects",
    ...DI_OBJECTS_LEAF_IDS,
    "di-decor",
    ...DI_DECOR_LEAF_IDS,
    "di-textile",
    ...DI_TEXTILE_LEAF_IDS,
    "di-jewelry-timepieces",
    ...DI_JEWELRY_LEAF_IDS,
    "di-women-accessories",
    ...DI_WOMEN_ACCESSORIES_LEAF_IDS,
    "di-women-jewelry",
    ...DI_WOMEN_JEWELRY_LEAF_IDS,
    "di-women-slg",
    ...DI_WOMEN_SLG_LEAF_IDS,
    "di-men-accessories",
    ...DI_MEN_ACCESSORIES_LEAF_IDS,
    "di-men-slg",
    ...DI_MEN_SLG_LEAF_IDS,
  ],
  "di-home": [
    "di-home",
    "di-tableware",
    ...DI_TABLEWARE_LEAF_IDS,
    "di-objects",
    ...DI_OBJECTS_LEAF_IDS,
    "di-decor",
    ...DI_DECOR_LEAF_IDS,
    "di-textile",
    ...DI_TEXTILE_LEAF_IDS,
  ],
  "di-tableware": ["di-tableware", ...DI_TABLEWARE_LEAF_IDS],
  "di-tableware-all": ["di-tableware-all"],
  "di-plates-bowls": ["di-plates-bowls"],
  "di-glasses": ["di-glasses"],
  "di-carafes": ["di-carafes"],
  "di-tea-coffee": ["di-tea-coffee"],
  "di-cutlery": ["di-cutlery"],
  "di-objects": ["di-objects", ...DI_OBJECTS_LEAF_IDS],
  "di-objects-all": ["di-objects-all"],
  "di-books": ["di-books"],
  "di-notebooks": ["di-notebooks"],
  "di-desk-accessories": ["di-desk-accessories"],
  "di-candleholders-candles": ["di-candleholders-candles"],
  "di-small-objects": ["di-small-objects"],
  "di-trinket-trays": ["di-trinket-trays"],
  "di-trays": ["di-trays"],
  "di-leisure": ["di-leisure"],
  "di-paperweights": ["di-paperweights"],
  "di-decor": ["di-decor", ...DI_DECOR_LEAF_IDS],
  "di-decor-all": ["di-decor-all"],
  "di-decorative-pieces": ["di-decorative-pieces"],
  "di-lighting": ["di-lighting"],
  "di-baskets": ["di-baskets"],
  "di-wallpapers": ["di-wallpapers"],
  "di-vases": ["di-vases"],
  "di-furniture": ["di-furniture"],
  "di-textile": ["di-textile", ...DI_TEXTILE_LEAF_IDS],
  "di-textile-all": ["di-textile-all"],
  "di-cushions": ["di-cushions"],
  "di-bath-linen": ["di-bath-linen"],
  "di-table-linen": ["di-table-linen"],
  "di-throws": ["di-throws"],
  "di-jewelry-timepieces": [
    "di-jewelry-timepieces",
    ...DI_JEWELRY_LEAF_IDS,
  ],
  "di-jewelry-all": ["di-jewelry-all"],
  "di-earrings": ["di-earrings"],
  "di-bracelets": ["di-bracelets"],
  "di-rings": ["di-rings"],
  "di-necklaces": ["di-necklaces"],
  "di-dior-icons": ["di-dior-icons"],
  "dior-watches": ["dior-watches", ...DI_TIMEPIECE_LEAF_IDS],
  "di-timepieces-all": ["di-timepieces-all"],
  "di-la-d-de-dior": ["di-la-d-de-dior"],
  "di-straps": ["di-straps"],
  "dior-bags": [
    "dior-bags",
    "di-bags-womens",
    ...DI_BAGS_WOMEN_LEAF_IDS,
    "di-bags-mens",
    ...DI_BAGS_MEN_LEAF_IDS,
  ],
  "di-bags-womens": ["di-bags-womens", ...DI_BAGS_WOMEN_LEAF_IDS],
  "di-bags-all": ["di-bags-all"],
  "di-handbags": ["di-handbags"],
  "di-crossbody-shoulder-bags": ["di-crossbody-shoulder-bags"],
  "di-tote-bags": ["di-tote-bags"],
  "di-bucket-bags": ["di-bucket-bags"],
  "di-clutches": ["di-clutches"],
  "di-mini-bags": ["di-mini-bags"],
  "di-accessorize-bag": ["di-accessorize-bag", ...DI_ACCESSORIZE_BAG_LEAF_IDS],
  "di-acc-bag-jewelry": ["di-acc-bag-jewelry"],
  "di-acc-bag-totes": ["di-acc-bag-totes"],
  "di-acc-bag-mini": ["di-acc-bag-mini"],
  "di-acc-bag-shoulder": ["di-acc-bag-shoulder"],
  "di-acc-bag-bucket": ["di-acc-bag-bucket"],
  "di-acc-bag-clutches": ["di-acc-bag-clutches"],
  "di-acc-bag-key-rings": ["di-acc-bag-key-rings"],
  "di-acc-bag-mitzah": ["di-acc-bag-mitzah"],
  "di-acc-bag-purse": ["di-acc-bag-purse"],
  "di-bags-mens": ["di-bags-mens", ...DI_BAGS_MEN_LEAF_IDS],
  "di-men-bags-all": ["di-men-bags-all"],
  "di-men-crossbody-shoulder-bags": ["di-men-crossbody-shoulder-bags"],
  "di-men-backpacks": ["di-men-backpacks"],
  "di-men-small-bags": ["di-men-small-bags"],
  "di-men-tote-bags": ["di-men-tote-bags"],
  "di-men-travel-bags": ["di-men-travel-bags"],
  "di-men-briefcases": ["di-men-briefcases"],
  "di-men-accessorize-bag": ["di-men-accessorize-bag"],

  "di-mens": ["di-mens", ...DI_MEN_RTW_LEAF_IDS],
  "di-womens": ["di-womens", ...DI_WOMEN_RTW_LEAF_IDS],
  "di-women-rtw-all": ["di-women-rtw-all"],
  "di-women-tshirts": ["di-women-tshirts"],
  "di-women-shirts": ["di-women-shirts"],
  "di-women-sweaters-cardigans": ["di-women-sweaters-cardigans"],
  "di-women-dresses": ["di-women-dresses"],
  "di-women-skirts": ["di-women-skirts"],
  "di-women-trousers-shorts": ["di-women-trousers-shorts"],
  "di-women-denim": ["di-women-denim"],
  "di-women-swimsuits": ["di-women-swimsuits"],
  "di-women-homewear-lingerie": ["di-women-homewear-lingerie"],
  "di-women-coats": ["di-women-coats"],
  "di-women-jackets": ["di-women-jackets"],
  "di-men-rtw-all": ["di-men-rtw-all"],
  "di-men-tshirts-polos": ["di-men-tshirts-polos"],
  "di-men-shirts": ["di-men-shirts"],
  "di-men-knitwear-sweatshirts": ["di-men-knitwear-sweatshirts"],
  "di-men-trousers-shorts": ["di-men-trousers-shorts"],
  "di-men-denim": ["di-men-denim"],
  "di-men-beachwear": ["di-men-beachwear"],
  "di-men-outerwear": ["di-men-outerwear"],
  "di-men-tailored-jackets": ["di-men-tailored-jackets"],
  "di-men-leather": ["di-men-leather"],
  "di-men-suits-tuxedos": ["di-men-suits-tuxedos"],
  "di-men-slg": ["di-men-slg", ...DI_MEN_SLG_LEAF_IDS],
  "di-men-slg-all": ["di-men-slg-all"],
  "di-women-accessories": [
    "di-women-accessories",
    ...DI_WOMEN_ACCESSORIES_LEAF_IDS,
    "di-women-jewelry",
    ...DI_WOMEN_JEWELRY_LEAF_IDS,
    "di-women-slg",
    ...DI_WOMEN_SLG_LEAF_IDS,
  ],
  "di-women-acc-all": ["di-women-acc-all"],
  "di-women-sunglasses": ["di-women-sunglasses"],
  "di-women-optical-glasses": ["di-women-optical-glasses"],
  "di-women-belts": ["di-women-belts"],
  "di-women-jewelry": ["di-women-jewelry", ...DI_WOMEN_JEWELRY_LEAF_IDS],
  "di-women-jewelry-all": ["di-women-jewelry-all"],
  "di-women-earrings": ["di-women-earrings"],
  "di-women-necklaces": ["di-women-necklaces"],
  "di-women-brooches": ["di-women-brooches"],
  "di-women-bracelets": ["di-women-bracelets"],
  "di-women-rings": ["di-women-rings"],
  "di-women-dior-tribales": ["di-women-dior-tribales"],
  "di-women-hats-gloves": ["di-women-hats-gloves"],
  "di-women-hair-accessories": ["di-women-hair-accessories"],
  "di-women-silk-scarves-mitzah": ["di-women-silk-scarves-mitzah"],
  "di-women-scarves-shawls": ["di-women-scarves-shawls"],
  "di-women-beach-accessories": ["di-women-beach-accessories"],
  "di-women-key-rings": ["di-women-key-rings"],
  "di-women-slg": ["di-women-slg", ...DI_WOMEN_SLG_LEAF_IDS],
  "di-women-slg-all": ["di-women-slg-all"],
  "di-women-card-holders": ["di-women-card-holders"],
  "di-women-wallets": ["di-women-wallets"],
  "di-women-pouches": ["di-women-pouches"],
  "di-women-slg-tech": ["di-women-slg-tech"],
  "di-men-accessories": [
    "di-men-accessories",
    ...DI_MEN_ACCESSORIES_LEAF_IDS,
    "di-men-slg",
    ...DI_MEN_SLG_LEAF_IDS,
  ],
  "di-men-acc-all": ["di-men-acc-all"],
  "di-men-sunglasses": ["di-men-sunglasses"],
  "di-men-belts": ["di-men-belts"],
  "di-men-ties-pocket-squares": ["di-men-ties-pocket-squares"],
  "di-men-scarves": ["di-men-scarves"],
  "di-men-hats-gloves": ["di-men-hats-gloves"],
  "di-men-socks": ["di-men-socks"],
  "di-men-fashion-jewelry": ["di-men-fashion-jewelry"],
  "di-men-silver-jewelry": ["di-men-silver-jewelry"],
  "di-men-key-rings": ["di-men-key-rings"],
  "di-men-charm-jewelry": ["di-men-charm-jewelry"],
  "di-men-lifestyle": ["di-men-lifestyle"],
  "di-men-acc-tech": ["di-men-acc-tech"],
  "di-men-pet-accessories": ["di-men-pet-accessories"],
  "di-men-card-holders": ["di-men-card-holders"],
  "di-men-compact-wallets": ["di-men-compact-wallets"],
  "di-men-long-wallets": ["di-men-long-wallets"],
  "di-men-pouches": ["di-men-pouches"],
  "di-men-tech-accessories": ["di-men-tech-accessories"],
  "ch-jewellery": ["ch-jewellery", ...CH_JEWELLERY_LEAF_IDS],
  "ch-high-jewellery": ["ch-high-jewellery"],
  "ch-fine-jewellery": ["ch-fine-jewellery"],
  "ch-women-earrings": ["ch-women-earrings"],
  "ch-women-necklaces": ["ch-women-necklaces"],
  "ch-women-bracelets-cuffs": ["ch-women-bracelets-cuffs"],
  "ch-women-brooches": ["ch-women-brooches"],
  "ch-women-rings": ["ch-women-rings"],
  "ch-slg": ["ch-slg", ...CH_SLG_LEAF_IDS],
  "ch-women-wallets-on-chain": ["ch-women-wallets-on-chain"],
  "ch-women-micro-bags": ["ch-women-micro-bags"],
  "ch-women-vanity": ["ch-women-vanity"],
  "ch-women-card-holders-wallets": ["ch-women-card-holders-wallets"],
  "ch-women-pouches-cases": ["ch-women-pouches-cases"],
  "ch-women-leather-accessories": ["ch-women-leather-accessories"],
  "ch-sunglasses": ["ch-sunglasses", ...CH_SUNGLASSES_LEAF_IDS],
  "ch-women-sunglasses": ["ch-women-sunglasses"],
  "ch-fragrance": ["ch-fragrance"],
  "ch-makeup": ["ch-makeup", ...CH_MAKEUP_LEAF_IDS],
  "ch-makeup-complexion": [
    "ch-makeup-complexion",
    ...CH_MAKEUP_COMPLEXION_LEAF_IDS,
  ],
  "ch-makeup-foundations": ["ch-makeup-foundations"],
  "ch-makeup-base": ["ch-makeup-base"],
  "ch-makeup-healthy-glow": ["ch-makeup-healthy-glow"],
  "ch-makeup-blush": ["ch-makeup-blush"],
  "ch-makeup-powders": ["ch-makeup-powders"],
  "ch-makeup-bronzers": ["ch-makeup-bronzers"],
  "ch-makeup-concealer": ["ch-makeup-concealer"],
  "ch-makeup-highlighter": ["ch-makeup-highlighter"],
  "ch-makeup-eyes": ["ch-makeup-eyes", ...CH_MAKEUP_EYE_LEAF_IDS],
  "ch-makeup-eyeshadows": ["ch-makeup-eyeshadows"],
  "ch-makeup-mascara": ["ch-makeup-mascara"],
  "ch-makeup-brows": ["ch-makeup-brows"],
  "ch-makeup-eyeliners": ["ch-makeup-eyeliners"],
  "ch-makeup-eye-palette": ["ch-makeup-eye-palette"],
  "ch-makeup-lips": ["ch-makeup-lips", ...CH_MAKEUP_LIP_LEAF_IDS],
  "ch-makeup-lip-gloss": ["ch-makeup-lip-gloss"],
  "ch-makeup-lipsticks": ["ch-makeup-lipsticks"],
  "ch-makeup-lip-pencils": ["ch-makeup-lip-pencils"],
  "ch-makeup-lip-balms": ["ch-makeup-lip-balms"],
  "ch-makeup-liquid-lipsticks": ["ch-makeup-liquid-lipsticks"],
  "ch-makeup-nails": ["ch-makeup-nails", ...CH_MAKEUP_NAIL_LEAF_IDS],
  "ch-makeup-manicure": ["ch-makeup-manicure"],
  "ch-makeup-nail-colour": ["ch-makeup-nail-colour"],
  "ch-makeup-brushes": ["ch-makeup-brushes", ...CH_MAKEUP_BRUSH_LEAF_IDS],
  "ch-makeup-eye-brushes": ["ch-makeup-eye-brushes"],
  "ch-makeup-complexion-brushes": ["ch-makeup-complexion-brushes"],
  "ch-makeup-lip-brushes": ["ch-makeup-lip-brushes"],
  "ch-skincare": ["ch-skincare", ...CH_SKINCARE_LEAF_IDS],
  "ch-skincare-cleansers": ["ch-skincare-cleansers"],
  "ch-skincare-serums": ["ch-skincare-serums"],
  "ch-skincare-moisturisers": ["ch-skincare-moisturisers"],
  "ch-skincare-eyes-lips": ["ch-skincare-eyes-lips"],
  "ch-skincare-body": ["ch-skincare-body"],
  "ch-skincare-masks": ["ch-skincare-masks"],
  "ch-skincare-oils": ["ch-skincare-oils"],
  "ch-skincare-protection": ["ch-skincare-protection"],
  "ch-skincare-toners": ["ch-skincare-toners"],
  "ch-skincare-mists": ["ch-skincare-mists"],
  "ch-other-accessories": ["ch-other-accessories", ...CH_OTHER_ACC_LEAF_IDS],
  "chanel-watches": ["chanel-watches", "ch-watches", ...CH_WATCH_LEAF_IDS],
  "ch-watches": ["ch-watches", ...CH_WATCH_LEAF_IDS],
  "ch-watches-j12": ["ch-watches-j12"],
  "ch-watches-premiere": ["ch-watches-premiere"],
  "ch-watches-boy-friend": ["ch-watches-boy-friend"],
  "ch-watches-monsieur": ["ch-watches-monsieur"],
  "ch-watches-code-coco": ["ch-watches-code-coco"],
  "ch-women-headwear": ["ch-women-headwear"],
  "ch-women-belts": ["ch-women-belts"],
  "ch-women-scarves": ["ch-women-scarves"],
  "ch-women-camellias": ["ch-women-camellias"],
  "ch-women-winter-accessories": ["ch-women-winter-accessories"],
  "ch-women-summer-accessories": ["ch-women-summer-accessories"],
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
  "arcteryx-accessories": [
    "ax-acc-womens",
    "ax-acc-mens",
    "ax-climbing-womens",
    "ax-climbing-mens",
  ],
  "ax-acc-womens": ["ax-acc-womens"],
  "ax-acc-mens": ["ax-acc-mens"],
  "ax-climbing-gear": ["ax-climbing-womens", "ax-climbing-mens"],
  "ax-climbing-womens": ["ax-climbing-womens"],
  "ax-climbing-mens": ["ax-climbing-mens"],
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
    labelKo: "시그니처 의류 컬렉션",
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
                labelKo: "팬츠 & 버뮤다",
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
        id: "dior",
        labelKo: "디올",
        href: "/shop?category=luxury&sub=dior",
        children: [
          {
            id: "di-womens",
            labelKo: "여성용",
            href: "/shop?category=luxury&sub=di-womens",
            navLeaf: true,
            children: [
              {
                id: "di-women-rtw-all",
                labelKo: "전체",
                href: "/shop?category=luxury&sub=di-women-rtw-all",
              },
              {
                id: "di-women-coats",
                labelKo: "코트",
                href: "/shop?category=luxury&sub=di-women-coats",
              },
              {
                id: "di-women-jackets",
                labelKo: "재킷",
                href: "/shop?category=luxury&sub=di-women-jackets",
              },
              {
                id: "di-women-sweaters-cardigans",
                labelKo: "스웨터 & 가디건",
                href: "/shop?category=luxury&sub=di-women-sweaters-cardigans",
              },
              {
                id: "di-women-shirts",
                labelKo: "셔츠",
                href: "/shop?category=luxury&sub=di-women-shirts",
              },
              {
                id: "di-women-tshirts",
                labelKo: "탑 & 티셔츠",
                href: "/shop?category=luxury&sub=di-women-tshirts",
              },
              {
                id: "di-women-dresses",
                labelKo: "원피스",
                href: "/shop?category=luxury&sub=di-women-dresses",
              },
              {
                id: "di-women-skirts",
                labelKo: "스커트",
                href: "/shop?category=luxury&sub=di-women-skirts",
              },
              {
                id: "di-women-trousers-shorts",
                labelKo: "팬츠 & 쇼츠",
                href: "/shop?category=luxury&sub=di-women-trousers-shorts",
              },
              {
                id: "di-women-denim",
                labelKo: "데님",
                href: "/shop?category=luxury&sub=di-women-denim",
              },
              {
                id: "di-women-homewear-lingerie",
                labelKo: "홈웨어 & 란제리",
                href: "/shop?category=luxury&sub=di-women-homewear-lingerie",
              },
              {
                id: "di-women-swimsuits",
                labelKo: "스윔웨어",
                href: "/shop?category=luxury&sub=di-women-swimsuits",
              },
            ],
          },
          {
            id: "di-mens",
            labelKo: "남성용",
            href: "/shop?category=luxury&sub=di-mens",
            navLeaf: true,
            children: [
              {
                id: "di-men-rtw-all",
                labelKo: "전체",
                href: "/shop?category=luxury&sub=di-men-rtw-all",
              },
              {
                id: "di-men-tshirts-polos",
                labelKo: "티셔츠 & 폴로",
                href: "/shop?category=luxury&sub=di-men-tshirts-polos",
              },
              {
                id: "di-men-shirts",
                labelKo: "셔츠",
                href: "/shop?category=luxury&sub=di-men-shirts",
              },
              {
                id: "di-men-knitwear-sweatshirts",
                labelKo: "니트웨어 & 스웨터",
                href: "/shop?category=luxury&sub=di-men-knitwear-sweatshirts",
              },
              {
                id: "di-men-trousers-shorts",
                labelKo: "팬츠 & 쇼츠",
                href: "/shop?category=luxury&sub=di-men-trousers-shorts",
              },
              {
                id: "di-men-denim",
                labelKo: "데님",
                href: "/shop?category=luxury&sub=di-men-denim",
              },
              {
                id: "di-men-outerwear",
                labelKo: "아우터웨어",
                href: "/shop?category=luxury&sub=di-men-outerwear",
              },
              {
                id: "di-men-tailored-jackets",
                labelKo: "재킷",
                href: "/shop?category=luxury&sub=di-men-tailored-jackets",
              },
              {
                id: "di-men-beachwear",
                labelKo: "스윔웨어",
                href: "/shop?category=luxury&sub=di-men-beachwear",
              },
              {
                id: "di-men-leather",
                labelKo: "레더",
                href: "/shop?category=luxury&sub=di-men-leather",
              },
              {
                id: "di-men-suits-tuxedos",
                labelKo: "수트 & 턱시도",
                href: "/shop?category=luxury&sub=di-men-suits-tuxedos",
              },
            ],
          },
        ],
      },
      {
        id: "prada",
        labelKo: "프라다",
        href: "/shop?category=luxury&sub=prada",
        children: [
          {
            id: "pr-women",
            labelKo: "여성용",
            href: "/shop?category=luxury&sub=pr-women",
            navLeaf: true,
            children: [
              {
                id: "pr-women-rtw",
                labelKo: "전체보기",
                href: "/shop?category=luxury&sub=pr-women-rtw",
              },
              {
                id: "pr-women-knitwear",
                labelKo: "니트웨어",
                href: "/shop?category=luxury&sub=pr-women-knitwear",
              },
              {
                id: "pr-women-shirts-tops",
                labelKo: "셔츠 & 탑",
                href: "/shop?category=luxury&sub=pr-women-shirts-tops",
              },
              {
                id: "pr-women-tshirts-sweatshirts",
                labelKo: "티셔츠 & 스웻셔츠",
                href: "/shop?category=luxury&sub=pr-women-tshirts-sweatshirts",
              },
              {
                id: "pr-women-dresses",
                labelKo: "드레스",
                href: "/shop?category=luxury&sub=pr-women-dresses",
              },
              {
                id: "pr-women-skirts",
                labelKo: "스커트",
                href: "/shop?category=luxury&sub=pr-women-skirts",
              },
              {
                id: "pr-women-trousers-shorts",
                labelKo: "팬츠 & 쇼츠",
                href: "/shop?category=luxury&sub=pr-women-trousers-shorts",
              },
              {
                id: "pr-women-denim",
                labelKo: "데님",
                href: "/shop?category=luxury&sub=pr-women-denim",
              },
              {
                id: "pr-women-jackets-coats",
                labelKo: "재킷 & 코트",
                href: "/shop?category=luxury&sub=pr-women-jackets-coats",
              },
              {
                id: "pr-women-outerwear",
                labelKo: "아우터",
                href: "/shop?category=luxury&sub=pr-women-outerwear",
              },
              {
                id: "pr-women-leather",
                labelKo: "레더",
                href: "/shop?category=luxury&sub=pr-women-leather",
              },
              {
                id: "pr-women-swimwear",
                labelKo: "스윔웨어",
                href: "/shop?category=luxury&sub=pr-women-swimwear",
              },
              {
                id: "pr-women-pajamas-underwear",
                labelKo: "파자마 & 언더웨어",
                href: "/shop?category=luxury&sub=pr-women-pajamas-underwear",
              },
            ],
          },
          {
            id: "pr-men",
            labelKo: "남성용",
            href: "/shop?category=luxury&sub=pr-men",
            navLeaf: true,
            children: [
              {
                id: "pr-men-rtw",
                labelKo: "전체보기",
                href: "/shop?category=luxury&sub=pr-men-rtw",
              },
              {
                id: "pr-men-denim",
                labelKo: "데님",
                href: "/shop?category=luxury&sub=pr-men-denim",
              },
              {
                id: "pr-men-jackets-coats",
                labelKo: "재킷 & 코트",
                href: "/shop?category=luxury&sub=pr-men-jackets-coats",
              },
              {
                id: "pr-men-jogging-suits-sweatshirts",
                labelKo: "조깅 & 스웻셔츠",
                href: "/shop?category=luxury&sub=pr-men-jogging-suits-sweatshirts",
              },
              {
                id: "pr-men-knitwear",
                labelKo: "니트웨어",
                href: "/shop?category=luxury&sub=pr-men-knitwear",
              },
              {
                id: "pr-men-leather",
                labelKo: "레더",
                href: "/shop?category=luxury&sub=pr-men-leather",
              },
              {
                id: "pr-men-outerwear",
                labelKo: "아우터",
                href: "/shop?category=luxury&sub=pr-men-outerwear",
              },
              {
                id: "pr-men-pajamas-underwear",
                labelKo: "파자마 & 언더웨어",
                href: "/shop?category=luxury&sub=pr-men-pajamas-underwear",
              },
              {
                id: "pr-men-shirts",
                labelKo: "셔츠",
                href: "/shop?category=luxury&sub=pr-men-shirts",
              },
              {
                id: "pr-men-suits",
                labelKo: "수트",
                href: "/shop?category=luxury&sub=pr-men-suits",
              },
              {
                id: "pr-men-swimwear",
                labelKo: "스윔웨어",
                href: "/shop?category=luxury&sub=pr-men-swimwear",
              },
              {
                id: "pr-men-trousers-bermudas",
                labelKo: "팬츠 & 버뫤다",
                href: "/shop?category=luxury&sub=pr-men-trousers-bermudas",
              },
              {
                id: "pr-men-tshirts-polos",
                labelKo: "티셔츠 & 폴로",
                href: "/shop?category=luxury&sub=pr-men-tshirts-polos",
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
      {
        id: "chanel-watches",
        labelKo: "샤넬",
        href: "/shop?category=watches&sub=chanel-watches",
        children: [
          {
            id: "ch-watches",
            labelKo: "전체보기",
            href: "/shop?category=watches&sub=ch-watches",
            navLeaf: true,
          },
          {
            id: "ch-watches-j12",
            labelKo: "J12",
            href: "/shop?category=watches&sub=ch-watches-j12",
            navLeaf: true,
          },
          {
            id: "ch-watches-premiere",
            labelKo: "프리미에르",
            href: "/shop?category=watches&sub=ch-watches-premiere",
            navLeaf: true,
          },
          {
            id: "ch-watches-boy-friend",
            labelKo: "보이·프렌드",
            href: "/shop?category=watches&sub=ch-watches-boy-friend",
            navLeaf: true,
          },
          {
            id: "ch-watches-monsieur",
            labelKo: "무슈",
            href: "/shop?category=watches&sub=ch-watches-monsieur",
            navLeaf: true,
          },
          {
            id: "ch-watches-code-coco",
            labelKo: "코드 코코",
            href: "/shop?category=watches&sub=ch-watches-code-coco",
            navLeaf: true,
          },
        ],
      },
      {
        id: "dior-watches",
        labelKo: "디올",
        href: "/shop?category=watches&sub=dior-watches",
        children: [
          {
            id: "di-timepieces-all",
            labelKo: "전체",
            href: "/shop?category=watches&sub=di-timepieces-all",
            navLeaf: true,
          },
          {
            id: "di-la-d-de-dior",
            labelKo: "라 D 드 디올",
            href: "/shop?category=watches&sub=di-la-d-de-dior",
            navLeaf: true,
          },
          {
            id: "di-straps",
            labelKo: "스트랩",
            href: "/shop?category=watches&sub=di-straps",
            navLeaf: true,
          },
        ],
      },
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
        ],
      },
      {
        id: "dior-bags",
        labelKo: "디올",
        href: "/shop?category=bags&sub=dior-bags",
        children: [
          {
            id: "di-bags-womens",
            labelKo: "여성용",
            href: "/shop?category=bags&sub=di-bags-womens",
            navLeaf: true,
            children: [
              {
                id: "di-bags-all",
                labelKo: "전체",
                href: "/shop?category=bags&sub=di-bags-all",
              },
              {
                id: "di-handbags",
                labelKo: "핸드백",
                href: "/shop?category=bags&sub=di-handbags",
              },
              {
                id: "di-crossbody-shoulder-bags",
                labelKo: "크로스바디 & 숄더백",
                href: "/shop?category=bags&sub=di-crossbody-shoulder-bags",
              },
              {
                id: "di-tote-bags",
                labelKo: "토트백",
                href: "/shop?category=bags&sub=di-tote-bags",
              },
              {
                id: "di-bucket-bags",
                labelKo: "버킷백",
                href: "/shop?category=bags&sub=di-bucket-bags",
              },
              {
                id: "di-clutches",
                labelKo: "클러치",
                href: "/shop?category=bags&sub=di-clutches",
              },
              {
                id: "di-mini-bags",
                labelKo: "미니백",
                href: "/shop?category=bags&sub=di-mini-bags",
              },
              {
                id: "di-accessorize-bag",
                labelKo: "악세서리 Your Bag",
                href: "/shop?category=bags&sub=di-accessorize-bag",
                navLeaf: true,
                children: [
                  {
                    id: "di-acc-bag-jewelry",
                    labelKo: "백 주얼리",
                    href: "/shop?category=bags&sub=di-acc-bag-jewelry",
                  },
                  {
                    id: "di-acc-bag-totes",
                    labelKo: "토트용",
                    href: "/shop?category=bags&sub=di-acc-bag-totes",
                  },
                  {
                    id: "di-acc-bag-mini",
                    labelKo: "미니백용",
                    href: "/shop?category=bags&sub=di-acc-bag-mini",
                  },
                  {
                    id: "di-acc-bag-shoulder",
                    labelKo: "숄더·크로스바디용",
                    href: "/shop?category=bags&sub=di-acc-bag-shoulder",
                  },
                  {
                    id: "di-acc-bag-bucket",
                    labelKo: "버킷용",
                    href: "/shop?category=bags&sub=di-acc-bag-bucket",
                  },
                  {
                    id: "di-acc-bag-clutches",
                    labelKo: "클러치·파우치용",
                    href: "/shop?category=bags&sub=di-acc-bag-clutches",
                  },
                  {
                    id: "di-acc-bag-key-rings",
                    labelKo: "키링",
                    href: "/shop?category=bags&sub=di-acc-bag-key-rings",
                  },
                  {
                    id: "di-acc-bag-mitzah",
                    labelKo: "미차",
                    href: "/shop?category=bags&sub=di-acc-bag-mitzah",
                  },
                  {
                    id: "di-acc-bag-purse",
                    labelKo: "퍼스",
                    href: "/shop?category=bags&sub=di-acc-bag-purse",
                  },
                ],
              },
            ],
          },
          {
            id: "di-bags-mens",
            labelKo: "남성용",
            href: "/shop?category=bags&sub=di-bags-mens",
            navLeaf: true,
            children: [
              {
                id: "di-men-bags-all",
                labelKo: "전체",
                href: "/shop?category=bags&sub=di-men-bags-all",
              },
              {
                id: "di-men-crossbody-shoulder-bags",
                labelKo: "크로스바디 & 숄더백",
                href: "/shop?category=bags&sub=di-men-crossbody-shoulder-bags",
              },
              {
                id: "di-men-backpacks",
                labelKo: "백팩",
                href: "/shop?category=bags&sub=di-men-backpacks",
              },
              {
                id: "di-men-small-bags",
                labelKo: "스몰백",
                href: "/shop?category=bags&sub=di-men-small-bags",
              },
              {
                id: "di-men-tote-bags",
                labelKo: "토트백",
                href: "/shop?category=bags&sub=di-men-tote-bags",
              },
              {
                id: "di-men-travel-bags",
                labelKo: "트래블백",
                href: "/shop?category=bags&sub=di-men-travel-bags",
              },
              {
                id: "di-men-briefcases",
                labelKo: "브리프케이스",
                href: "/shop?category=bags&sub=di-men-briefcases",
              },
              {
                id: "di-men-accessorize-bag",
                labelKo: "백 액세서리",
                href: "/shop?category=bags&sub=di-men-accessorize-bag",
              },
            ],
          },
        ],
      },
      {
        id: "prada-bags",
        labelKo: "프라다",
        href: "/shop?category=bags&sub=prada-bags",
        children: [
          {
            id: "pr-handbags",
            labelKo: "여성용",
            href: "/shop?category=bags&sub=pr-handbags",
            navLeaf: true,
            children: [
              {
                id: "pr-women-shoulder-bags",
                labelKo: "숄더백",
                href: "/shop?category=bags&sub=pr-women-shoulder-bags",
              },
              {
                id: "pr-women-top-handle-bags",
                labelKo: "탑 핸들백",
                href: "/shop?category=bags&sub=pr-women-top-handle-bags",
              },
              {
                id: "pr-women-tote-bags",
                labelKo: "토트백",
                href: "/shop?category=bags&sub=pr-women-tote-bags",
              },
              {
                id: "pr-women-mini-bags",
                labelKo: "미니백",
                href: "/shop?category=bags&sub=pr-women-mini-bags",
              },
              {
                id: "pr-women-backpacks",
                labelKo: "백팩",
                href: "/shop?category=bags&sub=pr-women-backpacks",
              },
              {
                id: "pr-women-briefcases",
                labelKo: "브리프케이스",
                href: "/shop?category=bags&sub=pr-women-briefcases",
              },
              {
                id: "pr-women-travel",
                labelKo: "여행용",
                href: "/shop?category=bags&sub=pr-women-travel",
                navLeaf: true,
                children: [
                  {
                    id: "pr-women-travel-bags",
                    labelKo: "트래블백",
                    href: "/shop?category=bags&sub=pr-women-travel-bags",
                  },
                  {
                    id: "pr-women-luggage-carry-on",
                    labelKo: "러기지 & 캐리온",
                    href: "/shop?category=bags&sub=pr-women-luggage-carry-on",
                  },
                  {
                    id: "pr-women-travel-accessories",
                    labelKo: "트래블 액세서리",
                    href: "/shop?category=bags&sub=pr-women-travel-accessories",
                  },
                ],
              },
            ],
          },
          {
            id: "pr-mens-handbags",
            labelKo: "남성용",
            href: "/shop?category=bags&sub=pr-mens-handbags",
            navLeaf: true,
            children: [
              {
                id: "pr-men-backpacks-belt-bags",
                labelKo: "백팩·벨트백",
                href: "/shop?category=bags&sub=pr-men-backpacks-belt-bags",
              },
              {
                id: "pr-men-briefcases",
                labelKo: "브리프케이스",
                href: "/shop?category=bags&sub=pr-men-briefcases",
              },
              {
                id: "pr-men-clutches",
                labelKo: "클러치",
                href: "/shop?category=bags&sub=pr-men-clutches",
              },
              {
                id: "pr-men-messenger-bags",
                labelKo: "메신저백",
                href: "/shop?category=bags&sub=pr-men-messenger-bags",
              },
              {
                id: "pr-men-tote-bags",
                labelKo: "토트백",
                href: "/shop?category=bags&sub=pr-men-tote-bags",
              },
              {
                id: "pr-men-travel",
                labelKo: "여행용",
                href: "/shop?category=bags&sub=pr-men-travel",
                navLeaf: true,
                children: [
                  {
                    id: "pr-men-travel-bags",
                    labelKo: "트래블백",
                    href: "/shop?category=bags&sub=pr-men-travel-bags",
                  },
                  {
                    id: "pr-men-luggage-carry-on",
                    labelKo: "러기지 & 캐리온",
                    href: "/shop?category=bags&sub=pr-men-luggage-carry-on",
                  },
                  {
                    id: "pr-men-travel-accessories",
                    labelKo: "트래블 액세서리",
                    href: "/shop?category=bags&sub=pr-men-travel-accessories",
                  },
                ],
              },
            ],
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
        id: "dior-shoes",
        labelKo: "디올",
        href: "/shop?category=shoes&sub=dior-shoes",
        children: [
          {
            id: "di-men-shoes",
            labelKo: "남성용",
            href: "/shop?category=shoes&sub=di-men-shoes",
            navLeaf: true,
            children: [
              {
                id: "di-men-shoes-all",
                labelKo: "전체",
                href: "/shop?category=shoes&sub=di-men-shoes-all",
              },
              {
                id: "di-men-sneakers",
                labelKo: "스니커즈",
                href: "/shop?category=shoes&sub=di-men-sneakers",
              },
              {
                id: "di-men-sandals-mules",
                labelKo: "샌들 & 뮬",
                href: "/shop?category=shoes&sub=di-men-sandals-mules",
              },
              {
                id: "di-men-loafers",
                labelKo: "로퍼",
                href: "/shop?category=shoes&sub=di-men-loafers",
              },
              {
                id: "di-men-lace-ups",
                labelKo: "레이스업 슈즈",
                href: "/shop?category=shoes&sub=di-men-lace-ups",
              },
              {
                id: "di-men-boots",
                labelKo: "부츠 & 앵클부츠",
                href: "/shop?category=shoes&sub=di-men-boots",
              },
            ],
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
        id: "prada-shoes",
        labelKo: "프라다",
        href: "/shop?category=shoes&sub=prada-shoes",
        children: [
          {
            id: "pr-women-shoes",
            labelKo: "여성용",
            href: "/shop?category=shoes&sub=pr-women-shoes",
            navLeaf: true,
            children: [
              {
                id: "pr-women-ankle-boots-boots",
                labelKo: "앵클 부츠 & 부츠",
                href: "/shop?category=shoes&sub=pr-women-ankle-boots-boots",
              },
              {
                id: "pr-women-loafers-lace-ups",
                labelKo: "로퍼 & 레이스업",
                href: "/shop?category=shoes&sub=pr-women-loafers-lace-ups",
              },
              {
                id: "pr-women-pumps-ballerinas",
                labelKo: "펌프스 & 발레리나",
                href: "/shop?category=shoes&sub=pr-women-pumps-ballerinas",
              },
              {
                id: "pr-women-sneakers",
                labelKo: "스니커즈",
                href: "/shop?category=shoes&sub=pr-women-sneakers",
              },
              {
                id: "pr-women-sandals-mules",
                labelKo: "샌들 & 뮬",
                href: "/shop?category=shoes&sub=pr-women-sandals-mules",
              },
              {
                id: "pr-women-new-formal",
                labelKo: "뉴 포멀",
                href: "/shop?category=shoes&sub=pr-women-new-formal",
              },
              {
                id: "pr-women-chocolate",
                labelKo: "초콜릿",
                href: "/shop?category=shoes&sub=pr-women-chocolate",
              },
            ],
          },
          {
            id: "pr-men-shoes",
            labelKo: "남성용",
            href: "/shop?category=shoes&sub=pr-men-shoes",
            navLeaf: true,
            children: [
              {
                id: "pr-men-loafers",
                labelKo: "로퍼",
                href: "/shop?category=shoes&sub=pr-men-loafers",
              },
              {
                id: "pr-men-sneakers",
                labelKo: "스니커즈",
                href: "/shop?category=shoes&sub=pr-men-sneakers",
              },
              {
                id: "pr-men-sandals",
                labelKo: "샌들",
                href: "/shop?category=shoes&sub=pr-men-sandals",
              },
              {
                id: "pr-men-lace-ups",
                labelKo: "레이스업",
                href: "/shop?category=shoes&sub=pr-men-lace-ups",
              },
              {
                id: "pr-men-boots",
                labelKo: "부츠",
                href: "/shop?category=shoes&sub=pr-men-boots",
              },
              {
                id: "pr-men-americas-cup",
                labelKo: "아메리카스 컵",
                href: "/shop?category=shoes&sub=pr-men-americas-cup",
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
          {
            id: "ch-high-jewellery",
            labelKo: "High 주얼리",
            href: "/shop?category=accessories&sub=ch-high-jewellery",
            navLeaf: true,
          },
          {
            id: "ch-fine-jewellery",
            labelKo: "Fine 주얼리",
            href: "/shop?category=accessories&sub=ch-fine-jewellery",
            navLeaf: true,
          },
          {
            id: "ch-slg",
            labelKo: "스몰 레더 굿즈 전체",
            href: "/shop?category=accessories&sub=ch-slg",
            navLeaf: true,
          },
          {
            id: "ch-women-wallets-on-chain",
            labelKo: "월렛 온 체인",
            href: "/shop?category=accessories&sub=ch-women-wallets-on-chain",
            navLeaf: true,
          },
          {
            id: "ch-women-micro-bags",
            labelKo: "마이크로백",
            href: "/shop?category=accessories&sub=ch-women-micro-bags",
            navLeaf: true,
          },
          {
            id: "ch-women-vanity",
            labelKo: "배니티",
            href: "/shop?category=accessories&sub=ch-women-vanity",
            navLeaf: true,
          },
          {
            id: "ch-women-card-holders-wallets",
            labelKo: "카드홀더 & 월렛",
            href: "/shop?category=accessories&sub=ch-women-card-holders-wallets",
            navLeaf: true,
          },
          {
            id: "ch-women-pouches-cases",
            labelKo: "파우치 & 케이스",
            href: "/shop?category=accessories&sub=ch-women-pouches-cases",
            navLeaf: true,
          },
          {
            id: "ch-women-leather-accessories",
            labelKo: "레더 액세서리",
            href: "/shop?category=accessories&sub=ch-women-leather-accessories",
            navLeaf: true,
          },
          {
            id: "ch-women-sunglasses",
            labelKo: "선글라스",
            href: "/shop?category=accessories&sub=ch-women-sunglasses",
            navLeaf: true,
          },
          {
            id: "ch-fragrance",
            labelKo: "향수",
            href: "/shop?category=accessories&sub=ch-fragrance",
            navLeaf: true,
          },
          {
            id: "ch-makeup",
            labelKo: "메이크업",
            href: "/shop?category=accessories&sub=ch-makeup",
            navLeaf: true,
            children: [
              {
                id: "ch-makeup-complexion",
                labelKo: "컴플렉션",
                href: "/shop?category=accessories&sub=ch-makeup-complexion",
                navLeaf: true,
                children: [
                  {
                    id: "ch-makeup-foundations",
                    labelKo: "파운데이션",
                    href: "/shop?category=accessories&sub=ch-makeup-foundations",
                  },
                  {
                    id: "ch-makeup-base",
                    labelKo: "베이스",
                    href: "/shop?category=accessories&sub=ch-makeup-base",
                  },
                  {
                    id: "ch-makeup-healthy-glow",
                    labelKo: "헬시 글로우",
                    href: "/shop?category=accessories&sub=ch-makeup-healthy-glow",
                  },
                  {
                    id: "ch-makeup-blush",
                    labelKo: "블러시",
                    href: "/shop?category=accessories&sub=ch-makeup-blush",
                  },
                  {
                    id: "ch-makeup-powders",
                    labelKo: "파우더",
                    href: "/shop?category=accessories&sub=ch-makeup-powders",
                  },
                  {
                    id: "ch-makeup-bronzers",
                    labelKo: "브론저",
                    href: "/shop?category=accessories&sub=ch-makeup-bronzers",
                  },
                  {
                    id: "ch-makeup-concealer",
                    labelKo: "컨실러",
                    href: "/shop?category=accessories&sub=ch-makeup-concealer",
                  },
                  {
                    id: "ch-makeup-highlighter",
                    labelKo: "하이라이터",
                    href: "/shop?category=accessories&sub=ch-makeup-highlighter",
                  },
                ],
              },
              {
                id: "ch-makeup-eyes",
                labelKo: "아이",
                href: "/shop?category=accessories&sub=ch-makeup-eyes",
                navLeaf: true,
                children: [
                  {
                    id: "ch-makeup-eyeshadows",
                    labelKo: "아이섀도우",
                    href: "/shop?category=accessories&sub=ch-makeup-eyeshadows",
                  },
                  {
                    id: "ch-makeup-mascara",
                    labelKo: "마스카라",
                    href: "/shop?category=accessories&sub=ch-makeup-mascara",
                  },
                  {
                    id: "ch-makeup-brows",
                    labelKo: "브로우",
                    href: "/shop?category=accessories&sub=ch-makeup-brows",
                  },
                  {
                    id: "ch-makeup-eyeliners",
                    labelKo: "아이라이너",
                    href: "/shop?category=accessories&sub=ch-makeup-eyeliners",
                  },
                  {
                    id: "ch-makeup-eye-palette",
                    labelKo: "아이 팔레트",
                    href: "/shop?category=accessories&sub=ch-makeup-eye-palette",
                  },
                ],
              },
              {
                id: "ch-makeup-lips",
                labelKo: "립",
                href: "/shop?category=accessories&sub=ch-makeup-lips",
                navLeaf: true,
                children: [
                  {
                    id: "ch-makeup-lip-gloss",
                    labelKo: "립글로스",
                    href: "/shop?category=accessories&sub=ch-makeup-lip-gloss",
                  },
                  {
                    id: "ch-makeup-lipsticks",
                    labelKo: "립스틱",
                    href: "/shop?category=accessories&sub=ch-makeup-lipsticks",
                  },
                  {
                    id: "ch-makeup-lip-pencils",
                    labelKo: "립펜슬",
                    href: "/shop?category=accessories&sub=ch-makeup-lip-pencils",
                  },
                  {
                    id: "ch-makeup-lip-balms",
                    labelKo: "립밤 & 립케어",
                    href: "/shop?category=accessories&sub=ch-makeup-lip-balms",
                  },
                  {
                    id: "ch-makeup-liquid-lipsticks",
                    labelKo: "리퀴드 립스틱",
                    href: "/shop?category=accessories&sub=ch-makeup-liquid-lipsticks",
                  },
                ],
              },
              {
                id: "ch-makeup-nails",
                labelKo: "네일",
                href: "/shop?category=accessories&sub=ch-makeup-nails",
                navLeaf: true,
                children: [
                  {
                    id: "ch-makeup-manicure",
                    labelKo: "매니큐어",
                    href: "/shop?category=accessories&sub=ch-makeup-manicure",
                  },
                  {
                    id: "ch-makeup-nail-colour",
                    labelKo: "네일 컬러",
                    href: "/shop?category=accessories&sub=ch-makeup-nail-colour",
                  },
                ],
              },
              {
                id: "ch-makeup-brushes",
                labelKo: "브러시 & 액세서리",
                href: "/shop?category=accessories&sub=ch-makeup-brushes",
                navLeaf: true,
                children: [
                  {
                    id: "ch-makeup-eye-brushes",
                    labelKo: "아이 브러시",
                    href: "/shop?category=accessories&sub=ch-makeup-eye-brushes",
                  },
                  {
                    id: "ch-makeup-complexion-brushes",
                    labelKo: "컴플렉션 브러시",
                    href: "/shop?category=accessories&sub=ch-makeup-complexion-brushes",
                  },
                  {
                    id: "ch-makeup-lip-brushes",
                    labelKo: "립 브러시",
                    href: "/shop?category=accessories&sub=ch-makeup-lip-brushes",
                  },
                ],
              },
            ],
          },
          {
            id: "ch-skincare",
            labelKo: "스킨케어",
            href: "/shop?category=accessories&sub=ch-skincare",
            navLeaf: true,
            children: [
              {
                id: "ch-skincare-cleansers",
                labelKo: "클렌저/메이크업 리무버",
                href: "/shop?category=accessories&sub=ch-skincare-cleansers",
              },
              {
                id: "ch-skincare-serums",
                labelKo: "세럼",
                href: "/shop?category=accessories&sub=ch-skincare-serums",
              },
              {
                id: "ch-skincare-moisturisers",
                labelKo: "모이스처라이저",
                href: "/shop?category=accessories&sub=ch-skincare-moisturisers",
              },
              {
                id: "ch-skincare-eyes-lips",
                labelKo: "아이 & 립 케어",
                href: "/shop?category=accessories&sub=ch-skincare-eyes-lips",
              },
              {
                id: "ch-skincare-body",
                labelKo: "바디/핸드 케어",
                href: "/shop?category=accessories&sub=ch-skincare-body",
              },
              {
                id: "ch-skincare-masks",
                labelKo: "마스크 & 스크럽",
                href: "/shop?category=accessories&sub=ch-skincare-masks",
              },
              {
                id: "ch-skincare-oils",
                labelKo: "오일",
                href: "/shop?category=accessories&sub=ch-skincare-oils",
              },
              {
                id: "ch-skincare-protection",
                labelKo: "선 프로텍션",
                href: "/shop?category=accessories&sub=ch-skincare-protection",
              },
              {
                id: "ch-skincare-toners",
                labelKo: "토너/로션",
                href: "/shop?category=accessories&sub=ch-skincare-toners",
              },
              {
                id: "ch-skincare-mists",
                labelKo: "미스트",
                href: "/shop?category=accessories&sub=ch-skincare-mists",
              },
            ],
          },
          {
            id: "ch-other-accessories",
            labelKo: "기타 악세서리 전체",
            href: "/shop?category=accessories&sub=ch-other-accessories",
            navLeaf: true,
          },
          {
            id: "ch-women-headwear",
            labelKo: "헤드웨어",
            href: "/shop?category=accessories&sub=ch-women-headwear",
            navLeaf: true,
          },
          {
            id: "ch-women-belts",
            labelKo: "벨트",
            href: "/shop?category=accessories&sub=ch-women-belts",
            navLeaf: true,
          },
          {
            id: "ch-women-scarves",
            labelKo: "스카프",
            href: "/shop?category=accessories&sub=ch-women-scarves",
            navLeaf: true,
          },
          {
            id: "ch-women-camellias",
            labelKo: "카멜리아",
            href: "/shop?category=accessories&sub=ch-women-camellias",
            navLeaf: true,
          },
          {
            id: "ch-women-winter-accessories",
            labelKo: "윈터 악세서리",
            href: "/shop?category=accessories&sub=ch-women-winter-accessories",
            navLeaf: true,
          },
          {
            id: "ch-women-summer-accessories",
            labelKo: "서머 악세서리",
            href: "/shop?category=accessories&sub=ch-women-summer-accessories",
            navLeaf: true,
          },
        ],
      },
      {
        id: "louis-vuitton-accessories",
        labelKo: "루이 비통",
        href: "/shop?category=accessories&sub=louis-vuitton-accessories",
        children: [
          {
            id: "lv-home-lifestyle",
            labelKo: "홈, 라이프스타일과 서재",
            href: "/shop?category=accessories&sub=lv-home-lifestyle",
            children: [
              {
                id: "lv-furniture-lighting",
                labelKo: "가구와 라이트닝",
                href: "/shop?category=accessories&sub=lv-furniture-lighting",
                navLeaf: true,
                children: [
                  {
                    id: "lv-furniture-lighting-all",
                    labelKo: "전체",
                    href: "/shop?category=accessories&sub=lv-furniture-lighting-all",
                  },
                  {
                    id: "lv-seating",
                    labelKo: "시팅",
                    href: "/shop?category=accessories&sub=lv-seating",
                  },
                  {
                    id: "lv-tables",
                    labelKo: "테이블",
                    href: "/shop?category=accessories&sub=lv-tables",
                  },
                  {
                    id: "lv-lighting",
                    labelKo: "라이트닝",
                    href: "/shop?category=accessories&sub=lv-lighting",
                  },
                  {
                    id: "lv-storage",
                    labelKo: "수납 · 사이드보드",
                    href: "/shop?category=accessories&sub=lv-storage",
                  },
                ],
              },
            ],
          },
        ],
      },
      {
        id: "dior-accessories",
        labelKo: "디올",
        href: "/shop?category=accessories&sub=dior-accessories",
        children: [
          {
            id: "di-home",
            labelKo: "홈",
            href: "/shop?category=accessories&sub=di-home",
            children: [
              {
                id: "di-tableware",
                labelKo: "테이블웨어",
                href: "/shop?category=accessories&sub=di-tableware",
                navLeaf: true,
                children: [
                  {
                    id: "di-tableware-all",
                    labelKo: "전체",
                    href: "/shop?category=accessories&sub=di-tableware-all",
                  },
                  {
                    id: "di-plates-bowls",
                    labelKo: "플레이트 & 보울",
                    href: "/shop?category=accessories&sub=di-plates-bowls",
                  },
                  {
                    id: "di-glasses",
                    labelKo: "글라스",
                    href: "/shop?category=accessories&sub=di-glasses",
                  },
                  {
                    id: "di-carafes",
                    labelKo: "카라페",
                    href: "/shop?category=accessories&sub=di-carafes",
                  },
                  {
                    id: "di-tea-coffee",
                    labelKo: "티 & 커피",
                    href: "/shop?category=accessories&sub=di-tea-coffee",
                  },
                  {
                    id: "di-cutlery",
                    labelKo: "커트러리",
                    href: "/shop?category=accessories&sub=di-cutlery",
                  },
                ],
              },
              {
                id: "di-objects",
                labelKo: "오브젝트",
                href: "/shop?category=accessories&sub=di-objects",
                navLeaf: true,
                children: [
                  {
                    id: "di-objects-all",
                    labelKo: "전체",
                    href: "/shop?category=accessories&sub=di-objects-all",
                  },
                  {
                    id: "di-books",
                    labelKo: "북",
                    href: "/shop?category=accessories&sub=di-books",
                  },
                  {
                    id: "di-notebooks",
                    labelKo: "노트북",
                    href: "/shop?category=accessories&sub=di-notebooks",
                  },
                  {
                    id: "di-desk-accessories",
                    labelKo: "데스크 악세서리",
                    href: "/shop?category=accessories&sub=di-desk-accessories",
                  },
                  {
                    id: "di-candleholders-candles",
                    labelKo: "캔들홀더 & 캔들",
                    href: "/shop?category=accessories&sub=di-candleholders-candles",
                  },
                  {
                    id: "di-small-objects",
                    labelKo: "스몰 오브젝트",
                    href: "/shop?category=accessories&sub=di-small-objects",
                  },
                  {
                    id: "di-trinket-trays",
                    labelKo: "트링켓 트레이",
                    href: "/shop?category=accessories&sub=di-trinket-trays",
                  },
                  {
                    id: "di-trays",
                    labelKo: "트레이",
                    href: "/shop?category=accessories&sub=di-trays",
                  },
                  {
                    id: "di-leisure",
                    labelKo: "레저",
                    href: "/shop?category=accessories&sub=di-leisure",
                  },
                  {
                    id: "di-paperweights",
                    labelKo: "페이퍼웨이트",
                    href: "/shop?category=accessories&sub=di-paperweights",
                  },
                ],
              },
              {
                id: "di-decor",
                labelKo: "데코",
                href: "/shop?category=accessories&sub=di-decor",
                navLeaf: true,
                children: [
                  {
                    id: "di-decor-all",
                    labelKo: "전체",
                    href: "/shop?category=accessories&sub=di-decor-all",
                  },
                  {
                    id: "di-decorative-pieces",
                    labelKo: "데코러티브 피스",
                    href: "/shop?category=accessories&sub=di-decorative-pieces",
                  },
                  {
                    id: "di-lighting",
                    labelKo: "조명",
                    href: "/shop?category=accessories&sub=di-lighting",
                  },
                  {
                    id: "di-baskets",
                    labelKo: "바스켓",
                    href: "/shop?category=accessories&sub=di-baskets",
                  },
                  {
                    id: "di-wallpapers",
                    labelKo: "월페이퍼",
                    href: "/shop?category=accessories&sub=di-wallpapers",
                  },
                  {
                    id: "di-vases",
                    labelKo: "화병",
                    href: "/shop?category=accessories&sub=di-vases",
                  },
                  {
                    id: "di-furniture",
                    labelKo: "가구",
                    href: "/shop?category=accessories&sub=di-furniture",
                  },
                ],
              },
              {
                id: "di-textile",
                labelKo: "텍스타일즈",
                href: "/shop?category=accessories&sub=di-textile",
                navLeaf: true,
                children: [
                  {
                    id: "di-textile-all",
                    labelKo: "전체",
                    href: "/shop?category=accessories&sub=di-textile-all",
                  },
                  {
                    id: "di-cushions",
                    labelKo: "쿠션",
                    href: "/shop?category=accessories&sub=di-cushions",
                  },
                  {
                    id: "di-bath-linen",
                    labelKo: "배스 리넨",
                    href: "/shop?category=accessories&sub=di-bath-linen",
                  },
                  {
                    id: "di-table-linen",
                    labelKo: "테이블 리넨",
                    href: "/shop?category=accessories&sub=di-table-linen",
                  },
                  {
                    id: "di-throws",
                    labelKo: "스로우",
                    href: "/shop?category=accessories&sub=di-throws",
                  },
                ],
              },
            ],
          },
          {
            id: "di-jewelry-timepieces",
            labelKo: "쥬얼리 & 타임피스",
            href: "/shop?category=accessories&sub=di-jewelry-timepieces",
            navLeaf: true,
            children: [
              {
                id: "di-jewelry-all",
                labelKo: "전체",
                href: "/shop?category=accessories&sub=di-jewelry-all",
              },
              {
                id: "di-earrings",
                labelKo: "이어링스",
                href: "/shop?category=accessories&sub=di-earrings",
              },
              {
                id: "di-bracelets",
                labelKo: "브레이슬릿",
                href: "/shop?category=accessories&sub=di-bracelets",
              },
              {
                id: "di-rings",
                labelKo: "링",
                href: "/shop?category=accessories&sub=di-rings",
              },
              {
                id: "di-necklaces",
                labelKo: "네크리스",
                href: "/shop?category=accessories&sub=di-necklaces",
              },
              {
                id: "di-dior-icons",
                labelKo: "디올 아이콘즈",
                href: "/shop?category=accessories&sub=di-dior-icons",
              },
            ],
          },
          {
            id: "di-women-accessories",
            labelKo: "여성용",
            href: "/shop?category=accessories&sub=di-women-accessories",
            navLeaf: true,
            children: [
              {
                id: "di-women-acc-all",
                labelKo: "전체",
                href: "/shop?category=accessories&sub=di-women-acc-all",
              },
              {
                id: "di-women-sunglasses",
                labelKo: "선글라스",
                href: "/shop?category=accessories&sub=di-women-sunglasses",
              },
              {
                id: "di-women-jewelry",
                labelKo: "패션 주얼리",
                href: "/shop?category=accessories&sub=di-women-jewelry",
                navLeaf: true,
                children: [
                  {
                    id: "di-women-jewelry-all",
                    labelKo: "전체",
                    href: "/shop?category=accessories&sub=di-women-jewelry-all",
                  },
                  {
                    id: "di-women-earrings",
                    labelKo: "이어링",
                    href: "/shop?category=accessories&sub=di-women-earrings",
                  },
                  {
                    id: "di-women-necklaces",
                    labelKo: "네크리스",
                    href: "/shop?category=accessories&sub=di-women-necklaces",
                  },
                  {
                    id: "di-women-brooches",
                    labelKo: "브로치",
                    href: "/shop?category=accessories&sub=di-women-brooches",
                  },
                  {
                    id: "di-women-bracelets",
                    labelKo: "브레이슬릿",
                    href: "/shop?category=accessories&sub=di-women-bracelets",
                  },
                  {
                    id: "di-women-rings",
                    labelKo: "링",
                    href: "/shop?category=accessories&sub=di-women-rings",
                  },
                  {
                    id: "di-women-dior-tribales",
                    labelKo: "Dior Tribales",
                    href: "/shop?category=accessories&sub=di-women-dior-tribales",
                  },
                ],
              },
              {
                id: "di-women-optical-glasses",
                labelKo: "옵티컬 안경",
                href: "/shop?category=accessories&sub=di-women-optical-glasses",
              },
              {
                id: "di-women-belts",
                labelKo: "벨트",
                href: "/shop?category=accessories&sub=di-women-belts",
              },
              {
                id: "di-women-silk-scarves-mitzah",
                labelKo: "실크 스카프 & 미차",
                href: "/shop?category=accessories&sub=di-women-silk-scarves-mitzah",
              },
              {
                id: "di-women-scarves-shawls",
                labelKo: "스카프 & 쇼울",
                href: "/shop?category=accessories&sub=di-women-scarves-shawls",
              },
              {
                id: "di-women-hats-gloves",
                labelKo: "모자 & 장갑",
                href: "/shop?category=accessories&sub=di-women-hats-gloves",
              },
              {
                id: "di-women-hair-accessories",
                labelKo: "헤어 악세서리",
                href: "/shop?category=accessories&sub=di-women-hair-accessories",
              },
              {
                id: "di-women-beach-accessories",
                labelKo: "비치 악세서리",
                href: "/shop?category=accessories&sub=di-women-beach-accessories",
              },
              {
                id: "di-women-key-rings",
                labelKo: "키링 & 백 참",
                href: "/shop?category=accessories&sub=di-women-key-rings",
              },
              {
                id: "di-women-slg",
                labelKo: "스몰 레더 굿즈",
                href: "/shop?category=accessories&sub=di-women-slg",
                navLeaf: true,
                children: [
                  {
                    id: "di-women-slg-all",
                    labelKo: "전체",
                    href: "/shop?category=accessories&sub=di-women-slg-all",
                  },
                  {
                    id: "di-women-card-holders",
                    labelKo: "카드 홀더 & 스몰 악세서리",
                    href: "/shop?category=accessories&sub=di-women-card-holders",
                  },
                  {
                    id: "di-women-wallets",
                    labelKo: "월렛",
                    href: "/shop?category=accessories&sub=di-women-wallets",
                  },
                  {
                    id: "di-women-pouches",
                    labelKo: "파우치",
                    href: "/shop?category=accessories&sub=di-women-pouches",
                  },
                  {
                    id: "di-women-slg-tech",
                    labelKo: "테크 액세서리",
                    href: "/shop?category=accessories&sub=di-women-slg-tech",
                  },
                ],
              },
            ],
          },
          {
            id: "di-men-accessories",
            labelKo: "남성용",
            href: "/shop?category=accessories&sub=di-men-accessories",
            navLeaf: true,
            children: [
              {
                id: "di-men-acc-all",
                labelKo: "전체",
                href: "/shop?category=accessories&sub=di-men-acc-all",
              },
              {
                id: "di-men-sunglasses",
                labelKo: "선글라스",
                href: "/shop?category=accessories&sub=di-men-sunglasses",
              },
              {
                id: "di-men-belts",
                labelKo: "벨트",
                href: "/shop?category=accessories&sub=di-men-belts",
              },
              {
                id: "di-men-ties-pocket-squares",
                labelKo: "타이 & 포켓스퀘어",
                href: "/shop?category=accessories&sub=di-men-ties-pocket-squares",
              },
              {
                id: "di-men-fashion-jewelry",
                labelKo: "패션 주얼리 & 커프링크",
                href: "/shop?category=accessories&sub=di-men-fashion-jewelry",
              },
              {
                id: "di-men-silver-jewelry",
                labelKo: "실버 주얼리",
                href: "/shop?category=accessories&sub=di-men-silver-jewelry",
              },
              {
                id: "di-men-scarves",
                labelKo: "스카프",
                href: "/shop?category=accessories&sub=di-men-scarves",
              },
              {
                id: "di-men-hats-gloves",
                labelKo: "모자 & 장갑",
                href: "/shop?category=accessories&sub=di-men-hats-gloves",
              },
              {
                id: "di-men-socks",
                labelKo: "양말",
                href: "/shop?category=accessories&sub=di-men-socks",
              },
              {
                id: "di-men-key-rings",
                labelKo: "키링 & 백 참",
                href: "/shop?category=accessories&sub=di-men-key-rings",
              },
              {
                id: "di-men-charm-jewelry",
                labelKo: "커스터마이저블 참 주얼리",
                href: "/shop?category=accessories&sub=di-men-charm-jewelry",
              },
              {
                id: "di-men-lifestyle",
                labelKo: "라이프스타일",
                href: "/shop?category=accessories&sub=di-men-lifestyle",
              },
              {
                id: "di-men-acc-tech",
                labelKo: "테크 액세서리",
                href: "/shop?category=accessories&sub=di-men-acc-tech",
              },
              {
                id: "di-men-pet-accessories",
                labelKo: "펫 액세서리",
                href: "/shop?category=accessories&sub=di-men-pet-accessories",
              },
              {
                id: "di-men-slg",
                labelKo: "스몰 레더 굿즈",
                href: "/shop?category=accessories&sub=di-men-slg",
                navLeaf: true,
                children: [
                  {
                    id: "di-men-slg-all",
                    labelKo: "전체",
                    href: "/shop?category=accessories&sub=di-men-slg-all",
                  },
                  {
                    id: "di-men-card-holders",
                    labelKo: "카드 홀더",
                    href: "/shop?category=accessories&sub=di-men-card-holders",
                  },
                  {
                    id: "di-men-compact-wallets",
                    labelKo: "컴팩트 월렛",
                    href: "/shop?category=accessories&sub=di-men-compact-wallets",
                  },
                  {
                    id: "di-men-long-wallets",
                    labelKo: "롱 월렛",
                    href: "/shop?category=accessories&sub=di-men-long-wallets",
                  },
                  {
                    id: "di-men-pouches",
                    labelKo: "파우치 & 웨어러블 월렛",
                    href: "/shop?category=accessories&sub=di-men-pouches",
                  },
                  {
                    id: "di-men-tech-accessories",
                    labelKo: "테크 액세서리",
                    href: "/shop?category=accessories&sub=di-men-tech-accessories",
                  },
                ],
              },
            ],
          },
        ],
      },
      {
        id: "prada-accessories",
        labelKo: "프라다",
        href: "/shop?category=accessories&sub=prada-accessories",
        children: [
          {
            id: "pr-women-accessories",
            labelKo: "여성용",
            href: "/shop?category=accessories&sub=pr-women-accessories",
            navLeaf: true,
            children: [
              {
                id: "pr-women-sunglasses",
                labelKo: "선글라스",
                href: "/shop?category=accessories&sub=pr-women-sunglasses",
              },
              {
                id: "pr-women-silks-scarves",
                labelKo: "실크 & 스카프",
                href: "/shop?category=accessories&sub=pr-women-silks-scarves",
              },
              {
                id: "pr-women-hats-gloves",
                labelKo: "모자 & 장갑",
                href: "/shop?category=accessories&sub=pr-women-hats-gloves",
              },
              {
                id: "pr-women-headbands-hair",
                labelKo: "헤어밴드 & 헤어 액세서리",
                href: "/shop?category=accessories&sub=pr-women-headbands-hair",
              },
              {
                id: "pr-women-bag-charms",
                labelKo: "백 참 & 키체인",
                href: "/shop?category=accessories&sub=pr-women-bag-charms",
              },
              {
                id: "pr-women-jewels",
                labelKo: "주얼리",
                href: "/shop?category=accessories&sub=pr-women-jewels",
              },
              {
                id: "pr-women-belts",
                labelKo: "벨트",
                href: "/shop?category=accessories&sub=pr-women-belts",
              },
              {
                id: "pr-women-pouches",
                labelKo: "파우치",
                href: "/shop?category=accessories&sub=pr-women-pouches",
              },
              {
                id: "pr-women-card-holders",
                labelKo: "카드홀더",
                href: "/shop?category=accessories&sub=pr-women-card-holders",
              },
              {
                id: "pr-women-small-wallets",
                labelKo: "스몰 월렛",
                href: "/shop?category=accessories&sub=pr-women-small-wallets",
              },
              {
                id: "pr-women-large-wallets",
                labelKo: "라지 월렛",
                href: "/shop?category=accessories&sub=pr-women-large-wallets",
              },
              {
                id: "pr-women-wallets-on-chain",
                labelKo: "월렛 온 체인",
                href: "/shop?category=accessories&sub=pr-women-wallets-on-chain",
              },
              {
                id: "pr-women-high-tech-accessories",
                labelKo: "하이테크 액세서리",
                href: "/shop?category=accessories&sub=pr-women-high-tech-accessories",
              },
            ],
          },
          {
            id: "pr-mens-accessories",
            labelKo: "남성용",
            href: "/shop?category=accessories&sub=pr-mens-accessories",
            navLeaf: true,
            children: [
              {
                id: "pr-men-sunglasses",
                labelKo: "선글라스",
                href: "/shop?category=accessories&sub=pr-men-sunglasses",
              },
              {
                id: "pr-men-hats-gloves",
                labelKo: "모자 & 장갑",
                href: "/shop?category=accessories&sub=pr-men-hats-gloves",
              },
              {
                id: "pr-men-bag-charms",
                labelKo: "백 참 & 키체인",
                href: "/shop?category=accessories&sub=pr-men-bag-charms",
              },
              {
                id: "pr-men-belts",
                labelKo: "벨트",
                href: "/shop?category=accessories&sub=pr-men-belts",
              },
              {
                id: "pr-men-custom-belts",
                labelKo: "커스텀 벨트",
                href: "/shop?category=accessories&sub=pr-men-custom-belts",
              },
              {
                id: "pr-men-silks-scarves",
                labelKo: "실크 & 스카프",
                href: "/shop?category=accessories&sub=pr-men-silks-scarves",
              },
              {
                id: "pr-men-ties-bow-ties",
                labelKo: "넥타이 & 보우타이",
                href: "/shop?category=accessories&sub=pr-men-ties-bow-ties",
              },
              {
                id: "pr-men-jewels",
                labelKo: "주얼리",
                href: "/shop?category=accessories&sub=pr-men-jewels",
              },
              {
                id: "pr-men-card-holders",
                labelKo: "카드홀더",
                href: "/shop?category=accessories&sub=pr-men-card-holders",
              },
              {
                id: "pr-men-small-wallets",
                labelKo: "스몰 월렛",
                href: "/shop?category=accessories&sub=pr-men-small-wallets",
              },
              {
                id: "pr-men-large-wallets",
                labelKo: "라지 월렛",
                href: "/shop?category=accessories&sub=pr-men-large-wallets",
              },
              {
                id: "pr-men-high-tech-accessories",
                labelKo: "하이테크 액세서리",
                href: "/shop?category=accessories&sub=pr-men-high-tech-accessories",
              },
            ],
          },
          {
            id: "pr-linea-rossa",
            labelKo: "LINEA ROSSA",
            href: "/shop?category=accessories&sub=pr-linea-rossa",
            navLeaf: true,
            children: [
              {
                id: "pr-linea-rossa-women",
                labelKo: "여성용 컬렉션",
                href: "/shop?category=accessories&sub=pr-linea-rossa-women",
              },
              {
                id: "pr-linea-rossa-men",
                labelKo: "남성용 컬렉션",
                href: "/shop?category=accessories&sub=pr-linea-rossa-men",
              },
              {
                id: "pr-linea-rossa-sunglasses",
                labelKo: "선글라스",
                href: "/shop?category=accessories&sub=pr-linea-rossa-sunglasses",
              },
              {
                id: "pr-linea-rossa-shoes",
                labelKo: "슈즈",
                href: "/shop?category=accessories&sub=pr-linea-rossa-shoes",
              },
              {
                id: "pr-linea-rossa-fragrances",
                labelKo: "프래그런스",
                href: "/shop?category=accessories&sub=pr-linea-rossa-fragrances",
              },
            ],
          },
          {
            id: "pr-beauty",
            labelKo: "뷰티",
            href: "/shop?category=accessories&sub=pr-beauty",
            navLeaf: true,
            children: [
              {
                id: "pr-beauty-face",
                labelKo: "페이스",
                href: "/shop?category=accessories&sub=pr-beauty-face",
              },
              {
                id: "pr-beauty-eyes",
                labelKo: "아이즈",
                href: "/shop?category=accessories&sub=pr-beauty-eyes",
              },
              {
                id: "pr-beauty-lips",
                labelKo: "립스",
                href: "/shop?category=accessories&sub=pr-beauty-lips",
              },
              {
                id: "pr-beauty-skincare",
                labelKo: "스킨케어",
                href: "/shop?category=accessories&sub=pr-beauty-skincare",
              },
              {
                id: "pr-beauty-brushes",
                labelKo: "브러시 & 액세서리",
                href: "/shop?category=accessories&sub=pr-beauty-brushes",
              },
            ],
          },
          {
            id: "pr-fragrances",
            labelKo: "향수",
            href: "/shop?category=accessories&sub=pr-fragrances",
            navLeaf: true,
            children: [
              {
                id: "pr-fragrances-women",
                labelKo: "여성 향수",
                href: "/shop?category=accessories&sub=pr-fragrances-women",
              },
              {
                id: "pr-fragrances-men",
                labelKo: "남성 향수",
                href: "/shop?category=accessories&sub=pr-fragrances-men",
              },
              {
                id: "pr-fragrances-exclusive",
                labelKo: "익스클루시브 컬렉션",
                href: "/shop?category=accessories&sub=pr-fragrances-exclusive",
              },
            ],
          },
          {
            id: "pr-fine-jewelry",
            labelKo: "파인 주얼리",
            href: "/shop?category=accessories&sub=pr-fine-jewelry",
            navLeaf: true,
            children: [
              {
                id: "pr-fine-jewelry-bracelets",
                labelKo: "팔찌",
                href: "/shop?category=accessories&sub=pr-fine-jewelry-bracelets",
              },
              {
                id: "pr-fine-jewelry-necklaces",
                labelKo: "네크리스",
                href: "/shop?category=accessories&sub=pr-fine-jewelry-necklaces",
              },
              {
                id: "pr-fine-jewelry-rings",
                labelKo: "링",
                href: "/shop?category=accessories&sub=pr-fine-jewelry-rings",
              },
              {
                id: "pr-fine-jewelry-earrings-brooches",
                labelKo: "이어링 & 브로치",
                href: "/shop?category=accessories&sub=pr-fine-jewelry-earrings-brooches",
              },
            ],
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
          {
            id: "ax-climbing-gear",
            labelKo: "클라이밍기어",
            href: "/shop?category=accessories&sub=ax-climbing-gear",
            children: [
              {
                id: "ax-climbing-womens",
                labelKo: "여성용",
                href: "/shop?category=accessories&sub=ax-climbing-womens",
                navLeaf: true,
              },
              {
                id: "ax-climbing-mens",
                labelKo: "남성용",
                href: "/shop?category=accessories&sub=ax-climbing-mens",
                navLeaf: true,
              },
            ],
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
  return sortNavChildrenByBrandOrder(findCategory(categoryId)?.children ?? []);
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
