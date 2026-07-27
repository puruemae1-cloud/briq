import { notFound } from "next/navigation";
import { ProductDetail } from "@/components/ProductDetail";
import { getProduct } from "@/data/products";

type Props = {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ color?: string }>;
};

export default async function ProductPage({ params, searchParams }: Props) {
  const { id } = await params;
  const { color } = await searchParams;
  const product = getProduct(id);
  if (!product) notFound();

  return <ProductDetail product={product} colorId={color} />;
}
