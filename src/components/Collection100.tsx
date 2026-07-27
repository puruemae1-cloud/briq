import Link from "next/link";
import { pickRotating } from "@/data/home-banners";
import { getCollection100 } from "@/data/products";
import { CollectionOrdersGrid } from "@/components/CollectionOrdersGrid";
import { CollectionReveal } from "@/components/CollectionReveal";
import {
  PRODUCT_SORTS,
  sortProducts,
  type ProductSort,
} from "@/lib/product-sort";

/** @deprecated use ProductSort from product-sort */
export type CollectionSort = ProductSort;

export function sortCollection(
  list: ReturnType<typeof getCollection100>,
  sort: ProductSort,
) {
  return sortProducts(list, sort);
}

const collectionBannerImages = [
  "/banners/rot-luxury-1.jpg",
  "/banners/rot-event-1.jpg",
  "/banners/rot-cloth-1.jpg",
  "/banners/rot-hero-2.jpg",
  "/banners/rot-luxury-2.jpg",
  "/banners/rot-event-2.jpg",
];

export function Collection100({
  sort = "new",
}: {
  sort?: ProductSort;
}) {
  const banner = pickRotating(collectionBannerImages, 3);
  const list = sortProducts(getCollection100(), sort);

  return (
    <section className="collection-100" id="collection-100" aria-label="Briq 100 컬렉션">
      <div className="collection-100__banner">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          className="collection-100__banner-img"
          src={banner}
          alt=""
          aria-hidden
          loading="lazy"
          decoding="async"
        />
        <div className="collection-100__banner-shade" aria-hidden />
        <div className="collection-100__banner-content">
          <p className="collection-100__eyebrow">Briq Edit</p>
          <h2 className="collection-100__title">100 Collection</h2>
          <p className="collection-100__lead">
            맞춤형 필터를 통해 Briq의 100가지 감각적인
            <br className="br-mobile" /> 컬렉션을 더 깊이 있게 만나보세요.
          </p>
          <p className="collection-100__hint">
            Briq의 모든 컬렉션이 궁금하시다면
            <br className="br-mobile" /> 상단{" "}
            <Link href="/shop">[Shop - 전체상품]</Link>을 클릭해 보세요.
          </p>
        </div>
      </div>

      <div className="section collection-100__body">
        <div className="collection-100__toolbar">
          <div className="collection-100__sort" role="list" aria-label="상품 정렬">
            {PRODUCT_SORTS.map((option) => (
              <Link
                key={option.id}
                href={`/?csort=${option.id}#collection-100`}
                scroll={false}
                role="listitem"
                className={`collection-100__sort-btn ${
                  sort === option.id ? "is-active" : ""
                }`}
              >
                {option.label}
              </Link>
            ))}
          </div>
        </div>

        {sort === "orders" ? (
          <CollectionOrdersGrid key={sort} products={list} />
        ) : (
          <CollectionReveal key={sort} products={list} />
        )}
      </div>
    </section>
  );
}
