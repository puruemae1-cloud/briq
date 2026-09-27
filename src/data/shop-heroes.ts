import { pickBanner } from "@/data/home-banners";
import { resolveShopBrand } from "@/lib/shop-brand";

/**
 * Shop / subcategory page heroes — one fixed image per slot (no rotation).
 * Brand chips (Gucci, Burberry, …) use dedicated brand-* banners.
 * Key: `category` or `category:sub`.
 */
const shopHeroImages: Record<string, string[]> = {
  luxury: ["/banners/shop-luxury-signature.jpg"],
  "luxury:womens": ["/banners/rot-luxury-1.jpg"],
  "luxury:mens": ["/banners/rot-luxury-2.jpg"],
  "luxury:bottega-veneta": ["/banners/brand-bottega-veneta-clothing.jpg"],
  "luxury:chanel": ["/banners/brand-chanel.jpg"],
  "luxury:gucci": ["/banners/brand-gucci.jpg"],
  "luxury:celine": ["/banners/brand-celine-signature.jpg"],
  "luxury:saint-laurent": ["/banners/brand-saint-laurent.jpg"],
  "luxury:all-saints": ["/banners/brand-all-saints.jpg"],
  "luxury:paul-smith": ["/banners/brand-paul-smith-1.jpg"],

  watches: ["/banners/rot-watch-3.jpg"],
  "watches:christopher-ward": [
    "/banners/brand-christopher-ward-moonphase.jpg",
  ],
  "watches:chanel-watches": ["/banners/brand-chanel-premiere.jpg"],
  "bags:chanel-bags": ["/banners/brand-chanel-como-bag.jpg"],
  "bags:gucci-bags": ["/banners/brand-gucci-handbags.jpg"],
  "bags:saint-laurent-bags": ["/banners/brand-saint-laurent-bags.jpg"],
  "bags:vivienne-westwood-bags": ["/banners/brand-vivienne-westwood-bags.jpg"],
  "bags:vw-bags": ["/banners/brand-vivienne-westwood-bags.jpg"],
  "bags:vw-women-bags": ["/banners/brand-vivienne-westwood-bags.jpg"],
  "bags:vw-men-bags": ["/banners/brand-vivienne-westwood-bags.jpg"],
  "bags:bottega-veneta-bags": ["/banners/brand-bottega-veneta-bags.jpg"],
  "bags:prada-bags": ["/banners/brand-prada-bags.jpg"],
  "bags:burberry-bags": ["/banners/brand-burberry-bags.jpg"],
  "bags:mulberry-bags": ["/banners/brand-mulberry-bags.jpg"],
  "shoes:chanel-shoes": ["/banners/brand-chanel-shoes.jpg"],
  "shoes:gucci-shoes": ["/banners/brand-gucci-shoes.jpg"],
  "shoes:bottega-veneta-shoes": ["/banners/brand-bottega-veneta-shoes.jpg"],
  "shoes:dior-shoes": ["/banners/brand-dior-shoes.jpg"],
  "shoes:prada-shoes": ["/banners/brand-prada-shoes.jpg"],
  "shoes:burberry-shoes": ["/banners/brand-burberry-shoes.jpg"],
  "accessories:chanel-accessories": ["/banners/brand-chanel-como-bag.jpg"],
  "accessories:mulberry-accessories": ["/banners/brand-mulberry-accessories.jpg"],
  "accessories:bottega-veneta-accessories": ["/banners/brand-bottega-veneta-accessories.jpg"],

  clothing: ["/banners/rot-cloth-3.jpg"],
  "clothing:womens": ["/banners/shop-cloth-1.jpg"],
  "clothing:mens": ["/banners/shop-cloth-1.jpg"],

  bags: ["/banners/shop-bags-chanel.jpg"],

  shoes: ["/banners/rot-shoe-3.jpg"],

  accessories: ["/banners/shop-accessories-prada.jpg"],

  sports: ["/banners/rot-golf-1.jpg"],
  "sports:golf": [
    "/banners/brand-galvin-green.jpg",
  ],
  "sports:galvin-green": [
    "/banners/brand-galvin-green.jpg",
  ],
  "sports:running": ["/banners/rot-run-1.jpg"],
  "sports:swimming": ["/banners/rot-swim-3.jpg"],
  "sports:cycling": ["/banners/rot-cycle-3.jpg"],
  "sports:tennis": ["/banners/rot-tennis-3.jpg"],
};

const FALLBACK = ["/banners/rot-hero-3.jpg"];

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

export function pickShopHero(category?: string, sub?: string): string {
  return pickBanner(getShopHeroImages(category, sub));
}
