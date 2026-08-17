"use client";

import Link from "next/link";
import { getPro } from "@/lib/swing/pros";
import { useSwingStore } from "@/lib/swing/store";
import { METRIC_LABEL_KO } from "@/lib/swing/types";

export function ProgressPanel() {
  const tier = useSwingStore((s) => s.tier);
  const sessions = useSwingStore((s) => s.sessions);

  if (tier !== "pro") {
    return (
      <div className="swing-page">
        <header className="swing-page__head">
          <p className="swing-kicker">교정 추이</p>
          <h1>영상이 바뀔 때마다 점수가 쌓입니다</h1>
          <p>유료 회원만 재업로드 이력을 보관합니다.</p>
        </header>
        <Link href="/swing/membership" className="swing-btn">
          유료로 추이 열기
        </Link>
      </div>
    );
  }

  const first = sessions[sessions.length - 1];
  const latest = sessions[0];
  const delta =
    first && latest && sessions.length > 1 ? latest.overall - first.overall : 0;

  return (
    <div className="swing-page">
      <header className="swing-page__head">
        <p className="swing-kicker">교정 추이</p>
        <h1>교정이 먹히고 있는지</h1>
        <p>
          {sessions.length
            ? `기록 ${sessions.length}회 · 첫 분석 대비 ${delta >= 0 ? "+" : ""}${delta}점`
            : "아직 유료 분석 기록이 없습니다."}
        </p>
      </header>

      {sessions.length > 1 ? (
        <div className="swing-chart" aria-hidden>
          {sessions
            .slice()
            .reverse()
            .map((s) => (
              <div key={s.id} className="swing-chart__col">
                <div
                  className="swing-chart__bar"
                  style={{ height: `${Math.max(8, s.overall)}%` }}
                />
                <span>{s.overall}</span>
              </div>
            ))}
        </div>
      ) : null}

      <ul className="swing-sessions">
        {sessions.map((s) => (
          <li key={s.id}>
            <strong>{s.createdAt.slice(0, 10)}</strong>
            <span>{s.overall}점</span>
            <span>{getPro(s.proId)?.nameKo}</span>
            <span>
              {METRIC_LABEL_KO[s.coachingFocus]}
              {s.has3d ? " · 3D" : ""}
            </span>
            <p>{s.note}</p>
          </li>
        ))}
      </ul>
      <Link href="/swing/analyze" className="swing-btn">
        새 영상 올리기
      </Link>
    </div>
  );
}
