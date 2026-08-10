import {
  getProduct,
  isVariantInStock,
  type Product,
  type ProductVariant,
} from "@/data/products";
import {
  getNaverPayReturnInfo,
  NAVERPAY_SHIPPING_DEFAULTS,
  NAVERPAY_TAX_TYPE,
} from "@/lib/naverpay/config";
import {
  absoluteUrl,
  cdata,
  escapeXml,
  resolveBriqProductId,
  toNaverManageCode,
  toNaverProductId,
  variantManageCode,
} from "@/lib/naverpay/order-xml";
import { resolveProductImage } from "@/lib/product-image";

export type ProductInfoQuery = {
  id: string;
  optionManageCodes?: string[];
};

/**
 * Parse Naver's `product[0][id]=...&product[0][optionManageCodes]=...` query style.
 * Also accepts simple `id=` / `productId=` for manual testing.
 */
export function parseProductInfoQuery(url: URL): ProductInfoQuery[] {
  const out: ProductInfoQuery[] = [];
  const indexed = new Map<number, ProductInfoQuery>();

  for (const [key, value] of url.searchParams.entries()) {
    const m = key.match(/^product\[(\d+)]\[(id|optionManageCodes|optionManageCode)]$/i);
    if (m) {
      const idx = Number(m[1]);
      const field = m[2].toLowerCase();
      const row = indexed.get(idx) ?? { id: "", optionManageCodes: [] };
      if (field === "id") {
        row.id = value;
      } else {
        // Support comma-separated codes in a single param.
        const parts = value.split(",").map((s) => s.trim()).filter(Boolean);
        row.optionManageCodes = [...(row.optionManageCodes ?? []), ...parts];
      }
      indexed.set(idx, row);
      continue;
    }
  }

  const sorted = [...indexed.entries()]
    .sort((a, b) => a[0] - b[0])
    .map(([, row]) => row)
    .filter((row) => row.id);

  if (sorted.length > 0) return sorted;

  const single =
    url.searchParams.get("id") ||
    url.searchParams.get("productId") ||
    url.searchParams.get("ITEM_ID");
  if (single) {
    const codes = url.searchParams.getAll("optionManageCodes").flatMap((v) =>
      v.split(",").map((s) => s.trim()).filter(Boolean),
    );
    return [{ id: single, optionManageCodes: codes.length ? codes : undefined }];
  }
  return out;
}

function shippingPolicyXml(): string {
  const s = NAVERPAY_SHIPPING_DEFAULTS;
  return [
    "<shippingPolicy>",
    `<groupId>${escapeXml(s.groupId)}</groupId>`,
    `<method>${s.method}</method>`,
    `<feeType>${s.feeType}</feeType>`,
    `<feePayType>${s.feePayType}</feePayType>`,
    `<feePrice>${s.feePrice}</feePrice>`,
    "</shippingPolicy>",
  ].join("");
}

function returnInfoXml(): string {
  const r = getNaverPayReturnInfo();
  return [
    "<returnInfo>",
    `<zipcode>${escapeXml(r.zipcode)}</zipcode>`,
    `<address1>${cdata(r.address1)}</address1>`,
    `<address2>${cdata(r.address2)}</address2>`,
    `<sellername>${cdata(r.sellername)}</sellername>`,
    `<contact1>${escapeXml(r.contact1)}</contact1>`,
    "</returnInfo>",
  ].join("");
}

/**
 * Option axes: size variants → 컬러 + 사이즈; otherwise single 옵션 per variant id.
 * Combination manageCode = variant id (must match order XML).
 */
