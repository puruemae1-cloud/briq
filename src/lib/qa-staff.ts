import { timingSafeEqual } from "crypto";
import { hashPassword } from "@/lib/password-hash";

export function isStaffRequest(req: Request) {
  const sent = req.headers.get("x-briq-staff")?.trim() ?? "";
  const password = process.env.NEXT_PUBLIC_ADMIN_PASSWORD?.trim() ?? "";
  if (!sent || !password) return false;
  const expected = hashPassword(password);
  const a = Buffer.from(sent);
  const b = Buffer.from(expected);
  if (a.length !== b.length) return false;
  return timingSafeEqual(a, b);
}
