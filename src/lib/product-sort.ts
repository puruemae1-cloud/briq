import type { Product } from "@/data/product-types";
import { isProductInStock } from "@/data/product-utils";
import { isHomepageSwimwearProduct } from "@/lib/homepage-product-filters";

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

function updatedAtMs(product: Product): number {
  const raw = product.updatedAt || product.registeredAt;
  if (!raw) return 0;
  const ms = Date.parse(raw);
  return Number.isFinite(ms) ? ms : 0;
}

/** In-stock first (0), sold-out last (1) — applied to every PLP / collection sort. */
export function stockSortRank(product: Product): number {
  return isProductInStock(product) ? 0 : 1;
}

/** Newest first by `updatedAt ?? registeredAt` (ISO). Missing dates sort last. */
export function compareProductsByNewest(a: Product, b: Product): number {
  const diff = updatedAtMs(b) - updatedAtMs(a);
  if (diff !== 0) return diff;
  const registeredDiff = registeredAtMs(b) - registeredAtMs(a);
  if (registeredDiff !== 0) return registeredDiff;
  return a.id.localeCompare(b.id);
}

function withSoldOutLast(
  cmp: (a: Product, b: Product) => number,
): (a: Product, b: Product) => number {
  return (a, b) => {
    const stock = stockSortRank(a) - stockSortRank(b);
    if (stock !== 0) return stock;
    return cmp(a, b);
  };
}

/**
 * Cap for `/shop?sort=new` (신상 보러가기).
 * Weekly brand syncs stamp fresh `registeredAt` on new SKUs; this pool is
 * always the newest N. When full, older rows drop out of New Arrivals only —
 * they remain in 전체상품 and category PLPs.
 */
export const NEW_ARRIVALS_LIMIT = 100;

/** Soft cap per brand inside New Arrivals so one weekly sync cannot dominate. */
export const NEW_ARRIVALS_MAX_PER_BRAND = 8;

/**
 * Interleave newest products across brands (round-robin on newest-first
 * brand queues). Keeps chronological preference while mixing houses.
 *
 * Does **not** back-fill with the same dominant brand — that undoes mixing
 * when one weekly import stamps hundreds of fresh `registeredAt` values.
 */
export function diversifyByBrandNewestFirst(
  newestFirst: Product[],
  limit: number,
  maxPerBrand: number = NEW_ARRIVALS_MAX_PER_BRAND,
  brandKey: (p: Product) => string = (p) =>
    (p.brand || p.subcategory || p.id || "unknown").toLowerCase(),
): Product[] {
  if (limit <= 0 || newestFirst.length === 0) return [];
  const queues = new Map<string, Product[]>();
  const brandOrder: string[] = [];
  for (const product of newestFirst) {
    const key = brandKey(product) || "unknown";
    let q = queues.get(key);
    if (!q) {
      q = [];
      queues.set(key, q);
      brandOrder.push(key);
    }
    if (q.length < maxPerBrand) q.push(product);
  }
  const out: Product[] = [];
  const taken = new Set<string>();
  let progress = true;
  while (out.length < limit && progress) {
    progress = false;
    for (const key of brandOrder) {
      if (out.length >= limit) break;
      const q = queues.get(key);
      if (!q || q.length === 0) continue;
      const next = q.shift()!;
      if (taken.has(next.id)) continue;
      taken.add(next.id);
      out.push(next);
      progress = true;
    }
  }
  return out;
}

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

/** CW watch straps — weekly sync refreshes `registeredAt`, which would otherwise float them first. */
export function isCwStrapProduct(product: Product): boolean {
  if (product.subcategory === "cw-straps") return true;
  if (product.id.startsWith("cw-strap-")) return true;
  return Boolean(product.cwCollections?.some((c) => c === "cw-straps"));
}

/**
 * Christopher Ward brand PLP: watches first, straps always last.
 * Preserves relative order within each group after the active sort.
 */
export function preferCwWatchesFirst(list: Product[]): Product[] {
  const watches: Product[] = [];
  const straps: Product[] = [];
  for (const product of list) {
    if (isCwStrapProduct(product)) straps.push(product);
    else watches.push(product);
  }
  if (straps.length === 0) return list;
  return [...watches, ...straps];
}

