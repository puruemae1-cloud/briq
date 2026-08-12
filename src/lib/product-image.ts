/**
 * Briq product photo standard
 * ----------------------------
 * Every catalog photo is rendered inside a fixed 4:5 frame with
 * `object-fit: contain`, so mixed camera crops / brand assets still
 * line up cleanly on the homepage, shop grids, PDP, and cart.
 *
 * When adding or replacing product images under `/public/products/`:
 * - Prefer JPG/WebP, ~1600×2000 (4:5) or larger with the same ratio
 * - Subject centered; CSS frame pad is minimal so white studio mats blend with the page
 * - Plain / soft studio background preferred (White for Gucci packshots)
 * - Avoid extreme close-ups that crop the product edge
 * - Variant colors should share the same framing & crop style
 * - Gallery order for cards: [0] primary packshot, [1+] remaining frames
 *   (hover / PLP swap should be included but primary stays first)
 * - Card hover / carousel uses official PLP swap order when possible
 *   (Gucci: on-model type-100; Arc'teryx: *-Hover.jpg; Paul Smith: PLP imageInfo[1])
 *
 * Do not rely on CSS `cover` for catalog photos — always go through
 * `ProductImage` / `.product-frame` so future updates stay uniform.
 */

import type {  Product, ProductVariant  } from "@/data/product-types";

export const PRODUCT_IMAGE = {
  /** Canonical display ratio for cards, PDP, cart thumbs */
  aspect: "4 / 5",
  /** Recommended upload size (width × height) */
  uploadWidth: 1600,
  uploadHeight: 2000,
  /** Clean white mat behind every product photo (matches page) */
  frameBg: "#ffffff",
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

function colourwayGallery(product: Product): string[] {
  if (product.shopColorKey && product.variants?.length) {
    const colour = product.variants.find(
      (v) => v.colorKey === product.shopColorKey,
    );
    if (colour) {
      return uniqueGallery([
        colour.image,
        colour.hoverImage,
        ...(colour.images ?? []),
        product.image,
        product.hoverImage,
        ...(product.images ?? []),
      ]);
    }
  }

  return uniqueGallery([
    product.image,
    product.hoverImage,
    ...(product.images ?? []),
    ...(product.variants ?? []).flatMap((v) => [
      v.image,
      v.hoverImage,
      ...(v.images ?? []),
    ]),
  ]);
}

/**
 * Gallery for shop cards — primary packshot first, then hover + remaining frames.
 * Caps length so PLP carousels stay light.
 */
export function resolveCardGallery(product: Product, limit = 8): string[] {
  return colourwayGallery(product).slice(0, Math.max(1, limit));
}

/**
 * Second photo for PC card hover — official PLP swap image when available.
 * Explicit `hoverImage` wins; otherwise the first gallery frame that differs
 * from the primary card image.
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
