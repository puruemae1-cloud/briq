import { brandHeroes } from "@/data/brand-heroes";
import { pickRotating } from "@/data/home-banners";
import { resolveShopBrand } from "@/lib/shop-brand";

/**
 * Shop / subcategory page heroes — rotate every week via pickRotating.
 * Brand chips (Gucci, Burberry, …) use dedicated brand-* banners.
 * Key: `category` or `category:sub`.
 */
const shopHeroImages: Record<string, string[]> = {
  luxury: [
    "/banners/rot-luxury-1.jpg",
    "/banners/rot-luxury-2.jpg",
    "/banners/rot-luxury-3.jpg",
  ],
  "luxury:womens": [
    "/banners/shop-lux-w-1.jpg",
    "/banners/shop-lux-w-2.jpg",
    "/banners/rot-luxury-1.jpg",
  ],
  "luxury:mens": [
    "/banners/shop-lux-m-1.jpg",
    "/banners/shop-lux-m-2.jpg",
    "/banners/rot-luxury-2.jpg",
  ],

  watches: [
    "/banners/rot-watch-1.jpg",
    "/banners/rot-watch-2.jpg",
    "/banners/rot-watch-3.jpg",
  ],
  "watches:christopher-ward": [
    "/banners/brand-christopher-ward-moonphase.jpg",
  ],

  clothing: [
    "/banners/rot-cloth-1.jpg",
    "/banners/rot-cloth-2.jpg",
    "/banners/rot-cloth-3.jpg",
  ],
  "clothing:womens": [
    "/banners/shop-cloth-w-1.jpg",
    "/banners/rot-cloth-1.jpg",
    "/banners/shop-cloth-1.jpg",
  ],
  "clothing:mens": [
    "/banners/shop-cloth-m-1.jpg",
    "/banners/rot-cloth-2.jpg",
    "/banners/shop-cloth-1.jpg",
  ],

  bags: [
    "/banners/rot-bag-1.jpg",
    "/banners/rot-bag-2.jpg",
    "/banners/rot-bag-3.jpg",
    "/banners/shop-bag-1.jpg",
  ],

  shoes: [
    "/banners/rot-shoe-1.jpg",
    "/banners/rot-shoe-2.jpg",
    "/banners/rot-shoe-3.jpg",
  ],
  "shoes:luxury-shoes": [
    "/banners/shop-shoe-lux-w-1.jpg",
    "/banners/shop-shoe-lux-m-1.jpg",
    "/banners/rot-shoe-1.jpg",
  ],
  "shoes:luxury-womens": [
    "/banners/shop-shoe-lux-w-1.jpg",
    "/banners/rot-shoe-3.jpg",
    "/banners/shop-shoe-lux-w-1.jpg",
  ],
  "shoes:luxury-mens": [
    "/banners/shop-shoe-lux-m-1.jpg",
    "/banners/rot-shoe-1.jpg",
    "/banners/shop-shoe-lux-m-1.jpg",
  ],
  "shoes:training-shoes": [
    "/banners/shop-shoe-train-w-1.jpg",
    "/banners/shop-shoe-train-m-1.jpg",
    "/banners/rot-shoe-2.jpg",
  ],
  "shoes:training-womens": [
    "/banners/shop-shoe-train-w-1.jpg",
    "/banners/rot-run-2.jpg",
    "/banners/shop-shoe-train-w-1.jpg",
  ],
  "shoes:training-mens": [
    "/banners/shop-shoe-train-m-1.jpg",
    "/banners/rot-shoe-2.jpg",
    "/banners/shop-shoe-train-m-1.jpg",
  ],

  accessories: [
    "/banners/rot-acc-1.jpg",
    "/banners/rot-acc-2.jpg",
    "/banners/rot-acc-3.jpg",
  ],

  sports: [
    "/banners/rot-golf-1.jpg",
    "/banners/rot-cycle-1.jpg",
    "/banners/rot-swim-1.jpg",
    "/banners/rot-run-1.jpg",
    "/banners/rot-tennis-1.jpg",
  ],
  "sports:golf": [
    "/banners/rot-golf-1.jpg",
    "/banners/rot-golf-2.jpg",
    "/banners/rot-golf-3.jpg",
    "/banners/shop-golf-1.jpg",
  ],
  "sports:running": [
    "/banners/rot-run-1.jpg",
    "/banners/rot-run-2.jpg",
    "/banners/rot-run-3.jpg",
    "/banners/shop-run-1.jpg",
  ],
  "sports:swimming": [
    "/banners/rot-swim-1.jpg",
    "/banners/rot-swim-2.jpg",
    "/banners/rot-swim-3.jpg",
  ],
  "sports:cycling": [
    "/banners/rot-cycle-1.jpg",
    "/banners/rot-cycle-2.jpg",
    "/banners/rot-cycle-3.jpg",
  ],
  "sports:tennis": [
    "/banners/rot-tennis-1.jpg",
    "/banners/rot-tennis-2.jpg",
    "/banners/rot-tennis-3.jpg",
  ],
};

const FALLBACK = [
  "/banners/rot-hero-1.jpg",
  "/banners/rot-hero-2.jpg",
  "/banners/rot-hero-3.jpg",
];

export function getShopHeroImages(category?: string, sub?: string): string[] {
  const brand = resolveShopBrand(category, sub);
  if (brand?.images?.length) return brand.images;

  if (category && category !== "all") {
    if (sub) {
      const keyed = shopHeroImages[`${category}:${sub}`];
      if (keyed?.length) return keyed;
    }
    const cat = shopHeroImages[category];
    if (cat?.length) return cat;
  }
  return FALLBACK;
}

/** Re-export so banner refresh can discover brand-* paths via this module. */
export const brandHeroImagePaths = Object.values(brandHeroes).flatMap(
  (b) => b.images,
);

export function pickShopHero(category?: string, sub?: string, offset = 0): string {
  return pickRotating(getShopHeroImages(category, sub), offset);
}
