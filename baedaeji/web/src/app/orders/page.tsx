import Link from "next/link";
import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth";
import { readOnlyDb } from "@/lib/db";
import { formatDate } from "@/lib/format";
import { formatKrw } from "@/lib/fx";
import { ORDER_STATUS_LABEL } from "@/lib/types";

export default async function OrdersPage() {
  const me = await getCurrentUser();
  if (!me) redirect("/login?next=/orders");
  const db = await readOnlyDb();
  const orders = db.orders.filter((o) => o.userId === me.id);

  return (
    <div className="page-wrap py-12">
      <h1 className="display text-4xl">내 주문</h1>
      <div className="mt-8 grid gap-3">
        {orders.length === 0 ? (
          <p className="card p-6 text-sm text-[var(--muted)]">아직 견적 요청이 없습니다.</p>
        ) : (
          orders.map((order) => (
            <Link key={order.id} href={`/orders/${order.id}`} className="card flex items-center justify-between gap-4 p-5">
              <div>
                <p className="text-sm text-[var(--muted)]">{order.number}</p>
                <p className="mt-1 font-medium">
                  {order.items[0]?.title ?? "주문"}
                  {order.items.length > 1 ? ` 외 ${order.items.length - 1}건` : ""}
                </p>
                <p className="mt-1 text-sm text-[var(--muted)]">{formatDate(order.createdAt)}</p>
              </div>
              <div className="text-right">
                <p>{ORDER_STATUS_LABEL[order.status]}</p>
                <p className="display text-xl">
                  {order.quotedKrw ? formatKrw(order.quotedKrw) : "견적 대기"}
                </p>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
