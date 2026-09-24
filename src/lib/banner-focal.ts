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
  /* Burberry night check tote — keep bag body + knight medallion (lower mid) */
  "brand-burberry-bags.jpg": "50% 70%",
  "brand-burberry-bags.webp": "50% 70%",
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
  "brand-chanel.jpg": "62% 22%",
  "brand-chanel.webp": "62% 22%",
  /* J12 new-watches PLP — watch fills height; subject sits left-centre */
  "brand-chanel-premiere.jpg": "27% 50%",
  "brand-chanel-premiere.webp": "27% 50%",
  "brand-chanel-como-bag.jpg": "36% 42%",
  "brand-chanel-como-bag.webp": "36% 42%",
  /* Shoes barefoot sandals — CC heel + feet (mobile/tablet). PC overrides to 42% 88% in globals.css */
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
  /* Arc'teryx shoes — trail runners on rock; mid-lower footwear */
  "brand-arcteryx-shoes.jpg": "48% 70%",
  "brand-arcteryx-shoes.webp": "48% 70%",
  /* Belstaff shoes — Munro Boot lifestyle; full boots lower crop */
  "brand-belstaff-shoes.jpg": "42% 72%",
  "brand-belstaff-shoes.webp": "42% 72%",
  /* Primavera handbags — model face + GG Marmont bag */
  "brand-gucci.jpg": "48% 20%",
  "brand-gucci.webp": "48% 20%",
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
  /* Celine accessories — Francoise temple still; keep CELINE gold wordmark */
  "brand-celine-accessories.jpg": "39% 58%",
  "brand-celine-accessories.webp": "39% 58%",
  /* AllSaints clothing — AW26 campaign denim; top-anchored face */
  "brand-all-saints.jpg": "52% 18%",
  "brand-all-saints.webp": "52% 18%",
  /* AllSaints shoes — Lila W129FF-5 side packshot; centered full shoe */
  "brand-all-saints-shoes.jpg": "50% 50%",
  "brand-all-saints-shoes.webp": "50% 50%",
  /* AllSaints bags — black field + white ALLSAINTS wordmark */
  "brand-all-saints-bags.jpg": "50% 50%",
  "brand-all-saints-bags.webp": "50% 50%",
  /* AllSaints accessories — Emrys Aviator M203XF-5 3/4 still; mid-lower + temple wordmark */
  "brand-all-saints-accessories.jpg": "43% 64%",
  "brand-all-saints-accessories.webp": "43% 64%",
  /* Celine signature RTW — Hiver 2026 lying model; keep face on the right */
  "brand-celine-signature.jpg": "73% 28%",
  "brand-celine-signature.webp": "73% 28%",
  /* Saint Laurent RTW — Winter 26 lookbook #44; top-anchored faces + jewelry */
  "brand-saint-laurent.jpg": "48% 18%",
  "brand-saint-laurent.webp": "48% 18%",
  /* Saint Laurent bags — Icare quilted hobo; mid-lower Cassandre logo */
  "brand-saint-laurent-bags.jpg": "42% 66%",
  "brand-saint-laurent-bags.webp": "42% 66%",
  /* Saint Laurent shoes — red croc peep-toe; bottom shoe + ankle straps */
  "brand-saint-laurent-shoes.jpg": "42% 72%",
  "brand-saint-laurent-shoes.webp": "42% 72%",
  /* Paul Smith AW26 campaign — headphones still; keep face + orange cans upper */
  "brand-paul-smith-1.jpg": "50% 18%",
  "brand-paul-smith-1.webp": "50% 18%",
  /* Paul Smith AW26 campaign — tailoring still; face sits right-upper */
  "brand-paul-smith-2.jpg": "62% 18%",
  "brand-paul-smith-2.webp": "62% 18%",
  /* Paul Smith shoes — Cream Chilly trainers; red tongue logo lower-left */
  "brand-paul-smith-shoes.jpg": "40% 72%",
  "brand-paul-smith-shoes.webp": "40% 72%",
  /* Celine handbags — Small Flair open-bag still; mid-upper Triomphe / CELINE PARIS */
  "brand-celine-bags.jpg": "50% 32%",
  "brand-celine-bags.webp": "50% 32%",
  /* Celine shoes — Runner calfskin/suede/mesh top-down pair */
  "brand-celine-shoes.jpg": "50% 48%",
  "brand-celine-shoes.webp": "50% 48%",
  /* Vivienne Westwood x George Cox — bias lower so embossed Vivienne strap stays in PC strip */
  "brand-vivienne-westwood-shoes.jpg": "50% 66%",
  "brand-vivienne-westwood-shoes.webp": "50% 66%",
  /* Vivienne Westwood Tasha pastel pink — mid-frame Orb logo */
  "brand-vivienne-westwood-bags.jpg": "42% 55%",
  "brand-vivienne-westwood-bags.webp": "42% 55%",
  /* Galvin Green DryVR Two hero — poster still behind autoplay video */
  "brand-galvin-green.jpg": "50% 45%",
  "brand-galvin-green.webp": "50% 45%",
  "brand-galvin-green-1.jpg": "50% 45%",
  "brand-galvin-green-1.webp": "50% 45%",
  "brand-galvin-green-2.jpg": "50% 45%",
  "brand-galvin-green-2.webp": "50% 45%",
  "brand-galvin-green-3.jpg": "50% 45%",
  "brand-galvin-green-3.webp": "50% 45%",
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
