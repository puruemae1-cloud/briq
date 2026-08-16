import Link from "next/link";
import { BestItems } from "@/components/BestItems";
import { BannerImage } from "@/components/BannerImage";
import {
  Collection100,
} from "@/components/Collection100";
import { LookBannerBlock } from "@/components/LookBanner";
import { ProductCard } from "@/components/ProductCard";
import { heroImages, homeLookBanners, pickRotating, resolveHomeRailLinks } from "@/data/home-banners";
import { getProductsByCategory } from "@/data/products";
import { bannerFocalForSrc } from "@/lib/banner-focal";
import { getHomepageRailProducts } from "@/lib/product-sort";

export default async function HomePage() {
  const heroImage = pickRotating(heroImages);
  const heroFocal = bannerFocalForSrc(heroImage, "center 40%");

  return (
    <>
      <section className="hero">
        <div className="hero__stage">
          <BannerImage
            className="hero__bg"
            src={heroImage}
            alt="Briq 명품의류·명품직구 메인 비주얼"
            fetchPriority="high"
            loading="eager"
            style={heroFocal ? { objectPosition: heroFocal } : undefined}
          />
          <div className="hero__shade" aria-hidden />
          <div className="hero__content">
            <h1 className="hero__brand">London to Your Door</h1>
            <p className="hero__headline">British Boutique. Unique edit.</p>
            <p className="hero__support">
              영국 현지 기준의 까다로운 셀렉션,
              <br className="br-mobile" /> 오직 당신만을 위한 직배송.
            </p>
          </div>
        </div>
      </section>

      <section className="seo-intro" aria-label="Briq 소개">
        <div className="seo-intro__inner">
          <h2 className="seo-intro__title">
            명품의류 · 명품직구 · 명품구매대행
          </h2>
          <p className="seo-intro__copy">
            Briq(브릭)은 샤넬·구찌·버버리·아크테릭스 등 유명 명품브랜드를
            영국 부티크 기준으로 큐레이션하는 셀렉트숍입니다. 프라다·에르메스
            등 하이엔드 명품을 찾는 고객에게도 투명한 직구·구매대행형 쇼핑을
            제공합니다. 항공 배송비와 관·부가세가 포함된 가격으로 국내
            직배송까지 이어집니다.
          </p>
          <nav className="seo-intro__links" aria-label="가이드">
            <Link href="/guide/luxury-direct">명품직구 가이드</Link>
            <Link href="/guide/buying-agency">명품구매대행 안내</Link>
            <Link href="/guide/luxury-apparel">명품의류</Link>
            <Link href="/brands">브랜드</Link>
          </nav>
        </div>
      </section>

      <div className="lookbook" aria-label="Briq lookbook">
        {homeLookBanners.map((banner, i) => {
          const products = banner.categoryId
            ? getHomepageRailProducts(
                getProductsByCategory(banner.categoryId),
                4,
              )
            : [];
          const railLinks = resolveHomeRailLinks(banner);

          return (
            <div key={banner.id} className="lookbook__block">
              <LookBannerBlock banner={banner} rotationOffset={i} />
              {products.length > 0 ? (
                <section className="section lookbook__rail lookbook__rail--bleed">
                  <div className="lookbook__rail-inner">
                    <div className="section__head">
                      <div>
                        <h2>{banner.titleKo}</h2>
                        {railLinks.length > 0 ? (
                          <nav
                            className="section__brands"
                            aria-label={`${banner.titleKo} 브랜드`}
                          >
                            {railLinks.map((link, idx) => (
                              <span key={link.href} className="section__brands-item">
                                <Link href={link.href}>{link.label}</Link>
                                {idx < railLinks.length - 1 ? (
                                  <span className="section__brands-sep" aria-hidden>
                                    ·
                                  </span>
                                ) : null}
                              </span>
                            ))}
                          </nav>
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

      <Collection100 />
    </>
  );
}
