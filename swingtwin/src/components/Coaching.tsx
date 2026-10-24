import { Link } from "react-router-dom";
import { buildDailyPlan } from "@/lib/coaching";
import { getPro } from "@/lib/pros";
import { todayKey, useTwinStore } from "@/lib/store";
import { METRIC_LABEL, PHASE_LABEL } from "@/lib/types";

export function Coaching() {
  const lastResult = useTwinStore((s) => s.lastResult);
  const pro = getPro(lastResult?.proId ?? "custom-clip");

  if (!lastResult || !pro) {
    return (
      <div className="twin-page">
        <header className="twin-page__head">
          <p className="twin-kicker">Daily</p>
          <h1>Compare a swing first</h1>
        </header>
        <Link to="/compare" className="twin-btn">
          Compare
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
    <div className="twin-page">
      <header className="twin-page__head">
        <p className="twin-kicker">Today · {plan.date}</p>
        <h1>{plan.title}</h1>
        <p>{plan.why}</p>
      </header>
      <p className="twin-focus">
        Focus <strong>{METRIC_LABEL[plan.focus]}</strong>
        {gap ? ` · you ${gap.user} / them ${gap.pro}` : null}
      </p>
      <ol className="twin-drills">
        {plan.drills.map((d) => (
          <li key={d.name}>
            <h2>{d.name}</h2>
            <p className="twin-gaps__drill">{d.sets}</p>
            <p>{d.how}</p>
            <p className="twin-gaps__feel">Feel: {d.feel}</p>
          </li>
        ))}
      </ol>
      <p className="twin-note">{plan.checkpoint}</p>
      {lastResult.phaseNotes.length ? (
        <div className="twin-phases">
          {lastResult.phaseNotes.map((p) => (
            <article key={p.phase}>
              <h3>{PHASE_LABEL[p.phase]}</h3>
              <p>{p.note}</p>
            </article>
          ))}
        </div>
      ) : null}
    </div>
  );
}
