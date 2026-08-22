import bannerManifest from "@/data/banner-refresh-manifest.json";

/** Short token appended to banner CDN URLs so browsers refetch after weekly refresh. */
export function bannerMediaVersion(): string {
  const refreshedAt = (bannerManifest as { refreshedAt?: string }).refreshedAt;
  if (!refreshedAt) return "";
  return refreshedAt.replace(/[:.+-]/g, "").slice(0, 15);
}
