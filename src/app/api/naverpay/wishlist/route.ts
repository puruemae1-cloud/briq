import { NextResponse } from "next/server";
import {
  getNaverPayCertiKey,
  getNaverPayMerchantId,
  getNaverPayUrls,
  isNaverPayServerReady,
} from "@/lib/naverpay/config";
import {
  absoluteUrl,
  resolveOrderLines,
  toNaverProductId,
  type NaverPayOrderLineInput,
} from "@/lib/naverpay/order-xml";
import { resolveProductImage } from "@/lib/product-image";

export const runtime = "nodejs";

type Body = {
  productId?: string;
  variantId?: string;
  braceletCm?: string;
};

/**
 * Wishlist register (V2.1): POST form to wishlist.nhn → plain-text payProductId.
 * Client onWishlistClick returns { merchantId, payProductId }.
 */
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

  if (!body.productId) {
    return NextResponse.json(
      { ok: false, message: "상품 ID가 필요합니다." },
      { status: 400 },
    );
  }

  const lineInput: NaverPayOrderLineInput = {
    productId: body.productId,
    variantId: body.variantId,
    braceletCm: body.braceletCm,
    qty: 1,
  };
  const lines = resolveOrderLines([lineInput]);
  if (lines.length === 0) {
    return NextResponse.json(
      { ok: false, message: "찜할 상품을 찾을 수 없습니다." },
      { status: 400 },
    );
  }

  const line = lines[0]!;
  const merchantId = getNaverPayMerchantId();
  const certiKey = getNaverPayCertiKey();
  const name = (
    line.optionLabel
      ? `${line.product.brand} ${line.product.nameKo} (${line.optionLabel})`
      : `${line.product.brand} ${line.product.nameKo}`
  ).slice(0, 100);
  const imageUrl = absoluteUrl(
    resolveProductImage(line.product.image, line.variant?.image),
  );
  // Keep PDP URL stable (no option query) so wishlist deep-links stay consistent.
  const itemUrl = absoluteUrl(`/product/${line.product.id}`);
  const itemId = toNaverProductId(line.product.id);

  const params = new URLSearchParams();
  params.set("SHOP_ID", merchantId);
  params.set("CERTI_KEY", certiKey);
  params.set("RESERVE1", "");
  params.set("RESERVE2", "");
  params.set("RESERVE3", "");
  params.set("RESERVE4", "");
  params.set("RESERVE5", "");
  params.set("ITEM_ID", itemId);
  params.set("ITEM_NAME", name);
  params.set("ITEM_UPRICE", String(line.unitPrice));
  params.set("ITEM_IMAGE", imageUrl);
  params.set("ITEM_URL", itemUrl);

  const { wishlistRegister } = getNaverPayUrls();
  let raw = "";
  try {
    const res = await fetch(wishlistRegister, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        Accept: "*/*",
      },
      body: params.toString(),
      cache: "no-store",
    });
    raw = (await res.text()).trim();
    if (!res.ok) {
      return NextResponse.json(
        {
          ok: false,
          message: raw || `찜 등록 실패 (HTTP ${res.status})`,
        },
        { status: 502 },
      );
    }
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "네이버페이 찜 등록 네트워크 오류";
    return NextResponse.json({ ok: false, message }, { status: 502 });
  }

  // Success body is the payProductId (alphanumeric, max 19). Failures often start with FAIL / HTML.
  const payProductId = raw.split(/\s/)[0] || "";
  if (!payProductId || /fail|error|html|<!/i.test(payProductId) || payProductId.length > 32) {
    return NextResponse.json(
      { ok: false, message: raw || "찜 등록 응답을 해석할 수 없습니다." },
      { status: 502 },
    );
  }

  return NextResponse.json({
    ok: true,
    merchantId,
    payProductId,
  });
}
