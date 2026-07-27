import type { Product } from "@/data/products";

/** Curated homepage / 100 Collection edit roles. */
export type EditTier = "signature" | "bestseller" | "new";

export const EDIT_TIER_COPY: Record<
  EditTier,
  { titleKo: string; purposeKo: string; eyebrowKo: string }
> = {
  signature: {
    eyebrowKo: "Signature · 100만 원 이상",
    titleKo: "프리미엄을 재정의하다, 하이엔드 컬렉션",
    purposeKo: "브랜드의 프리미엄 이미지 구축 및 정체성 전달",
  },
  bestseller: {
    eyebrowKo: "Bestseller · 입문·데일리",
    titleKo: "첫 구매자 만족도 1위 컬렉션",
    purposeKo: "부담 없는 첫 구매 유도 및 실질적인 매출 발생",
  },
  new: {
    eyebrowKo: "New · 시즌 기획",
    titleKo: "가장 먼저 만나는 신상품 큐레이션",
    purposeKo: "재방문 고객 호기심 자극 및 활력 부여",
  },
};

/** First-screen mix for the 100 Collection edit (~25 / 50 / 25). */
export const EDIT_QUOTA = {
  signature: 5,
  bestseller: 11,
  new: 4,
} as const;

const SIGNATURE_MIN = 1_000_000;
const BESTSELLER_MIN = 80_000;
const BESTSELLER_MAX = 200_000;

/**
 * Resolve edit tier for curation.
 * Explicit `product.editTier` always wins — set it when registering products.
 * Otherwise inferred from price / badge / recency.
 */
export function resolveEditTier(product: Product): EditTier {
  if (product.editTier) return product.editTier;

  if (product.price >= SIGNATURE_MIN) return "signature";

  const badge = (product.badge || "").toLowerCase();
  if (badge === "new" || badge === "limited") return "new";

  if (product.price >= BESTSELLER_MIN && product.price <= BESTSELLER_MAX) {
    return "bestseller";
  }

  // Mid-luxury still reads as signature ladder
  if (product.price >= 500_000) return "signature";

  // Very recent registrations without a badge → new
  if (product.registeredAt) {
    const ageMs = Date.now() - Date.parse(product.registeredAt);
    if (Number.isFinite(ageMs) && ageMs >= 0 && ageMs < 1000 * 60 * 60 * 24 * 45) {
      return "new";
    }
  }

  return "bestseller";
}

function registeredMs(product: Product) {
  const ms = product.registeredAt ? Date.parse(product.registeredAt) : 0;
  return Number.isFinite(ms) ? ms : 0;
}

function sortTier(tier: EditTier, list: Product[]) {
  const copy = [...list];
  switch (tier) {
    case "signature":
      return copy.sort((a, b) => b.price - a.price || registeredMs(b) - registeredMs(a));
    case "new":
      return copy.sort((a, b) => registeredMs(b) - registeredMs(a) || b.price - a.price);
    case "bestseller":
    default:
      return copy.sort((a, b) => {
        const ba = a.badge ? 1 : 0;
        const bb = b.badge ? 1 : 0;
        if (bb !== ba) return bb - ba;
        // Prefer 10–15만 band for entry bestsellers
        const score = (p: Product) => {
          if (p.price >= 100_000 && p.price <= 150_000) return 2;
          if (p.price >= BESTSELLER_MIN && p.price <= BESTSELLER_MAX) return 1;
          return 0;
        };
        const ds = score(b) - score(a);
        if (ds !== 0) return ds;
        return registeredMs(b) - registeredMs(a);
      });
  }
}

function take(
  pool: Product[],
  n: number,
  used: Set<string>,
): Product[] {
  const out: Product[] = [];
  for (const p of pool) {
    if (out.length >= n) break;
    if (used.has(p.id)) continue;
    used.add(p.id);
    out.push(p);
  }
  return out;
}

export type CuratedEdit = {
  /** First-screen curated mix (quota filled, then backfilled). */
  preview: Product[];
  signature: Product[];
  bestseller: Product[];
  newItems: Product[];
  /** Remaining catalogue after preview, newest-first for expand. */
  rest: Product[];
  total: number;
};

/**
 * Build the 100 Collection first screen + expandable remainder.
 * Future products auto-bucket via `editTier` or price/badge inference.
 */
export function curateCollectionEdit(products: Product[]): CuratedEdit {
  const buckets: Record<EditTier, Product[]> = {
    signature: [],
    bestseller: [],
    new: [],
  };

  for (const p of products) {
    buckets[resolveEditTier(p)].push(p);
  }

  buckets.signature = sortTier("signature", buckets.signature);
  buckets.bestseller = sortTier("bestseller", buckets.bestseller);
  buckets.new = sortTier("new", buckets.new);

  const used = new Set<string>();
  let signature = take(buckets.signature, EDIT_QUOTA.signature, used);
  let bestseller = take(buckets.bestseller, EDIT_QUOTA.bestseller, used);
  let newItems = take(buckets.new, EDIT_QUOTA.new, used);

  const need = EDIT_QUOTA.signature + EDIT_QUOTA.bestseller + EDIT_QUOTA.new;
  const have = signature.length + bestseller.length + newItems.length;
  if (have < need) {
    const filler = sortTier(
      "new",
      products.filter((p) => !used.has(p.id)),
    );
    const extra = take(filler, need - have, used);
    // Prefer topping up bestseller, then new, then signature
    for (const p of extra) {
      if (bestseller.length < EDIT_QUOTA.bestseller) bestseller.push(p);
      else if (newItems.length < EDIT_QUOTA.new) newItems.push(p);
      else signature.push(p);
    }
  }

  const preview = [...signature, ...bestseller, ...newItems];
  const rest = products
    .filter((p) => !used.has(p.id))
    .sort((a, b) => registeredMs(b) - registeredMs(a) || b.price - a.price);

  return {
    preview,
    signature,
    bestseller,
    newItems,
    rest,
    total: products.length,
  };
}
