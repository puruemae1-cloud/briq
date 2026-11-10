import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { BestItems } from "@/components/BestItems";
import { BannerImage } from "@/components/BannerImage";
import {
  Collection100,
} from "@/components/Collection100";
import { FlannelsHomeBanner } from "@/components/FlannelsHomeBanner";
import { LookBannerBlock } from "@/components/LookBanner";
import { ProductCard } from "@/components/ProductCard";
import { heroImage, homeLookBanners, resolveHomeRailLinks } from "@/data/home-banners";
import { bannerFocalForSrc } from "@/lib/banner-focal";
import { BrandChipLink, isBrandChipNavId } from "@/components/BrandChip";
import { BrandChipRail } from "@/components/BrandChipRail";
import { getHomepageData } from "@/lib/homepage-feed";
import { DEFAULT_DESCRIPTION, DEFAULT_TITLE, getSiteUrl } from "@/lib/site";
import { DEFAULT_OG_IMAGE } from "@/lib/seo-metadata";

export const metadata: Metadata = {
  alternates: { canonical: getSiteUrl() },
  openGraph: {
    title: DEFAULT_TITLE,
    description: DEFAULT_DESCRIPTION,
    url: getSiteUrl(),
    images: [DEFAULT_OG_IMAGE],
  },
};

/** Stream below-the-fold 100 Collection after hero + lookbook rails. */
async function DeferredCollection100() {
  await Promise.resolve();
  return <Collection100 />;
}

