import type { Product, ProductVariant } from "@/data/product-types";

/** Max gallery frames serialized into PLP/card HTML (RSC flight). */
export const CARD_GALLERY_LIMIT = 2;

/**
 * Max variants kept on a card. Size runs (UK 2–12 etc.) used to ship 50+
 * full variants into every Yeti HTML download — that blew Naver "다운로드 크기".
 * One row per colour is enough for swatches + price range.
 */
export const CARD_VARIANT_LIMIT = 6;

/** Marker so live /api checks can confirm the slim DTO is deployed (v3). */
export const CARD_DTO_VERSION = 3;

type CardVariant = Pick<
  ProductVariant,
  "id" | "price" | "inStock" | "image"
> &
  Partial<Pick<ProductVariant, "compareAtPrice" | "colorKey" | "hoverImage">>;

function toCardVariant(v: ProductVariant): CardVariant {
  const out: CardVariant = {
    id: v.id,
    price: v.price,
    inStock: v.inStock,
    image: v.image,
  };
  if (v.compareAtPrice) out.compareAtPrice = v.compareAtPrice;
  if (v.colorKey) out.colorKey = v.colorKey;
  if (v.hoverImage) out.hoverImage = v.hoverImage;
  return out;
}

/** Prefer one variant per colour; fall back to id when colour is absent. */
function slimVariantsForCard(
  variants: ProductVariant[] | undefined,
): CardVariant[] | undefined {
  if (!variants?.length) return undefined;

  const byColour = new Map<string, ProductVariant>();
  for (const v of variants) {
    const key = v.colorKey?.trim() || v.id;
    if (!byColour.has(key)) byColour.set(key, v);
  }

  let picked = [...byColour.values()];
  if (picked.length > CARD_VARIANT_LIMIT) {
    // Keep cheapest + dearest so ProductCard `price~` still works, then fill.
    const byPrice = [...picked].sort((a, b) => a.price - b.price);
    const must = new Set<ProductVariant>([byPrice[0], byPrice[byPrice.length - 1]]);
    const rest = picked.filter((v) => !must.has(v));
    picked = [...must, ...rest].slice(0, CARD_VARIANT_LIMIT);
  }

  return picked.map(toCardVariant);
}

/**
 * Slim product for PLP/cards — omit PDP-only fields and cap variants.
 * Serialized into every shop/home HTML response Yeti downloads, so keep tiny.
 *
 * Intentionally drops: description*, tags, accent, sku, gbpPrice, sourceUrl,
 * story, tech specs, size charts, and per-size variant rows.
 */
export function toCardProduct(p: Product): Product {
  const images = p.images?.slice(0, CARD_GALLERY_LIMIT);
  const variants = slimVariantsForCard(p.variants);

  const out: Product = {
    id: p.id,
    name: p.name,
    nameKo: p.nameKo,
    brand: p.brand,
    price: p.price,
    category: p.category,
    subcategory: p.subcategory,
    image: p.image,
    inStock: p.inStock,
  };

  if (p.compareAtPrice) out.compareAtPrice = p.compareAtPrice;
  if (images?.length) out.images = images;
  if (p.hoverImage) out.hoverImage = p.hoverImage;
  if (p.badge) out.badge = p.badge;
  if (p.registeredAt) out.registeredAt = p.registeredAt;
  if (p.newBadgeAt) out.newBadgeAt = p.newBadgeAt;
  if (p.shopColorKey) out.shopColorKey = p.shopColorKey;
  if (p.cwCollections?.length) out.cwCollections = p.cwCollections;
  if (p.ggCollections?.length) out.ggCollections = p.ggCollections;
  if (variants?.length) out.variants = variants as ProductVariant[];

  return out;
}
