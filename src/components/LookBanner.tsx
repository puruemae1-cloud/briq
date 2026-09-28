import type { CSSProperties } from "react";
import { BannerCarousel } from "@/components/BannerCarousel";
import { BannerImage } from "@/components/BannerImage";
import { ShopFastLink } from "@/components/ShopFastLink";
import { pickBanner, type LookBanner } from "@/data/home-banners";
import { bannerFocalForSrc } from "@/lib/banner-focal";
import { mediaUrl } from "@/lib/product-image";

export function LookBannerBlock({ banner }: { banner: LookBanner }) {
  const align = banner.align ?? "left";
  const image = pickBanner(banner.images);
  const focal = bannerFocalForSrc(image, banner.focal);
  const slides = banner.slides?.map((slide) => {
    const slideImage = pickBanner(slide.images);
    return {
      id: slide.id,
      labelKo: slide.labelKo,
      href: slide.href,
      image: slideImage,
      focal: bannerFocalForSrc(slideImage, slide.focal),
      video: slide.videoSrc ? mediaUrl(slide.videoSrc) : undefined,
    };
  });

  const titleBlock = (
    <>
      <p className="look-banner__eyebrow">{banner.eyebrow}</p>
      <h2 className="look-banner__title">
        <span className="look-banner__title-en">{banner.title}</span>
        <span className="look-banner__title-ko">{banner.titleKo}</span>
      </h2>
      <p className="look-banner__support">{banner.support}</p>
    </>
  );

  return (
    <section
      className={`look-banner look-banner--${banner.id} look-banner--${align}${slides ? " look-banner--carousel" : ""}${banner.fullFrame ? " look-banner--fullframe" : ""}`}
      style={
        banner.fullFrame && banner.aspectRatio
          ? ({
              // Desktop only — mobile overrides via CSS (avoid inline aspect clipping CTAs).
              "--look-banner-aspect": banner.aspectRatio,
            } as CSSProperties)
          : undefined
      }
      aria-label={`${banner.titleKo} ${banner.eyebrow}`}
    >
      {slides ? (
        <>
          <BannerCarousel slides={slides} />
          <div className="look-banner__content">
            {titleBlock}
            <ShopFastLink href={banner.href} className="look-banner__cta">
              {banner.cta}
            </ShopFastLink>
          </div>
        </>
      ) : (
        <ShopFastLink
          href={banner.href}
          className="look-banner__hit"
          aria-label={banner.cta}
        >
          <div className="look-banner__media" aria-hidden>
            <BannerImage
              className="look-banner__img"
              src={image}
              alt=""
              style={focal ? { objectPosition: focal } : undefined}
              loading="lazy"
            />
            <div className="look-banner__shade" />
          </div>
          <div className="look-banner__content">
            {titleBlock}
            <span className="look-banner__cta">{banner.cta}</span>
          </div>
        </ShopFastLink>
      )}
    </section>
  );
}