function optionBlockXml(
  product: Product,
  optionManageCodes?: string[],
): string {
  const variants = product.variants ?? [];
  if (variants.length === 0) return "";

  const codeFilter = optionManageCodes?.length
    ? new Set(optionManageCodes.map((c) => toNaverManageCode(c)))
    : null;
  const filtered = codeFilter
    ? variants.filter((v) => codeFilter.has(variantManageCode(v.id)))
    : variants;
  // If Naver asked for codes we don't have, still return full catalogue (safer for 검수).
  const list = filtered.length > 0 ? filtered : variants;

  const hasSizes = list.some((v) => Boolean(v.size));
  const colorMap = new Map<string, { id: string; text: string; status: boolean }>();
  const sizeMap = new Map<string, { id: string; text: string; status: boolean }>();

  for (const v of list) {
    if (hasSizes) {
      const colorId = toNaverManageCode(v.colorKey || v.id);
      const colorText = v.colorNameKo || v.nameKo || colorId;
      const prev = colorMap.get(colorId);
      colorMap.set(colorId, {
        id: colorId,
        text: colorText,
        status: Boolean(prev?.status || v.inStock),
      });
      if (v.size) {
        const sizeId = toNaverManageCode(v.size);
        const prevSize = sizeMap.get(sizeId);
        sizeMap.set(sizeId, {
          id: sizeId,
          text: v.size,
          status: Boolean(prevSize?.status || v.inStock),
        });
      }
    } else {
      const id = toNaverManageCode(v.id);
      colorMap.set(id, {
        id,
        text: v.nameKo || v.name,
        status: v.inStock,
      });
    }
  }

  const optionItems: string[] = [];
  if (hasSizes) {
    optionItems.push(
      [
        "<optionItem>",
        "<type>SELECT</type>",
        `<name>${cdata("컬러")}</name>`,
        ...[...colorMap.values()].map(
          (c) =>
            `<value><id>${escapeXml(c.id)}</id><text>${cdata(c.text)}</text><status>${c.status}</status></value>`,
        ),
        "</optionItem>",
      ].join(""),
    );
    if (sizeMap.size > 0) {
      optionItems.push(
        [
          "<optionItem>",
          "<type>SELECT</type>",
          `<name>${cdata("사이즈")}</name>`,
          ...[...sizeMap.values()].map(
            (s) =>
              `<value><id>${escapeXml(s.id)}</id><text>${cdata(s.text)}</text><status>${s.status}</status></value>`,
          ),
          "</optionItem>",
        ].join(""),
      );
    }
  } else {
    optionItems.push(
      [
        "<optionItem>",
        "<type>SELECT</type>",
        `<name>${cdata("옵션")}</name>`,
        ...[...colorMap.values()].map(
          (c) =>
            `<value><id>${escapeXml(c.id)}</id><text>${cdata(c.text)}</text><status>${c.status}</status></value>`,
        ),
        "</optionItem>",
      ].join(""),
    );
  }

  const combinations = list.map((v) => combinationXml(product, v)).join("");

  return [
    "<optionSupport>true</optionSupport>",
    "<option>",
    ...optionItems,
    combinations,
    "</option>",
  ].join("");
}

function combinationXml(product: Product, variant: ProductVariant): string {
  const manageCode = variantManageCode(variant.id);
  const inStock = isVariantInStock(product, variant.id);
  // Relative to product.basePrice; order XML uses full unit as basePrice + option price 0.
  const optionPrice = Math.max(0, variant.price - product.price);
  const options: string[] = [];
  // Keep axes identical to order-xml optionXml / optionItem names above.
  if (variant.size) {
    options.push(
      `<options><name>${cdata("컬러")}</name><id>${escapeXml(toNaverManageCode(variant.colorKey || variant.id))}</id></options>`,
    );
    options.push(
      `<options><name>${cdata("사이즈")}</name><id>${escapeXml(toNaverManageCode(variant.size))}</id></options>`,
    );
  } else {
    options.push(
      `<options><name>${cdata("옵션")}</name><id>${escapeXml(toNaverManageCode(variant.id))}</id></options>`,
    );
  }
  return [
    "<combination>",
    `<manageCode>${escapeXml(manageCode)}</manageCode>`,
    optionPrice ? `<price>${optionPrice}</price>` : "<price>0</price>",
    `<status>${inStock}</status>`,
    ...options,
    "</combination>",
  ].join("");
}

function productXml(query: ProductInfoQuery): string | null {
  const briqId = resolveBriqProductId(query.id);
  if (!briqId) return null;
  const product = getProduct(briqId);
  if (!product) return null;

  const image = resolveProductImage(product.image, product.variants?.[0]?.image);
  const hasVariants = Boolean(product.variants && product.variants.length > 0);
  const anyInStock = hasVariants
    ? product.variants!.some((v) => v.inStock)
    : product.inStock !== false;
  const status = anyInStock ? "ON_SALE" : "SOLD_OUT";
  // Soft stock for private-order UK→KR; real availability is variant.inStock flags.
  const stockQuantity = anyInStock ? 99 : 0;
  const name = `${product.brand} ${product.nameKo}`.slice(0, 100);

  return [
    "<product>",
    `<id>${escapeXml(toNaverProductId(product.id))}</id>`,
    `<merchantProductId>${escapeXml(product.id.slice(0, 100))}</merchantProductId>`,
    `<name>${cdata(name)}</name>`,
    `<basePrice>${product.price}</basePrice>`,
    `<taxType>${NAVERPAY_TAX_TYPE}</taxType>`,
    `<infoUrl>${cdata(absoluteUrl(`/product/${product.id}`))}</infoUrl>`,
    `<imageUrl>${cdata(absoluteUrl(image))}</imageUrl>`,
    `<status>${status}</status>`,
    `<stockQuantity>${stockQuantity}</stockQuantity>`,
    "<supplementSupport>false</supplementSupport>",
    hasVariants
      ? optionBlockXml(product, query.optionManageCodes)
      : "<optionSupport>false</optionSupport>",
    returnInfoXml(),
    shippingPolicyXml(),
    "</product>",
  ].join("");
}

export function buildProductInfoXml(queries: ProductInfoQuery[]): string {
  const body =
    queries.length === 0
      ? ""
      : queries.map((q) => productXml(q)).filter(Boolean).join("");
  return `<?xml version="1.0" encoding="UTF-8"?><products>${body}</products>`;
}
