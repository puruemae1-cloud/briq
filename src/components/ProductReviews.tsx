"use client";

import { FormEvent, useMemo, useRef, useState } from "react";
import { ImagePlus, Star, Video } from "lucide-react";
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
  const fileRef = useRef<HTMLInputElement>(null);

  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [rating, setRating] = useState(5);
  const [body, setBody] = useState("");
  const [media, setMedia] = useState<ReviewMedia[]>([]);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const list = useMemo(
    () => items.filter((i) => i.productId === productId),
    [items, productId],
  );

  const average =
    list.length === 0
      ? 0
      : list.reduce((sum, r) => sum + r.rating, 0) / list.length;

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
    const text = body.trim();
    if (!authorName || !text) {
      setError("이름과 리뷰 내용을 입력해 주세요.");
      return;
    }

    setBusy(true);
    const reviewId = `rv-${Date.now()}`;
    const item = {
      id: reviewId,
      productId,
      productName,
      authorName,
      rating,
      body: text,
      media,
      createdAt: new Date().toISOString(),
    };
    add(item);

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
    setNotice("리뷰가 등록되었습니다. 소중한 후기 감사합니다.");
  }

  return (
    <div className="engage-panel">
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
              사진 최대 4장 · 동영상 1개(8MB 이하)
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
            {busy ? "등록 중…" : "리뷰 등록"}
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