function compareBySort(sort: ProductSort): (a: Product, b: Product) => number {
  switch (sort) {
    case "price-asc":
      return withSoldOutLast((a, b) => a.price - b.price);
    case "price-desc":
      return withSoldOutLast((a, b) => b.price - a.price);
    case "orders":
      return withSoldOutLast((a, b) => {
        const ba = a.badge ? 1 : 0;
        const bb = b.badge ? 1 : 0;
        if (bb !== ba) return bb - ba;
        return a.price - b.price;
      });
    case "new":
    default:
      return withSoldOutLast(compareProductsByNewest);
  }
}

/**
 * Single-pass top-N for catalogue-wide shop surfaces.
 * Avoids `[...list].sort(...)` on the full multi-brand catalogue (Vercel OOM).
 */
export function getTopSortedProducts(
  list: Product[],
  sort: ProductSort,
  limit: number = NEW_ARRIVALS_LIMIT,
): Product[] {
  const cmp = compareBySort(sort);
  const top: Product[] = [];
  const cap = Math.max(1, limit);
  for (const product of list) {
    if (top.length < cap) {
      top.push(product);
      if (top.length === cap) top.sort(cmp);
      continue;
    }
    const last = top[cap - 1];
    if (cmp(product, last) < 0) {
      top[cap - 1] = product;
      top.sort(cmp);
    }
  }
  if (top.length < cap) top.sort(cmp);
  return top;
}

/**
 * Catalogue-wide New Arrivals: take each brand's newest
 * {@link NEW_ARRIVALS_MAX_PER_BRAND} by `registeredAt`, then round-robin.
 * One import (e.g. 2500 Bottega rows on the same day) cannot fill the rail.
 */
export function getNewArrivalsProducts(list: Product[]): Product[] {
  const cmp = withSoldOutLast((a, b) => {
    const byRegistered = registeredAtMs(b) - registeredAtMs(a);
    if (byRegistered !== 0) return byRegistered;
    return compareProductsByNewest(a, b);
  });
  const brandKey = (p: Product) =>
    (p.brand || p.subcategory || p.id || "unknown").toLowerCase();

  const perBrand = new Map<string, Product[]>();
  for (const product of list) {
    const key = brandKey(product);
    let q = perBrand.get(key);
    if (!q) {
      q = [];
      perBrand.set(key, q);
    }
    if (q.length < NEW_ARRIVALS_MAX_PER_BRAND) {
      q.push(product);
      if (q.length === NEW_ARRIVALS_MAX_PER_BRAND) q.sort(cmp);
      continue;
    }
    if (cmp(product, q[q.length - 1]) < 0) {
      q[q.length - 1] = product;
      q.sort(cmp);
    }
  }

  const brandOrder = [...perBrand.entries()]
    .sort((a, b) => cmp(a[1][0]!, b[1][0]!))
    .map(([key]) => key);

  const queues = new Map(
    [...perBrand.entries()].map(([key, rows]) => [key, rows.slice()]),
  );
  const out: Product[] = [];
  let progress = true;
  while (out.length < NEW_ARRIVALS_LIMIT && progress) {
    progress = false;
    for (const key of brandOrder) {
      if (out.length >= NEW_ARRIVALS_LIMIT) break;
      const q = queues.get(key);
      if (!q || q.length === 0) continue;
      out.push(q.shift()!);
      progress = true;
    }
  }
  return out;
}

/**
 * Full sort for brand/category PLPs. For huge lists prefer
 * {@link getTopSortedProducts} when only a capped window is needed.
 */
export function sortProducts(list: Product[], sort: ProductSort): Product[] {
  // Copy before sort so we never mutate the shared `products` catalogue.
  const copy = list.slice();
  return copy.sort(compareBySort(sort));
}

/**
 * Homepage lookbook rails — newest catalogue update first.
 * Prefers in-stock styles so OOS newest items don't occupy the rail.
 *
 * Prefer ``assignHomepageCategoryRails`` / ``getHomepageRailProductsExclusive``
 * on the homepage so the same brand cannot occupy multiple category rails.
 */
export function getHomepageRailProducts(
  list: Product[],
  limit = 4,
): Product[] {
  const eligible = list.filter((p) => !isHomepageSwimwearProduct(p));
  const inStock = eligible.filter((p) => isProductInStock(p));
  const pool = inStock.length >= limit ? inStock : eligible;
  return sortProducts(pool, "new").slice(0, limit);
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
