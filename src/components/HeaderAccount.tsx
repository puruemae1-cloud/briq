"use client";

import Link from "next/link";
import { UserRound } from "lucide-react";
import { useAuthStore } from "@/lib/auth-store";

export function HeaderAccount() {
  const user = useAuthStore((s) => s.currentUser());

  return (
    <Link
      href={user ? "/account" : "/account/login"}
      className="icon-btn account-btn"
      aria-label={user ? "마이페이지" : "로그인"}
      title={user ? user.name : "로그인"}
    >
      <UserRound size={20} />
      {user ? <span className="account-btn__dot" aria-hidden /> : null}
    </Link>
  );
}
