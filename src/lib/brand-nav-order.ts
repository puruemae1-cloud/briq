/**
 * Global brand chip / nav display order across homepage rails, shop filters,
 * and header menus.
 *
 *   샤넬 → 구찌 → (앞으로 추가되는 브랜드) → 버버리 → 폴 스미스
 *   → 아크테릭스 → 벨스타프
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
  chanel: 100,
  gucci: 200,
  /** Slot for newly added brands — always after Gucci, before Burberry. */
  _new: 250,
  burberry: 300,
  "paul-smith": 400,
  arcteryx: 900,
  belstaff: 1000,
};

function brandFamily(id: string): string | null {
  const x = id.toLowerCase();
  if (x === "chanel" || x.startsWith("chanel-")) return "chanel";
  if (x === "gucci" || x.startsWith("gucci-")) return "gucci";
  if (x === "burberry" || x.startsWith("burberry-")) return "burberry";
  if (x === "paul-smith" || x.startsWith("paul-smith-")) return "paul-smith";
  if (x === "arcteryx" || x.startsWith("arcteryx-")) return "arcteryx";
  if (x === "belstaff" || x.startsWith("belstaff-")) return "belstaff";
  if (
    x === "london-undercover" ||
    x === "umbrellas" ||
    x.startsWith("london-undercover")
  ) {
    return "_new";
  }
  if (x === "christopher-ward" || x.startsWith("christopher-ward")) {
    return "_new";
  }
  if (x === "galvin-green" || x.startsWith("galvin-green")) return "_new";
  return null;
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
  "chanel",
  "gucci",
  // new brands insert here
  "prada",
  "hermes",
  "london-undercover",
  "christopher-ward",
  "galvin-green",
  "burberry",
  "paul-smith",
  "arcteryx",
  "belstaff",
] as const;
