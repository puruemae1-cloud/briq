import type { CategoryId, SubcategoryId } from "@/data/categories";
import { expandSubcategoryFilter } from "@/data/categories";
import { cwTwelvePicNMixProducts } from "@/data/cw-twelve-picnmix";

export type ProductStorySection = {
  titleKo: string;
  bodyKo: string;
  image?: string;
  imageAlt?: string;
  reverse?: boolean;
};

export type ProductVariant = {
  id: string;
  name: string;
  nameKo: string;
  sku: string;
  gbpPrice: number;
  price: number;
  /**
   * Catalog photo path under `/public/products/`.
   * Use the shared 4:5 framing standard — see `src/lib/product-image.ts`.
   */
  image: string;
  sourceUrl: string;
  inStock: boolean;
};

export type Product = {
  id: string;
  name: string;
  nameKo: string;
  brand: string;
  price: number;
  category: CategoryId;
  subcategory?: SubcategoryId;
  tags: string[];
  /** Customer-facing Korean description only */
  descriptionKo?: string;
  /**
   * Primary catalog photo (`/public/products/...`).
   * Prefer ~1600×2000 (4:5), subject centered — rendered via `ProductImage`
   * with `object-fit: contain` so all grid/PDP/cart tiles stay uniform.
   */
  image: string;
  images?: string[];
  accent: string;
  badge?: string;
  gbpPrice?: number;
  sku?: string;
  sourceUrl?: string;
  size?: string;
  variants?: ProductVariant[];
  /**
   * Product-level stock when there are no variants.
   * With variants, availability is derived from `variant.inStock`.
   */
  inStock?: boolean;
  /**
   * Optional bracelet resize (Christopher Ward).
   * Selecting any cm size adds `feeKrw`; "no" keeps base price.
   */
  braceletResize?: {
    feeKrw: number;
    sizesCm: string[];
  };
  /** Long-form PDP story blocks (image + Korean copy). */
  storySections?: ProductStorySection[];
};

/** KRW = GBP × 2100 × 1.06 + 20,000 (internal pricing — not shown on PDP) */
export function gbpToBriqKrw(gbp: number) {
  return Math.round(gbp * 2100 * 1.06 + 20000);
}

/** True if the product (or any of its variants) can be purchased. */
export function isProductInStock(product: Product) {
  if (product.variants && product.variants.length > 0) {
    return product.variants.some((v) => v.inStock);
  }
  return product.inStock !== false;
}

/** True if a specific variant (or the product itself) is purchasable. */
export function isVariantInStock(product: Product, variantId?: string | null) {
  if (product.variants && product.variants.length > 0) {
    if (!variantId) return false;
    return product.variants.some((v) => v.id === variantId && v.inStock);
  }
  return product.inStock !== false;
}

