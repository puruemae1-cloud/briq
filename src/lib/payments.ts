/**
 * Korean PG payment adapters — wire these up after merchant contracts.
 *
 * Expected flow later:
 * 1. Create order on server
 * 2. Request payment with PG (Toss / Nice / Inicis)
 * 3. Enable Naver Pay / Kakao Pay via that PG
 * 4. Verify webhook / callback, then fulfill order
 */

export type PaymentMethod = "naverpay" | "kakaopay" | "tosspay" | "card";

export type PaymentConfig = {
  provider: "toss" | "nice" | "inicis" | "none";
  clientKey?: string;
  secretKey?: string;
  mid?: string;
  naverPayEnabled: boolean;
  kakaoPayEnabled: boolean;
};

/** Fill from env after PG contract. Never commit real secrets. */
export function getPaymentConfig(): PaymentConfig {
  return {
    provider: (process.env.NEXT_PUBLIC_PG_PROVIDER as PaymentConfig["provider"]) || "none",
    clientKey: process.env.NEXT_PUBLIC_PG_CLIENT_KEY,
    secretKey: process.env.PG_SECRET_KEY,
    mid: process.env.NEXT_PUBLIC_PG_MID,
    naverPayEnabled: process.env.NEXT_PUBLIC_NAVERPAY === "true",
    kakaoPayEnabled: process.env.NEXT_PUBLIC_KAKAOPAY === "true",
  };
}

export type CheckoutPayload = {
  orderId: string;
  amount: number;
  method: PaymentMethod;
  customerName: string;
  customerPhone: string;
  /** Optional — checkout still proceeds without email */
  customerEmail?: string;
  address: string;
  /** Korean personal customs code — must start with P (e.g. P123456789012) */
  customsCode: string;
};

export type PaymentResult =
  | { ok: true; paymentId: string; message: string }
  | { ok: false; message: string };

/**
 * Placeholder checkout. Replace body with real PG SDK / server API call
 * once (주)리치몬드인터내셔널 merchant keys are issued.
 */
export async function requestPayment(
  payload: CheckoutPayload,
): Promise<PaymentResult> {
  const config = getPaymentConfig();

  if (config.provider === "none" || !config.clientKey) {
    // Demo mode: accept order locally so UI/flow can be tested now.
    await new Promise((r) => setTimeout(r, 600));
    return {
      ok: true,
      paymentId: `DEMO-${payload.orderId}`,
      message:
        "결제 연동 대기 모드입니다. PG 계약 후 환경변수만 넣으면 네이버페이·카카오페이가 활성화됩니다.",
    };
  }

  // TODO: call chosen PG (Toss Payments / Nice / Inicis) here.
  return {
    ok: false,
    message: "PG 키가 설정됐지만 실제 SDK 연동 코드가 아직 없습니다. 개발자에게 연동을 요청하세요.",
  };
}

export const paymentMethods: {
  id: PaymentMethod;
  label: string;
  hint: string;
}[] = [
  {
    id: "naverpay",
    label: "네이버페이",
    hint: "PG 계약 후 활성화",
  },
  {
    id: "kakaopay",
    label: "카카오페이",
    hint: "PG 계약 후 활성화",
  },
  {
    id: "tosspay",
    label: "토스페이",
    hint: "PG 계약 후 활성화",
  },
  {
    id: "card",
    label: "신용/체크카드",
    hint: "국내 카드 (PG 경유)",
  },
];
