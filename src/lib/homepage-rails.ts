/**
 * Homepage lookbook rails — newest first, but each brand may appear on
 * at most one category rail (시그니처 / 시계 / 가방 / 슈즈 / 악세서리 / 스포츠).
 *
 * Earlier rails in `homeLookBanners` claim brands first (luxury → … → sports).
 */
import type { Product } from "@/data/product-types";
import { isProductInStock } from "@/data/product-utils";
import { sortProducts } from "@/lib/product-sort";

export type HomepageRailSpec = {
  /** Banner / category id (luxury, bags, …). */
  railId: string;
  products: Product[];
};

/** Brands never shown on a given homepage lookbook rail (shop categories unchanged). */
const RAIL_BLOCKED_BRANDS: Record<string, ReadonlySet<string>> = {
  luxury: new Set(["arcteryx", "belstaff"]),
};

const ID_PREFIX_BRAND: Array<{ prefix: string; brand: string }> = [
  { prefix: "axa-", brand: "arcteryx" },
  { prefix: "axg-", brand: "arcteryx" },
  { prefix: "axo-", brand: "arcteryx" },
  { prefix: "ax-", brand: "arcteryx" },
  { prefix: "ce-", brand: "celine" },
  { prefix: "ch-", brand: "chanel" },
  { prefix: "gc-", brand: "gucci" },
  { prefix: "gg-", brand: "galvin-green" },
  { prefix: "di-", brand: "dior" },
  { prefix: "pr-", brand: "prada" },
  { prefix: "lv-", brand: "louis-vuitton" },
  { prefix: "mb-", brand: "mulberry" },
  { prefix: "vw-", brand: "vivienne-westwood" },
  { prefix: "bb-", brand: "burberry" },
  { prefix: "bs-", brand: "belstaff" },
  { prefix: "ps-", brand: "paul-smith" },
  { prefix: "cw-", brand: "christopher-ward" },
  { prefix: "lu-", brand: "london-undercover" },
];

const BRAND_ALIASES: Array<{ re: RegExp; brand: string }> = [
  { re: /arc'?teryx|아크테릭스/i, brand: "arcteryx" },
  { re: /celine|셀린/i, brand: "celine" },
  { re: /chanel|샤넬/i, brand: "chanel" },
  { re: /gucci|구찌/i, brand: "gucci" },
  { re: /galvin\s*green|갈빈/i, brand: "galvin-green" },
  { re: /dior|디올/i, brand: "dior" },
  { re: /prada|프라다/i, brand: "prada" },
  { re: /louis\s*vuitton|루이\s*비통|\blv\b/i, brand: "louis-vuitton" },
  { re: /mulberry|멀버리/i, brand: "mulberry" },
  { re: /vivienne|웨스트우드|westwood/i, brand: "vivienne-westwood" },
  { re: /burberry|버버리/i, brand: "burberry" },
  { re: /belstaff|벨스타프/i, brand: "belstaff" },
  { re: /paul\s*smith|폴\s*스미스/i, brand: "paul-smith" },
  { re: /christopher\s*ward|크리스토퍼/i, brand: "christopher-ward" },
  { re: /london\s*undercover|런던언더커버/i, brand: "london-undercover" },
];

/** Stable brand key for homepage cross-rail exclusivity. */
export function homepageBrandKey(product: Product): string {
  const id = (product.id || "").toLowerCase();
  for (const { prefix, brand } of ID_PREFIX_BRAND) {
    if (id.startsWith(prefix)) return brand;
  }

  const blob = [product.brand, product.subcategory, ...(product.tags || [])]
    .filter(Boolean)
    .join(" ");
  for (const { re, brand } of BRAND_ALIASES) {
    if (re.test(blob)) return brand;
  }

  const brand = (product.brand || "").trim().toLowerCase();
  if (brand) return brand.replace(/\s+/g, "-");
  return id || "unknown";
}

/**
 * Pick up to `limit` newest in-stock products, skipping brands in `excludeBrands`.
 * Does not soft-fill with excluded brands — empty slots stay empty so another
 * brand can surface rather than repeating a brand already on an earlier rail.
 */
export function getHomepageRailProductsExclusive(
  list: Product[],
  limit = 4,
  excludeBrands: ReadonlySet<string> = new Set(),
): Product[] {
  const inStock = list.filter((p) => isProductInStock(p));
  const pool = sortProducts(inStock.length >= limit ? inStock : list, "new");
  const out: Product[] = [];
  for (const product of pool) {
    const key = homepageBrandKey(product);
    if (excludeBrands.has(key)) continue;
    out.push(product);
    if (out.length >= limit) break;
  }
  return out;
}

/**
 * Assign products to every category rail in order. Brands claimed by an
 * earlier rail are excluded from later rails.
 */
export function assignHomepageCategoryRails(
  rails: HomepageRailSpec[],
  limit = 4,
): Record<string, Product[]> {
  const used = new Set<string>();
  const result: Record<string, Product[]> = {};

  for (const rail of rails) {
    const exclude = new Set(used);
    const blocked = RAIL_BLOCKED_BRANDS[rail.railId];
    if (blocked) {
      for (const brand of blocked) exclude.add(brand);
    }
    const picked = getHomepageRailProductsExclusive(
      rail.products,
      limit,
      exclude,
    );
    result[rail.railId] = picked;
    for (const product of picked) {
      used.add(homepageBrandKey(product));
    }
  }

  return result;
}
