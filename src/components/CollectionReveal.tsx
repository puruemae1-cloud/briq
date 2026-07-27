"use client";

import Link from "next/link";
import { useMemo } from "react";
import { ProductCard } from "@/components/ProductCard";
import type { Product } from "@/data/products";
import {
  EDIT_TIER_COPY,
  curateCollectionEdit,
  type EditTier,
} from "@/lib/collection-edit";
import { usePurchases } from "@/lib/purchase-store";

function TierBlock({
  tier,
  products,
}: {
  tier: EditTier;
  products: Product[];
}) {
  if (!products.length) return null;
  const copy = EDIT_TIER_COPY[tier];
  return (
    <div className="collection-edit-tier">
      <header className="collection-edit-tier__head">
        <h3 className="collection-edit-tier__title">{copy.titleKo}</h3>
      </header>
      <div className="product-grid">
        {products.map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
    </div>
  );
}

/**
 * Three curated sections + link through to the full shop catalogue.
 */
export function CollectionReveal({ products }: { products: Product[] }) {
  const counts = usePurchases((s) => s.counts);
  const curated = useMemo(
    () => curateCollectionEdit(products, counts),
    [products, counts],
  );

  return (
    <>
      <TierBlock tier="signature" products={curated.signature} />
      <TierBlock tier="bestseller" products={curated.bestseller} />
      <TierBlock tier="new" products={curated.newItems} />

      <div className="collection-100__sentinel">
        <Link href="/shop" className="btn btn-solid collection-100__more-btn">
          전체 상품 보러가기
        </Link>
      </div>
    </>
  );
}
