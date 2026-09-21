import Link from "next/link";
import type { ReactNode } from "react";
import { brandLogoSrcForNavId } from "@/lib/brand-logos";
import { brandTileSrcForNavId } from "@/lib/brand-tiles";

type BrandChipProps = {
  href: string;
  navId: string;
  label: string;
  active?: boolean;
  className?: string;
  children?: ReactNode;
};

/**
 * Luxury brand tile: symbolic photo + dark wash + white wordmark.
 * Falls back to solid black chip when no tile/logo is known.
 */
export function BrandChipContent({
  navId,
  label,
}: {
  navId: string;
  label: string;
}) {
  const logo = brandLogoSrcForNavId(navId);
  const tile = brandTileSrcForNavId(navId);

  return (
    <>
      {tile ? (
        <>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            className="chip__brand-bg"
            src={tile}
            alt=""
            aria-hidden
            decoding="async"
            loading="lazy"
          />
          <span className="chip__brand-shade" aria-hidden />
        </>
      ) : null}
      {logo ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          className="chip__brand-logo"
          src={logo}
          alt=""
          aria-hidden
          decoding="async"
        />
      ) : (
        <span className="chip__brand-label">{label}</span>
      )}
    </>
  );
}

export function BrandChipLink({
  href,
  navId,
  label,
  active,
  className,
}: BrandChipProps) {
  const logo = brandLogoSrcForNavId(navId);
  const tile = brandTileSrcForNavId(navId);
  const hasBrand = Boolean(logo || tile);

  return (
    <Link
      href={href}
      className={
        className ||
        (hasBrand
          ? `chip chip--brand${active ? " is-active" : ""}`
          : `chip chip--sub${active ? " is-active" : ""}`)
      }
      aria-label={label}
    >
      {hasBrand ? <BrandChipContent navId={navId} label={label} /> : label}
    </Link>
  );
}
