"use client";

import {
  useCallback,
  useEffect,
  useState,
  type KeyboardEvent,
  type MouseEvent,
  type ReactNode,
} from "react";
import type {  Product  } from "@/data/product-types";
import { mediaUrl, resolveCardGallery } from "@/lib/product-image";

type ProductCardMediaProps = {
  product: Product;
  soldOut?: boolean;
  children?: ReactNode;
};

/**
 * Gucci-like PLP media: primary packshot, hover advances to slide 2,
 * arrow controls + ultra-thin segment bars for the gallery.
 */
export function ProductCardMedia({
  product,
  soldOut = false,
  children,
}: ProductCardMediaProps) {
  const gallery = resolveCardGallery(product, 8);
  // Sold-out cards only need the primary packshot — extra slides still used to
  // paint when sold-out opacity leaked onto non-current imgs.
  const slides = soldOut ? gallery.slice(0, 1) : gallery;
  const multi = slides.length > 1;
  const [index, setIndex] = useState(0);
  const [active, setActive] = useState(false);

  useEffect(() => {
    setIndex(0);
    setActive(false);
  }, [product.id, product.shopColorKey, product.image, soldOut]);

  const go = useCallback(
    (next: number) => {
      if (!multi) return;
      const len = slides.length;
      setIndex(((next % len) + len) % len);
    },
    [slides.length, multi],
  );

  const onEnter = () => {
    if (!multi) return;
    setActive(true);
    // Match Gucci PLP: hover jumps to the second frame when available
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

  return (
    <div
      className={`product-card-media${multi ? " product-card-media--multi" : ""}${
        active ? " is-active" : ""
      }`}
      onMouseEnter={onEnter}
      onMouseLeave={onLeave}
      onFocus={onEnter}
      onBlur={onLeave}
      onKeyDown={onKey}
    >
      <div className="product-frame product-frame--card product-card-media__frame">
        {slides.map((src, i) => (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            key={src}
            className={`product-frame__img product-card__img product-card-media__img${
              i === index ? " is-current" : ""
            }`}
            src={mediaUrl(src)}
            alt={i === 0 ? product.nameKo : ""}
            aria-hidden={i !== 0}
            loading={i === 0 ? "lazy" : "lazy"}
            decoding="async"
            referrerPolicy="no-referrer"
          />
        ))}
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
