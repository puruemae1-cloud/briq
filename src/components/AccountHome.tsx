"use client";

import { useMemo } from "react";
import Link from "next/link";
import { AccountNav } from "@/components/AccountNav";
import { formatKrw } from "@/data/products";
import { isAdminUser, useAuthStore } from "@/lib/auth-store";
import { SHIPPING_STAGE_COPY } from "@/lib/orders";
import { useOrderStore } from "@/lib/order-store";
import { useQaStore } from "@/lib/qa-store";

export function AccountHome() {
  const sessionUserId = useAuthStore((s) => s.sessionUserId);
  const users = useAuthStore((s) => s.users);
  const user = useMemo(
    () => users.find((u) => u.id === sessionUserId) ?? null,
    [users, sessionUserId],
  );
  const allOrders = useOrderStore((s) => s.orders);
  const orders = useMemo(
    () => (user ? allOrders.filter((o) => o.userId === user.id) : []),
    [allOrders, user],
  );
  const pendingQa = useQaStore(
    (s) => s.items.reduce((n, i) => (i.answer ? n : n + 1), 0),
  );

  if (!user) {
    return (
      <section className="section account-shell">
        <div className="panel account-gate">
          <p className="product-card__brand">Account</p>
          <h1>마이페이지</h1>
          <p>
            로그인하면 장바구니, 주문·결제이력, 개인통관부호를 한곳에서 확인할 수
            있습니다.
          </p>
          <div className="account-gate__actions">
            <Link href="/account/login" className="btn btn-solid">
              로그인
            </Link>
            <Link href="/account/signup" className="btn btn-outline">
              회원가입
            </Link>
          </div>
        </div>
      </section>
    );
  }

  const latest = orders[0];
  const hasCustoms = Boolean(user.profile?.customsCode);
  const admin = isAdminUser(user);

  return (
    <section className="section account-shell">
      <div className="account-layout">
        <AccountNav />
        <div className="account-main">
          <header className="account-main__head">
            <p className="product-card__brand">
              {admin ? "Briq Admin" : "My Briq"}
            </p>
            <h1>
              {user.name} 님, 환영합니다
              {admin ? " · 관리자" : ""}
            </h1>
            <p className="account-main__email">{user.email}</p>
          </header>

          {admin ? (
            <div className="account-cards">
              <Link href="/account/admin/qa" className="account-card">
                <p className="account-card__label">Q&A 관리</p>
                <p className="account-card__value">{pendingQa}건</p>
                <p className="account-card__hint">미답변 고객 문의</p>
              </Link>
              <Link href="/shop" className="account-card">
                <p className="account-card__label">상품</p>
                <p className="account-card__value">바로가기</p>
                <p className="account-card__hint">상품 페이지에서 바로 답변 가능</p>
              </Link>
            </div>
          ) : (
            <div className="account-cards">
              <Link href="/cart" className="account-card">
                <p className="account-card__label">장바구니</p>
                <p className="account-card__value">바로가기</p>
                <p className="account-card__hint">담아둔 상품을 이어서 결제하세요</p>
              </Link>
              <Link href="/account/orders" className="account-card">
                <p className="account-card__label">주문·결제</p>
                <p className="account-card__value">{orders.length}건</p>
                <p className="account-card__hint">
                  {latest
                    ? `최근: ${SHIPPING_STAGE_COPY[latest.status].title}`
                    : "아직 주문이 없습니다"}
                </p>
              </Link>
              <Link href="/account/coupons" className="account-card">
                <p className="account-card__label">쿠폰함</p>
                <p className="account-card__value">리뷰 혜택</p>
                <p className="account-card__hint">
                  텍스트 3,000원 · 포토·영상 5,000원
                </p>
              </Link>
              <Link href="/account/profile" className="account-card">
                <p className="account-card__label">통관부호</p>
                <p className="account-card__value">
                  {hasCustoms ? "저장됨" : "미등록"}
                </p>
                <p className="account-card__hint">
                  {hasCustoms
                    ? "결제 시 자동으로 불러옵니다"
                    : "한 번 저장하면 다음 결제부터 자동 입력"}
                </p>
              </Link>
            </div>
          )}

          {!admin && latest ? (
            <div className="panel account-latest">
              <p className="account-latest__label">최근 주문</p>
              <p className="account-latest__id">{latest.id}</p>
              <p>
                {SHIPPING_STAGE_COPY[latest.status].title} ·{" "}
                {formatKrw(latest.totalKrw)}
              </p>
              <Link href="/account/orders" className="btn btn-outline">
                전체 주문 보기
              </Link>
            </div>
          ) : null}

          {!admin && !latest ? (
            <div className="panel account-latest">
              <p>아직 주문 이력이 없습니다.</p>
              <Link href="/shop" className="btn btn-solid">
                쇼핑하러 가기
              </Link>
            </div>
          ) : null}

          {admin ? (
            <div className="panel account-latest">
              <p className="account-latest__label">Staff</p>
              <p>
                고객 Q&A 답변은 관리자만 가능합니다. 일반 회원은 문의만 등록할 수
                있습니다.
              </p>
              <Link href="/account/admin/qa" className="btn btn-solid">
                미답변 확인하기
              </Link>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
