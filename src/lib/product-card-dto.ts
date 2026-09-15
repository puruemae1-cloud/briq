import type { Product } from "@/data/product-types";

/**
 * Slim product for PLP/cards — omit heavy PDP-only fields and variant galleries.
 * Card media uses `image` / `images` / `hoverImage` (colourway expand already
 * promotes the lead colour onto those fields).
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
    tags: p.tags?.slice(0, 12),
    image: p.image,
    images: p.images?.slice(0, 4),
    hoverImage: p.hoverImage,
    accent: p.accent,
    badge: p.badge,
    sku: p.sku,
    inStock: p.inStock,
    registeredAt: p.registeredAt,
    editTier: p.editTier,
    shopColorKey: p.shopColorKey,
    cwCollections: p.cwCollections,
    ggCollections: p.ggCollections,
    // Prices + stock only — enough for `~` ranges and sold-out badges.
    variants: p.variants?.map((v) => ({
      id: v.id,
      price: v.price,
      compareAtPrice: v.compareAtPrice,
      inStock: v.inStock,
      colorKey: v.colorKey,
      name: v.name,
      nameKo: v.nameKo,
    })),
  };
}
