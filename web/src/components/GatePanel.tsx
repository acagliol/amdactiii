import type { CurrentCheck } from "../types";
import { readableId } from "../format";

interface GatePanelProps {
  check: CurrentCheck;
  busy: boolean;
  onConfirm: () => void;
}

/** A step that covers earlier work (close the lid / panel). It only unlocks once its checks passed. */
export function GatePanel({ check, busy, onConfirm }: GatePanelProps) {
  const { blocked, missing } = check.gate;
  return (
    <section className={`action-panel gate ${blocked ? "gate-locked" : "gate-open"}`}>
      <span className="gate-icon" aria-hidden="true">
        {blocked ? "🔒" : "🔓"}
      </span>
      <span className="action-kicker">This step hides earlier work</span>
      <h2 className="action-title">{check.instruction}</h2>

      <ul className="gate-list">
        {check.requires.map((id) => (
          <li key={id} className={missing.includes(id) ? "gate-missing" : "gate-ok"}>
            {missing.includes(id) ? "✗" : "✓"} {readableId(id)}
          </li>
        ))}
      </ul>

      {blocked ? (
        <p className="error">Locked: these checks must pass before this step.</p>
      ) : (
        <p className="muted">Everything this step will cover has been verified and photographed.</p>
      )}

      <button className="button button-primary button-large" disabled={busy || blocked} onClick={onConfirm}>
        Step done
      </button>
    </section>
  );
}
