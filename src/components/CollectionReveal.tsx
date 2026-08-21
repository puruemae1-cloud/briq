"use client";

import { useEffect, useMemo, useState } from "react";
import { CollectionTierBlock } from "@/components/CollectionTierBlock";
import type { Product } from "@/data/product-types";
import { SECTION_LIMIT } from "@/lib/collection-edit";
import { stockSortRank } from "@/lib/product-sort";
import { usePurchases } from "@/lib/purchase-store";

async function fetchProductsByIds(ids: string[]): Promise<Product[]> {
  if (ids.length === 0) return [];
  const res = await fetch(
    `/api/products/by-ids?ids=${encodeURIComponent(ids.join(","))}`,
    { cache: "force-cache" },
  );
  if (!res.ok) return [];
  const data = (await res.json()) as { products?: Product[] };
  return data.products ?? [];
}

/**
 * Client-only bestseller tier — re-ranks by live purchase counts.
 * Loads only the purchased product ids (not the full catalogue).
 */
export function CollectionBestsellerTier() {
  const counts = usePurchases((s) => s.counts);
  const [bestseller, setBestseller] = useState<Product[]>([]);

  const topIds = useMemo(() => {
    return Object.entries(counts)
      .filter(([, count]) => count >= 1)
      .sort((a, b) => b[1] - a[1])
      .slice(0, SECTION_LIMIT * 2)
      .map(([id]) => id);
  }, [counts]);

  useEffect(() => {
    let cancelled = false;
    if (topIds.length === 0) {
      setBestseller([]);
      return;
    }
    void fetchProductsByIds(topIds).then((products) => {
      if (cancelled) return;
      const order = new Map(topIds.map((id, i) => [id, i]));
      products.sort((a, b) => {
        const stock = stockSortRank(a) - stockSortRank(b);
        if (stock !== 0) return stock;
        return (order.get(a.id) ?? 99) - (order.get(b.id) ?? 99);
      });
      setBestseller(products.slice(0, SECTION_LIMIT));
    });
    return () => {
      cancelled = true;
    };
  }, [topIds]);

  return <CollectionTierBlock tier="bestseller" products={bestseller} />;
}
