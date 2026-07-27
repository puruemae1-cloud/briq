/**
 * CSS-only sports carousel — works without client JavaScript
 * (secret/incognito + LAN IP where React hydration often fails).
 */
export type CarouselSlide = {
  id: string;
  labelKo: string;
  href: string;
  image: string;
  focal?: string;
};

export function BannerCarousel({
  slides,
  name = "sports-banner",
}: {
  slides: CarouselSlide[];
  name?: string;
}) {
  if (slides.length === 0) return null;

  return (
    <div
      className="banner-carousel"
      data-slides={slides.length}
      style={{ ["--slide-count" as string]: String(slides.length) }}
    >
      {slides.map((slide, i) => (
        <input
          key={`radio-${slide.id}`}
          type="radio"
          name={name}
          id={`${name}-${i}`}
          className="banner-radio"
          aria-label={slide.labelKo}
        />
      ))}

      <div className="banner-carousel__viewport">
        <div className="banner-carousel__track">
          {slides.map((slide) => (
            <a
              key={slide.id}
              href={slide.href}
              className="banner-slide"
              aria-label={`${slide.labelKo} 카테고리로 이동`}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={slide.image}
                alt={slide.labelKo}
                style={slide.focal ? { objectPosition: slide.focal } : undefined}
                loading="eager"
                draggable={false}
              />
              <span className="banner-slide__label">{slide.labelKo}</span>
            </a>
          ))}
        </div>
      </div>

      <div className="banner-carousel__dots" aria-label="스포츠 배너">
        {slides.map((slide, i) => (
          <label
            key={`dot-${slide.id}`}
            htmlFor={`${name}-${i}`}
            className="banner-dot"
            title={slide.labelKo}
          >
            <span className="sr-only">{slide.labelKo}</span>
          </label>
        ))}
      </div>
    </div>
  );
}
