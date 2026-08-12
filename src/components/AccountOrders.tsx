"use client";

import { useMemo } from "react";
import Link from "next/link";
import { AccountNav } from "@/components/AccountNav";
import { formatKrw } from "@/data/product-utils";
import { useAuthStore } from "@/lib/auth-store";
import { SHIPPING_STAGE_COPY } from "@/lib/orders";
import { useOrderStore } from "@/lib/order-store";

export function AccountOrders() {
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

  if (!user) {
    return (
      <section className="section">
        <div className="panel account-gate">
          <h1>주문·결제이력</h1>
          <p>로그인 후 확인할 수 있습니다.</p>
          <Link href="/account/login?next=/account/orders" className="btn btn-solid">
            로그인
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="section account-shell">
      <div className="account-layout">
        <AccountNav />
        <div className="account-main">
          <header className="account-main__head">
            <p className="product-card__brand">Orders</p>
            <h1>주문·결제 이력</h1>
          </header>

          {orders.length === 0 ? (
            <div className="panel">
              <p>주문 내역이 없습니다.</p>
              <Link href="/shop" className="btn btn-solid">
                쇼핑하러 가기
              </Link>
            </div>
          ) : (
            <div className="account-order-list">
              {orders.map((order) => (
                <article key={order.id} className="panel account-order">
                  <div className="account-order__top">
                    <div>
                      <p className="account-order__id">{order.id}</p>
                      <p className="account-order__date">
                        {new Date(order.createdAt).toLocaleString("ko-KR")}
                      </p>
                    </div>
                    <p className="account-order__status">
                      {SHIPPING_STAGE_COPY[order.status].title}
                    </p>
                  </div>

                  <ul className="account-order__lines">
                    {order.lines.map((line) => (
                      <li key={`${line.productId}-${line.variantId ?? "d"}`}>
                        <span>
                          {line.nameKo} × {line.qty}
                        </span>
                        <strong>{formatKrw(line.unitPrice * line.qty)}</strong>
                      </li>
                    ))}
                  </ul>

                  <div className="account-order__meta">
                    <p>결제 · {order.paymentMethod}</p>
                    <p>결제 ID · {order.paymentId}</p>
                    {order.address ? <p>배송지 · {order.address}</p> : null}
                    <p>
                      배송비 · {formatKrw(order.shippingFeeKrw ?? 0)}
                      {order.shippingNote ? ` (${order.shippingNote})` : ""}
                    </p>
                    {order.trackingNumber ? (
                      <p>ACI EXPRESS · {order.trackingNumber}</p>
                    ) : (
                      <p>송장번호 · 준비 중</p>
                    )}
                    <p className="account-order__total">
                      합계 {formatKrw(order.totalKrw)}
                    </p>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
