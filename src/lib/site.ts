/** Shared public site URL + SEO copy for Naver / Google. */

export function getSiteUrl(): string {
  return (
    process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/$/, "") || "https://briq.kr"
  );
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

export type SeoBrand = {
  slug: string;
  nameEn: string;
  nameKo: string;
  shopHref: string;
  keywords: string[];
  blurb: string;
};

/** Brands we sell + discovery keywords for related luxury searches. */
export const SEO_BRANDS: SeoBrand[] = [
  {
    slug: "gucci",
    nameEn: "Gucci",
    nameKo: "구찌",
    shopHref: "/shop?category=luxury&sub=gucci",
    keywords: ["구찌", "Gucci", "구찌 직구", "구찌 의류"],
    blurb:
      "구찌 레디투웨어·가방·슈즈·악세서리를 Briq에서 영국 셀렉션 기준으로 만나보세요.",
  },
  {
    slug: "chanel",
    nameEn: "Chanel",
    nameKo: "샤넬",
    shopHref: "/shop?category=luxury&sub=chanel",
    keywords: ["샤넬", "Chanel", "샤넬 직구", "샤넬 가방"],
    blurb:
      "샤넬 의류·핸드백·슈즈·주얼리·향수까지 Briq 큐레이션으로 살펴보세요.",
  },
  {
    slug: "burberry",
    nameEn: "Burberry",
    nameKo: "버버리",
    shopHref: "/shop?category=luxury&sub=burberry",
    keywords: ["버버리", "Burberry", "버버리 트렌치", "버버리 직구"],
    blurb:
      "버버리 트렌치·아우터·체크 백·슈즈를 영국 부티크 감성으로 선별했습니다.",
  },
  {
    slug: "arcteryx",
    nameEn: "Arc'teryx",
    nameKo: "아크테릭스",
    shopHref: "/shop?category=luxury&sub=arcteryx",
    keywords: ["아크테릭스", "Arc'teryx", "아크테릭스 직구"],
    blurb: "아크테릭스 어패럴·기어를 아웃도어 하이엔드 라인으로 소개합니다.",
  },
  {
    slug: "paul-smith",
    nameEn: "Paul Smith",
    nameKo: "폴 스미스",
    shopHref: "/shop?category=luxury&sub=paul-smith",
    keywords: ["폴스미스", "Paul Smith", "폴 스미스"],
    blurb: "폴 스미스의 브리티시 테일러링과 액세서리를 Briq에서 쇼핑하세요.",
  },
  {
    slug: "belstaff",
    nameEn: "Belstaff",
    nameKo: "벨스타프",
    shopHref: "/shop?category=luxury&sub=belstaff",
    keywords: ["벨스타프", "Belstaff"],
    blurb: "벨스타프 아우터와 라이딩 헤리티지 룩을 큐레이션했습니다.",
  },
  {
    slug: "prada",
    nameEn: "Prada",
    nameKo: "프라다",
    shopHref: "/shop?category=luxury&sort=new",
    keywords: ["프라다", "Prada", "프라다 직구", "프라다 명품"],
    blurb:
      "프라다 등 하이엔드 명품 직구·구매대행을 찾는 분께 Briq의 영국 명품 셀렉션을 안내합니다.",
  },
  {
    slug: "hermes",
    nameEn: "Hermès",
    nameKo: "에르메스",
    shopHref: "/shop?category=luxury&sort=new",
    keywords: ["에르메스", "Hermès", "Hermes", "에르메스 직구"],
    blurb:
      "에르메스급 명품 구매를 고민 중이라면, Briq의 명품직구·구매대행 가이드와 영국 큐레이션을 참고해 보세요.",
  },
];

export function getSeoBrand(slug: string): SeoBrand | undefined {
  return SEO_BRANDS.find((b) => b.slug === slug);
}
