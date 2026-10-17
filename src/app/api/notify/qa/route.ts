import { NextResponse } from "next/server";
import { mailDocument, sendMail } from "@/lib/email";

export const runtime = "nodejs";

type Body = {
  productId?: string;
  productName?: string;
  authorName?: string;
  authorEmail?: string;
  authorPhone?: string;
  question?: string;
  visibility?: "public" | "private";
  qaId?: string;
};

export async function POST(req: Request) {
  let body: Body;
  try {
    body = (await req.json()) as Body;
  } catch {
    return NextResponse.json({ ok: false, message: "잘못된 요청입니다." }, { status: 400 });
  }

  const productId = body.productId?.trim();
  const productName = body.productName?.trim();
  const authorName = body.authorName?.trim();
  const question = body.question?.trim();
  const visibility = body.visibility === "private" ? "private" : "public";

  if (!productId || !productName || !authorName || !question) {
    return NextResponse.json(
      { ok: false, message: "필수 항목이 누락되었습니다." },
      { status: 400 },
    );
  }

  if (question.length > 2000) {
    return NextResponse.json(
      { ok: false, message: "질문은 2000자 이내로 작성해 주세요." },
      { status: 400 },
    );
  }

  const subject = `[Briq Q&A] ${visibility === "private" ? "비밀글 · " : ""}${productName}`;
  const rows = [
    { label: "상품", value: `${productName} (${productId})` },
    { label: "공개여부", value: visibility === "private" ? "비밀글" : "공개" },
    { label: "작성자", value: authorName },
    { label: "이메일", value: body.authorEmail?.trim() || "-" },
    { label: "연락처", value: body.authorPhone?.trim() || "-" },
    { label: "질문", value: question },
    { label: "Q&A ID", value: body.qaId?.trim() || "-" },
  ];

  const mail = await sendMail({
    subject,
    text: rows.map((r) => `${r.label}: ${r.value}`).join("\n"),
    html: mailDocument("새 상품 Q&A", rows),
    replyTo: body.authorEmail?.trim() || undefined,
  });

  return NextResponse.json({
    ok: true,
    mailed: mail.ok,
    mailMode: mail.mode,
    mailMessage: mail.ok ? undefined : mail.message,
  });
}
