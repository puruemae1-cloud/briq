/**
 * Naver Pay 주문형 V2.1 — sandbox-first config.
 * certiKey / merchant secrets stay server-only; button key is public (SDK requirement).
 */

export type NaverPayUrls = {
  buttonScript: string;
  orderRegister: string;
  orderSheetPc: string;
  orderSheetMobile: string;
  /** Form POST — returns payProductId (plain body, max 19 alnum). */
  wishlistRegister: string;
};

const SANDBOX_URLS: NaverPayUrls = {
  buttonScript: "https://test-pay.naver.com/assets/button/latest/npay.button.js",
  orderRegister: "https://test-api.pay.naver.com/o/customer/api/order/v20/register",
  orderSheetPc: "https://test-order.pay.naver.com/customer/buy",
  orderSheetMobile: "https://test-m.pay.naver.com/o/customer/buy",
  wishlistRegister: "https://test-pay.naver.com/customer/api/wishlist.nhn",
};

const PROD_URLS: NaverPayUrls = {
  buttonScript: "https://npay-order.pstatic.net/assets/button/latest/npay.button.js",
  orderRegister: "https://api.pay.naver.com/o/customer/api/order/v20/register",
  orderSheetPc: "https://order.pay.naver.com/customer/buy",
  orderSheetMobile: "https://m.pay.naver.com/o/customer/buy",
  wishlistRegister: "https://pay.naver.com/customer/api/wishlist.nhn",
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
 * Briq shipping policy for Npay XML (order register + product-info).
 *
 * Site truth (ProductPurchaseNotice / orders.ts):
 * - UK→KR private order; delivery ~7–14 business days after payment
 * - Product price already includes overseas air freight + duties
 *   (`INCLUDED_SHIPPING_NOTE` = "해외 항공 배송비·관세 포함 (별도 청구 없음)")
 * - Checkout `shippingFeeKrw` is normally 0
 *
 * Therefore feeType/feePayType = FREE with feePrice 0 (not CONDITIONAL_FREE —
 * there is no threshold; shipping is never charged separately).
 * Delivery lead time is communicated on PDP/checkout, not as an Npay fee field.
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

export type NaverPayReturnInfo = {
  zipcode: string;
  address1: string;
  address2: string;
  sellername: string;
  contact1: string;
};

/**
 * Default return/seller contacts from SiteFooter 사업자 정보.
 * PDP policy: 단순 변심 반품 불가·하자 외 교환 제한 — Npay still requires returnInfo.
 * Override via NAVERPAY_RETURN_* env when 페이센터 반품지 differs.
 */
const RETURN_INFO_DEFAULTS: NaverPayReturnInfo = {
  // 경기도 김포시 고촌읍 은행영사정로23번길 46
  zipcode: "10066",
  address1: "경기도 김포시 고촌읍 은행영사정로23번길 46",
  address2: "(주)리치몬드인터내셔널 / Briq",
  sellername: "(주)리치몬드인터내셔널",
  // SiteFooter: +44 7897 535888 (digits only for Npay contact1)
  contact1: "447897535888",
};

function envOr(key: string, fallback: string) {
  const v = process.env[key]?.trim();
  return v || fallback;
}

export function getNaverPayReturnInfo(): NaverPayReturnInfo {
  return {
    zipcode: envOr("NAVERPAY_RETURN_ZIPCODE", RETURN_INFO_DEFAULTS.zipcode),
    address1: envOr("NAVERPAY_RETURN_ADDRESS1", RETURN_INFO_DEFAULTS.address1),
    address2: envOr("NAVERPAY_RETURN_ADDRESS2", RETURN_INFO_DEFAULTS.address2),
    sellername: envOr(
      "NAVERPAY_RETURN_SELLERNAME",
      RETURN_INFO_DEFAULTS.sellername,
    ),
    contact1: envOr(
      "NAVERPAY_RETURN_CONTACT1",
      RETURN_INFO_DEFAULTS.contact1,
    ).replace(/[^\d]/g, ""),
  };
}
