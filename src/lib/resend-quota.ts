import { get, put } from "@vercel/blob";

/** Resend free transactional plan. Paid sending starts only after this is used up. */
export const RESEND_FREE_MONTHLY = 3000;
export const RESEND_FREE_DAILY = 100;
export const RESEND_QUOTA_WARN_AT = 10;

const BLOB_PATH = "mail/resend-quota.json";

export type ResendQuotaState = {
  month: string;
  day: string;
  monthlyUsed: number;
  dailyUsed: number;
  warnedMonth: boolean;
  warnedDay: boolean;
};

function utcMonth(date = new Date()) {
  return date.toISOString().slice(0, 7);
}

function utcDay(date = new Date()) {
  return date.toISOString().slice(0, 10);
}

function freshState(): ResendQuotaState {
  return {
    month: utcMonth(),
    day: utcDay(),
    monthlyUsed: 0,
    dailyUsed: 0,
    warnedMonth: false,
    warnedDay: false,
  };
}

export async function loadResendQuota(): Promise<ResendQuotaState> {
  const fresh = freshState();
  if (!process.env.BLOB_READ_WRITE_TOKEN) return fresh;
  try {
    const result = await get(BLOB_PATH, { access: "private", useCache: false });
    if (!result || result.statusCode !== 200 || !result.stream) return fresh;
    const saved = JSON.parse(await new Response(result.stream).text()) as Partial<ResendQuotaState>;
    const sameMonth = saved.month === fresh.month;
    const sameDay = saved.day === fresh.day;
    return {
      month: fresh.month,
      day: fresh.day,
      monthlyUsed: sameMonth ? Number(saved.monthlyUsed) || 0 : 0,
      dailyUsed: sameDay ? Number(saved.dailyUsed) || 0 : 0,
      warnedMonth: sameMonth ? Boolean(saved.warnedMonth) : false,
      warnedDay: sameDay ? Boolean(saved.warnedDay) : false,
    };
  } catch {
    return fresh;
  }
}

export async function saveResendQuota(state: ResendQuotaState) {
  if (!process.env.BLOB_READ_WRITE_TOKEN) return;
  try {
    await put(BLOB_PATH, JSON.stringify(state), {
      access: "private",
      addRandomSuffix: false,
      allowOverwrite: true,
      contentType: "application/json",
      cacheControlMaxAge: 60,
    });
  } catch {
    /* The next send still uses the usage headers from Resend. */
  }
}

/** Refuse a send that would leave the free plan and start paid overage. */
export function resendQuotaBlockReason(state: ResendQuotaState): string | null {
  if (state.monthlyUsed >= RESEND_FREE_MONTHLY) {
    return "Resend 무료 월 한도를 모두 사용해 메일을 보내지 않았습니다. 유료 발송으로 넘어가지 않습니다.";
  }
  if (state.dailyUsed >= RESEND_FREE_DAILY) {
    return "Resend 무료 하루 한도를 모두 사용해 메일을 보내지 않았습니다. 유료 발송으로 넘어가지 않습니다.";
  }
  return null;
}

export function applyResendUsage(
  state: ResendQuotaState,
  monthlyUsed?: number,
  dailyUsed?: number,
): ResendQuotaState {
  const next = { ...state, month: utcMonth(), day: utcDay() };
  if (state.month !== next.month) {
    next.monthlyUsed = 0;
    next.warnedMonth = false;
  }
  if (state.day !== next.day) {
    next.dailyUsed = 0;
    next.warnedDay = false;
  }
  if (Number.isFinite(monthlyUsed)) next.monthlyUsed = monthlyUsed as number;
  else next.monthlyUsed += 1;
  if (Number.isFinite(dailyUsed)) next.dailyUsed = dailyUsed as number;
  else next.dailyUsed += 1;
  return next;
}

export function resendQuotaWarning(state: ResendQuotaState): string | null {
  const monthLeft = RESEND_FREE_MONTHLY - state.monthlyUsed;
  const dayLeft = RESEND_FREE_DAILY - state.dailyUsed;
  const lines: string[] = [];
  if (monthLeft > 0 && monthLeft <= RESEND_QUOTA_WARN_AT && !state.warnedMonth) {
    lines.push(`이번 달 무료 메일 한도가 ${monthLeft}통 남았습니다. 한도는 ${RESEND_FREE_MONTHLY}통입니다.`);
  }
  if (dayLeft > 0 && dayLeft <= RESEND_QUOTA_WARN_AT && !state.warnedDay) {
    lines.push(`오늘 무료 메일 한도가 ${dayLeft}통 남았습니다. 하루 한도는 ${RESEND_FREE_DAILY}통입니다.`);
  }
  if (!lines.length) return null;
  lines.push("한도가 끝나면 유료로 넘어가지 않도록 메일은 더 보내지 않습니다.");
  return lines.join("\n");
}
