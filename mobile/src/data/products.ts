export type CategoryId =
  | "luxury"
  | "watches"
  | "clothing"
  | "bags"
  | "shoes"
  | "accessories"
  | "sports";

export type ProductVariant = {
  id: string;
  name: string;
  nameKo: string;
  sku: string;
  gbpPrice: number;
  price: number;
  /** Local require() asset or remote URI string */
  image: number;
  inStock: boolean;
};

export type Product = {
  id: string;
  name: string;
  nameKo: string;
  brand: string;
  price: number;
  category: CategoryId;
  descriptionKo?: string;
  accent: string;
  badge?: string;
  image?: number;
  variants?: ProductVariant[];
};

/** KRW = GBP × 2100 × 1.06 + 20,000 */
export function gbpToBriqKrw(gbp: number) {
  return Math.round(gbp * 2100 * 1.06 + 20000);
}

const chinoCapVariants: ProductVariant[] = [
  {
    id: "black-white",
    name: "black/white",
    nameKo: "블랙/화이트",
    sku: "PO252P011-Q11",
    gbpPrice: 70,
    price: gbpToBriqKrw(70),
    image: require("../../assets/products/prl-chino-cap-black-white.jpg"),
    inStock: true,
  },
  {
    id: "company-olive",
    name: "company olive",
    nameKo: "컴퍼니 올리브",
    sku: "PO252P011-M15",
    gbpPrice: 70,
    price: gbpToBriqKrw(70),
    image: require("../../assets/products/prl-chino-cap-company-olive.jpg"),
    inStock: true,
  },
  {
    id: "cruise-lime",
    name: "cruise lime",
    nameKo: "크루즈 라임",
    sku: "PO252P011-K19",
    gbpPrice: 60,
    price: gbpToBriqKrw(60),
    image: require("../../assets/products/prl-chino-cap-cruise-lime.jpg"),
    inStock: true,
  },
  {
    id: "garden-trail-cream",
    name: "garden trail/cream pp",
    nameKo: "가든 트레일/크림",
    sku: "PO252P011-Q12",
    gbpPrice: 54,
    price: gbpToBriqKrw(54),
    image: require("../../assets/products/prl-chino-cap-garden-trail-cream.jpg"),
    inStock: true,
  },
  {
    id: "new-forest",
    name: "new forest",
    nameKo: "뉴 포레스트",
    sku: "PO252P011-M11",
    gbpPrice: 70,
    price: gbpToBriqKrw(70),
    image: require("../../assets/products/prl-chino-cap-new-forest.jpg"),
    inStock: true,
  },
  {
    id: "rustic-navy",
    name: "rustic navy",
    nameKo: "러스틱 네이비",
    sku: "PO252P011-K13",
    gbpPrice: 70,
    price: gbpToBriqKrw(70),
    image: require("../../assets/products/prl-chino-cap-rustic-navy.jpg"),
    inStock: true,
  },
  {
    id: "rustic-tan",
    name: "rustic tan",
    nameKo: "러스틱 탄",
    sku: "PO252P011-B11",
    gbpPrice: 54,
    price: gbpToBriqKrw(54),
    image: require("../../assets/products/prl-chino-cap-rustic-tan.jpg"),
    inStock: true,
  },
  {
    id: "terrace-pink",
    name: "terrace pink/c7560",
    nameKo: "테라스 핑크",
    sku: "PO252P011-J11",
    gbpPrice: 70,
    price: gbpToBriqKrw(70),
    image: require("../../assets/products/prl-chino-cap-terrace-pink.jpg"),
    inStock: true,
  },
  {
    id: "wisteria",
    name: "wisteria w/ c9601",
    nameKo: "위스테리아",
    sku: "PO252P011-I12",
    gbpPrice: 70,
    price: gbpToBriqKrw(70),
    image: require("../../assets/products/prl-chino-cap-wisteria.jpg"),
    inStock: true,
  },
];

const chinoCapMinPrice = Math.min(...chinoCapVariants.map((v) => v.price));

export const categories: { id: CategoryId | "all"; labelKo: string }[] = [
  { id: "all", labelKo: "전체" },
  { id: "luxury", labelKo: "명품럭셔리 의류" },
  { id: "watches", labelKo: "시계" },
  { id: "clothing", labelKo: "패션의류" },
  { id: "bags", labelKo: "가방" },
  { id: "shoes", labelKo: "슈즈" },
  { id: "accessories", labelKo: "악세서리" },
  { id: "sports", labelKo: "스포츠" },
];

