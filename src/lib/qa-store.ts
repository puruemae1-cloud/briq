"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type QaVisibility = "public" | "private";

export type QaItem = {
  id: string;
  productId: string;
  productName: string;
  authorName: string;
  authorEmail?: string;
  authorPhone?: string;
  question: string;
  visibility: QaVisibility;
  createdAt: string;
  answer?: string;
  answeredAt?: string;
};

type QaState = {
  items: QaItem[];
  add: (item: QaItem) => void;
  forProduct: (productId: string) => QaItem[];
};

export const useQaStore = create<QaState>()(
  persist(
    (set, get) => ({
      items: [],
      add(item) {
        set((s) => ({ items: [item, ...s.items] }));
      },
      forProduct(productId) {
        return get().items.filter((i) => i.productId === productId);
      },
    }),
    { name: "briq-qa-v1" },
  ),
);
