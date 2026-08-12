"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ProductCard } from "@/components/ProductCard";
import type { Product } from "@/data/product-types";
import { usePurchases } from "@/lib/purchase-store";

const MAX_ITEMS = 10;

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

export function BestItems() {
  const counts = usePurchases((s) => s.counts);
  const [list, setList] = useState<Product[]>([]);
  const trackRef = useRef<HTMLDivElement>(null);
  const pausedUntil = useRef(0);

  const topIds = useMemo(() => {
    return Object.entries(counts)
      .filter(([, count]) => count > 0)
      .sort((a, b) => b[1] - a[1])
      .slice(0, MAX_ITEMS)
      .map(([id]) => id);
  }, [counts]);

  useEffect(() => {
    let cancelled = false;
    if (topIds.length === 0) {
      setList([]);
      return;
    }
    void fetchProductsByIds(topIds).then((products) => {
      if (cancelled) return;
      const order = new Map(topIds.map((id, i) => [id, i]));
      products.sort(
        (a, b) => (order.get(a.id) ?? 99) - (order.get(b.id) ?? 99),
      );
      setList(products);
    });
    return () => {
      cancelled = true;
    };
  }, [topIds]);

  useEffect(() => {
    if (list.length === 0) return;
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
        behavior: "auto",
      });
    }, 4500);

    return () => clearInterval(id);
  }, [list.length]);

  const pause = () => {
    pausedUntil.current = Date.now() + 10000;
  };

  if (list.length === 0) {
    return null;
  }

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
