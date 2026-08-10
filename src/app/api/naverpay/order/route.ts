import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import {
  getNaverPayCertiKey,
  getNaverPayMerchantId,
  getNaverPaySiteOrigin,
  getNaverPayUrls,
  isNaverPayServerReady,
} from "@/lib/naverpay/config";
import {
  buildOrderRegisterXml,
  parseOrderRegisterResponse,
  resolveOrderLines,
  type NaverPayOrderLineInput,
} from "@/lib/naverpay/order-xml";

export const runtime = "nodejs";

type Body = {
  items?: NaverPayOrderLineInput[];
  backUrl?: string;
};

function cookieValue(jar: Awaited<ReturnType<typeof cookies>>, name: string) {
  return jar.get(name)?.value?.trim() || undefined;
}

export async function POST(req: Request) {
  if (!isNaverPayServerReady()) {
    return NextResponse.json(
      {
        ok: false,
        message:
          "네이버페이 주문형 환경변수가 없습니다. NAVERPAY_MERCHANT_ID / NAVERPAY_CERTI_KEY / NEXT_PUBLIC_NAVERPAY_BUTTON_KEY 를 설정하세요.",
      },
      { status: 503 },
    );
  }

  let body: Body;
  try {
    body = (await req.json()) as Body;
  } catch {
    return NextResponse.json({ ok: false, message: "잘못된 요청입니다." }, { status: 400 });
  }

  const items = Array.isArray(body.items) ? body.items : [];
  const lines = resolveOrderLines(items);
  if (lines.length === 0) {
    return NextResponse.json(
      { ok: false, message: "주문할 상품이 없습니다." },
      { status: 400 },
    );
  }

  const origin = getNaverPaySiteOrigin();
  const backUrl =
    body.backUrl && /^https?:\/\//i.test(body.backUrl)
      ? body.backUrl
      : `${origin}/cart`;

  const jar = await cookies();
  const xml = buildOrderRegisterXml({
    merchantId: getNaverPayMerchantId(),
    certiKey: getNaverPayCertiKey(),
    backUrl,
    lines,
    interfaceCodes: {
      cpaInflowCode: cookieValue(jar, "CPAValidator"),
      naverInflowCode: cookieValue(jar, "NA_CO"),
      saClickId: cookieValue(jar, "NVADID"),
    },
  });

  const { orderRegister } = getNaverPayUrls();
  let raw = "";
  try {
    const res = await fetch(orderRegister, {
      method: "POST",
      headers: { "Content-Type": "application/xml; charset=utf-8" },
      body: xml,
      cache: "no-store",
    });
    raw = await res.text();
  } catch (err) {
    const message = err instanceof Error ? err.message : "네이버페이 주문 등록 네트워크 오류";
    return NextResponse.json({ ok: false, message }, { status: 502 });
  }

  const parsed = parseOrderRegisterResponse(raw);
  if (!parsed.ok) {
    return NextResponse.json(
      { ok: false, message: parsed.message, raw },
      { status: 502 },
    );
  }

  // V2.1 SDK expects { key, merchantNo }
  return NextResponse.json({
    ok: true,
    key: parsed.key,
    merchantNo: parsed.merchantNo,
  });
}