const chinoCapVariants: ProductVariant[] = [
  {
    id: "black-white",
    name: "black/white",
    nameKo: "블랙/화이트",
    sku: "PO252P011-Q11",
    gbpPrice: 70,
    price: gbpToBriqKrw(70),
    image: "/products/prl-chino-cap-black-white.jpg",
    sourceUrl:
      "https://www.zalando.co.uk/polo-ralph-lauren-cotton-chino-ball-cap-cap-blackwhite-po252p011-q11.html",
    inStock: false,
  },
  {
    id: "company-olive",
    name: "company olive",
    nameKo: "컴퍼니 올리브",
    sku: "PO252P011-M15",
    gbpPrice: 70,
    price: gbpToBriqKrw(70),
    image: "/products/prl-chino-cap-company-olive.jpg",
    sourceUrl:
      "https://www.zalando.co.uk/polo-ralph-lauren-the-iconic-cotton-chino-ball-cap-cap-company-olive-po252p011-m15.html",
    inStock: false,
  },
  {
    id: "cruise-lime",
    name: "cruise lime",
    nameKo: "크루즈 라임",
    sku: "PO252P011-K19",
    gbpPrice: 60,
    price: gbpToBriqKrw(60),
    image: "/products/prl-chino-cap-cruise-lime.jpg",
    sourceUrl:
      "https://www.zalando.co.uk/polo-ralph-lauren-the-iconic-cotton-chino-ball-cap-cap-cruise-lime-po252p011-k19.html",
    inStock: false,
  },
  {
    id: "garden-trail-cream",
    name: "garden trail/cream pp",
    nameKo: "가든 트레일/크림",
    sku: "PO252P011-Q12",
    gbpPrice: 54,
    price: gbpToBriqKrw(54),
    image: "/products/prl-chino-cap-garden-trail-cream.jpg",
    sourceUrl:
      "https://www.zalando.co.uk/polo-ralph-lauren-the-iconic-cotton-chino-ball-cap-cap-garden-trailcream-pp-po252p011-q12.html",
    inStock: false,
  },
  {
    id: "new-forest",
    name: "new forest",
    nameKo: "뉴 포레스트",
    sku: "PO252P011-M11",
    gbpPrice: 70,
    price: gbpToBriqKrw(70),
    image: "/products/prl-chino-cap-new-forest.jpg",
    sourceUrl:
      "https://www.zalando.co.uk/polo-ralph-lauren-cotton-chino-ball-cap-cap-new-forest-po252p011-m11.html",
    inStock: false,
  },
  {
    id: "rustic-navy",
    name: "rustic navy",
    nameKo: "러스틱 네이비",
    sku: "PO252P011-K13",
    gbpPrice: 70,
    price: gbpToBriqKrw(70),
    image: "/products/prl-chino-cap-rustic-navy.jpg",
    sourceUrl:
      "https://www.zalando.co.uk/polo-ralph-lauren-chino-ball-hat-cap-rustic-navy-po252p011-k13.html",
    inStock: false,
  },
  {
    id: "rustic-tan",
    name: "rustic tan",
    nameKo: "러스틱 탄",
    sku: "PO252P011-B11",
    gbpPrice: 54,
    price: gbpToBriqKrw(54),
    image: "/products/prl-chino-cap-rustic-tan.jpg",
    sourceUrl:
      "https://www.zalando.co.uk/polo-ralph-lauren-cotton-chino-ball-cap-cap-rustic-tan-po252p011-b11.html",
    inStock: false,
  },
  {
    id: "terrace-pink",
    name: "terrace pink/c7560",
    nameKo: "테라스 핑크",
    sku: "PO252P011-J11",
    gbpPrice: 70,
    price: gbpToBriqKrw(70),
    image: "/products/prl-chino-cap-terrace-pink.jpg",
    sourceUrl:
      "https://www.zalando.co.uk/polo-ralph-lauren-the-iconic-cotton-chino-ball-cap-cap-terrace-pinkc7560-po252p011-j11.html",
    inStock: false,
  },
  {
    id: "wisteria",
    name: "wisteria w/ c9601",
    nameKo: "위스테리아",
    sku: "PO252P011-I12",
    gbpPrice: 70,
    price: gbpToBriqKrw(70),
    image: "/products/prl-chino-cap-wisteria.jpg",
    sourceUrl:
      "https://www.zalando.co.uk/polo-ralph-lauren-the-iconic-cotton-chino-ball-cap-cap-wisteria-w-c9601-po252p011-i12.html",
    inStock: false,
  },
];

const chinoCapMinPrice = Math.min(...chinoCapVariants.map((v) => v.price));

