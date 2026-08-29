/**
 * Global brand chip / nav display order across homepage rails, shop filters,
 * and header menus.
 *
 *   크리스토퍼와드 → 샤넬 → 구찌 → (앞으로 추가되는 브랜드) → 버버리
 *   → 폴 스미스 → 아크테릭스 → 벨스타프
 *
 * Gender / sport / type leaves stay ahead of brand chips.
 */

const STRUCTURAL_IDS = new Set([
  "womens",
  "mens",
  "luxury-shoes",
  "training-shoes",
  "golf",
  "running",
  "swimming",
  "cycling",
  "tennis",
]);

/** Lower = further left / higher in the list. */
const FAMILY_RANK: Record<string, number> = {
  /** Watches: Christopher Ward before Chanel. */
  "christopher-ward": 50,
  chanel: 100,
  gucci: 200,
  /** Louis Vuitton — after Chanel, before other _new brands. */
  "louis-vuitton": 220,
  /** Slot for newly added brands — always after Gucci, before Burberry. */
  _new: 250,
  burberry: 300,
  "paul-smith": 400,
  arcteryx: 900,
  "london-undercover": 950,
  belstaff: 1000,
};

function brandFamily(id: string): string | null {
  const x = id.toLowerCase();
  if (
    x === "christopher-ward" ||
    x.startsWith("christopher-ward") ||
    x.startsWith("cw-")
  ) {
    return "christopher-ward";
  }
  if (
    x === "chanel" ||
    x.startsWith("chanel-") ||
    x.startsWith("ch-watches")
  ) {
    return "chanel";
  }
  if (x === "gucci" || x.startsWith("gucci-") || x.startsWith("gc-")) return "gucci";
  if (x === "burberry" || x.startsWith("burberry-")) return "burberry";
  if (x === "paul-smith" || x.startsWith("paul-smith-")) return "paul-smith";
  if (x === "arcteryx" || x.startsWith("arcteryx-") || x.startsWith("ax-") || x.startsWith("axa-")) {
    return "arcteryx";
  }
  if (x === "london-undercover" || x === "umbrellas" || x.startsWith("london-undercover") || x.startsWith("lu-")) {
    return "london-undercover";
  }
  if (x === "belstaff" || x.startsWith("belstaff-") || x.startsWith("bb-")) return "belstaff";
  if (x === "louis-vuitton" || x.startsWith("louis-vuitton") || x.startsWith("lv-")) {
    return "louis-vuitton";
  }
  if (x === "galvin-green" || x.startsWith("galvin-green") || x.startsWith("gg-")) return "_new";
  return null;
}

/** Brand rank for a nav / subcategory / tag id (lower = earlier). */
export function brandRankForId(id: string): number {
  return rankForId(id);
}

/**
 * Best (lowest) brand rank across a product's subcategory + tags.
 * Used so homepage rails lead with preferred brands (e.g. CW before Chanel).
 */
export function brandRankForProduct(product: {
  subcategory?: string;
  tags?: string[];
}): number {
  const keys = [product.subcategory, ...(product.tags ?? [])].filter(
    (k): k is string => Boolean(k),
  );
  if (keys.length === 0) return FAMILY_RANK._new;
  let best = Number.POSITIVE_INFINITY;
  for (const key of keys) {
    best = Math.min(best, rankForId(key));
  }
  return Number.isFinite(best) ? best : FAMILY_RANK._new;
}

function rankForId(id: string): number {
  if (STRUCTURAL_IDS.has(id)) return 10;
  const family = brandFamily(id);
  if (family && family in FAMILY_RANK) return FAMILY_RANK[family];
  // Unknown brand-like nodes: treat as "new" (after Gucci).
  if (!STRUCTURAL_IDS.has(id)) return FAMILY_RANK._new;
  return 500;
}

/** Stable sort — preserves relative order within the same rank. */
export function sortNavChildrenByBrandOrder<T extends { id: string }>(
  items: T[],
): T[] {
  return items
    .map((item, index) => ({ item, index }))
    .sort((a, b) => {
      const ra = rankForId(a.item.id);
      const rb = rankForId(b.item.id);
      if (ra !== rb) return ra - rb;
      return a.index - b.index;
    })
    .map(({ item }) => item);
}

/** Preferred slug order for SEO brand hub pages. */
export const SEO_BRAND_SLUG_ORDER = [
  "christopher-ward",
  "chanel",
  "gucci",
  // new brands insert here
  "prada",
  "hermes",
  "london-undercover",
  "galvin-green",
  "burberry",
  "paul-smith",
  "arcteryx",
  "belstaff",
] as const;
