"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { useEffect, useState, type MouseEvent } from "react";
import { rememberScrollFor } from "@/lib/keep-scroll";

type Props = {
  href: string;
  className?: string;
  children: React.ReactNode;
  scroll?: boolean;
  replace?: boolean;
  role?: string;
  "aria-label"?: string;
};

function setShopNavigating(on: boolean) {
  if (typeof document === "undefined") return;
  if (on) document.documentElement.dataset.shopNavigating = "1";
  else delete document.documentElement.dataset.shopNavigating;
}

function sameHref(a: string, b: string): boolean {
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
 * Shop filter chips / brand rows.
 *
 * Soft RSC navigation waits on catalogue work and leaves the chrome feeling
 * stuck. Hard assign matches header {@link ShopFastLink} so chips react on the
 * same tap even as weekly sync grows brand JSON.
 */
export function ShopNavLink({
  href,
  className,
  children,
  scroll = false,
  replace = false,
  role,
  "aria-label": ariaLabel,
}: Props) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [optimistic, setOptimistic] = useState(false);
  const currentHref = `${pathname}${searchParams.toString() ? `?${searchParams.toString()}` : ""}`;

  useEffect(() => {
    setOptimistic(false);
    setShopNavigating(false);
  }, [currentHref]);

  const baseClass = (className ?? "").replace(/\bis-active\b/g, "").replace(/\bis-pending\b/g, "").trim();
  const serverActive = Boolean(className?.includes("is-active"));
  const active = optimistic || serverActive || sameHref(href, currentHref);

  const onClick = (e: MouseEvent<HTMLAnchorElement>) => {
    if (sameHref(href, currentHref)) {
      e.preventDefault();
      return;
    }
    e.preventDefault();
    setOptimistic(true);
    setShopNavigating(true);
    document.documentElement.dataset.homeNavigating = "1";
    if (!scroll) rememberScrollFor(href);
    if (replace) window.location.replace(href);
    else window.location.assign(href);
  };

  return (
    <Link
      href={href}
      scroll={scroll}
      replace={replace}
      prefetch
      role={role}
      aria-label={ariaLabel}
      aria-current={active ? "page" : undefined}
      className={`${baseClass}${active ? " is-active" : ""}`}
      onClick={onClick}
    >
      {children}
    </Link>
  );
}
