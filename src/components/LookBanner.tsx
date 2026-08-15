import Link from "next/link";
import { BannerCarousel } from "@/components/BannerCarousel";
import { BannerImage } from "@/components/BannerImage";
import { pickRotating, type LookBanner } from "@/data/home-banners";
import { bannerFocalForSrc } from "@/lib/banner-focal";

export function LookBannerBlock({
  banner,
  rotationOffset = 0,
}: {
  banner: LookBanner;
  rotationOffset?: number;
}) {
  const align = banner.align ?? "left";
  const image = pickRotating(banner.images, rotationOffset);
  const focal = bannerFocalForSrc(image, banner.focal);
  const slides = banner.slides?.map((slide, i) => {
    const slideImage = pickRotating(slide.images, rotationOffset + i);
    return {
      id: slide.id,
      labelKo: slide.labelKo,
      href: slide.href,
      image: slideImage,
      focal: bannerFocalForSrc(slideImage, slide.focal),
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
      className={`look-banner look-banner--${align}${slides ? " look-banner--carousel" : ""}`}
      aria-label={`${banner.titleKo} ${banner.eyebrow}`}
    >
      {slides ? (
        <>
          <BannerCarousel slides={slides} />
          <div className="look-banner__content">
            {titleBlock}
            <Link href={banner.href} className="look-banner__cta">
              {banner.cta}
            </Link>
          </div>
        </>
      ) : (
        <Link
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
        </Link>
      )}
    </section>
  );
}