export const products: Product[] = [
  ...cwTwelvePicNMixProducts,
  {
    id: "prl-chino-cap",
    name: "The Iconic Cotton Chino Ball Cap",
    nameKo: "폴로 랄프 로렌 아이코닉 코튼 치노 볼캡",
    brand: "Polo Ralph Lauren",
    price: chinoCapMinPrice,
    gbpPrice: Math.min(...chinoCapVariants.map((v) => v.gbpPrice)),
    category: "accessories",
    tags: ["cap", "cotton", "one-size"],
    descriptionKo: "100% 코튼 치노 볼캡. 포니 자수, 버클 조절 스트랩. 사이즈 One Size.",
    image: chinoCapVariants[0].image,
    images: chinoCapVariants.map((v) => v.image),
    accent: "#1a1a1a",
    badge: "New",
    size: "One Size",
    sku: "PO252P011",
    sourceUrl: chinoCapVariants[0].sourceUrl,
    variants: chinoCapVariants,
  },
  {
    id: "briq-heritage-coat",
    name: "Belgravia Heritage Coat",
    nameKo: "벨그레이비아 헤리티지 코트",
    brand: "Briq Luxury",
    price: 890000,
    category: "luxury",
    subcategory: "womens",
    tags: ["heritage"],
    descriptionKo: "영국 헤리티지 하우스의 시그니처 실루엣을 담은 럭셔리 코트.",
    image: "/products/wool-coat.svg",
    accent: "#2C241C",
    badge: "Editor",
  },
  {
    id: "briq-cashmere-wrap",
    name: "Mayfair Cashmere Wrap",
    nameKo: "메이페어 캐시미어 랩",
    brand: "Briq Luxury",
    price: 520000,
    category: "luxury",
    subcategory: "womens",
    tags: ["cashmere"],
    descriptionKo: "가벼운 드레이프의 캐시미어 랩. 이브닝부터 트래블까지.",
    image: "/products/scarf.svg",
    accent: "#4A3A32",
  },
  {
    id: "briq-savile-suit",
    name: "Savile Row Suit",
    nameKo: "새빌로우 슈트",
    brand: "Briq Luxury",
    price: 1280000,
    category: "luxury",
    subcategory: "mens",
    tags: ["tailoring"],
    descriptionKo: "런던 테일러링 감성의 명품 슈트.",
    image: "/products/wool-coat.svg",
    accent: "#1A2428",
    badge: "Editor",
  },
  {
    id: "briq-dress-watch",
    name: "Savile Dress Watch",
    nameKo: "새빌 드레스 워치",
    brand: "Briq Horology",
    price: 1280000,
    category: "watches",
    tags: ["dress"],
    descriptionKo: "절제된 다이얼과 가죽 스트랩의 클래식 드레스 워치.",
    image: "/products/cap.svg",
    accent: "#1A2428",
    badge: "Editor",
  },
  {
    id: "briq-field-watch",
    name: "Field Automatic",
    nameKo: "필드 오토매틱",
    brand: "Briq Horology",
    price: 760000,
    category: "watches",
    tags: ["automatic"],
    descriptionKo: "데일리 필드 감성의 오토매틱 워치.",
    image: "/products/bottle.svg",
    accent: "#24302A",
  },
  {
    id: "cw-c60-trident",
    name: "C60 Trident Pro 300",
    nameKo: "C60 트라이던트 프로 300",
    brand: "Christopher Ward",
    price: gbpToBriqKrw(895),
    gbpPrice: 895,
    category: "watches",
    subcategory: "christopher-ward",
    tags: ["dive", "british"],
    descriptionKo: "영국 독립 워치메이커 크리스토퍼와드의 시그니처 다이버 워치.",
    image: "/products/cap.svg",
    accent: "#1A2A38",
    badge: "Editor",
  },
  {
    id: "briq-run-jacket",
    name: "Brixton Run Shell",
    nameKo: "브릭스턴 런 셸 재킷",
    brand: "Briq Edit",
    price: 189000,
    category: "sports",
    subcategory: "running",
    tags: ["running", "outer"],
    descriptionKo: "시티 러닝과 주말 트레일을 위한 경량 방수 셸.",
    image: "/products/run-jacket.svg",
    accent: "#1F4D3A",
  },
  {
    id: "briq-track-tee",
    name: "Track Day Tee",
    nameKo: "트랙 데이 티셔츠",
    brand: "Briq Edit",
    price: 59000,
    category: "sports",
    subcategory: "running",
    tags: ["training"],
    descriptionKo: "영국식 애슬레틱 실루엣의 통기성 좋은 코튼 티.",
    image: "/products/track-tee.svg",
    accent: "#243447",
  },
  {
    id: "briq-golf-polo",
    name: "St Andrews Polo",
    nameKo: "세인트앤드루스 폴로",
    brand: "Briq Sport",
    price: 129000,
    category: "sports",
    subcategory: "golf",
    tags: ["golf"],
    descriptionKo: "라운드용 클린 실루엣 폴로 셔츠.",
    image: "/products/track-tee.svg",
    accent: "#2F5A3E",
  },
  {
    id: "briq-swim-brief",
    name: "Brighton Swim Short",
    nameKo: "브라이튼 스윔 쇼츠",
    brand: "Briq Sport",
    price: 89000,
    category: "sports",
    subcategory: "swimming",
    tags: ["swim"],
    descriptionKo: "영국 코스트 무드의 퀵드라이 스윔 쇼츠.",
    image: "/products/runner.svg",
    accent: "#1E3A4A",
  },
  {
    id: "briq-cycle-jersey",
    name: "Cotswold Cycle Jersey",
    nameKo: "콧스월드 사이클 저지",
    brand: "Briq Sport",
    price: 159000,
    category: "sports",
    subcategory: "cycling",
    tags: ["cycling"],
    descriptionKo: "주말 라이딩을 위한 통기성 사이클 저지.",
    image: "/products/run-jacket.svg",
    accent: "#2A4038",
  },
  {
    id: "briq-tennis-skirt",
    name: "Wimbledon Court Skirt",
    nameKo: "윔블던 코트 스커트",
    brand: "Briq Sport",
    price: 119000,
    category: "sports",
    subcategory: "tennis",
    tags: ["tennis"],
    descriptionKo: "프라이빗 클럽 코트용 클린 실루엣 테니스 스커트.",
    image: "/products/track-tee.svg",
    accent: "#2F5A48",
  },
  {
    id: "briq-tennis-polo",
    name: "Queen's Club Polo",
    nameKo: "퀸즈클럽 폴로",
    brand: "Briq Sport",
    price: 139000,
    category: "sports",
    subcategory: "tennis",
    tags: ["tennis"],
    descriptionKo: "잔디·하드코트 모두를 위한 프리미엄 테니스 폴로.",
    image: "/products/track-tee.svg",
    accent: "#1E4A3A",
  },
  {
    id: "briq-wool-coat",
    name: "Mayfair Wool Coat",
    nameKo: "메이페어 울 코트",
    brand: "Briq Atelier",
    price: 429000,
    category: "clothing",
    subcategory: "mens",
    tags: ["outerwear"],
    descriptionKo: "부티크 테일러링이 돋보이는 구조감 울 코트.",
    image: "/products/wool-coat.svg",
    accent: "#2C2A28",
    badge: "Editor",
  },
  {
    id: "briq-knit",
    name: "Camden Merino Knit",
    nameKo: "캠든 메리노 니트",
    brand: "Briq Atelier",
    price: 149000,
    category: "clothing",
    subcategory: "womens",
    tags: ["knit"],
    descriptionKo: "부드러운 메리노, 절제된 모던 드레이프.",
    image: "/products/knit.svg",
    accent: "#5C4A3A",
  },
  {
    id: "briq-blouse",
    name: "Chelsea Silk Blouse",
    nameKo: "첼시 실크 블라우스",
    brand: "Briq Atelier",
    price: 189000,
    category: "clothing",
    subcategory: "womens",
    tags: ["silk"],
    descriptionKo: "소프트 실크의 에브리데이 블라우스.",
    image: "/products/knit.svg",
    accent: "#6A5550",
  },
  {
    id: "briq-tote",
    name: "Soho Leather Tote",
    nameKo: "소호 레더 토트",
    brand: "Briq Goods",
    price: 259000,
    category: "bags",
    tags: ["leather"],
    descriptionKo: "풀그레인 가죽의 데일리 토트백.",
    image: "/products/tote.svg",
    accent: "#6B3E2E",
  },
  {
    id: "briq-crossbody",
    name: "Fleet Crossbody",
    nameKo: "플리트 크로스바디",
    brand: "Briq Goods",
    price: 129000,
    category: "bags",
    tags: ["daily"],
    descriptionKo: "시티 트래블에 맞춘 컴팩트 크로스바디.",
    image: "/products/crossbody.svg",
    accent: "#3D4A3A",
    badge: "Best",
  },
  {
    id: "briq-cap",
    name: "Briq Cap",
    nameKo: "브릭 캡",
    brand: "Briq",
    price: 49000,
    category: "accessories",
    tags: ["logo"],
    descriptionKo: "네 글자 마크. 앱 아이콘처럼 강렬하게.",
    image: "/products/cap.svg",
    accent: "#0E1A17",
  },
  {
    id: "briq-scarf",
    name: "Thames Check Scarf",
    nameKo: "템스 체크 스카프",
    brand: "Briq Atelier",
    price: 89000,
    category: "accessories",
    tags: ["wool"],
    descriptionKo: "런던 겨울 무드의 소프트 체크 스카프.",
    image: "/products/scarf.svg",
    accent: "#4A5560",
  },
  {
    id: "briq-tea-set",
    name: "Afternoon Tea Caddy",
    nameKo: "애프터눈 티 캐디",
    brand: "Briq Pantry",
    price: 68000,
    category: "accessories",
    subcategory: "british-tea",
    tags: ["tea"],
    descriptionKo: "영국식 애프터눈 티를 위한 셀렉트 티 캐디.",
    image: "/products/bottle.svg",
    accent: "#3A4A38",
  },
  {
    id: "briq-wallet",
    name: "Bond Compact Wallet",
    nameKo: "본드 컴팩트 월렛",
    brand: "Briq Goods",
    price: 98000,
    category: "accessories",
    subcategory: "wallets",
    tags: ["leather"],
    descriptionKo: "슬림한 풀그레인 레더 월렛.",
    image: "/products/pouch.svg",
    accent: "#3A2F28",
  },
  {
    id: "briq-runner",
    name: "Brixton Runner",
    nameKo: "브릭스턴 러너",
    brand: "Briq Sport",
    price: 179000,
    category: "shoes",
    subcategory: "training-mens",
    tags: ["sneakers", "training"],
    descriptionKo: "절제된 영국식 실루엣의 데일리 트레이닝 러너.",
    image: "/products/runner.svg",
    accent: "#1A2E28",
  },
  {
    id: "briq-train-womens",
    name: "Chelsea Train",
    nameKo: "첼시 트레인",
    brand: "Briq Sport",
    price: 169000,
    category: "shoes",
    subcategory: "training-womens",
    tags: ["sneakers", "training"],
    descriptionKo: "시티 트레이닝을 위한 라이트웨이트 스니커.",
    image: "/products/runner.svg",
    accent: "#2A3A45",
  },
  {
    id: "briq-loafer",
    name: "Bond Street Loafer",
    nameKo: "본드스트리트 로퍼",
    brand: "Briq Atelier",
    price: 219000,
    category: "shoes",
    subcategory: "luxury-mens",
    tags: ["leather", "luxury"],
    descriptionKo: "데스크부터 디너까지, 폴리시드 레더 로퍼.",
    image: "/products/loafer.svg",
    accent: "#3A2F28",
  },
  {
    id: "briq-heel",
    name: "Knightsbridge Heel",
    nameKo: "나이츠브리지 힐",
    brand: "Briq Atelier",
    price: 249000,
    category: "shoes",
    subcategory: "luxury-womens",
    tags: ["heel", "luxury"],
    descriptionKo: "이브닝을 위한 미니멀 힐.",
    image: "/products/loafer.svg",
    accent: "#4A3038",
  },
  {
    id: "briq-bottle",
    name: "Briq Day Bottle",
    nameKo: "브릭 데이 보틀",
    brand: "Briq Lifestyle",
    price: 39000,
    category: "sports",
    subcategory: "running",
    tags: ["daily"],
    descriptionKo: "트레이닝과 트래블용 매트 스틸 보틀.",
    image: "/products/bottle.svg",
    accent: "#2A3A45",
  },
  {
    id: "briq-pouch",
    name: "Edit Tech Pouch",
    nameKo: "에디트 테크 파우치",
    brand: "Briq Lifestyle",
    price: 45000,
    category: "accessories",
    subcategory: "wallets",
    tags: ["organizer"],
    descriptionKo: "케이블·카드·소품을 담는 컴팩트 파우치.",
    image: "/products/pouch.svg",
    accent: "#314036",
  },
];

