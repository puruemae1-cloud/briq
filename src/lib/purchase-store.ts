"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

/** Number of paid units required for a product to appear in "Best Items". */
export const BEST_THRESHOLD = 1;

type PurchaseLine = { id: string; qty: number };

type PurchaseState = {
  counts: Record<string, number>;
  record: (lines: PurchaseLine[]) => void;
  getCount: (id: string) => number;
};

export const usePurchases = create<PurchaseState>()(
  persist(
    (set, get) => ({
      counts: {},
      record: (lines) =>
        set((state) => {
          const counts = { ...state.counts };
          for (const { id, qty } of lines) {
            counts[id] = (counts[id] ?? 0) + Math.max(1, qty);
          }
          return { counts };
        }),
      getCount: (id) => get().counts[id] ?? 0,
    }),
    { name: "briq-purchases" },
  ),
);
