"use client";

import { useEffect, useState } from "react";
import { ProductImage } from "@/components/ProductImage";

export function ProductGallery({
  images,
  alt,
  soldOut,
  badge,
  resetKey,
}: {
  images: string[];
  alt: string;
  soldOut?: boolean;
  badge?: string | null;
  /** Change when option/variant changes so the first image is shown again. */
  resetKey?: string;
}) {
  const list = images.length > 0 ? images : [];
  const [active, setActive] = useState(0);

  useEffect(() => {
    setActive(0);
  }, [resetKey, list.join("|")]);

  const safeIndex = list.length ? Math.min(active, list.length - 1) : 0;
  const src = list[safeIndex] ?? list[0];

  if (!src) return null;

  const go = (dir: -1 | 1) => {
    if (list.length < 2) return;
    setActive((i) => (i + dir + list.length) % list.length);
  };

  return (
    <div className="product-detail__gallery">
      <button
        type="button"
        className={`product-detail__media-hit${soldOut ? " is-sold-out" : ""}`}
        onClick={() => go(1)}
        aria-label={list.length > 1 ? "다음 상품 사진" : alt}
      >
        <ProductImage
          src={src}
          alt={alt}
          tone="detail"
          className={`product-detail__media${soldOut ? " is-sold-out" : ""}`}
          loading="eager"
        >
          {soldOut ? (
            <span
              className="product-sold-out product-sold-out--detail"
              aria-label="Sold Out"
            >
              Sold Out
            </span>
          ) : badge ? (
            <p className="product-detail__media-badge">{badge}</p>
          ) : null}
          {list.length > 1 ? (
            <span className="product-gallery-count" aria-hidden>
              {safeIndex + 1} / {list.length}
            </span>
          ) : null}
        </ProductImage>
      </button>

      {list.length > 1 ? (
        <div
          className="product-gallery-thumbs"
          role="listbox"
          aria-label="상품 이미지"
        >
          {list.map((img, i) => (
            <button
              key={`${img}-${i}`}
              type="button"
              role="option"
              aria-selected={i === safeIndex}
              className={`product-gallery-thumbs__item${i === safeIndex ? " is-active" : ""}`}
              onClick={() => setActive(i)}
            >
              <ProductImage src={img} alt="" tone="swatch" />
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
