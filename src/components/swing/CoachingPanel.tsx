"use client";

import Link from "next/link";
import { buildDailyPlan } from "@/lib/swing/coaching";
import { getPro } from "@/lib/swing/pros";
import { todayKey, useSwingStore } from "@/lib/swing/store";
import { METRIC_LABEL_KO, PHASE_LABEL_KO } from "@/lib/swing/types";

export function CoachingPanel() {
  const tier = useSwingStore((s) => s.tier);
  const lastResult = useSwingStore((s) => s.lastResult);
  const pro = getPro(lastResult?.proId ?? "puregolf-tour");

  if (tier !== "pro") {
    return (
      <div className="swing-page">
        <header className="swing-page__head">
          <p className="swing-kicker">데일리 코칭</p>
          <h1>매일 한 가지 간격만 좁힙니다</h1>
          <p>
            유료 회원은 최근 분석의 1순위 결함을 오늘의 드릴 3개로 풀어 주고, 주말에는
            영상을 다시 올리라고 안내합니다.
          </p>
        </header>
        <div className="swing-banner">
          트라이얼은 분석 요약만 제공합니다.{" "}
          <Link href="/swing/membership">유료로 데일리 코칭 열기</Link>
        </div>
      </div>
    );
  }

  if (!lastResult || !pro) {
    return (
      <div className="swing-page">
        <header className="swing-page__head">
          <p className="swing-kicker">데일리 코칭</p>
          <h1>먼저 스윙을 한 번 올려 주세요</h1>
        </header>
        <Link href="/swing/analyze" className="swing-btn">
          분석하기
        </Link>
      </div>
    );
  }

  const gap = lastResult.gaps.find((g) => g.key === lastResult.coachingFocus);
  const plan = buildDailyPlan({
    date: todayKey(),
    focus: lastResult.coachingFocus,
    pro,
    overall: lastResult.overall,
    userValue: lastResult.userMetrics[lastResult.coachingFocus],
    proValue: lastResult.proMetrics[lastResult.coachingFocus],
  });

  return (
    <div className="swing-page">
      <header className="swing-page__head">
        <p className="swing-kicker">오늘 · {plan.date}</p>
        <h1>{plan.title}</h1>
        <p>{plan.why}</p>
      </header>
      <p className="swing-focus">
        포커스 <strong>{METRIC_LABEL_KO[plan.focus]}</strong>
        {gap ? ` · 나 ${gap.user} / 프로 ${gap.pro}` : null}
      </p>
      <ol className="swing-drills">
        {plan.drills.map((d) => (
          <li key={d.name}>
            <h2>{d.name}</h2>
            <p className="swing-drills__sets">{d.sets}</p>
            <p>{d.how}</p>
            <p className="swing-gaps__feel">감각: {d.feel}</p>
          </li>
        ))}
      </ol>
      <p className="swing-note">{plan.checkpoint}</p>
      {lastResult.phaseNotes.length ? (
        <div className="swing-phases">
          {lastResult.phaseNotes.map((p) => (
            <article key={p.phase}>
              <h3>{PHASE_LABEL_KO[p.phase]}</h3>
              <p>{p.note}</p>
            </article>
          ))}
        </div>
      ) : null}
      <Link href="/swing/materials" className="swing-btn">
        오늘 자료 배포받기
      </Link>
    </div>
  );
}
