import {
  METRIC_LABEL,
  SWING_PHASES,
  type DailyPlan,
  type MetricKey,
  type ProProfile,
} from "./types";
import { gapCopy } from "./copy";

const WEEK_TITLES = [
  "Sunday — film it slow",
  "Monday — feel only",
  "Tuesday — tempo",
  "Wednesday — full swing",
  "Thursday — ten balls",
  "Friday — pressure",
  "Saturday — film again",
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
  const dayIndex = new Date(date + "T12:00:00").getDay();
  const copy = gapCopy(focus, userValue, proValue);

  return {
    date,
    dayIndex,
    title: WEEK_TITLES[dayIndex],
    focus,
    why: `${METRIC_LABEL[focus]} is still the biggest gap versus ${pro.name}. Match ${overall}. Today’s session only attacks that gap.`,
    drills: [
      {
        name: copy.drill.split(". ")[0] || copy.drill,
        sets: dayIndex === 6 ? "Two takes, both cameras" : "3 sets of 8–12",
        how: copy.drill,
        feel: copy.feel,
      },
      {
        name: `Copy ${pro.name} — ${SWING_PHASES[Math.min(dayIndex, 5)]}`,
        sets: "6 slow / 6 normal",
        how: pro.phaseCues[SWING_PHASES[Math.min(dayIndex, 5)]],
        feel: "Same camera height as the tour clip.",
      },
      {
        name: dayIndex === 6 ? "Re-upload check" : "Three-second finish",
        sets: dayIndex === 6 ? "Face-on and DTL" : "Every swing",
        how:
          dayIndex === 6
            ? "Film both cameras after the drill and compare again to their clip."
            : "Hold the finish for three seconds. If you fall, the downswing was rushed.",
        feel: "Balance left means the sequence held.",
      },
    ],
    checkpoint:
      dayIndex === 6
        ? "Subscribers should re-upload today and check whether the match score moved."
        : `If ${METRIC_LABEL[focus]} is still first tomorrow, repeat — do not add a new move.`,
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
    .map((h) => `<tr><td>${h.date.slice(0, 10)}</td><td>${h.overall}</td></tr>`)
    .join("");
  const drills = opts.plan.drills
    .map(
      (d) => `<section>
        <h3>${d.name}</h3>
        <p><strong>Sets</strong> ${d.sets}</p>
        <p>${d.how}</p>
        <p><em>Feel: ${d.feel}</em></p>
      </section>`,
    )
    .join("");

  return `<!doctype html>
<html lang="en-GB">
<meta charset="utf-8"/>
<title>TwinSwing session — ${opts.date.slice(0, 10)}</title>
<style>
  body { font-family: ui-sans-serif, system-ui, sans-serif; max-width: 720px; margin: 40px auto; color: #102018; }
  h1 { font-size: 1.4rem; }
  .meta { color: #4a5c54; }
  table { width: 100%; border-collapse: collapse; margin: 1rem 0 2rem; }
  td, th { border-bottom: 1px solid #ddd; padding: 8px 4px; text-align: left; }
  section { padding: 12px 0; border-top: 1px solid #eee; }
  @media print { body { margin: 16px; } }
</style>
<body>
  <p class="meta">TwinSwing · United Kingdom</p>
  <h1>${opts.memberName} — matching ${opts.proName}</h1>
  <p>Printed ${opts.date.slice(0, 10)} · last match <strong>${opts.overall}</strong></p>
  <p>${opts.plan.why}</p>
  <h2>Today</h2>
  ${drills}
  <h2>Recent scores</h2>
  <table>
    <thead><tr><th>Date</th><th>Match</th></tr></thead>
    <tbody>${rows || "<tr><td colspan='2'>No sessions yet</td></tr>"}</tbody>
  </table>
  <p class="meta">${opts.plan.checkpoint}</p>
  <p class="meta">Clips stay on your phone. This sheet is the only thing we suggest you share.</p>
</body>
</html>`;
}
