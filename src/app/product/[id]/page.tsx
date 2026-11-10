import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { JsonLd } from "@/components/JsonLd";
import { ProductDetail } from "@/components/ProductDetail";
import { formatKrw, getProduct, isProductInStock, productDisplayPrice } from "@/data/products";
import { mediaUrl } from "@/lib/product-image";
import { getSiteUrl, productSeoHeadline, seoTitle } from "@/lib/site";

/** Catalogue HTML is deploy-stable; edge-cache for Naver Yeti download time. */
export const revalidate = 3600;

type Props = {
  params: Promise<{ id: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const product = getProduct(id);
  if (!product) return { title: "상품을 찾을 수 없습니다" };

  const name = product.nameKo || product.name;
  const brand = product.brand || "Briq";
  const headline = productSeoHeadline(brand, name);
  const title = seoTitle(headline);
  const listPrice = productDisplayPrice(product);
  const description = [
    `${headline}.`,
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
      title: title.absolute,
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

export default async function ProductPage({ params }: Props) {
  const { id } = await params;
  const product = getProduct(id);
  if (!product) notFound();

  // Path-variant deep links (id matches a variant sku) — resolve once for SSR.
  const pathVariant = product.variants?.find(
    (v) => v.id === id || `cw-${v.id}` === id || v.sku === id,
  );
  const colorId = pathVariant?.colorKey || pathVariant?.id;
  const sizeId = pathVariant?.size;

  const site = getSiteUrl();
  const name = product.nameKo || product.name;
  const image = mediaUrl(product.image || product.images?.[0] || "");
  // Do not await listQa()/Blob or searchParams here — both forced private,
  // uncacheable HTML and ~0.6–0.7s waits (Naver "다운로드 소요시간").
  // Colour/size query is read in ProductDetail via useSearchParams.
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
      <Suspense fallback={null}>
        <ProductDetail product={product} colorId={colorId} sizeId={sizeId} />
      </Suspense>
    </>
  );
}
