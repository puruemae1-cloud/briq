"use client";

import { useEffect, useMemo, useState } from "react";
import { CollectionReveal } from "@/components/CollectionReveal";
import type { Product } from "@/data/products";
import { usePurchases } from "@/lib/purchase-store";

/** Re-ranks by live purchase counts once client store hydrates. */
export function CollectionOrdersGrid({ products }: { products: Product[] }) {
  const counts = usePurchases((s) => s.counts);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const list = useMemo(() => {
    if (!mounted) return products;
    return [...products].sort((a, b) => {
      const ca = counts[a.id] ?? 0;
      const cb = counts[b.id] ?? 0;
      if (cb !== ca) return cb - ca;
      const ba = a.badge ? 1 : 0;
      const bb = b.badge ? 1 : 0;
      if (bb !== ba) return bb - ba;
      return a.price - b.price;
    });
  }, [products, counts, mounted]);

  return <CollectionReveal products={list} />;
}
