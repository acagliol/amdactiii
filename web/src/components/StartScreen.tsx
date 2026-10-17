import { useEffect, useState } from "react";
import type { AssemblyInfo, CustomChecklist } from "../types";
import { CustomChecklistForm } from "./CustomChecklistForm";
import { LogoMark, Wordmark } from "./Logo";

interface StartScreenProps {
  assemblies: AssemblyInfo[];
  busy: boolean;
  error: string | null;
  onStart: (assemblyFile: string, serial: string) => void;
  onStartCustom: (spec: CustomChecklist, serial: string) => void;
}

const PREFERRED_DEMO = "packing_box.yaml";

/** "What are you checking today?": a ready-made checklist, or your own in a minute. */
export function StartScreen({ assemblies, busy, error, onStart, onStartCustom }: StartScreenProps) {
  const [serial, setSerial] = useState("");

  return (
    <main className="start">
      <div className="start-brand">
        <LogoMark size={80} />
        <Wordmark large />
        <p className="tagline">Catch it before it&apos;s covered</p>
      </div>

      <div className="start-body">
        <div className="start-head">
          <h1 className="start-title">What are you checking today?</h1>
          <label className="field serial-field">
            <span>Unit serial (optional)</span>
            <input value={serial} onChange={(event) => setSerial(event.target.value)} placeholder="e.g. BOX-1042" maxLength={64} />
          </label>
        </div>

        {error && <p className="error banner">{error}</p>}

        <div className="start-grid">
          <ReadyMadeOption assemblies={assemblies} busy={busy} onStart={(file) => onStart(file, serial)} />
          <CustomChecklistForm busy={busy} onStart={(spec) => onStartCustom(spec, serial)} />
        </div>
      </div>
    </main>
  );
}

interface ReadyMadeOptionProps {
  assemblies: AssemblyInfo[];
  busy: boolean;
  onStart: (assemblyFile: string) => void;
}

/** Checklists a supervisor already set up (this is how it works on a real line). */
function ReadyMadeOption({ assemblies, busy, onStart }: ReadyMadeOptionProps) {
  const [selected, setSelected] = useState("");

  // Default to the demo checklist once the list arrives.
  useEffect(() => {
    if (selected || assemblies.length === 0) return;
    setSelected((assemblies.find((item) => item.file === PREFERRED_DEMO) ?? assemblies[0]).file);
  }, [assemblies, selected]);

  return (
    <form
      className="start-option"
      onSubmit={(event) => {
        event.preventDefault();
        if (selected) onStart(selected);
      }}
    >
      <div>
        <h2 className="option-title">Ready-made</h2>
        <p className="muted option-text">Checklists a supervisor already set up, like on a real line.</p>
      </div>

      <div className="option-list" role="radiogroup" aria-label="Checklist">
        {assemblies.map((item) => (
          <label key={item.file} className={selected === item.file ? "option-row selected" : "option-row"}>
            <input
              type="radio"
              name="assembly"
              value={item.file}
              checked={selected === item.file}
              onChange={() => setSelected(item.file)}
            />
            <span className="option-name">{item.name}</span>
            <span className="muted">{item.checks} checks</span>
          </label>
        ))}
      </div>

      <button className="button button-primary button-large" type="submit" disabled={busy || !selected}>
        {busy ? "Starting…" : "Start unit"}
      </button>
    </form>
  );
}
