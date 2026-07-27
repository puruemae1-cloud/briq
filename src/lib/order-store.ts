"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { OrderRecord, ShippingStage } from "@/lib/orders";

export type OrderLine = {
  productId: string;
  variantId?: string;
  nameKo: string;
  qty: number;
  unitPrice: number;
  image: string;
};

export type MemberOrder = OrderRecord & {
  lines: OrderLine[];
  paymentMethod: string;
  paymentId: string;
};

type OrderState = {
  orders: MemberOrder[];
  addOrder: (order: MemberOrder) => void;
  ordersForUser: (userId: string) => MemberOrder[];
  setTracking: (
    orderId: string,
    trackingNumber: string,
    status?: ShippingStage,
  ) => void;
  setStatus: (orderId: string, status: ShippingStage) => void;
};

export const useOrderStore = create<OrderState>()(
  persist(
    (set, get) => ({
      orders: [],

      addOrder(order) {
        set((s) => ({ orders: [order, ...s.orders] }));
      },

      ordersForUser(userId) {
        return get().orders.filter((o) => o.userId === userId);
      },

      setTracking(orderId, trackingNumber, status = "waybill_issued") {
        const now = new Date().toISOString();
        set((s) => ({
          orders: s.orders.map((o) =>
            o.id === orderId
              ? {
                  ...o,
                  trackingNumber,
                  carrier: "ACI_EXPRESS",
                  status,
                  updatedAt: now,
                }
              : o,
          ),
        }));
      },

      setStatus(orderId, status) {
        const now = new Date().toISOString();
        set((s) => ({
          orders: s.orders.map((o) =>
            o.id === orderId ? { ...o, status, updatedAt: now } : o,
          ),
        }));
      },
    }),
    { name: "briq-orders-v1" },
  ),
);
