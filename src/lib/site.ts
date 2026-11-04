/** Shared public site URL + SEO copy for Naver / Google. */

import { SEO_BRAND_SLUG_ORDER } from "@/lib/brand-nav-order";

/**
 * Canonical origin for SEO. Vercel serves www (briq.kr 308-redirects there), and
 * Naver/Google drop canonical, sitemap and RSS URLs that redirect.
 */
export function getSiteUrl(): string {
  const site =
    process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/$/, "") || "https://www.briq.kr";
  return site.replace(/^https?:\/\/briq\.kr$/, "https://www.briq.kr");
}

/** Primary Korean discovery keywords (used in metadata + copy, not stuffed). */
export const SEO_KEYWORDS = [
  "Briq",
  "브릭",
  "명품의류",
  "명품직구",
  "명품구매대행",
  "영국 명품",
  "명품 셀렉트숍",
  "샤넬",
  "셀린느",
  "생로랑",
  "입생로랑",
  "구찌",
  "버버리",
  "프라다",
  "에르메스",
  "아크테릭스",
  "폴스미스",
  "벨스타프",
  "명품가방",
  "명품시계",
  "명품악세서리",
] as const;

export const SITE_NAME = "Briq";
export const SITE_NAME_KO = "브릭";

export const DEFAULT_TITLE =
  "Briq 브릭 | 명품의류·명품직구·명품구매대행 영국 셀렉트숍";

export const DEFAULT_DESCRIPTION =
  "Briq(브릭) — 영국 현지 기준 명품의류·가방·시계·악세서리 직구/구매대행. 샤넬·구찌·버버리·아크테릭스 등 큐레이션, 항공배송·관부가세 포함 가격으로 국내 직배송.";

/**
 * Absolute document title with a single " | Briq" suffix.
 * Use for product/shop/brand pages that already include brand keywords.
 */
export function seoTitle(page: string): { absolute: string } {
  const bare = (page || "")
    .replace(/\s*[|·—-]\s*(명품직구\s*)?Briq\s*$/i, "")
    .replace(/\s*Briq\s*$/i, "")
    .trim();
  return { absolute: bare ? `${bare} | Briq` : DEFAULT_TITLE };
}

/** Prefer nameKo alone when it already carries the brand (avoid "IWC IWC …"). */
export function productSeoHeadline(brand: string | undefined, name: string): string {
  const n = (name || "").trim();
  const b = (brand || "").trim();
  if (!b || b === "Briq") return n;
  const core = b.replace(/\s*Schaffhausen\s*/i, "").trim();
  const tokens = [...new Set([b, core, ...core.split(/\s+/)])].filter(
    (t) => t.length >= 2,
  );
  const lower = n.toLowerCase();
  if (
    tokens.some(
      (t) =>
        lower.startsWith(t.toLowerCase()) ||
        lower.includes(` ${t.toLowerCase()}`) ||
        lower.includes(t.toLowerCase()),
    )
  ) {
    return n;
  }
  return `${b} ${n}`;
}

export type SeoBrand = {
  slug: string;
  nameEn: string;
  nameKo: string;
  shopHref: string;
  keywords: string[];
  blurb: string;
};

