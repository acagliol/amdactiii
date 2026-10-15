// Product-page sections. Wording rule: describe what is built as built, and put
// anything not built yet under "Next". No invented numbers.

const COST_TIERS = [
  { where: "At the workstation", detail: "Still visible: reseat the clip, add the part.", factor: 1 },
  { where: "At final test", detail: "Open the unit back up, find it, fix it, retest.", factor: 10 },
  { where: "At the customer", detail: "Repair visit, warranty, reputation, maybe a recall.", factor: 100 },
];

export function ProblemSection() {
  return (
    <section className="lp-section" id="problem">
      <p className="lp-kicker">The problem</p>
      <h2 className="lp-title">The expensive mistakes are the ones you can&apos;t see anymore.</h2>
      <p className="lp-lead">
        A connector that&apos;s only half in. A missing clip. A charger left out of the box. Each takes a second
        to make and a second to fix, until the next step hides it. Then it shows up at final test, or at the
        customer.
      </p>
      <div className="cost-tiers">
        {COST_TIERS.map((tier) => (
          <div className="cost-tier" key={tier.factor}>
            <div className="cost-head">
              <span className="cost-factor">{tier.factor}×</span>
              <span className="cost-where">{tier.where}</span>
            </div>
            <div className="cost-bar">
              <div className="cost-fill" style={{ width: `${tier.factor}%` }} />
            </div>
            <p className="muted">{tier.detail}</p>
          </div>
        ))}
      </div>
      <p className="lp-footnote">The 1–10–100 rule of thumb from quality management. Multilönd works at the cheapest point.</p>
    </section>
  );
}

const STEPS = [
  {
    title: "Describe what correct looks like",
    text: "Each check is one visible yes/no question plus a photo of the correct state. A new product means a new checklist, not a new machine.",
  },
  {
    title: "Check at the right moment",
    text: "Before a step hides earlier work, the worker shows it to the camera. Blurry, dark or glary photos are rejected before any AI runs.",
  },
  {
    title: "The model looks. Rules decide.",
    text: "An open vision model answers yes, no, or can't tell, and marks where the problem is. Fixed rules, not the model, decide what happens next.",
  },
  {
    title: "Unlock, or fix it",
    text: "Pass unlocks the next step. Fix it puts a red box on the mistake. The step that would cover it stays locked until it's right.",
  },
];

export function HowItWorksSection() {
  return (
    <section className="lp-section" id="how">
      <p className="lp-kicker">How it works</p>
      <h2 className="lp-title">One camera, a checklist, and a lock on the steps that hide things.</h2>
      <ol className="how-steps">
        {STEPS.map((step, index) => (
          <li key={step.title} className="how-step">
            <span className="how-number">{String(index + 1).padStart(2, "0")}</span>
            <h3>{step.title}</h3>
            <p className="muted">{step.text}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}

const HONEST_POINTS = [
  { title: "Says “can't tell” instead of guessing", text: "If the photo doesn't show enough, it asks for another angle." },
  { title: "Knows what a photo can't prove", text: "A camera can't feel a screw's tightness, so those steps are confirmed by hand." },
  { title: "Overrides need a reason", text: "A person can overrule the AI, but only with a written reason that stays with the unit." },
  { title: "Frames the work, not the worker", text: "The camera points at the bench, not at faces. The data is for coaching, not policing." },
];

export function HonestSection() {
  return (
    <section className="lp-section" id="honest">
      <p className="lp-kicker">Honest by design</p>
      <h2 className="lp-title">Built to be trusted on the line.</h2>
      <div className="honest-grid">
        {HONEST_POINTS.map((point) => (
          <div className="honest-card" key={point.title}>
            <h3>{point.title}</h3>
            <p className="muted">{point.text}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

const CHECKLIST_EXAMPLE = `assembly: "Accessory box pack-out"
steps:
  - id: "pack_base"
    instruction: "Put the charger and cable in the box."
    checks:
      - id: "charger_and_cable"
        type: "visual"
        question: "A correct box has a black charger
          and a white USB cable. Are both in it?"

  - id: "close_lid"
    instruction: "Close the lid."
    # locked until the check above passes
    requires: ["charger_and_cable"]`;

export function ChecklistSection() {
  return (
    <section className="lp-section lp-split" id="checklist">
      <div>
        <p className="lp-kicker">Set up a product</p>
        <h2 className="lp-title">A new product is a text file.</h2>
        <p className="lp-lead">
          The engine knows nothing about chargers or connectors. Each product is a short checklist: the steps,
          the question for each check, and which steps stay locked until others pass.
        </p>
        <p className="muted">
          Questions work best when they describe the correct state. In our own tests, a vague “is it free of
          defects?” missed a swapped wire. Describing the correct wire colours caught it, and boxed it.
        </p>
      </div>
      <pre className="code-card" aria-label="Example checklist file">
        <code>{CHECKLIST_EXAMPLE}</code>
      </pre>
    </section>
  );
}

export function AmdSection() {
  return (
    <section className="lp-section lp-amd" id="amd">
      <p className="lp-kicker">Runs on AMD</p>
      <h2 className="lp-title">An open model, on AMD GPUs.</h2>
      <div className="amd-grid">
        <div>
          <h3>In this prototype</h3>
          <p className="muted">
            Every inspection runs on Gemma 4, Google&apos;s open vision model, served on AMD GPUs through AMD&apos;s
            Token Factory.
          </p>
        </div>
        <div>
          <h3>Why it matters for a factory</h3>
          <p className="muted">
            Because the model is open, it can run on a factory&apos;s own AMD GPU. Photos of unreleased products
            would never have to leave the site, and cost is the factory&apos;s own GPU time, not a fee per image.
          </p>
        </div>
      </div>
    </section>
  );
}

const AVAILABLE_NOW = [
  "Worker station: live camera, check, red box on the mistake",
  "Locked steps until the work underneath passes",
  "Manual checks and overrides with a written reason",
  "Photo proof for every attempt, per unit serial",
  "Checklists as simple text files",
];

const NEXT = [
  "Manager dashboard: mistakes by step and shift",
  "Weekly summary for plant management",
  "Write checklists in plain English",
  "On-site deployment on the factory's own AMD GPU",
];

export function StatusSection() {
  return (
    <section className="lp-section" id="status">
      <p className="lp-kicker">Where it stands</p>
      <h2 className="lp-title">A working prototype, with a clear next step.</h2>
      <div className="status-grid">
        <div className="status-card">
          <h3>
            <span className="status-dot status-now" /> Available now
          </h3>
          <ul>
            {AVAILABLE_NOW.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
        <div className="status-card">
          <h3>
            <span className="status-dot status-next" /> Next
          </h3>
          <ul>
            {NEXT.map((item) => (
              <li key={item} className="muted">
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
