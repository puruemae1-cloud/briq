import { Link } from "react-router-dom";
import { IG_SOURCES, PROS } from "@/lib/players";

const FEATURED = [
  "rory-mcilroy",
  "scottie-scheffler",
  "tiger-woods",
  "tommy-fleetwood",
  "collin-morikawa",
  "jon-rahm",
];

export function Landing() {
  const pgaCount = PROS.filter((p) => p.tour === "PGA Tour").length;
  const featured = FEATURED.map((id) => PROS.find((p) => p.id === id)).filter(Boolean);

  return (
    <div className="twin-page twin-landing">
      <section className="twin-hero">
        <p className="twin-kicker">Made for golfers in the UK</p>
        <h1>
          Put your swing next to any PGA player — 30 phases, 30 body lines
        </h1>
        <p>
          Choose a name from the {pgaCount}-player archive (learned from
          @golf_swings, @pgatour, @golfdigest, @golf_gods and @golfonthesnap),
          upload your clip, and we sync both swings. Gold is the player, mint is
          you. A dashed line marks every joint that is off — head, hands,
          wrists, arms, shoulders, thighs, knees, feet.
        </p>
        <div className="twin-hero__cta">
          <Link to="/compare" className="twin-btn">
            Start comparing — free
          </Link>
        </div>
      </section>
      <ol className="twin-steps">
        <li>
          <span>01</span>
          <h2>Pick the player</h2>
          <p>Search every PGA name on file. Change player any time — the overlay redraws.</p>
        </li>
        <li>
          <span>02</span>
          <h2>Your video + theirs</h2>
          <p>
            Face-on is enough. Add down-the-line for 3D. Optionally upload the
            exact Instagram slow-mo you saved.
          </p>
        </li>
        <li>
          <span>03</span>
          <h2>30 synced phases</h2>
          <p>
            Scrub Setup through Recoil. Each of ~30 body parts gets a gap line
            so the difference is obvious.
          </p>
        </li>
      </ol>
      <section>
        <h2>Learned from these archives</h2>
        <p className="twin-note">
          We do not scrape Instagram. Models are distilled from the public
          face-on / down-the-line patterns those accounts repeat. Upload a saved
          clip for a true clip-vs-clip compare.
        </p>
        <div className="twin-pro-grid">
          {IG_SOURCES.filter((s) => s.id !== "purego1f").map((s) => (
            <article key={s.id}>
              <p>Instagram</p>
              <h3>{s.handle}</h3>
              <p>
                <a href={s.url} target="_blank" rel="noreferrer">
                  {s.url.replace("https://", "")}
                </a>
              </p>
            </article>
          ))}
        </div>
      </section>
      <section>
        <h2>Players on file</h2>
        <p className="twin-note">
          {pgaCount} PGA names are selectable. A few to start —{" "}
          <Link to="/library">see the full list</Link>.
        </p>
        <div className="twin-pro-grid">
          {featured.map((p) =>
            p ? (
              <article key={p.id}>
                <p>
                  {p.tour}
                  {p.country ? ` · ${p.country}` : ""}
                </p>
                <h3>{p.name}</h3>
                <p>{p.signature}</p>
              </article>
            ) : null,
          )}
        </div>
      </section>
    </div>
  );
}
