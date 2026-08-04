"use client";

import {
  useCallback,
  useEffect,
  useState,
  type KeyboardEvent,
  type MouseEvent,
  type ReactNode,
} from "react";
import type { Product } from "@/data/products";
import { resolveCardGallery } from "@/lib/product-image";

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
  const multi = gallery.length > 1 && !soldOut;
  const [index, setIndex] = useState(0);
  const [active, setActive] = useState(false);

  useEffect(() => {
    setIndex(0);
    setActive(false);
  }, [product.id, product.shopColorKey, product.image]);

  const go = useCallback(
    (next: number) => {
      if (!multi) return;
      const len = gallery.length;
      setIndex(((next % len) + len) % len);
    },
    [gallery.length, multi],
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
        {gallery.map((src, i) => (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            key={src}
            className={`product-frame__img product-card__img product-card-media__img${
              i === index ? " is-current" : ""
            }`}
            src={src}
            alt={i === 0 ? product.nameKo : ""}
            aria-hidden={i !== 0}
            loading={i === 0 ? "lazy" : "lazy"}
            decoding="async"
          />
        ))}
        {children}
        {multi ? (
          <>
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
              <span aria-hidden>‹</span>
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
              <span aria-hidden>›</span>
            </button>
            <div
              className="product-card-media__bars"
              aria-hidden
            >
              {gallery.map((src, i) => (
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
