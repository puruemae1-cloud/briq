export type StoreMode = "purchase" | "forward" | "both";
export type Role = "customer" | "admin";

export type User = {
  id: string;
  email: string;
  passwordHash: string;
  salt: string;
  name: string;
  phone: string;
  address: string;
  customsCode: string;
  role: Role;
  createdAt: string;
};

export type CartItem = {
  id: string;
  url: string;
  storeId: string;
  storeName: string;
  title: string;
  image: string;
  size: string;
  color: string;
  qty: number;
  gbpPrice: number | null;
  memo: string;
  addedAt: string;
  source?: "url" | "search";
  priceSource?: "pdp" | "search" | null;
};

export type OrderStatus =
  | "needs_price"
  | "quoted"
  | "payment_pending"
  | "paid"
  | "buying_uk"
  | "purchased"
  | "in_warehouse"
  | "shipped"
  | "customs"
  | "delivered"
  | "cancelled_refund";

export type Order = {
  id: string;
  number: string;
  userId: string;
  customer: {
    name: string;
    email: string;
    phone: string;
    address: string;
    customsCode: string;
  };
  items: CartItem[];
  fx: {
    gbpKrw: number;
    source: string;
    fetchedAt: string;
    margin: number;
  };
  fees: {
    agencyRate: number;
    shippingEstKrw: number;
  };
  goodsGbp: number | null;
  quotedKrw: number | null;
  quotedUntil: string | null;
  status: OrderStatus;
  adminNote: string;
  createdAt: string;
  updatedAt: string;
};

export const ORDER_STATUS_LABEL: Record<OrderStatus, string> = {
  needs_price: "가격 확인 중",
  quoted: "견적 확인",
  payment_pending: "입금 대기",
  paid: "결제 확인",
  buying_uk: "영국 구매 중",
  purchased: "영국 구매 완료",
  in_warehouse: "창고 입고",
  shipped: "국제 배송",
  customs: "통관",
  delivered: "배송 완료",
  cancelled_refund: "취소·환불",
};

export const FEE = {
  fxMargin: 0.03,
  agencyRate: 0,
  shippingKrw: 20000,
  cardRate: 0.05,
  quoteTtlHours: 12,
} as const;
