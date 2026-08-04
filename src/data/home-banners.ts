import type { CategoryId } from "@/data/categories";

export type BannerSlide = {
  id: string;
  labelKo: string;
  href: string;
  images: string[];
  /** CSS object-position so the subject stays in frame when cropped */
  focal?: string;
};

export type LookBannerLink = {
  label: string;
  href: string;
};

export type LookBanner = {
  id: string;
  kind: "event" | "category";
  categoryId?: CategoryId;
  eyebrow: string;
  title: string;
  titleKo: string;
  support: string;
  href: string;
  cta: string;
  /** Rotates to the next photo every two weeks */
  images: string[];
  focal?: string;
  align?: "left" | "center" | "right";
  /** When present the banner renders as an auto-advancing carousel */
  slides?: BannerSlide[];
  /** Brand / leaf links shown under the lookbook rail title (replaces “Selection”). */
  railLinks?: LookBannerLink[];
};

const TWO_WEEKS_MS = 14 * 24 * 60 * 60 * 1000;

/** Advances once every two weeks so the artwork refreshes itself. */
export function rotationIndex(now: number = Date.now()) {
  return Math.floor(now / TWO_WEEKS_MS);
}

/** Picks this fortnight's photo; `offset` keeps banners out of sync. */
export function pickRotating(
  images: string[],
  offset = 0,
  now?: number,
): string {
  if (images.length === 0) return "";
  const index = (rotationIndex(now) + offset) % images.length;
  return images[index];
}

export const heroImages = [
  "/banners/rot-hero-1.jpg",
  "/banners/rot-hero-2.jpg",
  "/banners/rot-hero-3.jpg",
  "/banners/rot-hero-4.jpg",
];

