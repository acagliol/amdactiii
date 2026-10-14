import { STATION_HREF } from "../../hooks/useHashRoute";
import { LogoMark, Wordmark } from "../Logo";
import { HeroIllustration } from "./HeroIllustration";
import {
  AmdSection,
  ChecklistSection,
  HonestSection,
  HowItWorksSection,
  ProblemSection,
  StatusSection,
} from "./Sections";
import "./landing.css";

const INDUSTRIES = ["Electronics assembly", "Appliances", "Kitting & pack-out", "Repair & refurbishment"];

function scrollToSection(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

/** Product page for customers: what Multilönd does, how, what's built, and a link to the live station. */
export function Landing() {
  return (
    <div className="landing">
      <nav className="lp-nav">
        <a className="header-brand" href="#/">
          <LogoMark size={30} />
          <Wordmark />
        </a>
        <div className="lp-nav-links">
          <button className="lp-link" onClick={() => scrollToSection("how")}>
            How it works
          </button>
          <button className="lp-link" onClick={() => scrollToSection("amd")}>
            AMD
          </button>
          <a className="button button-primary" href={STATION_HREF}>
            Open the station
          </a>
        </div>
      </nav>

      <header className="hero">
        <div className="hero-copy">
          <p className="lp-kicker">Assembly verification for hand-built products</p>
          <h1>Catch mistakes before the next step covers them.</h1>
          <p className="lp-lead">
            Multilönd checks each critical step with a single camera. An open vision model compares the photo with
            your checklist, points at the exact problem, and keeps the cover from going on until the work underneath
            is right. Every unit gets photo proof.
          </p>
          <div className="hero-actions">
            <a className="button button-primary button-large" href={STATION_HREF}>
              Try the live station
            </a>
            <button className="button button-ghost button-large" onClick={() => scrollToSection("how")}>
              How it works
            </button>
          </div>
          <ul className="industries" aria-label="Who it's for">
            {INDUSTRIES.map((industry) => (
              <li key={industry}>{industry}</li>
            ))}
          </ul>
        </div>
        <HeroIllustration />
      </header>

      <ProblemSection />
      <HowItWorksSection />
      <HonestSection />
      <ChecklistSection />
      <AmdSection />
      <StatusSection />

      <section className="lp-cta">
        <LogoMark size={64} />
        <h2 className="lp-title">See it catch a mistake.</h2>
        <p className="lp-lead">Open the worker station, show it a box with something missing, and watch the lid stay locked.</p>
        <a className="button button-primary button-large" href={STATION_HREF}>
          Open the worker station
        </a>
      </section>

      <footer className="lp-footer">
        <span className="header-brand">
          <LogoMark size={22} />
          <Wordmark />
        </span>
        <span className="muted">Prototype built for the AMD Developer Hackathon: ACT III · Intelligent Industry</span>
      </footer>
    </div>
  );
}
