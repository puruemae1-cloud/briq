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
  image: number | string;
  images?: Array<number | string>;
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
  image?: number | string;
  images?: Array<number | string>;
  variants?: ProductVariant[];
  featuresKo?: string[];
  techSpecs?: Array<{ labelKo: string; valueKo: string }>;
};

/** KRW = round_만원(GBP × 2100 × 1.05 + 200,000) */
export function gbpToBriqKrw(gbp: number) {
  return Math.round((gbp * 2100 * 1.05 + 200_000) / 10_000) * 10_000;
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
  { id: "luxury", labelKo: "명품 하이엔드 의류" },
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
