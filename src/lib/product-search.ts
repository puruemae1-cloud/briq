import type { Product } from "@/data/products";
import { categoryLabel, subcategoryLabel } from "@/data/categories";

/** Common KR/EN aliases so casual keywords still hit products. */
const SEARCH_ALIASES: Record<string, string[]> = {
  폴로: ["polo", "ralph", "lauren"],
  랄프: ["polo", "ralph", "lauren"],
  랄프로렌: ["polo", "ralph", "lauren"],
  ralph: ["polo", "lauren"],
  polo: ["ralph", "lauren"],
  브릭: ["briq"],
  briq: ["브릭"],
  시계: ["watch", "watches", "horology"],
  watch: ["시계", "watches"],
  가방: ["bag", "bags", "tote", "crossbody", "handbag", "구찌", "gucci"],
  bag: ["가방", "bags", "핸드백"],
  구찌: ["gucci", "gc"],
  gucci: ["구찌"],
  슈즈: ["shoes", "shoe", "loafer", "runner"],
  신발: ["shoes", "shoe", "슈즈"],
  shoes: ["슈즈", "신발"],
  캡: ["cap", "hat"],
  cap: ["캡", "모자"],
  모자: ["cap", "hat"],
  골프: ["golf"],
  golf: ["골프"],
  러닝: ["running", "run"],
  running: ["러닝"],
  수영: ["swim", "swimming"],
  swimming: ["수영", "swim"],
  자전거: ["cycling", "cycle", "bike"],
  cycling: ["자전거"],
  테니스: ["tennis"],
  tennis: ["테니스"],
  코트: ["coat"],
  coat: ["코트"],
  니트: ["knit"],
  스카프: ["scarf"],
  지갑: ["wallet", "pouch"],
  wallet: ["지갑"],
  쥬얼리: ["jewelry", "jewellery"],
  jewelry: ["쥬얼리"],
  화장품: ["cosmetics", "beauty"],
  티: ["tea"],
  tea: ["티", "tea"],
};

function normalize(value: string) {
  return value
    .normalize("NFKC")
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s/+.-]+/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function tokenize(query: string): string[] {
  return normalize(query).split(" ").filter(Boolean);
}

function expandToken(token: string): string[] {
  const aliases = SEARCH_ALIASES[token] ?? [];
  return [token, ...aliases.map(normalize)];
}

function productSearchText(product: Product): string {
  const category = categoryLabel(product.category);
  const subcategory = product.subcategory
    ? subcategoryLabel(product.category, product.subcategory)
    : "";
  const variantBits =
    product.variants?.flatMap((v) => [v.name, v.nameKo, v.sku ?? ""]) ?? [];

  return normalize(
    [
      product.id,
      product.name,
      product.nameKo,
      product.brand,
      product.descriptionKo ?? "",
      product.sku ?? "",
      product.badge ?? "",
      product.size ?? "",
      category,
      subcategory,
      product.category,
      product.subcategory ?? "",
      ...product.tags,
      ...variantBits,
    ].join(" "),
  );
}

/** True if every query token (or one of its aliases) appears in haystack. */
function matchesQuery(haystack: string, query: string): boolean {
  const tokens = tokenize(query);
  if (!tokens.length) return true;

  return tokens.every((token) =>
    expandToken(token).some((term) => haystack.includes(term)),
  );
}

/**
 * Keyword search across product name (EN/KO), brand, tags, category,
 * description, SKU, and variant labels. Multi-word queries require all tokens.
 */
export function searchProducts(products: Product[], query?: string | null): Product[] {
  const q = query?.trim();
  if (!q) return products;

  return products.filter((product) =>
    matchesQuery(productSearchText(product), q),
  );
}

export function buildShopSearchHref(query: string) {
  const q = query.trim();
  if (!q) return "/shop";
  return `/shop?q=${encodeURIComponent(q)}`;
}
