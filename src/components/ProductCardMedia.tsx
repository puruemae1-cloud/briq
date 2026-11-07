"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type KeyboardEvent,
  type MouseEvent,
  type ReactNode,
  type TouchEvent,
} from "react";
import type { Product } from "@/data/product-types";
import { mediaUrl, mediaUrlFallback, resolveCardGallery } from "@/lib/product-image";

type ProductCardMediaProps = {
  product: Product;
  soldOut?: boolean;
  children?: ReactNode;
};

const SWIPE_THRESHOLD = 36;

function CardSlide({
  src,
  alt,
  current,
  eager,
}: {
  src: string;
  alt: string;
  current: boolean;
  eager: boolean;
}) {
  const resolved = mediaUrl(src);
  const [shown, setShown] = useState(resolved);
  const [status, setStatus] = useState<"loading" | "ready" | "failed">(
    "loading",
  );
  useEffect(() => {
    setShown(resolved);
    setStatus("loading");
  }, [resolved]);

  useEffect(() => {
    if (status !== "loading" || !shown) return;
    const t = window.setTimeout(() => {
      const altUrl = mediaUrlFallback(resolved);
      if (altUrl && altUrl !== shown) {
        setShown(altUrl);
        setStatus("loading");
        return;
      }
      setStatus("failed");
    }, 4500);
    return () => window.clearTimeout(t);
  }, [status, shown, resolved]);

  const markReady = (el: HTMLImageElement | null) => {
    if (!el) return;
    if (el.complete && el.naturalWidth > 0) {
      setStatus("ready");
      return;
    }
    if (el.complete && el.naturalWidth === 0) {
      const altUrl = mediaUrlFallback(resolved);
      if (altUrl && altUrl !== shown) {
        setShown(altUrl);
        setStatus("loading");
        return;
      }
      setStatus("failed");
    }
  };

  return (
    <>
      {status !== "ready" ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          className={`product-frame__placeholder product-card-media__img${
            current ? " is-current" : ""
          }`}
          src="/briq-mark.svg"
          alt="Briq"
          aria-hidden
          decoding="async"
        />
      ) : null}
      {status !== "failed" ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          ref={markReady}
          className={`product-frame__img product-card__img product-card-media__img${
            current ? " is-current" : ""
          }${status === "loading" ? " is-loading" : ""}`}
          src={shown}
          alt={alt}
          aria-hidden={!current}
          /* Current / near-viewport slides must not use lazy — iOS Safari often
             skips decoding opacity:0 lazy imgs until a tap (PDP navigation). */
          loading={eager || current ? "eager" : "lazy"}
          fetchPriority={current ? "high" : "auto"}
          decoding="async"
          referrerPolicy="no-referrer"
          onLoad={() => setStatus("ready")}
          onError={() => {
            const altUrl = mediaUrlFallback(resolved);
            if (altUrl && altUrl !== shown) {
              setShown(altUrl);
              setStatus("loading");
              return;
            }
            setStatus("failed");
          }}
        />
      ) : null}
    </>
  );
}

/**
 * Gucci-like PLP media: primary packshot, hover advances to slide 2,
 * arrow controls + ultra-thin segment bars for the gallery.
 * Near-viewport cards preload every gallery frame so mobile thumbs paint
 * without waiting for a PDP click.
 */
