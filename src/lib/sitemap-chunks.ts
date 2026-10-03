import { products } from "@/data/products";

export const PRODUCT_CHUNK = 4000;

/** Number of sitemap files: id 0 = static pages, 1..N = product chunks. */
export function sitemapCount(): number {
  return Math.max(1, Math.ceil(products.length / PRODUCT_CHUNK)) + 1;
}