export default async function HomePage() {
  const heroFocal = bannerFocalForSrc(heroImage, "50% 50%");

  // Cross-rail brand exclusivity: a brand on 시그니처 cannot also fill 슈즈/악세서리 등.
  // Watches rail is locked to Christopher Ward New Releases (+ HOME_FEATURED).
  const { rails: railProducts, flannels: flannelsProducts = [], deployKey } =
    await getHomepageData();

  return (
    <>
      <section className="hero hero--fullframe">
        <div className="hero__stage">
          <BannerImage
            className="hero__bg"
            src={heroImage}
            alt="Briq 메인 비주얼"
            fetchPriority="high"
            loading="eager"
            style={heroFocal ? { objectPosition: heroFocal } : undefined}
          />
          <div className="hero__shade" aria-hidden />
          <div className="hero__content">
            {/* Korean H1 for Naver indexing; English line kept as brand atmosphere. */}
            <h1 className="hero__brand">
              Briq{" "}
              <span className="hero__brand-line">브릭</span>
            </h1>
            <p className="hero__headline">London to Your Door · British Boutique</p>
            <p className="hero__support">
              영국 현지 기준 명품직구·구매대행,
              <br className="br-mobile" /> 관부가세 포함 국내 직배송.
            </p>
          </div>
        </div>
      </section>

      <div
        className="lookbook"
        aria-label="Briq lookbook"
        data-cards-deploy={deployKey ?? "none"}
      >
        {homeLookBanners.map((banner) => {
          const products = banner.categoryId
            ? railProducts[banner.id] || []
            : [];
          const railLinks = resolveHomeRailLinks(banner);

          return (
            <div key={banner.id} className="lookbook__block">
              <LookBannerBlock banner={banner} />
              {products.length > 0 ? (
                <section className="section lookbook__rail lookbook__rail--bleed">
                  <div className="lookbook__rail-inner">
                    <div className="section__head">
                      <div>
                        <h2>{banner.titleKo}</h2>
                        {railLinks.length > 0 ? (
                          (() => {
                            const useLogos = railLinks.some((l) =>
                              isBrandChipNavId(l.id || ""),
                            );
                            return (
                              <BrandChipRail
                                className={`section__brands${
                                  useLogos ? " section__brands--logos" : ""
                                }`}
                                aria-label={`${banner.titleKo} 브랜드`}
                              >
                                {railLinks.map((link, idx) => {
                                  const isBrand = isBrandChipNavId(
                                    link.id || "",
                                  );
                                  if (useLogos && isBrand) {
                                    return (
                                      <BrandChipLink
                                        key={link.href}
                                        href={link.href}
                                        navId={link.id || ""}
                                        label={link.label}
                                      />
                                    );
                                  }
                                  if (useLogos) {
                                    return (
                                      <Link
                                        key={link.href}
                                        href={link.href}
                                        className="chip chip--brand"
                                      >
                                        <span className="chip__brand-label">
                                          {link.label}
                                        </span>
                                      </Link>
                                    );
                                  }
                                  return (
                                    <span
                                      key={link.href}
                                      className="section__brands-item"
                                    >
                                      <Link href={link.href}>{link.label}</Link>
                                      {idx < railLinks.length - 1 ? (
                                        <span
                                          className="section__brands-sep"
                                          aria-hidden
                                        >
                                          ·
                                        </span>
                                      ) : null}
                                    </span>
                                  );
                                })}
                              </BrandChipRail>
                            );
                          })()
                        ) : null}
                      </div>
                      <Link href={banner.href}>전체 보기</Link>
                    </div>
                    <div className="product-grid product-grid--lookbook">
                      {products.map((p) => (
                        <ProductCard key={p.id} product={p} />
                      ))}
                    </div>
                  </div>
                </section>
              ) : null}

              {banner.id === "luxury" ? (
                <>
                  <FlannelsHomeBanner />
                  {flannelsProducts.length > 0 ? (
                    <section className="section lookbook__rail lookbook__rail--bleed">
                      <div className="lookbook__rail-inner">
                        <div className="section__head">
                          <div>
                            <h2>FLANNELS</h2>
                          </div>
                          <Link href="/shop?category=luxury&sub=flannels">
                            전체 보기
                          </Link>
                        </div>
                        <div className="product-grid product-grid--lookbook">
                          {flannelsProducts.map((p) => (
                            <ProductCard key={p.id} product={p} />
                          ))}
                        </div>
                      </div>
                    </section>
                  ) : null}
                </>
              ) : null}

              {banner.id === "watches" ? (
                <section className="manifesto" aria-label="Briq manifesto">
                  <div className="manifesto__inner">
                    <p className="manifesto__mark">Briq</p>
                    <div className="manifesto__rule" aria-hidden />
                    <h2 className="manifesto__title">
                      영국의 모든 감각을
                      <br />
                      하나의 공간에.
                    </h2>
                    <p className="manifesto__copy">
                      그동안 유일무이했던 깊고 넓은 라인업을
                      <br />
                      오직 Briq에서 펼쳐냅니다.
                    </p>
                    <div
                      className="manifesto__rule manifesto__rule--short"
                      aria-hidden
                    />
                  </div>
                </section>
              ) : null}

              {banner.id === "shoes" ? (
                <section className="pricing-banner" aria-label="All-inclusive pricing">
                  <div className="pricing-banner__inner">
                    <p className="pricing-banner__mark">Transparency</p>
                    <div className="pricing-banner__rule" aria-hidden />
                    <h2 className="pricing-banner__title">
                      All-Inclusive Pricing,
                      <br />
                      No Hidden Fees.
                    </h2>
                    <p className="pricing-banner__copy">
                      Briq에서 안내하는 가격은 해외 항공 배송비와
                      <br className="br-mobile" /> 관·부가세가
                      <br className="br-desktop" /> 모두 포함된 최종 확정 금액입니다.
                    </p>
                    <div
                      className="pricing-banner__rule pricing-banner__rule--short"
                      aria-hidden
                    />
                  </div>
                </section>
              ) : null}
            </div>
          );
        })}
      </div>

      <BestItems />

      <Suspense fallback={<div className="collection-100-pending" aria-hidden />}>
        <DeferredCollection100 />
      </Suspense>
    </>
  );
}
