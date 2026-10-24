import { Link } from "react-router-dom";

export function Subscribe() {
  return (
    <div className="twin-page">
      <header className="twin-page__head">
        <p className="twin-kicker">UK subscription</p>
        <h1>Everything is free for now</h1>
        <p>
          Upload as many swings as you like, compare side-by-side, use daily
          coaching, and track progress — no limits on this build. Paid plans
          (£12.99 / month) will come later with Stripe billing.
        </p>
      </header>
      <div className="twin-plans">
        <article className="is-featured">
          <p>TwinSwing</p>
          <h2>Free · unlimited</h2>
          <ul>
            <li>Unlimited uploads of your swing and tour clips</li>
            <li>Side-by-side synced to impact, plus 3D from two cameras</li>
            <li>All 30 phases and body-line differences</li>
            <li>Daily plan, printable range sheet, and score history</li>
          </ul>
          <p className="twin-plans__state">Active on this device</p>
          <Link to="/compare" className="twin-btn">
            Compare a swing
          </Link>
        </article>
      </div>
    </div>
  );
}
