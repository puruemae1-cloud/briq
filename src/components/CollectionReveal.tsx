"use client";

import { useMemo } from "react";
import { CollectionTierBlock } from "@/components/CollectionTierBlock";
import type { Product } from "@/data/products";
import { SECTION_LIMIT } from "@/lib/collection-edit";
import { compareProductsByNewest } from "@/lib/product-sort";
import { usePurchases } from "@/lib/purchase-store";

/**
 * Client-only bestseller tier — re-ranks by live purchase counts.
 * Signature / 신상품 are server-rendered so newest `registeredAt` is in HTML.
 */
export function CollectionBestsellerTier({
  products,
}: {
  products: Product[];
}) {
  const counts = usePurchases((s) => s.counts);
  const bestseller = useMemo(() => {
    return products
      .filter((p) => (counts[p.id] ?? 0) >= 1)
      .sort((a, b) => {
        const ca = counts[a.id] ?? 0;
        const cb = counts[b.id] ?? 0;
        if (cb !== ca) return cb - ca;
        return compareProductsByNewest(a, b);
      })
      .slice(0, SECTION_LIMIT);
  }, [products, counts]);

  return <CollectionTierBlock tier="bestseller" products={bestseller} />;
}
