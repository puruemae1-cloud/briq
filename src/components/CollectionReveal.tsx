"use client";

import { useMemo, useState } from "react";
import { ProductCard } from "@/components/ProductCard";
import type { Product } from "@/data/products";
import {
  EDIT_TIER_COPY,
  curateCollectionEdit,
  type EditTier,
} from "@/lib/collection-edit";

const EXPAND_BY = 20;

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
        <p className="collection-edit-tier__eyebrow">{copy.eyebrowKo}</p>
        <h3 className="collection-edit-tier__title">{copy.titleKo}</h3>
        <p className="collection-edit-tier__purpose">{copy.purposeKo}</p>
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
 * Curated first 20 (signature / bestseller / new), then expand +20 on click.
 */
export function CollectionReveal({ products }: { products: Product[] }) {
  const curated = useMemo(() => curateCollectionEdit(products), [products]);
  const [extra, setExtra] = useState(0);

  const expanded = curated.rest.slice(0, extra);
  const visibleCount = curated.preview.length + expanded.length;
  const total = curated.total;
  const hasMore = visibleCount < total;

  return (
    <>
      <TierBlock tier="signature" products={curated.signature} />
      <TierBlock tier="bestseller" products={curated.bestseller} />
      <TierBlock tier="new" products={curated.newItems} />

      {expanded.length > 0 ? (
        <div className="collection-edit-tier collection-edit-tier--more">
          <header className="collection-edit-tier__head">
            <p className="collection-edit-tier__eyebrow">More from Briq</p>
            <h3 className="collection-edit-tier__title">이어서 살펴보기</h3>
          </header>
          <div className="product-grid">
            {expanded.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        </div>
      ) : null}

      {hasMore ? (
        <div className="collection-100__sentinel">
          <button
            type="button"
            className="btn btn-solid collection-100__more-btn"
            onClick={() => setExtra((n) => n + EXPAND_BY)}
          >
            전체 상품 보러가기 ({visibleCount} / {total})
          </button>
        </div>
      ) : null}
    </>
  );
}
