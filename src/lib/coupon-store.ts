"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

export const REVIEW_COUPON_TEXT = 3000;
export const REVIEW_COUPON_MEDIA = 5000;

export type CouponKind = "review-text" | "review-media";
export type CouponStatus = "available" | "used";

export type ReviewCoupon = {
  id: string;
  kind: CouponKind;
  amountKrw: number;
  label: string;
  reviewId: string;
  productId: string;
  productName: string;
  /** Logged-in member id when available */
  userId?: string;
  /** Always stored lowercased for guest matching at checkout */
  ownerEmail: string;
  status: CouponStatus;
  createdAt: string;
  usedAt?: string;
  usedOrderId?: string;
};

type CouponState = {
  coupons: ReviewCoupon[];
  issueForReview: (input: {
    reviewId: string;
    productId: string;
    productName: string;
    ownerEmail: string;
    userId?: string;
    hasMedia: boolean;
  }) => ReviewCoupon;
  availableFor: (opts: {
    userId?: string | null;
    email?: string | null;
  }) => ReviewCoupon[];
  markUsed: (couponId: string, orderId: string) => void;
};

export function couponAmountForMedia(hasMedia: boolean) {
  return hasMedia ? REVIEW_COUPON_MEDIA : REVIEW_COUPON_TEXT;
}

export function couponLabelForMedia(hasMedia: boolean) {
  return hasMedia
    ? "포토·영상 리뷰 감사 쿠폰"
    : "텍스트 리뷰 감사 쿠폰";
}

export const useCouponStore = create<CouponState>()(
  persist(
    (set, get) => ({
      coupons: [],

      issueForReview({
        reviewId,
        productId,
        productName,
        ownerEmail,
        userId,
        hasMedia,
      }) {
        const email = ownerEmail.trim().toLowerCase();
        const amountKrw = couponAmountForMedia(hasMedia);
        const coupon: ReviewCoupon = {
          id: `cpn-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
          kind: hasMedia ? "review-media" : "review-text",
          amountKrw,
          label: couponLabelForMedia(hasMedia),
          reviewId,
          productId,
          productName,
          userId,
          ownerEmail: email,
          status: "available",
          createdAt: new Date().toISOString(),
        };
        set((s) => ({ coupons: [coupon, ...s.coupons] }));
        return coupon;
      },

      availableFor({ userId, email }) {
        const key = email?.trim().toLowerCase() || "";
        return get()
          .coupons.filter((c) => c.status === "available")
          .filter((c) => {
            if (userId && c.userId === userId) return true;
            if (key && c.ownerEmail === key) return true;
            return false;
          })
          .sort((a, b) => b.amountKrw - a.amountKrw);
      },

      markUsed(couponId, orderId) {
        const now = new Date().toISOString();
        set((s) => ({
          coupons: s.coupons.map((c) =>
            c.id === couponId
              ? {
                  ...c,
                  status: "used" as const,
                  usedAt: now,
                  usedOrderId: orderId,
                }
              : c,
          ),
        }));
      },
    }),
    { name: "briq-coupons-v1" },
  ),
);
