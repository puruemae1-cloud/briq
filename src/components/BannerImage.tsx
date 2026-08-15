"use client";

import { toMobileBannerSrc, toTabletBannerSrc } from "@/lib/banner-image";
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
 * Serves device-optimised banner assets:
 *  - phone  (≤899px):  `/banners/m/…`
 *  - tablet (900–1199px): `/banners/t/…` when present, else desktop
 *  - desktop (≥1200px): original `/banners/…`
 * On Vercel all resolve to the external media CDN (not Vercel bandwidth).
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
  const tabletSrc = mediaUrl(toTabletBannerSrc(src));
  const mobileSrc = mediaUrl(toMobileBannerSrc(src));
  const hasTablet = tabletSrc !== desktopSrc;
  const hasMobile = mobileSrc !== desktopSrc;

  if (!hasTablet && !hasMobile) {
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
      {hasMobile ? (
        <source
          media="(max-width: 899px)"
          srcSet={mobileSrc}
          type="image/jpeg"
        />
      ) : null}
      {hasTablet ? (
        <source
          media="(max-width: 1199px)"
          srcSet={tabletSrc}
          type="image/jpeg"
        />
      ) : null}
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
