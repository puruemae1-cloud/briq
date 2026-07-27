"use client";

import { useState } from "react";
import { ProductCard } from "@/components/ProductCard";
import type { Product } from "@/data/products";

const PAGE_SIZE = 20;

/**
 * 100 Collection loads 20 at a time via explicit "더 보기"
 * so mobile vertical scroll stays light.
 */
export function CollectionReveal({ products }: { products: Product[] }) {
  const [count, setCount] = useState(() => Math.min(PAGE_SIZE, products.length));

  const visible = products.slice(0, count);
  const hasMore = count < products.length;

  return (
    <>
      <div className="product-grid">
        {visible.map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
      {hasMore ? (
        <div className="collection-100__sentinel">
          <button
            type="button"
            className="btn btn-outline collection-100__more-btn"
            onClick={() =>
              setCount((prev) => Math.min(prev + PAGE_SIZE, products.length))
            }
          >
            더 보기 ({count}/{products.length})
          </button>
        </div>
      ) : null}
    </>
  );
}
