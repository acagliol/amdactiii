import { useEffect, useState } from "react";
import { api } from "../api";
import { ACTION_LABEL, errorMessage, formatTime, readableId } from "../format";
import type { EvidenceResponse, UnitState } from "../types";
import { LogoMark } from "./Logo";
import { PhotoWithBox } from "./PhotoWithBox";

interface CompleteScreenProps {
  unit: UnitState;
  onNextUnit: () => void;
}

/** End of a unit: what was verified, what was caught, and the photo proof (the audit trail). */
export function CompleteScreen({ unit, onNextUnit }: CompleteScreenProps) {
  const [evidence, setEvidence] = useState<EvidenceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.evidence(unit.unit_id).then(setEvidence).catch((e) => setError(errorMessage(e)));
  }, [unit.unit_id]);

  const caught = evidence?.summary.actions.fix ?? 0;
  const withPhotos = evidence?.items.filter((item) => item.photo_url) ?? [];

  return (
    <main className="complete">
      <section className="complete-hero">
        <LogoMark size={88} state="pass" />
        <h1>Unit complete</h1>
        <p className="muted">
          {unit.assembly} · unit <span className="mono">{unit.unit_id}</span>
        </p>
        <div className="stats">
          <Stat value={unit.total} label="steps verified" />
          <Stat value={caught} label={caught === 1 ? "mistake caught" : "mistakes caught"} />
          <Stat value={unit.overrides.length} label="overrides" />
          <Stat value={evidence?.summary.attempts ?? 0} label="logged attempts" />
        </div>
        <button className="button button-primary button-large" onClick={onNextUnit}>
          Start next unit
        </button>
      </section>

      <section className="evidence">
        <h2 className="panel-title">Photo proof for this unit</h2>
        {error && <p className="error">{error}</p>}
        <div className="evidence-grid">
          {withPhotos.map((item, index) => (
            <figure key={`${item.timestamp}-${index}`} className={`evidence-card evidence-${item.action}`}>
              <div className="evidence-photo">
                <PhotoWithBox src={item.photo_url!} box={item.problem_box} alt={readableId(item.check_id)} />
              </div>
              <figcaption>
                <span className={`badge badge-small badge-${item.action}`}>{ACTION_LABEL[item.action]}</span>
                <strong>{readableId(item.check_id)}</strong>
                <span className="muted mono">{formatTime(item.timestamp)}</span>
                <span className="evidence-reason">{item.reason}</span>
              </figcaption>
            </figure>
          ))}
        </div>
      </section>
    </main>
  );
}

function Stat({ value, label }: { value: number; label: string }) {
  return (
    <div className="stat">
      <span className="stat-value">{value}</span>
      <span className="stat-label">{label}</span>
    </div>
  );
}
