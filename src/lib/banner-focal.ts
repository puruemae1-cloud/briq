import bannerFocals from "@/data/banner-refresh-manifest.json";

type ManifestSlot = {
  focal?: string;
};

type Manifest = {
  slots?: Record<string, ManifestSlot>;
};

/** Locked creatives with a preferred object-position (head/product framing). */
const FOCAL_OVERRIDES: Record<string, string> = {
  "brand-burberry-scarf.jpg": "center 28%",
  "brand-burberry-scarf.webp": "center 28%",
  /* CC logo sits ~36% x / 42% y after crop — keep it in the shop-hero strip */
  "brand-chanel-como-bag.jpg": "36% 42%",
  "brand-chanel-como-bag.webp": "36% 42%",
  /* Linea Rossa model — keep crown + red temple mark in frame */
  "brand-prada-linea-rossa.jpg": "48% 18%",
  "brand-prada-linea-rossa.webp": "48% 18%",
  /* Who We Are ridge — keep climbers on the diagonal */
  "brand-arcteryx-ridge.jpg": "38% 55%",
  "brand-arcteryx-ridge.webp": "38% 55%",
  /* All Bags forest bench — keep models + Promenade bag centred */
  "brand-dior-bags.jpg": "50% 58%",
  "brand-dior-bags.webp": "50% 58%",
  /* Men's RTW boat campaign — model + jacket on the right */
  "brand-dior-mens-rtw.jpg": "68% 46%",
  "brand-dior-mens-rtw.webp": "68% 46%",
  /* Women's RTW grass campaign — three models centred in the strip */
  "brand-dior-womens-rtw.jpg": "50% 52%",
  "brand-dior-womens-rtw.webp": "50% 52%",
  /* Accessories jewelry — Rose des Vents necklace + face */
  "brand-dior-accessories.jpg": "66% 34%",
  "brand-dior-accessories.webp": "66% 34%",
};

/**
 * CSS object-position computed during weekly banner refresh so faces/products
 * stay framed under object-fit: cover on PC / tablet / mobile.
 */
export function bannerFocalForSrc(src: string, fallback?: string): string | undefined {
  const name = src.split("/").pop() || "";
  if (FOCAL_OVERRIDES[name]) return FOCAL_OVERRIDES[name];
  const slots = (bannerFocals as Manifest).slots || {};
  return slots[name]?.focal || fallback;
}
