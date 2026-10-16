import { useState } from "react";
import type { CurrentCheck } from "../types";

interface ManualPanelProps {
  check: CurrentCheck;
  busy: boolean;
  onConfirm: (ok: boolean, note: string) => void;
}

/** A check a photo cannot prove (e.g. tape holds, screw is tight): the worker confirms by hand. */
export function ManualPanel({ check, busy, onConfirm }: ManualPanelProps) {
  const [reportingProblem, setReportingProblem] = useState(false);
  const [note, setNote] = useState("");

  return (
    <section className="action-panel">
      <span className="action-kicker">Confirm by hand</span>
      <h2 className="action-title">{check.question}</h2>
      <p className="muted">A photo can&apos;t prove this, so the worker confirms it by hand.</p>

      {!reportingProblem ? (
        <div className="result-actions">
          <button className="button button-pass button-large" disabled={busy} onClick={() => onConfirm(true, "")}>
            ✓ Confirmed
          </button>
          <button className="button button-ghost" disabled={busy} onClick={() => setReportingProblem(true)}>
            ✗ There&apos;s a problem
          </button>
        </div>
      ) : (
        <form
          className="note-form"
          onSubmit={(event) => {
            event.preventDefault();
            onConfirm(false, note);
          }}
        >
          <label className="field">
            <span>What&apos;s wrong?</span>
            <input value={note} onChange={(event) => setNote(event.target.value)} placeholder="e.g. tape peels off at the corner" autoFocus />
          </label>
          <div className="result-actions">
            <button className="button button-fix" type="submit" disabled={busy || note.trim().length < 3}>
              Report problem
            </button>
            <button className="button button-ghost" type="button" onClick={() => setReportingProblem(false)}>
              Cancel
            </button>
          </div>
        </form>
      )}
    </section>
  );
}
