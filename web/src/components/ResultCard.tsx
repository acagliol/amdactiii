import type { CheckResult } from "../types";
import { ACTION_LABEL } from "../format";
import { LogoMark } from "./Logo";

interface ResultCardProps {
  result: CheckResult;
  onRetake: () => void;
  onContinue: () => void;
  onOverride: () => void;
}

/** The verdict after a photo check: badge, the AI's reason, a hint, and what to do next. */
export function ResultCard({ result, onRetake, onContinue, onOverride }: ResultCardProps) {
  const passed = result.action === "pass";
  return (
    <section className={`result result-${result.action}`} aria-live="polite">
      <div className="result-head">
        <LogoMark size={44} state={result.action} />
        <span className={`badge badge-${result.action}`}>{ACTION_LABEL[result.action]}</span>
      </div>

      <p className="result-reason">{result.reason}</p>
      {result.hint && !passed && <p className="result-hint">{result.hint}</p>}
      {result.action === "supervisor" && (
        <p className="result-hint">Three retakes in a row. Ask a supervisor to look, or override with a written reason.</p>
      )}

      <div className="result-actions">
        {passed ? (
          <button className="button button-primary" onClick={onContinue}>
            Next step →
          </button>
        ) : (
          <>
            <button className="button button-primary" onClick={onRetake}>
              {result.action === "fix" ? "Fixed it, check again" : "Take another photo"}
            </button>
            <button className="button button-ghost" onClick={onOverride}>
              Override…
            </button>
          </>
        )}
      </div>
    </section>
  );
}
