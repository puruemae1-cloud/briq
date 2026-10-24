import { mailDocument, sendMail, SUPPORT_INBOX } from "@/lib/email";
import { answerQa, listQa } from "@/lib/qa-inbox";
import { isAutoReplyDue, soldOutReplyFor } from "@/lib/qa-soldout-reply";
import { mailCustomerReply } from "@/lib/qa-reply-mail";
import type { QaItem } from "@/lib/qa-store";
import { getSiteUrl } from "@/lib/site";

async function mailPostedReply(item: QaItem, answer: string) {
  const productUrl = `${getSiteUrl()}/product/${encodeURIComponent(item.productId)}`;
  const rows = [
    { label: "상품", value: item.productName },
    { label: "상품 페이지", value: productUrl },
    { label: "질문", value: item.question },
    { label: "답글", value: answer },
  ];
  await sendMail({
    to: SUPPORT_INBOX,
    subject: `[Briq 자동답글] ${item.productName}`,
    text: rows.map((row) => `${row.label}: ${row.value}`).join("\n"),
    html: mailDocument("자동 답글이 등록되었습니다", rows),
    replyTo: item.authorEmail,
  });
  await mailCustomerReply(item, answer);
}

/** Post sold-out replies that have waited 10 minutes, then mail that they were posted. */
export async function postDueSoldOutReplies(now = Date.now()): Promise<{ posted: number }> {
  const due = (await listQa()).filter((item) => !item.answer?.trim() && isAutoReplyDue(item.createdAt, now));
  let posted = 0;
  for (const item of due) {
    let answer: string | null = null;
    try {
      answer = await soldOutReplyFor(item.productId, item.question);
    } catch {
      continue;
    }
    if (!answer) continue;
    const saved = await answerQa(item.id, answer, "Briq", { onlyIfEmpty: true });
    if (!saved?.answer) continue;
    posted += 1;
    try {
      await mailPostedReply(saved, saved.answer);
    } catch {
      // The reply is already on the product page.
    }
  }
  return { posted };
}