export function ProductCardMedia({
  product,
  soldOut = false,
  children,
}: ProductCardMediaProps) {
  // Cap frames so PLP RSC/HTML stays small for crawlers (Naver download size).
  const gallery = resolveCardGallery(product, 4);
  const slides = soldOut ? gallery.slice(0, 1) : gallery;
  const multi = slides.length > 1;
  const [index, setIndex] = useState(0);
  const [active, setActive] = useState(false);
  const [inView, setInView] = useState(false);
  const rootRef = useRef<HTMLDivElement | null>(null);
  const touchStart = useRef<{ x: number; y: number } | null>(null);

  useEffect(() => {
    setIndex(0);
    setActive(false);
  }, [product.id, product.shopColorKey, product.image, soldOut]);

  useEffect(() => {
    const el = rootRef.current;
    if (!el) return;
    const io = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          setInView(true);
          io.disconnect();
        }
      },
      { rootMargin: "240px 0px", threshold: 0.01 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [product.id]);

  const go = useCallback(
    (next: number) => {
      if (!multi) return;
      const len = slides.length;
      setIndex(((next % len) + len) % len);
      setActive(true);
    },
    [slides.length, multi],
  );

  const onEnter = () => {
    if (!multi) return;
    setActive(true);
    setIndex((i) => (i === 0 ? 1 : i));
  };

  const onLeave = () => {
    setActive(false);
    setIndex(0);
  };

  const stopNav = (e: MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const onKey = (e: KeyboardEvent) => {
    if (!multi || !active) return;
    if (e.key === "ArrowLeft") {
      e.preventDefault();
      go(index - 1);
    } else if (e.key === "ArrowRight") {
      e.preventDefault();
      go(index + 1);
    }
  };

  const onTouchStart = (e: TouchEvent) => {
    if (!multi) return;
    const t = e.changedTouches[0];
    if (!t) return;
    touchStart.current = { x: t.clientX, y: t.clientY };
  };

  const onTouchEnd = (e: TouchEvent) => {
    if (!multi) return;
    const start = touchStart.current;
    touchStart.current = null;
    if (!start) return;
    const t = e.changedTouches[0];
    if (!t) return;
    const dx = t.clientX - start.x;
    const dy = t.clientY - start.y;
    if (Math.abs(dx) < SWIPE_THRESHOLD) return;
    if (Math.abs(dx) <= Math.abs(dy)) return;
    e.preventDefault();
    e.stopPropagation();
    go(dx < 0 ? index + 1 : index - 1);
  };

  // Once near the viewport, mount every frame so thumbs are warm before tap.
  const mountedSlides = multi && inView ? slides : slides.slice(0, 1);

  return (
    <div
      ref={rootRef}
      className={`product-card-media${multi ? " product-card-media--multi" : ""}${
        active ? " is-active" : ""
      }`}
      onMouseEnter={onEnter}
      onMouseLeave={onLeave}
      onFocus={onEnter}
      onBlur={onLeave}
      onKeyDown={onKey}
      onTouchStart={onTouchStart}
      onTouchEnd={onTouchEnd}
    >
      <div className="product-frame product-frame--card product-card-media__frame">
        {mountedSlides.map((src, i) => {
          const slideIndex = multi && inView ? i : 0;
          return (
            <CardSlide
              key={src}
              src={src}
              alt={
                slideIndex === 0
                  ? product.nameKo
                  : `${product.nameKo} ${slideIndex + 1}`
              }
              current={slideIndex === index}
              eager={inView}
            />
          );
        })}
        {children}
        {multi ? (
          <>
            <div className="product-card-media__nav" aria-hidden={false}>
              <button
                type="button"
                className="product-card-media__arrow product-card-media__arrow--prev"
                aria-label="이전 사진"
                tabIndex={active ? 0 : -1}
                onClick={(e) => {
                  stopNav(e);
                  go(index - 1);
                }}
              >
                <svg
                  className="product-card-media__chevron"
                  viewBox="0 0 24 24"
                  width="12"
                  height="12"
                  aria-hidden
                >
                  <path
                    d="M14.5 5.25 8.75 12l5.75 6.75"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="square"
                    strokeLinejoin="miter"
                  />
                </svg>
              </button>
              <button
                type="button"
                className="product-card-media__arrow product-card-media__arrow--next"
                aria-label="다음 사진"
                tabIndex={active ? 0 : -1}
                onClick={(e) => {
                  stopNav(e);
                  go(index + 1);
                }}
              >
                <svg
                  className="product-card-media__chevron"
                  viewBox="0 0 24 24"
                  width="12"
                  height="12"
                  aria-hidden
                >
                  <path
                    d="M9.5 5.25 15.25 12 9.5 18.75"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="square"
                    strokeLinejoin="miter"
                  />
                </svg>
              </button>
            </div>
            <div className="product-card-media__bars" aria-hidden>
              {slides.map((src, i) => (
                <span
                  key={src}
                  className={`product-card-media__bar${
                    i === index ? " is-active" : ""
                  }`}
                />
              ))}
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}
