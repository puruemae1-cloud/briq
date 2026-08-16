import type {  Product  } from "@/data/product-types";

export type ProductSort = "new" | "orders" | "price-asc" | "price-desc";

/** Default shop / homepage sort — always 최신등록순 unless the URL overrides it. */
export const DEFAULT_PRODUCT_SORT: ProductSort = "new";

export const PRODUCT_SORTS: { id: ProductSort; label: string }[] = [
  { id: "new", label: "최신등록순" },
  { id: "orders", label: "주문많은순" },
  { id: "price-asc", label: "가격낮은순" },
  { id: "price-desc", label: "가격높은순" },
];

export function parseProductSort(value?: string | null): ProductSort {
  if (
    value === "new" ||
    value === "orders" ||
    value === "price-asc" ||
    value === "price-desc"
  ) {
    return value;
  }
  return DEFAULT_PRODUCT_SORT;
}

function registeredAtMs(product: Product): number {
  const raw = product.registeredAt;
  if (!raw) return 0;
  const ms = Date.parse(raw);
  return Number.isFinite(ms) ? ms : 0;
}

/** Newest first by `registeredAt` (ISO). Missing dates sort last. */
export function compareProductsByNewest(a: Product, b: Product): number {
  const diff = registeredAtMs(b) - registeredAtMs(a);
  if (diff !== 0) return diff;
  return a.id.localeCompare(b.id);
}

/**
 * Cap for `/shop?sort=new` (신상 보러가기).
 * Weekly brand syncs stamp fresh `registeredAt` on new SKUs; this pool is
 * always the newest N. When full, older rows drop out of New Arrivals only —
 * they remain in 전체상품 and category PLPs.
 */
export const NEW_ARRIVALS_LIMIT = 100;

const GG_ACCESSORY_NAME_RE =
  /\b(belt|cap|hat|glove|gloves|umbrella|towel|visor|bag|neck warmer|wrist warmer|wristwarmers?)\b/i;

/** Unisex accessories that also sit in Men/Women collections. */
export function isGgAccessoryProduct(product: Product): boolean {
  if (product.subcategory === "gg-accessories") return true;
  if (product.ggCollections?.includes("gg-accessories")) return true;
  return GG_ACCESSORY_NAME_RE.test(`${product.name} ${product.nameKo}`);
}

/**
 * Men/Women PLPs should lead with apparel (matching Galvin Green featured feel).
 * Keeps relative order within apparel and within accessories.
 */
export function preferGgApparelFirst(list: Product[]): Product[] {
  const apparel: Product[] = [];
  const accessories: Product[] = [];
  for (const product of list) {
    if (isGgAccessoryProduct(product)) accessories.push(product);
    else apparel.push(product);
  }
  return [...apparel, ...accessories];
}

/** Same ranking rules as the homepage 100 Collection / every shop category. */
export function sortProducts(list: Product[], sort: ProductSort): Product[] {
  const copy = [...list];
  switch (sort) {
    case "price-asc":
      return copy.sort((a, b) => a.price - b.price);
    case "price-desc":
      return copy.sort((a, b) => b.price - a.price);
    case "orders":
      return copy.sort((a, b) => {
        const ba = a.badge ? 1 : 0;
        const bb = b.badge ? 1 : 0;
        if (bb !== ba) return bb - ba;
        return a.price - b.price;
      });
    case "new":
    default:
      return copy.sort(compareProductsByNewest);
  }
}

/** Catalogue-wide newest products for the New Arrivals shop surface. */
export function getNewArrivalsProducts(list: Product[]): Product[] {
  return sortProducts(list, "new").slice(0, NEW_ARRIVALS_LIMIT);
}

/**
 * Homepage lookbook rails — always newest registered first.
 * Prefers in-stock styles so OOS newest items don't occupy the rail.
 * `registeredAt` is Briq catalogue registration time (set when a SKU is first
 * imported); rebuilds must preserve it so newly added brands stay on top.
 */
export function getHomepageRailProducts(
  list: Product[],
  limit = 4,
): Product[] {
  const inStock = list.filter((p) => p.inStock !== false);
  const pool = inStock.length >= limit ? inStock : list;
  return sortProducts(pool, DEFAULT_PRODUCT_SORT).slice(0, limit);
}

/** Build a /shop href while preserving filters and updating sort. */
export function buildShopHref(params: {
  category?: string;
  sub?: string;
  q?: string;
  sort?: ProductSort;
}) {
  const sp = new URLSearchParams();
  if (params.category && params.category !== "all") {
    sp.set("category", params.category);
  }
  if (params.sub) sp.set("sub", params.sub);
  if (params.q?.trim()) sp.set("q", params.q.trim());
  // Always persist sort explicitly so shares / filters keep 최신등록순 visible.
  sp.set("sort", params.sort ?? DEFAULT_PRODUCT_SORT);
  const qs = sp.toString();
  return qs ? `/shop?${qs}` : "/shop";
}
