"use client";

import Link from "next/link";
import { PROS, getPro } from "@/lib/swing/pros";
import { useSwingStore } from "@/lib/swing/store";

export function ProsPanel() {
  const preferredProId = useSwingStore((s) => s.preferredProId);
  const setPreferredPro = useSwingStore((s) => s.setPreferredPro);

  return (
    <div className="swing-page">
      <header className="swing-page__head">
        <p className="swing-kicker">프로 라이브러리</p>
        <h1>비교할 스윙을 고르세요</h1>
        <p>
          @purego1f 가 반복해서 보여주는 앞·뒤 슬로모션을 기준으로, 투어 평균과 선수별
          시그니처를 템플릿으로 넣었습니다.
        </p>
      </header>
      <div className="swing-pro-list">
        {PROS.map((p) => (
          <article key={p.id} className={p.id === preferredProId ? "is-on" : ""}>
            <p>
              {p.tour} · {p.role}
            </p>
            <h2>
              {p.nameKo} <span>{p.name}</span>
            </h2>
            <p>{p.signature}</p>
            <p>{p.whyMatch}</p>
            <ul>
              {p.sources.map((s) => (
                <li key={s.id}>
                  <strong>{s.title}</strong> — {s.learned}
                </li>
              ))}
            </ul>
            <div className="swing-pro-list__actions">
              <button
                type="button"
                className="swing-btn swing-btn--small"
                onClick={() => setPreferredPro(p.id)}
              >
                {p.id === preferredProId ? "선택됨" : "이 프로로 비교"}
              </button>
              {p.instagram ? (
                <a href={p.instagram} target="_blank" rel="noreferrer">
                  Instagram
                </a>
              ) : null}
            </div>
          </article>
        ))}
      </div>
      <p className="swing-note">
        선택한 프로: <strong>{getPro(preferredProId)?.nameKo}</strong> ·{" "}
        <Link href="/swing/analyze">분석으로</Link>
      </p>
    </div>
  );
}
