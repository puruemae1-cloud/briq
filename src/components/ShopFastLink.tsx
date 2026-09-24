"use client";

import Link from "next/link";
import type { ReactNode, MouseEvent } from "react";

type Props = {
  href: string;
  className?: string;
  children: ReactNode;
  prefetch?: boolean;
  "aria-label"?: string;
  role?: string;
};

function setShopNavigating(on: boolean) {
  if (typeof document === "undefined") return;
  if (on) document.documentElement.dataset.shopNavigating = "1";
  else delete document.documentElement.dataset.shopNavigating;
}

function currentPathAndQuery(): string {
  if (typeof window === "undefined") return "";
  return `${window.location.pathname}${window.location.search}`;
}

function sameShopHref(a: string, b: string): boolean {
  try {
    const left = new URL(a, "https://briq.local");
    const right = new URL(b, "https://briq.local");
    if (left.pathname !== right.pathname) return false;
    const lk = [...left.searchParams.entries()].sort().toString();
    const rk = [...right.searchParams.entries()].sort().toString();
    return lk === rk;
  } catch {
    return a === b;
  }
}

/**
 * Header / drawer links into heavy `/shop` PLPs.
 *
 * Soft RSC navigation waits on multi-brand catalogue work and can sit on the
 * current page with no chrome. Full document navigation moves the browser
 * immediately (same pattern as HomeLogoLink → `/`).
 */
export function ShopFastLink({
  href,
  className,
  children,
  prefetch = true,
  "aria-label": ariaLabel,
  role,
}: Props) {
  const isShop = href.startsWith("/shop");

  const onClick = (e: MouseEvent<HTMLAnchorElement>) => {
    if (!isShop) return;
    if (sameShopHref(href, currentPathAndQuery())) {
      e.preventDefault();
      return;
    }
    e.preventDefault();
    setShopNavigating(true);
    document.documentElement.dataset.homeNavigating = "1";
    window.location.assign(href);
  };

  return (
    <Link
      href={href}
      prefetch={prefetch}
      className={className}
      aria-label={ariaLabel}
      role={role}
      onClick={onClick}
    >
      {children}
    </Link>
  );
}
