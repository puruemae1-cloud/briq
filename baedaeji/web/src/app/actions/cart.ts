"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth";
import { updateDb } from "@/lib/db";
import { previewProductUrl } from "@/lib/preview";
import { resolveProductInput } from "@/lib/product-input";
import type { CartItem } from "@/lib/types";

export async function previewUrlAction(url: string) {
  return previewProductUrl(url);
}

export async function addCartItemAction(_prev: { error: string } | null, formData: FormData) {
  const me = await getCurrentUser();
  if (!me) return { error: "로그인이 필요합니다." };

  const url = String(formData.get("url") || "").trim();
  const titleIn = String(formData.get("title") || "").trim();
  const storeId = String(formData.get("storeId") || "asos").trim();
  const size = String(formData.get("size") || "").trim();
  const color = String(formData.get("color") || "").trim();
  const memo = String(formData.get("memo") || "").trim();
  const qty = Math.max(1, Number(formData.get("qty") || 1) || 1);
  const gbpRaw = String(formData.get("gbpPrice") || "").trim();
  const gbpPrice = gbpRaw ? Number(gbpRaw) : null;

  let resolved;
  try {
    resolved = resolveProductInput(url, storeId);
  } catch (err) {
    return { error: err instanceof Error ? err.message : "상품을 인식하지 못했습니다." };
  }
  if (gbpPrice !== null && (!Number.isFinite(gbpPrice) || gbpPrice <= 0)) {
    return { error: "GBP 가격을 숫자로 입력해 주세요. 모르면 비워 두세요." };
  }

  let title = titleIn || resolved.title;
  let image = "";
  if (resolved.kind === "url") {
    try {
      const preview = await previewProductUrl(resolved.url);
      title = titleIn || preview.title;
      image = preview.image;
    } catch (err) {
      return { error: err instanceof Error ? err.message : "링크를 읽지 못했습니다." };
    }
  }
  if (!title) title = resolved.store.nameEn;

  const item: CartItem = {
    id: crypto.randomUUID(),
    url: resolved.url,
    storeId: resolved.store.id,
    storeName: resolved.store.nameEn,
    title,
    image,
    size,
    color,
    qty,
    gbpPrice,
    memo:
      resolved.kind === "search"
        ? [memo, `${resolved.store.nameEn}에서 상품 이름으로 검색`].filter(Boolean).join(" · ")
        : memo,
    addedAt: new Date().toISOString(),
    source: resolved.kind,
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
