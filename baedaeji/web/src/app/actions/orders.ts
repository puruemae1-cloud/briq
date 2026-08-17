"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { getCurrentUser } from "@/lib/auth";
import { updateDb } from "@/lib/db";
import { FEE, type Order, type OrderStatus } from "@/lib/types";
import { getGbpKrw, quoteKrw } from "@/lib/fx";

export async function requestQuoteAction() {
  const me = await getCurrentUser();
  if (!me) redirect("/login?next=/cart");
  if (!me.address || !me.phone) {
    redirect("/account?need=shipping");
  }

  const fx = await getGbpKrw();
  const order = await updateDb((db) => {
    const items = db.carts[me.id] ?? [];
    if (items.length === 0) throw new Error("empty");
    const priced = items.every((i) => i.gbpPrice && i.gbpPrice > 0);
    const goodsGbp = priced
      ? items.reduce((sum, i) => sum + (i.gbpPrice ?? 0) * i.qty, 0)
      : null;
    const breakdown =
      goodsGbp !== null ? quoteKrw({ goodsGbp, gbpKrw: fx.gbpKrw }) : null;
    const now = new Date();
    const quotedUntil = new Date(now.getTime() + FEE.quoteTtlHours * 60 * 60 * 1000).toISOString();
    const next: Order = {
      id: crypto.randomUUID(),
      number: `BD-${1001 + db.orders.length}`,
      userId: me.id,
      customer: {
        name: me.name,
        email: me.email,
        phone: me.phone,
        address: me.address,
        customsCode: me.customsCode,
      },
      items: items.map((i) => ({ ...i })),
      fx: {
        gbpKrw: fx.gbpKrw,
        source: fx.source,
        fetchedAt: fx.fetchedAt,
        margin: FEE.fxMargin,
      },
      fees: {
        agencyRate: FEE.agencyRate,
        shippingEstKrw: breakdown?.shippingKrw ?? FEE.shippingKrw,
      },
      goodsGbp,
      quotedKrw: breakdown?.totalKrw ?? null,
      quotedUntil: breakdown ? quotedUntil : null,
      status: priced ? "quoted" : "needs_price",
      adminNote: "",
      createdAt: now.toISOString(),
      updatedAt: now.toISOString(),
    };
    db.orders.unshift(next);
    db.carts[me.id] = [];
    return next;
  }).catch((err: unknown) => {
    if (err instanceof Error && err.message === "empty") return null;
    throw err;
  });

  if (!order) redirect("/cart");
  redirect(`/orders/${order.id}`);
}

export async function markPaymentPendingAction(orderId: string) {
  const me = await getCurrentUser();
  if (!me) redirect("/login");
  await updateDb((db) => {
    const order = db.orders.find((o) => o.id === orderId && o.userId === me.id);
    if (!order) return;
    if (order.status !== "quoted") return;
    if (order.quotedUntil && new Date(order.quotedUntil) < new Date()) return;
    order.status = "payment_pending";
    order.updatedAt = new Date().toISOString();
  });
  revalidatePath(`/orders/${orderId}`);
  revalidatePath("/admin");
}

export async function adminUpdateOrderAction(orderId: string, formData: FormData) {
  const me = await getCurrentUser();
  if (!me || me.role !== "admin") throw new Error("forbidden");

  const status = String(formData.get("status") || "") as OrderStatus;
  const adminNote = String(formData.get("adminNote") || "");
  const gbpRaw = String(formData.get("goodsGbp") || "").trim();
  const shippingRaw = String(formData.get("shippingEstKrw") || "").trim();

  const fx = await getGbpKrw();

  await updateDb((db) => {
    const order = db.orders.find((o) => o.id === orderId);
    if (!order) return;
    if (gbpRaw) {
      const goodsGbp = Number(gbpRaw);
      if (Number.isFinite(goodsGbp) && goodsGbp > 0) {
        order.goodsGbp = goodsGbp;
        const q = quoteKrw({
          goodsGbp,
          gbpKrw: fx.gbpKrw,
          shippingKrw: shippingRaw ? Number(shippingRaw) : undefined,
        });
        order.fx = {
          gbpKrw: fx.gbpKrw,
          source: fx.source,
          fetchedAt: fx.fetchedAt,
          margin: FEE.fxMargin,
        };
        order.fees.shippingEstKrw = q.shippingKrw;
        order.quotedKrw = q.totalKrw;
        order.quotedUntil = new Date(Date.now() + FEE.quoteTtlHours * 60 * 60 * 1000).toISOString();
        if (order.status === "needs_price") order.status = "quoted";
      }
    }
    if (shippingRaw && Number.isFinite(Number(shippingRaw)) && order.goodsGbp) {
      const q = quoteKrw({
        goodsGbp: order.goodsGbp,
        gbpKrw: order.fx.gbpKrw,
        shippingKrw: Number(shippingRaw),
      });
      order.fees.shippingEstKrw = q.shippingKrw;
      order.quotedKrw = q.totalKrw;
    }
    if (status && status in {
      needs_price: 1,
      quoted: 1,
      payment_pending: 1,
      paid: 1,
      buying_uk: 1,
      purchased: 1,
      in_warehouse: 1,
      shipped: 1,
      customs: 1,
      delivered: 1,
      cancelled_refund: 1,
    }) {
      order.status = status;
    }
    order.adminNote = adminNote;
    order.updatedAt = new Date().toISOString();
  });
  revalidatePath("/admin");
  revalidatePath(`/orders/${orderId}`);
}
