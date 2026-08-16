export type CategoryId =
  | "luxury"
  | "watches"
  | "clothing"
  | "bags"
  | "shoes"
  | "accessories"
  | "sports";

export type ProductVariant = {
  id: string;
  name: string;
  nameKo: string;
  sku: string;
  gbpPrice: number;
  price: number;
  /** Local require() asset or remote URI string */
  image: number | string;
  images?: Array<number | string>;
  inStock: boolean;
};

export type Product = {
  id: string;
  name: string;
  nameKo: string;
  brand: string;
  price: number;
  category: CategoryId;
  descriptionKo?: string;
  accent: string;
  badge?: string;
  image?: number | string;
  images?: Array<number | string>;
  variants?: ProductVariant[];
  featuresKo?: string[];
  techSpecs?: Array<{ labelKo: string; valueKo: string }>;
};

/** KRW = round_만원(GBP × 2100 × 1.05 + 200,000) */
export function gbpToBriqKrw(gbp: number) {
  return Math.round((gbp * 2100 * 1.05 + 200_000) / 10_000) * 10_000;
}

export const categories: { id: CategoryId | "all"; labelKo: string }[] = [
  { id: "all", labelKo: "전체" },
  { id: "luxury", labelKo: "시그니처 의류 컬렉션" },
  { id: "watches", labelKo: "시계" },
  { id: "clothing", labelKo: "패션의류" },
  { id: "bags", labelKo: "가방" },
  { id: "shoes", labelKo: "슈즈" },
  { id: "accessories", labelKo: "악세서리" },
  { id: "sports", labelKo: "스포츠" },
];

export const products: Product[] = [];

export function formatKrw(price: number) {
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: "KRW",
    maximumFractionDigits: 0,
  }).format(price);
}

export function getProduct(id: string) {
  return products.find((p) => p.id === id);
}
