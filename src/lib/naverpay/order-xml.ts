import { createHash } from "crypto";
import { getProduct, products, type Product, type ProductVariant } from "@/data/products";
import { cartUnitPrice } from "@/lib/cart-price";
import {
  getNaverPaySiteOrigin,
  NAVERPAY_SHIPPING_DEFAULTS,
  NAVERPAY_TAX_TYPE,
} from "@/lib/naverpay/config";
import { resolveProductImage } from "@/lib/product-image";

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

export function resolveOrderLines(
  inputs: NaverPayOrderLineInput[],
): ResolvedNaverPayLine[] {
  const out: ResolvedNaverPayLine[] = [];
  for (const row of inputs) {
    const product = getProduct(row.productId);
    if (!product) continue;
    const qty = Math.max(1, Math.min(999, Math.floor(row.qty) || 1));
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
    const hasOption = Boolean(variant || (row.braceletCm && row.braceletCm !== "no"));
    // manageCode must match product-info <combination><manageCode> (variant id).
    const manageCode = hasOption
      ? toNaverManageCode(
          variant
            ? row.braceletCm && row.braceletCm !== "no"
              ? `${variant.id}_${row.braceletCm}`
              : variant.id
            : row.braceletCm || "default",
        )
      : undefined;
    const optionLabel = variant
      ? [variant.colorNameKo || variant.nameKo, variant.size].filter(Boolean).join(" · ")
      : undefined;
    out.push({
      product,
      variant,
      braceletCm: row.braceletCm,
      qty,
      unitPrice,
      naverProductId: toNaverProductId(product.id),
      manageCode,
      optionLabel,
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
  if (!line.manageCode) {
    return `<single><quantity>${line.qty}</quantity></single>`;
  }
  const selected: string[] = [];
  if (line.variant) {
    if (line.variant.colorNameKo || line.variant.colorKey) {
      const id = toNaverManageCode(line.variant.colorKey || line.variant.id);
      const text = line.variant.colorNameKo || line.variant.nameKo || id;
      selected.push(
        `<selectedItem><type>SELECT</type><name>${cdata("컬러")}</name><value><id>${escapeXml(id)}</id><text>${cdata(text)}</text></value></selectedItem>`,
      );
    }
    if (line.variant.size) {
      const id = toNaverManageCode(line.variant.size);
      selected.push(
        `<selectedItem><type>SELECT</type><name>${cdata("사이즈")}</name><value><id>${escapeXml(id)}</id><text>${cdata(line.variant.size)}</text></value></selectedItem>`,
      );
    }
    if (selected.length === 0) {
      selected.push(
        `<selectedItem><type>SELECT</type><name>${cdata("옵션")}</name><value><id>${escapeXml(toNaverManageCode(line.variant.id))}</id><text>${cdata(line.variant.nameKo || line.variant.id)}</text></value></selectedItem>`,
      );
    }
  }
  if (line.braceletCm && line.braceletCm !== "no") {
    selected.push(
      `<selectedItem><type>SELECT</type><name>${cdata("브레이슬릿")}</name><value><id>${escapeXml(toNaverManageCode(line.braceletCm))}</id><text>${cdata(`${line.braceletCm}cm`)}</text></value></selectedItem>`,
    );
  }
  // Option add-on price is folded into basePrice for Briq (unit already includes bracelet fee).
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
