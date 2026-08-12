"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

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
        if (pathname !== "/") return;
        e.preventDefault();
        window.scrollTo(0, 0);
      }}
    >
      {children}
    </Link>
  );
}
