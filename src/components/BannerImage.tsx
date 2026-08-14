"use client";

import { toMobileBannerSrc } from "@/lib/banner-image";
import { mediaUrl } from "@/lib/product-image";

type BannerImageProps = {
  src: string;
  className?: string;
  alt?: string;
  loading?: "lazy" | "eager";
  fetchPriority?: "high" | "low" | "auto";
  style?: React.CSSProperties;
  "aria-hidden"?: boolean | "true" | "false";
};

/**
 * Serves a lighter `/banners/m/` asset on mobile viewports when present.
 * Desktop keeps the original high-res file.
 * On Vercel both resolve to the external media CDN (not Vercel bandwidth).
 */
export function BannerImage({
  src,
  className,
  alt = "",
  loading = "lazy",
  fetchPriority,
  style,
  "aria-hidden": ariaHidden,
}: BannerImageProps) {
  const desktopSrc = mediaUrl(src);
  const mobileSrc = mediaUrl(toMobileBannerSrc(src));
  const hasMobile = mobileSrc !== desktopSrc;

  if (!hasMobile) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        className={className}
        src={desktopSrc}
        alt={alt}
        loading={loading}
        decoding="async"
        fetchPriority={fetchPriority}
        style={style}
        aria-hidden={ariaHidden}
        referrerPolicy="no-referrer"
      />
    );
  }

  return (
    <picture style={{ display: "contents" }}>
      <source media="(max-width: 899px)" srcSet={mobileSrc} type="image/jpeg" />
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        className={className}
        src={desktopSrc}
        alt={alt}
        loading={loading}
        decoding="async"
        fetchPriority={fetchPriority}
        style={style}
        aria-hidden={ariaHidden}
        referrerPolicy="no-referrer"
      />
    </picture>
  );
}
