import Link from "next/link";
import { BannerImage } from "@/components/BannerImage";
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
        <BannerImage
          className="collection-100__banner-img"
          src={banner}
          alt=""
          aria-hidden
          loading="lazy"
        />
        <div className="collection-100__banner-shade" aria-hidden />
        <div className="collection-100__banner-content">
          <p className="collection-100__eyebrow">Briq Edit</p>
          <h2 className="collection-100__title">
            가장 사랑받는 베스트셀러부터
            <br className="br-mobile" /> 플래그십 모델까지
          </h2>
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
