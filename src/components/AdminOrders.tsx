"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { AccountNav } from "@/components/AccountNav";
import { formatKrw } from "@/data/products";
import { isAdminUser, useAuthStore } from "@/lib/auth-store";
import {
  INCLUDED_SHIPPING_NOTE,
  SHIPPING_STAGE_COPY,
  SHIPPING_STAGES,
  type MemberOrder,
  type ShippingStage,
} from "@/lib/orders";
import { useOrderStore } from "@/lib/order-store";

export function AdminOrders() {
  const ensureAdminSeeded = useAuthStore((s) => s.ensureAdminSeeded);
  const user = useAuthStore((s) => s.currentUser());
  const localOrders = useOrderStore((s) => s.orders);
  const mergeOrders = useOrderStore((s) => s.mergeOrders);
  const setTracking = useOrderStore((s) => s.setTracking);
  const setStatus = useOrderStore((s) => s.setStatus);

  const [filter, setFilter] = useState<"all" | "paid" | "shipping">("all");
  const [drafts, setDrafts] = useState<
    Record<string, { status: ShippingStage; tracking: string }>
  >({});
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    ensureAdminSeeded();
  }, [ensureAdminSeeded]);

  useEffect(() => {
    let cancelled = false;
    async function syncInbox() {
      setSyncing(true);
      try {
        const res = await fetch("/api/orders");
        if (!res.ok) return;
        const data = (await res.json()) as { orders?: MemberOrder[] };
        if (!cancelled && data.orders?.length) {
          mergeOrders(data.orders);
        }
      } catch {
        /* keep local orders */
      } finally {
        if (!cancelled) setSyncing(false);
      }
    }
    void syncInbox();
    return () => {
      cancelled = true;
    };
  }, [mergeOrders]);

  const orders = useMemo(() => {
    const sorted = [...localOrders].sort(
      (a, b) => +new Date(b.createdAt) - +new Date(a.createdAt),
    );
    if (filter === "paid") return sorted.filter((o) => o.status === "paid");
    if (filter === "shipping") {
      return sorted.filter((o) => o.status !== "paid" && o.status !== "delivered");
    }
    return sorted;
  }, [localOrders, filter]);

  function draftFor(order: MemberOrder) {
    return (
      drafts[order.id] ?? {
        status: order.status,
        tracking: order.trackingNumber ?? "",
      }
    );
  }

  async function onSaveFulfillment(e: FormEvent, order: MemberOrder) {
    e.preventDefault();
    setError(null);
    setNotice(null);
    const draft = draftFor(order);
    const tracking = draft.tracking.trim();

    if (tracking) {
      setTracking(order.id, tracking, draft.status);
    } else {
      setStatus(order.id, draft.status);
    }

    try {
      const res = await fetch("/api/orders", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          orderId: order.id,
          status: draft.status,
          trackingNumber: tracking,
        }),
      });
      if (res.ok) {
        const data = (await res.json()) as { order?: MemberOrder };
        if (data.order) mergeOrders([data.order]);
      }
    } catch {
      /* local update already applied */
    }

    setNotice(`${order.id} 배송 정보가 저장되었습니다.`);
  }

  if (!user) {
    return (
      <section className="section account-shell">
        <div className="panel account-gate">
          <h1>관리자 로그인 필요</h1>
          <p>주문 이력은 관리자 계정으로 로그인한 뒤 확인할 수 있습니다.</p>
          <Link
            href="/account/login?next=/account/admin/orders"
            className="btn btn-solid"
          >
            로그인
          </Link>
        </div>
      </section>
    );
  }

  if (!isAdminUser(user)) {
    return (
      <section className="section account-shell">
        <div className="panel account-gate">
          <h1>접근 권한이 없습니다</h1>
          <p>주문 관리는 관리자만 이용할 수 있습니다.</p>
          <Link href="/account" className="btn btn-outline">
            마이페이지
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
            <p className="product-card__brand">Admin</p>
            <h1>주문 이력</h1>
            <p className="account-main__email">
              고객 정보 · 배송지 · 배송비 · 결제 내역을 확인합니다
              {syncing ? " · 동기화 중…" : ""}
            </p>
          </header>

          <div className="admin-orders__filters" role="tablist">
            {(
              [
                { id: "all", label: "전체" },
                { id: "paid", label: "결제완료" },
                { id: "shipping", label: "배송중" },
              ] as const
            ).map((tab) => (
              <button
                key={tab.id}
                type="button"
                role="tab"
                aria-selected={filter === tab.id}
                className={`admin-orders__filter${filter === tab.id ? " is-active" : ""}`}
                onClick={() => setFilter(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {notice ? <p className="admin-orders__notice">{notice}</p> : null}
          {error ? <p className="admin-orders__error">{error}</p> : null}

          {orders.length === 0 ? (
            <div className="panel">
              <p>아직 인입된 주문이 없습니다.</p>
              <p className="admin-orders__hint">
                결제 완료 시 이 목록과 서버 인박스에 자동 기록됩니다.
              </p>
            </div>
          ) : (
            <div className="account-order-list">
              {orders.map((order) => {
                const draft = draftFor(order);
                const shippingFee = order.shippingFeeKrw ?? 0;
                const subtotal = order.subtotalKrw ?? order.totalKrw;
                const discount = order.discountKrw ?? 0;
                return (
                  <article key={order.id} className="panel admin-order">
                    <div className="account-order__top">
                      <div>
                        <p className="account-order__id">{order.id}</p>
                        <p className="account-order__date">
                          {new Date(order.createdAt).toLocaleString("ko-KR")}
                          {order.userId ? " · 회원" : " · 비회원"}
                        </p>
                      </div>
                      <p className="account-order__status">
                        {SHIPPING_STAGE_COPY[order.status].title}
                      </p>
                    </div>

                    <div className="admin-order__grid">
                      <section>
                        <h2>고객 정보</h2>
                        <dl className="admin-order__dl">
                          <div>
                            <dt>수취인</dt>
                            <dd>{order.customerName}</dd>
                          </div>
                          <div>
                            <dt>연락처</dt>
                            <dd>{order.customerPhone}</dd>
                          </div>
                          <div>
                            <dt>이메일</dt>
                            <dd>{order.customerEmail || "—"}</dd>
                          </div>
                          <div>
                            <dt>개인통관부호</dt>
                            <dd>{order.customsCode}</dd>
                          </div>
                        </dl>
                      </section>

                      <section>
                        <h2>배송 정보</h2>
                        <dl className="admin-order__dl">
                          <div>
                            <dt>우편번호</dt>
                            <dd>{order.zonecode || "—"}</dd>
                          </div>
                          <div>
                            <dt>기본주소</dt>
                            <dd>{order.addressBase || order.address}</dd>
                          </div>
                          <div>
                            <dt>상세주소</dt>
                            <dd>{order.addressDetail || "—"}</dd>
                          </div>
                          <div>
                            <dt>배송비</dt>
                            <dd>
                              {formatKrw(shippingFee)}
                              <span className="admin-order__ship-note">
                                {order.shippingNote || INCLUDED_SHIPPING_NOTE}
                              </span>
                            </dd>
                          </div>
                          <div>
                            <dt>택배</dt>
                            <dd>
                              {order.carrier === "ACI_EXPRESS"
                                ? "ACI EXPRESS"
                                : "미지정"}
                              {order.trackingNumber
                                ? ` · ${order.trackingNumber}`
                                : " · 송장 대기"}
                            </dd>
                          </div>
                        </dl>
                      </section>

                      <section>
                        <h2>결제</h2>
                        <dl className="admin-order__dl">
                          <div>
                            <dt>결제수단</dt>
                            <dd>{order.paymentMethod}</dd>
                          </div>
                          <div>
                            <dt>결제 ID</dt>
                            <dd>{order.paymentId}</dd>
                          </div>
                          <div>
                            <dt>상품합계</dt>
                            <dd>{formatKrw(subtotal)}</dd>
                          </div>
                          <div>
                            <dt>쿠폰할인</dt>
                            <dd>-{formatKrw(discount)}</dd>
                          </div>
                          <div>
                            <dt>배송비</dt>
                            <dd>{formatKrw(shippingFee)}</dd>
                          </div>
                          <div>
                            <dt>결제금액</dt>
                            <dd>
                              <strong>{formatKrw(order.totalKrw)}</strong>
                            </dd>
                          </div>
                        </dl>
                      </section>
                    </div>

                    <ul className="account-order__lines">
                      {order.lines.map((line) => (
                        <li
                          key={`${order.id}-${line.productId}-${line.variantId ?? "d"}-${line.nameKo}`}
                        >
                          <span>
                            {line.nameKo} × {line.qty}
                          </span>
                          <strong>
                            {formatKrw(line.unitPrice * line.qty)}
                          </strong>
                        </li>
                      ))}
                    </ul>

                    <form
                      className="admin-order__fulfill"
                      onSubmit={(e) => onSaveFulfillment(e, order)}
                    >
                      <label>
                        배송 단계
                        <select
                          value={draft.status}
                          onChange={(e) =>
                            setDrafts((d) => ({
                              ...d,
                              [order.id]: {
                                ...draftFor(order),
                                status: e.target.value as ShippingStage,
                              },
                            }))
                          }
                        >
                          {SHIPPING_STAGES.map((stage) => (
                            <option key={stage} value={stage}>
                              {SHIPPING_STAGE_COPY[stage].title}
                            </option>
                          ))}
                        </select>
                      </label>
                      <label>
                        ACI EXPRESS 송장번호
                        <input
                          type="text"
                          value={draft.tracking}
                          placeholder="송장번호 입력"
                          onChange={(e) =>
                            setDrafts((d) => ({
                              ...d,
                              [order.id]: {
                                ...draftFor(order),
                                tracking: e.target.value,
                              },
                            }))
                          }
                        />
                      </label>
                      <button type="submit" className="btn btn-solid">
                        저장
                      </button>
                    </form>
                  </article>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
