import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { JsonLd } from "@/components/JsonLd";
import { SEO_BRANDS, getSeoBrand, getSiteUrl } from "@/lib/site";

type Props = {
  params: Promise<{ slug: string }>;
};

export function generateStaticParams() {
  return SEO_BRANDS.map((b) => ({ slug: b.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const brand = getSeoBrand(slug);
  if (!brand) return {};
  const title = `${brand.nameKo} ${brand.nameEn} | 명품직구·구매대행 Briq`;
  const description = `${brand.blurb} 명품의류·명품직구·명품구매대행은 Briq 브릭.`;
  return {
    title,
    description,
    keywords: brand.keywords,
    alternates: { canonical: `${getSiteUrl()}/brands/${brand.slug}` },
    openGraph: {
      title,
      description,
      url: `${getSiteUrl()}/brands/${brand.slug}`,
      locale: "ko_KR",
      type: "website",
    },
  };
}

export default async function BrandLandingPage({ params }: Props) {
  const { slug } = await params;
  const brand = getSeoBrand(slug);
  if (!brand) notFound();
  const site = getSiteUrl();

  const ld = {
    "@context": "https://schema.org",
    "@type": "Brand",
    name: brand.nameEn,
    alternateName: brand.nameKo,
    url: `${site}/brands/${brand.slug}`,
    description: brand.blurb,
  };

  return (
    <article className="seo-guide">
      <JsonLd data={ld} />
      <header className="seo-guide__hero">
        <p className="seo-guide__eyebrow">{brand.nameEn}</p>
        <h1 className="seo-guide__title">
          {brand.nameKo} <span className="seo-guide__title-en">{brand.nameEn}</span>
        </h1>
        <p className="seo-guide__lead">{brand.blurb}</p>
      </header>

      <div className="seo-guide__body">
        <section>
          <h2>{brand.nameKo} 쇼핑하기</h2>
          <p>
            Briq에서 {brand.nameKo} 관련 셀렉션을 확인하고, 명품직구·구매대행형
            결제로 국내 직배송까지 이어갈 수 있습니다.
          </p>
        </section>

        <p className="seo-guide__cta-row">
          <Link href={brand.shopHref} className="btn btn-solid">
            {brand.nameKo} 상품 보기
          </Link>
          <Link href="/brands" className="btn btn-outline">
            모든 브랜드
          </Link>
          <Link href="/guide/luxury-direct" className="btn btn-outline">
            명품직구 가이드
          </Link>
        </p>
      </div>
    </article>
  );
}
