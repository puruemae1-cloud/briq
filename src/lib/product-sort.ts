import type { Product } from "@/data/products";

export type ProductSort = "new" | "orders" | "price-asc" | "price-desc";

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
  return "new";
}

/** Same ranking rules as the homepage 100 Collection. */
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
      // Newest first: later catalogue entries are newer
      return copy.reverse();
  }
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
  if (params.sort) sp.set("sort", params.sort);
  const qs = sp.toString();
  return qs ? `/shop?${qs}` : "/shop";
}
