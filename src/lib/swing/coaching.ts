import {
  METRIC_LABEL_KO,
  SWING_PHASES,
  type DailyPlan,
  type MetricKey,
  type ProProfile,
} from "./types";
import { gapCopy } from "./copy";

const WEEK_TITLES = [
  "원인 확인 — 슬로모로 한 동작만",
  "감각 만들기 — 하프 스윙",
  "템포에 얹기",
  "풀스윙에 이식",
  "압력 테스트 — 볼 10개만",
  "코스 전 점검",
  "영상으로 재측정",
];

export function buildDailyPlan(opts: {
  date: string;
  focus: MetricKey;
  pro: ProProfile;
  overall: number;
  userValue: number;
  proValue: number;
}): DailyPlan {
  const { date, focus, pro, overall, userValue, proValue } = opts;
  const day = new Date(date + "T12:00:00");
  const dayIndex = day.getDay();
  const copy = gapCopy(focus, userValue, proValue);
  const title = WEEK_TITLES[dayIndex];

  return {
    date,
    dayIndex,
    title,
    focus,
    why: `${pro.nameKo}와 가장 벌어진 항목은 ${METRIC_LABEL_KO[focus]}입니다. 지금 유사도 ${overall}점 — 오늘 드릴은 이 간격만 좁힙니다.`,
    drills: [
      {
        name: copy.drill.split(" (")[0] || copy.drill,
        sets: dayIndex === 6 ? "영상 2테이크 (앞·뒤)" : "3세트 × 8–12회",
        how: copy.drill,
        feel: copy.feel,
      },
      {
        name: `${pro.nameKo} 페이즈 카피 — ${SWING_PHASES[Math.min(dayIndex, 5)]}`,
        sets: "슬로모 6회 + 일반 6회",
        how: pro.phaseCues[SWING_PHASES[Math.min(dayIndex, 5)]],
        feel: "프로 영상과 같은 카메라 높이에서 찍어 비교.",
      },
      {
        name: dayIndex === 6 ? "재업로드 체크" : "피니시 3초 홀드",
        sets: dayIndex === 6 ? "앞면·뒷면 각 1개" : "매 스윙",
        how:
          dayIndex === 6
            ? "오늘 드릴을 반영한 스윙을 앞·뒤에서 올려 3D로 교정 여부를 확인합니다."
            : "피니시에서 3초. 밸런스가 깨지면 다운이 급했던 것입니다.",
        feel: "밸런스가 남으면 시퀀스가 산 것입니다.",
      },
    ],
    checkpoint:
      dayIndex === 6
        ? "유료 회원은 오늘 영상을 다시 올려 지난 세션 대비 점수가 올랐는지 확인하세요."
        : `${METRIC_LABEL_KO[focus]}가 내일도 1순위면 같은 드릴을 반복하는 편이 새 동작을 넣는 것보다 낫습니다.`,
  };
}

export function buildMaterialHtml(opts: {
  memberName: string;
  proName: string;
  date: string;
  overall: number;
  plan: DailyPlan;
  history: { date: string; overall: number }[];
}) {
  const rows = opts.history
    .slice(0, 8)
    .map(
      (h) =>
        `<tr><td>${h.date.slice(0, 10)}</td><td>${h.overall}점</td></tr>`,
    )
    .join("");

  const drills = opts.plan.drills
    .map(
      (d) => `<section>
        <h3>${d.name}</h3>
        <p><strong>세트</strong> ${d.sets}</p>
        <p>${d.how}</p>
        <p><em>감각: ${d.feel}</em></p>
      </section>`,
    )
    .join("");

  return `<!doctype html>
<html lang="ko">
<meta charset="utf-8"/>
<title>Briq Swing 교정 자료 — ${opts.date.slice(0, 10)}</title>
<style>
  body { font-family: "Pretendard", system-ui, sans-serif; max-width: 720px; margin: 40px auto; color: #102018; }
  h1 { font-size: 1.4rem; }
  .meta { color: #4a5c54; }
  table { width: 100%; border-collapse: collapse; margin: 1rem 0 2rem; }
  td, th { border-bottom: 1px solid #ddd; padding: 8px 4px; text-align: left; }
  section { padding: 12px 0; border-top: 1px solid #eee; }
  @media print { body { margin: 16px; } }
</style>
<body>
  <p class="meta">Briq Swing · 유료 코칭 자료</p>
  <h1>${opts.memberName} 님의 ${opts.proName} 교정 플랜</h1>
  <p>작성일 ${opts.date.slice(0, 10)} · 최근 유사도 <strong>${opts.overall}점</strong></p>
  <p>${opts.plan.why}</p>
  <h2>오늘 드릴</h2>
  ${drills}
  <h2>최근 점수</h2>
  <table>
    <thead><tr><th>날짜</th><th>유사도</th></tr></thead>
    <tbody>${rows || "<tr><td colspan='2'>아직 기록이 없습니다</td></tr>"}</tbody>
  </table>
  <p class="meta">${opts.plan.checkpoint}</p>
  <p class="meta">영상은 기기에서만 분석됩니다. 이 자료만 저장·공유하세요.</p>
</body>
</html>`;
}
