"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { MessageCircleQuestion } from "lucide-react";
import { isAdminUser, useAuthStore } from "@/lib/auth-store";
import { qaStaffHeaders, refreshQa, useQaStore, type QaItem } from "@/lib/qa-store";

export function ProductQA({
  productId,
  productName,
  initialItems = [],
}: {
  productId: string;
  productName: string;
  initialItems?: QaItem[];
}) {
  const items = useQaStore((s) => s.items);
  const answerQa = useQaStore((s) => s.answer);
  const ensureAdminSeeded = useAuthStore((s) => s.ensureAdminSeeded);
  const user = useAuthStore((s) => s.currentUser());
  const isAdmin = isAdminUser(user);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [secret, setSecret] = useState(false);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [synced, setSynced] = useState(false);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [replyingId, setReplyingId] = useState<string | null>(null);

  useEffect(() => {
    ensureAdminSeeded();
    let cancel = false;
    void refreshQa(productId, { staff: isAdmin }).finally(() => {
      if (!cancel) setSynced(true);
    });
    return () => {
      cancel = true;
    };
  }, [ensureAdminSeeded, productId, isAdmin]);

  useEffect(() => {
    if (user && !isAdmin) {
      setName(user.name || "");
    }
  }, [user, isAdmin]);

  const list = useMemo(() => {
    const fromStore = items.filter((i) => i.productId === productId);
    if (!synced && fromStore.length === 0) return initialItems;
    return fromStore;
  }, [items, productId, initialItems, synced]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setNotice(null);

    const authorName = name.trim() || "고객";
    const q = question.trim();
    const authorEmail = email.trim();
    if (!q) {
      setError("문의 내용을 입력해 주세요.");
      return;
    }
    if (secret && authorEmail && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(authorEmail)) {
      setError("이메일 형식을 확인해 주세요.");
      return;
    }

    setBusy(true);
    try {
      const res = await fetch("/api/qa", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          productId,
          productName,
          authorName,
          authorEmail: secret ? authorEmail : undefined,
          question: q,
          visibility: secret ? "private" : "public",
        }),
      });
      const data = (await res.json()) as { ok?: boolean; message?: string };
      if (!res.ok || !data.ok) {
        setError(data.message || "문의를 등록하지 못했습니다.");
        return;
      }
      setQuestion("");
      setSecret(false);
      setEmail("");
      await refreshQa(productId, { staff: isAdmin });
      setNotice(
        secret
          ? "비밀 문의로 등록되었습니다. 다른 고객에게는 보이지 않고 Briq만 확인합니다."
          : "질문이 등록되었습니다. 이 페이지를 보는 누구나 확인할 수 있습니다.",
      );
    } catch {
      setError("문의를 등록하지 못했습니다.");
    } finally {
      setBusy(false);
    }
  }

  async function onReply(e: FormEvent, qaId: string) {
    e.preventDefault();
    if (!isAdmin || !user) return;
    setError(null);
    const text = (drafts[qaId] || "").trim();
    if (!text) {
      setError("답변 내용을 입력해 주세요.");
      return;
    }
    const res = await fetch("/api/qa", {
      method: "PATCH",
      headers: qaStaffHeaders(),
      body: JSON.stringify({ id: qaId, answer: text, answeredBy: user.name }),
    });
    const data = (await res.json()) as { ok?: boolean; message?: string };
    if (!res.ok || !data.ok) {
      setError(data.message || "답변을 저장하지 못했습니다.");
      return;
    }
    const result = answerQa(qaId, text, user.name);
    if (!result.ok) {
      setError(result.message);
      return;
    }
    await refreshQa(productId, { staff: true });
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
        {isAdmin ? (
          <span className="engage-admin-badge">관리자 · 답변 모드</span>
        ) : null}
      </div>

      {notice ? <p className="engage-banner engage-banner--ok">{notice}</p> : null}
      {error ? <p className="engage-banner engage-banner--err">{error}</p> : null}

      {!isAdmin ? (
        <form className="engage-form" onSubmit={onSubmit}>
          <label className="engage-field">
            <span>문의 내용</span>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              required
              rows={4}
              maxLength={2000}
              placeholder="사이즈, 배송, 구성품 등 궁금한 점을 남겨 주세요."
            />
          </label>

          <label className="engage-check">
            <input
              type="checkbox"
              checked={secret}
              onChange={(e) => setSecret(e.target.checked)}
            />
            <span>비밀 문의로 남기기. 다른 고객에게는 보이지 않습니다.</span>
          </label>

          <div className="engage-form__grid">
            <label className="engage-field">
              <span>이름 (선택)</span>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="비워 두면 고객으로 표시됩니다"
                autoComplete="name"
              />
            </label>
            {secret ? (
              <label className="engage-field">
                <span>이메일 (선택)</span>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="답변을 메일로 받으려면 입력"
                  autoComplete="email"
                />
              </label>
            ) : null}
          </div>

          {secret ? (
            <p className="engage-form__hint">
              비밀 문의는 상품 페이지에 공개되지 않습니다. Briq이 확인하고, 이메일을 남기면 그 주소로 답장을 드릴 수 있습니다.
            </p>
          ) : null}

          <button type="submit" className="btn btn-solid" disabled={busy}>
            {busy ? "등록 중…" : "문의 남기기"}
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
                {isAdmin && item.visibility === "private" ? (
                  <span className="engage-pill">비밀</span>
                ) : null}
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
