"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  useTransition,
} from "react";
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

type ShopPagePayload = {
  products?: Product[];
  total?: number;
};

function shopApiUrl(
  query: ShopGridQuery,
  offset: number,
  pageSize: number,
): string {
  const sp = new URLSearchParams();
  if (query.category && query.category !== "all") {
    sp.set("category", query.category);
  }
  if (query.sub) sp.set("sub", query.sub);
  if (query.q?.trim()) sp.set("q", query.q.trim());
  sp.set("sort", query.sort);
  sp.set("offset", String(offset));
  sp.set("limit", String(pageSize));
  return `/api/products/shop?${sp.toString()}`;
}

export function ShopProductGrid({
  products: initialProducts,
  nextPageProducts = [],
  totalCount,
  pageSize = DEFAULT_PAGE_SIZE,
  query,
  liveOrdersRank = false,
}: {
  products: Product[];
  /** SSR-warmed page 2 — first "더보기" is instant (no cold API). */
  nextPageProducts?: Product[];
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
  const ssrNextConsumed = useRef(false);
  const prefetchRef = useRef<{
    offset: number;
    promise: Promise<ShopPagePayload | null>;
  } | null>(null);

  // Reset when the PLP query changes (nav / sort / search).
  useEffect(() => {
    setProducts(initialProducts);
    setTotal(totalCount);
    setError(null);
    ssrNextConsumed.current = false;
    prefetchRef.current = null;
  }, [initialProducts, totalCount, query.category, query.sub, query.q, query.sort]);

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

  const fetchPage = useCallback(
    async (offset: number): Promise<ShopPagePayload | null> => {
      try {
        const res = await fetch(shopApiUrl(query, offset, pageSize), {
          headers: { Accept: "application/json" },
        });
        if (!res.ok) return null;
        return (await res.json()) as ShopPagePayload;
      } catch {
        return null;
      }
    },
    [query, pageSize],
  );

  const ensurePrefetch = useCallback(
    (offset: number) => {
      if (offset >= total) return;
      const cur = prefetchRef.current;
      if (cur?.offset === offset) return;
      prefetchRef.current = {
        offset,
        promise: fetchPage(offset),
      };
    },
    [fetchPage, total],
  );

  // Warm the next network page immediately (skip idle — cold API is ~10s+).
  useEffect(() => {
    if (remaining <= 0) return;
    const nextOffset = products.length;
    // Page 2 may already be in SSR props — prefetch page 3 instead.
    const target =
      !ssrNextConsumed.current &&
      nextPageProducts.length > 0 &&
      nextOffset === initialProducts.length
        ? nextOffset + pageSize
        : nextOffset;
    ensurePrefetch(target);
  }, [
    products.length,
    remaining,
    ensurePrefetch,
    nextPageProducts.length,
    initialProducts.length,
    pageSize,
  ]);

  const appendPage = useCallback(
    (data: ShopPagePayload) => {
      const next = Array.isArray(data.products) ? data.products : [];
      startTransition(() => {
        setProducts((prev) => {
          const seen = new Set(
            prev.map((p) =>
              p.shopColorKey ? `${p.id}-${p.shopColorKey}` : p.id,
            ),
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
    },
    [],
  );

  const loadMore = useCallback(async () => {
    if (loadingMore || remaining <= 0) return;
    setLoadingMore(true);
    setError(null);
    const offset = products.length;
    try {
      // Instant path: SSR-embedded page 2.
      if (
        !ssrNextConsumed.current &&
        nextPageProducts.length > 0 &&
        offset === initialProducts.length
      ) {
        ssrNextConsumed.current = true;
        appendPage({ products: nextPageProducts, total });
        ensurePrefetch(offset + pageSize);
        return;
      }

      let data: ShopPagePayload | null = null;
      const pre = prefetchRef.current;
      if (pre?.offset === offset) {
        data = await pre.promise;
        prefetchRef.current = null;
      }
      if (!data) {
        data = await fetchPage(offset);
      }
      if (!data?.products?.length && remaining > 0) {
        setError("더 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.");
        return;
      }
      if (data) {
        appendPage(data);
        ensurePrefetch(offset + pageSize);
      }
    } finally {
      setLoadingMore(false);
    }
  }, [
    loadingMore,
    remaining,
    products.length,
    nextPageProducts,
    initialProducts.length,
    total,
    appendPage,
    ensurePrefetch,
    fetchPage,
    pageSize,
  ]);

  return (
    <div className="shop-grid-wrap">
      <div className="product-grid">
        {visible.map((product) => (
          <ProductCard
            key={
              product.shopColorKey
                ? `${product.id}-${product.shopColorKey}`
                : product.id
            }
            product={product}
          />
        ))}
      </div>
      {canShowMore ? (
        <div className="shop-load-more">
          <p className="shop-load-more__meta">
            {remaining.toLocaleString("ko-KR")}개 남음
          </p>
          <button
            type="button"
            className="shop-load-more__btn"
            disabled={loadingMore || isPending}
            onClick={() => void loadMore()}
          >
            {loadingMore ? "불러오는 중…" : "더보기"}
          </button>
          {error ? <p className="shop-load-more__error">{error}</p> : null}
        </div>
      ) : null}
    </div>
  );
}
