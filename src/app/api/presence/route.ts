import { NextResponse } from "next/server";
import { heartbeatPresence, readPresenceCount } from "@/lib/presence-store";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  const productId = new URL(req.url).searchParams.get("productId") || "";
  const result = await readPresenceCount(productId);
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 400 });
  }
  return NextResponse.json(
    { count: result.count, display: result.display },
    { headers: { "Cache-Control": "no-store" } },
  );
}

export async function POST(req: Request) {
  let body: { productId?: string; visitorId?: string } = {};
  try {
    body = (await req.json()) as { productId?: string; visitorId?: string };
  } catch {
    return NextResponse.json({ error: "invalid json" }, { status: 400 });
  }
  const result = await heartbeatPresence(
    String(body.productId || ""),
    String(body.visitorId || ""),
  );
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 400 });
  }
  return NextResponse.json(
    { count: result.count, display: result.display },
    { headers: { "Cache-Control": "no-store" } },
  );
}
