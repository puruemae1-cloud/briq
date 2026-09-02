/**
 * Brand hero banners for shop category pages when a brand chip is selected.
 * Images live under `/banners/brand-<key>-N.jpg` (PC / t / m via weekly refresh).
 */

export type BrandKey =
  | "gucci"
  | "burberry"
  | "chanel"
  | "chanel-watches"
  | "dior-watches"
  | "dior-bags"
  | "dior-mens-rtw"
  | "dior-womens-rtw"
  | "dior-accessories"
  | "dior-shoes"
  | "prada"
  | "arcteryx"
  | "paul-smith"
  | "belstaff"
  | "galvin-green"
  | "christopher-ward"
  | "louis-vuitton"
  | "dior"
  | "london-undercover";

export type BrandHeroDef = {
  key: BrandKey;
  nameEn: string;
  nameKo: string;
  /** Elegant wordmark / monogram SVG (ships with the app, not the media tag). */
  logoSrc: string;
  /** Shop-strip banners — weekly refresh rotates source photography. */
  images: string[];
};

export const brandHeroes: Record<BrandKey, BrandHeroDef> = {
  gucci: {
    key: "gucci",
    nameEn: "Gucci",
    nameKo: "구찌",
    logoSrc: "/brands/gucci.svg",
    images: [
      "/banners/brand-gucci-1.jpg",
      "/banners/brand-gucci-2.jpg",
      "/banners/brand-gucci-3.jpg",
    ],
  },
  burberry: {
    key: "burberry",
    nameEn: "Burberry",
    nameKo: "버버리",
    logoSrc: "/brands/burberry.svg",
    // Locked scarf campaign creative (A Good Sport / Romeo Beckham) — head to shoulders.
    images: ["/banners/brand-burberry-scarf.jpg"],
  },
  chanel: {
    key: "chanel",
    nameEn: "Chanel",
    nameKo: "샤넬",
    logoSrc: "/brands/chanel.svg",
    // Locked Como cruise bag creative — bags / shoes / accessories (not watches).
    images: ["/banners/brand-chanel-como-bag.jpg"],
  },
  "chanel-watches": {
    key: "chanel-watches",
    nameEn: "Chanel",
    nameKo: "샤넬",
    logoSrc: "/brands/chanel.svg",
    // Locked Première creative — watches only.
    images: ["/banners/brand-chanel-premiere.jpg"],
  },
  prada: {
    key: "prada",
    nameEn: "Prada",
    nameKo: "프라다",
    logoSrc: "/brands/prada.svg",
    // Locked Linea Rossa campaign creative — head to chest.
    images: ["/banners/brand-prada-linea-rossa.jpg"],
  },
  arcteryx: {
    key: "arcteryx",
    nameEn: "Arc'teryx",
    nameKo: "아크테릭스",
    logoSrc: "/brands/arcteryx.svg",
    // Locked Who We Are ridge creative — all Arc'teryx category heroes.
    images: ["/banners/brand-arcteryx-ridge.jpg"],
  },
  "paul-smith": {
    key: "paul-smith",
    nameEn: "Paul Smith",
    nameKo: "폴 스미스",
    logoSrc: "/brands/paul-smith.svg",
    images: [
      "/banners/brand-paul-smith-1.jpg",
      "/banners/brand-paul-smith-2.jpg",
      "/banners/brand-paul-smith-3.jpg",
    ],
  },
  belstaff: {
    key: "belstaff",
    nameEn: "Belstaff",
    nameKo: "벨스타프",
    logoSrc: "/brands/belstaff.svg",
    images: [
      "/banners/brand-belstaff-1.jpg",
      "/banners/brand-belstaff-2.jpg",
      "/banners/brand-belstaff-3.jpg",
    ],
  },
  "galvin-green": {
    key: "galvin-green",
    nameEn: "Galvin Green",
    nameKo: "갈빈 그린",
    logoSrc: "/brands/galvin-green.svg",
    images: [
      "/banners/brand-galvin-green-1.jpg",
      "/banners/brand-galvin-green-2.jpg",
      "/banners/brand-galvin-green-3.jpg",
    ],
  },
  "christopher-ward": {
    key: "christopher-ward",
    nameEn: "Christopher Ward",
    nameKo: "크리스토퍼와드",
    logoSrc: "/brands/christopher-ward.svg",
    // Locked C1 Moonphase creative — not rotated weekly.
    images: ["/banners/brand-christopher-ward-moonphase.jpg"],
  },
  "louis-vuitton": {
    key: "louis-vuitton",
    nameEn: "Louis Vuitton",
    nameKo: "루이 비통",
    logoSrc: "/brands/louis-vuitton.svg",
    images: [
      "/banners/rot-acc-1.jpg",
      "/banners/rot-acc-2.jpg",
      "/banners/rot-acc-3.jpg",
    ],
  },
  dior: {
    key: "dior",
    nameEn: "Dior",
    nameKo: "디올",
    logoSrc: "/brands/dior.svg",
    // Locked women's RTW campaign — grass / countryside (all-ready-to-wear PLP).
    images: ["/banners/brand-dior-womens-rtw.jpg"],
  },
  "dior-watches": {
    key: "dior-watches",
    nameEn: "Dior",
    nameKo: "디올",
    logoSrc: "/brands/dior.svg",
    images: [
      "/banners/rot-acc-1.jpg",
      "/banners/rot-acc-2.jpg",
      "/banners/rot-acc-3.jpg",
    ],
  },
  "dior-bags": {
    key: "dior-bags",
    nameEn: "Dior",
    nameKo: "디올",
    logoSrc: "/brands/dior.svg",
    // Locked All Bags campaign creative — forest bench / Dior Promenade bag.
    images: ["/banners/brand-dior-bags.jpg"],
  },
  "dior-mens-rtw": {
    key: "dior-mens-rtw",
    nameEn: "Dior",
    nameKo: "디올",
    logoSrc: "/brands/dior.svg",
    // Locked men's RTW campaign — boat / technical jacket (all-ready-to-wear PLP).
    images: ["/banners/brand-dior-mens-rtw.jpg"],
  },
  "dior-womens-rtw": {
    key: "dior-womens-rtw",
    nameEn: "Dior",
    nameKo: "디올",
    logoSrc: "/brands/dior.svg",
    // Locked women's RTW campaign creative.
    images: ["/banners/brand-dior-womens-rtw.jpg"],
  },
  "dior-accessories": {
    key: "dior-accessories",
    nameEn: "Dior",
    nameKo: "디올",
    logoSrc: "/brands/dior.svg",
    // Locked jewelry campaign — Rose des Vents necklace (necklaces PLP).
    images: ["/banners/brand-dior-accessories.jpg"],
  },
  "dior-shoes": {
    key: "dior-shoes",
    nameEn: "Dior",
    nameKo: "디올",
    logoSrc: "/brands/dior.svg",
    // Reuse men's fashion campaign until a dedicated shoes PLP hero is locked.
    images: ["/banners/brand-dior-mens-rtw.jpg"],
  },
  "london-undercover": {
    key: "london-undercover",
    nameEn: "London Undercover",
    logoSrc: "/brands/london-undercover.svg",
    nameKo: "런던언더커버",
    images: [
      "/banners/brand-london-undercover-1.jpg",
      "/banners/brand-london-undercover-2.jpg",
      "/banners/brand-london-undercover-3.jpg",
    ],
  },
};

