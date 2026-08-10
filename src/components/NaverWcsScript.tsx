"use client";

import Script from "next/script";
import { getNaverWcsAccount, isNaverPayOrderEnabled } from "@/lib/naverpay/config";

/**
 * Naver common inflow (wcs) — must run before Npay button SDK.
 * Account ID = 네이버공통인증키 (NEXT_PUBLIC_NAVER_WCS_ACCOUNT).
 */
export function NaverWcsScript() {
  if (!isNaverPayOrderEnabled() && !getNaverWcsAccount()) return null;

  const account = getNaverWcsAccount();

  return (
    <>
      <Script
        src="https://wcs.naver.net/wcslog.js"
        strategy="afterInteractive"
      />
      <Script id="briq-naver-wcs-init" strategy="afterInteractive">
        {`
          if (!window.wcs_add) window.wcs_add = {};
          ${account ? `window.wcs_add["wa"] = ${JSON.stringify(account)};` : ""}
          if (window.wcs) {
            window.wcs.checkoutWhitelist = ["briq.kr", "www.briq.kr"];
            window.wcs.inflow("briq.kr");
          }
        `}
      </Script>
      <Script id="briq-naver-wcs-do" strategy="lazyOnload">
        {`
          if (window.wcs) {
            try { window.wcs_do(); } catch (e) {}
          }
        `}
      </Script>
    </>
  );
}
