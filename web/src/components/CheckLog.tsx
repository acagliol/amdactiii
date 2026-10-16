import { ACTION_LABEL, readableId } from "../format";
import type { Action } from "../types";

export interface LogEntry {
  id: number;
  at: string; // video time ("0:12") or clock time
  checkId: string;
  action: Action;
  reason: string;
}

/** Every check of this unit, newest first: a timeline when analysing a recorded video. */
export function CheckLog({ entries }: { entries: LogEntry[] }) {
  if (entries.length === 0) return null;
  return (
    <section className="check-log" aria-label="Checks so far">
      <h2 className="panel-title">Checks so far</h2>
      <ol>
        {entries.map((entry) => (
          <li key={entry.id}>
            <span className="mono muted">{entry.at}</span>
            <span className={`badge badge-small badge-${entry.action}`}>{ACTION_LABEL[entry.action]}</span>
            <span className="check-log-step">{readableId(entry.checkId)}</span>
            <span className="muted check-log-reason">{entry.reason}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}
