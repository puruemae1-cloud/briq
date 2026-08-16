import type { Metadata } from "next";
import Link from "next/link";
import { getSiteUrl } from "@/lib/site";

const title = "명품의류 쇼핑 | Briq 브릭 하이엔드 의류";
const description =
  "명품의류를 영국 셀렉트로. 샤넬·구찌·버버리·아크테릭스 등 하이엔드 의류를 Briq에서 명품직구·구매대행형으로 만나보세요.";

export const metadata: Metadata = {
  title,
  description,
  keywords: [
    "명품의류",
    "하이엔드 의류",
    "명품 옷",
    "샤넬 의류",
    "구찌 의류",
    "버버리 코트",
  ],
  alternates: { canonical: `${getSiteUrl()}/guide/luxury-apparel` },
  openGraph: {
    title,
    description,
    url: `${getSiteUrl()}/guide/luxury-apparel`,
    locale: "ko_KR",
    type: "article",
  },
};

export default function LuxuryApparelGuidePage() {
  return (
    <article className="seo-guide">
      <header className="seo-guide__hero">
        <p className="seo-guide__eyebrow">Briq Guide</p>
        <h1 className="seo-guide__title">명품의류 하이엔드 에디트</h1>
        <p className="seo-guide__lead">
          시즌 아우터부터 니트·테일러링까지. Briq의 명품의류 카테고리는 영국
          현지 기준으로 고른 하이엔드 룩을 모았습니다.
        </p>
      </header>

      <div className="seo-guide__body">
        <section>
          <h2>지금 쇼핑하기</h2>
          <ul className="seo-guide__brands">
            <li>
              <Link href="/shop?category=luxury&sort=new">
                명품 하이엔드 의류 전체
              </Link>
            </li>
            <li>
              <Link href="/shop?category=luxury&sub=chanel">샤넬 의류</Link>
            </li>
            <li>
              <Link href="/shop?category=luxury&sub=gucci">구찌 의류</Link>
            </li>
            <li>
              <Link href="/shop?category=luxury&sub=burberry">버버리 의류</Link>
            </li>
            <li>
              <Link href="/shop?category=luxury&sub=paul-smith">폴 스미스</Link>
            </li>
            <li>
              <Link href="/shop?category=luxury&sub=arcteryx">아크테릭스</Link>
            </li>
            <li>
              <Link href="/shop?category=luxury&sub=belstaff">벨스타프</Link>
            </li>
          </ul>
        </section>

        <p className="seo-guide__cta-row">
          <Link href="/shop?category=luxury" className="btn btn-solid">
            명품의류 보러가기
          </Link>
        </p>
      </div>
    </article>
  );
}
