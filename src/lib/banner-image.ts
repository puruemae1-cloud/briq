/**
 * Homepage / shop banner paths.
 * Mobile uses `/banners/m/`, tablet `/banners/t/` when available.
 */

export function toMobileBannerSrc(src: string): string {
  if (!src.startsWith("/banners/")) return src;
  if (src.startsWith("/banners/m/") || src.startsWith("/banners/t/")) return src;
  const name = src.slice("/banners/".length);
  if (name.includes("/")) return src;
  return `/banners/m/${name}`;
}

export function toTabletBannerSrc(src: string): string {
  if (!src.startsWith("/banners/")) return src;
  if (src.startsWith("/banners/m/") || src.startsWith("/banners/t/")) return src;
  const name = src.slice("/banners/".length);
  if (name.includes("/")) return src;
  return `/banners/t/${name}`;
}

/** Prefer WebP sibling when the catalog path is a JPEG banner. */
export function toWebpBannerSrc(src: string): string {
  if (!src.startsWith("/banners/") || !src.endsWith(".jpg")) return src;
  return `${src.slice(0, -4)}.webp`;
}
