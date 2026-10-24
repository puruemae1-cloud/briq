/**
 * Transactional email helper for Briq support alerts.
 *
 * Configure either:
 *   RESEND_API_KEY + MAIL_FROM
 * or leave unset for safe demo mode (logs only, returns ok:false with queued:false).
 *
 * Support inbox defaults to support@hjstoryltd.com
 */

import {
  applyResendUsage,
  loadResendQuota,
  RESEND_FREE_DAILY,
  RESEND_FREE_MONTHLY,
  resendQuotaBlockReason,
  resendQuotaWarning,
  saveResendQuota,
} from "@/lib/resend-quota";

export const SUPPORT_INBOX =
  process.env.MAIL_TO_SUPPORT?.trim() || "support@hjstoryltd.com";

export type MailPayload = {
  subject: string;
  text: string;
  html?: string;
  replyTo?: string;
  to?: string | string[];
};

export type MailResult =
  | { ok: true; id?: string; mode: "resend" | "log" }
  | { ok: false; message: string; mode: "resend" | "log" };

function escapeHtml(value: string) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/** Simple HTML wrapper for support emails. */
export function mailDocument(title: string, rows: { label: string; value: string }[]) {
  const body = rows
    .map(
      (r) =>
        `<tr><td style="padding:8px 12px;color:#6b7280;vertical-align:top;white-space:nowrap">${escapeHtml(r.label)}</td><td style="padding:8px 12px;color:#111;white-space:pre-wrap">${escapeHtml(r.value)}</td></tr>`,
    )
    .join("");
  return `<!doctype html><html><body style="font-family:Georgia,'Times New Roman',serif;background:#f7f8f5;padding:24px">
  <div style="max-width:560px;margin:0 auto;background:#fff;border:1px solid #e5e7eb;padding:28px 24px">
    <p style="margin:0 0 4px;letter-spacing:.2em;font-size:11px;color:#b7a16a;text-transform:uppercase">Briq</p>
    <h1 style="margin:0 0 18px;font-size:22px;font-weight:500">${escapeHtml(title)}</h1>
    <table style="width:100%;border-collapse:collapse;font-size:14px;line-height:1.55">${body}</table>
  </div>
  </body></html>`;
}

export async function sendMail(payload: MailPayload): Promise<MailResult> {
  return deliverMail(payload, true);
}

async function deliverMail(payload: MailPayload, enforceQuota: boolean): Promise<MailResult> {
  const to = payload.to ?? SUPPORT_INBOX;
  const recipients = Array.isArray(to) ? to : [to];
  const from =
    process.env.MAIL_FROM?.trim() || "Briq <onboarding@resend.dev>";
  const apiKey = process.env.RESEND_API_KEY?.trim();

  if (!apiKey) {
    console.info("[briq-mail:demo]", {
      to: recipients,
      subject: payload.subject,
      text: payload.text,
    });
    return {
      ok: false,
      mode: "log",
      message:
        "메일 키가 없어 데모 로그만 남겼습니다. RESEND_API_KEY와 MAIL_FROM을 설정하면 support 메일함으로 발송됩니다.",
    };
  }

  if (enforceQuota) {
    const blocked = resendQuotaBlockReason(await loadResendQuota());
    if (blocked) {
      return { ok: false, mode: "resend", message: blocked };
    }
  }

  try {
    const res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from,
        to: recipients,
        subject: payload.subject,
        text: payload.text,
        html: payload.html,
        reply_to: payload.replyTo,
      }),
    });

    const data = (await res.json().catch(() => ({}))) as {
      id?: string;
      message?: string;
      name?: string;
    };

    if (!res.ok) {
      if (res.status === 429) {
        const state = await loadResendQuota();
        const reason = `${data.name || ""} ${data.message || ""}`;
        if (/monthly/i.test(reason)) state.monthlyUsed = RESEND_FREE_MONTHLY;
        if (/daily/i.test(reason)) state.dailyUsed = RESEND_FREE_DAILY;
        await saveResendQuota(state);
      }
      return {
        ok: false,
        mode: "resend",
        message: data.message || `Resend error (${res.status})`,
      };
    }

    const monthly = Number(res.headers.get("x-resend-monthly-quota"));
    const daily = Number(res.headers.get("x-resend-daily-quota"));
    if (!enforceQuota) {
      return { ok: true, mode: "resend", id: data.id };
    }
    const state = applyResendUsage(
      await loadResendQuota(),
      Number.isFinite(monthly) ? monthly : undefined,
      Number.isFinite(daily) ? daily : undefined,
    );
    const warning = resendQuotaWarning(state);
    if (warning) {
      if (warning.includes("이번 달")) state.warnedMonth = true;
      if (warning.includes("오늘")) state.warnedDay = true;
    }
    await saveResendQuota(state);
    if (warning) {
      await deliverMail(
        {
          to: SUPPORT_INBOX,
          subject: "[Briq] Resend 무료 메일 한도가 얼마 남지 않았습니다",
          text: warning,
          html: mailDocument("Resend 무료 메일 한도", [
            { label: "안내", value: warning },
          ]),
        },
        false,
      );
    }

    return { ok: true, mode: "resend", id: data.id };
  } catch (err) {
    return {
      ok: false,
      mode: "resend",
      message: err instanceof Error ? err.message : "메일 발송 실패",
    };
  }
}
