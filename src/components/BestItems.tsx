"use client";

import { useEffect, useState } from "react";
import { ProductCard } from "@/components/ProductCard";
import { products } from "@/data/products";
import { usePurchases } from "@/lib/purchase-store";

const MAX_ITEMS = 10;

/** Curated fallback so the rail is always full before real orders come in. */
const fallback = [...products]
  .sort((a, b) => (b.badge ? 1 : 0) - (a.badge ? 1 : 0))
  .slice(0, MAX_ITEMS);

export function BestItems() {
  const counts = usePurchases((s) => s.counts);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const ordered = mounted
    ? products
        .map((product) => ({ product, count: counts[product.id] ?? 0 }))
        .filter((entry) => entry.count > 0)
        .sort((a, b) => b.count - a.count)
        .map((entry) => entry.product)
    : [];

  const seen = new Set(ordered.map((p) => p.id));
  const list = [
    ...ordered,
    ...fallback.filter((p) => !seen.has(p.id)),
  ].slice(0, MAX_ITEMS);

  // Extra clones so the last steps still fill the viewport (PC shows 5).
  const loop = [...list, ...list.slice(0, 5)];

  return (
    <section className="best-live" aria-label="실시간 주문상품 10선">
      <div className="best-live__inner">
        <div className="best-live__stage">
          <div className="best-live__copy">
            <p className="best-live__eyebrow">Briq Edit</p>
            <h2 className="best-live__title">실시간 주문상품 10선</h2>
            <p className="best-live__lead">
              지금 이 순간 주문이 이어지고 있는 상품들을 만나보세요.
            </p>
          </div>

          <div
            className="best-carousel"
            style={{ ["--slide-count" as string]: String(list.length) }}
          >
            <div className="best-carousel__track">
              {loop.map((product, i) => (
                <div
                  key={`${product.id}-${i}`}
                  className="best-carousel__item"
                >
                  <ProductCard product={product} />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
