import { NextResponse } from "next/server";
import type { MemberOrder, ShippingStage } from "@/lib/orders";
import { SHIPPING_STAGES } from "@/lib/orders";
import {
  listInboxOrders,
  patchInboxOrder,
  upsertInboxOrder,
} from "@/lib/order-inbox";

export const runtime = "nodejs";

function isMemberOrder(value: unknown): value is MemberOrder {
  if (!value || typeof value !== "object") return false;
  const o = value as Record<string, unknown>;
  return (
    typeof o.id === "string" &&
    typeof o.customerName === "string" &&
    typeof o.customerPhone === "string" &&
    typeof o.address === "string" &&
    typeof o.customsCode === "string" &&
    typeof o.totalKrw === "number" &&
    typeof o.paymentMethod === "string" &&
    typeof o.paymentId === "string" &&
    typeof o.createdAt === "string" &&
    Array.isArray(o.lines)
  );
}

export async function GET() {
  const orders = await listInboxOrders();
  return NextResponse.json({ ok: true, orders });
}

export async function POST(req: Request) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ ok: false, message: "잘못된 요청입니다." }, { status: 400 });
  }

  if (!isMemberOrder(body)) {
    return NextResponse.json(
      { ok: false, message: "주문 형식이 올바르지 않습니다." },
      { status: 400 },
    );
  }

  const orders = await upsertInboxOrder(body);
  return NextResponse.json({ ok: true, count: orders.length });
}

export async function PATCH(req: Request) {
  let body: {
    orderId?: string;
    status?: ShippingStage;
    trackingNumber?: string;
  };
  try {
    body = (await req.json()) as typeof body;
  } catch {
    return NextResponse.json({ ok: false, message: "잘못된 요청입니다." }, { status: 400 });
  }

  const orderId = body.orderId?.trim();
  if (!orderId) {
    return NextResponse.json(
      { ok: false, message: "주문번호가 필요합니다." },
      { status: 400 },
    );
  }

  const patch: Partial<MemberOrder> = {};
  if (body.status && SHIPPING_STAGES.includes(body.status)) {
    patch.status = body.status;
  }
  if (typeof body.trackingNumber === "string") {
    const tracking = body.trackingNumber.trim();
    patch.trackingNumber = tracking || undefined;
    if (tracking) patch.carrier = "ACI_EXPRESS";
  }

  const updated = await patchInboxOrder(orderId, patch);
  if (!updated) {
    return NextResponse.json(
      { ok: false, message: "주문을 찾을 수 없습니다." },
      { status: 404 },
    );
  }
  return NextResponse.json({ ok: true, order: updated });
}
