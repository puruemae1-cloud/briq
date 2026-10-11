"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { Gift, ImagePlus, Star, Video } from "lucide-react";
import { formatKrw } from "@/data/products";
import { useAuthStore } from "@/lib/auth-store";
import {
  REVIEW_COUPON_MEDIA,
  REVIEW_COUPON_TEXT,
  useCouponStore,
} from "@/lib/coupon-store";
import {
  readMediaFile,
  useReviewStore,
  type ReviewMedia,
} from "@/lib/review-store";

export function ProductReviews({
  productId,
  productName,
}: {
  productId: string;
  productName: string;
}) {
  const items = useReviewStore((s) => s.items);
  const add = useReviewStore((s) => s.add);
  const issueCoupon = useCouponStore((s) => s.issueForReview);
  const user = useAuthStore((s) => s.currentUser());
  const fileRef = useRef<HTMLInputElement>(null);

  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [rating, setRating] = useState(5);
  const [body, setBody] = useState("");
  const [media, setMedia] = useState<ReviewMedia[]>([]);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      setName(user.name || "");
      setEmail(user.email || "");
    }
  }, [user]);

  const list = useMemo(
    () => items.filter((i) => i.productId === productId),
    [items, productId],
  );

  const average =
    list.length === 0
      ? 0
      : list.reduce((sum, r) => sum + r.rating, 0) / list.length;

  const previewAmount =
    media.length > 0 ? REVIEW_COUPON_MEDIA : REVIEW_COUPON_TEXT;

  async function onPickFiles(files: FileList | null) {
    if (!files?.length) return;
    setError(null);
    try {
      const next: ReviewMedia[] = [...media];
      for (const file of Array.from(files)) {
        const images = next.filter((m) => m.type === "image").length;
        const videos = next.filter((m) => m.type === "video").length;
        if (file.type.startsWith("video/") && videos >= 1) {
          throw new Error("동영상은 1개까지 첨부할 수 있습니다.");
        }
        if (file.type.startsWith("image/") && images >= 4) {
          throw new Error("사진은 최대 4장까지 첨부할 수 있습니다.");
        }
        if (next.length >= 5) {
          throw new Error("미디어는 최대 5개까지 첨부할 수 있습니다.");
        }
        next.push(await readMediaFile(file));
      }
      setMedia(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : "첨부에 실패했습니다.");
    } finally {
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setNotice(null);

    const authorName = name.trim();
    const authorEmail = email.trim().toLowerCase();
    const text = body.trim();
    if (!authorName || !text) {
      setError("이름과 리뷰 내용을 입력해 주세요.");
      return;
    }
    if (!authorEmail || !authorEmail.includes("@")) {
      setError("쿠폰 지급을 위해 이메일을 입력해 주세요.");
      return;
    }

    setBusy(true);
    const reviewId = `rv-${Date.now()}`;
    const hasMedia = media.length > 0;

    const coupon = issueCoupon({
      reviewId,
      productId,
      productName,
      ownerEmail: authorEmail,
      userId: user?.id,
      hasMedia,
    });

    add({
      id: reviewId,
      productId,
      productName,
      authorName,
      authorEmail,
      userId: user?.id,
      rating,
      body: text,
      media,
      createdAt: new Date().toISOString(),
      couponId: coupon.id,
      couponAmountKrw: coupon.amountKrw,
    });

    try {
      await fetch("/api/notify/review", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          productId,
          productName,
          authorName,
          rating,
          body: text,
          mediaCount: media.length,
          reviewId,
        }),
      });
    } catch {
      // Local save is enough for the shopper; mail is best-effort.
    }

    setBody("");
    setMedia([]);
    setRating(5);
    setOpen(false);
    setBusy(false);
    setNotice(
      `리뷰가 등록되었습니다. ${formatKrw(coupon.amountKrw)} 할인 쿠폰이 지급되었습니다. 다음 결제 시 자동으로 적용할 수 있습니다.`,
    );
  }

  return (
    <div className="engage-panel">
      <aside className="review-perk" aria-label="리뷰 혜택 안내">
        <p className="review-perk__eyebrow">
          <Gift size={14} aria-hidden /> Review Privilege
        </p>
        <h3 className="review-perk__title">리뷰 감사 쿠폰</h3>
        <p className="review-perk__lead">
          소중한 후기를 남겨 주시면, 다음 구매에 바로 쓸 수 있는 할인 쿠폰을
          자동 지급해 드립니다.
        </p>
        <div className="review-perk__tiers">
          <div className="review-perk__tier">
            <p className="review-perk__tier-label">텍스트 리뷰</p>
            <p className="review-perk__tier-value">
              {formatKrw(REVIEW_COUPON_TEXT)}
            </p>
            <p className="review-perk__tier-hint">다음 결제 즉시 할인</p>
          </div>
          <div className="review-perk__tier review-perk__tier--featured">
            <p className="review-perk__tier-label">포토 · 영상 리뷰</p>
            <p className="review-perk__tier-value">
              {formatKrw(REVIEW_COUPON_MEDIA)}
            </p>
            <p className="review-perk__tier-hint">사진 또는 동영상 첨부 시</p>
          </div>
        </div>
        <p className="review-perk__note">
          쿠폰은 리뷰에 입력하신 이메일(또는 로그인 계정)로 지급되며, 마이페이지
          · 쿠폰함과 결제 단계에서 확인할 수 있습니다.
          {!user ? (
            <>
              {" "}
              <Link href="/account/login">로그인</Link>하시면 쿠폰 관리가 더
              편리합니다.
            </>
          ) : null}
        </p>
      </aside>

      <div className="engage-panel__toolbar">
        <div className="review-summary">
          <p className="review-summary__score">
            <Star size={16} fill="currentColor" aria-hidden />
            {list.length ? average.toFixed(1) : "—"}
          </p>
          <p className="review-summary__meta">리뷰 {list.length}건</p>
        </div>
        <button
          type="button"
          className="btn btn-outline engage-panel__cta"
          onClick={() => setOpen((v) => !v)}
        >
          {open ? "작성 닫기" : "리뷰 작성"}
        </button>
      </div>

      {notice ? <p className="engage-banner engage-banner--ok">{notice}</p> : null}
      {error ? <p className="engage-banner engage-banner--err">{error}</p> : null}

      {open ? (
        <form className="engage-form" onSubmit={onSubmit}>
          <p className="review-form-perk">
            이번 리뷰 예상 쿠폰 · <strong>{formatKrw(previewAmount)}</strong>
            {media.length > 0 ? " (포토·영상)" : " (텍스트)"}
          </p>

          <div className="review-stars" role="radiogroup" aria-label="별점">
            {[1, 2, 3, 4, 5].map((n) => (
              <button
                key={n}
                type="button"
                className={`review-stars__btn${rating >= n ? " is-on" : ""}`}
                aria-label={`${n}점`}
                aria-pressed={rating === n}
                onClick={() => setRating(n)}
              >
                <Star size={22} fill={rating >= n ? "currentColor" : "none"} />
              </button>
            ))}
          </div>

          <div className="engage-form__grid engage-form__grid--2">
            <label className="engage-field">
              <span>이름</span>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                placeholder="홍길동"
                autoComplete="name"
              />
            </label>
            <label className="engage-field">
              <span>이메일 (쿠폰 지급)</span>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="you@email.com"
                autoComplete="email"
              />
            </label>
          </div>

          <label className="engage-field">
            <span>리뷰</span>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              required
              rows={5}
              maxLength={3000}
              placeholder="착용감, 사이즈, 배송 경험을 남겨 주세요."
            />
          </label>

          <div className="review-media-picker">
            <input
              ref={fileRef}
              type="file"
              accept="image/*,video/*"
              multiple
              hidden
              onChange={(e) => onPickFiles(e.target.files)}
            />
            <button
              type="button"
              className="btn btn-outline"
              onClick={() => fileRef.current?.click()}
            >
              <ImagePlus size={16} aria-hidden />
              사진 · 동영상 첨부
            </button>
            <p className="engage-form__hint">
              사진/영상 첨부 시 {formatKrw(REVIEW_COUPON_MEDIA)} 쿠폰 · 텍스트만
              작성 시 {formatKrw(REVIEW_COUPON_TEXT)} 쿠폰
            </p>
          </div>

          {media.length > 0 ? (
            <ul className="review-media-draft">
              {media.map((m) => (
                <li key={m.id} className="review-media-draft__item">
                  {m.type === "image" ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={m.dataUrl} alt={m.name} />
                  ) : (
                    <span className="review-media-draft__video">
                      <Video size={18} aria-hidden />
                      {m.name}
                    </span>
                  )}
                  <button
                    type="button"
                    className="review-media-draft__remove"
                    onClick={() =>
                      setMedia((prev) => prev.filter((x) => x.id !== m.id))
                    }
                  >
                    삭제
                  </button>
                </li>
              ))}
            </ul>
          ) : null}

          <button type="submit" className="btn btn-solid" disabled={busy}>
            {busy
              ? "등록 중…"
              : `리뷰 등록 · ${formatKrw(previewAmount)} 쿠폰 받기`}
          </button>
        </form>
      ) : null}

      <ul className="engage-list">
        {list.length === 0 ? (
          <li className="engage-empty">첫 리뷰의 주인공이 되어 보세요.</li>
        ) : (
          list.map((item) => (
            <li key={item.id} className="engage-item review-card">
              <div className="engage-item__meta">
                <span className="review-card__stars" aria-label={`${item.rating}점`}>
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Star
                      key={i}
                      size={13}
                      fill={i < item.rating ? "currentColor" : "none"}
                      aria-hidden
                    />
                  ))}
                </span>
                <span className="engage-item__author">{maskName(item.authorName)}</span>
                <span className="engage-item__dot" aria-hidden>
                  ·
                </span>
                <time dateTime={item.createdAt}>
                  {formatDate(item.createdAt)}
                </time>
                {item.media.length > 0 ? (
                  <span className="engage-pill engage-pill--public">포토·영상</span>
                ) : (
                  <span className="engage-pill">텍스트</span>
                )}
              </div>
              <p className="engage-item__body">{item.body}</p>
              {item.media.length > 0 ? (
                <div className="review-media">
                  {item.media.map((m) =>
                    m.type === "image" ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        key={m.id}
                        src={m.dataUrl}
                        alt=""
                        className="review-media__img"
                      />
                    ) : (
                      <video
                        key={m.id}
                        className="review-media__video"
                        src={m.dataUrl}
                        controls
                        playsInline
                        preload="metadata"
                      />
                    ),
                  )}
                </div>
              ) : null}
            </li>
          ))
        )}
      </ul>
    </div>
  );
}

function maskName(name: string) {
  const t = name.trim();
  if (t.length <= 1) return "*";
  if (t.length === 2) return `${t[0]}*`;
  return `${t[0]}${"*".repeat(Math.min(3, t.length - 2))}${t[t.length - 1]}`;
}

function formatDate(iso: string) {
  try {
    return new Intl.DateTimeFormat("ko-KR", {
      year: "numeric",
      month: "short",
      day: "numeric",
    }).format(new Date(iso));
  } catch {
    return iso.slice(0, 10);
  }
}
