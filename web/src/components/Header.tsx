import { LANDING_HREF } from "../hooks/useHashRoute";
import type { Health, UnitState } from "../types";
import { LogoMark, Wordmark } from "./Logo";

interface HeaderProps {
  health: Health | null;
  unit: UnitState | null;
}

export function Header({ health, unit }: HeaderProps) {
  return (
    <header className="header">
      <a className="header-brand" href={LANDING_HREF} title="About Multilönd">
        <LogoMark size={30} />
        <Wordmark />
      </a>

      {unit && (
        <div className="header-unit">
          <span className="header-assembly">{unit.assembly}</span>
          <ProgressBar done={unit.done} total={unit.total} />
        </div>
      )}

      <div className="header-right">
        {unit && <span className="chip chip-mono">Unit {unit.unit_id.slice(0, 12)}</span>}
        <AiBadge health={health} />
      </div>
    </header>
  );
}

function ProgressBar({ done, total }: { done: number; total: number }) {
  const percent = total ? Math.round((done / total) * 100) : 100;
  return (
    <div className="progress" aria-label={`${done} of ${total} checks done`}>
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${percent}%` }} />
      </div>
      <span className="progress-text">
        {done} / {total}
      </span>
    </div>
  );
}

function AiBadge({ health }: { health: Health | null }) {
  if (!health) return <span className="chip">Connecting…</span>;
  if (health.ai === "fake") return <span className="chip chip-warn">Demo AI (offline)</span>;
  return (
    <span className="chip chip-live">
      <span className="live-dot" /> {health.model ?? "AI"} · AMD
    </span>
  );
}