/** Extra catalogue rows so the homepage can show a full 100-piece edit. */
const collectionSeeds: Array<{
  name: string;
  nameKo: string;
  brand: string;
  category: CategoryId;
  subcategory?: SubcategoryId;
  basePrice: number;
  image: string;
  accent: string;
}> = [
  { name: "Notting Hill Coat", nameKo: "노팅힐 코트", brand: "Briq Luxury", category: "luxury", subcategory: "womens", basePrice: 680000, image: "/products/wool-coat.svg", accent: "#2C241C" },
  { name: "Belgravia Blazer", nameKo: "벨그레이비아 블레이저", brand: "Briq Luxury", category: "luxury", subcategory: "mens", basePrice: 720000, image: "/products/wool-coat.svg", accent: "#1A2428" },
  { name: "Mayfair Trouser", nameKo: "메이페어 트라우저", brand: "Briq Luxury", category: "luxury", subcategory: "womens", basePrice: 390000, image: "/products/knit.svg", accent: "#4A3A32" },
  { name: "Chelsea Dress", nameKo: "첼시 드레스", brand: "Briq Luxury", category: "luxury", subcategory: "womens", basePrice: 540000, image: "/products/knit.svg", accent: "#5C4A3A" },
  { name: "Savile Overcoat", nameKo: "새빌 오버코트", brand: "Briq Luxury", category: "luxury", subcategory: "mens", basePrice: 980000, image: "/products/wool-coat.svg", accent: "#2C2A28" },
  { name: "C65 Aquitaine", nameKo: "C65 아키텐", brand: "Christopher Ward", category: "watches", subcategory: "christopher-ward", basePrice: gbpToBriqKrw(1495), image: "/products/cap.svg", accent: "#1A2A38" },
  { name: "C60 Sealander", nameKo: "C60 실랜더", brand: "Christopher Ward", category: "watches", subcategory: "christopher-ward", basePrice: gbpToBriqKrw(795), image: "/products/bottle.svg", accent: "#24302A" },
  { name: "Belgravia Chronograph", nameKo: "벨그레이비아 크로노그래프", brand: "Briq Horology", category: "watches", basePrice: 980000, image: "/products/cap.svg", accent: "#1A2428" },
  { name: "Fleet Field Watch", nameKo: "플리트 필드 워치", brand: "Briq Horology", category: "watches", basePrice: 620000, image: "/products/bottle.svg", accent: "#243447" },
  { name: "Camden Trench", nameKo: "캠든 트렌치", brand: "Briq Atelier", category: "clothing", subcategory: "womens", basePrice: 359000, image: "/products/wool-coat.svg", accent: "#2C2A28" },
  { name: "Soho Merino", nameKo: "소호 메리노", brand: "Briq Atelier", category: "clothing", subcategory: "mens", basePrice: 129000, image: "/products/knit.svg", accent: "#5C4A3A" },
  { name: "Hampstead Shirt", nameKo: "햄스테드 셔츠", brand: "Briq Atelier", category: "clothing", subcategory: "mens", basePrice: 98000, image: "/products/track-tee.svg", accent: "#243447" },
  { name: "Kensington Skirt", nameKo: "켄싱턴 스커트", brand: "Briq Atelier", category: "clothing", subcategory: "womens", basePrice: 159000, image: "/products/knit.svg", accent: "#6A5550" },
  { name: "Islington Jacket", nameKo: "이슬링턴 재킷", brand: "Briq Atelier", category: "clothing", subcategory: "womens", basePrice: 289000, image: "/products/run-jacket.svg", accent: "#1F4D3A" },
  { name: "Marylebone Bag", nameKo: "메릴본 백", brand: "Briq Goods", category: "bags", basePrice: 329000, image: "/products/tote.svg", accent: "#6B3E2E" },
  { name: "Clerkenwell Clutch", nameKo: "클러큰웰 클러치", brand: "Briq Goods", category: "bags", basePrice: 189000, image: "/products/crossbody.svg", accent: "#3D4A3A" },
  { name: "Shoreditch Satchel", nameKo: "쇼디치 사첼", brand: "Briq Goods", category: "bags", basePrice: 279000, image: "/products/tote.svg", accent: "#3A2F28" },
  { name: "Covent Garden Mini", nameKo: "코벤트 가든 미니", brand: "Briq Goods", category: "bags", basePrice: 219000, image: "/products/crossbody.svg", accent: "#4A3A32" },
  { name: "Piccadilly Derby", nameKo: "피카딜리 더비", brand: "Briq Atelier", category: "shoes", subcategory: "luxury-mens", basePrice: 289000, image: "/products/loafer.svg", accent: "#3A2F28" },
  { name: "Sloane Pump", nameKo: "슬론 펌프", brand: "Briq Atelier", category: "shoes", subcategory: "luxury-womens", basePrice: 259000, image: "/products/loafer.svg", accent: "#4A3038" },
  { name: "Battersea Trainer", nameKo: "배터시 트레이너", brand: "Briq Sport", category: "shoes", subcategory: "training-mens", basePrice: 189000, image: "/products/runner.svg", accent: "#1A2E28" },
  { name: "Fulham Trainer", nameKo: "풀럼 트레이너", brand: "Briq Sport", category: "shoes", subcategory: "training-womens", basePrice: 179000, image: "/products/runner.svg", accent: "#2A3A45" },
  { name: "Mayfair Pearl Stud", nameKo: "메이페어 펄 스터드", brand: "Briq Atelier", category: "accessories", subcategory: "jewelry", basePrice: 129000, image: "/products/scarf.svg", accent: "#4A5560" },
  { name: "Bond Street Lip", nameKo: "본드스트리트 립", brand: "Briq Beauty", category: "accessories", subcategory: "cosmetics", basePrice: 48000, image: "/products/bottle.svg", accent: "#4A3038" },
  { name: "Fleet Card Case", nameKo: "플리트 카드 케이스", brand: "Briq Goods", category: "accessories", subcategory: "wallets", basePrice: 78000, image: "/products/pouch.svg", accent: "#3A2F28" },
  { name: "Afternoon Biscuit Tin", nameKo: "애프터눈 비스킷 틴", brand: "Briq Pantry", category: "accessories", subcategory: "snacks", basePrice: 42000, image: "/products/bottle.svg", accent: "#3A4A38" },
  { name: "Richmond Wellness Mix", nameKo: "리치먼드 웰니스 믹스", brand: "Briq Pantry", category: "accessories", subcategory: "health-food", basePrice: 56000, image: "/products/bottle.svg", accent: "#2F5A3E" },
  { name: "Earl Grey Caddy", nameKo: "얼그레이 캐디", brand: "Briq Pantry", category: "accessories", subcategory: "british-tea", basePrice: 52000, image: "/products/bottle.svg", accent: "#3A4A38" },
  { name: "St Andrews Cap", nameKo: "세인트앤드루스 캡", brand: "Briq Sport", category: "sports", subcategory: "golf", basePrice: 79000, image: "/products/cap.svg", accent: "#2F5A3E" },
  { name: "Gleneagles Vest", nameKo: "글린이글스 베스트", brand: "Briq Sport", category: "sports", subcategory: "golf", basePrice: 189000, image: "/products/run-jacket.svg", accent: "#1F4D3A" },
  { name: "Thames Run Short", nameKo: "템스 런 쇼츠", brand: "Briq Edit", category: "sports", subcategory: "running", basePrice: 89000, image: "/products/runner.svg", accent: "#243447" },
  { name: "Brixton Run Cap", nameKo: "브릭스턴 런 캡", brand: "Briq Edit", category: "sports", subcategory: "running", basePrice: 49000, image: "/products/cap.svg", accent: "#1A2E28" },
  { name: "Brighton Towel", nameKo: "브라이튼 타월", brand: "Briq Sport", category: "sports", subcategory: "swimming", basePrice: 69000, image: "/products/scarf.svg", accent: "#1E3A4A" },
  { name: "Hove Swim Cap", nameKo: "호브 스윔 캡", brand: "Briq Sport", category: "sports", subcategory: "swimming", basePrice: 39000, image: "/products/cap.svg", accent: "#1E4A3A" },
  { name: "Cotswold Cap", nameKo: "콧스월드 캡", brand: "Briq Sport", category: "sports", subcategory: "cycling", basePrice: 59000, image: "/products/cap.svg", accent: "#2A4038" },
  { name: "Chiltern Cycle Short", nameKo: "칠턴 사이클 쇼츠", brand: "Briq Sport", category: "sports", subcategory: "cycling", basePrice: 129000, image: "/products/runner.svg", accent: "#24302A" },
  { name: "Wimbledon Cap", nameKo: "윔블던 캡", brand: "Briq Sport", category: "sports", subcategory: "tennis", basePrice: 69000, image: "/products/cap.svg", accent: "#2F5A48" },
  { name: "Queen's Club Short", nameKo: "퀸즈클럽 쇼츠", brand: "Briq Sport", category: "sports", subcategory: "tennis", basePrice: 99000, image: "/products/runner.svg", accent: "#1E4A3A" },
];

