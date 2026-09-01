import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { JsonLd } from "@/components/JsonLd";
import { ProductDetail } from "@/components/ProductDetail";
import { formatKrw, getProduct, isProductInStock, productDisplayPrice } from "@/data/products";
import { mediaUrl } from "@/lib/product-image";
import { getSiteUrl } from "@/lib/site";

type Props = {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ color?: string; size?: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const product = getProduct(id);
  if (!product) return { title: "상품을 찾을 수 없습니다" };

  const name = product.nameKo || product.name;
  const brand = product.brand || "Briq";
  const title = `${brand} ${name} | 명품직구 Briq`;
  const listPrice = productDisplayPrice(product);
  const description = [
    `${brand} ${name}.`,
    product.compareAtPrice
      ? `판매가 ${formatKrw(listPrice)}.`
      : `가격 ${formatKrw(listPrice)}.`,
    "Briq 영국 명품직구·구매대행, 항공배송·관부가세 포함.",
  ].join(" ");
  const image = mediaUrl(product.image || product.images?.[0] || "");
  const url = `${getSiteUrl()}/product/${encodeURIComponent(product.id)}`;

  return {
    title,
    description,
    keywords: [
      brand,
      name,
      "명품직구",
      "명품구매대행",
      "명품의류",
      product.category,
    ].filter(Boolean) as string[],
    alternates: { canonical: url },
    openGraph: {
      title,
      description,
      url,
      type: "website",
      locale: "ko_KR",
      images: image
        ? [{ url: image, alt: `${brand} ${name}` }]
        : undefined,
    },
  };
}

export default async function ProductPage({ params, searchParams }: Props) {
  const { id } = await params;
  const { color, size } = await searchParams;
  const product = getProduct(id);
  if (!product) notFound();

  let colorId = color;
  let sizeId = size;
  if (!colorId || !sizeId) {
    const pathVariant = product.variants?.find(
      (v) => v.id === id || `cw-${v.id}` === id || v.sku === id,
    );
    if (pathVariant) {
      colorId = colorId || pathVariant.colorKey || pathVariant.id;
      sizeId = sizeId || pathVariant.size;
    }
  }

  const site = getSiteUrl();
  const name = product.nameKo || product.name;
  const image = mediaUrl(product.image || product.images?.[0] || "");
  const productLd = {
    "@context": "https://schema.org",
    "@type": "Product",
    name,
    brand: {
      "@type": "Brand",
      name: product.brand || "Briq",
    },
    description: `${product.brand || ""} ${name} — Briq 명품직구`.trim(),
    sku: product.sku || product.id,
    image: image ? [image] : undefined,
    offers: {
      "@type": "Offer",
      url: `${site}/product/${encodeURIComponent(product.id)}`,
      priceCurrency: "KRW",
      price: product.price,
      availability: isProductInStock(product)
        ? "https://schema.org/InStock"
        : "https://schema.org/OutOfStock",
      seller: {
        "@type": "Organization",
        name: "Briq",
      },
    },
  };

  return (
    <>
      <JsonLd data={productLd} />
      <ProductDetail product={product} colorId={colorId} sizeId={sizeId} />
    </>
  );
}
