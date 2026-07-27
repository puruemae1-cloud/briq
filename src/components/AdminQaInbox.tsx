"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { AccountNav } from "@/components/AccountNav";
import { isAdminUser, useAuthStore } from "@/lib/auth-store";
import { useQaStore } from "@/lib/qa-store";

export function AdminQaInbox() {
  const ensureAdminSeeded = useAuthStore((s) => s.ensureAdminSeeded);
  const user = useAuthStore((s) => s.currentUser());
  const items = useQaStore((s) => s.items);
  const answerQa = useQaStore((s) => s.answer);
  const [filter, setFilter] = useState<"pending" | "all">("pending");
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    ensureAdminSeeded();
  }, [ensureAdminSeeded]);

  const list = useMemo(() => {
    const sorted = [...items].sort(
      (a, b) => +new Date(b.createdAt) - +new Date(a.createdAt),
    );
    if (filter === "pending") return sorted.filter((i) => !i.answer);
    return sorted;
  }, [items, filter]);

  if (!user) {
    return (
      <section className="section account-shell">
        <div className="panel account-gate">
          <h1>관리자 로그인 필요</h1>
          <p>Q&A 답변은 관리자 계정으로 로그인한 뒤 이용할 수 있습니다.</p>
          <Link
            href="/account/login?next=/account/admin/qa"
            className="btn btn-solid"
          >
            로그인
          </Link>
        </div>
      </section>
    );
  }

  if (!isAdminUser(user)) {
    return (
      <section className="section account-shell">
        <div className="panel account-gate">
          <h1>접근 권한이 없습니다</h1>
          <p>일반 회원은 Q&A에 답글을 달 수 없습니다.</p>
          <Link href="/account" className="btn btn-outline">
            마이페이지
          </Link>
        </div>
      </section>
    );
  }

  function onReply(e: FormEvent, qaId: string) {
    e.preventDefault();
    setError(null);
    setNotice(null);
    const result = answerQa(qaId, drafts[qaId] || "", user!.name);
    if (!result.ok) {
      setError(result.message);
      return;
    }
    setDrafts((d) => {
      const next = { ...d };
      delete next[qaId];
      return next;
    });
    setNotice("답변이 저장되었습니다.");
  }

  return (
    <section className="section account-shell">
      <div className="account-layout">
        <AccountNav />
        <div className="account-main">
          <header className="account-main__head">
            <p className="product-card__brand">Admin</p>
            <h1>Q&A 관리</h1>
            <p className="account-main__email">
              고객 문의에 답변합니다. 일반 회원은 답글을 작성할 수 없습니다.
            </p>
          </header>

          <div className="engage-visibility" style={{ marginBottom: "1rem" }}>
            <button
              type="button"
              className={`engage-visibility__btn${filter === "pending" ? " is-active" : ""}`}
              onClick={() => setFilter("pending")}
            >
              미답변
            </button>
            <button
              type="button"
              className={`engage-visibility__btn${filter === "all" ? " is-active" : ""}`}
              onClick={() => setFilter("all")}
            >
              전체
            </button>
          </div>

          {notice ? (
            <p className="engage-banner engage-banner--ok">{notice}</p>
          ) : null}
          {error ? (
            <p className="engage-banner engage-banner--err">{error}</p>
          ) : null}

          <ul className="engage-list">
            {list.length === 0 ? (
              <li className="engage-empty">
                {filter === "pending"
                  ? "대기 중인 문의가 없습니다."
                  : "등록된 문의가 없습니다."}
              </li>
            ) : (
              list.map((item) => (
                <li key={item.id} className="engage-item">
                  <div className="engage-item__meta">
                    <Link
                      href={`/product/${item.productId}`}
                      className="engage-item__product"
                    >
                      {item.productName}
                    </Link>
                    <span className="engage-item__dot" aria-hidden>
                      ·
                    </span>
                    <span>{item.authorName}</span>
                    <span className="engage-item__dot" aria-hidden>
                      ·
                    </span>
                    <time dateTime={item.createdAt}>
                      {new Intl.DateTimeFormat("ko-KR", {
                        dateStyle: "medium",
                        timeStyle: "short",
                      }).format(new Date(item.createdAt))}
                    </time>
                    <span
                      className={`engage-pill${item.visibility === "public" ? " engage-pill--public" : ""}`}
                    >
                      {item.visibility === "private" ? "비밀" : "공개"}
                    </span>
                  </div>
                  {(item.authorEmail || item.authorPhone) && (
                    <p className="engage-item__contact">
                      {[item.authorEmail, item.authorPhone]
                        .filter(Boolean)
                        .join(" · ")}
                    </p>
                  )}
                  <p className="engage-item__body">{item.question}</p>
                  {item.answer ? (
                    <div className="engage-answer">
                      <p className="engage-answer__label">
                        등록된 답변
                        {item.answeredBy ? ` · ${item.answeredBy}` : ""}
                      </p>
                      <p>{item.answer}</p>
                    </div>
                  ) : null}
                  <form
                    className="engage-reply"
                    onSubmit={(e) => onReply(e, item.id)}
                  >
                    <label className="engage-field">
                      <span>{item.answer ? "답변 수정" : "답변 작성"}</span>
                      <textarea
                        value={drafts[item.id] ?? item.answer ?? ""}
                        onChange={(e) =>
                          setDrafts((d) => ({
                            ...d,
                            [item.id]: e.target.value,
                          }))
                        }
                        rows={3}
                        required
                        placeholder="답변을 입력하세요"
                      />
                    </label>
                    <button type="submit" className="btn btn-solid">
                      저장
                    </button>
                  </form>
                </li>
              ))
            )}
          </ul>
        </div>
      </div>
    </section>
  );
}
