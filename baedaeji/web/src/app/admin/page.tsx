import { redirect } from "next/navigation";
import { adminUpdateOrderAction } from "@/app/actions/orders";
import { getCurrentUser } from "@/lib/auth";
import { readOnlyDb } from "@/lib/db";
import { formatDate } from "@/lib/format";
import { formatGbp, formatKrw } from "@/lib/fx";
import { ORDER_STATUS_LABEL, type OrderStatus } from "@/lib/types";
import { cartLinkLabel } from "@/lib/product-input";

const STATUSES = Object.keys(ORDER_STATUS_LABEL) as OrderStatus[];

export default async function AdminPage() {
  const me = await getCurrentUser();
  if (!me) redirect("/login?next=/admin");
  if (me.role !== "admin") redirect("/");
  const db = await readOnlyDb();

  return (
    <div className="page-wrap py-12">
      <h1 className="display text-4xl">운영 주문</h1>
      <p className="mt-2 text-sm text-[var(--muted)]">
        영국 몰에 자동 로그인하지 않습니다. 검색 링크나 상품 페이지를 열고 직접 구매하세요.
      </p>
      <div className="mt-8 grid gap-6">
        {db.orders.length === 0 ? (
          <p className="card p-6 text-sm">아직 주문이 없습니다.</p>
        ) : (
          db.orders.map((order) => (
            <article key={order.id} className="card p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-sm text-[var(--muted)]">
                    {order.number} · {ORDER_STATUS_LABEL[order.status]} · {formatDate(order.createdAt)}
                  </p>
                  <p className="mt-1 font-medium">
                    {order.customer.name} · {order.customer.email} · {order.customer.phone}
                  </p>
                  <p className="mt-1 text-sm text-[var(--muted)]">{order.customer.address}</p>
                  {order.customer.customsCode ? (
                    <p className="mt-1 text-sm">통관부호 {order.customer.customsCode}</p>
                  ) : null}
                </div>
                <p className="display text-2xl">
                  {order.quotedKrw ? formatKrw(order.quotedKrw) : "미견적"}
                </p>
              </div>
              <ul className="mt-4 grid gap-2 text-sm">
                {order.items.map((item) => (
                  <li key={item.id} className="border-t border-[var(--line)] pt-2">
                    <span className="text-[var(--muted)]">{item.storeName}</span> {item.title} ·{" "}
                    {item.size || "사이즈?"} · {item.qty}개 · {item.gbpPrice ? formatGbp(item.gbpPrice) : "GBP?"}
                    <br />
                    <a href={item.url} className="underline" target="_blank" rel="noopener noreferrer">
                      {cartLinkLabel(item.url, item.storeName, item.source)}
                    </a>
                  </li>
                ))}
              </ul>
              <form action={adminUpdateOrderAction.bind(null, order.id)} className="mt-4 grid gap-3 md:grid-cols-4">
                <label className="field">
                  <span>상태</span>
                  <select name="status" defaultValue={order.status}>
                    {STATUSES.map((s) => (
                      <option key={s} value={s}>
                        {ORDER_STATUS_LABEL[s]}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  <span>상품 GBP 합계</span>
                  <input name="goodsGbp" defaultValue={order.goodsGbp ?? ""} placeholder="89.00" />
                </label>
                <label className="field">
                  <span>배송비 (원)</span>
                  <input name="shippingEstKrw" defaultValue={order.fees.shippingEstKrw} placeholder="20000" />
                </label>
                <label className="field md:col-span-4">
                  <span>운영 메모</span>
                  <textarea name="adminNote" rows={2} defaultValue={order.adminNote} />
                </label>
                <button className="btn md:col-span-4" type="submit">
                  저장 · 견적 갱신
                </button>
              </form>
            </article>
          ))
        )}
      </div>
    </div>
  );
}
