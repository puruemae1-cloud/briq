/**
 * Client-readable mirror of the httpOnly cart cookie.
 *
 * The header badge reads this in the browser so the root layout never calls
 * `cookies()` — that would force every page (incl. the homepage) to render
 * dynamically on each request instead of being served from the CDN.
 */
export const CART_COOKIE = "briq-cart";
export const CART_COUNT_COOKIE = "briq-cart-n";
export const CART_COUNT_EVENT = "briq:cart-count";

type CartLineQty = { qty: number };

export function cartCountFromRaw(raw: string | undefined): number {
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

export function cartCountFromLines(lines: { qty: number }[]): number {
  return lines.reduce((sum, l) => sum + (l.qty > 0 ? Math.floor(l.qty) : 0), 0);
}
