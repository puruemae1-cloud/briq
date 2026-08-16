import type { Metadata } from "next";
import Link from "next/link";
import { getSiteUrl } from "@/lib/site";

export const metadata: Metadata = {
  title: "가이드 | 명품직구·구매대행·명품의류 — Briq",
  description:
    "Briq 가이드 모음 — 명품직구, 명품구매대행, 명품의류 하이엔드 셀렉션 안내.",
  alternates: { canonical: `${getSiteUrl()}/guide` },
};

const links = [
  {
    href: "/guide/luxury-direct",
    title: "명품직구 가이드",
    desc: "영국에서 바로 오는 명품직구 이용 방법",
  },
  {
    href: "/guide/buying-agency",
    title: "명품구매대행 안내",
    desc: "투명한 구매대행형 쇼핑과 All-Inclusive 가격",
  },
  {
    href: "/guide/luxury-apparel",
    title: "명품의류",
    desc: "샤넬·구찌·버버리 하이엔드 의류 에디트",
  },
  {
    href: "/brands",
    title: "명품 브랜드",
    desc: "샤넬·구찌·버버리·프라다·에르메스 등",
  },
];

export default function GuideIndexPage() {
  return (
    <article className="seo-guide">
      <header className="seo-guide__hero">
        <p className="seo-guide__eyebrow">Guides</p>
        <h1 className="seo-guide__title">Briq 쇼핑 가이드</h1>
        <p className="seo-guide__lead">
          명품의류·명품직구·명품구매대행을 처음 이용하셔도 쉽게 시작할 수 있도록
          정리했습니다.
        </p>
      </header>
      <ul className="seo-brand-grid">
        {links.map((l) => (
          <li key={l.href} className="seo-brand-card">
            <Link href={l.href}>
              <span className="seo-brand-card__ko">{l.title}</span>
              <span className="seo-brand-card__blurb">{l.desc}</span>
            </Link>
          </li>
        ))}
      </ul>
    </article>
  );
}
