import Link from "next/link";
import { BannerCarousel } from "@/components/BannerCarousel";
import { pickRotating, type LookBanner } from "@/data/home-banners";

export function LookBannerBlock({
  banner,
  rotationOffset = 0,
}: {
  banner: LookBanner;
  rotationOffset?: number;
}) {
  const align = banner.align ?? "left";
  const image = pickRotating(banner.images, rotationOffset);
  const slides = banner.slides?.map((slide, i) => ({
    id: slide.id,
    labelKo: slide.labelKo,
    href: slide.href,
    image: pickRotating(slide.images, rotationOffset + i),
    focal: slide.focal,
  }));

  return (
    <section
      className={`look-banner look-banner--${align}${slides ? " look-banner--carousel" : ""}`}
      aria-label={`${banner.titleKo} ${banner.eyebrow}`}
    >
      {slides ? (
        <BannerCarousel slides={slides} />
      ) : (
        <div className="look-banner__media" aria-hidden>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            className="look-banner__img"
            src={image}
            alt=""
            style={banner.focal ? { objectPosition: banner.focal } : undefined}
            loading="lazy"
          />
          <div className="look-banner__shade" />
        </div>
      )}

      <div className="look-banner__content">
        <p className="look-banner__eyebrow">{banner.eyebrow}</p>
        <h2 className="look-banner__title">
          <span className="look-banner__title-en">{banner.title}</span>
          <span className="look-banner__title-ko">{banner.titleKo}</span>
        </h2>
        <p className="look-banner__support">{banner.support}</p>
        <Link href={banner.href} className="look-banner__cta">
          {banner.cta}
        </Link>
      </div>
    </section>
  );
}
