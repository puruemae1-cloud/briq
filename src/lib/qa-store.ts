"use client";

import { create } from "zustand";
import { ADMIN_PASSWORD, hashPassword } from "@/lib/auth-store";

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
  setItems: (items: QaItem[]) => void;
  add: (item: QaItem) => void;
  answer: (
    id: string,
    answer: string,
    answeredBy: string,
  ) => { ok: true } | { ok: false; message: string };
  forProduct: (productId: string) => QaItem[];
  unanswered: () => QaItem[];
};

export const useQaStore = create<QaState>()((set, get) => ({
  items: [],
  setItems(items) {
    set({ items });
  },
  add(item) {
    set((s) => ({
      items: [item, ...s.items.filter((row) => row.id !== item.id)],
    }));
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
}));

export function qaStaffHeaders(): HeadersInit {
  return {
    "Content-Type": "application/json",
    "x-briq-staff": hashPassword(ADMIN_PASSWORD),
  };
}

export async function refreshQa(
  productId?: string,
  opts?: { staff?: boolean },
) {
  const query = productId ? `?productId=${encodeURIComponent(productId)}` : "";
  const headers: HeadersInit = opts?.staff ? qaStaffHeaders() : {};
  const res = await fetch(`/api/qa${query}`, { cache: "no-store", headers });
  if (!res.ok) return;
  const data = (await res.json()) as { ok?: boolean; items?: QaItem[] };
  if (!data.ok || !Array.isArray(data.items)) return;
  if (productId) {
    const rest = useQaStore
      .getState()
      .items.filter((item) => item.productId !== productId);
    useQaStore.getState().setItems([...data.items, ...rest]);
    return;
  }
  useQaStore.getState().setItems(data.items);
}
