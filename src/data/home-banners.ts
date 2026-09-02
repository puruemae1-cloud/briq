import type { CategoryId } from "@/data/categories";
import { navCategories } from "@/data/categories";
import { sortNavChildrenByBrandOrder } from "@/lib/brand-nav-order";

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
  /** Rotating sports rails only (golf / run / swim / cycle / tennis). */
  images: string[];
  focal?: string;
  align?: "left" | "center" | "right";
  /**
   * Locked creatives: keep the full photo visible (no cover-crop strip).
   * Stage uses the image aspect ratio instead of a short panoramic max-height.
   */
  fullFrame?: boolean;
  /** CSS aspect-ratio for fullFrame banners (e.g. "16 / 9"). */
  aspectRatio?: string;
  /** When present the banner renders as an auto-advancing carousel */
  slides?: BannerSlide[];
  /**
   * Optional override for brand / leaf links under the lookbook rail title.
   * When omitted, links are derived from `navCategories` children for
   * `categoryId` so new brands appear on the homepage automatically.
   */
  railLinks?: LookBannerLink[];
};

/**
 * Shop nav still mixes product-type / gender leaves with brands.
 * Homepage rails (except sports) should show brand names only.
 */
const HOMEPAGE_RAIL_NON_BRAND_IDS = new Set([
  // shoes — type groupings, not brands
  "luxury-shoes",
  "training-shoes",
]);

/** Homepage rail brand chips — mirrors top-level children under each shop category. */
export function homeRailLinksForCategory(
  categoryId: CategoryId,
): LookBannerLink[] {
  const cat = navCategories.find((c) => c.id === categoryId);
  if (!cat?.children?.length) return [];
  // Sports keeps sport-type leaves (골프, 러닝, …) as-is.
  const children =
    categoryId === "sports"
      ? cat.children
      : sortNavChildrenByBrandOrder(
          cat.children.filter(
            (child) => !HOMEPAGE_RAIL_NON_BRAND_IDS.has(child.id),
          ),
        );
  return children.map((child) => ({
    label: child.labelKo,
    href: child.href,
  }));
}

/** Resolve rail links: explicit override wins, else auto from nav. */
export function resolveHomeRailLinks(banner: LookBanner): LookBannerLink[] {
  if (banner.railLinks && banner.railLinks.length > 0) {
    return banner.railLinks;
  }
  if (banner.categoryId) {
    return homeRailLinksForCategory(banner.categoryId);
  }
  return [];
}

const ONE_WEEK_MS = 7 * 24 * 60 * 60 * 1000;

/** Advances once every week so the artwork refreshes itself. */
export function rotationIndex(now: number = Date.now()) {
  return Math.floor(now / ONE_WEEK_MS);
}

/** Picks this week's photo; `offset` keeps banners out of sync. */
export function pickRotating(
  images: string[],
  offset = 0,
  now?: number,
): string {
  if (images.length === 0) return "";
  const index = (rotationIndex(now) + offset) % images.length;
  return images[index];
}

/**
 * Fixed homepage hero ("London to Your Door").
 * Not rotated weekly — keep a single locked asset under /banners/hero-london-door.jpg
 * (plus /t/ and /m/ variants). Weekly refresh only rotates sports rails.
 */
export const heroImage = "/banners/hero-london-door.jpg";

/** @deprecated Prefer `heroImage` — kept as a one-item list for any callers. */
export const heroImages = [heroImage];

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
    // Locked creative — weekly refresh only rotates rot-event-* (unused here).
    images: ["/banners/event-now-london.jpg"],
    align: "left",
    focal: "50% 45%",
    fullFrame: true,
    aspectRatio: "2560 / 1436",
  },
  {
    id: "luxury",
    kind: "category",
    categoryId: "luxury",
    eyebrow: "Signature",
    title: "Heritage & Modern",
    titleKo: "시그니처 의류 컬렉션",
    support: "영국 헤리티지와 현대 럭셔리의 교차점.",
    href: "/shop?category=luxury&sort=new",
    cta: "시그니처 의류 컬렉션 쇼핑",
    images: ["/banners/luxury-heritage-modern.jpg"],
    align: "right",
    focal: "50% 42%",
    fullFrame: true,
    aspectRatio: "16 / 9",
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
    // Locked Christopher Ward C12 Loco open-balance creative — not rotated weekly.
    images: ["/banners/watches-bel-canto.jpg"],
    align: "left",
    focal: "50% 45%",
    fullFrame: true,
    aspectRatio: "2500 / 1875",
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
    // Locked Chanel Spring 2018 campaign creative — not rotated weekly.
    images: ["/banners/bags-chanel-campaign.jpg"],
    align: "left",
    focal: "50% 50%",
    fullFrame: true,
    aspectRatio: "2 / 1",
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
    // Locked fur-mule creative — not rotated weekly.
    images: ["/banners/shoes-fur-mule.jpg"],
    align: "right",
    focal: "50% 55%",
    fullFrame: true,
    aspectRatio: "16 / 9",
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
    images: ["/banners/accessories-finishing-edit.jpg"],
    align: "left",
    focal: "38% 50%",
    fullFrame: true,
    aspectRatio: "2560 / 1120",
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
