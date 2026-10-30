"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/auth-store";

export function SignupForm() {
  const router = useRouter();
  const signup = useAuthStore((s) => s.signup);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const result = signup({ email, password, name, phone });
    if (!result.ok) {
      setError(result.message);
      return;
    }
    router.push("/account");
  }

  return (
    <form className="panel account-form" onSubmit={onSubmit}>
      <h1 className="account-form__title">회원가입</h1>
      <p className="account-form__lead">
        한 번 가입하면 개인통관부호·주문 이력이 자동으로 연결됩니다.
      </p>

      <div className="field">
        <label htmlFor="signup-name">이름</label>
        <input
          id="signup-name"
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="홍길동"
          autoComplete="name"
        />
      </div>
      <div className="field">
        <label htmlFor="signup-email">이메일</label>
        <input
          id="signup-email"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@email.com"
          autoComplete="email"
        />
      </div>
      <div className="field">
        <label htmlFor="signup-phone">휴대폰 (선택)</label>
        <input
          id="signup-phone"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          placeholder="010-0000-0000"
          autoComplete="tel"
        />
      </div>
      <div className="field">
        <label htmlFor="signup-password">비밀번호</label>
        <input
          id="signup-password"
          type="password"
          required
          minLength={6}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="6자 이상"
          autoComplete="new-password"
        />
      </div>

      {error ? <p className="account-form__error">{error}</p> : null}

      <button type="submit" className="btn btn-solid">
        가입하기
      </button>

      <p className="account-form__switch">
        이미 계정이 있으신가요? <Link href="/account/login">로그인</Link>
      </p>
    </form>
  );
}