export const products: Product[] = [
  {
    id: "prl-chino-cap",
    name: "The Iconic Cotton Chino Ball Cap",
    nameKo: "폴로 랄프 로렌 아이코닉 코튼 치노 볼캡",
    brand: "Polo Ralph Lauren",
    price: chinoCapMinPrice,
    category: "accessories",
    descriptionKo: "100% 코튼 치노 볼캡. 포니 자수, 버클 조절 스트랩. 사이즈 One Size.",
    accent: "#1a1a1a",
    badge: "New",
    image: chinoCapVariants[0].image,
    variants: chinoCapVariants,
  },
  {
    id: "briq-run-jacket",
    name: "Brixton Run Shell",
    nameKo: "브릭스턴 런 셸 재킷",
    brand: "Briq Edit",
    price: 189000,
    category: "sports",
    descriptionKo: "시티 러닝과 주말 트레일을 위한 경량 방수 셸.",
    accent: "#1F4D3A",
    badge: "New",
  },
  {
    id: "briq-track-tee",
    name: "Track Day Tee",
    nameKo: "트랙 데이 티셔츠",
    brand: "Briq Edit",
    price: 59000,
    category: "sports",
    descriptionKo: "영국식 애슬레틱 실루엣의 통기성 좋은 코튼 티.",
    accent: "#243447",
  },
  {
    id: "briq-wool-coat",
    name: "Mayfair Wool Coat",
    nameKo: "메이페어 울 코트",
    brand: "Briq Atelier",
    price: 429000,
    category: "clothing",
    descriptionKo: "부티크 테일러링이 돋보이는 구조감 울 코트.",
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
    descriptionKo: "부드러운 메리노, 절제된 모던 드레이프.",
    accent: "#5C4A3A",
  },
  {
    id: "briq-tote",
    name: "Soho Leather Tote",
    nameKo: "소호 레더 토트",
    brand: "Briq Goods",
    price: 259000,
    category: "bags",
    descriptionKo: "풀그레인 가죽의 데일리 토트백.",
    accent: "#6B3E2E",
  },
  {
    id: "briq-crossbody",
    name: "Fleet Crossbody",
    nameKo: "플리트 크로스바디",
    brand: "Briq Goods",
    price: 129000,
    category: "bags",
    descriptionKo: "시티 트래블에 맞춘 컴팩트 크로스바디.",
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
    descriptionKo: "네 글자 마크. 앱 아이콘처럼 강렬하게.",
    accent: "#0E1A17",
  },
  {
    id: "briq-scarf",
    name: "Thames Check Scarf",
    nameKo: "템스 체크 스카프",
    brand: "Briq Atelier",
    price: 89000,
    category: "accessories",
    descriptionKo: "런던 겨울 무드의 소프트 체크 스카프.",
    accent: "#4A5560",
  },
  {
    id: "briq-runner",
    name: "Brixton Runner",
    nameKo: "브릭스턴 러너",
    brand: "Briq Sport",
    price: 179000,
    category: "shoes",
    descriptionKo: "절제된 영국식 실루엣의 데일리 러너.",
    accent: "#1A2E28",
  },
  {
    id: "briq-loafer",
    name: "Bond Street Loafer",
    nameKo: "본드스트리트 로퍼",
    brand: "Briq Atelier",
    price: 219000,
    category: "shoes",
    descriptionKo: "데스크부터 디너까지, 폴리시드 레더 로퍼.",
    accent: "#3A2F28",
  },
  {
    id: "briq-bottle",
    name: "Briq Day Bottle",
    nameKo: "브릭 데이 보틀",
    brand: "Briq Lifestyle",
    price: 39000,
    category: "sports",
    descriptionKo: "트레이닝과 트래블용 매트 스틸 보틀.",
    accent: "#2A3A45",
  },
  {
    id: "briq-pouch",
    name: "Edit Tech Pouch",
    nameKo: "에디트 테크 파우치",
    brand: "Briq Lifestyle",
    price: 45000,
    category: "accessories",
    descriptionKo: "케이블·카드·소품을 담는 컴팩트 파우치.",
    accent: "#314036",
  },
];

export function formatKrw(price: number) {
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: "KRW",
    maximumFractionDigits: 0,
  }).format(price);
}

export function getProduct(id: string) {
  if (id === "prl-chino-cap-old-royal") {
    return products.find((p) => p.id === "prl-chino-cap");
  }
  return products.find((p) => p.id === id);
}
