"use client";

import { useEffect, useState, type ReactNode } from "react";
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

/** If jsDelivr stalls (common with some KR networks / blockers), flip CDN. */
const CDN_LOAD_TIMEOUT_MS = 4500;

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
  const [status, setStatus] = useState<"loading" | "ready" | "failed">(
    "loading",
  );
  useEffect(() => {
    setSrc(resolved);
    setStatus("loading");
  }, [resolved]);

  useEffect(() => {
    if (status !== "loading" || !src) return;
    const t = window.setTimeout(() => {
      const altUrl = mediaUrlFallback(resolved);
      if (altUrl && altUrl !== src) {
        setSrc(altUrl);
        setStatus("loading");
        return;
      }
      // No alternate host — stop hiding behind opacity:0 forever.
      setStatus("failed");
    }, CDN_LOAD_TIMEOUT_MS);
    return () => window.clearTimeout(t);
  }, [status, src, resolved]);

  if (!resolved) return null;

  const markReady = (el: HTMLImageElement | null) => {
    // Cached images often skip onLoad after hydration — check complete.
    if (!el) return;
    if (el.complete && el.naturalWidth > 0) {
      setStatus("ready");
      return;
    }
    // Blockers sometimes return a 0×0 "success" — treat as hard fail.
    if (el.complete && el.naturalWidth === 0) {
      const altUrl = mediaUrlFallback(resolved);
      if (altUrl && altUrl !== src) {
        setSrc(altUrl);
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
          className={`product-frame__placeholder ${className}`}
          src="/briq-mark.svg"
          alt=""
          aria-hidden
          decoding="async"
        />
      ) : null}
      {status !== "failed" ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          ref={markReady}
          className={`${className}${status === "loading" ? " is-loading" : ""}`}
          src={src}
          alt={alt}
          aria-hidden={ariaHidden}
          loading={loading}
          decoding="async"
          referrerPolicy="no-referrer"
          onLoad={(e) => {
            const el = e.currentTarget;
            if (el.naturalWidth > 0) {
              setStatus("ready");
              return;
            }
            const altUrl = mediaUrlFallback(resolved);
            if (altUrl && altUrl !== src) {
              setSrc(altUrl);
              setStatus("loading");
              return;
            }
            setStatus("failed");
          }}
          onError={() => {
            const altUrl = mediaUrlFallback(resolved);
            if (altUrl && altUrl !== src) {
              setSrc(altUrl);
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
