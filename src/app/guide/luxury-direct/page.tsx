import type { Metadata } from "next";
import Link from "next/link";
import { SEO_BRANDS, getSiteUrl } from "@/lib/site";

const title = "명품직구 가이드 | 영국 명품 직배송 Briq";
const description =
  "명품직구가 처음이어도 안심. Briq(브릭)은 영국 현지 셀렉션 기준의 샤넬·구찌·버버리 등 명품의류·가방을 관부가세·항공배송 포함 가격으로 국내 직배송합니다.";

export const metadata: Metadata = {
  title,
  description,
  keywords: [
    "명품직구",
    "명품 직구",
    "영국 명품직구",
    "명품의류 직구",
    "샤넬 직구",
    "구찌 직구",
    "버버리 직구",
  ],
  alternates: { canonical: `${getSiteUrl()}/guide/luxury-direct` },
  openGraph: {
    title,
    description,
    url: `${getSiteUrl()}/guide/luxury-direct`,
    locale: "ko_KR",
    type: "article",
  },
};

export default function LuxuryDirectGuidePage() {
  return (
    <article className="seo-guide">
      <header className="seo-guide__hero">
        <p className="seo-guide__eyebrow">Briq Guide</p>
        <h1 className="seo-guide__title">명품직구, 영국에서 바로</h1>
        <p className="seo-guide__lead">
          Briq(브릭)은 영국 부티크 기준으로 고른 명품의류·가방·시계·악세서리를
          명품직구·국내 직배송으로 연결합니다. 항공 배송비와 관·부가세가 포함된
          All-Inclusive 가격으로 최종 금액을 미리 확인하세요.
        </p>
      </header>

      <div className="seo-guide__body">
        <section>
          <h2>왜 영국 명품직구인가</h2>
          <p>
            유럽·영국 시즌 릴리즈와 현지 사이즈·컬러웨이 정보를 바탕으로
            샤넬, 구찌, 버버리, 아크테릭스 등 인기 명품 브랜드를 큐레이션합니다.
            프라다·에르메스 등 하이엔드 명품을 찾는 고객에게도 신뢰할 수 있는
            직구·구매대행 기준을 안내합니다.
          </p>
        </section>

        <section>
          <h2>Briq 명품직구 이용 방법</h2>
          <ol>
            <li>원하는 카테고리·브랜드에서 상품을 고릅니다.</li>
            <li>표시 가격(배송·세금 포함)과 옵션을 확인합니다.</li>
            <li>네이버페이 등으로 결제하면 영국→한국 직배송이 진행됩니다.</li>
          </ol>
        </section>

        <section>
          <h2>함께 보면 좋은 브랜드</h2>
          <ul className="seo-guide__brands">
            {SEO_BRANDS.map((b) => (
              <li key={b.slug}>
                <Link href={`/brands/${b.slug}`}>
                  {b.nameKo} ({b.nameEn})
                </Link>
              </li>
            ))}
          </ul>
        </section>

        <p className="seo-guide__cta-row">
          <Link href="/shop?sort=new" className="btn btn-solid">
            신상품 보러가기
          </Link>
          <Link href="/guide/buying-agency" className="btn btn-outline">
            명품구매대행 안내
          </Link>
        </p>
      </div>
    </article>
  );
}
