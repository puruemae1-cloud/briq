"use client";

import { useMemo, useState } from "react";
import { ProductCard } from "@/components/ProductCard";
import type { Product } from "@/data/products";

const DEFAULT_PAGE_SIZE = 24;

export function ShopProductGrid({
  products,
  pageSize = DEFAULT_PAGE_SIZE,
}: {
  products: Product[];
  pageSize?: number;
}) {
  const [visibleCount, setVisibleCount] = useState(pageSize);
  const visible = useMemo(
    () => products.slice(0, visibleCount),
    [products, visibleCount],
  );
  const remaining = Math.max(0, products.length - visible.length);
  const canShowMore = remaining > 0;

  return (
    <>
      <div className="product-grid">
        {visible.map((p) => (
          <ProductCard
            key={p.shopColorKey ? `${p.id}-${p.shopColorKey}` : p.id}
            product={p}
          />
        ))}
      </div>
      {canShowMore ? (
        <div className="shop-browse__morebar">
          <button
            type="button"
            className="shop-browse__more-btn"
            onClick={() =>
              setVisibleCount((count) =>
                Math.min(count + pageSize, products.length),
              )
            }
          >
            더보기
            <span className="shop-browse__more-remaining">
              {remaining.toLocaleString()}개 남음
            </span>
          </button>
        </div>
      ) : null}
    </>
  );
}
