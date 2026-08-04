/**
 * Briq product photo standard
 * ----------------------------
 * Every catalog photo is rendered inside a fixed 4:5 frame with
 * `object-fit: contain`, so mixed camera crops / brand assets still
 * line up cleanly on the homepage, shop grids, PDP, and cart.
 *
 * When adding or replacing product images under `/public/products/`:
 * - Prefer JPG/WebP, ~1600×2000 (4:5) or larger with the same ratio
 * - Subject centered; leave generous studio-style breathing room around the item
 *   (CSS frame pad ~15% so tiles match a Gucci-like PLP scale, not edge-to-edge)
 * - Plain / soft studio background preferred (frame fills the rest)
 * - Avoid extreme close-ups that crop the product edge
 * - Variant colors should share the same framing & crop style
 * - Gallery order: [0] packshot / dial face, [1] model wear or wrist shot
 *   (used automatically for PC card hover). Override with `hoverImage`
 *   when the second gallery frame is not the lifestyle cut.
 *
 * Do not rely on CSS `cover` for catalog photos — always go through
 * `ProductImage` / `.product-frame` so future updates stay uniform.
 */

import type { Product, ProductVariant } from "@/data/products";

export const PRODUCT_IMAGE = {
  /** Canonical display ratio for cards, PDP, cart thumbs */
  aspect: "4 / 5",
  /** Recommended upload size (width × height) */
  uploadWidth: 1600,
  uploadHeight: 2000,
  /** Soft studio mat behind every product photo */
  frameBg: "#f5f5f5",
} as const;

export type ProductImageTone = "card" | "detail" | "cart" | "swatch";

/** Resolves the catalog image to show for a product / optional variant. */
export function resolveProductImage(
  productImage: string,
  variantImage?: string | null,
) {
  return variantImage?.trim() || productImage;
}

function uniqueGallery(paths: Array<string | undefined | null>): string[] {
  const out: string[] = [];
  const seen = new Set<string>();
  for (const raw of paths) {
    const src = raw?.trim();
    if (!src || seen.has(src)) continue;
    seen.add(src);
    out.push(src);
  }
  return out;
}

/** Gallery used for a shop card (honours colourway expand via shopColorKey). */
export function resolveCardGallery(product: Product): string[] {
  if (product.shopColorKey && product.variants?.length) {
    const colour = product.variants.find(
      (v) => v.colorKey === product.shopColorKey,
    );
    if (colour) {
      return uniqueGallery([
        colour.hoverImage,
        ...(colour.images ?? []),
        colour.image,
        product.hoverImage,
        ...(product.images ?? []),
        product.image,
      ]);
    }
  }

  return uniqueGallery([
    product.hoverImage,
    ...(product.images ?? []),
    product.image,
    ...(product.variants ?? []).flatMap((v) => [
      v.hoverImage,
      ...(v.images ?? []),
      v.image,
    ]),
  ]);
}

/**
 * Second photo for PC card hover — model wear / wrist shot when available.
 * Explicit `hoverImage` wins; otherwise the first gallery frame that differs
 * from the primary card image (typically images[1]).
 */
export function resolveCardHoverImage(product: Product): string | undefined {
  const primary = product.image?.trim();
  if (!primary) return undefined;

  if (product.shopColorKey && product.variants?.length) {
    const colour = product.variants.find(
      (v) => v.colorKey === product.shopColorKey,
    ) as ProductVariant | undefined;
    if (colour?.hoverImage && colour.hoverImage !== primary) {
      return colour.hoverImage;
    }
  }

  if (product.hoverImage && product.hoverImage !== primary) {
    return product.hoverImage;
  }

  const gallery = resolveCardGallery(product);
  return gallery.find((src) => src !== primary);
}
