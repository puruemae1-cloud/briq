"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth";
import { updateDb } from "@/lib/db";
import { lookupProduct } from "@/lib/lookup";
import type { CartItem } from "@/lib/types";

export async function lookupProductAction(raw: string, storeId: string) {
  return lookupProduct(raw, storeId);
}

export async function addCartItemAction(_prev: { error: string } | null, formData: FormData) {
  const me = await getCurrentUser();
  if (!me) return { error: "로그인이 필요합니다." };

  const raw = String(formData.get("url") || "").trim();
  const titleIn = String(formData.get("title") || "").trim();
  const storeId = String(formData.get("storeId") || "asos").trim();
  const size = String(formData.get("size") || "").trim();
  const color = String(formData.get("color") || "").trim();
  const memo = String(formData.get("memo") || "").trim();
  const qty = Math.max(1, Number(formData.get("qty") || 1) || 1);

  let found;
  try {
    found = await lookupProduct(raw, storeId);
  } catch (err) {
    return { error: err instanceof Error ? err.message : "상품을 인식하지 못했습니다." };
  }

  const title = titleIn || found.title || found.storeName;
  const notes = [
    memo,
    found.source === "search" ? `${found.storeName}에서 상품 이름으로 검색` : "",
    found.gbpPrice
      ? found.priceSource === "search"
        ? `표시가 ${found.gbpPrice.toFixed(2)} GBP (검색 결과)`
        : `표시가 ${found.gbpPrice.toFixed(2)} GBP`
      : "스토어 가격을 못 찾아 운영자 확인",
  ].filter(Boolean);

  const item: CartItem = {
    id: crypto.randomUUID(),
    url: found.url,
    storeId: found.storeId,
    storeName: found.storeName,
    title,
    image: found.image,
    size,
    color,
    qty,
    gbpPrice: found.gbpPrice,
    memo: notes.join(" · "),
    addedAt: new Date().toISOString(),
    source: found.source,
    priceSource: found.priceSource,
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