const accents = [
  "#1A2428", "#2C241C", "#1F4D3A", "#243447", "#3A2F28",
  "#4A3038", "#2A3A45", "#314036", "#5C4A3A", "#1E3A4A",
];

const COLLECTION_TARGET = 100;

function expandToTarget(base: Product[], target: number): Product[] {
  if (base.length >= target) return base.slice(0, target);
  const out = [...base];
  let n = 0;
  while (out.length < target) {
    const seed = collectionSeeds[n % collectionSeeds.length];
    const edition = Math.floor(n / collectionSeeds.length) + 1;
    out.push({
      id: `briq-col-${String(n + 1).padStart(3, "0")}`,
      name: edition > 1 ? `${seed.name} ${edition}` : seed.name,
      nameKo: edition > 1 ? `${seed.nameKo} ${edition}` : seed.nameKo,
      brand: seed.brand,
      price: seed.basePrice + (edition - 1) * 10000,
      category: seed.category,
      subcategory: seed.subcategory,
      tags: ["collection"],
      descriptionKo: "Briq 컬렉션 에디트.",
      image: seed.image,
      accent: accents[n % accents.length] ?? seed.accent,
    });
    n += 1;
  }
  return out;
}

/** First 100 products for the homepage collection grid. */
export function getCollection100() {
  return expandToTarget(products, COLLECTION_TARGET);
}

