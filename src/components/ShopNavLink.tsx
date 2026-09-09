"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useTransition } from "react";

type Props = {
  href: string;
  className?: string;
  children: React.ReactNode;
  scroll?: boolean;
  replace?: boolean;
  role?: string;
};

export function ShopNavLink({
  href,
  className,
  children,
  scroll = false,
  replace = false,
  role,
}: Props) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();
  const currentHref = `${pathname}${searchParams.toString() ? `?${searchParams.toString()}` : ""}`;
  const pending = isPending && href !== currentHref;

  return (
    <Link
      href={href}
      scroll={scroll}
      replace={replace}
      prefetch
      role={role}
      aria-busy={pending || undefined}
      className={`${className ?? ""}${pending ? " is-pending" : ""}`}
      onClick={(e) => {
        if (href === currentHref) return;
        e.preventDefault();
        startTransition(() => {
          if (replace) router.replace(href, { scroll });
          else router.push(href, { scroll });
        });
      }}
    >
      {children}
    </Link>
  );
}
