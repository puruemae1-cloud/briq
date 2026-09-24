import type { ReactNode } from "react";
import { ShopFastLink } from "@/components/ShopFastLink";
import { brandDisplayNameForNavId } from "@/lib/brand-logos";
import { navBrandFamily } from "@/lib/brand-nav-order";

type BrandChipProps = {
  href: string;
  navId: string;
  label: string;
  active?: boolean;
  className?: string;
  children?: ReactNode;
};

/** True when this nav id should render as a solid black brand tile. */
export function isBrandChipNavId(navId: string): boolean {
  return Boolean(navBrandFamily(navId));
}

/**
 * Luxury brand tile: solid black + uniform white wordmark text.
 */
export function BrandChipContent({
  navId,
  label,
}: {
  navId: string;
  label: string;
}) {
  const text = brandDisplayNameForNavId(navId) || label;

  return <span className="chip__brand-label">{text}</span>;
}

export function BrandChipLink({
  href,
  navId,
  label,
  active,
  className,
}: BrandChipProps) {
  const isBrand = isBrandChipNavId(navId);

  return (
    <ShopFastLink
      href={href}
      className={
        className ||
        (isBrand
          ? `chip chip--brand${active ? " is-active" : ""}`
          : `chip chip--sub${active ? " is-active" : ""}`)
      }
      aria-label={label}
    >
      {isBrand ? <BrandChipContent navId={navId} label={label} /> : label}
    </ShopFastLink>
  );
}
