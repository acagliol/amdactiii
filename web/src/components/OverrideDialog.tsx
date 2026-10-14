import { useState } from "react";

const MIN_REASON_LENGTH = 8; // same rule as the checker (Session.override_pass)

interface OverrideDialogProps {
  busy: boolean;
  onSubmit: (reason: string) => void;
  onCancel: () => void;
}

/** Accept a step despite the AI, with a written reason that goes into the evidence log. */
export function OverrideDialog({ busy, onSubmit, onCancel }: OverrideDialogProps) {
  const [reason, setReason] = useState("");
  const tooShort = reason.trim().length < MIN_REASON_LENGTH;

  return (
    <div className="dialog-backdrop" role="dialog" aria-modal="true" aria-labelledby="override-title">
      <form
        className="dialog"
        onSubmit={(event) => {
          event.preventDefault();
          if (!tooShort) onSubmit(reason.trim());
        }}
      >
        <h2 id="override-title">Override this check</h2>
        <p className="muted">Use only if the AI is clearly wrong. Your reason is saved with this unit.</p>
        <textarea
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          placeholder="e.g. Verified by hand: all four items are in the box"
          rows={3}
          autoFocus
        />
        <div className="result-actions">
          <button className="button button-primary" type="submit" disabled={busy || tooShort}>
            Accept override
          </button>
          <button className="button button-ghost" type="button" onClick={onCancel}>
            Cancel
          </button>
        </div>
        {tooShort && reason.length > 0 && <p className="muted">At least {MIN_REASON_LENGTH} characters.</p>}
      </form>
    </div>
  );
}
