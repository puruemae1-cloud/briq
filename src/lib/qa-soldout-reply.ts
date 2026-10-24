import { getProduct } from "@/data/products";
import type { Product, ProductVariant } from "@/data/product-types";
import { officialSizeStock } from "@/lib/official-size-stock";
import { SEO_BRANDS } from "@/lib/site";

const BRAND_ORIGIN: Record<string, string> = {
  AllSaints: "https://www.allsaints.com",
};

const STOCK_QUESTION =
  /재고|품절|있나요|있는지|있습니까|구매|주문|입고|구할|살\s*수|재입고|sold\s*out|in\s*stock/i;

const SIZE_PATTERNS = [
  /사이즈\s*[:：]?\s*(\d{1,3}(?:\.\d)?|xxs|xs|s|m|l|xl|xxl|xxxl|os|one\s*size|원\s*사이즈|프리\s*사이즈)/gi,
  /(\d{1,3})\s*사이즈/gi,
  /\bsize\s*[:：]?\s*(\d{1,3}(?:\.\d)?|xxs|xs|s|m|l|xl|xxl|xxxl)\b/gi,
];

export function sizesAskedIn(question: string): string[] {
  const found: string[] = [];
  for (const pattern of SIZE_PATTERNS) {
    pattern.lastIndex = 0;
    for (const match of question.matchAll(pattern)) {
      const label = match[1]?.replace(/\s+/g, " ").trim();
      if (!label) continue;
      const key = label.toLowerCase().replace(/\s+/g, "");
      if (!found.some((item) => item.toLowerCase().replace(/\s+/g, "") === key)) found.push(label);
    }
  }
  return found;
}

function variantSize(variant: ProductVariant): string {
  return variant.size || variant.nameKo || variant.name || "";
}

function sameSize(asked: string, candidate: string): boolean {
  const left = asked.trim().toLowerCase().replace(/^size\s+/, "").replace(/\s+/g, "");
  const right = candidate.trim().toLowerCase().replace(/^size\s+/, "").replace(/\s+/g, "");
  return Boolean(left) && left === right;
}

function matchingVariants(product: Product, size: string): ProductVariant[] {
  return (product.variants ?? []).filter((variant) => sameSize(size, variantSize(variant)));
}

function briqSoldOut(product: Product, size: string): boolean {
  const variants = matchingVariants(product, size);
  if (variants.length) return variants.every((variant) => variant.inStock === false);
  if (product.size && sameSize(size, product.size)) return product.inStock === false;
  return false;
}

function brandEnglish(product: Product): string | null {
  const brand = product.brand?.trim();
  if (!brand) return null;
  const lowered = brand.toLowerCase();
  const known = SEO_BRANDS.find(
    (item) =>
      item.nameKo === brand ||
      item.nameEn.toLowerCase() === lowered ||
      item.keywords.some((keyword) => keyword.toLowerCase() === lowered),
  );
  return known?.nameEn || (/^[a-z0-9 '&+-]+$/i.test(brand) ? brand : null);
}

function officialPage(product: Product, brandEn: string): string | null {
  const raw =
    product.sourceUrl ||
    product.variants?.find((variant) => variant.sourceUrl)?.sourceUrl ||
    "";
  if (/^https?:\/\//i.test(raw)) return raw;
  const origin = BRAND_ORIGIN[brandEn];
  if (raw.startsWith("/") && origin) return `${origin}${raw}`;
  return null;
}

export function soldOutReplyText(sizeLabel: string, brandEn: string): string {
  return [
    "고객님 안녕하세요.",
    "문의 주셔서 감사합니다.",
    "",
    `말씀해 주신 ${sizeLabel} 사이즈는 현재 영국 공식몰에서도 품절되어, 아쉽게도 지금은 구매가 어려운 상태입니다.`,
    `저희는 영국 공식 ${brandEn} 재고와 연동되어 운영되고 있어, 추후 재입고가 되면 다시 구매 가능하도록 안내드릴 예정입니다.`,
    "",
    "다만 재입고 일정은 브랜드사에서 별도로 공유해 주지 않아, 정확한 일정 안내가 어려운 점 양해 부탁드립니다.",
    "",
    "추가로 궁금하신 점이 있으시면 대표 메일이나 상품 문의로 편하게 연락 주세요.",
    "감사합니다.",
  ].join("\n");
}

/**
 * The sold-out reply, or null when the size is available, a restock date is
 * published, or the official page cannot be checked.
 */
export async function soldOutReplyFor(productId: string, question: string): Promise<string | null> {
  const text = question.trim();
  if (!STOCK_QUESTION.test(text)) return null;
  const product = getProduct(productId);
  if (!product) return null;
  const sizes = sizesAskedIn(text);
  const asked = sizes.length ? sizes : sizesMentionedOn(product, text);
  if (!asked.length) return null;
  if (!asked.every((size) => briqSoldOut(product, size))) return null;

  const brandEn = brandEnglish(product);
  const pageUrl = brandEn ? officialPage(product, brandEn) : null;
  if (!brandEn || !pageUrl) return null;

  for (const size of asked) {
    let official;
    try {
      official = await officialSizeStock(pageUrl, size);
    } catch {
      return null;
    }
    if (official.state !== "sold-out" || official.restockDate) return null;
  }

  const label = asked
    .map((size) => matchingVariants(product, size)[0]?.size || size)
    .join(", ");
  return soldOutReplyText(label, brandEn);
}

function sizesMentionedOn(product: Product, question: string): string[] {
  const found: string[] = [];
  for (const variant of product.variants ?? []) {
    const label = variantSize(variant).trim();
    if (label.length < 2) continue;
    if (found.some((item) => sameSize(item, label))) continue;
    const escaped = label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const pattern = new RegExp(`(?:^|[^0-9A-Za-z])${escaped}(?:$|[^0-9A-Za-z])`, "i");
    if (pattern.test(question)) found.push(label);
  }
  return found;
}
