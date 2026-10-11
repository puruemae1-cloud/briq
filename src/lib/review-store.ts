"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type ReviewMedia = {
  id: string;
  type: "image" | "video";
  dataUrl: string;
  name: string;
};

export type ReviewItem = {
  id: string;
  productId: string;
  productName: string;
  authorName: string;
  authorEmail?: string;
  userId?: string;
  rating: number;
  body: string;
  media: ReviewMedia[];
  createdAt: string;
  couponId?: string;
  couponAmountKrw?: number;
};

type ReviewState = {
  items: ReviewItem[];
  add: (item: ReviewItem) => void;
  forProduct: (productId: string) => ReviewItem[];
};

export const useReviewStore = create<ReviewState>()(
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
    { name: "briq-reviews-v1" },
  ),
);

/** Compress images client-side so localStorage stays usable. */
export async function readMediaFile(file: File): Promise<ReviewMedia> {
  const id = `media-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;

  if (file.type.startsWith("video/")) {
    if (file.size > 8 * 1024 * 1024) {
      throw new Error("동영상은 8MB 이하만 첨부할 수 있습니다.");
    }
    const dataUrl = await readAsDataUrl(file);
    return { id, type: "video", dataUrl, name: file.name };
  }

  if (!file.type.startsWith("image/")) {
    throw new Error("이미지 또는 동영상만 첨부할 수 있습니다.");
  }

  const dataUrl = await compressImage(file, 1400, 0.72);
  return { id, type: "image", dataUrl, name: file.name };
}

function readAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(new Error("파일을 읽지 못했습니다."));
    reader.readAsDataURL(file);
  });
}

function compressImage(
  file: File,
  maxEdge: number,
  quality: number,
): Promise<string> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      const scale = Math.min(1, maxEdge / Math.max(img.width, img.height));
      const w = Math.max(1, Math.round(img.width * scale));
      const h = Math.max(1, Math.round(img.height * scale));
      const canvas = document.createElement("canvas");
      canvas.width = w;
      canvas.height = h;
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        URL.revokeObjectURL(url);
        reject(new Error("이미지 압축에 실패했습니다."));
        return;
      }
      ctx.drawImage(img, 0, 0, w, h);
      URL.revokeObjectURL(url);
      resolve(canvas.toDataURL("image/jpeg", quality));
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("이미지를 불러오지 못했습니다."));
    };
    img.src = url;
  });
}
