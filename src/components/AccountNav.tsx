"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuthStore } from "@/lib/auth-store";

const links = [
  { href: "/account", label: "마이페이지", exact: true },
  { href: "/account/orders", label: "주문·배송" },
  { href: "/account/profile", label: "통관·배송정보" },
  { href: "/cart", label: "장바구니" },
];

export function AccountNav() {
  const pathname = usePathname();
  const logout = useAuthStore((s) => s.logout);
  const user = useAuthStore((s) => s.currentUser());

  return (
    <aside className="account-nav">
      <p className="account-nav__hello">
        {user ? (
          <>
            <strong>{user.name}</strong> 님
          </>
        ) : (
          "Account"
        )}
      </p>
      <nav aria-label="마이페이지">
        {links.map((l) => {
          const active = l.exact
            ? pathname === l.href
            : pathname === l.href || pathname.startsWith(`${l.href}/`);
          return (
            <Link
              key={l.href}
              href={l.href}
              className={`account-nav__link${active ? " is-active" : ""}`}
            >
              {l.label}
            </Link>
          );
        })}
      </nav>
      {user ? (
        <button type="button" className="account-nav__logout" onClick={() => logout()}>
          로그아웃
        </button>
      ) : null}
    </aside>
  );
}
