"use client";

import { useCallback, useMemo, useState, useTransition } from "react";
import { ProductCard } from "@/components/ProductCard";
import type { Product } from "@/data/product-types";
import { usePurchases } from "@/lib/purchase-store";

const DEFAULT_PAGE_SIZE = 24;

export type ShopGridQuery = {
  category: string;
  sub?: string;
  q?: string;
  sort: string;
};

export function ShopProductGrid({
  products: initialProducts,
  totalCount,
  pageSize = DEFAULT_PAGE_SIZE,
  query,
  liveOrdersRank = false,
}: {
  products: Product[];
  totalCount: number;
  pageSize?: number;
  query: ShopGridQuery;
  /** Re-rank currently loaded cards by live purchase counts (주문많은순). */
  liveOrdersRank?: boolean;
}) {
  const [products, setProducts] = useState(initialProducts);
  const [total, setTotal] = useState(totalCount);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const counts = usePurchases((s) => s.counts);

  const visible = useMemo(() => {
    if (!liveOrdersRank) return products;
    return [...products].sort((a, b) => {
      const ca = counts[a.id] ?? 0;
      const cb = counts[b.id] ?? 0;
      if (cb !== ca) return cb - ca;
      const ba = a.badge ? 1 : 0;
      const bb = b.badge ? 1 : 0;
      if (bb !== ba) return bb - ba;
      return a.price - b.price;
    });
  }, [products, liveOrdersRank, counts]);

  const remaining = Math.max(0, total - products.length);
  const canShowMore = remaining > 0;

  const loadMore = useCallback(async () => {
    if (loadingMore || remaining <= 0) return;
    setLoadingMore(true);
    setError(null);
    try {
      const sp = new URLSearchParams();
      if (query.category && query.category !== "all") {
        sp.set("category", query.category);
      }
      if (query.sub) sp.set("sub", query.sub);
      if (query.q?.trim()) sp.set("q", query.q.trim());
      sp.set("sort", query.sort);
      sp.set("offset", String(products.length));
      sp.set("limit", String(pageSize));

      const res = await fetch(`/api/products/shop?${sp.toString()}`, {
        headers: { Accept: "application/json" },
      });
      if (!res.ok) throw new Error(`load failed (${res.status})`);
      const data = (await res.json()) as {
        products?: Product[];
        total?: number;
      };
      const next = Array.isArray(data.products) ? data.products : [];
      startTransition(() => {
        setProducts((prev) => {
          const seen = new Set(
            prev.map((p) => (p.shopColorKey ? `${p.id}-${p.shopColorKey}` : p.id)),
          );
          const merged = [...prev];
          for (const p of next) {
            const key = p.shopColorKey ? `${p.id}-${p.shopColorKey}` : p.id;
            if (seen.has(key)) continue;
            seen.add(key);
            merged.push(p);
          }
          return merged;
        });
        if (typeof data.total === "number") setTotal(data.total);
      });
    } catch {
      setError("더 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.");
    } finally {
      setLoadingMore(false);
    }
  }, [loadingMore, remaining, query, products.length, pageSize]);

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
            disabled={loadingMore || isPending}
            onClick={() => void loadMore()}
          >
            {loadingMore ? "불러오는 중…" : "더보기"}
            <span className="shop-browse__more-remaining">
              {remaining.toLocaleString()}개 남음
            </span>
          </button>
          {error ? <p className="shop-browse__more-error">{error}</p> : null}
        </div>
      ) : null}
    </>
  );
}
