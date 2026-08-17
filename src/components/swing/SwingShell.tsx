"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSwingStore } from "@/lib/swing/store";

const links = [
  { href: "/swing", label: "소개", exact: true },
  { href: "/swing/analyze", label: "분석" },
  { href: "/swing/pros", label: "프로" },
  { href: "/swing/coaching", label: "데일리" },
  { href: "/swing/progress", label: "추이" },
  { href: "/swing/materials", label: "자료" },
  { href: "/swing/membership", label: "멤버십" },
];

export function SwingShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const tier = useSwingStore((s) => s.tier);

  return (
    <div className="swing-root">
      <header className="swing-top">
        <Link href="/swing" className="swing-logo">
          <span>Briq Swing</span>
          <em>코칭</em>
        </Link>
        <nav className="swing-nav" aria-label="스윙 코칭">
          {links.map((l) => {
            const active = l.exact
              ? pathname === l.href
              : pathname === l.href || pathname.startsWith(`${l.href}/`);
            return (
              <Link
                key={l.href}
                href={l.href}
                className={active ? "is-active" : undefined}
              >
                {l.label}
              </Link>
            );
          })}
        </nav>
        <div className="swing-top__meta">
          <span className={`swing-pill ${tier === "pro" ? "is-pro" : ""}`}>
            {tier === "pro" ? "유료 회원" : "트라이얼"}
          </span>
          <Link href="/" className="swing-shop">
            Shop
          </Link>
        </div>
      </header>
      {children}
    </div>
  );
}
