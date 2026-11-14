import { cookies } from "next/headers";
import { getProduct, type Product, type ProductVariant } from "@/data/products";
import { cartUnitPrice } from "@/lib/cart-price";

export const CART_COOKIE = "briq-cart";

export type CartLine = {
  productId: string;
  variantId?: string;
  /** "no" or wrist size like "18.0" */
  braceletCm?: string;
  qty: number;
};

export type CartItem = {
  product: Product;
  variant?: ProductVariant;
  braceletCm?: string;
  qty: number;
};

function lineKey(productId: string, variantId?: string, braceletCm?: string) {
  const v = variantId ?? "";
  const b = braceletCm ?? "";
  return `${productId}::${v}::${b}`;
}

export async function readCartLines(): Promise<CartLine[]> {
  const jar = await cookies();
  const raw = jar.get(CART_COOKIE)?.value;
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    const lines: CartLine[] = [];
    for (const row of parsed) {
      if (!row || typeof row !== "object") continue;
      const r = row as Record<string, unknown>;
      const productId = typeof r.productId === "string" ? r.productId : "";
      const qty = typeof r.qty === "number" && r.qty > 0 ? Math.floor(r.qty) : 0;
      const variantId =
        typeof r.variantId === "string" && r.variantId ? r.variantId : undefined;
      const braceletCm =
        typeof r.braceletCm === "string" && r.braceletCm
          ? r.braceletCm
          : undefined;
      if (!productId || qty <= 0) continue;
      lines.push({ productId, variantId, braceletCm, qty });
    }
    return lines;
  } catch {
    return [];
  }
}

export async function writeCartLines(lines: CartLine[]) {
  const jar = await cookies();
  jar.set(CART_COOKIE, JSON.stringify(lines), {
    path: "/",
    httpOnly: true,
    sameSite: "lax",
    maxAge: 60 * 60 * 24 * 30,
  });
}

export function resolveCartItems(lines: CartLine[]): CartItem[] {
  const items: CartItem[] = [];
  for (const line of lines) {
    const product = getProduct(line.productId);
    if (!product) continue;
    const variant = line.variantId
      ? product.variants?.find((v) => v.id === line.variantId)
      : undefined;
    if (line.variantId && !variant) continue;
    items.push({
      product,
      variant,
      braceletCm: line.braceletCm,
      qty: line.qty,
    });
  }
  return items;
}

export async function getCartItems(): Promise<CartItem[]> {
  return resolveCartItems(await readCartLines());
}

export async function getCartCount(): Promise<number> {
  const lines = await readCartLines();
  return lines.reduce((sum, line) => sum + line.qty, 0);
}

export function cartSubtotal(items: CartItem[]): number {
  return items.reduce((sum, item) => {
    const unit = cartUnitPrice(item.product, item.variant, item.braceletCm);
    return sum + unit * item.qty;
  }, 0);
}

export function upsertCartLine(
  lines: CartLine[],
  productId: string,
  qty: number,
  variantId?: string,
  braceletCm?: string,
): CartLine[] {
  const key = lineKey(productId, variantId, braceletCm);
  const existing = lines.find(
    (l) => lineKey(l.productId, l.variantId, l.braceletCm) === key,
  );
  if (existing) {
    return lines.map((l) =>
      lineKey(l.productId, l.variantId, l.braceletCm) === key
        ? { ...l, qty: l.qty + qty }
        : l,
    );
  }
  return [...lines, { productId, variantId, braceletCm, qty }];
}

export function setCartLineQty(
  lines: CartLine[],
  productId: string,
  qty: number,
  variantId?: string,
  braceletCm?: string,
): CartLine[] {
  const key = lineKey(productId, variantId, braceletCm);
  if (qty <= 0) {
    return lines.filter(
      (l) => lineKey(l.productId, l.variantId, l.braceletCm) !== key,
    );
  }
  return lines.map((l) =>
    lineKey(l.productId, l.variantId, l.braceletCm) === key
      ? { ...l, qty }
      : l,
  );
}

export function removeCartLine(
  lines: CartLine[],
  productId: string,
  variantId?: string,
  braceletCm?: string,
): CartLine[] {
  const key = lineKey(productId, variantId, braceletCm);
  return lines.filter(
    (l) => lineKey(l.productId, l.variantId, l.braceletCm) !== key,
  );
}

export function productHref(productId: string, variantId?: string) {
  return variantId
    ? `/product/${productId}?color=${encodeURIComponent(variantId)}`
    : `/product/${productId}`;
}
