import { notFound } from "next/navigation";
import { ProductDetail } from "@/components/ProductDetail";
import { getProduct } from "@/data/products";

type Props = {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ color?: string; size?: string }>;
};

export default async function ProductPage({ params, searchParams }: Props) {
  const { id } = await params;
  const { color, size } = await searchParams;
  const product = getProduct(id);
  if (!product) notFound();

  // Old CW URLs were per case-size SKU (`/product/cw-c63-36ada4-…`). After
  // merging sizes onto one PDP, use the path id as a variant hint when there
  // is no explicit ?color= / ?size=.
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

  return <ProductDetail product={product} colorId={colorId} sizeId={sizeId} />;
}
