import type { CurrentCheck } from "../types";

/** The instruction, the yes/no question, and (if there is one) a photo of what correct looks like. */
export function ReferencePanel({ check }: { check: CurrentCheck }) {
  return (
    <aside className="reference">
      <h2 className="panel-title">This step</h2>
      <p className="instruction">{check.instruction}</p>

      {check.kind !== "gate" && (
        <div className="question">
          <span className="question-label">{check.kind === "manual" ? "Confirm by hand" : "The AI checks"}</span>
          <p>{check.question}</p>
        </div>
      )}

      {check.reference_url ? (
        <figure className="reference-photo">
          <img src={check.reference_url} alt="What correct looks like" />
          <figcaption>What correct looks like</figcaption>
        </figure>
      ) : (
        check.kind === "visual" && <p className="muted">No reference photo for this check yet.</p>
      )}

      {check.show && <p className="camera-hint">📷 {check.show}</p>}
    </aside>
  );
}
