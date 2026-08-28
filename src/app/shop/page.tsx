import Link from "next/link";
import type { Metadata } from "next";
import { BannerImage } from "@/components/BannerImage";
import { BrandWordmark } from "@/components/BrandWordmark";
import { CollectionOrdersGrid } from "@/components/CollectionOrdersGrid";
import { ShareLinkButton } from "@/components/ShareLinkButton";
import { ShopProductGrid } from "@/components/ShopProductGrid";
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
import { bannerFocalForSrc } from "@/lib/banner-focal";
import { searchProducts } from "@/lib/product-search";
import { resolveShopBrand } from "@/lib/shop-brand";
import { getSiteUrl } from "@/lib/site";
import { sortNavChildrenByBrandOrder } from "@/lib/brand-nav-order";
import {
  NEW_ARRIVALS_LIMIT,
  PRODUCT_SORTS,
  buildShopHref,
  getNewArrivalsProducts,
  parseProductSort,
  preferGgApparelFirst,
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

const LOAD_MORE_PAGE_SIZE = 24;

export async function generateMetadata({
  searchParams,
}: Props): Promise<Metadata> {
  const params = await searchParams;
  const category = params.category ?? "all";
  const sub = params.sub;
  const brand = resolveShopBrand(category, sub);
  const current = category !== "all" ? findCategory(category) : undefined;
  const subNode = sub && current ? findSubcategory(category, sub) : undefined;
  const isNew =
    params.sort === "new" && !params.q?.trim() && category === "all" && !sub;

  let title: string;
  let description: string;
  if (params.q?.trim()) {
    title = `‘${params.q.trim()}’ 검색 | 명품직구 Briq`;
    description = `${params.q.trim()} 검색 결과 — Briq 영국 명품의류·명품직구·명품구매대행.`;
  } else if (isNew) {
    title = "New Arrivals 신상품 | 명품직구 Briq";
    description =
      "Briq 신상품 — 브랜드 주간 업데이트로 새로 등록된 최신 100개. 영국 명품직구·구매대행.";
  } else if (brand) {
    title = `${brand.nameKo} ${brand.nameEn} | 명품직구 Briq`;
    description = `${brand.nameKo}(${brand.nameEn}) 셀렉션 — 명품의류·명품직구·명품구매대행 Briq.`;
  } else if (subNode && current) {
    title = `${current.labelKo} · ${subNode.labelKo} | Briq`;
    description = `${current.labelKo} ${subNode.labelKo} — 영국 명품 셀렉트숍 Briq 명품직구.`;
  } else if (current) {
    title = `${current.labelKo} | 명품직구 Briq`;
    description = `${current.labelKo} 명품 쇼핑 — 샤넬·구찌·버버리 등 Briq 영국 직구.`;
  } else {
    title = "Shop 전체상품 | 명품의류·명품직구 Briq";
    description =
      "Briq 전체 카탈로그 — 명품의류·가방·시계·악세서리 명품직구·구매대행.";
  }

  const canonicalPath = buildShopHref({
    category: category === "all" ? undefined : category,
    sub,
    q: params.q,
    sort: params.sort === "new" ? "new" : undefined,
  });

  return {
    title,
    description,
    alternates: { canonical: `${getSiteUrl()}${canonicalPath}` },
    openGraph: {
      title,
      description,
      url: `${getSiteUrl()}${canonicalPath}`,
      locale: "ko_KR",
      type: "website",
    },
  };
}

function chipClass(node: NavChild, sub: string | undefined, pathIds: Set<string>) {
  const active = sub === node.id || pathIds.has(node.id);
  const clearance =
    node.id === "cw-clearance" || node.id === "gg-sale" ? " chip--clearance" : "";
  return `chip chip--sub chip--nested${clearance}${active ? " is-active" : ""}`;
}

export default async function ShopPage({ searchParams }: Props) {
  const params = await searchParams;
  const category = params.category ?? "all";
  const sub = params.sub;
  const sort = parseProductSort(params.sort);

  /** New Arrivals = newest 100 only (신상 보러가기); full catalogue stays on /shop. */
  const isNewArrivals = Boolean(
    params.sort === "new" &&
      !params.q?.trim() &&
      category === "all" &&
      !sub,
  );

  let list = getProductsByCategory(category, sub);
  list = searchProducts(list, params.q);
  if (isNewArrivals) {
    list = getNewArrivalsProducts(list);
  } else {
    list = sortProducts(list, sort);
  }
  // Men/Women include unisex accessories — keep apparel first like the official PLP.
  if (sub === "gg-men" || sub === "gg-women") {
    list = preferGgApparelFirst(list);
  }

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
  const shopBrand = !isNewArrivals && !isAllCatalogue
    ? resolveShopBrand(category, sub)
    : null;
  const heroImage = isNewArrivals
    ? pickRotating(NEW_ARRIVALS_HERO_IMAGES, 1)
    : isAllCatalogue
      ? pickRotating(ALL_PRODUCTS_HERO_IMAGES, 0)
      : pickShopHero(category, sub);
  const heroEyebrow = isNewArrivals
    ? "New Season Edit"
    : isAllCatalogue
      ? "Briq Catalogue"
      : shopBrand
        ? shopBrand.nameEn
        : (subNode?.labelKo ?? current?.labelKo ?? "Shop");
  const heroTitle = isNewArrivals ? "New Arrivals" : title;
  const heroSupport = isNewArrivals
    ? `브랜드 주간 업데이트 신상 · 최대 ${NEW_ARRIVALS_LIMIT}개`
    : isAllCatalogue
      ? "시그니처부터 입문까지 — 영국 셀렉션 전체"
      : shopBrand
        ? `${shopBrand.nameKo} · Briq edit`
        : null;

  const sortBase = {
    category,
    sub,
    q: params.q,
  };

  return (
    <>
      <section
        className={`shop-hero${shopBrand ? " shop-hero--brand" : ""}`}
        aria-label={heroTitle}
      >
        <BannerImage
          className="shop-hero__img"
          src={heroImage}
          alt=""
          aria-hidden
          loading="eager"
          fetchPriority="high"
          style={{
            objectPosition: bannerFocalForSrc(heroImage, "center 45%"),
          }}
        />
        <div className="shop-hero__shade" aria-hidden />
        <div className="shop-hero__content">
          {shopBrand ? (
            <BrandWordmark
              nameEn={shopBrand.nameEn}
              className="shop-hero__logo"
            />
          ) : (
            <p className="shop-hero__eyebrow">{heroEyebrow}</p>
          )}
          <div className="shop-hero__title-row">
            <h1 className="shop-hero__title">{heroTitle}</h1>
            <ShareLinkButton
              title={`Briq · ${heroTitle}`}
              url={buildShopHref({
                category,
                sub,
                q: params.q,
                sort: isNewArrivals ? "new" : sort,
              })}
              compact
              className="shop-hero__share"
            />
          </div>
          {heroSupport ? (
            <p className="shop-hero__support">{heroSupport}</p>
          ) : null}
        </div>
      </section>

      <section className="section shop-browse">
        <div className="section__head">
          <div className="section__head-title">
            <h2>{title}</h2>
            <ShareLinkButton
              title={`Briq · ${title}`}
              url={buildShopHref({
                category,
                sub,
                q: params.q,
                sort: isNewArrivals ? "new" : sort,
              })}
              compact
              className="shop-browse__share"
            />
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
                {sortNavChildrenByBrandOrder(current.children).map((child) => (
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

            {nestedRows.map((row, rowIndex) => {
              const parent = openPath?.[rowIndex];
              return (
                <div
                  key={`nested-${rowIndex}-${row.map((n) => n.id).join("-")}`}
                  className="category-nest"
                >
                  {parent ? (
                    <p className="category-nest__label">
                      <span className="category-nest__brand">
                        {parent.labelKo}
                      </span>
                      <span className="category-nest__rule" aria-hidden />
                      <span className="category-nest__hint">하위 컬렉션</span>
                    </p>
                  ) : null}
                  <div className="category-row category-row--sub category-row--nested category-row--nest-chips">
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
                </div>
              );
            })}

            <div className="shop-browse__controls" aria-label="상품 정렬 필터">
              {sort !== "orders" ? (
                <p className="shop-browse__count">
                  총 {list.length.toLocaleString()}개 상품
                </p>
              ) : (
                <span className="shop-browse__count" aria-hidden />
              )}
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
            </div>

            {sort === "orders" ? (
              <CollectionOrdersGrid products={list} />
            ) : (
              <ShopProductGrid
                key={`${category}-${sub ?? ""}-${sort}-${params.q ?? ""}`}
                products={list}
                pageSize={LOAD_MORE_PAGE_SIZE}
              />
            )}
          </div>
        </div>
      </section>
    </>
  );
}
