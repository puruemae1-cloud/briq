import { createHmac, randomBytes, scryptSync, timingSafeEqual } from "crypto";
import { cookies } from "next/headers";
import { readOnlyDb } from "./db";
import type { Role, User } from "./types";

const COOKIE = "baedaeji_session";
const TTL_MS = 14 * 24 * 60 * 60 * 1000;

function secret() {
  return process.env.BAEDAEJI_SESSION_SECRET || "baedaeji-dev-secret-only";
}

export type SessionPayload = {
  userId: string;
  email: string;
  role: Role;
  exp: number;
};

export function hashPassword(password: string, salt = randomBytes(16).toString("hex")) {
  const hash = scryptSync(password, salt, 32).toString("hex");
  return { hash, salt };
}

export function verifyPassword(password: string, salt: string, hash: string) {
  const next = scryptSync(password, salt, 32);
  const prev = Buffer.from(hash, "hex");
  if (next.length !== prev.length) return false;
  return timingSafeEqual(next, prev);
}

function sign(payload: SessionPayload) {
  const body = Buffer.from(JSON.stringify(payload)).toString("base64url");
  const sig = createHmac("sha256", secret()).update(body).digest("base64url");
  return `${body}.${sig}`;
}

function unsign(token: string): SessionPayload | null {
  const [body, sig] = token.split(".");
  if (!body || !sig) return null;
  const expected = createHmac("sha256", secret()).update(body).digest("base64url");
  const a = Buffer.from(sig);
  const b = Buffer.from(expected);
  if (a.length !== b.length || !timingSafeEqual(a, b)) return null;
  try {
    const payload = JSON.parse(Buffer.from(body, "base64url").toString("utf8")) as SessionPayload;
    if (payload.exp < Date.now()) return null;
    return payload;
  } catch {
    return null;
  }
}

export async function setSession(user: Pick<User, "id" | "email" | "role">) {
  const token = sign({
    userId: user.id,
    email: user.email,
    role: user.role,
    exp: Date.now() + TTL_MS,
  });
  const jar = await cookies();
  jar.set(COOKIE, token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: TTL_MS / 1000,
  });
}

export async function clearSession() {
  const jar = await cookies();
  jar.delete(COOKIE);
}

export async function getSession(): Promise<SessionPayload | null> {
  const jar = await cookies();
  const token = jar.get(COOKIE)?.value;
  if (!token) return null;
  return unsign(token);
}

export async function getCurrentUser(): Promise<User | null> {
  const session = await getSession();
  if (!session) return null;
  const db = await readOnlyDb();
  return db.users.find((u) => u.id === session.userId) ?? null;
}

export function isAdminEmail(email: string) {
  const configured = process.env.BAEDAEJI_ADMIN_EMAIL?.trim().toLowerCase();
  return Boolean(configured && email === configured);
}

export function isAdminCode(code: string) {
  const expected = process.env.BAEDAEJI_ADMIN_CODE?.trim();
  return Boolean(expected && code && code === expected);
}

export function publicUser(user: User) {
  return {
    id: user.id,
    email: user.email,
    name: user.name,
    phone: user.phone,
    address: user.address,
    customsCode: user.customsCode,
    role: user.role,
  };
}
