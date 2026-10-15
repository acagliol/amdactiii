import type { Step } from "../types";
import { readableId } from "../format";

const STATUS_ICON: Record<Step["status"], string> = {
  done: "✓",
  overridden: "⚑",
  current: "●",
  upcoming: "○",
};

/** Every check of the unit in order. Steps that hide earlier work show what they wait for. */
export function StepList({ steps }: { steps: Step[] }) {
  const finished = new Set(steps.filter((step) => step.status === "done" || step.status === "overridden").map((s) => s.check_id));

  return (
    <nav className="steps" aria-label="Assembly steps">
      <h2 className="panel-title">Steps</h2>
      <ol>
        {steps.map((step) => {
          const waitingFor = step.requires.filter((id) => !finished.has(id));
          const locked = step.status === "upcoming" && step.hides && waitingFor.length > 0;
          return (
            <li key={step.check_id} className={`step step-${step.status}`}>
              <span className="step-icon" aria-hidden="true">
                {locked ? "🔒" : STATUS_ICON[step.status]}
              </span>
              <div className="step-text">
                <span className="step-name">{readableId(step.check_id)}</span>
                <span className="step-meta">
                  {step.kind === "manual" && "Confirm by hand"}
                  {step.kind === "gate" && "Covers earlier work"}
                  {step.kind === "visual" && (step.hides ? "Photo check · covers earlier work" : "Photo check")}
                  {step.status === "overridden" && " · overridden"}
                </span>
                {locked && <span className="step-lock">Locked until: {waitingFor.map(readableId).join(", ")}</span>}
              </div>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
