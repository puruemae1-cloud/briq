import { NextResponse } from "next/server";
import { mailDocument, sendMail } from "@/lib/email";
import { addQa, answerQa, listQa } from "@/lib/qa-inbox";
import { isStaffRequest } from "@/lib/qa-staff";
import type { QaItem, QaVisibility } from "@/lib/qa-store";
import { getSiteUrl } from "@/lib/site";

export const runtime = "nodejs";

function viewItem(item: QaItem, staff: boolean): QaItem | null {
  const visibility: QaVisibility = item.visibility === "private" ? "private" : "public";
  if (visibility === "private" && !staff) return null;
  return {
    id: item.id,
    productId: item.productId,
    productName: item.productName,
    authorName: item.authorName,
    authorEmail: staff ? item.authorEmail : undefined,
    authorPhone: staff ? item.authorPhone : undefined,
    question: item.question,
    visibility,
    createdAt: item.createdAt,
    answer: item.answer,
    answeredAt: item.answeredAt,
    answeredBy: item.answeredBy,
  };
}

function cleanEmail(value: unknown): string | undefined | null {
  if (value == null || value === "") return undefined;
  if (typeof value !== "string") return null;
  const email = value.trim().toLowerCase();
  if (!email) return undefined;
  if (email.length > 200 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return null;
  return email;
}

export async function GET(req: Request) {
  const staff = isStaffRequest(req);
  const productId = new URL(req.url).searchParams.get("productId")?.trim();
  const items = (await listQa()).flatMap((item) => {
    const view = viewItem(item, staff);
    return view ? [view] : [];
  });
  const filtered = productId
    ? items.filter((item) => item.productId === productId)
    : items;
  return NextResponse.json({ ok: true, items: filtered });
}

export async function POST(req: Request) {
  let body: {
    productId?: string;
    productName?: string;
    authorName?: string;
    authorEmail?: string;
    question?: string;
    visibility?: string;
  };
  try {
    body = (await req.json()) as typeof body;
  } catch {
    return NextResponse.json({ ok: false, message: "잘못된 요청입니다." }, { status: 400 });
  }

  const productId = body.productId?.trim();
  const productName = body.productName?.trim();
  const authorName = body.authorName?.trim() || "고객";
  const question = body.question?.trim();
  const visibility: QaVisibility = body.visibility === "private" ? "private" : "public";
  const authorEmail = cleanEmail(body.authorEmail);

  if (!productId || !productName || !question) {
    return NextResponse.json(
      { ok: false, message: "문의 내용을 입력해 주세요." },
      { status: 400 },
    );
  }
  if (question.length > 2000 || authorName.length > 80) {
    return NextResponse.json(
      { ok: false, message: "질문은 2000자 이내로 작성해 주세요." },
      { status: 400 },
    );
  }
  if (authorEmail === null) {
    return NextResponse.json(
      { ok: false, message: "이메일 형식을 확인해 주세요." },
      { status: 400 },
    );
  }

  const item: QaItem = {
    id: `qa-${Date.now()}`,
    productId,
    productName,
    authorName,
    authorEmail,
    question,
    visibility,
    createdAt: new Date().toISOString(),
  };
  await addQa(item);

  const productUrl = `${getSiteUrl()}/product/${encodeURIComponent(productId)}`;
  const rows = [
    { label: "상품", value: productName },
    { label: "상품 페이지", value: productUrl },
    { label: "공개여부", value: visibility === "private" ? "비밀글" : "공개" },
    { label: "작성자", value: authorName },
    { label: "이메일", value: authorEmail || "-" },
    { label: "질문", value: question },
  ];
  const mail = await sendMail({
    subject: `[Briq 상품문의] ${visibility === "private" ? "비밀 · " : ""}${productName}`,
    text: rows.map((row) => `${row.label}: ${row.value}`).join("\n"),
    html: mailDocument("새 상품문의", rows),
    replyTo: authorEmail,
  });

  const staff = isStaffRequest(req);
  const items = (await listQa()).flatMap((row) => {
    const view = viewItem(row, staff);
    return view ? [view] : [];
  });
  return NextResponse.json({
    ok: true,
    item: viewItem(item, true),
    items,
    mailed: mail.ok,
  });
}

export async function PATCH(req: Request) {
  if (!isStaffRequest(req)) {
    return NextResponse.json(
      { ok: false, message: "답변은 관리자만 등록할 수 있습니다." },
      { status: 401 },
    );
  }

  let body: { id?: string; answer?: string; answeredBy?: string };
  try {
    body = (await req.json()) as typeof body;
  } catch {
    return NextResponse.json({ ok: false, message: "잘못된 요청입니다." }, { status: 400 });
  }

  const id = body.id?.trim();
  const answer = body.answer?.trim();
  const answeredBy = body.answeredBy?.trim() || "Briq";
  if (!id || !answer) {
    return NextResponse.json(
      { ok: false, message: "답변 내용을 입력해 주세요." },
      { status: 400 },
    );
  }
  if (answer.length > 2000) {
    return NextResponse.json(
      { ok: false, message: "답변은 2000자 이내로 작성해 주세요." },
      { status: 400 },
    );
  }

  const updated = await answerQa(id, answer, answeredBy);
  if (!updated) {
    return NextResponse.json(
      { ok: false, message: "문의를 찾을 수 없습니다." },
      { status: 404 },
    );
  }
  const items = (await listQa()).flatMap((row) => {
    const view = viewItem(row, true);
    return view ? [view] : [];
  });
  return NextResponse.json({ ok: true, item: viewItem(updated, true), items });
}
