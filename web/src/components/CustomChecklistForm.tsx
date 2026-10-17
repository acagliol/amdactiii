import { useState } from "react";
import type { CustomChecklist } from "../types";

// Same limits as the server (api/custom_checklist.py).
const MAX_CHECKS = 6;
const MAX_LINE_LENGTH = 160;

const PLACEHOLDER = ["Both earbuds are inside the case", "The charging cable is plugged into the case"].join("\n");

interface CustomChecklistFormProps {
  busy: boolean;
  onStart: (spec: CustomChecklist) => void;
}

/** "Your own": anyone can test with anything by writing what correct looks like, one check per line. */
export function CustomChecklistForm({ busy, onStart }: CustomChecklistFormProps) {
  const [name, setName] = useState("");
  const [text, setText] = useState("");
  const [hasCoverStep, setHasCoverStep] = useState(true);
  const [coverStep, setCoverStep] = useState("Close the lid");

  const checks = text.split("\n").map((line) => line.trim()).filter(Boolean);
  const problem = validate(checks, hasCoverStep ? coverStep : "");

  return (
    <form
      className="start-option"
      onSubmit={(event) => {
        event.preventDefault();
        if (!problem) onStart({ name, checks, coverStep: hasCoverStep ? coverStep.trim() : null });
      }}
    >
      <div>
        <h2 className="option-title">Your own</h2>
        <p className="muted option-text">Test with anything. Write what <strong>correct</strong> looks like, one check per line.</p>
      </div>

      <label className="field">
        <span>Name (optional)</span>
        <input value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Earbuds case" maxLength={60} />
      </label>

      <label className="field">
        <span>
          Checks <span className="muted">· {checks.length} of {MAX_CHECKS}</span>
        </span>
        <textarea value={text} onChange={(event) => setText(event.target.value)} placeholder={PLACEHOLDER} rows={4} />
      </label>

      <div className="cover-step">
        <label className="auto-toggle">
          <input type="checkbox" checked={hasCoverStep} onChange={(event) => setHasCoverStep(event.target.checked)} />
          Last step covers earlier work 🔒
        </label>
        {hasCoverStep && (
          <input
            className="cover-input"
            value={coverStep}
            onChange={(event) => setCoverStep(event.target.value)}
            maxLength={80}
            aria-label="Last step"
          />
        )}
        <p className="muted option-hint">It stays locked until every check above passes.</p>
      </div>

      {problem && checks.length > 0 && <p className="error">{problem}</p>}
      <button className="button button-primary button-large" type="submit" disabled={busy || Boolean(problem)}>
        Start my check
      </button>
    </form>
  );
}

function validate(checks: string[], coverStep: string): string | null {
  if (checks.length === 0) return "Write at least one check.";
  if (checks.length > MAX_CHECKS) return `Use at most ${MAX_CHECKS} checks.`;
  if (checks.some((line) => line.length > MAX_LINE_LENGTH)) return `Keep each check under ${MAX_LINE_LENGTH} characters.`;
  if (checks.some((line) => line.length < 3)) return "Each check needs a few words.";
  if (coverStep.trim().length > 80) return "Keep the last step short.";
  return null;
}
