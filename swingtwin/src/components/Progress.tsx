"use client";

import Link from "next/link";
import { buildDailyPlan, buildMaterialHtml } from "@/lib/coaching";
import { getPro } from "@/lib/pros";
import { todayKey, useTwinStore } from "@/lib/store";
import { METRIC_LABEL } from "@/lib/types";

function download(filename: string, html: string) {
  const blob = new Blob([html], { type: "text/html;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function Progress() {
  const tier = useTwinStore((s) => s.tier);
  const sessions = useTwinStore((s) => s.sessions);
  const lastResult = useTwinStore((s) => s.lastResult);
  const pro = getPro(lastResult?.proId ?? "custom-clip");

  if (tier !== "subscriber") {
    return (
      <div className="twin-page">
        <header className="twin-page__head">
          <p className="twin-kicker">Progress</p>
          <h1>See if the change is sticking</h1>
          <p>Subscribers keep every compare and can export today’s range sheet.</p>
        </header>
        <Link href="/subscribe" className="twin-btn">
          Subscribe
        </Link>
      </div>
    );
  }

  const first = sessions[sessions.length - 1];
  const latest = sessions[0];
  const delta =
    first && latest && sessions.length > 1 ? latest.overall - first.overall : 0;

  function issueSheet() {
    if (!lastResult || !pro) return;
    const plan = buildDailyPlan({
      date: todayKey(),
      focus: lastResult.coachingFocus,
      pro,
      overall: lastResult.overall,
      userValue: lastResult.userMetrics[lastResult.coachingFocus],
      proValue: lastResult.proMetrics[lastResult.coachingFocus],
    });
    download(
      `swingtwin-${todayKey()}.html`,
      buildMaterialHtml({
        memberName: "Subscriber",
        proName: pro.name,
        date: lastResult.createdAt,
        overall: lastResult.overall,
        plan,
        history: sessions.map((s) => ({ date: s.createdAt, overall: s.overall })),
      }),
    );
  }

  return (
    <div className="twin-page">
      <header className="twin-page__head">
        <p className="twin-kicker">Progress</p>
        <h1>Is the swing moving toward their clip?</h1>
        <p>
          {sessions.length
            ? `${sessions.length} compares · ${delta >= 0 ? "+" : ""}${delta} from first to last`
            : "No subscriber sessions yet."}
        </p>
      </header>
      {sessions.length > 1 ? (
        <div className="twin-chart" aria-hidden>
          {sessions
            .slice()
            .reverse()
            .map((s) => (
              <div key={s.id} className="twin-chart__col">
                <div
                  className="twin-chart__bar"
                  style={{ height: `${Math.max(8, s.overall)}%` }}
                />
                <span>{s.overall}</span>
              </div>
            ))}
        </div>
      ) : null}
      <ul className="twin-sessions">
        {sessions.map((s) => (
          <li key={s.id}>
            <strong>{s.createdAt.slice(0, 10)}</strong>
            <span>{s.overall} match</span>
            <span>{s.proName}</span>
            <span>
              {METRIC_LABEL[s.coachingFocus]}
              {s.comparedAgainstClip ? " · clip" : ""}
              {s.has3d ? " · 3D" : ""}
            </span>
            <p>{s.note}</p>
          </li>
        ))}
      </ul>
      <div className="twin-hero__cta">
        <Link href="/compare" className="twin-btn">
          New compare
        </Link>
        <button type="button" className="twin-btn twin-btn--ghost" onClick={issueSheet} disabled={!lastResult}>
          Download today’s sheet
        </button>
      </div>
    </div>
  );
}
