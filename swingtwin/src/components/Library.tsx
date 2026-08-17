"use client";

import Link from "next/link";
import { PROS, getPro } from "@/lib/pros";
import { useTwinStore } from "@/lib/store";

export function Library() {
  const preferredProId = useTwinStore((s) => s.preferredProId);
  const setPreferredPro = useTwinStore((s) => s.setPreferredPro);

  return (
    <div className="twin-page">
      <header className="twin-page__head">
        <p className="twin-kicker">Players</p>
        <h1>Who are you copying?</h1>
        <p>
          Label the clip so the daily plan uses that player’s feel. The comparison
          still runs on the video you upload, not a stock animation.
        </p>
      </header>
      <div className="twin-pro-list">
        {PROS.map((p) => (
          <article key={p.id} className={p.id === preferredProId ? "is-on" : ""}>
            <p>
              {p.tour} · {p.role}
            </p>
            <h2>{p.name}</h2>
            <p>{p.signature}</p>
            <p>{p.whyMatch}</p>
            <div className="twin-hero__cta">
              <button
                type="button"
                className="twin-btn twin-btn--small"
                onClick={() => setPreferredPro(p.id)}
              >
                {p.id === preferredProId ? "Selected" : "Use this player"}
              </button>
              {p.instagram ? (
                <a href={p.instagram} target="_blank" rel="noreferrer">
                  @purego1f
                </a>
              ) : null}
            </div>
          </article>
        ))}
      </div>
      <p className="twin-note">
        Selected: <strong>{getPro(preferredProId)?.name}</strong> ·{" "}
        <Link href="/compare">Compare</Link>
      </p>
    </div>
  );
}
