"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { BannerImage } from "@/components/BannerImage";

/**
 * Swipeable sports carousel with scroll-snap.
 * Autoplay: desktop (fine pointer) only — mobile is finger swipe only.
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
}: {
  slides: CarouselSlide[];
  name?: string;
}) {
  const viewportRef = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState(0);
  const pausedUntil = useRef(0);
  const activeRef = useRef(0);

  const pause = useCallback(() => {
    pausedUntil.current = Date.now() + 10000;
  }, []);

  const goTo = useCallback((index: number, behavior: ScrollBehavior = "smooth") => {
    const el = viewportRef.current;
    if (!el) return;
    const w = el.clientWidth;
    if (!w) return;
    el.scrollTo({ left: w * index, behavior });
  }, []);

  useEffect(() => {
    activeRef.current = active;
  }, [active]);

  useEffect(() => {
    const el = viewportRef.current;
    if (!el) return;

    const sync = () => {
      const w = el.clientWidth;
      if (!w) return;
      const i = Math.round(el.scrollLeft / w);
      const next = Math.max(0, Math.min(slides.length - 1, i));
      if (next === activeRef.current) return;
      activeRef.current = next;
      setActive(next);
    };

    const onScrollEnd = () => sync();
    el.addEventListener("scrollend", onScrollEnd);

    // Continuous scroll sync only on desktop — mobile keeps page scroll smooth
    const fine = window.matchMedia("(hover: hover) and (pointer: fine)");
    let raf = 0;
    const onScroll = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(sync);
    };
    if (fine.matches) {
      el.addEventListener("scroll", onScroll, { passive: true });
    }

    return () => {
      cancelAnimationFrame(raf);
      el.removeEventListener("scrollend", onScrollEnd);
      el.removeEventListener("scroll", onScroll);
    };
  }, [slides.length]);

  useEffect(() => {
    if (slides.length < 2) return;
    const fine = window.matchMedia("(hover: hover) and (pointer: fine)");
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (!fine.matches || reduce.matches) return;

    const id = window.setInterval(() => {
      if (Date.now() < pausedUntil.current) return;
      const el = viewportRef.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      if (rect.bottom < 0 || rect.top > window.innerHeight) return;

      const next = (activeRef.current + 1) % slides.length;
      goTo(next);
    }, 5000);

    return () => clearInterval(id);
  }, [slides.length, goTo]);

  /**
   * PC: overflow-x carousels trap the mouse wheel. Forward vertical wheel
   * to the page so scrolling works while the pointer is over Weekend Movement.
   */
  useEffect(() => {
    const el = viewportRef.current;
    if (!el) return;
    const fine = window.matchMedia("(hover: hover) and (pointer: fine)");
    if (!fine.matches) return;

    const onWheel = (e: WheelEvent) => {
      pause();
      if (Math.abs(e.deltaY) < Math.abs(e.deltaX)) return;
      e.preventDefault();
      window.scrollBy({ top: e.deltaY, left: 0, behavior: "auto" });
    };

    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, [pause]);

  if (slides.length === 0) return null;

  return (
    <div
      className="banner-carousel"
      data-slides={slides.length}
      style={{ ["--slide-count" as string]: String(slides.length) }}
    >
      <div
        ref={viewportRef}
        className="banner-carousel__viewport"
        onPointerDown={pause}
        onTouchStart={pause}
      >
        {slides.map((slide, i) => (
          <a
            key={slide.id}
            href={slide.href}
            className="banner-slide"
            aria-label={`${slide.labelKo} 카테고리로 이동`}
            draggable={false}
          >
            <BannerImage
              src={slide.image}
              alt={slide.labelKo}
              style={slide.focal ? { objectPosition: slide.focal } : undefined}
              loading={i === 0 ? "eager" : "lazy"}
            />
            <span className="banner-slide__label">{slide.labelKo}</span>
          </a>
        ))}
      </div>

      <div className="banner-carousel__dots" aria-label="스포츠 배너">
        {slides.map((slide, i) => (
          <button
            key={`dot-${slide.id}`}
            type="button"
            className={`banner-dot${active === i ? " is-active" : ""}`}
            aria-label={slide.labelKo}
            aria-current={active === i ? "true" : undefined}
            onClick={() => {
              pause();
              goTo(i);
              setActive(i);
            }}
          />
        ))}
      </div>
    </div>
  );
}
