import { products } from "@/data/products";

export const PRODUCT_CHUNK = 4000;

/**
 * Products with no registeredAt used to fall back to "now", so every deploy
 * looked like thousands of new URLs. Naver then spent its daily fetch
 * re-reading the same sitemap. This date stays put.
 */
export const SITEMAP_FALLBACK_LASTMOD = "2020-01-01T00:00:00.000Z";

/**
 * Hub pages (home, shop, brand landings) do not change when one product is
 * registered. A fresh lastmod on every sync made Naver spend its small daily
 * fetch on the same landing pages.
 */
export const HUB_SITEMAP_LASTMOD = "2026-10-01T00:00:00.000Z";

/** Newest real registrations listed ahead of the full catalogue. */
export const RECENT_SITEMAP_DAYS = 14;
export const RECENT_SITEMAP_CAP = 500;

/** Number of sitemap files: id 0 = static pages, 1..N = product chunks. */
export function sitemapCount(): number {
  return Math.max(1, Math.ceil(products.length / PRODUCT_CHUNK)) + 1;
}

export function registeredAtMs(registeredAt?: string | null): number | null {
  if (!registeredAt) return null;
  const ms = Date.parse(registeredAt);
  return Number.isFinite(ms) ? ms : null;
}

export function productLastmod(registeredAt?: string | null): Date {
  return new Date(registeredAtMs(registeredAt) ?? Date.parse(SITEMAP_FALLBACK_LASTMOD));
}

/** Latest real registration, or the stable fallback when the catalogue has none. */
export function newestProductLastmod(): Date {
  let max = Date.parse(SITEMAP_FALLBACK_LASTMOD);
  for (const product of products) {
    const ms = registeredAtMs(product.registeredAt);
    if (ms != null && ms > max) max = ms;
  }
  return new Date(max);
}

/** lastmod for /sitemap/{id}.xml. Unchanged catalogues keep the same value across deploys. */
export function chunkLastmod(id: number): Date {
  if (id === 0) return new Date(HUB_SITEMAP_LASTMOD);
  const start = (id - 1) * PRODUCT_CHUNK;
  const slice = products.slice(start, start + PRODUCT_CHUNK);
  let max = Date.parse(SITEMAP_FALLBACK_LASTMOD);
  for (const product of slice) {
    const ms = registeredAtMs(product.registeredAt);
    if (ms != null && ms > max) max = ms;
  }
  return new Date(max);
}
