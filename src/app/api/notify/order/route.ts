import { NextResponse } from "next/server";
import { mailDocument, sendMail } from "@/lib/email";
import { INCLUDED_SHIPPING_NOTE } from "@/lib/orders";

export const runtime = "nodejs";

/**
 * Payment / order notification.
 * Call from CheckoutClient after a successful payment (demo or live PG).
 */
type OrderLine = {
  nameKo?: string;
  qty?: number;
  unitPrice?: number;
};

type Body = {
  orderId?: string;
  paymentId?: string;
  paymentMethod?: string;
  customerName?: string;
  customerPhone?: string;
  customerEmail?: string;
  address?: string;
  zonecode?: string;
  addressBase?: string;
  addressDetail?: string;
  customsCode?: string;
  subtotalKrw?: number;
  discountKrw?: number;
  shippingFeeKrw?: number;
  shippingNote?: string;
  totalKrw?: number;
  lines?: OrderLine[];
};

export async function POST(req: Request) {
  let body: Body;
  try {
    body = (await req.json()) as Body;
  } catch {
    return NextResponse.json({ ok: false, message: "잘못된 요청입니다." }, { status: 400 });
  }

  const orderId = body.orderId?.trim();
  const paymentId = body.paymentId?.trim();
  const customerName = body.customerName?.trim();
  const totalKrw = Number(body.totalKrw);

  if (!orderId || !paymentId || !customerName || !Number.isFinite(totalKrw)) {
    return NextResponse.json(
      { ok: false, message: "필수 주문 정보가 누락되었습니다." },
      { status: 400 },
    );
  }

  const linesText =
    body.lines
      ?.map((l) => {
        const qty = l.qty ?? 1;
        const price = l.unitPrice ?? 0;
        return `· ${l.nameKo ?? "상품"} × ${qty} · ${price.toLocaleString("ko-KR")}원`;
      })
      .join("\n") || "-";

  const shippingFee = Number(body.shippingFeeKrw);
  const shippingFeeLabel = Number.isFinite(shippingFee)
    ? `${shippingFee.toLocaleString("ko-KR")}원`
    : "0원";
  const shippingNote = body.shippingNote?.trim() || INCLUDED_SHIPPING_NOTE;
  const addressParts = [
    body.zonecode?.trim() ? `[${body.zonecode.trim()}]` : "",
    body.addressBase?.trim() || "",
    body.addressDetail?.trim() || "",
  ]
    .filter(Boolean)
    .join(" ");

  const subject = `[Briq 결제완료] ${orderId} · ${totalKrw.toLocaleString("ko-KR")}원`;
  const rows = [
    { label: "주문번호", value: orderId },
    { label: "결제 ID", value: paymentId },
    { label: "결제수단", value: body.paymentMethod?.trim() || "-" },
    {
      label: "상품합계",
      value: Number.isFinite(Number(body.subtotalKrw))
        ? `${Number(body.subtotalKrw).toLocaleString("ko-KR")}원`
        : "-",
    },
    {
      label: "쿠폰할인",
      value: Number.isFinite(Number(body.discountKrw))
        ? `-${Number(body.discountKrw).toLocaleString("ko-KR")}원`
        : "-",
    },
    { label: "배송비", value: `${shippingFeeLabel} · ${shippingNote}` },
    { label: "결제금액", value: `${totalKrw.toLocaleString("ko-KR")}원` },
    { label: "수취인", value: customerName },
    { label: "연락처", value: body.customerPhone?.trim() || "-" },
    { label: "이메일", value: body.customerEmail?.trim() || "-" },
    { label: "배송지", value: addressParts || body.address?.trim() || "-" },
    { label: "개인통관부호", value: body.customsCode?.trim() || "-" },
    { label: "상품", value: linesText },
  ];

  const mail = await sendMail({
    subject,
    text: rows.map((r) => `${r.label}: ${r.value}`).join("\n"),
    html: mailDocument("결제 완료 알림", rows),
    replyTo: body.customerEmail?.trim() || undefined,
  });

  return NextResponse.json({
    ok: true,
    mailed: mail.ok,
    mailMode: mail.mode,
    mailMessage: mail.ok ? undefined : mail.message,
  });
}
