import AsyncStorage from "@react-native-async-storage/async-storage";
import { useCallback, useEffect, useState } from "react";

const AUTH_KEY = "briq-mobile-auth-v1";

export type MobileUser = {
  id: string;
  email: string;
  name: string;
  phone?: string;
  passwordHash: string;
  createdAt: string;
  profile?: {
    name: string;
    phone: string;
    customsCode: string;
    address: string;
  };
};

type AuthBlob = {
  users: MobileUser[];
  sessionUserId: string | null;
};

function hashPassword(password: string) {
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

async function readAuth(): Promise<AuthBlob> {
  try {
    const raw = await AsyncStorage.getItem(AUTH_KEY);
    if (!raw) return { users: [], sessionUserId: null };
    return JSON.parse(raw) as AuthBlob;
  } catch {
    return { users: [], sessionUserId: null };
  }
}

async function writeAuth(blob: AuthBlob) {
  await AsyncStorage.setItem(AUTH_KEY, JSON.stringify(blob));
}

export function useMobileAuth() {
  const [users, setUsers] = useState<MobileUser[]>([]);
  const [sessionUserId, setSessionUserId] = useState<string | null>(null);
  const [unlocked, setUnlocked] = useState(true);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    readAuth().then((blob) => {
      setUsers(blob.users);
      setSessionUserId(blob.sessionUserId);
      setReady(true);
    });
  }, []);

  const currentUser =
    users.find((u) => u.id === sessionUserId) ?? null;

  const signup = useCallback(
    async (input: {
      email: string;
      password: string;
      name: string;
      phone?: string;
    }) => {
      const blob = await readAuth();
      const email = input.email.trim().toLowerCase();
      if (!email.includes("@")) {
        return { ok: false as const, message: "올바른 이메일을 입력해 주세요." };
      }
      if (input.password.length < 6) {
        return { ok: false as const, message: "비밀번호는 6자 이상이어야 합니다." };
      }
      if (blob.users.some((u) => u.email === email)) {
        return { ok: false as const, message: "이미 가입된 이메일입니다." };
      }
      const user: MobileUser = {
        id: newId(),
        email,
        name: input.name.trim(),
        phone: input.phone?.trim(),
        passwordHash: hashPassword(input.password),
        createdAt: new Date().toISOString(),
      };
      const next = {
        users: [...blob.users, user],
        sessionUserId: user.id,
      };
      await writeAuth(next);
      setUsers(next.users);
      setSessionUserId(user.id);
      setUnlocked(true);
      return { ok: true as const };
    },
    [],
  );

  const login = useCallback(async (email: string, password: string) => {
    const blob = await readAuth();
    const user = blob.users.find(
      (u) => u.email === email.trim().toLowerCase(),
    );
    if (!user || user.passwordHash !== hashPassword(password)) {
      return {
        ok: false as const,
        message: "이메일 또는 비밀번호가 올바르지 않습니다.",
      };
    }
    const next = { ...blob, sessionUserId: user.id };
    await writeAuth(next);
    setUsers(next.users);
    setSessionUserId(user.id);
    setUnlocked(true);
    return { ok: true as const };
  }, []);

  const logout = useCallback(async () => {
    const blob = await readAuth();
    const next = { ...blob, sessionUserId: null };
    await writeAuth(next);
    setSessionUserId(null);
    setUnlocked(true);
  }, []);

  const updateProfile = useCallback(
    async (profile: NonNullable<MobileUser["profile"]>) => {
      if (!sessionUserId) return;
      const blob = await readAuth();
      const next = {
        ...blob,
        users: blob.users.map((u) =>
          u.id === sessionUserId
            ? {
                ...u,
                profile,
                name: profile.name || u.name,
                phone: profile.phone,
              }
            : u,
        ),
      };
      await writeAuth(next);
      setUsers(next.users);
    },
    [sessionUserId],
  );

  return {
    ready,
    currentUser,
    unlocked,
    lock: () => setUnlocked(false),
    unlock: () => setUnlocked(true),
    signup,
    login,
    logout,
    updateProfile,
  };
}
