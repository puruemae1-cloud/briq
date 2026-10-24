"use client";

import { useMemo } from "react";
import Link from "next/link";
import { UserRound } from "lucide-react";
import { useAuthStore } from "@/lib/auth-store";

export function HeaderAccount() {
  const sessionUserId = useAuthStore((s) => s.sessionUserId);
  const users = useAuthStore((s) => s.users);
  const user = useMemo(
    () => users.find((u) => u.id === sessionUserId) ?? null,
    [users, sessionUserId],
  );

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
