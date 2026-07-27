import type { ReactNode } from "react";
import type { ProductImageTone } from "@/lib/product-image";

const toneClass: Record<ProductImageTone, string> = {
  card: "product-frame product-frame--card",
  detail: "product-frame product-frame--detail",
  cart: "product-frame product-frame--cart",
  swatch: "product-frame product-frame--swatch",
};

type ProductImageProps = {
  src: string;
  alt: string;
  /** Visual size / aspect context — keeps every surface on the same frame rules */
  tone?: ProductImageTone;
  className?: string;
  imgClassName?: string;
  loading?: "lazy" | "eager";
  children?: ReactNode;
};

/**
 * Shared product photo frame. Always uses contain + fixed aspect so
 * newly uploaded catalog images stay aligned across the site.
 */
export function ProductImage({
  src,
  alt,
  tone = "card",
  className = "",
  imgClassName = "",
  loading = "lazy",
  children,
}: ProductImageProps) {
  const frameClass = [toneClass[tone], className].filter(Boolean).join(" ");
  const imageClass = ["product-frame__img", imgClassName]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={frameClass}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        className={imageClass}
        src={src}
        alt={alt}
        loading={loading}
        decoding="async"
      />
      {children}
    </div>
  );
}
