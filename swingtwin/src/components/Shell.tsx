import { Link, useLocation } from "react-router-dom";
import { useTwinStore } from "@/lib/store";

const links = [
  { href: "/", label: "Home", exact: true },
  { href: "/compare", label: "Compare" },
  { href: "/library", label: "Players" },
  { href: "/coaching", label: "Daily" },
  { href: "/progress", label: "Progress" },
  { href: "/subscribe", label: "Subscribe" },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = useLocation().pathname;
  const tier = useTwinStore((s) => s.tier);

  return (
    <div className="twin-root">
      <header className="twin-top">
        <Link to="/" className="twin-logo">
          TwinSwing
          <em>UK</em>
        </Link>
        <nav aria-label="App">
          {links.map((l) => {
            const active = l.exact
              ? pathname === l.href
              : pathname === l.href || pathname.startsWith(`${l.href}/`);
            return (
              <Link key={l.href} to={l.href} className={active ? "is-active" : undefined}>
                {l.label}
              </Link>
            );
          })}
        </nav>
        <span className={`twin-pill ${tier === "subscriber" ? "is-on" : ""}`}>
          {tier === "subscriber" ? "Subscriber" : "Trial"}
        </span>
      </header>
      {children}
      <footer className="twin-page" style={{ paddingTop: 0 }}>
        <p className="twin-note">
          TwinSwing · United Kingdom · independent of any shop ·{" "}
          <Link to="/privacy">Privacy</Link>
        </p>
      </footer>
    </div>
  );
}
