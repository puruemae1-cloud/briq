import { mailDocument, sendMail } from "@/lib/email";
import type { QaItem } from "@/lib/qa-store";
import { getSiteUrl } from "@/lib/site";

export async function mailCustomerReply(item: QaItem, answer: string) {
  if (!item.authorEmail) return;
  const productUrl = `${getSiteUrl()}/product/${encodeURIComponent(item.productId)}`;
  const greeting = `${item.authorName || "고객"}님, 남겨 주신 문의에 답글을 드립니다.`;
  const rows = [
    { label: "상품", value: item.productName },
    { label: "상품 페이지", value: productUrl },
    { label: "문의", value: item.question },
    { label: "답글", value: answer },
  ];
  await sendMail({
    to: item.authorEmail,
    subject: `[Briq] 문의하신 상품에 답글이 등록되었습니다`,
    text: [greeting, "", ...rows.map((row) => `${row.label}: ${row.value}`)].join("\n"),
    html: mailDocument("문의 답글이 등록되었습니다", [{ label: "안내", value: greeting }, ...rows]),
  });
}
