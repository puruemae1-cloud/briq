import type {  Product, ProductVariant  } from "@/data/product-types";
import { braceletResizeFee } from "@/data/cw-twelve-picnmix";
import { productDisplayPrice } from "@/data/product-utils";

export function cartUnitPrice(
  product: Product,
  variant?: ProductVariant,
  braceletCm?: string | null,
): number {
  const base = productDisplayPrice(product, variant);
  return base + braceletResizeFee(product, braceletCm);
}
