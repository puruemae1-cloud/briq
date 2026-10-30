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
  answeredBy?: string;
};

type QaState = {
  items: QaItem[];
  add: (item: QaItem) => void;
  answer: (
    id: string,
    answer: string,
    answeredBy: string,
  ) => { ok: true } | { ok: false; message: string };
  forProduct: (productId: string) => QaItem[];
  unanswered: () => QaItem[];
};

export const useQaStore = create<QaState>()(
  persist(
    (set, get) => ({
      items: [],
      add(item) {
        set((s) => ({ items: [item, ...s.items] }));
      },
      answer(id, answer, answeredBy) {
        const text = answer.trim();
        if (!text) {
          return { ok: false, message: "답변 내용을 입력해 주세요." };
        }
        const exists = get().items.some((i) => i.id === id);
        if (!exists) {
          return { ok: false, message: "문의를 찾을 수 없습니다." };
        }
        const now = new Date().toISOString();
        set((s) => ({
          items: s.items.map((i) =>
            i.id === id
              ? {
                  ...i,
                  answer: text,
                  answeredAt: now,
                  answeredBy,
                }
              : i,
          ),
        }));
        return { ok: true };
      },
      forProduct(productId) {
        return get().items.filter((i) => i.productId === productId);
      },
      unanswered() {
        return get().items.filter((i) => !i.answer);
      },
    }),
    { name: "briq-qa-v1" },
  ),
);
