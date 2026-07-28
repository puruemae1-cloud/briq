import Link from "next/link";
import { BannerImage } from "@/components/BannerImage";
import { ProductCard } from "@/components/ProductCard";
import { CollectionOrdersGrid } from "@/components/CollectionOrdersGrid";
import {
  categoryLabel,
  findCategory,
  findNavPath,
  findSubcategory,
  navCategories,
  type NavChild,
} from "@/data/categories";
import { getProductsByCategory } from "@/data/products";
import { pickRotating } from "@/data/home-banners";
import { pickShopHero } from "@/data/shop-heroes";
import { searchProducts } from "@/lib/product-search";
import {
  PRODUCT_SORTS,
  buildShopHref,
  parseProductSort,
  sortProducts,
} from "@/lib/product-sort";

const NEW_ARRIVALS_HERO_IMAGES = [
  "/banners/rot-event-1.jpg",
  "/banners/rot-event-2.jpg",
  "/banners/rot-event-3.jpg",
];

const ALL_PRODUCTS_HERO_IMAGES = [
  "/banners/rot-hero-1.jpg",
  "/banners/rot-hero-2.jpg",
  "/banners/rot-hero-3.jpg",
  "/banners/rot-hero-4.jpg",
];

type Props = {
  searchParams: Promise<{
    category?: string;
    sub?: string;
    q?: string;
    sort?: string;
  }>;
};

function chipClass(node: NavChild, sub: string | undefined, pathIds: Set<string>) {
  const active = sub === node.id || pathIds.has(node.id);
  const clearance = node.id === "cw-clearance" ? " chip--clearance" : "";
  return `chip chip--sub chip--nested${clearance}${active ? " is-active" : ""}`;
}

export default async function ShopPage({ searchParams }: Props) {
  const params = await searchParams;
  const category = params.category ?? "all";
  const sub = params.sub;
  const sort = parseProductSort(params.sort);

  /** New Arrivals = all products, newest first (from 신상 보러가기). */
  const isNewArrivals = Boolean(
    params.sort === "new" &&
      !params.q?.trim() &&
      category === "all" &&
      !sub,
  );

  let list = getProductsByCategory(category, sub);
  list = searchProducts(list, params.q);
  list = sortProducts(list, sort);

  const current = category !== "all" ? findCategory(category) : undefined;
  const subNode = sub && current ? findSubcategory(category, sub) : undefined;
  const baseTitle = isNewArrivals
    ? "New Arrivals"
    : subNode
      ? `${current!.labelKo} · ${subNode.labelKo}`
      : categoryLabel(category);
  const title = params.q?.trim()
    ? `‘${params.q.trim()}’ 검색 결과`
    : baseTitle;

  const openPath =
    current?.children && sub
      ? findNavPath(current.children, sub)
      : undefined;
  const pathIds = new Set((openPath ?? []).map((n) => n.id));
  const nestedRows: NavChild[][] = [];
  if (openPath) {
    for (const node of openPath) {
      if (node.children?.length) nestedRows.push(node.children);
    }
  }

  const isAllCatalogue =
    category === "all" && !sub && !params.q?.trim() && !isNewArrivals;
  const heroImage = isNewArrivals
    ? pickRotating(NEW_ARRIVALS_HERO_IMAGES, 1)
    : isAllCatalogue
      ? pickRotating(ALL_PRODUCTS_HERO_IMAGES, 0)
      : pickShopHero(category, sub);
  const heroEyebrow = isNewArrivals
    ? "New Season Edit"
    : isAllCatalogue
      ? "Briq Catalogue"
      : (subNode?.labelKo ?? current?.labelKo ?? "Shop");
  const heroTitle = isNewArrivals ? "New Arrivals" : title;
  const heroSupport = isNewArrivals
    ? "지금 영국에서 가장 핫한 신상 · 최신등록순"
    : isAllCatalogue
      ? "시그니처부터 입문까지 — 영국 셀렉션 전체"
      : null;

  const sortBase = {
    category,
    sub,
    q: params.q,
  };

  return (
    <>
      <section className="shop-hero" aria-label={heroTitle}>
        <BannerImage
          className="shop-hero__img"
          src={heroImage}
          alt=""
          aria-hidden
          loading="eager"
          fetchPriority="high"
        />
        <div className="shop-hero__shade" aria-hidden />
        <div className="shop-hero__content">
          <p className="shop-hero__eyebrow">{heroEyebrow}</p>
          <h1 className="shop-hero__title">{heroTitle}</h1>
          {heroSupport ? (
            <p className="shop-hero__support">{heroSupport}</p>
          ) : null}
        </div>
      </section>

      <section className="section shop-browse">
        <div className="section__head">
          <div>
            <h2>{title}</h2>
          </div>
        </div>

        <div className="shop-browse__layout">
          <div className="shop-browse__main">
            <div className="category-row">
              <Link
                href="/shop"
                scroll={false}
                className={`chip ${category === "all" && !sub ? "is-active" : ""}`}
              >
                Shop (전체상품)
              </Link>
              {navCategories.map((c) => (
                <Link
                  key={c.id}
                  href={buildShopHref({
                    category: c.id,
                    sort,
                  })}
                  scroll={false}
                  className={`chip ${category === c.id && !sub ? "is-active" : ""}`}
                >
                  {c.labelKo}
                </Link>
              ))}
            </div>

            {current?.children ? (
              <div className="category-row category-row--sub">
                {current.children.map((child) => (
                  <Link
                    key={child.id}
                    href={buildShopHref({
                      category,
                      sub: child.id,
                      sort,
                    })}
                    scroll={false}
                    className={`chip chip--sub ${
                      sub === child.id || pathIds.has(child.id) ? "is-active" : ""
                    }`}
                  >
                    {child.labelKo}
                  </Link>
                ))}
              </div>
            ) : null}

            {nestedRows.map((row, rowIndex) => (
              <div
                key={`nested-${rowIndex}-${row.map((n) => n.id).join("-")}`}
                className="category-row category-row--sub category-row--nested"
              >
                {row.map((nested) => (
                  <Link
                    key={nested.id}
                    href={buildShopHref({
                      category,
                      sub: nested.id,
                      sort,
                    })}
                    scroll={false}
                    className={chipClass(nested, sub, pathIds)}
                  >
                    {nested.labelKo}
                  </Link>
                ))}
              </div>
            ))}

            {sort === "orders" ? (
              <CollectionOrdersGrid products={list} />
            ) : (
              <div className="product-grid">
                {list.map((p) => (
                  <ProductCard key={p.id} product={p} />
                ))}
              </div>
            )}
          </div>

          <aside className="shop-browse__aside" aria-label="상품 정렬 필터">
            <p className="shop-browse__aside-title">정렬</p>
            <div className="shop-browse__sort" role="list">
              {PRODUCT_SORTS.map((option) => (
                <Link
                  key={option.id}
                  href={buildShopHref({ ...sortBase, sort: option.id })}
                  scroll={false}
                  role="listitem"
                  className={`shop-browse__sort-btn ${
                    sort === option.id ? "is-active" : ""
                  }`}
                >
                  {option.label}
                </Link>
              ))}
            </div>
          </aside>
        </div>
      </section>
    </>
  );
}
