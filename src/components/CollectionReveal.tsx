"use client";

import { useEffect, useRef, useState } from "react";
import { ProductCard } from "@/components/ProductCard";
import type { Product } from "@/data/products";

const PAGE_SIZE = 12;

/**
 * Renders Collection100 in chunks so mobile vertical scroll isn't crushed
 * by 100 product cards + images on first paint.
 */
export function CollectionReveal({ products }: { products: Product[] }) {
  const [count, setCount] = useState(() => Math.min(PAGE_SIZE, products.length));
  const sentinelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (count >= products.length) return;
    const node = sentinelRef.current;
    if (!node) return;

    const io = new IntersectionObserver(
      (entries) => {
        if (!entries.some((e) => e.isIntersecting)) return;
        setCount((prev) => Math.min(prev + PAGE_SIZE, products.length));
      },
      { rootMargin: "600px 0px", threshold: 0 },
    );
    io.observe(node);
    return () => io.disconnect();
  }, [count, products.length]);

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
        <div className="collection-100__sentinel" ref={sentinelRef}>
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
