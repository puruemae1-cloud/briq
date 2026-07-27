"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { getProduct } from "@/data/products";
import {
  readCartLines,
  removeCartLine,
  setCartLineQty,
  upsertCartLine,
  writeCartLines,
} from "@/lib/cart-server";

function revalidateCart() {
  revalidatePath("/", "layout");
  revalidatePath("/cart");
  revalidatePath("/checkout");
}

async function upsertFromForm(formData: FormData) {
  const productId = String(formData.get("productId") || "");
  const variantIdRaw = String(formData.get("variantId") || "");
  const variantId = variantIdRaw || undefined;
  const qty = Math.max(1, Number(formData.get("qty") || 1) || 1);

  const product = getProduct(productId);
  if (!product) {
    redirect("/shop");
  }

  if (variantId) {
    const variant = product.variants?.find((v) => v.id === variantId && v.inStock);
    if (!variant) {
      redirect(`/product/${productId}`);
    }
  } else if ((product.variants?.length ?? 0) > 0) {
    redirect(`/product/${productId}`);
  } else if (product.inStock === false) {
    redirect(`/product/${productId}`);
  }

  const lines = await readCartLines();
  await writeCartLines(upsertCartLine(lines, productId, qty, variantId));
  revalidateCart();
  return productId;
}

export async function addToCart(formData: FormData) {
  await upsertFromForm(formData);
  redirect("/cart");
}

/** Add current item then go straight to checkout. */
export async function buyNow(formData: FormData) {
  await upsertFromForm(formData);
  redirect("/checkout");
}

export async function updateCartQty(formData: FormData) {
  const productId = String(formData.get("productId") || "");
  const variantIdRaw = String(formData.get("variantId") || "");
  const variantId = variantIdRaw || undefined;
  const qty = Number(formData.get("qty") || 0);

  if (!productId) return;

  const lines = await readCartLines();
  await writeCartLines(setCartLineQty(lines, productId, qty, variantId));
  revalidateCart();
}

export async function removeFromCart(formData: FormData) {
  const productId = String(formData.get("productId") || "");
  const variantIdRaw = String(formData.get("variantId") || "");
  const variantId = variantIdRaw || undefined;

  if (!productId) return;

  const lines = await readCartLines();
  await writeCartLines(removeCartLine(lines, productId, variantId));
  revalidateCart();
}

export async function clearCart() {
  await writeCartLines([]);
  revalidateCart();
}
