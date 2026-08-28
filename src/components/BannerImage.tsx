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

function tierForWidth(width: number): BannerTier {
  if (width <= 899) return "mobile";
  if (width <= 1199) return "tablet";
  return "desktop";
}

function catalogPath(catalogSrc: string, tier: BannerTier): string {
  if (tier === "mobile") return toMobileBannerSrc(catalogSrc);
  if (tier === "tablet") return toTabletBannerSrc(catalogSrc);
  return catalogSrc;
}

function absoluteBannerUrl(
  catalogSrc: string,
  tier: BannerTier,
  useFallbackCdn: boolean,
): string {
  const path = catalogPath(catalogSrc, tier);
  return useFallbackCdn ? mediaUrlFallback(path) || mediaUrl(path) : mediaUrl(path);
}

/** Ordered fallbacks: current tier → larger tiers, primary CDN then jsDelivr. */
function buildFallbackChain(catalogSrc: string, tier: BannerTier): string[] {
  const tiers: BannerTier[] =
    tier === "mobile"
      ? ["mobile", "tablet", "desktop"]
      : tier === "tablet"
        ? ["tablet", "desktop"]
        : ["desktop"];
  const out: string[] = [];
  for (const t of tiers) {
    const primary = absoluteBannerUrl(catalogSrc, t, false);
    const fallback = absoluteBannerUrl(catalogSrc, t, true);
    if (primary) out.push(primary);
    if (fallback && fallback !== primary) out.push(fallback);
  }
  return out;
}

/**
 * Device-optimised banner JPEGs. Picks mobile/tablet/desktop URL from viewport
 * width (more reliable than `srcSet` + external CDN). Steps through CDN hosts
 * on error.
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
  const [tier, setTier] = useState<BannerTier>("desktop");
  const [fallbackIndex, setFallbackIndex] = useState(0);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const update = () => setTier(tierForWidth(window.innerWidth));
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);

  useEffect(() => {
    setFallbackIndex(0);
  }, [src, tier]);

  const chain = useMemo(() => buildFallbackChain(src, tier), [src, tier]);
  const resolvedSrc = chain[fallbackIndex] ?? mediaUrl(src);
  const displaySrc = mounted ? resolvedSrc : mediaUrl(src);

  const onError = (_e: SyntheticEvent<HTMLImageElement>) => {
    if (fallbackIndex + 1 < chain.length) {
      setFallbackIndex((i) => i + 1);
    }
  };

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      className={className}
      src={displaySrc}
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
