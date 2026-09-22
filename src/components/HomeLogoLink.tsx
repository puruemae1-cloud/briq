"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

/**
 * Header Briq mark → home.
 *
 * Soft RSC navigation to `/` waits on the heavy homepage catalogue and can sit
 * on the current page for a long time with no chrome. Leaving other routes uses
 * a full document navigation so the browser moves immediately.
 */
export function HomeLogoLink({
  children,
  className,
  "aria-label": ariaLabel,
}: {
  children: ReactNode;
  className?: string;
  "aria-label"?: string;
}) {
  const pathname = usePathname();

  return (
    <Link
      href="/"
      prefetch
      className={className}
      aria-label={ariaLabel}
      onClick={(e) => {
        if (pathname === "/") {
          e.preventDefault();
          window.scrollTo(0, 0);
          return;
        }
        e.preventDefault();
        document.documentElement.dataset.homeNavigating = "1";
        window.location.assign("/");
      }}
    >
      {children}
    </Link>
  );
}