const SEO_BRANDS_BY_SLUG: Record<string, SeoBrand> = {
  chanel: {
    slug: "chanel",
    nameEn: "Chanel",
    nameKo: "샤넬",
    shopHref: "/shop?category=luxury&sub=chanel",
    keywords: ["샤넬", "Chanel", "샤넬 직구", "샤넬 가방"],
    blurb:
      "샤넬 의류·핸드백·슈즈·주얼리·향수까지 Briq 큐레이션으로 살펴보세요.",
  },
  "louis-vuitton": {
    slug: "louis-vuitton",
    nameEn: "Louis Vuitton",
    nameKo: "루이 비통",
    shopHref: "/shop?category=accessories&sub=louis-vuitton-accessories",
    keywords: ["루이비통", "Louis Vuitton", "루이 비통", "LV 홈", "루이비통 가구"],
    blurb:
      "루이 비통 홈 · 가구와 라이트닝 컬렉션을 Briq 영국 셀렉션으로 만나보세요.",
  },
  mulberry: {
    slug: "mulberry",
    nameEn: "Mulberry",
    nameKo: "멀버리",
    shopHref: "/shop?category=bags&sub=mulberry-bags",
    keywords: ["멀버리", "Mulberry", "멀버리 가방", "멀버리 직구"],
    blurb:
      "멀버리 가방·액세서리를 Briq 영국 셀렉션으로 만나보세요.",
  },
  flannels: {
    slug: "flannels",
    nameEn: "FLANNELS",
    nameKo: "FLANNELS (영국현지명품몰)",
    shopHref: "/shop?category=luxury&sub=flannels",
    keywords: ["플래널스", "Flannels", "FLANNELS", "영국 명품몰", "영국현지명품몰"],
    blurb:
      "영국 현지 명품몰 Flannels 클리어런스 셀렉션을 Briq에서 만나보세요.",
  },
  mismo: {
    slug: "mismo",
    nameEn: "Mismo",
    nameKo: "미스모",
    shopHref: "/shop?category=bags&sub=mismo",
    keywords: ["미스모", "Mismo", "미스모 가방", "미스모 직구"],
    blurb:
      "덴마크 미스모의 캔버스 백팩·브리프케이스·토트·위켄드백을 Briq 영국 셀렉션으로 만나보세요.",
  },
  "bottega-veneta": {
    slug: "bottega-veneta",
    nameEn: "Bottega Veneta",
    nameKo: "보테가 베네타",
    shopHref: "/shop?category=bags&sub=bottega-veneta-bags",
    keywords: ["보테가", "보테가 베네타", "Bottega Veneta", "BV", "인트레치아토"],
    blurb:
      "보테가 베네타 가방·슈즈·의류·액세서리를 Briq 영국 셀렉션으로 만나보세요.",
  },
  dior: {
    slug: "dior",
    nameEn: "Dior",
    nameKo: "디올",
    shopHref: "/shop?category=accessories&sub=dior-accessories",
    keywords: ["디올", "Dior", "디올 메종", "디올 테이블웨어", "디올 직구"],
    blurb:
      "디올 메종 테이블웨어 · 홈 컬렉션을 Briq 영국 셀렉션으로 만나보세요.",
  },
  gucci: {
    slug: "gucci",
    nameEn: "Gucci",
    nameKo: "구찌",
    shopHref: "/shop?category=luxury&sub=gucci",
    keywords: ["구찌", "Gucci", "구찌 직구", "구찌 의류"],
    blurb:
      "구찌 레디투웨어·가방·슈즈·악세서리를 Briq에서 영국 셀렉션 기준으로 만나보세요.",
  },
  celine: {
    slug: "celine",
    nameEn: "Celine",
    nameKo: "셀린느",
    shopHref: "/shop?category=luxury&sub=celine",
    keywords: ["셀린느", "Celine", "셀린느 남성", "셀린느 여성", "셀린느 직구"],
    blurb:
      "셀린느 여성·남성 레디투웨어·가방·슈즈·악세서리를 Briq 영국 셀렉션으로 만나보세요.",
  },
  "saint-laurent": {
    slug: "saint-laurent",
    nameEn: "Saint Laurent",
    nameKo: "생로랑",
    shopHref: "/shop?category=luxury&sub=saint-laurent",
    keywords: [
      "생로랑",
      "입생로랑",
      "Saint Laurent",
      "YSL",
      "생로랑 직구",
      "생로랑 가방",
      "생로랑 의류",
    ],
    blurb:
      "생로랑(입생로랑) 남성·여성 레디투웨어·가방·슈즈·악세서리를 Briq 영국 셀렉션으로 만나보세요.",
  },
  "vivienne-westwood": {
    slug: "vivienne-westwood",
    nameEn: "Vivienne Westwood",
    nameKo: "비비안 웨스트우드",
    shopHref: "/shop?category=luxury&sub=vivienne-westwood",
    keywords: ["비비안 웨스트우드", "Vivienne Westwood", "VW", "비비안 직구"],
    blurb:
      "비비안 웨스트우드 의류·가방·슈즈·주얼리·워치를 Briq 영국 셀렉션으로 만나보세요.",
  },
  prada: {
    slug: "prada",
    nameEn: "Prada",
    nameKo: "프라다",
    shopHref: "/shop?category=luxury&sub=pr-women",
    keywords: ["프라다", "Prada", "프라다 직구", "프라다 가방", "프라다 의류", "프라다 명품"],
    blurb:
      "프라다 여성 레디투웨어·가방을 Briq에서 영국 셀렉션 기준으로 만나보세요.",
  },
  "all-saints": {
    slug: "all-saints",
    nameEn: "AllSaints",
    nameKo: "올세인츠",
    shopHref: "/shop?category=luxury&sub=all-saints",
    keywords: ["올세인츠", "AllSaints", "All Saints", "올세인츠 직구", "올세인츠 가죽"],
    blurb:
      "올세인츠 가죽 재킷·로퍼·데님을 Briq 영국 셀렉션으로 만나보세요.",
  },
  hermes: {
    slug: "hermes",
    nameEn: "Hermès",
    nameKo: "에르메스",
    shopHref: "/shop?category=luxury&sort=new",
    keywords: ["에르메스", "Hermès", "Hermes", "에르메스 직구"],
    blurb:
      "에르메스급 명품 구매를 고민 중이라면, Briq의 명품직구·구매대행 가이드와 영국 큐레이션을 참고해 보세요.",
  },
  "london-undercover": {
    slug: "london-undercover",
    nameEn: "London Undercover",
    nameKo: "런던언더커버",
    shopHref: "/shop?category=accessories&sub=london-undercover",
    keywords: ["런던언더커버", "London Undercover"],
    blurb: "런던언더커버 우산·라이프스타일 셀렉션을 Briq에서 만나보세요.",
  },
  "christopher-ward": {
    slug: "christopher-ward",
    nameEn: "Christopher Ward",
    nameKo: "크리스토퍼와드",
    shopHref: "/shop?category=watches&sub=christopher-ward",
    keywords: ["크리스토퍼와드", "Christopher Ward"],
    blurb: "크리스토퍼와드 시계를 Briq 영국 셀렉션으로 살펴보세요.",
  },
  rolex: {
    slug: "rolex",
    nameEn: "Rolex",
    nameKo: "롤렉스",
    shopHref: "/shop?category=watches&sub=rolex",
    keywords: ["롤렉스", "Rolex", "롤렉스 직구", "서브마리너", "데이토나"],
    blurb:
      "롤렉스 서브마리너·데이토나·데이트저스트 등 영국 DMR 취급 셀렉션을 Briq에서 확인하세요.",
  },
  "patek-philippe": {
    slug: "patek-philippe",
    nameEn: "Patek Philippe",
    nameKo: "파텍 필립",
    shopHref: "/shop?category=watches&sub=patek-philippe",
    keywords: ["파텍필립", "파텍 필립", "Patek Philippe", "노틸러스", "아쿠아넛"],
    blurb:
      "파텍 필립 노틸러스·아쿠아넛·칼라트라바를 Briq 영국 정품 시계 셀렉션으로 만나보세요.",
  },
  omega: {
    slug: "omega",
    nameEn: "OMEGA",
    nameKo: "오메가",
    shopHref: "/shop?category=watches&sub=omega",
    keywords: ["오메가", "OMEGA", "스피드마스터", "씨마스터", "오메가 직구"],
    blurb:
      "오메가 스피드마스터·씨마스터·컨스텔레이션을 Briq 영국 셀렉션으로 살펴보세요.",
  },
  "tag-heuer": {
    slug: "tag-heuer",
    nameEn: "TAG Heuer",
    nameKo: "태그호이어",
    shopHref: "/shop?category=watches&sub=tag-heuer",
    keywords: ["태그호이어", "TAG Heuer", "카레라", "모나코", "아쿠아레이서"],
    blurb:
      "태그호이어 카레라·모나코·아쿠아레이서를 Briq 영국 정품 시계로 쇼핑하세요.",
  },
  tudor: {
    slug: "tudor",
    nameEn: "TUDOR",
    nameKo: "튜더",
    shopHref: "/shop?category=watches&sub=tudor",
    keywords: ["튜더", "TUDOR", "블랙베이", "펠라고스", "튜더 직구"],
    blurb:
      "튜더 블랙 베이·펠라고스 등 툴 워치 라인업을 Briq 영국 셀렉션으로 만나보세요.",
  },
  iwc: {
    slug: "iwc",
    nameEn: "IWC",
    nameKo: "IWC",
    shopHref: "/shop?category=watches&sub=iwc",
    keywords: ["IWC", "아이더블유씨", "파일럿 워치", "포르투기저", "탑건"],
    blurb:
      "IWC 파일럿·포르투기저·인제니어 컬렉션을 Briq 영국 DMR 취급 기준으로 확인하세요.",
  },
  norqain: {
    slug: "norqain",
    nameEn: "NORQAIN",
    nameKo: "노르ケイン",
    shopHref: "/shop?category=watches&sub=norqain",
    keywords: ["노르케인", "NORQAIN", "노르케인 시계"],
    blurb: "스위스 노르케인 시계를 Briq 영국 셀렉션으로 살펴보세요.",
  },
  "galvin-green": {
    slug: "galvin-green",
    nameEn: "Galvin Green",
    nameKo: "갈빈 그린",
    shopHref: "/shop?category=sports&sub=galvin-green",
    keywords: ["갈빈그린", "Galvin Green"],
    blurb: "갈빈 그린 골프웨어를 Briq에서 쇼핑하세요.",
  },
  burberry: {
    slug: "burberry",
    nameEn: "Burberry",
    nameKo: "버버리",
    shopHref: "/shop?category=luxury&sub=burberry",
    keywords: ["버버리", "Burberry", "버버리 트렌치", "버버리 직구"],
    blurb:
      "버버리 트렌치·아우터·체크 백·슈즈를 영국 부티크 감성으로 선별했습니다.",
  },
  "paul-smith": {
    slug: "paul-smith",
    nameEn: "Paul Smith",
    nameKo: "폴 스미스",
    shopHref: "/shop?category=luxury&sub=paul-smith",
    keywords: ["폴스미스", "Paul Smith", "폴 스미스"],
    blurb: "폴 스미스의 브리티시 테일러링과 액세서리를 Briq에서 쇼핑하세요.",
  },
  arcteryx: {
    slug: "arcteryx",
    nameEn: "Arc'teryx",
    nameKo: "아크테릭스",
    shopHref: "/shop?category=luxury&sub=arcteryx",
    keywords: ["아크테릭스", "Arc'teryx", "아크테릭스 직구"],
    blurb: "아크테릭스 어패럴·기어를 아웃도어 하이엔드 라인으로 소개합니다.",
  },
  belstaff: {
    slug: "belstaff",
    nameEn: "Belstaff",
    nameKo: "벨스타프",
    shopHref: "/shop?category=luxury&sub=belstaff",
    keywords: ["벨스타프", "Belstaff"],
    blurb: "벨스타프 아우터와 라이딩 헤리티지 룩을 큐레이션했습니다.",
  },
};

/** Ordered: Chanel → Gucci → (new) → Burberry → Paul Smith → Arc'teryx → Belstaff */
export const SEO_BRANDS: SeoBrand[] = SEO_BRAND_SLUG_ORDER.map(
  (slug) => SEO_BRANDS_BY_SLUG[slug],
).filter(Boolean);

export function getSeoBrand(slug: string): SeoBrand | undefined {
  return SEO_BRANDS_BY_SLUG[slug] ?? SEO_BRANDS.find((b) => b.slug === slug);
}
