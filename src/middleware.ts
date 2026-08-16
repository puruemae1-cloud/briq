import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/** Prefer apex https://briq.kr (Naver/Google canonical). */
export function middleware(request: NextRequest) {
  const host = request.headers.get("host") || "";
  if (host === "www.briq.kr") {
    const url = request.nextUrl.clone();
    url.host = "briq.kr";
    url.protocol = "https:";
    return NextResponse.redirect(url, 301);
  }
  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|icon-|apple-icon|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
