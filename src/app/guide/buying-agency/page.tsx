import type { Metadata } from "next";
import Link from "next/link";
import { getSiteUrl } from "@/lib/site";

const title = "명품구매대행 안내 | Briq 브릭 영국 셀렉트숍";
const description =
  "명품구매대행이 필요할 때. Briq는 영국 현지 기준으로 명품의류·가방을 선별하고, 결제부터 통관·직배송까지 한 번에 처리하는 명품구매대행형 쇼핑을 제공합니다.";

export const metadata: Metadata = {
  title,
  description,
  keywords: [
    "명품구매대행",
    "구매대행",
    "명품 구매대행",
    "영국 구매대행",
    "명품의류 구매대행",
  ],
  alternates: { canonical: `${getSiteUrl()}/guide/buying-agency` },
  openGraph: {
    title,
    description,
    url: `${getSiteUrl()}/guide/buying-agency`,
    locale: "ko_KR",
    type: "article",
  },
};

export default function BuyingAgencyGuidePage() {
  return (
    <article className="seo-guide">
      <header className="seo-guide__hero">
        <p className="seo-guide__eyebrow">Briq Guide</p>
        <h1 className="seo-guide__title">명품구매대행, 더 투명하게</h1>
        <p className="seo-guide__lead">
          해외 사이트를 일일이 비교하지 않아도 됩니다. Briq(브릭)은 명품구매대행에
          필요한 상품 검수·결제·국제배송·관부가세 안내를 하나의 숍 경험으로
          정리했습니다.
        </p>
      </header>

      <div className="seo-guide__body">
        <section>
          <h2>구매대행 vs Briq 직구형 셀렉트</h2>
          <p>
            일반적인 명품구매대행은 고객이 URL을 넘기면 대행사가 구매합니다.
            Briq는 영국 현지 감각으로 이미 선별된 명품의류·가방·시계·악세서리를
            카탈로그로 제공해, 탐색부터 결제·배송까지 한 번에 끝냅니다.
          </p>
        </section>

        <section>
          <h2>안심 포인트</h2>
          <ul>
            <li>All-Inclusive Pricing — 해외 항공 배송비·관·부가세 포함 고지</li>
            <li>사업자·통신판매업 정보 푸터 공개</li>
            <li>네이버페이 등 익숙한 결제 수단 지원</li>
            <li>샤넬·구찌·버버리 등 인기 브랜드 중심 큐레이션</li>
          </ul>
        </section>

        <section>
          <h2>이런 검색에 답합니다</h2>
          <p>
            명품구매대행, 명품직구, 명품의류, 샤넬·구찌·프라다·에르메스 등
            유명 명품브랜드를 찾고 계시다면 Briq 가이드와 브랜드 페이지에서
            바로 쇼핑으로 이어질 수 있습니다.
          </p>
        </section>

        <p className="seo-guide__cta-row">
          <Link href="/brands" className="btn btn-solid">
            브랜드 전체 보기
          </Link>
          <Link href="/guide/luxury-direct" className="btn btn-outline">
            명품직구 가이드
          </Link>
        </p>
      </div>
    </article>
  );
}
