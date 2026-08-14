import { createHash } from "crypto";
import type { Product, ProductVariant } from "@/data/product-types";
import { getProduct, products } from "@/data/products";
import { cartUnitPrice } from "@/lib/cart-price";
import {
  getNaverPaySiteOrigin,
  NAVERPAY_SHIPPING_DEFAULTS,
  NAVERPAY_TAX_TYPE,
} from "@/lib/naverpay/config";
import { resolveProductImage, mediaUrl } from "@/lib/product-image";

const NAVER_ID_RE = /^[A-Za-z0-9!+\-/=_|]+$/;

/** Npay product/id: max 30 chars, limited charset. */
export function toNaverProductId(briqId: string): string {
  if (briqId.length <= 30 && NAVER_ID_RE.test(briqId)) return briqId;
  const hash = createHash("sha1").update(briqId).digest("hex").slice(0, 7);
  const base = briqId.replace(/[^A-Za-z0-9!+\-/=_|]/g, "_").slice(0, 22);
  return `${base}_${hash}`.slice(0, 30);
}

/** Npay option manageCode: max 100 chars. */
export function toNaverManageCode(raw: string): string {
  const cleaned = raw.replace(/[^A-Za-z0-9!+\-/=_|]/g, "_");
  return cleaned.slice(0, 100) || "default";
}

let naverIdIndex: Map<string, string> | null = null;

function buildNaverIdIndex() {
  const map = new Map<string, string>();
  for (const p of products) {
    map.set(toNaverProductId(p.id), p.id);
  }
  return map;
}

export function resolveBriqProductId(naverOrBriqId: string): string | undefined {
  const direct = getProduct(naverOrBriqId);
  if (direct) return direct.id;
  if (!naverIdIndex) naverIdIndex = buildNaverIdIndex();
  return naverIdIndex.get(naverOrBriqId);
}

export function escapeXml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

export function cdata(value: string): string {
  return `<![CDATA[${value.replace(/]]>/g, "]]]]><![CDATA[>")}]]>`;
}

