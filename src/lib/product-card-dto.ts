import type { Product } from "@/data/product-types";

/** Max gallery frames serialized into PLP/card HTML (RSC flight). */
export const CARD_GALLERY_LIMIT = 2;

/**
 * Slim product for PLP/cards — omit heavy PDP-only fields.
 * Serialized into every shop/home HTML response Yeti downloads, so keep tiny.
 */
export function toCardProduct(p: Product): Product {
  const images = p.images?.slice(0, CARD_GALLERY_LIMIT);
  return {
    id: p.id,
    name: p.name,
    nameKo: p.nameKo,
    brand: p.brand,
    price: p.price,
    compareAtPrice: p.compareAtPrice,
    category: p.category,
    subcategory: p.subcategory,
    image: p.image,
    images,
    hoverImage: p.hoverImage,
    badge: p.badge,
    inStock: p.inStock,
    registeredAt: p.registeredAt,
    newBadgeAt: p.newBadgeAt,
    shopColorKey: p.shopColorKey,
    cwCollections: p.cwCollections,
    ggCollections: p.ggCollections,
    // Price-range + colourway only — no per-variant image galleries in HTML.
    variants: p.variants?.map((v) => ({
      id: v.id,
      price: v.price,
      compareAtPrice: v.compareAtPrice,
      image: v.image,
      hoverImage: v.hoverImage,
      inStock: v.inStock,
      colorKey: v.colorKey,
    })),
  };
}
