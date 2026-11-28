"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Eye, EyeOff, Lock, MessageCircleQuestion } from "lucide-react";
import { isAdminUser, useAuthStore } from "@/lib/auth-store";
import { useQaStore, type QaVisibility } from "@/lib/qa-store";

export function ProductQA({
  productId,
  productName,
}: {
  productId: string;
  productName: string;
}) {
  const items = useQaStore((s) => s.items);
  const add = useQaStore((s) => s.add);
  const answerQa = useQaStore((s) => s.answer);
  const ensureAdminSeeded = useAuthStore((s) => s.ensureAdminSeeded);
  const user = useAuthStore((s) => s.currentUser());
  const isAdmin = isAdminUser(user);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [question, setQuestion] = useState("");
  const [visibility, setVisibility] = useState<QaVisibility>("public");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [replyingId, setReplyingId] = useState<string | null>(null);

  useEffect(() => {
    ensureAdminSeeded();
  }, [ensureAdminSeeded]);

  useEffect(() => {
    if (user && !isAdmin) {
      setName(user.name || "");
      setEmail(user.email || "");
      setPhone(user.phone || "");
    }
  }, [user, isAdmin]);

  const list = useMemo(() => {
    const mineKey = (email.trim() || user?.email || "").toLowerCase();
    return items
      .filter((i) => i.productId === productId)
      .filter((i) => {
        if (isAdmin) return true;
        if (i.visibility === "public") return true;
        if (!mineKey) return false;
        return (i.authorEmail || "").toLowerCase() === mineKey;
      });
  }, [items, productId, email, user?.email, isAdmin]);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setNotice(null);

    const authorName = name.trim();
    const q = question.trim();
    if (!authorName || !q) {
      setError("이름과 질문을 입력해 주세요.");
      return;
    }

    setBusy(true);
    add({
      id: `qa-${Date.now()}`,
      productId,
      productName,
      authorName,
      authorEmail: email.trim() || undefined,
      authorPhone: phone.trim() || undefined,
      question: q,
      visibility,
      createdAt: new Date().toISOString(),
    });

    setQuestion("");
    setOpen(false);
    setBusy(false);
    setNotice(
      visibility === "private"
        ? "비밀 질문이 등록되었습니다. Briq 담당자가 확인 후 답변드립니다."
        : "질문이 등록되었습니다. Briq 담당자가 확인 후 답변드립니다.",
    );
  }

  function onReply(e: FormEvent, qaId: string) {
    e.preventDefault();
    if (!isAdmin || !user) return;
    setError(null);
    const result = answerQa(qaId, drafts[qaId] || "", user.name);
    if (!result.ok) {
      setError(result.message);
      return;
    }
    setDrafts((d) => {
      const next = { ...d };
      delete next[qaId];
      return next;
    });
    setReplyingId(null);
    setNotice("답변이 등록되었습니다.");
  }

  return (
    <div className="engage-panel">
      <div className="engage-panel__toolbar">
        <p className="engage-panel__count">
          <MessageCircleQuestion size={16} aria-hidden />
          등록된 문의 {list.length}
          {isAdmin ? (
            <Link href="/account/admin/qa" className="engage-admin-link">
              관리 목록
            </Link>
          ) : null}
        </p>
        {!isAdmin ? (
          <button
            type="button"
            className="btn btn-outline engage-panel__cta"
            onClick={() => setOpen((v) => !v)}
          >
            {open ? "작성 닫기" : "문의 작성"}
          </button>
        ) : (
          <span className="engage-admin-badge">관리자 · 답변 모드</span>
        )}
      </div>

      {notice ? <p className="engage-banner engage-banner--ok">{notice}</p> : null}
      {error ? <p className="engage-banner engage-banner--err">{error}</p> : null}

      {open && !isAdmin ? (
        <form className="engage-form" onSubmit={onSubmit}>
          <div className="engage-visibility" role="radiogroup" aria-label="공개 설정">
            <button
              type="button"
              className={`engage-visibility__btn${visibility === "public" ? " is-active" : ""}`}
              aria-pressed={visibility === "public"}
              onClick={() => setVisibility("public")}
            >
              <Eye size={15} aria-hidden />
              공개
            </button>
            <button
              type="button"
              className={`engage-visibility__btn${visibility === "private" ? " is-active" : ""}`}
              aria-pressed={visibility === "private"}
              onClick={() => setVisibility("private")}
            >
              <Lock size={15} aria-hidden />
              비밀글
            </button>
          </div>
          <p className="engage-form__hint">
            {visibility === "private"
              ? "비밀글은 본인(동일 이메일)과 Briq 관리자만 확인할 수 있습니다. 일반 고객은 답글을 달 수 없습니다."
              : "공개 문의는 상품 페이지에 노출됩니다. 답변은 Briq 관리자만 작성할 수 있습니다."}
          </p>

          <div className="engage-form__grid">
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
              <span>이메일 (비밀글 확인용)</span>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@email.com"
                autoComplete="email"
              />
            </label>
            <label className="engage-field">
              <span>연락처 (선택)</span>
              <input
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="010-0000-0000"
                autoComplete="tel"
              />
            </label>
          </div>

          <label className="engage-field">
            <span>문의 내용</span>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              required
              rows={5}
              maxLength={2000}
              placeholder="사이즈, 배송, 구성품 등 궁금한 점을 남겨 주세요."
            />
          </label>

          <button type="submit" className="btn btn-solid" disabled={busy}>
            {busy ? "등록 중…" : "문의 등록"}
          </button>
        </form>
      ) : null}

      <ul className="engage-list">
        {list.length === 0 ? (
          <li className="engage-empty">아직 등록된 문의가 없습니다.</li>
        ) : (
          list.map((item) => (
            <li key={item.id} className="engage-item">
              <div className="engage-item__meta">
                <span className="engage-item__author">
                  {isAdmin ? item.authorName : maskName(item.authorName)}
                </span>
                <span className="engage-item__dot" aria-hidden>
                  ·
                </span>
                <time dateTime={item.createdAt}>
                  {formatDate(item.createdAt)}
                </time>
                {item.visibility === "private" ? (
                  <span className="engage-pill">
                    <EyeOff size={12} aria-hidden /> 비밀
                  </span>
                ) : (
                  <span className="engage-pill engage-pill--public">공개</span>
                )}
              </div>
              {isAdmin && (item.authorEmail || item.authorPhone) ? (
                <p className="engage-item__contact">
                  {[item.authorEmail, item.authorPhone].filter(Boolean).join(" · ")}
                </p>
              ) : null}
              <p className="engage-item__body">{item.question}</p>
              {item.answer ? (
                <div className="engage-answer">
                  <p className="engage-answer__label">
                    Briq 답변
                    {item.answeredBy ? ` · ${item.answeredBy}` : ""}
                  </p>
                  <p>{item.answer}</p>
                  {isAdmin ? (
                    <button
                      type="button"
                      className="engage-answer__edit"
                      onClick={() => {
                        setReplyingId(item.id);
                        setDrafts((d) => ({
                          ...d,
                          [item.id]: item.answer || "",
                        }));
                      }}
                    >
                      답변 수정
                    </button>
                  ) : null}
                </div>
              ) : (
                <p className="engage-item__pending">답변 대기 중</p>
              )}

              {isAdmin && (replyingId === item.id || !item.answer) ? (
                <form
                  className="engage-reply"
                  onSubmit={(e) => onReply(e, item.id)}
                >
                  <label className="engage-field">
                    <span>관리자 답변</span>
                    <textarea
                      value={drafts[item.id] || ""}
                      onChange={(e) =>
                        setDrafts((d) => ({ ...d, [item.id]: e.target.value }))
                      }
                      rows={3}
                      required
                      placeholder="고객에게 전달할 답변을 작성해 주세요."
                    />
                  </label>
                  <div className="engage-reply__actions">
                    <button type="submit" className="btn btn-solid">
                      {item.answer ? "답변 저장" : "답변 등록"}
                    </button>
                    {item.answer ? (
                      <button
                        type="button"
                        className="btn btn-outline"
                        onClick={() => setReplyingId(null)}
                      >
                        취소
                      </button>
                    ) : null}
                  </div>
                </form>
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
