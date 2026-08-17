"use client";

import Link from "next/link";
import { buildDailyPlan, buildMaterialHtml } from "@/lib/swing/coaching";
import { getPro } from "@/lib/swing/pros";
import { todayKey, useSwingStore } from "@/lib/swing/store";

function download(filename: string, html: string) {
  const blob = new Blob([html], { type: "text/html;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function MaterialsPanel() {
  const tier = useSwingStore((s) => s.tier);
  const lastResult = useSwingStore((s) => s.lastResult);
  const sessions = useSwingStore((s) => s.sessions);
  const pro = getPro(lastResult?.proId ?? "puregolf-tour");

  if (tier !== "pro") {
    return (
      <div className="swing-page">
        <header className="swing-page__head">
          <p className="swing-kicker">교정 자료</p>
          <h1>오늘 할 드릴을 파일로 배포합니다</h1>
          <p>유료 회원은 HTML 시트를 받아 인쇄하거나 연습장에서 펼칩니다.</p>
        </header>
        <Link href="/swing/membership" className="swing-btn">
          유료로 자료 받기
        </Link>
      </div>
    );
  }

  if (!lastResult || !pro) {
    return (
      <div className="swing-page">
        <header className="swing-page__head">
          <p className="swing-kicker">교정 자료</p>
          <h1>배포할 분석이 없습니다</h1>
        </header>
        <Link href="/swing/analyze" className="swing-btn">
          먼저 분석
        </Link>
      </div>
    );
  }

  const plan = buildDailyPlan({
    date: todayKey(),
    focus: lastResult.coachingFocus,
    pro,
    overall: lastResult.overall,
    userValue: lastResult.userMetrics[lastResult.coachingFocus],
    proValue: lastResult.proMetrics[lastResult.coachingFocus],
  });

  function issue() {
    const html = buildMaterialHtml({
      memberName: "Briq Swing 회원",
      proName: pro!.nameKo,
      date: lastResult!.createdAt,
      overall: lastResult!.overall,
      plan,
      history: sessions.map((s) => ({
        date: s.createdAt,
        overall: s.overall,
      })),
    });
    download(`briq-swing-${todayKey()}.html`, html);
  }

  return (
    <div className="swing-page">
      <header className="swing-page__head">
        <p className="swing-kicker">교정 자료 배포</p>
        <h1>{pro.nameKo} 기준 오늘 시트</h1>
        <p>{plan.why}</p>
      </header>
      <ol className="swing-drills">
        {plan.drills.map((d) => (
          <li key={d.name}>
            <h2>{d.name}</h2>
            <p className="swing-drills__sets">{d.sets}</p>
            <p>{d.how}</p>
          </li>
        ))}
      </ol>
      <div className="swing-hero__cta">
        <button type="button" className="swing-btn" onClick={issue}>
          HTML 자료 다운로드
        </button>
        <button
          type="button"
          className="swing-btn swing-btn--ghost"
          onClick={() => {
            issue();
            window.setTimeout(() => window.print(), 400);
          }}
        >
          인쇄
        </button>
      </div>
      <p className="swing-note">
        원본 영상은 이 기기에만 있습니다. 배포되는 것은 드릴·점수 요약입니다.
      </p>
    </div>
  );
}
