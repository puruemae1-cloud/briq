import type { Product, ProductVariant } from "@/data/product-types";

/** Max gallery frames serialized into PLP/card HTML (RSC flight). */
export const CARD_GALLERY_LIMIT = 2;

/** Slim variant fields needed for card price range + colourway gallery. */
function toCardVariant(v: ProductVariant): ProductVariant {
  return {
    id: v.id,
    name: v.name,
    nameKo: v.nameKo,
    sku: "",
    gbpPrice: 0,
    price: v.price,
    compareAtPrice: v.compareAtPrice,
    image: v.image,
    hoverImage: v.hoverImage,
    sourceUrl: "",
    inStock: v.inStock,
    colorKey: v.colorKey,
  };
}

/**
 * Slim product for PLP/cards — omit heavy PDP-only fields.
 * Serialized into every shop/home HTML response Yeti downloads, so keep tiny.
 */
export function toCardProduct(p: Product): Product {
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
    images: p.images?.slice(0, CARD_GALLERY_LIMIT),
    hoverImage: p.hoverImage,
    badge: p.badge,
    inStock: p.inStock,
    registeredAt: p.registeredAt,
    newBadgeAt: p.newBadgeAt,
    shopColorKey: p.shopColorKey,
    cwCollections: p.cwCollections,
    ggCollections: p.ggCollections,
    variants: p.variants?.map(toCardVariant),
  };
}
