import { Link } from "react-router-dom";
import { useTwinStore } from "@/lib/store";

export function Subscribe() {
  const tier = useTwinStore((s) => s.tier);
  const trialUsed = useTwinStore((s) => s.trialUsed);
  const activateSubscriber = useTwinStore((s) => s.activateSubscriber);

  return (
    <div className="twin-page">
      <header className="twin-page__head">
        <p className="twin-kicker">UK subscription</p>
        <h1>Trial is a peek. Subscribers keep filming.</h1>
        <p>
          Card billing (Stripe, GBP) is the production next step. This build stores
          membership on the device so you can walk the product.
        </p>
      </header>
      <div className="twin-plans">
        <article>
          <p>Trial</p>
          <h2>Free · one compare</h2>
          <ul>
            <li>One pair of videos</li>
            <li>Three differences versus their clip</li>
            <li>One drill for each</li>
          </ul>
          <p className="twin-plans__state">{trialUsed ? "Used on this phone" : "Still available"}</p>
          <Link to="/compare" className="twin-btn twin-btn--ghost">
            Compare
          </Link>
        </article>
        <article className="is-featured">
          <p>TwinSwing+</p>
          <h2>£12.99 / month</h2>
          <p className="twin-note">or £99 / year · cancel anytime · App Store / Play when we ship native</p>
          <ul>
            <li>Unlimited uploads of your swing and their swing</li>
            <li>Side-by-side synced to impact, plus 3D from two cameras</li>
            <li>Daily plan and printable range sheet</li>
            <li>Score history — did the change stick?</li>
          </ul>
          {tier === "subscriber" ? (
            <p className="twin-plans__state">Subscriber is on for this device</p>
          ) : (
            <button type="button" className="twin-btn" onClick={activateSubscriber}>
              Turn on subscriber (demo)
            </button>
          )}
        </article>
      </div>
    </div>
  );
}
