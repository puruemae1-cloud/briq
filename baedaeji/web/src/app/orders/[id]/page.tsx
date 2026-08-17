import { notFound, redirect } from "next/navigation";
import { markPaymentPendingAction } from "@/app/actions/orders";
import { getCurrentUser } from "@/lib/auth";
import { readOnlyDb } from "@/lib/db";
import { formatDate } from "@/lib/format";
import { formatGbp, formatKrw, quoteKrw, feePolicySummary } from "@/lib/fx";
import { ORDER_STATUS_LABEL } from "@/lib/types";
import { cartLinkLabel } from "@/lib/product-input";
import { QuoteFeeBreakdown } from "@/components/QuoteFeeBreakdown";

export default async function OrderDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const me = await getCurrentUser();
  if (!me) redirect("/login");
  const { id } = await params;
  const db = await readOnlyDb();
  const order = db.orders.find((o) => o.id === id);
  if (!order) notFound();
  if (order.userId !== me.id && me.role !== "admin") notFound();

  const expired = Boolean(order.quotedUntil && new Date(order.quotedUntil) < new Date());
  const canPay = order.status === "quoted" && !expired && order.quotedKrw;
  const breakdown = order.goodsGbp
    ? quoteKrw({
        goodsGbp: order.goodsGbp,
        gbpKrw: order.fx.gbpKrw,
        shippingKrw: order.fees.shippingEstKrw,
        agencyRate: order.fees.agencyRate,
      })
    : null;

  return (
    <div className="page-wrap py-12">
      <p className="text-sm text-[var(--muted)]">{order.number}</p>
      <h1 className="display mt-1 text-4xl">{ORDER_STATUS_LABEL[order.status]}</h1>
      <p className="mt-2 text-sm text-[var(--muted)]">
        {formatDate(order.createdAt)}
        {order.quotedUntil ? ` · 견적 유효 ${formatDate(order.quotedUntil)}` : ""}
      </p>

      <div className="mt-8 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="grid gap-3">
          {order.items.map((item) => (
            <article key={item.id} className="card p-4">
              <p className="text-[0.7rem] tracking-[0.14em] uppercase text-[var(--muted)]">
                {item.storeName}
              </p>
              <p className="mt-1 font-medium">{item.title}</p>
              <p className="mt-1 text-sm text-[var(--muted)]">
                {item.size || "—"} / {item.color || "—"} / {item.qty}개
                {item.gbpPrice ? ` / ${formatGbp(item.gbpPrice)}` : ""}
              </p>
              {item.memo ? <p className="mt-2 text-sm">메모: {item.memo}</p> : null}
              <a href={item.url} className="mt-2 inline-block text-sm underline" target="_blank" rel="noopener noreferrer">
                {cartLinkLabel(item.url, item.storeName, item.source)}
              </a>
            </article>
          ))}
        </div>
        <aside className="card p-5">
          <p className="text-sm">£1 = {formatKrw(order.fx.gbpKrw)} · {order.fx.source}</p>
          <p className="mt-2 text-sm text-[var(--muted)]">{feePolicySummary()}</p>
          <p className="mt-2">상품 {order.goodsGbp ? formatGbp(order.goodsGbp) : "확인 중"}</p>
          {breakdown ? (
            <div className="mt-4">
              <QuoteFeeBreakdown quote={breakdown} totalClassName="display text-2xl" />
            </div>
          ) : (
            <p className="display mt-4 text-3xl">
              {order.quotedKrw ? formatKrw(order.quotedKrw) : "운영자 견적 대기"}
            </p>
          )}
          <p className="mt-4 text-sm leading-6">
            {order.customer.name} · {order.customer.phone}
            <br />
            {order.customer.address}
          </p>
          {canPay ? (
            <form action={markPaymentPendingAction.bind(null, order.id)} className="mt-6">
              <button className="btn w-full" type="submit">
                결제하기 (입금 대기)
              </button>
              <p className="mt-3 text-sm text-[var(--muted)]">
                PG·네이버페이는 아직 연결 전입니다. 버튼을 누르면 운영자에게 입금 대기로
                표시됩니다.
              </p>
            </form>
          ) : null}
          {expired && order.status === "quoted" ? (
            <p className="mt-4 text-sm text-[var(--red)]">견적 유효 시간이 지났습니다. 운영자에게 재견적을 요청하세요.</p>
          ) : null}
        </aside>
      </div>
    </div>
  );
}
