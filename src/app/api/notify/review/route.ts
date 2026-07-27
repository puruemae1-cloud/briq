import { NextResponse } from "next/server";
import { mailDocument, sendMail } from "@/lib/email";

export const runtime = "nodejs";

type Body = {
  productId?: string;
  productName?: string;
  authorName?: string;
  rating?: number;
  body?: string;
  mediaCount?: number;
  reviewId?: string;
};

export async function POST(req: Request) {
  let payload: Body;
  try {
    payload = (await req.json()) as Body;
  } catch {
    return NextResponse.json({ ok: false, message: "잘못된 요청입니다." }, { status: 400 });
  }

  const productId = payload.productId?.trim();
  const productName = payload.productName?.trim();
  const authorName = payload.authorName?.trim();
  const body = payload.body?.trim();
  const rating = Number(payload.rating);

  if (!productId || !productName || !authorName || !body || !rating) {
    return NextResponse.json(
      { ok: false, message: "필수 항목이 누락되었습니다." },
      { status: 400 },
    );
  }

  const subject = `[Briq Review] ★${rating} · ${productName}`;
  const rows = [
    { label: "상품", value: `${productName} (${productId})` },
    { label: "평점", value: `${rating} / 5` },
    { label: "작성자", value: authorName },
    { label: "리뷰", value: body },
    {
      label: "미디어",
      value: `${payload.mediaCount ?? 0}개 첨부 (사이트에서 확인)`,
    },
    { label: "Review ID", value: payload.reviewId?.trim() || "-" },
  ];

  const mail = await sendMail({
    subject,
    text: rows.map((r) => `${r.label}: ${r.value}`).join("\n"),
    html: mailDocument("새 상품 리뷰", rows),
  });

  return NextResponse.json({
    ok: true,
    mailed: mail.ok,
    mailMode: mail.mode,
    mailMessage: mail.ok ? undefined : mail.message,
  });
}
