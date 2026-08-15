import bannerFocals from "@/data/banner-refresh-manifest.json";

type ManifestSlot = {
  focal?: string;
};

type Manifest = {
  slots?: Record<string, ManifestSlot>;
};

/**
 * CSS object-position computed during weekly banner refresh so faces/products
 * stay framed under object-fit: cover on PC / tablet / mobile.
 */
export function bannerFocalForSrc(src: string, fallback?: string): string | undefined {
  const name = src.split("/").pop() || "";
  const slots = (bannerFocals as Manifest).slots || {};
  return slots[name]?.focal || fallback;
}
