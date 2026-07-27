/**
 * Briq product photo standard
 * ----------------------------
 * Every catalog photo is rendered inside a fixed 4:5 frame with
 * `object-fit: contain`, so mixed camera crops / brand assets still
 * line up cleanly on the homepage, shop grids, PDP, and cart.
 *
 * When adding or replacing product images under `/public/products/`:
 * - Prefer JPG/WebP, ~1600×2000 (4:5) or larger with the same ratio
 * - Subject centered; leave a little breathing room around the item
 * - Plain / soft studio background preferred (frame fills the rest)
 * - Avoid extreme close-ups that crop the product edge
 * - Variant colors should share the same framing & crop style
 *
 * Do not rely on CSS `cover` for catalog photos — always go through
 * `ProductImage` / `.product-frame` so future updates stay uniform.
 */

export const PRODUCT_IMAGE = {
  /** Canonical display ratio for cards, PDP, cart thumbs */
  aspect: "4 / 5",
  /** Recommended upload size (width × height) */
  uploadWidth: 1600,
  uploadHeight: 2000,
  /** Soft studio mat behind every product photo */
  frameBg: "#f3f2ed",
} as const;

export type ProductImageTone = "card" | "detail" | "cart" | "swatch";

/** Resolves the catalog image to show for a product / optional variant. */
export function resolveProductImage(
  productImage: string,
  variantImage?: string | null,
) {
  return variantImage?.trim() || productImage;
}
