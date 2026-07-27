"use client";

import { useEffect, useRef, useState } from "react";
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
  const trackRef = useRef<HTMLDivElement>(null);
  const pausedUntil = useRef(0);

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

  // Soft autoplay on fine pointers only — mobile is finger-scroll only
  useEffect(() => {
    const fine = window.matchMedia("(hover: hover) and (pointer: fine)");
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (!fine.matches || reduce.matches) return;

    const id = window.setInterval(() => {
      if (Date.now() < pausedUntil.current) return;
      const el = trackRef.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      if (rect.bottom < 0 || rect.top > window.innerHeight) return;

      const page = el.clientWidth * 0.92;
      const max = el.scrollWidth - el.clientWidth;
      if (max <= 0) return;
      const next = el.scrollLeft + page;
      el.scrollTo({
        left: next >= max - 4 ? 0 : next,
        behavior: "smooth",
      });
    }, 4500);

    return () => clearInterval(id);
  }, [list.length]);

  const pause = () => {
    pausedUntil.current = Date.now() + 10000;
  };

  return (
    <section className="best-live" aria-label="실시간 주문상품 10선">
      <div className="best-live__inner">
        <div className="best-live__stage">
          <div className="best-live__copy">
            <p className="best-live__eyebrow">Briq Edit</p>
            <h2 className="best-live__title">실시간 주문상품 10선</h2>
            <p className="best-live__lead">
              지금 이 순간 주문이 이어지고 있는
              <br className="br-mobile" /> 상품들을 만나보세요.
            </p>
          </div>

          <div
            ref={trackRef}
            className="best-carousel"
            style={{ ["--slide-count" as string]: String(list.length) }}
            onPointerDown={pause}
            onTouchStart={pause}
            onWheel={pause}
          >
            <div className="best-carousel__track">
              {list.map((product) => (
                <div key={product.id} className="best-carousel__item">
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
