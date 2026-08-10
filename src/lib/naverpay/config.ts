/**
 * Naver Pay 주문형 V2.1 — sandbox-first config.
 * certiKey / merchant secrets stay server-only; button key is public (SDK requirement).
 */

export type NaverPayUrls = {
  buttonScript: string;
  orderRegister: string;
  orderSheetPc: string;
  orderSheetMobile: string;
};

const SANDBOX_URLS: NaverPayUrls = {
  buttonScript: "https://test-pay.naver.com/assets/button/latest/npay.button.js",
  orderRegister: "https://test-api.pay.naver.com/o/customer/api/order/v20/register",
  orderSheetPc: "https://test-order.pay.naver.com/customer/buy",
  orderSheetMobile: "https://test-m.pay.naver.com/o/customer/buy",
};

const PROD_URLS: NaverPayUrls = {
  buttonScript: "https://npay-order.pstatic.net/assets/button/latest/npay.button.js",
  orderRegister: "https://api.pay.naver.com/o/customer/api/order/v20/register",
  orderSheetPc: "https://order.pay.naver.com/customer/buy",
  orderSheetMobile: "https://m.pay.naver.com/o/customer/buy",
};

export function isNaverPaySandbox() {
  return process.env.NEXT_PUBLIC_NAVERPAY_SANDBOX !== "false";
}

/** Site origin used for product/info URLs and WCS whitelist. */
export function getNaverPaySiteOrigin() {
  return (
    process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/$/, "") || "https://briq.kr"
  );
}

export function getNaverPayUrls(): NaverPayUrls {
  return isNaverPaySandbox() ? SANDBOX_URLS : PROD_URLS;
}

export function getNaverPayMerchantId() {
  return process.env.NAVERPAY_MERCHANT_ID?.trim() || "";
}

/** Server-only 가맹점인증키 — never expose to the client. */
export function getNaverPayCertiKey() {
  return process.env.NAVERPAY_CERTI_KEY?.trim() || "";
}

export function getNaverPayButtonKey() {
  return (
    process.env.NEXT_PUBLIC_NAVERPAY_BUTTON_KEY?.trim() ||
    process.env.NAVERPAY_BUTTON_KEY?.trim() ||
    ""
  );
}

export function getNaverWcsAccount() {
  return process.env.NEXT_PUBLIC_NAVER_WCS_ACCOUNT?.trim() || "";
}

/**
 * Render Npay order button when the order feature flag is on,
 * or when a public button key is present (sandbox wiring).
 */
export function isNaverPayOrderEnabled() {
  if (process.env.NEXT_PUBLIC_NAVERPAY_ORDER === "true") return true;
  if (process.env.NEXT_PUBLIC_NAVERPAY_ORDER === "false") return false;
  return Boolean(getNaverPayButtonKey());
}

export function isNaverPayServerReady() {
  return Boolean(
    getNaverPayMerchantId() && getNaverPayCertiKey() && getNaverPayButtonKey(),
  );
}

/**
 * Briq UK→KR prices already include overseas air freight + duties.
 * Map to Npay FREE shipping policy until merchant sets a separate fee.
 */
export const NAVERPAY_SHIPPING_DEFAULTS = {
  groupId: "briq-uk-kr",
  method: "DELIVERY" as const,
  feeType: "FREE" as const,
  feePayType: "FREE" as const,
  feePrice: 0,
};

/**
 * Default tax type for checkout XML.
 * Briq sells as a KR mall; adjust if finance confirms TAX_FREE / ZERO_TAX.
 */
export const NAVERPAY_TAX_TYPE = "TAX" as const;

/** Placeholder return address — replace before 검수 요청. */
export const NAVERPAY_RETURN_INFO_PLACEHOLDER = {
  zipcode: "00000",
  address1: "대한민국 (반품지 미설정)",
  address2: "Briq 고객센터 확인 후 안내",
  sellername: "Briq",
  contact1: "00000000000",
};
