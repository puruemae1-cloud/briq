import { mailDocument, sendMail, SUPPORT_INBOX, type MailResult } from "@/lib/email";
import type { QaItem } from "@/lib/qa-store";
import { getSiteUrl } from "@/lib/site";

export async function mailCustomerReply(item: QaItem, answer: string): Promise<MailResult> {
  if (!item.authorEmail) {
    return { ok: false, mode: "log", message: "고객 이메일이 없습니다." };
  }
  const productUrl = `${getSiteUrl()}/product/${encodeURIComponent(item.productId)}`;
  const greeting = `${item.authorName || "고객"}님, 남겨 주신 문의에 답글을 드립니다.`;
  const rows = [
    { label: "상품", value: item.productName },
    { label: "상품 페이지", value: productUrl },
    { label: "문의", value: item.question },
    { label: "답글", value: answer },
  ];
  const result = await sendMail({
    to: item.authorEmail,
    subject: `[Briq] 문의하신 상품에 답글이 등록되었습니다`,
    text: [greeting, "", ...rows.map((row) => `${row.label}: ${row.value}`)].join("\n"),
    html: mailDocument("문의 답글이 등록되었습니다", [{ label: "안내", value: greeting }, ...rows]),
  });
  if (!result.ok) {
    const reason = result.message;
    const notice = [
      "상품 페이지의 답글은 저장되어 있습니다.",
      "고객이 남긴 주소로는 메일이 전달되지 않았습니다.",
      `사유: ${reason}`,
      "",
      "아래 내용을 고객 주소로 전달해 주세요.",
      `고객: ${item.authorEmail}`,
      ...rows.map((row) => `${row.label}: ${row.value}`),
    ];
    await sendMail({
      to: SUPPORT_INBOX,
      subject: `[Briq] 고객 답글 메일이 전달되지 않았습니다`,
      replyTo: item.authorEmail,
      text: notice.join("\n"),
      html: mailDocument("고객 답글 메일이 전달되지 않았습니다", [
        { label: "사유", value: reason },
        { label: "고객", value: item.authorEmail },
        ...rows,
      ]),
    });
  }
  return result;
}
