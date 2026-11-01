import type { CSSProperties } from "react";
import { BannerImage } from "@/components/BannerImage";
import { ShopFastLink } from "@/components/ShopFastLink";
import { bannerFocalForSrc } from "@/lib/banner-focal";

/** Locked Christmas 2026 Burberry dual-gender hero — Flannels Amplience. */
const IMAGE = "/banners/flannels-heritage-britain.jpg";
const HREF = "/shop?category=luxury&sub=flannels";
/** Store interior — keep FLANNELS sign + counter in frame. */
const FOCAL = "50% 42%";

/**
 * Interstitial under 시그니처 의류 컬렉션 (luxury rail).
 * Copy locked to Option 3 (concise chic) — do not freestyle.
 */
export function FlannelsHomeBanner() {
  const focal = bannerFocalForSrc(IMAGE, FOCAL);

  return (
    <section
      className="look-banner look-banner--flannels look-banner--left look-banner--fullframe"
      style={
        {
          "--look-banner-aspect": "4 / 3",
        } as CSSProperties
      }
      aria-label="FLANNELS Heritage of Britain"
    >
      <ShopFastLink
        href={HREF}
        className="look-banner__hit"
        aria-label="플란넬스 쇼핑하러 가기"
      >
        <div className="look-banner__media" aria-hidden>
          <BannerImage
            className="look-banner__img"
            src={IMAGE}
            alt=""
            style={focal ? { objectPosition: focal } : undefined}
            loading="lazy"
          />
          <div className="look-banner__shade" />
        </div>
        <div className="look-banner__content">
          <p className="look-banner__eyebrow">FLANNELS EXCLUSIVE</p>
          <h2 className="look-banner__title">
            <span className="look-banner__title-en look-banner__title-en--stack">
              <span className="look-banner__title-line">Heritage of</span>
              <span className="look-banner__title-em">Britain</span>
            </span>
            <span className="look-banner__title-ko">영국 소비자 유통 정품</span>
          </h2>
          <p className="look-banner__support">
            신뢰할 수 있는 영국의 품격을 대폭 할인된 특별한 가격으로 소장하세요.
          </p>
          <span className="look-banner__cta">플란넬스 쇼핑하러 가기</span>
        </div>
      </ShopFastLink>
    </section>
  );
}