export function absoluteUrl(pathOrUrl: string): string {
  if (/^https?:\/\//i.test(pathOrUrl)) return pathOrUrl;
  // Prefer external media CDN so product photos don't depend on Vercel bytes.
  const viaCdn = mediaUrl(pathOrUrl);
  if (/^https?:\/\//i.test(viaCdn)) return viaCdn;
  const origin = getNaverPaySiteOrigin();
  return `${origin}${pathOrUrl.startsWith("/") ? "" : "/"}${pathOrUrl}`;
}

export type NaverPayOrderLineInput = {
  productId: string;
  variantId?: string;
  braceletCm?: string;
  qty: number;
};

export type ResolvedNaverPayLine = {
  product: Product;
  variant?: ProductVariant;
  braceletCm?: string;
  qty: number;
  unitPrice: number;
  naverProductId: string;
  manageCode?: string;
  optionLabel?: string;
  infoUrl: string;
  imageUrl: string;
};

/**
 * manageCode must match product-info `<combination><manageCode>`.
 * Briq uses the variant id only. Bracelet resize is folded into basePrice + name
 * (not a separate Npay option dimension) so codes stay in sync with combinations.
 */
export function variantManageCode(variantId: string): string {
  return toNaverManageCode(variantId);
}

export function resolveOrderLines(
  inputs: NaverPayOrderLineInput[],
): ResolvedNaverPayLine[] {
  const out: ResolvedNaverPayLine[] = [];
  for (const row of inputs) {
    const product = getProduct(row.productId);
    if (!product) continue;
    const qty = Math.max(1, Math.min(999, Math.floor(row.qty) || 1));
    const hasVariants = Boolean(product.variants && product.variants.length > 0);
    // Variant SKUs must send the selected variant — required for 검수 option XML.
    if (hasVariants && !row.variantId) continue;
    const variant = row.variantId
      ? product.variants?.find((v) => v.id === row.variantId)
      : undefined;
    if (row.variantId && !variant) continue;
    const unitPrice = cartUnitPrice(product, variant, row.braceletCm);
    if (unitPrice < 1) continue;
    const image = resolveProductImage(product.image, variant?.image);
    const infoPath = variant
      ? `/product/${product.id}?color=${encodeURIComponent(variant.colorKey || variant.id)}${
          variant.size ? `&size=${encodeURIComponent(variant.size)}` : ""
        }`
      : `/product/${product.id}`;
    const manageCode = variant ? variantManageCode(variant.id) : undefined;
    const braceletLabel =
      row.braceletCm && row.braceletCm !== "no" ? `${row.braceletCm}cm` : undefined;
    const optionLabel = [
      variant
        ? [variant.colorNameKo || variant.nameKo, variant.size].filter(Boolean).join(" · ")
        : undefined,
      braceletLabel,
    ]
      .filter(Boolean)
      .join(" · ");
    out.push({
      product,
      variant,
      braceletCm: row.braceletCm,
      qty,
      unitPrice,
      naverProductId: toNaverProductId(product.id),
      manageCode,
      optionLabel: optionLabel || undefined,
      infoUrl: absoluteUrl(infoPath),
      imageUrl: absoluteUrl(image),
    });
  }
  return out;
}

function shippingPolicyXml(): string {
  const s = NAVERPAY_SHIPPING_DEFAULTS;
  return [
    "<shippingPolicy>",
    `<groupId>${escapeXml(s.groupId)}</groupId>`,
    `<method>${s.method}</method>`,
    `<feePayType>${s.feePayType}</feePayType>`,
    `<feeType>${s.feeType}</feeType>`,
    `<feePrice>${s.feePrice}</feePrice>`,
    "</shippingPolicy>",
  ].join("");
}

function optionXml(line: ResolvedNaverPayLine): string {
  if (!line.manageCode || !line.variant) {
    return `<single><quantity>${line.qty}</quantity></single>`;
  }
  const selected: string[] = [];
  const v = line.variant;
  // Mirror product-info optionItem names/ids (컬러+사이즈 or 옵션).
  if (v.size) {
    const isCw = line.product.brand === "Christopher Ward";
    const colorAxisName = isCw ? "스트랩" : "컬러";
    const sizeAxisName = isCw ? "케이스 사이즈" : "사이즈";
    const colorId = toNaverManageCode(v.colorKey || v.id);
    const colorText = v.colorNameKo || v.nameKo || colorId;
    selected.push(
      `<selectedItem><type>SELECT</type><name>${cdata(colorAxisName)}</name><value><id>${escapeXml(colorId)}</id><text>${cdata(colorText)}</text></value></selectedItem>`,
    );
    selected.push(
      `<selectedItem><type>SELECT</type><name>${cdata(sizeAxisName)}</name><value><id>${escapeXml(toNaverManageCode(v.size))}</id><text>${cdata(v.size)}</text></value></selectedItem>`,
    );
  } else {
    const isCw = line.product.brand === "Christopher Ward";
    selected.push(
      `<selectedItem><type>SELECT</type><name>${cdata(isCw ? "스트랩" : "옵션")}</name><value><id>${escapeXml(toNaverManageCode(v.id))}</id><text>${cdata(v.nameKo || v.name || v.id)}</text></value></selectedItem>`,
    );
  }
  // Bracelet resize fee is already in basePrice; do not emit a separate option
  // (product-info combinations key off variant id only — see variantManageCode).
  return [
    "<option>",
    `<manageCode>${cdata(line.manageCode)}</manageCode>`,
    "<price>0</price>",
    `<quantity>${line.qty}</quantity>`,
    ...selected,
    "</option>",
  ].join("");
}

export type OrderInterfaceCodes = {
  cpaInflowCode?: string;
  naverInflowCode?: string;
  saClickId?: string;
};

export function buildOrderRegisterXml(opts: {
  merchantId: string;
  certiKey: string;
  backUrl: string;
  lines: ResolvedNaverPayLine[];
  interfaceCodes?: OrderInterfaceCodes;
}): string {
  const productsXml = opts.lines
    .map((line) => {
      const name = line.optionLabel
        ? `${line.product.brand} ${line.product.nameKo} (${line.optionLabel})`
        : `${line.product.brand} ${line.product.nameKo}`;
      return [
        "<product>",
        `<id>${escapeXml(line.naverProductId)}</id>`,
        `<merchantProductId>${escapeXml(line.product.id.slice(0, 100))}</merchantProductId>`,
        `<name>${cdata(name.slice(0, 100))}</name>`,
        `<basePrice>${line.unitPrice}</basePrice>`,
        `<taxType>${NAVERPAY_TAX_TYPE}</taxType>`,
        `<infoUrl>${cdata(line.infoUrl)}</infoUrl>`,
        `<imageUrl>${cdata(line.imageUrl)}</imageUrl>`,
        optionXml(line),
        shippingPolicyXml(),
        "</product>",
      ].join("");
    })
    .join("");

  const iface = opts.interfaceCodes;
  const interfaceXml =
    iface && (iface.cpaInflowCode || iface.naverInflowCode || iface.saClickId)
      ? [
          "<interface>",
          iface.cpaInflowCode
            ? `<cpaInflowCode>${escapeXml(iface.cpaInflowCode)}</cpaInflowCode>`
            : "",
          iface.naverInflowCode
            ? `<naverInflowCode>${escapeXml(iface.naverInflowCode)}</naverInflowCode>`
            : "",
          iface.saClickId
            ? `<saClickId>${escapeXml(iface.saClickId)}</saClickId>`
            : "",
          "</interface>",
        ].join("")
      : "";

  return [
    '<?xml version="1.0" encoding="utf-8"?>',
    "<order>",
    `<merchantId>${escapeXml(opts.merchantId)}</merchantId>`,
    `<certiKey>${escapeXml(opts.certiKey)}</certiKey>`,
    `<backUrl>${cdata(opts.backUrl)}</backUrl>`,
    interfaceXml,
    productsXml,
    "</order>",
  ].join("");
}

/** Parse `SUCCESS:BUY_KEY:MERCHANT_NO` or `FAIL:[code]message`. */
export function parseOrderRegisterResponse(raw: string):
  | { ok: true; key: string; merchantNo: string }
  | { ok: false; message: string } {
  const text = raw.trim();
  const parts = text.split(":");
  if (parts[0] === "SUCCESS" && parts[1] && parts[2]) {
    return { ok: true, key: parts[1], merchantNo: parts[2] };
  }
  if (parts[0] === "FAIL") {
    return { ok: false, message: text.slice(5) || "주문 등록 실패" };
  }
  return { ok: false, message: text || "주문 등록 응답을 해석할 수 없습니다." };
}
