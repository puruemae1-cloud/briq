/** Cart cookie names shared by server code and the client header badge. */
export const CART_COOKIE = "briq-cart";

/**
 * Readable item count next to the httpOnly cart, so the header badge is filled
 * in the browser and pages stay identical for every visitor (CDN-cacheable).
 */
export const CART_COUNT_COOKIE = "briq-cart-n";

export const CART_CHANGE_EVENT = "briq:cart-change";

export const CART_COOKIE_MAX_AGE = 60 * 60 * 24 * 30;

export function sumCartQty(lines: unknown): number {
  if (!Array.isArray(lines)) return 0;
  let sum = 0;
  for (const row of lines) {
    if (!row || typeof row !== "object") continue;
    const qty = (row as { qty?: unknown }).qty;
    if (typeof qty === "number" && qty > 0) sum += Math.floor(qty);
  }
  return sum;
}
