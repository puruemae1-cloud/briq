import type { Product, ProductVariant } from "@/data/products";
import { braceletResizeFee } from "@/data/cw-twelve-picnmix";

export function cartUnitPrice(
  product: Product,
  variant?: ProductVariant,
  braceletCm?: string | null,
): number {
  const base = variant?.price ?? product.price;
  return base + braceletResizeFee(product, braceletCm);
}
