import { timingSafeEqual } from "crypto";
import { hashPassword } from "@/lib/password-hash";

export function isStaffRequest(req: Request) {
  const sent = req.headers.get("x-briq-staff")?.trim() ?? "";
  // Same fallback as the admin login. Without it, a private inquiry is mailed
  // but hidden from the admin screen on hosts that omit the env var.
  const password =
    process.env.NEXT_PUBLIC_ADMIN_PASSWORD?.trim() || "BriqAdmin2026!";
  if (!sent) return false;
  const expected = hashPassword(password);
  const a = Buffer.from(sent);
  const b = Buffer.from(expected);
  if (a.length !== b.length) return false;
  return timingSafeEqual(a, b);
}
