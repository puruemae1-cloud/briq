"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

type Props = {
  href: string;
  className?: string;
  children: React.ReactNode;
  scroll?: boolean;
  replace?: boolean;
  role?: string;
};

function setShopNavigating(on: boolean) {
  if (typeof document === "undefined") return;
  if (on) document.documentElement.dataset.shopNavigating = "1";
  else delete document.documentElement.dataset.shopNavigating;
}

/**
 * Shop filter chips. Prefer native Next Link navigation (no startTransition) so
 * the clicked chip activates immediately instead of sitting in a dashed pending
 * state while the RSC payload for a large brand leaf loads.
 */
export function ShopNavLink({
  href,
  className,
  children,
  scroll = false,
  replace = false,
  role,
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
  const active = optimistic || serverActive || href === currentHref;

  return (
    <Link
      href={href}
      scroll={scroll}
      replace={replace}
      prefetch
      role={role}
      aria-current={active ? "page" : undefined}
      className={`${baseClass}${active ? " is-active" : ""}`}
      onClick={() => {
        if (href === currentHref) return;
        setOptimistic(true);
        setShopNavigating(true);
        // Do not preventDefault / startTransition — let Link navigate at full
        // priority so the UI reacts on the same tap.
      }}
    >
      {children}
    </Link>
  );
}
