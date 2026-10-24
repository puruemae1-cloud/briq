import { NextResponse } from "next/server";
import { postDueSoldOutReplies } from "@/lib/qa-auto-reply";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 60;

function cronAuthorized(req: Request): boolean {
  const secret = process.env.CRON_SECRET?.trim();
  if (!secret) return false;
  return req.headers.get("authorization") === `Bearer ${secret}`;
}

export async function GET(req: Request) {
  if (!cronAuthorized(req)) {
    return NextResponse.json({ ok: false }, { status: 401 });
  }
  const result = await postDueSoldOutReplies();
  return NextResponse.json({ ok: true, posted: result.posted });
}
