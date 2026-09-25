import { cookies } from "next/headers";
import { CART_COOKIE, cartCountFromRaw } from "@/lib/cart-count-cookie";

/**
 * Server-side cart badge count (API routes / dynamic pages only).
 *
 * Never call this from `app/layout.tsx` or any component the layout renders:
 * `cookies()` there makes the whole site dynamic. The header uses
 * `HeaderCartCount` (client) + the `briq-cart-n` cookie instead.
 */
export { CART_COOKIE, CART_COUNT_COOKIE } from "@/lib/cart-count-cookie";

export async function getCartCount(): Promise<number> {
  const jar = await cookies();
  return cartCountFromRaw(jar.get(CART_COOKIE)?.value);
}
