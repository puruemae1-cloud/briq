import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { IG_SOURCES, PROS, getPro, searchPros } from "@/lib/players";
import { useTwinStore } from "@/lib/store";

export function Library() {
  const preferredProId = useTwinStore((s) => s.preferredProId);
  const setPreferredPro = useTwinStore((s) => s.setPreferredPro);
  const [q, setQ] = useState("");
  const [source, setSource] = useState("all");

  const list = useMemo(() => {
    const base = searchPros(q);
    if (source === "all") return base;
    return base.filter((p) => p.sources?.includes(source));
  }, [q, source]);

  return (
    <div className="twin-page">
      <header className="twin-page__head">
        <p className="twin-kicker">Players</p>
        <h1>Every PGA name on file</h1>
        <p>
          {PROS.filter((p) => p.tour === "PGA Tour").length} tour players, plus a
          tour-blend model. Learned from the public slow-mo patterns on{" "}
          {IG_SOURCES.filter((s) => s.id !== "purego1f")
            .map((s) => s.handle)
            .join(", ")}
          . Pick a name, then compare — Instagram is not scraped live.
        </p>
      </header>
      <div className="twin-picker">
        <label>
          Search
          <input
            type="search"
            placeholder="Name, country, or role…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </label>
        <label>
          Archive
          <select value={source} onChange={(e) => setSource(e.target.value)}>
            <option value="all">All five Instagram archives</option>
            {IG_SOURCES.filter((s) => s.id !== "purego1f").map((s) => (
              <option key={s.id} value={s.id}>
                {s.handle}
              </option>
            ))}
          </select>
        </label>
      </div>
      <p className="twin-note">
        {list.length} names · selected{" "}
        <strong>{getPro(preferredProId)?.name}</strong> ·{" "}
        <Link to="/compare">Compare</Link>
      </p>
      <div className="twin-pro-list">
        {list.map((p) => (
          <article key={p.id} className={p.id === preferredProId ? "is-on" : ""}>
            <p>
              {p.tour} · {p.role}
              {p.country ? ` · ${p.country}` : ""}
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
                  Open archive
                </a>
              ) : null}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
