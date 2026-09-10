"use client";

import Link from "next/link";
import { AccountNav } from "@/components/AccountNav";
import { formatKrw } from "@/data/products";
import { useAuthStore } from "@/lib/auth-store";
import { useCouponStore } from "@/lib/coupon-store";

export function AccountCoupons() {
  const user = useAuthStore((s) => s.currentUser());
  const coupons = useCouponStore((s) => s.coupons);

  if (!user) {
    return (
      <section className="section account-shell">
        <div className="panel account-gate">
          <h1>쿠폰함</h1>
          <p>로그인 후 리뷰 쿠폰을 확인할 수 있습니다.</p>
          <Link
            href="/account/login?next=/account/coupons"
            className="btn btn-solid"
          >
            로그인
          </Link>
        </div>
      </section>
    );
  }

  const mine = coupons
    .filter(
      (c) =>
        c.userId === user.id ||
        c.ownerEmail === user.email.toLowerCase(),
    )
    .sort((a, b) => +new Date(b.createdAt) - +new Date(a.createdAt));

  const available = mine.filter((c) => c.status === "available");

  return (
    <section className="section account-shell">
      <div className="account-layout">
        <AccountNav />
        <div className="account-main">
          <header className="account-main__head">
            <p className="product-card__brand">Coupons</p>
            <h1>쿠폰함</h1>
            <p className="account-main__email">
              사용 가능 {available.length}장 · 전체 {mine.length}장
            </p>
          </header>

          <div className="coupon-wallet__hero">
            <p className="coupon-wallet__hero-label">리뷰 감사 혜택</p>
            <p className="coupon-wallet__hero-copy">
              텍스트 리뷰 {formatKrw(3000)} · 포토·영상 리뷰 {formatKrw(5000)}.
              다음 결제 시 자동으로 선택할 수 있습니다.
            </p>
          </div>

          <ul className="coupon-wallet">
            {mine.length === 0 ? (
              <li className="engage-empty">
                아직 쿠폰이 없습니다. 상품 리뷰를 작성하면 자동 지급됩니다.
              </li>
            ) : (
              mine.map((c) => (
                <li
                  key={c.id}
                  className={`coupon-card${c.status === "used" ? " is-used" : ""}`}
                >
                  <div>
                    <p className="coupon-card__amount">{formatKrw(c.amountKrw)}</p>
                    <p className="coupon-card__label">{c.label}</p>
                    <p className="coupon-card__meta">{c.productName}</p>
                  </div>
                  <div className="coupon-card__side">
                    <span className="coupon-card__status">
                      {c.status === "available" ? "사용 가능" : "사용 완료"}
                    </span>
                    <time dateTime={c.createdAt}>
                      {new Intl.DateTimeFormat("ko-KR").format(
                        new Date(c.createdAt),
                      )}
                    </time>
                  </div>
                </li>
              ))
            )}
          </ul>

          {available.length > 0 ? (
            <Link href="/cart" className="btn btn-solid">
              장바구니에서 사용하기
            </Link>
          ) : null}
        </div>
      </div>
    </section>
  );
}
