import { NextResponse } from "next/server";
import {
  buildProductInfoXml,
  parseProductInfoQuery,
} from "@/lib/naverpay/product-info-xml";

export const runtime = "nodejs";

/**
 * Naver Pay product-info XML callback.
 * Test: GET /api/naverpay/product-info?product[0][id]=prl-chino-cap
 */
export async function GET(req: Request) {
  const url = new URL(req.url);
  const queries = parseProductInfoQuery(url);
  const xml = buildProductInfoXml(queries);
  return new NextResponse(xml, {
    status: 200,
    headers: {
      "Content-Type": "application/xml; charset=utf-8",
      "Cache-Control": "no-store",
    },
  });
}
