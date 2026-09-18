import type { Product } from "@/data/product-types";

/** Briq NEW badge lifetime after weekly sync registration / newBadgeAt stamp. */
export const NEW_BADGE_DAYS = 7;
const NEW_BADGE_MS = NEW_BADGE_DAYS * 24 * 60 * 60 * 1000;

function parseIsoMs(raw: string | undefined): number | null {
  if (!raw) return null;
  const t = Date.parse(raw);
  return Number.isFinite(t) ? t : null;
}

/**
 * When the NEW window started.
 * Prefer explicit `newBadgeAt` (weekly sync stamp); else `registeredAt`
 * when the row still carries catalog `badge: "New"`.
 */
export function productNewBadgeStartMs(product: Product): number | null {
  const explicit = parseIsoMs(product.newBadgeAt);
  if (explicit != null) return explicit;
  if (product.badge?.trim() === "New") {
    return parseIsoMs(product.registeredAt);
  }
  return null;
}

/** True when the product should show a Briq "New" badge (7-day window). */
export function productShowsNewBadge(product: Product): boolean {
  const hasMark =
    Boolean(product.newBadgeAt?.trim()) || product.badge?.trim() === "New";
  if (!hasMark) return false;
  const start = productNewBadgeStartMs(product);
  if (start == null) return false;
  const age = Date.now() - start;
  return age >= 0 && age < NEW_BADGE_MS;
}

/**
 * PLP overlay badge after Sold Out / % OFF handling.
 * Expired catalog `badge: "New"` is suppressed; other badges (Sale, Nearly New) pass through.
 */
export function productCardBadgeText(product: Product): string | null {
  if (productShowsNewBadge(product)) return "New";
  const b = product.badge?.trim();
  if (!b || b === "New") return null;
  return b;
}
