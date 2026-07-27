"use client";

import { useState } from "react";
import { ProductImage } from "@/components/ProductImage";

export function ProductGallery({
  images,
  alt,
  soldOut,
  badge,
}: {
  images: string[];
  alt: string;
  soldOut?: boolean;
  badge?: string | null;
}) {
  const list = images.length > 0 ? images : [];
  const [active, setActive] = useState(0);
  const src = list[active] ?? list[0];

  if (!src) return null;

  return (
    <div className="product-detail__gallery">
      <ProductImage
        src={src}
        alt={alt}
        tone="detail"
        className={`product-detail__media${soldOut ? " is-sold-out" : ""}`}
        loading="eager"
      >
        {soldOut ? (
          <span className="product-sold-out product-sold-out--detail" aria-label="Sold Out">
            Sold Out
          </span>
        ) : badge ? (
          <p className="product-detail__media-badge">{badge}</p>
        ) : null}
      </ProductImage>

      {list.length > 1 ? (
        <div className="product-gallery-thumbs" role="listbox" aria-label="상품 이미지">
          {list.map((img, i) => (
            <button
              key={img}
              type="button"
              role="option"
              aria-selected={i === active}
              className={`product-gallery-thumbs__item${i === active ? " is-active" : ""}`}
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
