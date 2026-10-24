"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { MemberOrder, ShippingStage } from "@/lib/orders";

export type { MemberOrder, OrderLine } from "@/lib/orders";

type OrderState = {
  orders: MemberOrder[];
  addOrder: (order: MemberOrder) => void;
  upsertOrder: (order: MemberOrder) => void;
  mergeOrders: (incoming: MemberOrder[]) => void;
  ordersForUser: (userId: string) => MemberOrder[];
  setTracking: (
    orderId: string,
    trackingNumber: string,
    status?: ShippingStage,
  ) => void;
  setStatus: (orderId: string, status: ShippingStage) => void;
};

function mergeById(a: MemberOrder[], b: MemberOrder[]): MemberOrder[] {
  const map = new Map<string, MemberOrder>();
  for (const order of [...a, ...b]) {
    const prev = map.get(order.id);
    if (!prev || +new Date(order.updatedAt) >= +new Date(prev.updatedAt)) {
      map.set(order.id, order);
    }
  }
  return [...map.values()].sort(
    (x, y) => +new Date(y.createdAt) - +new Date(x.createdAt),
  );
}

export const useOrderStore = create<OrderState>()(
  persist(
    (set, get) => ({
      orders: [],

      addOrder(order) {
        set((s) => ({ orders: mergeById([order], s.orders) }));
      },

      upsertOrder(order) {
        set((s) => ({ orders: mergeById(s.orders, [order]) }));
      },

      mergeOrders(incoming) {
        if (!incoming.length) return;
        set((s) => ({ orders: mergeById(s.orders, incoming) }));
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
                  carrier: "ACI_EXPRESS" as const,
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

/** Persist order locally and mirror to the server inbox for admin. */
export async function recordOrder(order: MemberOrder) {
  useOrderStore.getState().addOrder(order);
  try {
    await fetch("/api/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(order),
    });
  } catch {
    /* admin inbox sync is best-effort */
  }
}