export const homeLookBanners: LookBanner[] = [
  {
    id: "event-new",
    kind: "event",
    eyebrow: "New Season Edit",
    title: "Now in London",
    titleKo: "지금 영국에서 가장 핫한 신상",
    support: "남들보다 빠르게 선점하는 영국 실시간 프리미엄 트렌드.",
    href: "/shop?sort=new",
    cta: "신상 보러가기",
    images: [
      "/banners/rot-event-1.jpg",
      "/banners/rot-event-2.jpg",
      "/banners/rot-event-3.jpg",
    ],
    align: "left",
  },
  {
    id: "luxury",
    kind: "category",
    categoryId: "luxury",
    eyebrow: "Luxury",
    title: "Heritage & Modern",
    titleKo: "명품 하이엔드 의류",
    support: "영국 헤리티지와 현대 럭셔리의 교차점.",
    href: "/shop?category=luxury&sort=new",
    cta: "명품 하이엔드 의류 쇼핑",
    images: [
      "/banners/rot-luxury-1.jpg",
      "/banners/rot-luxury-2.jpg",
      "/banners/rot-luxury-3.jpg",
    ],
    align: "right",
    railLinks: [
      { label: "버버리", href: "/shop?category=luxury&sub=burberry" },
      { label: "벨스타프", href: "/shop?category=luxury&sub=belstaff" },
      { label: "폴스미스", href: "/shop?category=luxury&sub=paul-smith" },
      { label: "아크테릭스", href: "/shop?category=luxury&sub=arcteryx" },
    ],
  },
  {
    id: "watches",
    kind: "category",
    categoryId: "watches",
    eyebrow: "Watches",
    title: "Time, Refined",
    titleKo: "시계",
    support: "초침이 흐르는 순간까지, 시간에 품격을 더하는 셀렉트 워치.",
    href: "/shop?category=watches",
    cta: "시계 쇼핑",
    images: [
      "/banners/rot-watch-1.jpg",
      "/banners/rot-watch-2.jpg",
      "/banners/rot-watch-3.jpg",
    ],
    align: "left",
    focal: "center 42%",
    railLinks: [
      {
        label: "크리스토퍼와드",
        href: "/shop?category=watches&sub=christopher-ward",
      },
    ],
  },
  {
    id: "clothing",
    kind: "category",
    categoryId: "clothing",
    eyebrow: "Fashion",
    title: "British Silhouette",
    titleKo: "패션의류",
    support: "시티부터 위켄드까지, 절제된 영국식 실루엣.",
    href: "/shop?category=clothing",
    cta: "패션의류 쇼핑",
    images: [
      "/banners/rot-cloth-1.jpg",
      "/banners/rot-cloth-2.jpg",
      "/banners/rot-cloth-3.jpg",
    ],
    align: "center",
  },
  {
    id: "bags",
    kind: "category",
    categoryId: "bags",
    eyebrow: "Bags",
    title: "Crafted Carry",
    titleKo: "가방",
    support: "손끝에 느껴지는 가죽과 구조감.",
    href: "/shop?category=bags",
    cta: "가방 쇼핑",
    images: [
      "/banners/rot-bag-1.jpg",
      "/banners/rot-bag-2.jpg",
      "/banners/rot-bag-3.jpg",
    ],
    align: "left",
    railLinks: [
      { label: "구찌", href: "/shop?category=bags&sub=gucci-bags" },
      { label: "버버리", href: "/shop?category=bags&sub=burberry-bags" },
      { label: "벨스타프", href: "/shop?category=bags&sub=belstaff-bags" },
      { label: "아크테릭스", href: "/shop?category=bags&sub=arcteryx-bags" },
    ],
  },
  {
    id: "shoes",
    kind: "category",
    categoryId: "shoes",
    eyebrow: "Shoes",
    title: "From Desk to Dinner",
    titleKo: "슈즈",
    support: "데스크에서 디너까지 이어지는 풋웨어.",
    href: "/shop?category=shoes",
    cta: "슈즈 쇼핑",
    images: [
      "/banners/rot-shoe-1.jpg",
      "/banners/rot-shoe-2.jpg",
      "/banners/rot-shoe-3.jpg",
    ],
    align: "right",
    railLinks: [
      { label: "버버리", href: "/shop?category=shoes&sub=burberry-shoes" },
      { label: "벨스타프", href: "/shop?category=shoes&sub=belstaff-shoes" },
      { label: "폴스미스", href: "/shop?category=shoes&sub=paul-smith-shoes" },
      { label: "아크테릭스", href: "/shop?category=shoes&sub=arcteryx-shoes" },
    ],
  },
  {
    id: "accessories",
    kind: "category",
    categoryId: "accessories",
    eyebrow: "Accessories",
    title: "The Finishing Edit",
    titleKo: "악세서리",
    support: "티·지갑·쥬얼리까지, 일상의 마침표.",
    href: "/shop?category=accessories",
    cta: "악세서리 쇼핑",
    images: [
      "/banners/rot-acc-1.jpg",
      "/banners/rot-acc-2.jpg",
      "/banners/rot-acc-3.jpg",
    ],
    align: "left",
    railLinks: [
      {
        label: "폴스미스",
        href: "/shop?category=accessories&sub=paul-smith-accessories",
      },
      {
        label: "벨스타프",
        href: "/shop?category=accessories&sub=belstaff-accessories",
      },
      {
        label: "런던 언더커버",
        href: "/shop?category=accessories&sub=london-undercover",
      },
      { label: "버버리", href: "/shop?category=accessories&sub=burberry-accessories" },
    ],
  },
  {
    id: "sports",
    kind: "category",
    categoryId: "sports",
    eyebrow: "Sports",
    title: "Weekend Movement",
    titleKo: "스포츠",
    support: "골프·자전거·수영·러닝·테니스를 위한 영국식 에디트.",
    href: "/shop?category=sports",
    cta: "스포츠 쇼핑",
    images: ["/banners/rot-golf-1.jpg"],
    align: "left",
    railLinks: [
      { label: "골프", href: "/shop?category=sports&sub=golf" },
      { label: "자전거", href: "/shop?category=sports&sub=cycling" },
      { label: "수영", href: "/shop?category=sports&sub=swimming" },
      { label: "러닝", href: "/shop?category=sports&sub=running" },
      { label: "테니스", href: "/shop?category=sports&sub=tennis" },
    ],
    slides: [
      {
        id: "golf",
        labelKo: "골프",
        href: "/shop?category=sports&sub=golf",
        images: [
          "/banners/rot-golf-1.jpg",
          "/banners/rot-golf-2.jpg",
          "/banners/rot-golf-3.jpg",
        ],
        focal: "center 36%",
      },
      {
        id: "cycling",
        labelKo: "자전거",
        href: "/shop?category=sports&sub=cycling",
        images: [
          "/banners/rot-cycle-1.jpg",
          "/banners/rot-cycle-2.jpg",
          "/banners/rot-cycle-3.jpg",
        ],
        focal: "center 42%",
      },
      {
        id: "swimming",
        labelKo: "수영",
        href: "/shop?category=sports&sub=swimming",
        images: [
          "/banners/rot-swim-1.jpg",
          "/banners/rot-swim-2.jpg",
          "/banners/rot-swim-3.jpg",
        ],
        focal: "center 48%",
      },
      {
        id: "running",
        labelKo: "러닝",
        href: "/shop?category=sports&sub=running",
        images: [
          "/banners/rot-run-1.jpg",
          "/banners/rot-run-2.jpg",
          "/banners/rot-run-3.jpg",
        ],
        focal: "center 78%",
      },
      {
        id: "tennis",
        labelKo: "테니스",
        href: "/shop?category=sports&sub=tennis",
        images: [
          "/banners/rot-tennis-1.jpg",
          "/banners/rot-tennis-2.jpg",
          "/banners/rot-tennis-3.jpg",
        ],
        focal: "center 55%",
      },
    ],
  },
];
