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

type BannerTier = "mobile" | "tablet" | "desktop";
type CdnPick = "primary" | "fallback";

function catalogPath(catalogSrc: string, tier: BannerTier): string {
  if (tier === "mobile") return toMobileBannerSrc(catalogSrc);
  if (tier === "tablet") return toTabletBannerSrc(catalogSrc);
  return catalogSrc;
}

function absoluteBannerUrl(
  catalogSrc: string,
  tier: BannerTier,
  cdn: CdnPick,
): string {
  const path = catalogPath(catalogSrc, tier);
  if (cdn === "fallback") {
    return mediaUrlFallback(path) || mediaUrl(path);
  }
  return mediaUrl(path);
}

/**
 * Device-optimised banner JPEGs via `<picture>` media queries so the correct
 * tier (m / t / desktop) is chosen on first paint — no desktop→mobile flash.
 * CDN host fallbacks still step through on error.
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
  const [cdn, setCdn] = useState<CdnPick>("primary");
  /** After both CDNs fail for a tier, drop to the next larger tier. */
  const [tierFloor, setTierFloor] = useState<BannerTier>("mobile");

  useEffect(() => {
    setCdn("primary");
    setTierFloor("mobile");
  }, [src]);

  const urls = useMemo(
    () => ({
      mobile: absoluteBannerUrl(src, "mobile", cdn),
      tablet: absoluteBannerUrl(src, "tablet", cdn),
      desktop: absoluteBannerUrl(src, "desktop", cdn),
    }),
    [src, cdn],
  );

  const onError = (_e: SyntheticEvent<HTMLImageElement>) => {
    if (cdn === "primary") {
      setCdn("fallback");
      return;
    }
    // Both CDNs failed for the current floor — escalate tier so <picture>
    // stops offering the broken smaller asset.
    setCdn("primary");
    setTierFloor((prev) =>
      prev === "mobile" ? "tablet" : prev === "tablet" ? "desktop" : "desktop",
    );
  };

  const showMobile = tierFloor === "mobile";
  const showTablet = tierFloor === "mobile" || tierFloor === "tablet";

  return (
    <picture style={{ display: "contents" }}>
      {showMobile ? (
        <source media="(max-width: 899px)" srcSet={urls.mobile} />
      ) : null}
      {showTablet ? (
        <source
          media="(min-width: 900px) and (max-width: 1199px)"
          srcSet={urls.tablet}
        />
      ) : null}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        className={className}
        src={urls.desktop}
        alt={alt}
        loading={loading}
        decoding="async"
        fetchPriority={fetchPriority}
        style={style}
        aria-hidden={ariaHidden}
        referrerPolicy="no-referrer"
        onError={onError}
      />
    </picture>
  );
}
