import AsyncStorage from "@react-native-async-storage/async-storage";
import { useCallback, useEffect, useState } from "react";

const ORDERS_KEY = "briq-mobile-orders-v1";

export type MobileOrder = {
  id: string;
  userId: string;
  paymentId: string;
  paymentMethod: string;
  status:
    | "paid"
    | "waybill_issued"
    | "in_transit"
    | "customs_cleared"
    | "delivered";
  trackingNumber?: string;
  totalKrw: number;
  customsCode: string;
  customerName: string;
  customerPhone: string;
  address: string;
  lines: { nameKo: string; qty: number; unitPrice: number }[];
  createdAt: string;
};

export const STATUS_LABEL: Record<MobileOrder["status"], string> = {
  paid: "주문 접수",
  waybill_issued: "송장 작성 완료",
  in_transit: "배송 시작",
  customs_cleared: "통관 완료",
  delivered: "배송 완료",
};

export function useMobileOrders(userId?: string | null) {
  const [orders, setOrders] = useState<MobileOrder[]>([]);

  const reload = useCallback(async () => {
    try {
      const raw = await AsyncStorage.getItem(ORDERS_KEY);
      const all = raw ? (JSON.parse(raw) as MobileOrder[]) : [];
      setOrders(userId ? all.filter((o) => o.userId === userId) : []);
    } catch {
      setOrders([]);
    }
  }, [userId]);

  useEffect(() => {
    reload();
  }, [reload]);

  const addOrder = useCallback(
    async (order: MobileOrder) => {
      const raw = await AsyncStorage.getItem(ORDERS_KEY);
      const all = raw ? (JSON.parse(raw) as MobileOrder[]) : [];
      const next = [order, ...all];
      await AsyncStorage.setItem(ORDERS_KEY, JSON.stringify(next));
      if (userId) setOrders(next.filter((o) => o.userId === userId));
    },
    [userId],
  );

  return { orders, addOrder, reload };
}
