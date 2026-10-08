import { cookies } from "next/headers";
import { CART_COOKIE, sumCartQty } from "@/lib/cart-cookie";

/**
 * Cart item count from the httpOnly cart cookie.
 *
 * Must not import `@/data/products` (directly or via `cart-server`): anything it
 * pulls in is parsed on every cold start (the catalogue graph is hundreds of MB).
 */
export { CART_COOKIE };

export async function getCartCount(): Promise<number> {
  const jar = await cookies();
  const raw = jar.get(CART_COOKIE)?.value;
  if (!raw) return 0;
  try {
    return sumCartQty(JSON.parse(raw));
  } catch {
    return 0;
  }
}
