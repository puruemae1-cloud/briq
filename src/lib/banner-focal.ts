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
  /* Bags PLP night check tote — face + tote */
  "brand-burberry-bags.jpg": "52% 38%",
  "brand-burberry-bags.webp": "52% 38%",
  /* Mulberry bags PLP — Bayswater satchel on fountain rim */
  "brand-mulberry-bags.jpg": "50% 48%",
  "brand-mulberry-bags.webp": "50% 48%",
  /* Mulberry accessories PLP — Lily snakeskin red / face + bag */
  "brand-mulberry-accessories.jpg": "50% 38%",
  "brand-mulberry-accessories.webp": "50% 38%",
  /* Shoes PLP — Vintage Check platform sneakers */
  "brand-burberry-shoes.jpg": "50% 72%",
  "brand-burberry-shoes.webp": "50% 72%",
  /* CC logo sits ~36% x / 42% y after crop — keep it in the shop-hero strip */
  "brand-chanel-como-bag.jpg": "36% 42%",
  "brand-chanel-como-bag.webp": "36% 42%",
  /* Shoes barefoot sandals — CC heel + feet */
  "brand-chanel-shoes.jpg": "42% 55%",
  "brand-chanel-shoes.webp": "42% 55%",
  /* Linea Rossa model — keep crown + red temple mark in frame */
  "brand-prada-linea-rossa.jpg": "48% 18%",
  "brand-prada-linea-rossa.webp": "48% 18%",
  /* Women's bags PLP — crocodile bag + PRADA MILANO logo */
  "brand-prada-bags.jpg": "70% 50%",
  "brand-prada-bags.webp": "70% 50%",
  /* Women's shoes — green slingbacks / floral socks */
  "brand-prada-shoes.jpg": "52% 72%",
  "brand-prada-shoes.webp": "52% 72%",
  /* Who We Are ridge — keep climbers on the diagonal */
  "brand-arcteryx-ridge.jpg": "38% 55%",
  "brand-arcteryx-ridge.webp": "38% 55%",
  /* Primavera handbags — model face + GG Marmont bag */
  "brand-gucci-handbags.jpg": "52% 42%",
  "brand-gucci-handbags.webp": "52% 42%",
  /* Women's shoes PLP — GG Supreme slingbacks on carpet */
  "brand-gucci-shoes.jpg": "38% 58%",
  "brand-gucci-shoes.webp": "38% 58%",
  /* All Bags forest bench — keep models + Promenade bag centred */
  "brand-dior-bags.jpg": "50% 58%",
  "brand-dior-bags.webp": "50% 58%",
  /* Men's RTW boat campaign — model + jacket on the right */
  "brand-dior-mens-rtw.jpg": "68% 46%",
  "brand-dior-mens-rtw.webp": "68% 46%",
  /* Women's shoes — keep Dior boots / footwear at bottom edge */
  "brand-dior-shoes.jpg": "50% 88%",
  "brand-dior-shoes.webp": "50% 88%",
  /* Women's RTW grass campaign — three models centred in the strip */
  "brand-dior-womens-rtw.jpg": "50% 52%",
  "brand-dior-womens-rtw.webp": "50% 52%",
  /* New Arrivals — Dior FW26 grass / pink Lady Dior (face + bag) */
  "shop-new-arrivals.jpg": "48% 40%",
  "shop-new-arrivals.webp": "48% 40%",
  /* Accessories jewelry — Rose des Vents necklace + face */
  "brand-dior-accessories.jpg": "66% 34%",
  "brand-dior-accessories.webp": "66% 34%",
  /* Celine Hiver 2026 accessories creative — centered face / glasses */
  "brand-celine-accessories.jpg": "50% 43%",
  "brand-celine-accessories.webp": "50% 43%",
  /* Celine Hiver 2026 RTW creative — keep face / shoulders centered */
  "brand-celine-signature.jpg": "50% 36%",
  "brand-celine-signature.webp": "50% 36%",
  /* Celine handbags creative — keep Triomphe hardware centred */
  "brand-celine-bags.jpg": "50.5% 54%",
  "brand-celine-bags.webp": "50.5% 54%",
  /* Celine Winter 2026 shoes creative — keep both shoes framed */
  "brand-celine-shoes.jpg": "50% 53%",
  "brand-celine-shoes.webp": "50% 53%",
  /* Vivienne Westwood x George Cox creative — keep both shoes centered */
  "brand-vivienne-westwood-shoes.jpg": "50% 47%",
  "brand-vivienne-westwood-shoes.webp": "50% 47%",
  /* Vivienne Westwood homepage AW2728 bags — mobile/tablet keep lower stud detail;
     PC framing is overridden in globals.css (.shop-hero--vw-bags). */
  "brand-vivienne-westwood-bags.jpg": "50% 56%",
  "brand-vivienne-westwood-bags.webp": "50% 56%",
  /* Vivienne Westwood Spring Cherubs — keep face and upper torso in frame */
  "brand-vivienne-westwood-womens-rtw.jpg": "50% 23%",
  "brand-vivienne-westwood-womens-rtw.webp": "50% 23%",
  /* Vivienne Westwood mens RTW — keep face and jacket torso in frame */
  "brand-vivienne-westwood-mens-rtw.jpg": "50% 24%",
  "brand-vivienne-westwood-mens-rtw.webp": "50% 24%",
  /* Vivienne Westwood Tavistock watch — keep the watch centered in frame */
  "brand-vivienne-westwood-watches.jpg": "43% 50%",
  "brand-vivienne-westwood-watches.webp": "43% 50%",
  /* Vivienne Westwood homepage accessories — keep the lower jewelry detail visible */
  "brand-vivienne-westwood-accessories.jpg": "52% 60%",
  "brand-vivienne-westwood-accessories.webp": "52% 60%",
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