// Grow the live catalogue to 100 so PDP links from the homepage work.
{
  const extras = expandToTarget(products, COLLECTION_TARGET).slice(products.length);
  products.push(...extras);
}

export function formatKrw(price: number) {
  return `${new Intl.NumberFormat("ko-KR", {
    maximumFractionDigits: 0,
  }).format(price)}원`;
}

export function getProduct(id: string) {
  if (id === "prl-chino-cap-old-royal") {
    return products.find((p) => p.id === "prl-chino-cap");
  }
  return products.find((p) => p.id === id);
}

export function getProductsByCategory(category?: string, sub?: string) {
  let list = products;
  if (category && category !== "all") {
    list = list.filter((p) => p.category === category);
  }
  const expanded = expandSubcategoryFilter(sub);
  if (expanded) {
    list = list.filter(
      (p) => p.subcategory && expanded.includes(p.subcategory),
    );
  }
  return list;
}

/** @deprecated use navCategories from categories.ts */
export const categories = [
  { id: "luxury" as const, label: "Luxury", labelKo: "명품럭셔리 의류" },
  { id: "watches" as const, label: "Watches", labelKo: "시계" },
  { id: "clothing" as const, label: "Clothing", labelKo: "패션의류" },
  { id: "bags" as const, label: "Bags", labelKo: "가방" },
  { id: "shoes" as const, label: "Shoes", labelKo: "슈즈" },
  { id: "accessories" as const, label: "Accessories", labelKo: "악세서리" },
  { id: "sports" as const, label: "Sports", labelKo: "스포츠" },
];
