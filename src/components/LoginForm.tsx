"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { ADMIN_EMAIL, useAuthStore } from "@/lib/auth-store";

export function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const login = useAuthStore((s) => s.login);
  const ensureAdminSeeded = useAuthStore((s) => s.ensureAdminSeeded);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    ensureAdminSeeded();
  }, [ensureAdminSeeded]);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const result = login(email, password);
    if (!result.ok) {
      setError(result.message);
      return;
    }
    const normalized = email.trim().toLowerCase();
    const next =
      params.get("next") ||
      (normalized === ADMIN_EMAIL ? "/account/admin/orders" : "/account");
    router.push(next);
  }

  return (
    <form className="panel account-form" onSubmit={onSubmit}>
      <h1 className="account-form__title">로그인</h1>
      <p className="account-form__lead">
        가입 후 장바구니·주문·통관부호를 한곳에서 관리할 수 있습니다.
      </p>

      <div className="field">
        <label htmlFor="login-email">이메일</label>
        <input
          id="login-email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@email.com"
        />
      </div>
      <div className="field">
        <label htmlFor="login-password">비밀번호</label>
        <input
          id="login-password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="6자 이상"
        />
      </div>

      {error ? <p className="account-form__error">{error}</p> : null}

      <button type="submit" className="btn btn-solid">
        로그인
      </button>

      <p className="account-form__switch">
        아직 회원이 아니신가요?{" "}
        <Link href="/account/signup">회원가입</Link>
      </p>
    </form>
  );
}
