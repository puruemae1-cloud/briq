"use client";

import { useEffect, useCallback, useState } from "react";
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
  resetKey?: string;
}) {
  const list = images.length > 0 ? images : [];
  const [active, setActive] = useState(0);
  const [zoomOpen, setZoomOpen] = useState(false);

  useEffect(() => {
    setActive(0);
    setZoomOpen(false);
  }, [resetKey, list.join("|")]);

  const safeIndex = list.length ? Math.min(active, list.length - 1) : 0;
  const src = list[safeIndex] ?? list[0];

  const go = useCallback(
    (dir: -1 | 1) => {
      if (list.length < 2) return;
      setActive((i) => (i + dir + list.length) % list.length);
    },
    [list.length],
  );

  useEffect(() => {
    if (!zoomOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setZoomOpen(false);
      if (e.key === "ArrowRight") go(1);
      if (e.key === "ArrowLeft") go(-1);
    };
    window.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [zoomOpen, go]);

  if (!src) return null;

  return (
    <div className="product-detail__gallery">
      <div
        className={`product-detail__media-wrap${soldOut ? " is-sold-out" : ""}`}
      >
        <button
          type="button"
          className="product-detail__media-hit"
          aria-label={soldOut ? alt : "사진 확대 보기"}
          disabled={soldOut}
          onClick={() => {
            if (!soldOut) setZoomOpen(true);
          }}
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
            {!soldOut ? (
              <span className="product-gallery-zoom-hint" aria-hidden>
                <svg viewBox="0 0 24 24" width="18" height="18">
                  <circle
                    cx="10.5"
                    cy="10.5"
                    r="6.5"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                  />
                  <path
                    d="M15.5 15.5 L20 20"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                  />
                  <path
                    d="M10.5 7.5 v6 M7.5 10.5 h6"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.6"
                    strokeLinecap="round"
                  />
                </svg>
              </span>
            ) : null}
          </ProductImage>
        </button>

        {list.length > 1 ? (
          <>
            <button
              type="button"
              className="product-gallery-nav product-gallery-nav--prev"
              aria-label="이전 사진"
              onClick={(e) => {
                e.stopPropagation();
                go(-1);
              }}
            >
              ‹
            </button>
            <button
              type="button"
              className="product-gallery-nav product-gallery-nav--next"
              aria-label="다음 사진"
              onClick={(e) => {
                e.stopPropagation();
                go(1);
              }}
            >
              ›
            </button>
          </>
        ) : null}
      </div>

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

      {zoomOpen ? (
        <div
          className="product-lightbox"
          role="dialog"
          aria-modal="true"
          aria-label="확대 이미지"
          onClick={() => setZoomOpen(false)}
        >
          <button
            type="button"
            className="product-lightbox__close"
            aria-label="닫기"
            onClick={() => setZoomOpen(false)}
          >
            ×
          </button>
          {list.length > 1 ? (
            <>
              <button
                type="button"
                className="product-lightbox__nav product-lightbox__nav--prev"
                aria-label="이전 사진"
                onClick={(e) => {
                  e.stopPropagation();
                  go(-1);
                }}
              >
                ‹
              </button>
              <button
                type="button"
                className="product-lightbox__nav product-lightbox__nav--next"
                aria-label="다음 사진"
                onClick={(e) => {
                  e.stopPropagation();
                  go(1);
                }}
              >
                ›
              </button>
            </>
          ) : null}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            className="product-lightbox__img"
            src={src}
            alt={alt}
            onClick={(e) => e.stopPropagation()}
          />
          {list.length > 1 ? (
            <p className="product-lightbox__count">
              {safeIndex + 1} / {list.length}
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
