/**
 * Brand hero banners for shop category pages when a brand chip is selected.
 * Images live under `/banners/brand-<key>-N.jpg` (PC / t / m via weekly refresh).
 */

export type BrandKey =
  | "gucci"
  | "burberry"
  | "chanel"
  | "prada"
  | "arcteryx"
  | "paul-smith"
  | "belstaff"
  | "galvin-green"
  | "christopher-ward"
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
    images: [
      "/banners/brand-burberry-1.jpg",
      "/banners/brand-burberry-2.jpg",
      "/banners/brand-burberry-3.jpg",
    ],
  },
  chanel: {
    key: "chanel",
    nameEn: "Chanel",
    nameKo: "샤넬",
    logoSrc: "/brands/chanel.svg",
    images: [
      "/banners/brand-chanel-1.jpg",
      "/banners/brand-chanel-2.jpg",
      "/banners/brand-chanel-3.jpg",
    ],
  },
  prada: {
    key: "prada",
    nameEn: "Prada",
    nameKo: "프라다",
    logoSrc: "/brands/prada.svg",
    images: [
      "/banners/brand-prada-1.jpg",
      "/banners/brand-prada-2.jpg",
      "/banners/brand-prada-3.jpg",
    ],
  },
  arcteryx: {
    key: "arcteryx",
    nameEn: "Arc'teryx",
    nameKo: "아크테릭스",
    logoSrc: "/brands/arcteryx.svg",
    images: [
      "/banners/brand-arcteryx-1.jpg",
      "/banners/brand-arcteryx-2.jpg",
      "/banners/brand-arcteryx-3.jpg",
    ],
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
    images: [
      "/banners/brand-christopher-ward-1.jpg",
      "/banners/brand-christopher-ward-2.jpg",
      "/banners/brand-christopher-ward-3.jpg",
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
  "chanel-watches": "chanel",
  prada: "prada",
  "prada-bags": "prada",
  "prada-luxury": "prada",
  arcteryx: "arcteryx",
  "arcteryx-bags": "arcteryx",
  "arcteryx-shoes": "arcteryx",
  "arcteryx-accessories": "arcteryx",
  "paul-smith": "paul-smith",
  "paul-smith-shoes": "paul-smith",
  "paul-smith-accessories": "paul-smith",
  belstaff: "belstaff",
  "belstaff-bags": "belstaff",
  "belstaff-shoes": "belstaff",
  "belstaff-accessories": "belstaff",
  "galvin-green": "galvin-green",
  "christopher-ward": "christopher-ward",
  "london-undercover": "london-undercover",
  umbrellas: "london-undercover",
};

/** Flat list of every brand banner path (for weekly refresh references). */
export const allBrandHeroImages: string[] = Object.values(brandHeroes).flatMap(
  (b) => b.images,
);
