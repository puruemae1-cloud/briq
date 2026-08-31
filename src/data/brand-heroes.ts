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
    images: [
      "/banners/rot-acc-1.jpg",
      "/banners/rot-acc-2.jpg",
      "/banners/rot-acc-3.jpg",
    ],
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
    images: [
      "/banners/rot-acc-1.jpg",
      "/banners/rot-acc-2.jpg",
      "/banners/rot-acc-3.jpg",
    ],
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
  "dior-accessories": "dior",
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
  "di-jewelry-timepieces": "dior",
  "di-jewelry-all": "dior",
  "di-earrings": "dior",
  "di-bracelets": "dior",
  "di-rings": "dior",
  "di-necklaces": "dior",
  "di-dior-icons": "dior",
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
  "london-undercover": "london-undercover",
  umbrellas: "london-undercover",
};

/** Flat list of every brand banner path (for weekly refresh references). */
export const allBrandHeroImages: string[] = Object.values(brandHeroes).flatMap(
  (b) => b.images,
);
