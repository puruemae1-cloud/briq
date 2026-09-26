import { cookies } from "next/headers";

/**
 * Cart badge count for the site header.
 *
 * Must not import `@/data/products` (directly or via `cart-server`): the root
 * layout imports this, so anything it pulls in is bundled into every page and
 * parsed on every cold start (the catalogue graph is hundreds of MB).
 */
export const CART_COOKIE = "briq-cart";

type CartLineQty = { qty: number };

export async function getCartCount(): Promise<number> {
  const jar = await cookies();
  const raw = jar.get(CART_COOKIE)?.value;
  if (!raw) return 0;
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return 0;
    let sum = 0;
    for (const row of parsed) {
      if (!row || typeof row !== "object") continue;
      const qty = (row as CartLineQty).qty;
      if (typeof qty === "number" && qty > 0) sum += Math.floor(qty);
    }
    return sum;
  } catch {
    return 0;
  }
}
