/**
 * Order + shipping stage model (foundation for membership / push).
 *
 * Flow once accounts + admin exist:
 * 1. Checkout creates an Order (status: paid)
 * 2. Admin enters ACI EXPRESS waybill → status: waybill_issued → push
 * 3. Carrier departs UK → status: in_transit → push
 * 4. KR customs cleared → status: customs_cleared → push
 * 5. Delivered → status: delivered → push
 *
 * Push channel: Expo Push Notifications (mobile) + optional Kakao/Alimtalk.
 */

export type ShippingStage =
  | "paid"
  | "waybill_issued"
  | "in_transit"
  | "customs_cleared"
  | "delivered";

export const SHIPPING_STAGE_COPY: Record<
  ShippingStage,
  { title: string; body: string }
> = {
  paid: {
    title: "주문이 접수되었습니다",
    body: "결제가 완료되었습니다. 영국 현지 출고를 준비합니다.",
  },
  waybill_issued: {
    title: "송장 작성이 완료되었습니다",
    body: "ACI EXPRESS 송장이 등록되었습니다. 곧 배송이 시작됩니다.",
  },
  in_transit: {
    title: "배송이 시작되었습니다",
    body: "상품이 영국에서 출고되어 배송 중입니다.",
  },
  customs_cleared: {
    title: "통관이 완료되었습니다",
    body: "국내 통관이 완료되어 배송지로 이동합니다.",
  },
  delivered: {
    title: "배송이 완료되었습니다",
    body: "상품이 도착했습니다. Briq를 이용해 주셔서 감사합니다.",
  },
};

export type OrderRecord = {
  id: string;
  userId?: string;
  paymentId?: string;
  status: ShippingStage;
  /** ACI EXPRESS waybill / tracking number */
  trackingNumber?: string;
  carrier?: "ACI_EXPRESS";
  customsCode: string;
  customerName: string;
  customerPhone: string;
  address: string;
  totalKrw: number;
  createdAt: string;
  updatedAt: string;
};
