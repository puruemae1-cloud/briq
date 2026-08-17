"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth";
import { updateDb } from "@/lib/db";
import { isAllowedProductUrl, storeFromUrl } from "@/lib/stores";
import { previewProductUrl } from "@/lib/preview";
import type { CartItem } from "@/lib/types";

export async function previewUrlAction(url: string) {
  return previewProductUrl(url);
}

export async function addCartItemAction(_prev: { error: string } | null, formData: FormData) {
  const me = await getCurrentUser();
  if (!me) return { error: "로그인이 필요합니다." };

  const url = String(formData.get("url") || "").trim();
  const titleIn = String(formData.get("title") || "").trim();
  const size = String(formData.get("size") || "").trim();
  const color = String(formData.get("color") || "").trim();
  const memo = String(formData.get("memo") || "").trim();
  const qty = Math.max(1, Number(formData.get("qty") || 1) || 1);
  const gbpRaw = String(formData.get("gbpPrice") || "").trim();
  const gbpPrice = gbpRaw ? Number(gbpRaw) : null;

  if (!isAllowedProductUrl(url)) {
    return { error: "메인에 있는 영국 스토어 상품 URL만 담을 수 있습니다." };
  }
  if (gbpPrice !== null && (!Number.isFinite(gbpPrice) || gbpPrice <= 0)) {
    return { error: "GBP 가격을 숫자로 입력해 주세요. 모르면 비워 두세요." };
  }

  let preview;
  try {
    preview = await previewProductUrl(url);
  } catch (err) {
    return { error: err instanceof Error ? err.message : "링크를 읽지 못했습니다." };
  }

  const store = storeFromUrl(url)!;
  const item: CartItem = {
    id: crypto.randomUUID(),
    url,
    storeId: store.id,
    storeName: store.nameEn,
    title: titleIn || preview.title,
    image: preview.image,
    size,
    color,
    qty,
    gbpPrice,
    memo,
    addedAt: new Date().toISOString(),
  };

  await updateDb((db) => {
    db.carts[me.id] = [...(db.carts[me.id] ?? []), item];
  });
  revalidatePath("/cart");
  redirect("/cart");
}

export async function removeCartItemAction(itemId: string) {
  const me = await getCurrentUser();
  if (!me) return;
  await updateDb((db) => {
    db.carts[me.id] = (db.carts[me.id] ?? []).filter((i) => i.id !== itemId);
  });
  revalidatePath("/cart");
}
