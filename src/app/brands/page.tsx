import type { Metadata } from "next";
import Link from "next/link";
import { SEO_BRANDS, getSiteUrl } from "@/lib/site";

const title = "명품 브랜드 | 샤넬·구찌·버버리·프라다·에르메스 — Briq";
const description =
  "샤넬, 구찌, 버버리, 아크테릭스부터 프라다·에르메스 관심 고객까지. Briq 브릭에서 영국 명품브랜드 셀렉션을 살펴보세요.";

export const metadata: Metadata = {
  title,
  description,
  keywords: [
    "명품브랜드",
    "샤넬",
    "구찌",
    "버버리",
    "프라다",
    "에르메스",
    "아크테릭스",
  ],
  alternates: { canonical: `${getSiteUrl()}/brands` },
  openGraph: {
    title,
    description,
    url: `${getSiteUrl()}/brands`,
    locale: "ko_KR",
    type: "website",
  },
};

export default function BrandsIndexPage() {
  return (
    <article className="seo-guide">
      <header className="seo-guide__hero">
        <p className="seo-guide__eyebrow">Brands</p>
        <h1 className="seo-guide__title">Briq 명품 브랜드</h1>
        <p className="seo-guide__lead">
          유명 명품브랜드 검색으로 찾아오신 분을 위해, 브랜드별 소개와 쇼핑
          링크를 모았습니다. 명품의류·명품직구·명품구매대행을 Briq에서 이어가세요.
        </p>
      </header>

      <div className="seo-guide__body">
        <ul className="seo-brand-grid">
          {SEO_BRANDS.map((b) => (
            <li key={b.slug} className="seo-brand-card">
              <Link href={`/brands/${b.slug}`}>
                <span className="seo-brand-card__en">{b.nameEn}</span>
                <span className="seo-brand-card__ko">{b.nameKo}</span>
                <span className="seo-brand-card__blurb">{b.blurb}</span>
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </article>
  );
}
