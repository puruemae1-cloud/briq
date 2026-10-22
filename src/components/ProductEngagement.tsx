"use client";

import { ProductQA } from "@/components/ProductQA";
import type { QaItem } from "@/lib/qa-store";

export function ProductEngagement({
  productId,
  productName,
  initialItems = [],
}: {
  productId: string;
  productName: string;
  initialItems?: QaItem[];
}) {
  return (
    <section className="product-engage" aria-label="상품문의">
      <div className="product-engage__head">
        <p className="product-engage__eyebrow">Inquiry</p>
        <h2>상품문의</h2>
        <p className="product-engage__lead">
          로그인 없이 궁금한 점을 남겨 주세요. 공개 문의는 누구나 볼 수 있고, 비밀 문의를 체크하면 Briq 담당자만 확인 후 안내드립니다.
        </p>
      </div>
      <ProductQA
        productId={productId}
        productName={productName}
        initialItems={initialItems}
      />
    </section>
  );
}
