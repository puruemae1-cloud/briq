"use client";

import { useEffect, useMemo, useState, type SyntheticEvent } from "react";
import { toMobileBannerSrc, toTabletBannerSrc } from "@/lib/banner-image";
import { mediaUrl, mediaUrlFallback } from "@/lib/product-image";

type BannerImageProps = {
  src: string;
  className?: string;
  alt?: string;
  loading?: "lazy" | "eager";
  fetchPriority?: "high" | "low" | "auto";
  style?: React.CSSProperties;
  "aria-hidden"?: boolean | "true" | "false";
};

function bannerUrls(catalogSrc: string, useFallbackCdn: boolean) {
  const resolve = (path: string) =>
    useFallbackCdn ? mediaUrlFallback(path) || mediaUrl(path) : mediaUrl(path);
  const desktop = resolve(catalogSrc);
  const tablet = resolve(toTabletBannerSrc(catalogSrc));
  const mobile = resolve(toMobileBannerSrc(catalogSrc));
  return { desktop, tablet, mobile };
}

/**
 * Device-optimised banner JPEGs via srcSet (no WebP — raw CDN 404s broke mobile
 * `<picture>` fallbacks). Swaps to jsDelivr when GitHub raw is stale/missing.
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
  const [useFallbackCdn, setUseFallbackCdn] = useState(false);
  const urls = useMemo(
    () => bannerUrls(src, useFallbackCdn),
    [src, useFallbackCdn],
  );

  useEffect(() => {
    setUseFallbackCdn(false);
  }, [src]);

  const hasMobile = urls.mobile !== urls.desktop;
  const hasTablet = urls.tablet !== urls.desktop;

  const srcSet = hasMobile
    ? [
        `${urls.mobile} 900w`,
        hasTablet ? `${urls.tablet} 1200w` : null,
        `${urls.desktop} 2400w`,
      ]
        .filter(Boolean)
        .join(", ")
    : undefined;

  const onError = (_e: SyntheticEvent<HTMLImageElement>) => {
    if (!useFallbackCdn) {
      const altHost = mediaUrlFallback(urls.desktop);
      if (altHost && altHost !== urls.desktop) {
        setUseFallbackCdn(true);
      }
    }
  };

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      className={className}
      src={urls.desktop}
      srcSet={srcSet}
      sizes={srcSet ? "100vw" : undefined}
      alt={alt}
      loading={loading}
      decoding="async"
      fetchPriority={fetchPriority}
      style={style}
      aria-hidden={ariaHidden}
      referrerPolicy="no-referrer"
      onError={onError}
    />
  );
}
