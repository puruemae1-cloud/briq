"use client";

import Link from "next/link";
import { PROS } from "@/lib/pros";
import { useTwinStore } from "@/lib/store";

export function Landing() {
  const trialUsed = useTwinStore((s) => s.trialUsed);
  const tier = useTwinStore((s) => s.tier);

  return (
    <div className="twin-page twin-landing">
      <section className="twin-hero">
        <p className="twin-kicker">Made for golfers in the UK</p>
        <h1>
          Put your swing next to the PGA player you actually want to look like
        </h1>
        <p>
          Subscribers upload a swing, then the tour clip they are copying. TwinSwing
          plays them together, scores the gaps, and gives a daily fix. Face-on plus
          down-the-line becomes 3D.
        </p>
        <div className="twin-hero__cta">
          <Link href="/compare" className="twin-btn">
            {trialUsed && tier !== "subscriber" ? "Open last compare" : "Free trial"}
          </Link>
          <Link href="/subscribe" className="twin-btn twin-btn--ghost">
            Subscribe — £12.99/mo
          </Link>
        </div>
      </section>
      <ol className="twin-steps">
        <li>
          <span>01</span>
          <h2>Your video</h2>
          <p>Phone on a tripod. Face-on is enough. Add behind-the-ball for 3D.</p>
        </li>
        <li>
          <span>02</span>
          <h2>Their video</h2>
          <p>
            Save a slow-mo of Rory, Scheffler, or whoever you are copying — including
            clips from archives such as @purego1f — and upload it.
          </p>
        </li>
        <li>
          <span>03</span>
          <h2>The gap</h2>
          <p>Trial: three differences. Subscribers: daily drills and a progress score.</p>
        </li>
      </ol>
      <section>
        <h2>Players on file</h2>
        <p className="twin-note">
          Models help when you have not got a clip yet. The real product is your
          upload versus their upload.
        </p>
        <div className="twin-pro-grid">
          {PROS.filter((p) => p.id !== "custom-clip").map((p) => (
            <article key={p.id}>
              <p>
                {p.tour}
                {p.country ? ` · ${p.country}` : ""}
              </p>
              <h3>{p.name}</h3>
              <p>{p.signature}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
