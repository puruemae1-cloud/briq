"use client";

import { useEffect, useState, type ReactNode, type SyntheticEvent } from "react";
import {
  mediaUrl,
  mediaUrlFallback,
  type ProductImageTone,
} from "@/lib/product-image";

const toneClass: Record<ProductImageTone, string> = {
  card: "product-frame product-frame--card",
  detail: "product-frame product-frame--detail",
  cart: "product-frame product-frame--cart",
  swatch: "product-frame product-frame--swatch",
};

type ProductImageProps = {
  src: string;
  alt: string;
  /** Optional secondary image revealed on PC pointer hover (model / wrist). */
  hoverSrc?: string;
  /** Visual size / aspect context — keeps every surface on the same frame rules */
  tone?: ProductImageTone;
  className?: string;
  imgClassName?: string;
  loading?: "lazy" | "eager";
  children?: ReactNode;
};

function CdnImg({
  resolved,
  alt,
  className,
  loading,
  ariaHidden,
}: {
  resolved: string;
  alt: string;
  className: string;
  loading: "lazy" | "eager";
  ariaHidden?: boolean;
}) {
  const [src, setSrc] = useState(resolved);
  useEffect(() => {
    setSrc(resolved);
  }, [resolved]);

  const onError = (_e: SyntheticEvent<HTMLImageElement>) => {
    const altUrl = mediaUrlFallback(resolved);
    if (altUrl && altUrl !== src) {
      setSrc(altUrl);
    }
  };

  if (!resolved) return null;

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      className={className}
      src={src}
      alt={alt}
      aria-hidden={ariaHidden}
      loading={loading}
      decoding="async"
      referrerPolicy="no-referrer"
      onError={onError}
    />
  );
}

/**
 * Shared product photo frame. Always uses contain + fixed aspect so
 * newly uploaded catalog images stay aligned across the site.
 * When `hoverSrc` is set, fine-pointer hover crossfades to the lifestyle cut.
 */
export function ProductImage({
  src,
  alt,
  hoverSrc,
  tone = "card",
  className = "",
  imgClassName = "",
  loading = "lazy",
  children,
}: ProductImageProps) {
  const primary = mediaUrl(src);
  const hover = hoverSrc ? mediaUrl(hoverSrc) : undefined;
  const hasHover = Boolean(hover && hover !== primary);
  const frameClass = [
    toneClass[tone],
    hasHover ? "product-frame--has-hover" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");
  const imageClass = ["product-frame__img", imgClassName]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={frameClass}>
      <CdnImg
        resolved={primary}
        alt={alt}
        className={`${imageClass} product-frame__img--primary`}
        loading={loading}
      />
      {hasHover ? (
        <CdnImg
          resolved={hover!}
          alt=""
          className={`${imageClass} product-frame__img--hover`}
          loading="lazy"
          ariaHidden
        />
      ) : null}
      {children}
    </div>
  );
}
