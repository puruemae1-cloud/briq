import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { JsonLd } from "@/components/JsonLd";
import { ProductDetail } from "@/components/ProductDetail";
import { formatKrw, getProduct, isProductInStock, productDisplayPrice } from "@/data/products";
import { listQa } from "@/lib/qa-inbox";
import { maskInquiryEmail } from "@/lib/qa-privacy";
import { mediaUrl } from "@/lib/product-image";
import { getSiteUrl, productSeoHeadline, seoTitle } from "@/lib/site";

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
  const headline = productSeoHeadline(brand, name);
  const titleText = `${headline} 명품직구`;
  const title = seoTitle(titleText);
  const listPrice = productDisplayPrice(product);
  const stockHint = isProductInStock(product) ? "재고 확인 후 바로 주문" : "입고 문의 가능";
  const description = [
    `${headline}.`,
    product.compareAtPrice
      ? `판매가 ${formatKrw(listPrice)}.`
      : `${formatKrw(listPrice)} (관부가세·항공배송 포함).`,
    `${stockHint}. 영국 정품 명품직구 Briq.`,
  ].join(" ");
  const image = mediaUrl(product.image || product.images?.[0] || "");
  const url = `${getSiteUrl()}/product/${encodeURIComponent(product.id)}`;
  const ogTitle = title.absolute;

  return {
    title,
    description,
    keywords: [
      brand,
      name,
      "명품직구",
      "명품구매대행",
      "명품시계",
      "명품의류",
      product.category,
    ].filter(Boolean) as string[],
    alternates: { canonical: url },
    openGraph: {
      title: ogTitle,
      description,
      url,
      type: "website",
      locale: "ko_KR",
      images: image
        ? [{ url: image, alt: headline }]
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
  const initialInquiries = (await listQa())
    .filter((item) => item.productId === product.id && item.visibility !== "private")
    .map((item) => ({
      id: item.id,
      productId: item.productId,
      productName: item.productName,
      authorName: item.authorName,
      authorEmail: item.authorEmail ? maskInquiryEmail(item.authorEmail) : undefined,
      question: item.question,
      visibility: "public" as const,
      createdAt: item.createdAt,
      answer: item.answer,
      answeredAt: item.answeredAt,
      answeredBy: item.answeredBy,
    }));
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
      <ProductDetail
        product={product}
        colorId={colorId}
        sizeId={sizeId}
        initialInquiries={initialInquiries}
      />
    </>
  );
}
