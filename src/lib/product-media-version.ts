import manifest from "@/data/product-images-manifest.json";

/** Short token appended to product CDN URLs after `product-images` tag updates. */
export function productMediaVersion(): string {
  const rev = (manifest as { tagRev?: string }).tagRev;
  if (rev) return rev.replace(/[^a-zA-Z0-9]/g, "").slice(0, 12);
  const publishedAt = (manifest as { publishedAt?: string }).publishedAt;
  if (!publishedAt) return "";
  return publishedAt.replace(/[:.+-]/g, "").slice(0, 15);
}
