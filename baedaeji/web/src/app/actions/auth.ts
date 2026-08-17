"use server";

import { redirect } from "next/navigation";
import {
  clearSession,
  hashPassword,
  isAdminCode,
  isAdminEmail,
  setSession,
  verifyPassword,
} from "@/lib/auth";
import { readOnlyDb, updateDb } from "@/lib/db";

function formError(message: string) {
  return { error: message };
}

export async function registerAction(_prev: { error: string } | null, formData: FormData) {
  const email = String(formData.get("email") || "")
    .trim()
    .toLowerCase();
  const password = String(formData.get("password") || "");
  const name = String(formData.get("name") || "").trim();
  const phone = String(formData.get("phone") || "").trim();
  const address = String(formData.get("address") || "").trim();
  const adminCode = String(formData.get("adminCode") || "").trim();

  if (!email.includes("@")) return formError("이메일을 확인해 주세요.");
  if (password.length < 8) return formError("비밀번호는 8자 이상이어야 합니다.");
  if (!name) return formError("이름을 입력해 주세요.");

  const user = await updateDb((db) => {
    if (db.users.some((u) => u.email === email)) {
      throw new Error("already");
    }
    const { hash, salt } = hashPassword(password);
    const role =
      isAdminEmail(email) || isAdminCode(adminCode) ? ("admin" as const) : ("customer" as const);
    const next = {
      id: crypto.randomUUID(),
      email,
      passwordHash: hash,
      salt,
      name,
      phone,
      address,
      customsCode: "",
      role,
      createdAt: new Date().toISOString(),
    };
    db.users.push(next);
    db.carts[next.id] = [];
    return next;
  }).catch((err: unknown) => {
    if (err instanceof Error && err.message === "already") return null;
    throw err;
  });

  if (!user) return formError("이미 가입된 이메일입니다.");
  await setSession(user);
  redirect("/cart");
}

export async function loginAction(_prev: { error: string } | null, formData: FormData) {
  const email = String(formData.get("email") || "")
    .trim()
    .toLowerCase();
  const password = String(formData.get("password") || "");
  const next = String(formData.get("next") || "/cart");

  const db = await readOnlyDb();
  const user = db.users.find((u) => u.email === email) ?? null;
  if (!user || !verifyPassword(password, user.salt, user.passwordHash)) {
    return formError("이메일 또는 비밀번호가 올바르지 않습니다.");
  }
  await setSession(user);
  redirect(next.startsWith("/") && !next.startsWith("//") ? next : "/cart");
}

export async function logoutAction() {
  await clearSession();
  redirect("/");
}

export async function updateProfileAction(_prev: { error: string } | null, formData: FormData) {
  const { getCurrentUser } = await import("@/lib/auth");
  const me = await getCurrentUser();
  if (!me) return formError("로그인이 필요합니다.");
  const name = String(formData.get("name") || "").trim();
  const phone = String(formData.get("phone") || "").trim();
  const address = String(formData.get("address") || "").trim();
  const customsCode = String(formData.get("customsCode") || "").trim();
  if (!name) return formError("이름을 입력해 주세요.");
  await updateDb((db) => {
    const user = db.users.find((u) => u.id === me.id);
    if (!user) return;
    user.name = name;
    user.phone = phone;
    user.address = address;
    user.customsCode = customsCode;
  });
  redirect("/orders");
}
