/**
 * Homepage / shop banner paths.
 * Mobile uses compressed copies under `/banners/m/` when available.
 */

export function toMobileBannerSrc(src: string): string {
  if (!src.startsWith("/banners/")) return src;
  if (src.startsWith("/banners/m/")) return src;
  const name = src.slice("/banners/".length);
  if (name.includes("/")) return src;
  return `/banners/m/${name}`;
}
