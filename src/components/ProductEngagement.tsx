"use client";

import { useState } from "react";
import { ProductQA } from "@/components/ProductQA";
import { ProductReviews } from "@/components/ProductReviews";

type Tab = "reviews" | "qa";

export function ProductEngagement({
  productId,
  productName,
}: {
  productId: string;
  productName: string;
}) {
  const [tab, setTab] = useState<Tab>("reviews");

  return (
    <section className="product-engage" aria-label="고객 리뷰와 상품문의">
      <div className="product-engage__head">
        <p className="product-engage__eyebrow">Briq Community</p>
        <h2>고객 리뷰 &amp; 상품문의</h2>
        <p className="product-engage__lead">
          실제 구매 경험과 궁금한 점을 남겨 주세요. 비밀 문의도 가능합니다.
        </p>
      </div>

      <div className="product-engage__tabs" role="tablist" aria-label="리뷰와 상품문의">
        <button
          type="button"
          role="tab"
          aria-selected={tab === "reviews"}
          className={`product-engage__tab${tab === "reviews" ? " is-active" : ""}`}
          onClick={() => setTab("reviews")}
        >
          Reviews
          <span>리뷰</span>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === "qa"}
          className={`product-engage__tab${tab === "qa" ? " is-active" : ""}`}
          onClick={() => setTab("qa")}
        >
          Inquiry
          <span>상품문의</span>
        </button>
      </div>

      <div className="product-engage__body" role="tabpanel">
        {tab === "reviews" ? (
          <ProductReviews productId={productId} productName={productName} />
        ) : (
          <ProductQA productId={productId} productName={productName} />
        )}
      </div>
    </section>
  );
}
