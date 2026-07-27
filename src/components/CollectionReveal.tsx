"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ProductCard } from "@/components/ProductCard";
import type { Product } from "@/data/products";
import type { ProductSort } from "@/lib/product-sort";

const MOBILE_PREVIEW = 10;

/**
 * Mobile: 10 products + link to /shop (lighter homepage scroll).
 * Desktop: full collection grid.
 * Defaults to mobile preview until matchMedia runs (avoids dumping 100 cards on phones).
 */
export function CollectionReveal({
  products,
  sort = "new",
}: {
  products: Product[];
  sort?: ProductSort;
}) {
  const [isDesktop, setIsDesktop] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia("(min-width: 900px)");
    const apply = () => setIsDesktop(mq.matches);
    apply();
    mq.addEventListener("change", apply);
    return () => mq.removeEventListener("change", apply);
  }, []);

  const visible = isDesktop ? products : products.slice(0, MOBILE_PREVIEW);
  const shopHref =
    sort && sort !== "new" ? `/shop?sort=${sort}` : "/shop?sort=new";

  return (
    <>
      <div className="product-grid">
        {visible.map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
      {!isDesktop && products.length > MOBILE_PREVIEW ? (
        <div className="collection-100__sentinel">
          <Link href={shopHref} className="btn btn-solid collection-100__more-btn">
            전체 상품 보기
          </Link>
        </div>
      ) : null}
    </>
  );
}