/** Top-level shop nav brand nodes → canonical brand key. */
export const brandRootToKey: Record<string, BrandKey> = {
  gucci: "gucci",
  "gucci-bags": "gucci",
  "gucci-shoes": "gucci",
  "gucci-accessories": "gucci",
  burberry: "burberry",
  "burberry-bags": "burberry",
  "burberry-shoes": "burberry",
  "burberry-accessories": "burberry",
  "burberry-gifts": "burberry",
  chanel: "chanel",
  "chanel-bags": "chanel",
  "chanel-shoes": "chanel",
  "chanel-accessories": "chanel",
  "chanel-watches": "chanel-watches",
  "ch-watches": "chanel-watches",
  prada: "prada",
  "prada-bags": "prada",
  "prada-luxury": "prada",
  "prada-shoes": "prada",
  "prada-accessories": "prada",
  "pr-linea-rossa": "prada",
  "pr-linea-rossa-women": "prada",
  "pr-linea-rossa-men": "prada",
  "pr-linea-rossa-sunglasses": "prada",
  "pr-linea-rossa-shoes": "prada",
  "pr-linea-rossa-fragrances": "prada",
  arcteryx: "arcteryx",
  "arcteryx-bags": "arcteryx",
  "arcteryx-shoes": "arcteryx",
  "arcteryx-accessories": "arcteryx",
  "ax-climbing-gear": "arcteryx",
  "ax-climbing-womens": "arcteryx",
  "ax-climbing-mens": "arcteryx",
  "paul-smith": "paul-smith",
  "paul-smith-shoes": "paul-smith",
  "paul-smith-accessories": "paul-smith",
  belstaff: "belstaff",
  "belstaff-bags": "belstaff",
  "belstaff-shoes": "belstaff",
  "belstaff-accessories": "belstaff",
  "galvin-green": "galvin-green",
  "christopher-ward": "christopher-ward",
  "louis-vuitton": "louis-vuitton",
  "louis-vuitton-accessories": "louis-vuitton",
  "lv-home-lifestyle": "louis-vuitton",
  "lv-furniture-lighting": "louis-vuitton",
  dior: "dior",
  "dior-accessories": "dior-accessories",
  "dior-shoes": "dior-shoes",
  "di-men-shoes": "dior-shoes",
  "di-men-shoes-all": "dior-shoes",
  "di-men-sneakers": "dior-shoes",
  "di-men-sandals-mules": "dior-shoes",
  "di-men-loafers": "dior-shoes",
  "di-men-lace-ups": "dior-shoes",
  "di-men-boots": "dior-shoes",
  "di-home": "dior",
  "di-tableware": "dior",
  "di-objects": "dior",
  "di-objects-all": "dior",
  "di-books": "dior",
  "di-notebooks": "dior",
  "di-desk-accessories": "dior",
  "di-candleholders-candles": "dior",
  "di-small-objects": "dior",
  "di-trinket-trays": "dior",
  "di-trays": "dior",
  "di-leisure": "dior",
  "di-paperweights": "dior",
  "di-decor": "dior",
  "di-decor-all": "dior",
  "di-decorative-pieces": "dior",
  "di-lighting": "dior",
  "di-baskets": "dior",
  "di-wallpapers": "dior",
  "di-vases": "dior",
  "di-furniture": "dior",
  "di-textile": "dior",
  "di-textile-all": "dior",
  "di-cushions": "dior",
  "di-bath-linen": "dior",
  "di-table-linen": "dior",
  "di-throws": "dior",
  "di-jewelry-timepieces": "dior-accessories",
  "di-jewelry-all": "dior-accessories",
  "di-earrings": "dior-accessories",
  "di-bracelets": "dior-accessories",
  "di-rings": "dior-accessories",
  "di-necklaces": "dior-accessories",
  "di-dior-icons": "dior-accessories",
  "di-men-accessories": "dior-accessories",
  "di-men-acc-all": "dior-accessories",
  "di-men-sunglasses": "dior-accessories",
  "di-men-belts": "dior-accessories",
  "di-men-ties-pocket-squares": "dior-accessories",
  "di-men-scarves": "dior-accessories",
  "di-men-hats-gloves": "dior-accessories",
  "di-men-socks": "dior-accessories",
  "di-men-fashion-jewelry": "dior-accessories",
  "di-men-silver-jewelry": "dior-accessories",
  "di-men-key-rings": "dior-accessories",
  "di-men-charm-jewelry": "dior-accessories",
  "di-men-lifestyle": "dior-accessories",
  "di-men-acc-tech": "dior-accessories",
  "di-men-pet-accessories": "dior-accessories",
  "di-men-slg": "dior-accessories",
  "di-men-slg-all": "dior-accessories",
  "di-men-card-holders": "dior-accessories",
  "di-men-compact-wallets": "dior-accessories",
  "di-men-long-wallets": "dior-accessories",
  "di-men-pouches": "dior-accessories",
  "di-men-tech-accessories": "dior-accessories",
  "dior-watches": "dior-watches",
  "di-timepieces-all": "dior-watches",
  "di-la-d-de-dior": "dior-watches",
  "di-straps": "dior-watches",
  "dior-bags": "dior-bags",
  "di-bags-womens": "dior-bags",
  "di-bags-all": "dior-bags",
  "di-handbags": "dior-bags",
  "di-crossbody-shoulder-bags": "dior-bags",
  "di-tote-bags": "dior-bags",
  "di-bucket-bags": "dior-bags",
  "di-clutches": "dior-bags",
  "di-mini-bags": "dior-bags",
  "di-accessorize-bag": "dior-bags",
  "di-bags-mens": "dior-bags",
  "di-men-bags-all": "dior-bags",
  "di-men-crossbody-shoulder-bags": "dior-bags",
  "di-men-backpacks": "dior-bags",
  "di-men-small-bags": "dior-bags",
  "di-men-tote-bags": "dior-bags",
  "di-men-travel-bags": "dior-bags",
  "di-men-briefcases": "dior-bags",
  "di-men-accessorize-bag": "dior-bags",
  "di-mens": "dior-mens-rtw",
  "di-men-rtw-all": "dior-mens-rtw",
  "di-men-tshirts-polos": "dior-mens-rtw",
  "di-men-shirts": "dior-mens-rtw",
  "di-men-knitwear-sweatshirts": "dior-mens-rtw",
  "di-men-trousers-shorts": "dior-mens-rtw",
  "di-men-denim": "dior-mens-rtw",
  "di-men-beachwear": "dior-mens-rtw",
  "di-men-outerwear": "dior-mens-rtw",
  "di-men-tailored-jackets": "dior-mens-rtw",
  "di-men-leather": "dior-mens-rtw",
  "di-men-suits-tuxedos": "dior-mens-rtw",
  "di-womens": "dior-womens-rtw",
  "di-women-rtw-all": "dior-womens-rtw",
  "di-women-tshirts": "dior-womens-rtw",
  "di-women-shirts": "dior-womens-rtw",
  "di-women-sweaters-cardigans": "dior-womens-rtw",
  "di-women-dresses": "dior-womens-rtw",
  "di-women-skirts": "dior-womens-rtw",
  "di-women-trousers-shorts": "dior-womens-rtw",
  "di-women-denim": "dior-womens-rtw",
  "di-women-swimsuits": "dior-womens-rtw",
  "di-women-homewear-lingerie": "dior-womens-rtw",
  "di-women-coats": "dior-womens-rtw",
  "di-women-jackets": "dior-womens-rtw",
  "london-undercover": "london-undercover",
  umbrellas: "london-undercover",
};

/** Flat list of every brand banner path (for weekly refresh references). */
export const allBrandHeroImages: string[] = Object.values(brandHeroes).flatMap(
  (b) => b.images,
);
