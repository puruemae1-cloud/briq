"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { CheckoutProfile } from "@/lib/checkout-profile";

export type BriqUser = {
  id: string;
  email: string;
  name: string;
  phone?: string;
  /** Demo password hash — replace with real auth server later */
  passwordHash: string;
  createdAt: string;
  profile?: CheckoutProfile;
};

type AuthState = {
  users: BriqUser[];
  sessionUserId: string | null;
  signup: (input: {
    email: string;
    password: string;
    name: string;
    phone?: string;
  }) => { ok: true } | { ok: false; message: string };
  login: (
    email: string,
    password: string,
  ) => { ok: true } | { ok: false; message: string };
  logout: () => void;
  updateProfile: (profile: CheckoutProfile) => void;
  currentUser: () => BriqUser | null;
};

/** Lightweight client hash for demo accounts only — not for production. */
export function hashPassword(password: string) {
  let h = 2166136261;
  for (let i = 0; i < password.length; i++) {
    h ^= password.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return `demo_${(h >>> 0).toString(16)}`;
}

function newId() {
  return `u_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      users: [],
      sessionUserId: null,

      currentUser() {
        const { users, sessionUserId } = get();
        if (!sessionUserId) return null;
        return users.find((u) => u.id === sessionUserId) ?? null;
      },

      signup({ email, password, name, phone }) {
        const normalized = email.trim().toLowerCase();
        if (!normalized || !normalized.includes("@")) {
          return { ok: false, message: "올바른 이메일을 입력해 주세요." };
        }
        if (password.length < 6) {
          return { ok: false, message: "비밀번호는 6자 이상이어야 합니다." };
        }
        if (!name.trim()) {
          return { ok: false, message: "이름을 입력해 주세요." };
        }
        if (get().users.some((u) => u.email === normalized)) {
          return { ok: false, message: "이미 가입된 이메일입니다." };
        }

        const user: BriqUser = {
          id: newId(),
          email: normalized,
          name: name.trim(),
          phone: phone?.trim() || undefined,
          passwordHash: hashPassword(password),
          createdAt: new Date().toISOString(),
        };

        set((s) => ({
          users: [...s.users, user],
          sessionUserId: user.id,
        }));
        return { ok: true };
      },

      login(email, password) {
        const normalized = email.trim().toLowerCase();
        const user = get().users.find((u) => u.email === normalized);
        if (!user || user.passwordHash !== hashPassword(password)) {
          return { ok: false, message: "이메일 또는 비밀번호가 올바르지 않습니다." };
        }
        set({ sessionUserId: user.id });
        return { ok: true };
      },

      logout() {
        set({ sessionUserId: null });
      },

      updateProfile(profile) {
        const id = get().sessionUserId;
        if (!id) return;
        set((s) => ({
          users: s.users.map((u) =>
            u.id === id ? { ...u, profile, name: profile.name || u.name, phone: profile.phone || u.phone } : u,
          ),
        }));
      },
    }),
    { name: "briq-auth-v1" },
  ),
);
